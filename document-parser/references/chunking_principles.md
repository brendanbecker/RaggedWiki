# Document Chunking Principles for LLM Parsing

## The 400-900 Token Sweet Spot

When parsing large documents for LLM consumption, sections should target **400-900 tokens** for optimal balance:

- **< 400 tokens**: Risk of incomplete context leading to misunderstanding
- **400-900 tokens**: Complete semantic units that are self-contained
- **> 900 tokens**: Noise and reduced precision, harder to process

This range ensures:
1. **Semantic Completeness**: Each section contains a complete thought/procedure
2. **Embedding Efficiency**: Optimal for modern embedding models (text-embedding-3-large, etc.)
3. **Context Window Optimization**: 10-20 sections fit comfortably in LLM context windows

## Layout-Aware Hierarchical Chunking

The preferred strategy for structured documents (technical docs, research papers, runbooks):

### Core Principle
**Respect natural document structure** - split at semantic boundaries (headers) rather than arbitrary token counts.

### Implementation
1. **Extract headers** (H1, H2, H3, etc.) to identify natural sections
2. **Build hierarchy** - preserve parent-child relationships
3. **Merge small sections** - combine sections < 400 tokens with adjacent content
4. **Split large sections** - recursively break sections > 900 tokens at sub-headers or paragraphs

### Why This Works
- Prevents fragmenting concepts mid-thought
- Preserves logical flow and dependencies
- Maintains hierarchical relationships
- Each chunk is semantically complete and independently useful

## Dual-Storage Pattern

For maximum retrieval quality, create **two representations** of each section:

### 1. Abstract (100-200 tokens)
- High-level summary of the section
- Preserves technical terms exactly
- Lists key concepts, findings, or procedures
- Enables fast scanning and filtering

### 2. Full Section (400-900 tokens)
- Complete content with all details
- Includes code examples, tables, specifics
- Provides full context for LLM reasoning

### Benefits
- Abstracts enable quick overview without loading full content
- Full sections provide depth when needed
- Supports progressive disclosure (scan abstracts, then dive deep)

## Structure-Aware Parsing Patterns

### For Technical Documentation
- **Split on**: Markdown headers (#, ##, ###)
- **Preserve**: Section hierarchy, code blocks, tables
- **Target**: 400-900 tokens per major section
- **Include**: Breadcrumbs showing section path

### For Research Papers
- **Split on**: Major sections (Abstract, Introduction, Methods, Results, Discussion)
- **Preserve**: Citations, tables, figures with captions
- **Extract**: Key findings, benchmarks, metrics separately
- **Target**: 400-900 tokens per conceptual unit

### For Code Documentation
- **Split on**: Function/class boundaries
- **Preserve**: Complete functions with docstrings
- **Include**: Surrounding context (imports, class definition)
- **Target**: Logical code units (may vary from 400-900)

## Post-Processing Guidelines

After initial chunking:

1. **Validate completeness**: Every section should make sense standalone
2. **Check hierarchy**: Parent-child relationships must be valid
3. **Extract metadata**: Pull out tables, code blocks, benchmarks separately
4. **Generate abstracts**: Create summaries for sections ≥ 400 tokens
5. **Build section map**: Create navigable index with hierarchy

## Output Format

Structured markdown with:
- **Section metadata**: ID, title, level, token count
- **Hierarchy**: Parent-child relationships
- **Abstracts**: Quick summaries
- **Full content**: Complete sections
- **Extracted elements**: Tables, code, benchmarks in structured format
