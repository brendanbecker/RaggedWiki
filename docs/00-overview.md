# RaggedWiki: Enterprise RAG for SRE Knowledge

**Reading Time:** 10-15 minutes

## What Is RaggedWiki?

RaggedWiki is an educational curriculum that teaches how to build Retrieval-Augmented Generation (RAG) systems that actually work in production—particularly for Site Reliability Engineering (SRE) and DevOps environments.

This is not a collection of benchmark comparisons or performance claims. Instead, RaggedWiki focuses on **understanding why RAG systems fail**, **when different techniques are appropriate**, and **what trade-offs you're making** with each design decision.

## Who Is This For?

### Learning Path 1: Wiki Architects & Content Strategists
**Your Goal:** Structure wikis to work optimally for both human readers and LLM retrieval systems.

**What You'll Learn:**
- How document structure impacts retrieval quality
- Why certain organizational patterns enable better RAG performance
- Decision frameworks for wiki reorganization
- Content-specific patterns for runbooks, post-mortems, and technical documentation

**Start Here:** Module 01 (Why RAG Fails) → Module 02 (Chunking Strategies)

### Learning Path 2: RAG System Implementers
**Your Goal:** Build production-quality RAG systems with informed technical choices.

**What You'll Learn:**
- Multi-stage retrieval pipeline architecture
- Embedding model selection criteria (not benchmarks)
- Storage schema design for metadata-rich retrieval
- Cost vs. quality vs. latency trade-off analysis

**Start Here:** Module 01 (Why RAG Fails) → Module 02 (Chunking Strategies) → Jump to implementation modules as they become available

### Learning Path 3: Technical Writers & SRE Documentation Teams
**Your Goal:** Write documentation that works well for both human troubleshooting and LLM retrieval.

**What You'll Learn:**
- How to structure runbooks for retrieval completeness
- Section sizing guidelines (and the reasoning behind them)
- Why certain formatting patterns reduce hallucinations
- Real-world examples from SRE contexts

**Start Here:** Module 01 (Why RAG Fails) → Module 02 (Chunking Strategies, focus on SRE examples)

## Prerequisites

You should understand:
- **What RAG is:** Retrieval-Augmented Generation as a pattern for grounding LLM responses in retrieved documents
- **Basic LLM concepts:** Prompts, context windows, hallucinations
- **Vector databases (conceptually):** Storing embeddings and similarity search

You do NOT need:
- Machine learning expertise
- Deep mathematical understanding of embeddings
- Production RAG experience (that's what you're here to learn!)

## Learning Objectives

By completing this curriculum, you will be able to:

### Understand Failure Modes
- Explain why naive RAG systems produce incomplete or incorrect answers
- Identify which failure mode is affecting your system
- Recognize the difference between retrieval failures and generation failures

### Make Informed Design Decisions
- Select appropriate chunking strategies based on content characteristics
- Evaluate when advanced patterns (multi-hop, reranking) justify their complexity
- Balance cost, latency, and quality for your specific requirements

### Structure Content for RAG
- Organize documentation to maximize retrieval accuracy
- Write sections that work as self-contained retrieval units
- Apply the Four Pillars framework to audit existing content

### Avoid Common Pitfalls
- Understand why "just use fixed-size chunks" fails
- Recognize when benchmark numbers don't generalize
- Distinguish between what matters (concepts) and what doesn't (isolated percentages)

## The RaggedWiki Philosophy

### We Teach WHY, Not WHAT
Instead of saying "use 512-token chunks," we explain why chunk size impacts semantic completeness and retrieval precision, helping you choose the right size for your context.

### We Emphasize Trade-offs, Not Absolutes
Every decision in RAG has costs and benefits. We present these explicitly so you can make choices appropriate for your environment, requirements, and constraints.

### We Focus on Decision Criteria, Not Benchmarks
Benchmark results don't transfer across domains. We teach you how to evaluate approaches for your specific content, queries, and quality requirements.

