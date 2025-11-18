#!/usr/bin/env python3
"""
Extract metadata from markdown: tables, code blocks, benchmarks, key terms.

Usage:
    python extract_metadata.py <input_file> [--output <output_file>]
"""

import re
import json
import sys
from pathlib import Path
from typing import List, Dict
import argparse


def extract_tables(content: str) -> List[Dict]:
    """Extract markdown tables with their context."""
    tables = []
    lines = content.split('\n')
    in_table = False
    current_table = []
    table_start = 0

    for i, line in enumerate(lines, 1):
        # Check if line is part of a table (contains |)
        if '|' in line and line.strip():
            if not in_table:
                in_table = True
                table_start = i
                current_table = []
            current_table.append(line)
        else:
            if in_table and current_table:
                # End of table
                tables.append({
                    'start_line': table_start,
                    'end_line': i - 1,
                    'content': '\n'.join(current_table),
                    'num_rows': len(current_table)
                })
                in_table = False
                current_table = []

    # Handle table at end of file
    if in_table and current_table:
        tables.append({
            'start_line': table_start,
            'end_line': len(lines),
            'content': '\n'.join(current_table),
            'num_rows': len(current_table)
        })

    return tables


def extract_code_blocks(content: str) -> List[Dict]:
    """Extract fenced code blocks with language tags."""
    code_blocks = []
    pattern = r'```(\w*)\n(.*?)```'

    for match in re.finditer(pattern, content, re.DOTALL):
        language = match.group(1) or 'text'
        code = match.group(2)
        start_pos = match.start()

        # Find line number
        line_num = content[:start_pos].count('\n') + 1

        code_blocks.append({
            'language': language,
            'code': code.strip(),
            'line_num': line_num,
            'num_lines': code.count('\n') + 1
        })

    return code_blocks


def extract_benchmarks(content: str) -> List[Dict]:
    """
    Extract quantitative benchmarks and metrics.
    Looks for patterns like: X%, +X%, X improvement, accuracy of X, etc.
    """
    benchmarks = []

    # Patterns for different metric formats
    patterns = [
        # Percentages: 20%, +35%, -10%
        (r'([+\-]?\d+\.?\d*%)', 'percentage'),
        # Improvements: +11.2% accuracy, 20-35% improvement
        (r'([+\-]?\d+\.?\d*%)\s+(accuracy|improvement|gain|increase|decrease|reduction)', 'improvement'),
        # Ranges: 20-35%, 100k-200k
        (r'(\d+\.?\d*[kKmMbB]?)\s*-\s*(\d+\.?\d*[kKmMbB]?)', 'range'),
        # Latency: 150ms, 2.5s, 200-500ms
        (r'(\d+\.?\d*)\s*(ms|s|seconds?|milliseconds?)', 'latency'),
        # Recall/Precision: Recall@10, nDCG@10
        (r'(Recall|Precision|nDCG|MRR)@?(\d+)', 'metric'),
        # Scores: 0.88, 0.811
        (r'\b(0\.\d{2,3})\b', 'score')
    ]

    for pattern, metric_type in patterns:
        for match in re.finditer(pattern, content):
            # Get surrounding context (30 chars before/after)
            start = max(0, match.start() - 30)
            end = min(len(content), match.end() + 30)
            context = content[start:end].strip()

            benchmarks.append({
                'value': match.group(0),
                'type': metric_type,
                'context': context,
                'line_num': content[:match.start()].count('\n') + 1
            })

    return benchmarks


def extract_key_terms(content: str) -> Dict[str, List[str]]:
    """
    Extract key technical terms, model names, and techniques.
    Looks for capitalized terms, acronyms, and hyphenated terms.
    """
    # Common patterns for technical terms
    patterns = {
        'techniques': r'\b([A-Z][a-zA-Z]*(?:-[A-Z][a-zA-Z]*)+)\b',  # HyDE, Multi-HyDE, etc.
        'models': r'\b(text-embedding-[a-z0-9-]+|[a-z]+-[a-z]+-[a-z0-9]+|GPT-\d+|Claude|Gemini)\b',
        'acronyms': r'\b([A-Z]{2,})\b',  # BM25, RAG, etc.
    }

    results = {}
    for term_type, pattern in patterns.items():
        matches = set(re.findall(pattern, content))
        # Filter out common words
        filtered = [m for m in matches if m not in ['API', 'HTTP', 'URL', 'ID', 'PDF']]
        results[term_type] = sorted(filtered)

    return results


def main():
    parser = argparse.ArgumentParser(description='Extract metadata from markdown')
    parser.add_argument('input_file', help='Input markdown file')
    parser.add_argument('--output', '-o', help='Output JSON file (default: stdout)')

    args = parser.parse_args()

    # Read input file
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    content = input_path.read_text(encoding='utf-8')

    # Extract all metadata
    metadata = {
        'file': str(input_path),
        'tables': extract_tables(content),
        'code_blocks': extract_code_blocks(content),
        'benchmarks': extract_benchmarks(content),
        'key_terms': extract_key_terms(content)
    }

    # Add counts
    metadata['counts'] = {
        'tables': len(metadata['tables']),
        'code_blocks': len(metadata['code_blocks']),
        'benchmarks': len(metadata['benchmarks']),
        'techniques': len(metadata['key_terms'].get('techniques', [])),
        'models': len(metadata['key_terms'].get('models', [])),
        'acronyms': len(metadata['key_terms'].get('acronyms', []))
    }

    # Output
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        print(f"✓ Metadata written to: {output_path}")
    else:
        print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
