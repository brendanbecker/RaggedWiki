# RaggedWiki Modular Documentation Plan

## Philosophy

Focus on **concepts**, **trade-offs**, **decision frameworks**, and **real-world patterns** rather than benchmark performance claims. We recommend techniques because they are good practice and address specific failure modes, not because they achieve X% improvement in isolated benchmarks.

**Key Principles:**
- Explain **why** techniques work, not just what they are
- Provide **decision criteria** for choosing between approaches
- Emphasize **trade-offs** rather than absolute performance
- Focus on **when to apply** each technique based on use case
- Avoid benchmark percentages that don't generalize across domains

---

## Proposed Module Structure

```
docs/
├── 00-overview.md                      # Project purpose, learning paths, prerequisites
├── 01-why-rag-fails.md                 # Common failure modes, context fragmentation, hallucinations
├── 02-chunking-strategies.md           # Decision matrix, trade-offs, when to use each
├── 03-embedding-fundamentals.md        # How embeddings work, model selection criteria, fine-tuning
├── 04-retrieval-architecture.md        # Hybrid search rationale, multi-stage patterns, trade-offs
├── 05-advanced-patterns.md             # Self-RAG, multi-hop, query transformation (concepts)
├── 06-production-deployment.md         # Scaling, updates, deduplication, operational concerns
├── 07-evaluation-approach.md           # How to validate, what to measure, synthetic datasets
├── 08-implementation-guide.md          # Schemas, pipelines, concrete examples with justification
├── 09-sre-specific-considerations.md   # IaC, logs, stack traces, runbooks, time-series
└── 10-decision-trees.md                # Flowcharts for choosing approaches
```

---

## Module Content Focus

### 00-overview.md
**Purpose:** Orient learners, set expectations, define learning paths

**Content:**
- What is RaggedWiki and who is it for
- Learning objectives for each module
- Prerequisites (basic RAG understanding)
- How to use this curriculum
- Three learning paths:
  - Wiki Architects & Content Strategists
  - RAG System Implementers
  - Technical Writers & SRE Documentation Teams

**Completion Criteria:** 10-15 minutes reading time, clear next steps

---

### 01-why-rag-fails.md
**Purpose:** Establish the problems we're solving, create motivation for best practices

**Content:**
- **Context fragmentation:** Split procedures, lost hierarchies (why it causes hallucinations)
- **Vocabulary mismatch:** Technical terms vs semantic models (exact match vs semantic)
- **Lost-in-the-middle problem:** Model attention distribution in long contexts
- **Duplicate and stale content:** Context pollution, version confusion
- **Chunk boundary problems:** Instructions split mid-step, missing prerequisites
- **Real-world failure examples** (anonymized SRE incidents)

**Emphasis:** Each failure mode explained with **why it happens** and **what goes wrong**, not statistics

**Completion Criteria:** 30-45 minutes, reader understands risks of naive RAG

---

### 02-chunking-strategies.md
**Purpose:** Provide decision framework for selecting chunking approach

**Content:**
- **Layout-Aware Hierarchical**
  - When: Structured docs with headers (Markdown, HTML)
  - Why: Respects document semantics, keeps prerequisites with steps
  - Trade-offs: Requires structure, variable chunk sizes
  - Examples: Runbooks, post-mortems, design docs

- **Code-Aware**
  - When: Syntax-sensitive content (IaC, scripts, configs)
  - Why: Preserves syntactic validity, keeps resources/functions intact
  - Trade-offs: Requires AST parsing, language-specific
  - Examples: Terraform, Kubernetes YAML, shell scripts

- **Semantic Chunking**
  - When: Narrative content without clear structure
  - Why: Detects topic shifts, maintains conceptual coherence
  - Trade-offs: Higher compute cost, requires tuning
  - Examples: Long-form analysis, unstructured reports

- **Fixed-Size Sliding Window**
  - When: No structure available, temporal ordering matters
  - Why: Deterministic, preserves sequential context via overlap
  - Trade-offs: Arbitrary boundaries, may split concepts
  - Examples: Logs, stack traces, time-series data

**Decision Matrix:** Four Pillars of Content Analysis
1. Structure regularity (headers, syntax, schemas)
2. Semantic density (concept changes per paragraph)
3. Query patterns (exact match vs conceptual)
4. Update frequency (static docs vs streaming logs)

