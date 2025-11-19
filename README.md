# RaggedWiki

**An educational curriculum teaching enterprise-grade RAG for SRE and DevOps knowledge bases**

**Status:** All 11 core modules complete | [View Full Curriculum →](docs/README.md)

---

## What Is RaggedWiki?

RaggedWiki is a modular curriculum that teaches how to build Retrieval-Augmented Generation (RAG) systems that actually work in production—particularly for Site Reliability Engineering (SRE) and DevOps environments.

This curriculum focuses on **understanding why RAG systems fail**, **when different techniques are appropriate**, and **what trade-offs you're making** with each design decision.

## Quick Start

**New to RAG or RAG failures?**
→ Start with [Module 00: Overview](docs/00-overview.md) → [Module 01: Why RAG Fails](docs/01-why-rag-fails.md)

**Building a RAG system right now?**
→ Read [Module 01: Why RAG Fails](docs/01-why-rag-fails.md) → [Module 02: Chunking Strategies](docs/02-chunking-strategies.md) → [Module 04: Retrieval Architecture](docs/04-retrieval-architecture.md) → [Module 08: Implementation Guide](docs/08-implementation-guide.md)

**Restructuring wiki content for RAG?**
→ Focus on [Module 02: Chunking Strategies](docs/02-chunking-strategies.md) → [Module 09: SRE-Specific Considerations](docs/09-sre-specific-considerations.md) → [Module 10: Decision Trees](docs/10-decision-trees.md)

**Need a quick answer?**
→ Use [Module 10: Decision Trees](docs/10-decision-trees.md) for flowcharts

---

## Complete Module List

### Foundation (Start Here)

- **[00: Overview](docs/00-overview.md)** (10-15 min) — Curriculum orientation, learning paths, prerequisites
- **[01: Why RAG Fails](docs/01-why-rag-fails.md)** (30-45 min) — Five fundamental failure modes
- **[02: Chunking Strategies](docs/02-chunking-strategies.md)** (45-60 min) — Four approaches and decision framework

### Core Architecture

- **[03: Embedding Fundamentals](docs/03-embedding-fundamentals.md)** (40-50 min) — Model selection and fine-tuning
- **[04: Retrieval Architecture](docs/04-retrieval-architecture.md)** (50-60 min) — Multi-stage pipelines
- **[05: Advanced Patterns](docs/05-advanced-patterns.md)** (45-60 min) — Self-RAG, multi-hop, query transformation

### Production & Operations

- **[06: Production Deployment](docs/06-production-deployment.md)** (60-75 min) — Scaling, cost, deduplication
- **[07: Evaluation Approach](docs/07-evaluation-approach.md)** (60-75 min) — Validation and monitoring

### Implementation & Reference

- **[08: Implementation Guide](docs/08-implementation-guide.md)** (60-75 min) — Schemas, pipelines, reference architecture
- **[09: SRE-Specific Considerations](docs/09-sre-specific-considerations.md)** (60-75 min) — Runbooks, IaC, logs, post-mortems
- **[10: Decision Trees](docs/10-decision-trees.md)** (30-40 min) — Quick-reference flowcharts

**[→ View Full Curriculum Documentation](docs/README.md)** for learning paths and module details

---

## Three Learning Paths

### 1. Wiki Architects & Content Strategists (4-5 hours)
Structure wikis for optimal human and LLM retrieval
**Path:** Modules 00 → 01 → 02 → 09 → 10

### 2. RAG System Implementers (8-10 hours)
Build production-quality RAG systems with informed choices
**Path:** All modules 00-10 in sequence

### 3. Technical Writers & SRE Teams (3-4 hours)
Write documentation that works for both humans and RAG
**Path:** Modules 00 → 01 → 02 → 09 → 10

**[→ Full learning path details](docs/README.md#learning-paths)**

---

## Repository Contents

- **[`docs/`](docs/)** — Complete modular curriculum (11 modules + navigation)
  - **[`docs/README.md`](docs/README.md)** — Master curriculum navigation
  - **[`docs/archive/`](docs/archive/)** — Original research documents (preserved for reference)
- **[`sre_wiki_example/`](sre_wiki_example/)** — Example wiki structure following RAG best practices
- **[`PROGRESS.md`](PROGRESS.md)** — Project status and completion tracking
- **[`CLAUDE.md`](CLAUDE.md)** — Guidance for Claude Code when working with this repository

---

## What You'll Learn

After completing this curriculum, you'll be able to:

✓ **Identify failure modes** in your current or planned RAG system
✓ **Select chunking strategies** based on content characteristics
✓ **Design multi-stage retrieval pipelines** with informed trade-offs
✓ **Structure documentation** for both humans and LLMs
✓ **Make informed technology choices** based on requirements, not marketing
✓ **Communicate trade-offs** clearly to stakeholders
✓ **Debug RAG failures** systematically (retrieval vs. generation)
✓ **Avoid cargo-culting** — understand *why* you're choosing each approach

---

## Curriculum Philosophy

- **Teach WHY, not WHAT** — Understand mechanisms, not just recipes
- **Emphasize trade-offs, not absolutes** — No universal best practices
- **Focus on decision criteria, not benchmarks** — Learn to evaluate for your domain
- **Use real-world patterns** — Apply concepts to production systems

---

## Getting Started

**[Start with Module 00: Overview →](docs/00-overview.md)**

Or jump to [Module 01: Why RAG Fails](docs/01-why-rag-fails.md) if you're already familiar with RAG concepts.

---

## Previous Documentation

The original comprehensive research documents have been preserved in [`docs/archive/`](docs/archive/) with a [migration guide](docs/archive/DEPRECATED.md) explaining how content maps to the new modular curriculum.

---

## License & Contributions

This is an educational resource maintained as a living document. If you find gaps, unclear explanations, or opportunities to improve the teaching approach, contributions are welcome.

See [PROGRESS.md](PROGRESS.md) for contribution guidelines and feedback mechanisms.
