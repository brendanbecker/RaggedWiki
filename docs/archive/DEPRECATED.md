# Deprecated Documentation

**Status:** Archived (November 2024)
**Replacement:** Modular curriculum in parent directory

---

## What Happened

These documents were the original comprehensive guides that formed the foundation of RaggedWiki. They contained deep technical content covering:

- **technique_deep_dive.md** — Layout-aware hierarchical chunking mechanics, 3-stage retrieval pipelines, dual-storage models
- **wiki_content_strategy.md** — Content-aware chunking strategy selection, the Four Pillars framework, SRE-specific patterns
- **rag_implementation_specs.md** — Enterprise RAG architecture blueprints, schema designs, cost modeling, processing pipelines

These documents were **research-dense, comprehensive, and authoritative**—but also **long, intertwined, and challenging for progressive learning**.

---

## Why We Migrated

### The Problem
The original guides were excellent reference material but presented challenges for learners:
- **High cognitive load:** Dense technical content without clear progressive structure
- **Hard to navigate:** Cross-references between documents made it difficult to follow a linear path
- **Mixed audiences:** Content for architects, implementers, and writers was interwoven
- **No clear entry point:** Readers didn't know where to start or what to read in what order

### The Solution
We decomposed the content into **11 focused modules** that:
- **Build progressively:** Each module assumes you've read previous ones
- **Have clear learning paths:** Three distinct paths for different roles
- **Focus on specific topics:** Each module covers one concept deeply
- **Include time estimates:** You know how long each module takes
- **Provide quick reference:** Decision trees and flowcharts for rapid lookup

---

## Migration Mapping

If you were reading the old docs, here's where that content moved:

### technique_deep_dive.md → Modules
- **Why dual-storage works** → [Module 01: Why RAG Fails](../01-why-rag-fails.md) (context fragmentation section)
- **3-stage retrieval pipeline** → [Module 04: Retrieval Architecture](../04-retrieval-architecture.md)
- **Hierarchical chunking mechanics** → [Module 02: Chunking Strategies](../02-chunking-strategies.md)
- **Post-processing techniques** → [Module 05: Advanced Patterns](../05-advanced-patterns.md)
- **Performance characteristics** → [Module 06: Production Deployment](../06-production-deployment.md)

### wiki_content_strategy.md → Modules
- **Four Pillars framework** → [Module 02: Chunking Strategies](../02-chunking-strategies.md)
- **Content type decision matrix** → [Module 10: Decision Trees](../10-decision-trees.md)
- **Runbook/post-mortem patterns** → [Module 09: SRE-Specific Considerations](../09-sre-specific-considerations.md)
- **Chunking strategy selection** → [Module 02: Chunking Strategies](../02-chunking-strategies.md)
- **Token sizing rationale** → [Module 01: Why RAG Fails](../01-why-rag-fails.md) + [Module 02: Chunking Strategies](../02-chunking-strategies.md)

### rag_implementation_specs.md → Modules
- **Vector DB schema design** → [Module 08: Implementation Guide](../08-implementation-guide.md)
- **API contract design** → [Module 08: Implementation Guide](../08-implementation-guide.md)
- **Cost modeling** → [Module 06: Production Deployment](../06-production-deployment.md)
- **Processing pipeline architecture** → [Module 08: Implementation Guide](../08-implementation-guide.md)
- **Technology selection** → [Module 08: Implementation Guide](../08-implementation-guide.md)

---

## Should You Still Read These?

### Use the New Modules If...
- You're learning RAG concepts for the first time
- You want a structured, progressive curriculum
- You prefer focused topics with clear learning objectives
- You're following one of the three learning paths

### Reference the Archived Docs If...
- You need the exact original research that informed the curriculum
- You're conducting deep research and want comprehensive technical detail
- You're familiar with the old structure and want to quickly look something up
- You're comparing the modular curriculum to the original to understand how concepts evolved

---

## Content Preservation

**All original content is preserved.** Nothing was deleted; it was decomposed, reorganized, and expanded into the modular format.

In some cases, content was:
- **Expanded:** More examples, deeper explanations, clearer learning objectives
- **Refactored:** Better organization, progressive complexity, clearer dependencies
- **Augmented:** Additional modules (e.g., Module 07: Evaluation Approach) not present in original docs

The **concepts, principles, and technical accuracy remain identical**—only the presentation changed.

---

## For New Readers

**Do not start here.**

Instead, read the [modular curriculum](../README.md). It's designed for progressive learning and will give you a better educational experience.

These archived documents remain available for:
- **Historical reference**
- **Deep research purposes**
- **Comparison to the modular curriculum**
- **Verifying original sources**

---

## Questions About the Migration?

If you have questions about:
- **Where specific content moved:** See the mapping above or use search across modules
- **Why the curriculum was restructured:** See the [Module 00: Overview](../00-overview.md) philosophy section
- **How to use the new structure:** Read [docs/README.md](../README.md) for learning paths

---

**Last Updated:** November 2024
**Migration Completed By:** RaggedWiki curriculum development team
**New Documentation:** [docs/README.md](../README.md)