**Completion Criteria:** 45-60 minutes, reader can classify their content and select appropriate strategy

---

### 03-embedding-fundamentals.md
**Purpose:** Demystify embeddings, provide selection criteria

**Content:**
- **How embeddings work:** Vector representations of semantic meaning
- **Dense vs sparse vectors:**
  - Dense: Semantic similarity, handles paraphrasing
  - Sparse: Exact keyword matching, high-entropy identifiers
  - Trade-off: Coverage vs precision

- **Model selection criteria:**
  - Domain fit (general vs specialized)
  - Context length (document size limits)
  - Deployment model (API vs self-hosted)
  - Multilingual requirements
  - Fine-tuning availability

- **When to fine-tune:**
  - Highly specialized terminology
  - Proven vocabulary mismatch in evaluation
  - Domain-specific jargon (legal, medical, finance)
  - Trade-offs: Data requirements, maintenance burden, generalization risk

- **Matryoshka embeddings:** Variable-length vectors for hierarchical search
  - Concept: Truncatable vectors (1024d → 512d → 256d)
  - When useful: Multi-stage retrieval, storage optimization

**No benchmark tables** - Focus on "choose based on your domain characteristics"

**Completion Criteria:** 30-45 minutes, reader understands selection criteria for their use case

---

### 04-retrieval-architecture.md
**Purpose:** Explain multi-stage retrieval patterns and their rationale

**Content:**
- **Hybrid search (Dense + Sparse):**
  - Why: Covers semantic paraphrasing AND exact keyword matching
  - Addresses: Vocabulary mismatch, technical identifiers (error codes, configs)
  - Trade-off: Complexity vs coverage
  - When to skip: Simple keyword-only or purely semantic domains

- **Cross-encoder reranking:**
  - Why more accurate: Bidirectional attention on query+document pairs
  - Trade-off: Speed vs accuracy (slower but more precise)
  - When essential: High-stakes decisions, complex technical queries
  - When to skip: High-throughput APIs, simple lookups

- **Multi-vector approaches (ColBERT concept):**
  - Why: Token-level precision for granular matching
  - Trade-off: Index size and complexity vs precision
  - When useful: Exact phrase matching within semantic context

- **Parent-child retrieval:**
  - Concept: Search small, return large
  - Why: Balances precision (small chunks match better) with context (large chunks answer better)
  - Implementation pattern: Child chunks point to parent documents

**Architecture patterns:**
- Single-stage: Direct dense retrieval
- Two-stage: Hybrid retrieval only
- Three-stage: Hybrid + cross-encoder rerank
- Multi-stage with parent-child promotion

**Trade-offs explicitly stated:** Latency vs accuracy, index complexity vs recall quality

**Completion Criteria:** 45-60 minutes, reader can design appropriate retrieval pipeline for their requirements

---

### 05-advanced-patterns.md
**Purpose:** When and why to add complexity beyond basic retrieval

**Content:**
- **Self-RAG (Self-Reflective Retrieval):**
  - Concept: LLM identifies missing information and re-retrieves
  - When useful: Complex queries, incomplete initial retrieval common
  - Trade-offs: Latency (multiple retrieval cycles), cost, complexity
  - Implementation approaches: Detection prompts, iterative refinement

- **Multi-hop reasoning:**
  - Concept: Break complex queries into sub-questions
  - When useful: Questions requiring synthesis across multiple documents
  - Example: "Compare service A and B performance during incident X"
  - Trade-offs: Query planning complexity, multiple retrieval rounds

- **Query transformation:**
  - HyDE (Hypothetical Document Embeddings): Generate fake answer, search for it
  - Multi-query expansion: Rephrase query multiple ways
  - Domain vocabulary alignment: Map user terms to technical terms
  - When useful: Vocabulary mismatch, ambiguous queries
  - Trade-offs: Additional LLM calls, result merging complexity

- **Neighbor chunk expansion:**
  - Concept: Retrieve adjacent chunks to prevent boundary loss
  - When useful: Procedures spanning multiple chunks, context dependencies
  - Trade-offs: More tokens consumed, deduplication complexity

