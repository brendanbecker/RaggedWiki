# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

RaggedWiki is an **educational curriculum and project guideline** that teaches how to use RAG (Retrieval-Augmented Generation) correctly in enterprise environments, and how to structure wikis to work optimally for both human readers and LLM systems.

### Current State
The project currently contains **research-based educational materials** in the form of comprehensive technical documents. These materials are awaiting the results of ongoing deep research before being updated more thoroughly.

### Future Direction
Once research is complete and documents are updated, the goal is to evolve this into **modular educational content** similar to the ce101 course structure (see `../ce101/` for reference) - consisting of numbered modules (01-xxx.md, 02-xxx.md, etc.) that progressively build understanding.

The project may also evolve into a reference implementation or system in the future, but that's not the current focus.

## Learning Materials Structure

The repository contains three interconnected educational documents that build understanding from different angles:

### 1. `rag_implementation_specs.md` - "The Blueprint"
**Educational Focus**: Enterprise-grade RAG architecture patterns

**What You'll Learn**:
- How to design dual-collection vector databases (abstracts vs full sections)
- Why specific token ranges (400-900) prevent hallucinations
- API contract design for production RAG systems
- Cost modeling and infrastructure planning for real deployments
- Processing pipeline architecture with concrete Python examples

**Key Takeaway**: Enterprise RAG isn't just "chunk documents and search" - it requires deliberate schema design, multi-stage retrieval, and careful cost-performance tradeoffs.

### 2. `wiki_content_strategy.md` - "The Decision Framework"
**Educational Focus**: Content-aware chunking strategy selection

**What You'll Learn**:
- Why different content types require different chunking strategies
- The 4 fundamental chunking approaches and when to use each:
  - Layout-Aware Hierarchical (structured documents)
  - Code-Aware (IaC and source code)
  - Fixed-Size Sliding Window (logs and unstructured content)
  - Recursive Splitter (complex mixed content)
- How to analyze content characteristics (structure, density, query patterns, update frequency)
- Real-world examples from SRE contexts (runbooks, post-mortems, Terraform, K8s manifests)

**Key Takeaway**: There is no "one size fits all" chunking strategy - successful RAG requires matching strategy to content type.

### 3. `technique_deep_dive.md` - "The Technical Foundation"
**Educational Focus**: Deep understanding of hierarchical chunking mechanics

**What You'll Learn**:
- Why the dual-storage model (abstracts + full sections) reduces hallucinations by 65%
- Mathematical foundations of 3-stage retrieval (BM25, cosine similarity, cross-encoder)
- How semantic hierarchies enable better context delivery
- Post-processing techniques (deduplication, section packing, citation breadcrumbs)
- Performance characteristics and latency budgeting

**Key Takeaway**: Layout-aware chunking preserves document structure, enabling retrieval systems to understand context rather than just matching keywords.

## Learning Path Recommendations

### For Wiki Architects & Content Strategists
**Goal**: Structure wikis for both human usability and LLM retrieval

1. Start with `wiki_content_strategy.md` - understand the decision matrix
2. Read `technique_deep_dive.md` sections on "Why This Works" for each strategy
3. Apply the "Four Pillars of Content Analysis" to your existing wiki:
   - Structure Regularity
   - Semantic Density
   - Query Patterns
   - Update Frequency
4. Use the decision tree (bottom of `wiki_content_strategy.md`) to audit your content

**Key Question to Answer**: "If I reorganize my wiki sections to be 400-900 tokens each with clear hierarchical headers, how much better would retrieval be?"

### For RAG System Implementers
**Goal**: Build production-quality RAG systems

1. Start with `rag_implementation_specs.md` - understand the full architecture
2. Study the 3-stage retrieval pipeline in `technique_deep_dive.md`
3. Review schema designs (Vector DB, Elasticsearch, PostgreSQL) in implementation specs
4. Use `wiki_content_strategy.md` to build your content processing pipeline
5. Study the cost optimization strategies and monitoring approaches

**Key Question to Answer**: "How do I balance retrieval quality, latency, and cost in my specific environment?"

### For Technical Writers & SRE Documentation Teams
**Goal**: Write documentation that works well for both humans and RAG systems

1. Read the "Content-Specific Recommendations" section in `wiki_content_strategy.md`
2. Study the examples in `technique_deep_dive.md` showing "BAD vs GOOD" chunking
3. Learn from the runbook and post-mortem structuring examples
4. Understand why 400-900 token sections with clear headers improve both human scanning and LLM retrieval

**Key Question to Answer**: "How should I structure my runbooks/post-mortems/troubleshooting guides to maximize retrieval accuracy?"

## Core Educational Principles

### 1. Structure Preserves Context
Traditional fixed-size chunking destroys document structure, leading to:
- Fragmented procedures split mid-step
- Lost hierarchical relationships
- Context pollution (irrelevant chunks retrieved)

**Learning**: Layout-aware chunking respects natural section boundaries, keeping complete thoughts intact.

### 2. Abstracts Enable Hierarchical Search
The dual-storage model (100-200 token abstracts + 400-900 token full sections) enables:
- Fast initial filtering via abstract search
- Complete context delivery via full section retrieval
- Reduced false positives

**Learning**: Don't make LLMs search through full text when abstracts can filter candidates first.

### 3. Multi-Stage Retrieval Balances Recall and Precision
- **Stage 1 (BM25)**: High recall via keyword matching (captures technical terms)
- **Stage 2 (Dense Vector)**: Semantic understanding (handles paraphrasing)
- **Stage 3 (Cross-Encoder)**: Maximum precision (bidirectional attention)

**Learning**: Each stage optimizes for different aspects - skipping stages significantly degrades quality.

### 4. Content Type Determines Strategy
A runbook is not a log file. Kubernetes YAML is not a post-mortem. Each requires different chunking:

