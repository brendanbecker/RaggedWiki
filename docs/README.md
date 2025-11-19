# RaggedWiki Documentation

**Version:** Modular Curriculum (2025)
**Status:** All core modules complete

Welcome to RaggedWiki—an educational curriculum teaching enterprise-grade RAG (Retrieval-Augmented Generation) for Site Reliability Engineering and DevOps knowledge bases.

## Quick Start

**New to RAG or RAG failures?**
→ Start with [Module 00: Overview](00-overview.md) → [Module 01: Why RAG Fails](01-why-rag-fails.md)

**Building a RAG system right now?**
→ Read [Module 01: Why RAG Fails](01-why-rag-fails.md) → [Module 02: Chunking Strategies](02-chunking-strategies.md) → [Module 04: Retrieval Architecture](04-retrieval-architecture.md) → [Module 08: Implementation Guide](08-implementation-guide.md)

**Restructuring wiki content for RAG?**
→ Focus on [Module 02: Chunking Strategies](02-chunking-strategies.md) → [Module 09: SRE-Specific Considerations](09-sre-specific-considerations.md) → [Module 10: Decision Trees](10-decision-trees.md)

**Need a specific answer?**
→ Use [Module 10: Decision Trees](10-decision-trees.md) for quick-reference flowcharts

---

## Complete Module List

### Foundation (Start Here)

**[00: Overview](00-overview.md)** — 10-15 minutes
Curriculum orientation, learning paths, prerequisites, and philosophy

**[01: Why RAG Fails](01-why-rag-fails.md)** — 30-45 minutes
Five fundamental failure modes: context fragmentation, vocabulary mismatch, lost-in-the-middle, stale content, chunk boundary problems

**[02: Chunking Strategies](02-chunking-strategies.md)** — 45-60 minutes
The four chunking approaches (Layout-Aware Hierarchical, Code-Aware, Fixed-Size Sliding, Recursive Splitter) and when to use each

### Core Architecture

**[03: Embedding Fundamentals](03-embedding-fundamentals.md)** — 40-50 minutes
Embedding model selection criteria, when to fine-tune, multi-vector approaches, and domain adaptation strategies

**[04: Retrieval Architecture](04-retrieval-architecture.md)** — 50-60 minutes
Multi-stage retrieval pipelines: BM25 + dense vectors + reranking; hybrid search design; late interaction models

**[05: Advanced Patterns](05-advanced-patterns.md)** — 45-60 minutes
Self-RAG, multi-hop retrieval, query transformation, contextual compression, and when complexity is justified

### Production & Operations

**[06: Production Deployment](06-production-deployment.md)** — 60-75 minutes
Incremental indexing, deduplication strategies, monitoring approaches, scaling patterns, cost optimization

**[07: Evaluation Approach](07-evaluation-approach.md)** — 60-75 minutes
Building validation datasets, retrieval and generation metrics, human-in-the-loop evaluation, continuous quality monitoring

### Implementation & Reference

**[08: Implementation Guide](08-implementation-guide.md)** — 60-75 minutes
Concrete schemas (PostgreSQL, Elasticsearch, vector DBs), processing pipelines, technology selection criteria, reference architecture

**[09: SRE-Specific Considerations](09-sre-specific-considerations.md)** — 60-75 minutes
Runbooks, post-mortems, IaC (Terraform/Ansible/K8s), logs and stack traces, alert documentation patterns

**[10: Decision Trees](10-decision-trees.md)** — 30-40 minutes
Quick-reference flowcharts for chunking strategy selection, retrieval architecture choices, troubleshooting guides

---

## Learning Paths

### Path 1: Wiki Architects & Content Strategists

**Your Goal:** Structure wikis to work optimally for both human readers and LLM retrieval.

**Recommended Sequence:**
1. [Module 00: Overview](00-overview.md) — Understand the curriculum approach
2. [Module 01: Why RAG Fails](01-why-rag-fails.md) — Learn what goes wrong with poor structure
3. [Module 02: Chunking Strategies](02-chunking-strategies.md) — Apply the Four Pillars framework to your content
4. [Module 09: SRE-Specific Considerations](09-sre-specific-considerations.md) — See real-world wiki restructuring patterns
5. [Module 10: Decision Trees](10-decision-trees.md) — Use flowcharts to audit existing content

**Key Outcomes:**
- Understand how document structure impacts retrieval quality
- Apply content-specific chunking strategies (runbooks vs. IaC vs. logs)
- Restructure wiki sections for semantic completeness
- Write documentation that reduces hallucinations

**Time Investment:** 4-5 hours

---

### Path 2: RAG System Implementers

**Your Goal:** Build production-quality RAG systems with informed technical choices.