**Decision framework:** When is complexity justified?
- Query complexity (single fact vs multi-document reasoning)
- Acceptable latency (interactive vs batch)
- Failure rate of simple approaches (measured in evaluation)
- Operational maturity (can you maintain it?)

**Completion Criteria:** 30-45 minutes, reader understands when advanced patterns are worth the complexity

---

### 06-production-deployment.md
**Purpose:** Address operational realities of running RAG at scale

**Content:**
- **Incremental indexing:**
  - Why: Re-indexing everything is wasteful and slow
  - Strategies: Content hashing, change detection, upsert operations
  - Trade-offs: Complexity vs efficiency

- **Deduplication:**
  - Exact duplicates: Hash-based detection
  - Near-duplicates: Similarity thresholds
  - Conflicting versions: Temporal ordering, version metadata
  - Why it matters: Context pollution, wasted tokens

- **Version control:**
  - Problem: Yesterday's runbook may be dangerous today
  - Strategies: Temporal metadata, version filtering, deprecation flags
  - Multi-version support: When users need historical data

- **Scaling patterns:**
  - Sharding: Partition by tenant, service, or content type
  - Hierarchical indexing: Document-level then chunk-level retrieval
  - ANN parameter tuning: Recall vs speed trade-offs (HNSW ef, M parameters)
  - When to worry: 100k+ documents, high query volume

- **Cost considerations:**
  - Where costs come from: Embedding APIs, vector storage, compute
  - Optimization strategies: Batch processing, caching, model selection
  - Not specific dollar amounts - focus on cost drivers and levers

- **Content freshness:**
  - TTL policies: Auto-expire outdated content
  - Update propagation: Ensuring changes reach index
  - Staleness detection: Monitoring content age

- **Monitoring and observability:**
  - What to track: Query latency, retrieval quality, index health
  - Red flags: Increasing zero-result queries, latency spikes
  - Debugging approaches: Query logging, result inspection

**Completion Criteria:** 45-60 minutes, reader has operational playbook for production deployment

---

### 07-evaluation-approach.md
**Purpose:** How to validate RAG quality without relying on benchmarks

**Content:**
- **What to measure:**
  - Recall@K: Did we find relevant information in top K results?
  - MRR (Mean Reciprocal Rank): How early does first relevant result appear?
  - Context completeness: Did we retrieve all necessary pieces?
  - Answer quality: Did LLM produce correct response?

- **How to validate:**
  - **Synthetic datasets:** LLM-generated queries from documents
    - Pros: Scalable, covers corpus
    - Cons: May not match real user queries
  - **Human evaluation:** Subject matter experts judge relevance
    - Pros: Ground truth
    - Cons: Expensive, doesn't scale
  - **A/B testing:** Compare retrieval approaches in production
    - Pros: Real-world validation
    - Cons: Requires traffic, careful isolation
  - **Regression testing:** Ensure quality doesn't degrade over time

- **Building evaluation datasets:**
  - Curate query-document pairs from tickets, logs, real questions
  - Synthetic generation: Prompts for creating test queries
  - Edge cases: Version mismatches, ambiguous queries, missing info

- **Red flags to monitor:**
  - Zero results: Retrieval completely failed
  - Wrong version retrieved: Temporal filtering issues
  - Security leaks: Cross-tenant or access control failures
  - Hallucinations: LLM generates unsupported answers

- **Continuous monitoring (not "achieve 90%"):**
  - Detect degradation when content changes
  - Track query patterns over time
  - Identify systematic gaps in coverage

**Completion Criteria:** 30-45 minutes, reader can build evaluation framework for their domain

---

### 08-implementation-guide.md
**Purpose:** Concrete schemas, pipelines, and technology choices with justifications

**Content:**
- **Schema design:**
  - Dual abstract/full storage rationale
  - Metadata requirements: parent_id, breadcrumbs, temporal bounds
  - Multi-tenant isolation: tenant_id filtering
  - Access control: Stored with vectors to avoid post-filter recall loss

- **Pipeline stages (detailed):**
  1. Document ingestion and parsing
  2. Chunking with strategy selection
  3. Abstract generation (if dual storage)
  4. Embedding generation (batch processing)
  5. Vector indexing with metadata
  6. Quality validation (token counts, structure)