**Learning**: Analyze content characteristics before selecting chunking strategy - the decision matrix in `wiki_content_strategy.md` shows how.

### 5. Token Budgets Matter
- **<400 tokens**: Risk of incomplete context → hallucinations
- **400-900 tokens**: Complete operational units → accurate retrieval
- **>900 tokens**: Noise and reduced precision → degraded results

**Learning**: The "sweet spot" comes from balancing semantic completeness, embedding efficiency, and LLM context window constraints.

## Applying These Concepts to Your Wiki

### Wiki Structure Audit
Use the "Four Pillars" framework to evaluate each content type in your wiki:

1. **Structure Regularity**: Do your runbooks follow consistent header patterns?
2. **Semantic Density**: Can each section stand alone, or does it require context from other sections?
3. **Query Patterns**: How do users actually search for this content?
4. **Update Frequency**: Do you need versioning and change detection?

### Content Type Classification
Map your wiki content to the decision matrix:
- Runbooks → Layout-Aware Hierarchical
- IaC (Terraform/Ansible) → Code-Aware
- Kubernetes manifests → Code-Aware
- Post-mortems → Layout-Aware Hierarchical
- Application logs → Fixed-Size Sliding
- Stack traces → Fixed-Size Sliding
- Architecture docs → Layout-Aware Hierarchical
- Configuration files → Fixed-Size or Code-Aware

### Section Size Guidelines
When writing new documentation:
- Target 400-900 tokens per major section
- Use clear hierarchical headers (H1, H2, H3)
- Keep complete procedures within single sections
- Include validation steps with procedures
- Preserve command examples with explanations

## Real-World Application Examples

### Example 1: Runbook Restructuring
**Before** (poor for RAG):
```markdown
# Database Issues
Lots of text covering 12 different problems in one 5000-token section...
```

**After** (optimized):
```markdown
# Database Issues

## Connection Pool Exhaustion (650 tokens)
Detection, diagnosis, remediation - complete procedure

## Slow Query Performance (720 tokens)
EXPLAIN analysis, index optimization - complete procedure

## Replication Lag (580 tokens)
Monitoring, root causes, fixes - complete procedure
```

**Why This Works**: Each 400-900 token section is retrievable independently, contains complete context, and has clear semantic boundaries.

### Example 2: Multi-Strategy Wiki
An enterprise wiki might use:
- **Layout-Aware Hierarchical** for 4,000 runbooks
- **Code-Aware** for 3,000 Terraform/K8s files
- **Fixed-Size Sliding** for 2,000 log examples
- **Recursive Splitter** as fallback for 1,000 mixed documents

**Why This Works**: Content-specific strategies maximize retrieval quality per document type.

## Performance Benchmarks (Educational Context)

These metrics illustrate the quality difference between approaches:

### Traditional Fixed-Size Chunking
- Recall@10: 0.62
- Precision@10: 0.45
- Hallucination Rate: 23%

### Layout-Aware Hierarchical + 3-Stage Retrieval
- Recall@10: 0.87 (+40%)
- Precision@10: 0.79 (+76%)
- Hallucination Rate: 8% (-65%)

**Learning**: Structure-aware approaches dramatically improve retrieval quality.

## When Editing These Materials

### Current Phase: Research-Based Documents
The three existing documents (`rag_implementation_specs.md`, `wiki_content_strategy.md`, `technique_deep_dive.md`) are comprehensive technical resources awaiting research findings. When updating:

- Maintain real-world examples from SRE/DevOps contexts
- Include "Why This Works" explanations, not just "how to"
- Provide concrete metrics and benchmarks where possible
- Use realistic technical scenarios (K8s, Terraform, databases, monitoring)
- Show both "bad" and "good" approaches with clear explanations
- Include token counts and latency numbers for educational context

### Future Phase: Modular Educational Content
When evolving to numbered modules (similar to ce101):

- Break content into progressive learning modules (01-xxx.md, 02-xxx.md, etc.)
- Each module should be completable in 30-60 minutes
- Include practical exercises and real-world scenarios
- Create clear learning objectives for each module
- Build concepts progressively (each module builds on previous ones)
- Consider creating supporting materials (quick reference cards, example prompts, etc.)

### General Content Principles
New or updated content should teach:
- **Concepts** (why certain approaches work)
- **Trade-offs** (cost vs quality, latency vs accuracy)
- **Decision frameworks** (how to choose between options)
- **Real-world patterns** (concrete examples from production systems)

## Key Questions This Curriculum Answers

1. **Why do traditional RAG systems hallucinate?** → Context fragmentation from naive chunking
2. **What's special about 400-900 tokens?** → Semantic completeness without noise
3. **Why use abstracts?** → Enable hierarchical filtering before full-text retrieval
4. **When should I use code-aware chunking?** → For IaC, manifests, and application code
5. **How do I structure runbooks for RAG?** → Clear sections, 400-900 tokens, hierarchical headers
6. **What's the ROI of better chunking?** → 65% reduction in hallucinations, 76% better precision
7. **How much does this cost?** → ~$1,540/month for 10K documents with 10K queries
8. **Can I use one chunking strategy for everything?** → No - content type determines strategy

## Educational Goals

After studying these materials, you should be able to:
- ✓ Evaluate your wiki structure for RAG readiness
- ✓ Select appropriate chunking strategies for different content types
- ✓ Understand why dual-storage (abstracts + full text) reduces hallucinations
- ✓ Design 3-stage retrieval pipelines
- ✓ Structure documentation for both human and LLM consumption
- ✓ Make informed cost-quality tradeoffs in RAG system design
- ✓ Apply layout-aware hierarchical principles to your content

This is **education through architecture** - learn by understanding how production systems should be designed, then apply those principles to your own context.
