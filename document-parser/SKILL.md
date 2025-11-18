---
name: document-parser
description: Parse large documents that exceed context limits into structured sections with abstracts, metadata, and hierarchies. This skill should be used when encountering documents over the context limit (typically 25k+ tokens) or when a user explicitly requests document parsing. Apply layout-aware hierarchical chunking principles to preserve semantic structure.
---

# Document Parser

## Overview

Parse large documents into structured, navigable sections while preserving semantic meaning and hierarchical relationships. Generate abstracts for efficient scanning, extract metadata (tables, code blocks, benchmarks), and create section maps that enable targeted retrieval without loading entire documents into context.

## When to Use This Skill

Activate this skill when:
- A document exceeds the context window limit (>25,000 tokens)
- A user explicitly requests "parse this large document"
- Multiple large documents need to be analyzed comparatively
- Document structure needs to be preserved for future retrieval

## Quick Start

### Basic Document Parsing Workflow

1. **Analyze document structure** using `scripts/parse_document_structure.py`:
   ```bash
   python scripts/parse_document_structure.py <document.md> --output structure.json --map section_map.md
   ```

2. **Extract metadata** using `scripts/extract_metadata.py`:
   ```bash
   python scripts/extract_metadata.py <document.md> --output metadata.json
   ```

3. **Generate abstracts** for major sections (400+ tokens)

4. **Create final parsed output** in markdown format with:
   - Section map showing hierarchy
   - Abstracts for quick scanning
   - Full sections organized hierarchically
   - Extracted metadata (tables, code, benchmarks)

## Core Capabilities

### 1. Structure Analysis

Extract document structure respecting semantic boundaries rather than arbitrary token counts.

**Implementation:**
- Run `parse_document_structure.py` to extract headers and build hierarchy
- Review the structure JSON to understand sections, levels, and token counts
- Check `section_map.md` for human-readable hierarchy visualization

**Key Principles** (from `references/chunking_principles.md`):
- Target 400-900 tokens per section (semantic completeness without noise)
- Split at natural boundaries (headers, not arbitrary counts)
- Preserve parent-child relationships in hierarchy
- Merge sections < 400 tokens with adjacent content

**Example Output:**
```json
{
  "sections": [
    {
      "id": "sec_0",
      "title": "Executive Summary",
      "level": 1,
      "parent_id": null,
      "token_count": 420,
      "children": ["sec_1", "sec_2"]
    }
  ]
}
```

### 2. Abstract Generation

Create 100-200 token summaries for each major section (≥400 tokens).

**Prompt Template:**
```
Generate a 100-200 token abstract for this technical section.

The abstract should:
- Preserve all technical terms and model names exactly
- List key findings, benchmarks, or recommendations
- Include quantitative results (percentages, metrics)
- Be searchable by domain experts

Section Title: {title}
Section Content: {content}

Abstract:
```

**Quality Checks:**
- Abstracts preserve technical terminology
- Key metrics and benchmarks are included
- Length is within 100-200 token range
- Standalone readability (no external references needed)

### 3. Metadata Extraction

Extract structured data with special semantic value using `extract_metadata.py`.

**Extracted Elements:**
- **Tables**: Full markdown tables with row/column counts
- **Code blocks**: Language-tagged code with line numbers
- **Benchmarks**: Quantitative metrics (%, accuracy, latency, etc.)
- **Key terms**: Techniques, model names, acronyms

**Example Usage:**
```bash
python scripts/extract_metadata.py research_paper.md --output metadata.json
```

**Metadata Categories:**
```json
{
  "tables": [{"content": "...", "num_rows": 7, "start_line": 58}],
  "code_blocks": [{"language": "python", "code": "...", "line_num": 150}],
  "benchmarks": [{"value": "+35%", "type": "improvement", "context": "..."}],
  "key_terms": {
    "techniques": ["ColBERT", "MUVERA", "HyDE"],
    "models": ["text-embedding-3-large", "bge-m3"],
    "acronyms": ["RAG", "BM25", "MIPS"]
  }
}
```

### 4. Output Generation

Create structured markdown output for parsed documents.

