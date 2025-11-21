# Chunking Strategy Examples

This directory contains **side-by-side demonstrations** of different chunking strategies applied to the same content. Use these examples to understand how chunking choices affect retrieval quality, context preservation, and LLM performance.

## Purpose

The examples here demonstrate:
1. **How different chunking strategies handle the same content**
2. **Token counts per chunk** (with annotations showing how close they are to the 400-900 token "sweet spot")
3. **What gets lost or preserved** with each approach
4. **When to use each strategy** (decision criteria)

## Available Examples

### Example 1: Runbook Chunking
**Source Material**: Database failover runbook (realistic SRE content)

Demonstrates:
- **Naive Fixed-Size Chunking** → Breaks procedures mid-step, loses context
- **Layout-Aware Hierarchical Chunking** → Preserves complete procedures, maintains hierarchy
- **Abstract + Full Section** → Dual-storage model for hierarchical retrieval

**Files**:
- `01-runbook-naive.md` - Fixed 512-token chunks (bad approach)
- `01-runbook-layout-aware.md` - Section-based chunks (good approach)
- `01-runbook-with-abstracts.md` - Abstracts + full sections (best approach)
- `01-analysis.md` - Comparison and retrieval simulation

### Example 2: Code Documentation Chunking
**Source Material**: Kubernetes manifest with documentation

Demonstrates:
- **Code-Aware Chunking** → Preserves complete YAML resources
- **Fixed-Size Chunking** → Breaks YAML structure, creates invalid chunks
- **Hybrid Approach** → Combines code-aware and layout-aware for docs + code

**Files**:
- `02-code-naive.md` - Fixed-size chunks (bad approach)
- `02-code-aware.md` - AST-based chunking (good approach)
- `02-analysis.md` - Comparison and when to use each

### Example 3: Post-Mortem Chunking
**Source Material**: Incident post-mortem (timeline, RCA, action items)

Demonstrates:
- **Section-Based Chunking** → Each section as separate chunk
- **Time-Window Chunking** → Timeline grouped by time windows (alternative approach)
- **Entity-Based Chunking** → Grouped by involved service/team (alternative approach)

**Files**:
- `03-postmortem-section-based.md` - Standard section chunking
- `03-postmortem-time-windows.md` - Alternative time-based approach
- `03-analysis.md` - Which approach works best for post-mortems

## How to Use These Examples

### For Content Strategists
1. Read the **analysis files** (`*-analysis.md`) first to understand trade-offs
2. Compare chunk outputs side-by-side
3. Apply the decision criteria to your own content types

### For RAG System Implementers
1. Use the chunked outputs as **test cases** for your ingestion pipeline
2. Implement the chunking algorithms described
3. Validate that your chunker produces similar results on the source material

### For Technical Writers
1. See how **document structure affects chunking quality**
2. Learn to write sections in the 400-900 token range
3. Understand why hierarchical headers improve retrieval

## Token Counting Convention

All examples use this annotation format:

```markdown
## Section Title [650 tokens] ✅

Content here...

[End of chunk - tokens: 650/900 - 72% utilization - GOOD]
```

**Legend**:
- ✅ **400-900 tokens**: Sweet spot, optimal for retrieval
- ⚠️ **200-400 or 900-1200 tokens**: Acceptable but not ideal
- ❌ **<200 or >1200 tokens**: Problematic for quality retrieval

## Retrieval Quality Metrics

Each analysis file includes simulated retrieval scenarios:

**Query**: "How do I fail over the database?"

**Naive Chunking Result**:
- Chunk 3/8 retrieved (score: 0.82)
- Contains: "...initiate a failover, ensure you have: Access to psql client..."
- **Missing**: The actual failover commands (in chunk 5/8, not retrieved)

**Layout-Aware Chunking Result**:
- Chunk "Failover Procedure" retrieved (score: 0.89)
- Contains: Complete procedure from prerequisites through validation
- **Success**: All necessary steps in one chunk

## Implementation Hints

Each example includes notes on **how the chunking was done**:

```python
# Example: Layout-aware hierarchical chunking
def chunk_by_sections(markdown_content):
    # Parse markdown into AST
    # Identify H2 sections as chunk boundaries
    # Extract content between boundaries
    # Generate abstract (first 100-200 tokens)
    # Store both abstract and full section
```

These are **conceptual** implementations to guide your own work, not production-ready code.

## Related Curriculum Modules

These examples support learning objectives from:
- **Module 01: Why RAG Fails** - See failure modes in action
- **Module 02: Chunking Strategies** - Concrete implementations of the Four Pillars
- **Module 08: Implementation Guide** - Reference schemas and pipelines

## Contributing

To add new examples:
1. Choose a distinct content type (logs, config files, architecture docs, etc.)
2. Create at least 2 chunking approaches (bad vs. good)
3. Write analysis comparing retrieval quality
4. Include token counts and annotations
5. Update this README with new example description
