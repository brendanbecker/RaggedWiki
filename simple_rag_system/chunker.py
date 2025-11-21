"""
Chunking strategies for RAG system.

Implements three chunking approaches:
1. Layout-aware: Chunk at section (H2) boundaries
2. Naive: Fixed-size chunks with overlap
3. Abstract-first: Generate abstracts + full sections
"""

import re
import tiktoken
from typing import List, Dict, Tuple
import config


class Chunker:
    """Base chunker class with common utilities."""

    def __init__(self):
        self.encoding = tiktoken.get_encoding(config.TIKTOKEN_ENCODING)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        return len(self.encoding.encode(text))

    def chunk(self, content: str, metadata: Dict) -> List[Dict]:
        """
        Chunk content into semantic units.
        Returns list of chunk dicts with content and metadata.
        """
        raise NotImplementedError("Subclass must implement chunk()")


class LayoutAwareChunker(Chunker):
    """
    Layout-aware chunking that respects document structure.
    Splits at H2 (##) section boundaries.
    """

    def __init__(self):
        super().__init__()
        self.max_tokens = config.LAYOUT_AWARE_MAX_TOKENS
        self.min_tokens = config.LAYOUT_AWARE_MIN_TOKENS
        self.merge_small = config.LAYOUT_AWARE_MERGE_SMALL

    def chunk(self, content: str, metadata: Dict) -> List[Dict]:
        """
        Chunk markdown content at H2 boundaries.

        Args:
            content: Markdown content
            metadata: Document metadata

        Returns:
            List of chunk dicts with content, metadata, and token count
        """
        sections = self._split_by_h2(content)
        chunks = []

        for i, section in enumerate(sections):
            token_count = self.count_tokens(section["content"])

            # Skip empty or very small sections
            if token_count < 50:
                continue

            # If section is too large, split by H3
            if token_count > self.max_tokens:
                subsections = self._split_by_h3(section["content"])
                for j, subsection in enumerate(subsections):
                    subtoken_count = self.count_tokens(subsection["content"])
                    chunks.append({
                        "content": subsection["content"],
                        "section_title": f"{section['title']} - {subsection['title']}",
                        "heading_level": "h3",
                        "tokens": subtoken_count,
                        "chunk_index": len(chunks),
                        **metadata
                    })
            else:
                chunks.append({
                    "content": section["content"],
                    "section_title": section["title"],
                    "heading_level": "h2",
                    "tokens": token_count,
                    "chunk_index": len(chunks),
                    **metadata
                })

        # Optionally merge small sections
        if self.merge_small:
            chunks = self._merge_small_chunks(chunks)

        return chunks

    def _split_by_h2(self, content: str) -> List[Dict]:
        """Split content at H2 (##) boundaries."""
        sections = []
        lines = content.split('\n')
        current_section = []
        current_title = "Introduction"

        for line in lines:
            # Check for H2 header (## Title)
            h2_match = re.match(r'^##\s+(.+)$', line)
            if h2_match:
                # Save previous section
                if current_section:
                    sections.append({
                        "title": current_title,
                        "content": '\n'.join(current_section).strip()
                    })
                # Start new section
                current_title = h2_match.group(1)
                current_section = [line]
            else:
                current_section.append(line)

        # Save last section
        if current_section:
            sections.append({
                "title": current_title,
                "content": '\n'.join(current_section).strip()
            })

        return sections

    def _split_by_h3(self, content: str) -> List[Dict]:
        """Split content at H3 (###) boundaries."""
        sections = []
        lines = content.split('\n')
        current_section = []
        current_title = "Section"

        for line in lines:
            # Check for H3 header (### Title)
            h3_match = re.match(r'^###\s+(.+)$', line)
            if h3_match:
                # Save previous section
                if current_section:
                    sections.append({
                        "title": current_title,
                        "content": '\n'.join(current_section).strip()
                    })
                # Start new section
                current_title = h3_match.group(1)
                current_section = [line]
            else:
                current_section.append(line)

        # Save last section
        if current_section:
            sections.append({
                "title": current_title,
                "content": '\n'.join(current_section).strip()
            })

        return sections

    def _merge_small_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Merge chunks smaller than min_tokens with next chunk."""
        merged = []
        i = 0

        while i < len(chunks):
            current = chunks[i]

            # If current chunk is small and there's a next chunk
            if current["tokens"] < self.min_tokens and i + 1 < len(chunks):
                next_chunk = chunks[i + 1]
                # Merge with next
                merged_content = current["content"] + "\n\n" + next_chunk["content"]
                merged.append({
                    **current,
                    "content": merged_content,
                    "section_title": f"{current['section_title']} + {next_chunk['section_title']}",
                    "tokens": self.count_tokens(merged_content),
                    "merged": True
                })
                i += 2  # Skip next chunk since we merged it
            else:
                merged.append(current)
                i += 1

        return merged


class NaiveChunker(Chunker):
    """
    Naive fixed-size chunking with overlap.
    Splits at arbitrary token boundaries.
    """

    def __init__(self):
        super().__init__()
        self.chunk_size = config.NAIVE_CHUNK_SIZE
        self.overlap = config.NAIVE_OVERLAP

    def chunk(self, content: str, metadata: Dict) -> List[Dict]:
        """
        Chunk content into fixed-size pieces with overlap.

        Args:
            content: Text content
            metadata: Document metadata

        Returns:
            List of chunk dicts
        """
        # Tokenize entire content
        tokens = self.encoding.encode(content)
        chunks = []
        start = 0

        while start < len(tokens):
            # Get chunk of tokens
            end = min(start + self.chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]

            # Decode back to text
            chunk_text = self.encoding.decode(chunk_tokens)

            chunks.append({
                "content": chunk_text,
                "section_title": f"Chunk {len(chunks) + 1}",
                "heading_level": "none",
                "tokens": len(chunk_tokens),
                "chunk_index": len(chunks),
                "start_token": start,
                "end_token": end,
                **metadata
            })

            # Move start forward with overlap
            start = end - self.overlap

        return chunks


class AbstractFirstChunker(LayoutAwareChunker):
    """
    Abstract-first chunking: Generate abstracts for each section.
    Stores both abstract and full content.
    """

    def __init__(self):
        super().__init__()
        self.abstract_max_tokens = config.ABSTRACT_MAX_TOKENS

    def chunk(self, content: str, metadata: Dict) -> List[Dict]:
        """
        Chunk with abstract generation.

        Returns chunks with both 'abstract' and 'content' fields.
        """
        # First, do layout-aware chunking
        base_chunks = super().chunk(content, metadata)

        # Then generate abstracts for each chunk
        for chunk in base_chunks:
            chunk["abstract"] = self._generate_abstract(chunk["content"])
            chunk["abstract_tokens"] = self.count_tokens(chunk["abstract"])

        return base_chunks

    def _generate_abstract(self, content: str) -> str:
        """
        Generate abstract from content.

        Current implementation: Extractive (first N tokens)
        Future: Use summarization model (e.g., BART, T5)
        """
        if config.ABSTRACT_GENERATION_METHOD == "extractive":
            return self._extractive_abstract(content)
        else:
            # TODO: Implement LLM-based summarization
            return self._extractive_abstract(content)

    def _extractive_abstract(self, content: str) -> str:
        """Extract first N tokens as abstract."""
        tokens = self.encoding.encode(content)
        abstract_tokens = tokens[:self.abstract_max_tokens]
        abstract = self.encoding.decode(abstract_tokens)

        # Try to end at sentence boundary
        # Find last period, exclamation, or question mark
        for char in ['. ', '! ', '? ']:
            last_pos = abstract.rfind(char)
            if last_pos > len(abstract) * 0.7:  # Only if we're close to the end
                abstract = abstract[:last_pos + 1]
                break

        return abstract


def get_chunker(strategy: str = None) -> Chunker:
    """
    Factory function to get chunker instance.

    Args:
        strategy: Chunking strategy name (layout-aware, naive, abstract-first)

    Returns:
        Chunker instance
    """
    if strategy is None:
        strategy = config.CHUNKING_STRATEGY

    if strategy == "layout-aware":
        return LayoutAwareChunker()
    elif strategy == "naive":
        return NaiveChunker()
    elif strategy == "abstract-first":
        return AbstractFirstChunker()
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy}")