**Output Structure:**
```markdown
# [Document Title] - Parsed

## Document Overview
- **Total Tokens**: 47,508
- **Sections**: 45
- **Tables**: 12
- **Code Blocks**: 8

## Section Map
[Hierarchical tree showing all sections with token counts]

## Abstracts
### [Section 1 Title]
[100-200 token summary]

### [Section 2 Title]
[100-200 token summary]

## Full Sections
### [Section 1 Title]
[Complete section content]

### [Section 2 Title]
[Complete section content]

## Extracted Metadata
### Tables
[All tables with context]

### Code Examples
[All code blocks with language tags]

### Benchmarks
[All quantitative metrics with context]

### Key Terms
[Techniques, models, acronyms]
```

## Common Workflows

### Workflow 1: Parse Single Large Document

**Input**: Single markdown file exceeding context limits

**Steps**:
1. Run `parse_document_structure.py` to get structure.json and section_map.md
2. Review section map to identify sections requiring abstracts
3. Generate abstracts for sections ≥400 tokens using LLM
4. Run `extract_metadata.py` to get metadata.json
5. Compile final parsed document in markdown format
6. Validate completeness (all sections have abstracts, metadata extracted)

**Output**: Structured markdown with sections, abstracts, and metadata

### Workflow 2: Comparative Analysis of Multiple Documents

**Input**: Multiple research papers or technical documents

**Steps**:
1. Parse each document individually (Workflow 1)
2. Extract all benchmarks and compare across documents
3. Identify common concepts using key terms
4. Create synthesis document showing comparative findings
5. Use section hierarchies to understand relationships

**Output**: Comparative analysis with cross-document insights

### Workflow 3: Progressive Document Reading

**Input**: Parsed document (from Workflow 1)

**Steps**:
1. Read all abstracts in "Abstracts" section
2. Identify high-value sections based on abstract relevance
3. Load full sections for those areas from "Full Sections"
4. Consult "Extracted Metadata" for specific benchmarks or code
5. Use section map to find related sections

**Output**: Efficient targeted understanding without loading full document

## Validation Checklist

Before completing a parsing task:

✓ **Structure**
- [ ] All headers extracted and hierarchy is valid
- [ ] Parent-child relationships are correct
- [ ] Section token counts are within guidelines (merge <400, consider splitting >900)

✓ **Abstracts**
- [ ] All sections ≥400 tokens have abstracts
- [ ] Abstracts are 100-200 tokens
- [ ] Technical terms preserved exactly
- [ ] Key metrics included

✓ **Metadata**
- [ ] All tables extracted with proper formatting
- [ ] Code blocks have language tags
- [ ] Benchmarks include context and values
- [ ] Key terms are categorized (techniques, models, acronyms)

✓ **Output Format**
- [ ] Document overview includes counts
- [ ] Section map is hierarchical and readable
- [ ] Abstracts section is complete
- [ ] Full sections maintain original formatting
- [ ] Metadata is organized by category

## Advanced Patterns

### Pattern 1: Edge Parsing (Section Relationships)

Identify how sections relate beyond hierarchy:
- **References**: "as discussed in Section X"
- **Dependencies**: "building on the previous section"
- **Comparisons**: "compared to Section Y"

Track these relationships to enable graph-based navigation.

### Pattern 2: Multi-Document Integration

When parsing multiple related documents:
1. Parse each document individually
2. Extract common concepts using key terms
3. Map relationships across documents
4. Create unified concept graph
5. Generate synthesis showing cross-document insights

### Pattern 3: Iterative Refinement

For complex documents:
1. Initial parse with structure extraction
2. Review section token counts
3. Merge or split sections as needed
4. Regenerate abstracts for modified sections
5. Validate completeness

## Resources

### scripts/

**`parse_document_structure.py`**: Extract headers, build hierarchy, count tokens
- Outputs: structure.json (machine-readable), section_map.md (human-readable)
- Usage: `python parse_document_structure.py <file.md> --output structure.json --map section_map.md`

**`extract_metadata.py`**: Extract tables, code blocks, benchmarks, key terms
- Outputs: metadata.json with categorized extracted elements
- Usage: `python extract_metadata.py <file.md> --output metadata.json`

### references/

**`chunking_principles.md`**: Core principles for document chunking
- The 400-900 token sweet spot rationale
- Layout-aware hierarchical chunking strategy
- Dual-storage pattern (abstracts + full sections)
- Structure-aware parsing patterns for different content types

Consult this reference when making chunking decisions or validating output quality.