- **Retrieval pipeline stages:**
  1. Query analysis and transformation
  2. Metadata filtering (tenant, time, access)
  3. Hybrid retrieval (dense + sparse)
  4. Result fusion (RRF or weighted)
  5. Cross-encoder reranking
  6. Parent-child promotion (if applicable)
  7. Deduplication and packing
  8. Citation attachment

- **Technology choices (decision criteria, not mandates):**
  - **Vector databases:**
    - "If you need hybrid search built-in, consider Weaviate"
    - "If you have existing PostgreSQL, pgvector is simpler operationally"
    - "If you need multi-tenant isolation guarantees, evaluate filtering performance"

  - **Embedding models:**
    - "If using APIs, newer models generally handle long context better"
    - "If self-hosting, consider model size vs throughput requirements"
    - "If domain-specific, evaluate fine-tuning vs prompt engineering"

  - **Chunking tools:**
    - "For Markdown/HTML, leverage structure-aware parsers"
    - "For code, use AST-based splitters (tree-sitter)"
    - "For unstructured text, RecursiveCharacterTextSplitter is reliable baseline"

- **Example architecture:**
  - Complete stack with justifications for each component
  - Data flow diagrams (Mermaid)
  - Configuration examples (not production secrets)

**Completion Criteria:** 60-90 minutes, reader can implement basic RAG pipeline with informed choices

---

### 09-sre-specific-considerations.md
**Purpose:** Domain-specific patterns for SRE/operations content

**Content:**
- **Infrastructure as Code (Terraform/YAML):**
  - Problem: Syntax fragmentation breaks configurations
  - Solution: AST-based splitting preserves resource blocks
  - Environment metadata: Prevents cross-environment leaks (prod vs staging)
  - Dependency tracking: Link modules and resources

- **System logs:**
  - Problem: No structure, high volume, temporal ordering critical
  - Solution: Sliding window with timestamp anchoring
  - Summary-index pattern: Extract key events, store full log
  - Retention policies: Balance freshness vs volume

- **Stack traces:**
  - Problem: High entropy (hex addresses), non-linguistic
  - Solution: Summary-index (exception type + top frames)
  - Why: Dense embeddings degrade on random tokens
  - Sparse search on exception classes more effective

- **Runbooks and playbooks:**
  - Problem: Prerequisites and steps must stay together
  - Solution: Hierarchical chunking respects sections
  - Parent-child: Quick steps (child) link to full context (parent)
  - Validation: Ensure procedures aren't split mid-step

- **Post-mortems and incident reports:**
  - Problem: Narrative flow, audit requirements
  - Solution: Layout-aware to preserve Executive Summary, Timeline, RCA
  - Temporal tagging: Link to specific incident time ranges
  - Version control: Critical for regulatory compliance

- **Monitoring alerts and oncall documentation:**
  - Problem: Template-based, table-heavy
  - Solution: Per-alert chunking, preserve signal+threshold+response
  - Metadata enrichment: Service, severity, escalation path

**Operational patterns:**
- Freshness requirements (runbooks vs historical incidents)
- Access control (production configs vs public docs)
- Multi-tenant isolation (team-specific knowledge)
- Time-aware retrieval ("current state" vs "what happened")

**Completion Criteria:** 45-60 minutes, SRE teams can structure their wikis optimally

---

### 10-decision-trees.md
**Purpose:** Quick reference flowcharts for common decisions

**Content (Mermaid diagrams):**

- **Flowchart: "Which chunking strategy?"**
  ```
  Does content have consistent structure (headers/syntax)?
    Yes → Is it code/config?
      Yes → Code-Aware (AST-based)
      No → Layout-Aware Hierarchical
    No → Is it narrative prose?
      Yes → Semantic Chunking
      No → Fixed-Size Sliding Window (logs, traces)
  ```

- **Flowchart: "Do I need hybrid search?"**
  ```
  Do queries include exact identifiers (error codes, configs)?
    Yes → Hybrid search recommended
    No → Are queries purely conceptual?
      Yes → Dense-only may suffice
      No → Hybrid search for safety
  ```

- **Flowchart: "When to add cross-encoder reranking?"**
  ```
  Can you accept 100-500ms additional latency?
    No → Skip reranking or use lightweight model
    Yes → Are queries complex/technical?
      Yes → Cross-encoder recommended
      No → Evaluate on quality needs
  ```

