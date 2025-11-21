#!/usr/bin/env python3
"""
Query interface for RAG system.

Search the indexed wiki documents using semantic similarity.
"""

import argparse
import sys
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

import config

console = Console()


class RAGQueryEngine:
    """Query engine for RAG system."""

    def __init__(self, index_path: str = None, embedding_model: str = None):
        self.index_path = index_path or config.CHROMADB_PERSIST_DIRECTORY
        self.embedding_model_name = embedding_model or config.EMBEDDING_MODEL

        # Load embedding model
        console.print(f"[cyan]Loading embedding model: {self.embedding_model_name}[/cyan]")
        self.embedding_model = SentenceTransformer(self.embedding_model_name)

        # Load ChromaDB
        console.print(f"[cyan]Loading index from: {self.index_path}[/cyan]")
        self.client = chromadb.PersistentClient(path=self.index_path)

        try:
            self.collection = self.client.get_collection(name=config.CHROMADB_COLLECTION_NAME)
            count = self.collection.count()
            console.print(f"[green]✓ Loaded collection with {count} chunks[/green]\n")
        except Exception as e:
            console.print(f"[red]✗ Error loading collection: {e}[/red]")
            console.print(f"[yellow]Have you run ingest.py first?[/yellow]")
            sys.exit(1)

    def query(
        self,
        query: str,
        top_k: int = None,
        filters: Optional[Dict] = None,
        min_score: float = None
    ) -> List[Dict]:
        """
        Query the RAG system.

        Args:
            query: Query string
            top_k: Number of results to return
            filters: Metadata filters (e.g., {"content_type": "runbook"})
            min_score: Minimum similarity score threshold (0-1)

        Returns:
            List of result dicts with content, metadata, and scores
        """
        top_k = top_k or config.DEFAULT_TOP_K
        min_score = min_score or config.MIN_SIMILARITY_SCORE

        # Generate query embedding
        query_embedding = self.embedding_model.encode(query)

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k * 2,  # Get extra results for filtering
            where=filters
        )

        # Process results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            # Calculate similarity score (ChromaDB returns L2 distance by default)
            # Convert distance to similarity score (0-1, where 1 is most similar)
            # For L2 distance, smaller is better, so we use: similarity = 1 / (1 + distance)
            distance = results['distances'][0][i] if 'distances' in results else 0
            similarity = 1 / (1 + distance)  # Converts distance to 0-1 score

            # Filter by minimum score
            if similarity < min_score:
                continue

            formatted_results.append({
                "id": results['ids'][0][i],
                "content": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "score": similarity
            })

            # Stop if we have enough results
            if len(formatted_results) >= top_k:
                break

        return formatted_results

    def interactive_mode(self):
        """Run interactive query mode."""
        console.print("\n[bold cyan]Interactive Query Mode[/bold cyan]")
        console.print("[dim]Type 'quit' or 'exit' to quit[/dim]\n")

        while True:
            try:
                query = console.input("[bold green]Enter query:[/bold green] ")

                if query.lower() in ['quit', 'exit', 'q']:
                    console.print("\n[cyan]Goodbye![/cyan]")
                    break

                if not query.strip():
                    continue

                # Execute query
                results = self.query(query)

                # Display results
                self.display_results(query, results)

            except KeyboardInterrupt:
                console.print("\n\n[cyan]Goodbye![/cyan]")
                break
            except Exception as e:
                console.print(f"\n[red]Error: {e}[/red]\n")

    def display_results(self, query: str, results: List[Dict]):
        """Display query results in rich format."""
        if not results:
            console.print("\n[yellow]No results found[/yellow]\n")
            return

        console.print(f"\n[bold]Results for:[/bold] \"{query}\"\n")

        for i, result in enumerate(results, 1):
            metadata = result['metadata']
            score = result['score']
            content = result['content']

            # Build header
            source = metadata.get('source_file', 'Unknown')
            section = metadata.get('section_title', 'N/A')
            content_type = metadata.get('content_type', 'document')

            # Truncate content for display (first 500 chars)
            display_content = content[:500]
            if len(content) > 500:
                display_content += "\n\n[dim]...(truncated)[/dim]"

            # Create panel with result
            title = f"[{i}] Score: {score:.2f} | {content_type.title()}: {source}"

            # Add optional metadata to subtitle
            subtitle_parts = []
            if 'service_name' in metadata:
                subtitle_parts.append(f"Service: {metadata['service_name']}")
            if 'severity' in metadata:
                subtitle_parts.append(f"Severity: {metadata['severity']}")
            subtitle = " | ".join(subtitle_parts) if subtitle_parts else None

            panel = Panel(
                Markdown(display_content),
                title=title,
                subtitle=subtitle,
                border_style="cyan",
                expand=False
            )

            console.print(panel)
            console.print()  # Blank line between results


def main():
    parser = argparse.ArgumentParser(
        description="Query the SRE wiki RAG system"
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Query string (omit for interactive mode)"
    )
    parser.add_argument(
        "--index",
        type=str,
        default=config.CHROMADB_PERSIST_DIRECTORY,
        help="Path to ChromaDB index directory"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=config.DEFAULT_TOP_K,
        help="Number of results to return"
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=config.MIN_SIMILARITY_SCORE,
        help="Minimum similarity score (0-1)"
    )
    parser.add_argument(
        "--filter-service",
        type=str,
        help="Filter by service name"
    )
    parser.add_argument(
        "--filter-type",
        type=str,
        choices=["runbook", "how-to", "incident", "process", "service-overview"],
        help="Filter by content type"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=config.EMBEDDING_MODEL,
        help="Sentence-transformers model"
    )

    args = parser.parse_args()

    # Build filters
    filters = {}
    if args.filter_service:
        filters["service_name"] = args.filter_service
    if args.filter_type:
        filters["content_type"] = args.filter_type

    # Create query engine
    engine = RAGQueryEngine(index_path=args.index, embedding_model=args.model)

    if args.query:
        # Single query mode
        results = engine.query(
            query=args.query,
            top_k=args.top_k,
            filters=filters if filters else None,
            min_score=args.min_score
        )
        engine.display_results(args.query, results)
    else:
        # Interactive mode
        engine.interactive_mode()


if __name__ == "__main__":
    main()
