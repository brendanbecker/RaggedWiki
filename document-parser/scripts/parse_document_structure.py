#!/usr/bin/env python3
"""
Parse document structure: extract headers, build hierarchy, count tokens.

Usage:
    python parse_document_structure.py <input_file> [--output <output_file>]
"""

import re
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional
import argparse


def count_tokens(text: str) -> int:
    """
    Rough token count estimation (words * 1.3 for English text).
    For more accurate counts, use tiktoken library.
    """
    words = len(text.split())
    return int(words * 1.3)


def extract_headers(content: str) -> List[Dict]:
    """
    Extract all markdown headers with their positions and levels.

    Returns list of dicts with: level, title, line_num
    """
    headers = []
    lines = content.split('\n')

    for i, line in enumerate(lines, 1):
        # Match markdown headers (# Header, ## Header, etc.)
        match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            headers.append({
                'level': level,
                'title': title,
                'line_num': i
            })

    return headers


def build_section_hierarchy(content: str, headers: List[Dict]) -> List[Dict]:
    """
    Build hierarchical section structure with content and token counts.
    """
    lines = content.split('\n')
    sections = []

    for i, header in enumerate(headers):
        # Find section boundaries
        start_line = header['line_num']
        end_line = headers[i + 1]['line_num'] - 1 if i + 1 < len(headers) else len(lines)

        # Extract section content
        section_lines = lines[start_line:end_line]
        section_content = '\n'.join(section_lines)

        # Find parent section (previous header with lower level)
        parent_id = None
        for j in range(i - 1, -1, -1):
            if headers[j]['level'] < header['level']:
                parent_id = f"sec_{j}"
                break

        # Create section object
        section = {
            'id': f"sec_{i}",
            'title': header['title'],
            'level': header['level'],
            'parent_id': parent_id,
            'start_line': start_line,
            'end_line': end_line,
            'token_count': count_tokens(section_content),
            'content': section_content,
            'children': []
        }

        sections.append(section)

    # Build children lists
    for section in sections:
        for other in sections:
            if other['parent_id'] == section['id']:
                section['children'].append(other['id'])

    return sections


def generate_section_map(sections: List[Dict]) -> str:
    """
    Generate human-readable section map showing hierarchy.
    """
    def format_section(sec_id: str, indent: int = 0) -> str:
        section = next(s for s in sections if s['id'] == sec_id)
        prefix = "  " * indent
        title = section['title']
        tokens = section['token_count']
        level = section['level']

        output = f"{prefix}{'#' * level} {title} ({tokens} tokens)\n"

        for child_id in section['children']:
            output += format_section(child_id, indent + 1)

        return output

    # Find root sections (no parent)
    roots = [s['id'] for s in sections if s['parent_id'] is None]

    map_text = "# Document Section Map\n\n"
    for root_id in roots:
        map_text += format_section(root_id)

    return map_text


def main():
    parser = argparse.ArgumentParser(description='Parse document structure')
    parser.add_argument('input_file', help='Input markdown file')
    parser.add_argument('--output', '-o', help='Output JSON file (default: stdout)')
    parser.add_argument('--map', help='Generate section map to this file')

    args = parser.parse_args()

    # Read input file
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    content = input_path.read_text(encoding='utf-8')

    # Extract headers and build structure
    headers = extract_headers(content)
    sections = build_section_hierarchy(content, headers)

    # Prepare output
    result = {
        'file': str(input_path),
        'total_tokens': count_tokens(content),
        'num_sections': len(sections),
        'sections': sections
    }

    # Output JSON
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(f"✓ Structure written to: {output_path}")
    else:
        print(json.dumps(result, indent=2))

    # Generate section map if requested
    if args.map:
        map_text = generate_section_map(sections)
        map_path = Path(args.map)
        map_path.write_text(map_text, encoding='utf-8')
        print(f"✓ Section map written to: {map_path}")


if __name__ == '__main__':
    main()