- **Flowchart: "Is my retrieval quality degrading?" (debugging)**
  ```
  Check: Zero results increasing?
    Yes → Index completeness issue or vocabulary mismatch
  Check: Wrong version retrieved?
    Yes → Temporal filtering or version metadata issue
  Check: Irrelevant results in top-K?
    Yes → Chunking fragmentation or metadata filtering needed
  Check: Correct chunks retrieved but wrong answer?
    Yes → Context assembly or LLM prompting issue
  ```

- **Flowchart: "Should I use advanced patterns?"**
  ```
  Is basic retrieval failing on complex queries?
    No → Stick with simpler approach
    Yes → What's the failure mode?
      Missing info → Consider Self-RAG
      Multi-document reasoning → Consider Multi-hop
      Vocabulary mismatch → Query transformation
      Context boundaries → Parent-child retrieval
  ```

**Completion Criteria:** 15-20 minutes, quick reference for decision-making

---

## What Gets Removed/De-emphasized

❌ **Remove:** Benchmark percentages ("+12.7% recall improvement")
✅ **Replace with:** "Hybrid search addresses both semantic and exact-match needs, reducing misses from vocabulary mismatch"

❌ **Remove:** Model leaderboard comparisons ("Ada-002 scored 31% vs 44%")
✅ **Replace with:** "Newer models generally handle multilingual and long-context better; evaluate on your domain"

❌ **Remove:** Specific latency numbers ("~200ms retrieval")
✅ **Replace with:** "Cross-encoder reranking adds noticeable latency; acceptable for human-facing queries, problematic for high-throughput APIs"

❌ **Remove:** Cost calculations ("$0.0001 per query")
✅ **Replace with:** "Embedding costs are typically negligible compared to LLM generation; optimize based on your query volume"

---

## What Gets Emphasized

✅ **Trade-offs:** "Small chunks = precise matching but risk losing context; large chunks = complete context but noisier matches"

✅ **Decision criteria:** "If your content has consistent headers (H1, H2, H3), use Layout-Aware; if it's unstructured prose, consider Semantic"

✅ **Failure modes:** "When procedures split mid-step, LLMs hallucinate the missing steps. Parent-child retrieval prevents this."

✅ **Operational patterns:** "Version control matters because yesterday's runbook may be dangerous today. Implement temporal filtering."

✅ **When techniques matter:** "Multi-hop retrieval is overkill for simple lookups but essential for 'compare X and Y' queries spanning documents"

---

## Implementation Phasing

### Phase 1: Foundation Modules (Week 1-2)
**Goal:** Establish core concepts and failure modes

1. `00-overview.md` - Clear learning objectives, no prerequisites beyond RAG basics
2. `01-why-rag-fails.md` - Establish the problems we're solving
3. `02-chunking-strategies.md` - Core decision matrix with trade-offs, no percentages

**Milestone:** Reader understands what can go wrong and basic mitigation strategies

**Status:** ✅ COMPLETED (2025-11-18)
- Created `docs/00-overview.md` with three learning paths and clear objectives
- Created `docs/01-why-rag-fails.md` covering five major failure modes with mechanisms
- Created `docs/02-chunking-strategies.md` with four strategies, decision matrix, and trade-offs

---

### Phase 2: Core Architecture (Week 3-4)
**Goal:** Design retrieval systems with informed choices

4. `03-embedding-fundamentals.md` - Selection criteria, not benchmarks
5. `04-retrieval-architecture.md` - Multi-stage patterns with clear trade-offs
6. `08-implementation-guide.md` - Concrete schemas and pipeline

**Milestone:** Reader can design and implement basic RAG system

**Status:** ✅ COMPLETED (2025-11-18)
- Created `docs/03-embedding-fundamentals.md` covering dense vs sparse vectors, model selection criteria, when to fine-tune, and Matryoshka embeddings
- Created `docs/04-retrieval-architecture.md` covering hybrid search, cross-encoder reranking, parent-child retrieval, and multi-stage architectures
- Created `docs/08-implementation-guide.md` with complete schemas, pipelines, technology selection criteria, and example architectures

---

