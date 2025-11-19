# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

RaggedWiki is an **educational curriculum** that teaches how to use RAG (Retrieval-Augmented Generation) correctly in enterprise environments, and how to structure wikis to work optimally for both human readers and LLM systems.

### Current State
The project now contains a **complete modular curriculum** consisting of 11 progressive modules (00-overview through 10-decision-trees) covering RAG fundamentals, architecture, implementation, and SRE-specific patterns.

**Start here:** [docs/README.md](docs/README.md) for complete navigation and learning paths.

### Documentation Structure
- **Modular curriculum:** `docs/00-*.md` through `docs/10-*.md` (11 modules total)
- **Master navigation:** `docs/README.md` with learning paths for three audiences
- **Archived research:** `docs/archive/` contains the original comprehensive documents that informed the modular curriculum

## Modular Curriculum Overview

The curriculum consists of **11 progressive modules** organized into four phases:

### Foundation Modules (Start Here)
- **Module 00: Overview** — Curriculum orientation, learning paths, prerequisites
- **Module 01: Why RAG Fails** — Five fundamental failure modes in depth
- **Module 02: Chunking Strategies** — Four approaches and the Four Pillars decision framework

### Core Architecture Modules
- **Module 03: Embedding Fundamentals** — Model selection criteria, fine-tuning, multi-vector approaches
- **Module 04: Retrieval Architecture** — Multi-stage pipelines (BM25 + dense + reranking)
- **Module 05: Advanced Patterns** — Self-RAG, multi-hop retrieval, query transformation

### Production & Operations Modules
- **Module 06: Production Deployment** — Incremental indexing, deduplication, scaling, cost optimization
- **Module 07: Evaluation Approach** — Validation datasets, metrics, continuous monitoring

### Implementation & Reference Modules
- **Module 08: Implementation Guide** — Concrete schemas, pipelines, technology selection
- **Module 09: SRE-Specific Considerations** — Runbooks, post-mortems, IaC, logs, alerts
- **Module 10: Decision Trees** — Quick-reference flowcharts and troubleshooting guides

**See [docs/README.md](docs/README.md) for complete module descriptions, time estimates, and learning paths.**

## Three Learning Paths

The curriculum supports three distinct learning paths for different roles. See [docs/README.md](docs/README.md) for complete details.

### Path 1: Wiki Architects & Content Strategists
**Goal:** Structure wikis for optimal human and LLM retrieval

**Module Sequence:**
- Module 00 (Overview) → Module 01 (Why RAG Fails) → Module 02 (Chunking Strategies) → Module 09 (SRE-Specific) → Module 10 (Decision Trees)

**Time Investment:** 4-5 hours
**Key Outcome:** Understand how document structure impacts retrieval; apply content-specific chunking strategies

### Path 2: RAG System Implementers
**Goal:** Build production-quality RAG systems with informed choices

**Module Sequence:**
- Modules 00-10 in order (all modules)

**Time Investment:** 8-10 hours
**Key Outcomes:** Design 3-stage retrieval pipelines, select embedding models, build metadata-rich schemas, balance cost/quality/latency, implement monitoring

### Path 3: Technical Writers & SRE Documentation Teams
**Goal:** Write documentation that works for both humans and RAG

**Module Sequence:**
- Module 00 (Overview) → Module 01 (Why RAG Fails) → Module 02 (Chunking Strategies, focus on SRE examples) → Module 09 (SRE-Specific) → Module 10 (Decision Trees)

**Time Investment:** 3-4 hours
**Key Outcome:** Structure runbooks/post-mortems for retrieval completeness; understand section sizing rationale

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

## When Editing Module Content

The curriculum is now in **modular format**. When updating or extending modules:

### Module Structure Standards
Each module should:
- Have a clear reading time estimate (based on ~200 words/minute for technical content)
- State prerequisites explicitly
- Include "Learning Objectives" or "What You'll Learn" section
- Provide "What's Next" navigation to subsequent modules
- Use real-world SRE/DevOps examples (K8s, Terraform, databases, monitoring, incidents)
- Show both "bad" and "good" approaches with clear explanations
- Focus on **why** (mechanisms) over **what** (prescriptions)

### Content Principles
Module content should teach:
- **Concepts:** Why certain approaches work (mechanisms, not just outcomes)
- **Trade-offs:** Cost vs quality, latency vs accuracy, complexity vs benefit
- **Decision frameworks:** How to choose between options for your context
- **Real-world patterns:** Concrete examples from production systems

### What to Avoid
- **Benchmark percentages without context:** Don't say "X is 40% better" without explaining why and under what conditions
- **Absolute prescriptions:** Avoid "always do X" — explain when X is appropriate and when it's not
- **Vendor-specific recommendations:** Focus on decision criteria, not specific products
- **Unexplained jargon:** Define technical terms or link to definitions

### Adding New Modules
If creating additional modules (11-xxx.md and beyond):
- Maintain the numbering scheme
- Update `docs/README.md` with new module info
- Ensure clear dependencies (what prerequisite modules must be read first)
- Target 30-75 minutes reading time per module
- Consider which learning path(s) the module supports

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
