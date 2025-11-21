#!/usr/bin/env python3
"""
Document ingestion script for RAG system.

Indexes documents from sre_wiki_example/ into ChromaDB vector database.
"""

import os
import re
import argparse
from pathlib import Path
from typing import List, Dict
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from rich.console import Console
from rich.progress import track
from tqdm import tqdm

import config
from chunker import get_chunker

console = Console()


class MetadataExtractor:
    """Extract metadata from markdown documents."""

    @staticmethod
    def extract_from_content(content: str, file_path: str) -> Dict:
        """
        Extract metadata from document content.

        Looks for metadata in:
        - Frontmatter (YAML)
        - Blockquote metadata tables (> **Key:** Value)
        - H1 title
        """
        metadata = {
            "source_file": str(file_path),
            "content_type": MetadataExtractor._infer_content_type(file_path),
        }

        # Extract from blockquote metadata (> **Service:** value | **Env:** value)
        blockquote_pattern = r'>\s*\*\*(.+?):\*\*\s*(.+?)(?:\s*\||$)'
        for match in re.finditer(blockquote_pattern, content):
            key = match.group(1).lower().replace(' ', '_')
            value = match.group(2).strip()
            metadata[key] = value

        # Extract H1 title
        h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if h1_match:
            metadata['title'] = h1_match.group(1)

        # Clean up specific metadata fields
        if 'service' in metadata:
            metadata['service_name'] = metadata['service']
        if 'severity' in metadata:
            metadata['severity'] = metadata['severity'].upper()

        return metadata

    @staticmethod
    def _infer_content_type(file_path: Path) -> str:
        """Infer content type from file path."""
        path_str = str(file_path)
        if '/runbooks/' in path_str:
            return 'runbook'
        elif '/how-to/' in path_str:
            return 'how-to'
        elif '/incidents/' in path_str:
            return 'incident'
        elif '/process/' in path_str:
            return 'process'
        elif '/apps/' in path_str:
            return 'service-overview'
        elif '/event-prep/' in path_str:
            return 'event-prep'
        else:
            return 'document'


class DocumentIndexer:
    """Index documents into ChromaDB vector database."""

    def __init__(self, index_path: str = None, embedding_model: str = None):
        self.index_path = index_path or config.CHROMADB_PERSIST_DIRECTORY
        self.embedding_model_name = embedding_model or config.EMBEDDING_MODEL

        console.print(f"[cyan]Loading embedding model: {self.embedding_model_name}[/cyan]")
        self.embedding_model = SentenceTransformer(self.embedding_model_name)

        console.print(f"[cyan]Initializing ChromaDB at: {self.index_path}[/cyan]")
        self.client = chromadb.PersistentClient(path=self.index_path)

        # Create or get collection
        try:
            self.client.delete_collection(name=config.CHROMADB_COLLECTION_NAME)
            console.print(f"[yellow]Deleted existing collection: {config.CHROMADB_COLLECTION_NAME}[/yellow]")
        except:
            pass

        self.collection = self.client.create_collection(
            name=config.CHROMADB_COLLECTION_NAME,
            metadata={"description": "SRE Wiki documentation"}
        )

    def index_directory(self, directory: str, strategy: str = None):
        """
        Index all markdown files in directory.

        Args:
            directory: Path to directory containing markdown files
            strategy: Chunking strategy (layout-aware, naive, abstract-first)
        """
        directory = Path(directory)
        chunker = get_chunker(strategy)

        # Find all markdown files
        md_files = []
        for ext in config.SUPPORTED_EXTENSIONS:
            md_files.extend(directory.rglob(f"*{ext}"))

        # Filter out excluded files
        md_files = [
            f for f in md_files
            if not any(re.match(pattern, f.name) for pattern in config.EXCLUDE_PATTERNS)
        ]

        console.print(f"\n[green]Found {len(md_files)} documents to index[/green]\n")

        # Process each file
        total_chunks = 0
        for file_path in track(md_files, description="Indexing documents"):
            chunks_count = self.index_file(file_path, chunker)
            total_chunks += chunks_count

        console.print(f"\n[green]✓ Indexed {len(md_files)} documents, {total_chunks} chunks total[/green]")

    def index_file(self, file_path: Path, chunker) -> int:
        """Index a single file."""
        # Read content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract metadata
        metadata = MetadataExtractor.extract_from_content(content, file_path)

        # Chunk content
        chunks = chunker.chunk(content, metadata)

        if not chunks:
            console.print(f"[yellow]  No chunks extracted from {file_path.name}[/yellow]")
            return 0

        # Generate embeddings
        chunk_texts = [chunk["content"] for chunk in chunks]
        embeddings = self.embedding_model.encode(chunk_texts, show_progress_bar=False)

        # Prepare data for ChromaDB
        ids = []
        metadatas = []
        documents = []

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Create unique ID
            chunk_id = f"{file_path.stem}-chunk-{i}"
            ids.append(chunk_id)

            # Prepare metadata (ChromaDB requires all values to be strings, ints, or floats)
            chunk_metadata = {
                "source_file": str(file_path.relative_to(file_path.parent.parent)),
                "section_title": chunk.get("section_title", ""),
                "heading_level": chunk.get("heading_level", "h2"),
                "tokens": chunk.get("tokens", 0),
                "chunk_index": i,
                "content_type": chunk.get("content_type", "document"),
            }

            # Add optional metadata fields if present
            optional_fields = ["service_name", "environment", "severity", "owner", "title"]
            for field in optional_fields:
                if field in chunk and chunk[field]:
                    chunk_metadata[field] = str(chunk[field])

            metadatas.append(chunk_metadata)

            # Store full content
            documents.append(chunk["content"])

        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=documents,
            metadatas=metadatas
        )

        console.print(f"  [dim]{file_path.name}: {len(chunks)} chunks[/dim]")

        return len(chunks)


def main():
    parser = argparse.ArgumentParser(
        description="Index SRE wiki documents into ChromaDB vector database"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="../sre_wiki_example",
        help="Input directory containing markdown files"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=config.CHROMADB_PERSIST_DIRECTORY,
        help="Output directory for ChromaDB index"
    )
    parser.add_argument(
        "--strategy",
        type=str,
        choices=["layout-aware", "naive", "abstract-first"],
        default=config.CHUNKING_STRATEGY,
        help="Chunking strategy to use"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=config.EMBEDDING_MODEL,
        help="Sentence-transformers model to use for embeddings"
    )

    args = parser.parse_args()

    console.print("\n[bold cyan]SRE Wiki Document Indexer[/bold cyan]\n")
    console.print(f"Input directory: {args.input}")
    console.print(f"Output index: {args.output}")
    console.print(f"Chunking strategy: {args.strategy}")
    console.print(f"Embedding model: {args.model}\n")

    # Create indexer and run
    indexer = DocumentIndexer(index_path=args.output, embedding_model=args.model)
    indexer.index_directory(args.input, strategy=args.strategy)

    console.print(f"\n[bold green]✓ Indexing complete![/bold green]")
    console.print(f"[dim]Database saved to: {args.output}[/dim]\n")


if __name__ == "__main__":
    main()