### We Use Real-World Patterns
Examples come from actual SRE contexts: runbooks, post-mortems, IaC, logs, incidents. The patterns you learn apply directly to production engineering knowledge bases.

## Module Overview

### Foundation Modules (Weeks 1-2)

**Module 00: Overview** (this document)
- Orient yourself to the curriculum
- Select your learning path
- Understand learning objectives

**Module 01: Why RAG Fails**
- Explore common failure modes in depth
- Understand the mechanisms behind each failure
- See real-world anonymized examples from SRE contexts

**Module 02: Chunking Strategies**
- Learn the four fundamental chunking approaches
- Apply the Four Pillars decision framework
- Map strategies to SRE content types with clear trade-offs

### Core Architecture Modules (Future)

**Module 03: Embedding Fundamentals**
- Selection criteria for embedding models
- When (and when not) to fine-tune
- Multi-vector and hierarchical approaches

**Module 04: Retrieval Architecture**
- Multi-stage pipeline patterns
- Hybrid search rationale
- Reranking trade-offs

**Module 08: Implementation Guide**
- Concrete schemas and pipelines
- Technology selection criteria
- Complete reference architecture

### Advanced & Operational Modules (Future)

**Module 05: Advanced Patterns**
- Self-RAG and multi-hop retrieval
- Query transformation techniques
- When complexity is justified

**Module 06: Production Deployment**
- Incremental indexing strategies
- Deduplication approaches
- Scaling and cost optimization

**Module 09: SRE-Specific Considerations**
- IaC and code repository patterns
- Log and stack trace handling
- Runbook and post-mortem structure

### Validation & Reference (Future)

**Module 07: Evaluation Approach**
- Building validation datasets
- Metrics that matter
- Continuous quality monitoring

**Module 10: Decision Trees**
- Quick reference flowcharts
- Common decision patterns
- Troubleshooting guides

## How to Use This Curriculum

### For Self-Paced Learning
1. Read modules in order (01 → 02 → 03...)
2. Each module builds on concepts from previous modules
3. Expect 30-60 minutes per module (except this overview)
4. Take notes on how concepts apply to your specific environment

### For Team Study
1. Assign modules as pre-reading before design discussions
2. Use the "When to Use" sections to drive technology selection
3. Reference decision frameworks when evaluating vendors or approaches
4. Adapt SRE examples to your domain's specific content types

### For Architecture Planning
1. Use the failure modes (Module 01) to audit your current system
2. Apply the Four Pillars framework (Module 02) to classify your content
3. Map your requirements to the trade-offs presented in each module
4. Build a decision document citing specific trade-offs and criteria

## What This Curriculum Is NOT

This is **not** a vendor comparison. We explain decision criteria; you evaluate vendors against those criteria.

This is **not** a benchmark leaderboard. We explain why certain patterns work; you validate them in your domain.

This is **not** a step-by-step tutorial. We teach concepts and trade-offs; you adapt them to your stack and requirements.

This is **not** prescriptive. We don't tell you "always use X." We tell you "X works well when [conditions], but trades off [costs] for [benefits]."

## What Success Looks Like

After completing this curriculum, you should:

- **Stop cargo-culting:** Understand why you're choosing each component, not just copying what worked for someone else
- **Communicate trade-offs:** Explain to stakeholders why you're prioritizing quality over cost (or vice versa) with clear reasoning
- **Debug failures systematically:** Identify whether issues stem from chunking, retrieval, or generation
- **Make informed choices:** Select technologies and patterns based on your requirements, not marketing claims

## Getting Started

**Immediate next step:** Read [Module 01: Why RAG Fails](01-why-rag-fails.md)

Understanding failure modes is the foundation for every other decision in RAG architecture. Once you understand what can go wrong and why, the rest of the curriculum will make intuitive sense.

---

**Next Module:** [Module 01: Why RAG Fails](01-why-rag-fails.md) — Explore the five fundamental failure modes in depth