**Recommended Sequence:**
1. [Module 00: Overview](00-overview.md) — Curriculum orientation
2. [Module 01: Why RAG Fails](01-why-rag-fails.md) — Understand failure modes
3. [Module 02: Chunking Strategies](02-chunking-strategies.md) — Match chunking to content types
4. [Module 03: Embedding Fundamentals](03-embedding-fundamentals.md) — Select embedding models
5. [Module 04: Retrieval Architecture](04-retrieval-architecture.md) — Design multi-stage pipelines
6. [Module 08: Implementation Guide](08-implementation-guide.md) — Build concrete schemas and pipelines
7. [Module 05: Advanced Patterns](05-advanced-patterns.md) — Learn when complexity is justified
8. [Module 06: Production Deployment](06-production-deployment.md) — Plan for scale and cost
9. [Module 07: Evaluation Approach](07-evaluation-approach.md) — Measure quality continuously
10. [Module 10: Decision Trees](10-decision-trees.md) — Quick reference for architecture decisions

**Key Outcomes:**
- Design 3-stage retrieval pipelines (BM25 + dense + reranking)
- Select embedding models based on domain characteristics
- Build metadata-rich storage schemas
- Balance cost, latency, and quality trade-offs
- Implement deduplication and incremental indexing
- Create validation datasets and monitor quality

**Time Investment:** 8-10 hours

---

### Path 3: Technical Writers & SRE Documentation Teams

**Your Goal:** Write documentation that works for both human troubleshooting and LLM retrieval.

**Recommended Sequence:**
1. [Module 00: Overview](00-overview.md) — Understand the approach
2. [Module 01: Why RAG Fails](01-why-rag-fails.md) — See why structure matters
3. [Module 02: Chunking Strategies](02-chunking-strategies.md) — Focus on SRE content examples
4. [Module 09: SRE-Specific Considerations](09-sre-specific-considerations.md) — Learn runbook and post-mortem patterns
5. [Module 10: Decision Trees](10-decision-trees.md) — Apply quick-reference guides

**Key Outcomes:**
- Structure runbooks for retrieval completeness
- Write sections that work as self-contained units
- Understand token sizing guidelines and their rationale
- Apply formatting patterns that reduce hallucinations
- Organize post-mortems for effective retrieval

**Time Investment:** 3-4 hours

---

## Module Dependencies

```
00-overview (START HERE)
    ↓
01-why-rag-fails (REQUIRED FOR ALL PATHS)
    ↓
02-chunking-strategies (REQUIRED FOR ALL PATHS)
    ├─→ 03-embedding-fundamentals
    │       ↓
    │   04-retrieval-architecture
    │       ├─→ 05-advanced-patterns
    │       └─→ 08-implementation-guide
    │               ↓
    │           06-production-deployment
    │               ↓
    │           07-evaluation-approach
    │
    └─→ 09-sre-specific-considerations
            ↓
        10-decision-trees (QUICK REFERENCE)
```

**Reading in order (00 → 10) builds concepts progressively.**
**Jumping to specific modules for targeted needs is also supported.**

---

## What This Curriculum Teaches

### Concepts Over Benchmarks
We explain **why** certain approaches work, not just **what** percentages they achieve. You'll learn decision criteria, not vendor comparisons.

### Trade-offs Over Prescriptions
Every design choice has costs and benefits. We present these explicitly so you can make informed decisions for your context.

### Real-World Patterns
Examples come from actual SRE environments: Kubernetes manifests, Terraform code, database runbooks, post-mortems, alert documentation.

### Failure-First Learning
Understanding how and why RAG fails (Module 01) informs every subsequent design decision. We teach you to recognize and prevent failure modes.

---

## Curriculum Philosophy

1. **Teach WHY, not WHAT** — Understand mechanisms, not just recipes
2. **Emphasize trade-offs, not absolutes** — There are no universal best practices
3. **Focus on decision criteria, not benchmarks** — Learn to evaluate for your domain
4. **Use real-world patterns** — Apply concepts directly to production systems

---

## Source Research

The deep research documents that informed this curriculum are available in [`deepresearch/`](deepresearch/) for additional context and reference material.

---

## Feedback & Contributions

This is a living educational resource. Contributions are welcome for:
- Clarifying concepts
- Adding real-world examples
- Improving teaching approach
- Correcting errors or updating information

---

## What Success Looks Like

After completing this curriculum, you should be able to:

✓ **Identify failure modes** in your current or planned RAG system
✓ **Select chunking strategies** based on content characteristics
✓ **Design multi-stage retrieval pipelines** with informed trade-offs
✓ **Structure documentation** for both humans and LLMs
✓ **Make informed technology choices** based on requirements, not marketing
✓ **Communicate trade-offs** clearly to stakeholders
✓ **Debug RAG failures** systematically (retrieval vs. generation)
✓ **Avoid cargo-culting** — understand *why* you're choosing each approach

---

## Ready to Begin?

**Start here:** [Module 00: Overview](00-overview.md)

Or jump directly to [Module 01: Why RAG Fails](01-why-rag-fails.md) if you're already familiar with RAG concepts.