### Phase 3: Advanced & Operational (Week 5-6)
**Goal:** Handle complexity and production realities

7. `05-advanced-patterns.md` - When complexity is justified
8. `06-production-deployment.md` - Operational realities
9. `09-sre-specific-considerations.md` - Domain-specific patterns

**Milestone:** Reader can operate RAG system in production and handle SRE-specific content

**Status:** ✅ COMPLETED (2025-11-18)
- Created `docs/05-advanced-patterns.md` covering Self-RAG, multi-hop reasoning, query transformation (HyDE, multi-query), neighbor chunk expansion, and decision frameworks for when complexity is justified
- Created `docs/06-production-deployment.md` covering incremental indexing, deduplication strategies, version control, scaling patterns, cost optimization, content freshness, and monitoring/observability
- Created `docs/09-sre-specific-considerations.md` covering IaC chunking (AST-based), system logs (sliding window), stack traces (summary-index pattern), runbooks (layout-aware hierarchical), post-mortems (temporal tagging), monitoring alerts, and operational patterns

---

### Phase 4: Validation & Tools (Week 7-8)
**Goal:** Measure quality and provide quick references

10. `07-evaluation-approach.md` - How to validate quality
11. `10-decision-trees.md` - Quick reference flowcharts

**Milestone:** Complete curriculum with validation framework and decision aids

**Status:** ✅ COMPLETED (2025-11-18)
- Created `docs/07-evaluation-approach.md` covering what to measure (Recall@K, MRR, context completeness, answer quality), validation methods (synthetic datasets, human evaluation, A/B testing, regression testing), building evaluation datasets, red flags (zero results, wrong versions, security leaks, hallucinations), and continuous monitoring approaches
- Created `docs/10-decision-trees.md` with comprehensive Mermaid flowcharts for: (1) chunking strategy selection based on Four Pillars framework, (2) hybrid search decision criteria, (3) cross-encoder reranking trade-offs, (4) debugging quality degradation with root cause analysis, and (5) advanced pattern evaluation with complexity justification

**🎉 CURRICULUM COMPLETE:** All 10 modules implemented. The RaggedWiki modular documentation curriculum is now ready for learners across all three learning paths (Wiki Architects, RAG Implementers, and SRE Documentation Teams).

---

## Migration Strategy from Current Docs

### Current State
```
docs/
├── technique_deep_dive.md
├── wiki_content_strategy.md
└── rag_implementation_specs.md
```

### Migration Approach

**Option A: Clean Slate (Recommended)**
1. Create new `docs/modules/` directory
2. Build modules incrementally (phases above)
3. Keep current docs as `docs/archive/` for reference
4. Update CLAUDE.md to point to new structure
5. Add deprecation notice to old docs

**Option B: Evolutionary**
1. Extract content from existing docs into modules
2. Maintain both structures during transition
3. Gradually deprecate old docs as modules mature
4. Risk: Confusion during transition period

**Recommendation:** Option A for clean break, clear learning path

---

## Success Criteria

Each module should achieve:
- ✅ **30-60 minute reading time** (except overview and decision trees)
- ✅ **Clear learning objective** stated at beginning
- ✅ **No benchmark percentages** unless explaining why they don't generalize
- ✅ **Decision frameworks** with explicit trade-offs
- ✅ **Real-world examples** from SRE context
- ✅ **"When to use"** guidance for every technique
- ✅ **Builds on previous modules** (progressive learning)

Overall curriculum success:
- ✅ **Wiki architects** can structure content optimally
- ✅ **RAG implementers** can build production systems
- ✅ **SRE teams** can maintain high-quality technical knowledge bases
- ✅ **No cargo-culting** of techniques without understanding trade-offs

---

## Maintenance Plan

**Quarterly Review:**
- Update with new techniques (only if they solve real problems)
- Revise based on community feedback
- Add real-world case studies (anonymized)
- Remove techniques that didn't prove valuable

**No benchmark chasing:**
- If new research claims "X% improvement," translate to conceptual understanding
- Focus on "what problem does this solve" not "how much faster is it"

**Community contributions:**
- Accept: Trade-off analysis, failure mode examples, decision criteria
- Reject: Benchmark comparisons, vendor-specific promotions, unvalidated techniques
