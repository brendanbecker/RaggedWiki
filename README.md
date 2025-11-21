# RaggedWiki

**An educational curriculum teaching enterprise-grade RAG for SRE and DevOps knowledge bases**

**Status:** All 11 core modules complete | [View Full Curriculum →](docs/README.md)

---

## What Is RaggedWiki?

RaggedWiki is a modular curriculum that teaches how to build Retrieval-Augmented Generation (RAG) systems that actually work in production—particularly for Site Reliability Engineering (SRE) and DevOps environments.

This curriculum focuses on **understanding why RAG systems fail**, **when different techniques are appropriate**, and **what trade-offs you're making** with each design decision.

## Quick Start

**Want to try the RAG system immediately? (5 minutes)**
→ See **[QUICKSTART.md](QUICKSTART.md)** → Run the working RAG system and query example docs

**New to RAG or RAG failures?**
→ Start with [Module 00: Overview](docs/00-overview.md) → [Module 01: Why RAG Fails](docs/01-why-rag-fails.md)

**Building a RAG system right now?**
→ Read [Module 01: Why RAG Fails](docs/01-why-rag-fails.md) → [Module 02: Chunking Strategies](docs/02-chunking-strategies.md) → [Module 04: Retrieval Architecture](docs/04-retrieval-architecture.md) → [Module 08: Implementation Guide](docs/08-implementation-guide.md)

**Restructuring wiki content for RAG?**
→ Focus on [Module 02: Chunking Strategies](docs/02-chunking-strategies.md) → [Module 09: SRE-Specific Considerations](docs/09-sre-specific-considerations.md) → [Module 10: Decision Trees](docs/10-decision-trees.md)

**Want to see chunking strategies in action?**
→ Explore [chunking_examples/](chunking_examples/) for side-by-side comparisons

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

### 📚 Educational Materials

- **[`docs/`](docs/)** — Complete modular curriculum (11 modules + navigation)
  - **[`docs/README.md`](docs/README.md)** — Master curriculum navigation with learning paths
  - **[`docs/00-overview.md`](docs/00-overview.md)** through **[`docs/10-decision-trees.md`](docs/10-decision-trees.md)** — 11 progressive modules
  - **[`docs/deepresearch/`](docs/deepresearch/)** — Source research documents that informed the curriculum

### 🛠️ Practical Implementation

- **[`simple_rag_system/`](simple_rag_system/)** — **Working RAG system** (Python + sentence-transformers + ChromaDB)
  - **[`simple_rag_system/README.md`](simple_rag_system/README.md)** — Complete system documentation
  - **[`simple_rag_system/TESTING.md`](simple_rag_system/TESTING.md)** — Step-by-step verification guide (568 lines)
  - **[`simple_rag_system/SETUP.md`](simple_rag_system/SETUP.md)** — Setup options and troubleshooting
  - Local embeddings, no API keys required, fully reproducible

### 📝 Examples & References

- **[`sre_wiki_example/`](sre_wiki_example/)** — **17 realistic SRE documents** structured for optimal RAG
  - Runbooks, how-to guides, incident postmortems, process docs, service overviews
  - All follow 400-900 token section sizing and layout-aware principles

- **[`chunking_examples/`](chunking_examples/)** — **Side-by-side chunking demonstrations**
  - Naive fixed-size (wrong approach) vs. layout-aware (correct) vs. abstract-first (advanced)
  - Token counts, retrieval simulations, and detailed analysis for each

### 💡 Planning & Future Work

- **[`future_features/`](future_features/)** — Enhancement roadmap and feature ideas
  - Validation tools, advanced retrieval patterns, evaluation framework, integrations

- **[`QUICKSTART.md`](QUICKSTART.md)** — 5-minute quick start to try the RAG system

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

## What's Included

### 📖 Theory + Practice

- **11-module curriculum** (8-10 hours) teaching RAG fundamentals through advanced patterns
- **Working RAG implementation** demonstrating concepts in real code
- **17 example documents** showing proper structure and metadata
- **Side-by-side chunking comparisons** with retrieval simulations
- **568-line testing guide** for hands-on verification

### 🎯 Real-World Focus

All examples use realistic SRE/DevOps content:
- Kubernetes troubleshooting runbooks
- Database failover procedures
- Incident postmortems with RCA
- On-call rotation guides
- Prometheus monitoring setup
- Service architecture overviews

### 🚀 Production-Ready Patterns

- Layout-aware hierarchical chunking (not naive fixed-size)
- Dual-storage model (abstracts + full sections)
- Metadata-rich schemas for filtering
- Multi-stage retrieval (BM25 + dense + reranking)
- Cost optimization strategies
- Evaluation frameworks

---

## Curriculum Philosophy

- **Teach WHY, not WHAT** — Understand mechanisms, not just recipes
- **Emphasize trade-offs, not absolutes** — No universal best practices
- **Focus on decision criteria, not benchmarks** — Learn to evaluate for your domain
- **Use real-world patterns** — Apply concepts to production systems

---

## Getting Started

### Hands-On (Recommended for First-Time Visitors)

1. **[Try the RAG System →](QUICKSTART.md)** (5 minutes)
   ```bash
   cd simple_rag_system && source ./activate-venv.sh
   python ingest.py --input ../sre_wiki_example
   python query.py --query "How do I restart the auth service?"
   ```

2. **[Explore Chunking Examples →](chunking_examples/)** (10 minutes)
   - See side-by-side comparisons of naive vs. layout-aware chunking
   - Understand why 400-900 token sections work better

3. **[Read Why RAG Fails →](docs/01-why-rag-fails.md)** (30 minutes)
   - Learn the five fundamental failure modes
   - Understand what you just saw in action

### Conceptual (For Deep Understanding)

**[Start with Module 00: Overview →](docs/00-overview.md)**

Or jump to [Module 01: Why RAG Fails](docs/01-why-rag-fails.md) if you're already familiar with RAG concepts, then work through the curriculum modules sequentially.

---

## Source Research

The deep research documents that informed this curriculum are available in [`docs/deepresearch/`](docs/deepresearch/) for reference and additional context.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributions

This is an educational resource maintained as a living document. If you find gaps, unclear explanations, or opportunities to improve the teaching approach, contributions are welcome.
