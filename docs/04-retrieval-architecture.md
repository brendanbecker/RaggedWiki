# Module 04: Retrieval Architecture

## Learning Objectives

After completing this module, you will understand:
- Why hybrid search (dense + sparse) is the production standard for technical content
- How cross-encoder reranking improves precision and when the latency cost is justified
- What multi-vector approaches like ColBERT offer for fine-grained matching
- How parent-child retrieval solves the precision-context trade-off
- The rationale behind multi-stage retrieval architectures
- When to skip complexity and use simpler approaches

**Prerequisites:** Module 03 (Embedding Fundamentals)

**Estimated time:** 50-60 minutes

---

## Why Multi-Stage Retrieval?

### The Single-Stage Problem

**Naive RAG architecture:**
```
User Query → Dense Vector Search → Top-K chunks → Feed to LLM → Answer
```

**What goes wrong:**
1. **Semantic-only search misses technical identifiers**
   - Query: "Fix error 0x80040154" → Dense embeddings conflate error codes
   - Miss: Exact document with this specific error

2. **Top-K includes "near-miss" distractors**
   - Query: "Database connection timeout troubleshooting"
   - Retrieves: "Database connection success logs" (keyword overlap, wrong causality)

3. **Small chunks lack context, large chunks lack precision**
   - Small: "Run DROP DATABASE" (missing: "⚠️ DR drill only, requires approval")
   - Large: 2000-token section about 10 different database issues (noisy embedding)

**Result:** LLM receives incomplete, noisy, or dangerous context → hallucinations, wrong answers, operational risks.

---

### The Multi-Stage Solution

**Progressive refinement through specialized stages:**

```
Stage 1: Cast Wide Net (Hybrid Search)
  → Maximize RECALL (don't miss the answer)
  → Combine dense + sparse retrieval
  → Output: 100 candidates

Stage 2: Filter Noise (Cross-Encoder Reranking)
  → Maximize PRECISION (find the RIGHT answer)
  → Re-sort by relevance using bidirectional attention
  → Output: 10 high-quality results

Stage 3: Assemble Context (Parent-Child Retrieval)
  → Maximize CONTEXT QUALITY (provide SAFE, complete information)
  → Fetch full parent documents for matched child chunks
  → Output: Complete, safe sections for LLM
```

**Philosophy:** Each stage corrects weaknesses of the previous stage. Expensive operations only applied to small candidate sets.

---

## Stage 1: Hybrid Search (Dense + Sparse)

### Why Combine Both?

From Module 03, recall:
- **Dense vectors** (semantic search): Handle paraphrasing, conceptual similarity
- **Sparse vectors** (keyword search): Handle exact technical terms, identifiers

**Neither is sufficient alone for technical documentation.**

---

### Real-World Failure Examples

**Dense-Only Failure:**
```
Query: "Kubernetes annotation nginx.ingress.kubernetes.io/force-ssl-redirect"

Dense search results:
  1. "Nginx ingress SSL configuration overview" ✓ Related but not exact
  2. "Force HTTPS redirect best practices" ✓ Related but not exact
  3. [MISS] "Annotation reference: nginx.ingress.kubernetes.io/force-ssl-redirect" ✗ Contains exact answer but ranked #47

Why: Dense embedding averages the long technical string into generic "nginx ssl" concept
```

**Sparse-Only Failure:**
```
Query: "How do I prevent database connection pool exhaustion?"

Sparse search results:
  1. "Database connection pooling configuration" ✓ Keywords match but wrong topic (setup, not troubleshooting)
  2. [MISS] "Preventing resource exhaustion in database layers" ✗ Right answer but different wording

Why: User query uses "prevent exhaustion", doc uses "avoid resource starvation" - vocabulary mismatch
```

---

### Hybrid Search Architecture

**Parallel execution:**
```
User Query: "database connection timeout troubleshooting"
    │
    ├──> Dense Vector Search (e.g., HNSW index)
    │     - Embedding: OpenAI text-embedding-3 or BGE
    │     - Cosine similarity search
    │     - Output: Top-100 by semantic relevance
    │
    └──> Sparse Keyword Search (e.g., BM25/Elasticsearch)
          - Inverted index lookup
          - Term frequency scoring
          - Output: Top-100 by keyword match

    Both result sets → Fusion Algorithm → Combined Top-100
```

---

### Fusion Algorithms: Combining Incompatible Scores

**The Problem:**
- Dense scores: Cosine similarity (0.0 to 1.0)
- Sparse scores: BM25 score (0 to ~50, no fixed upper bound)
- **Cannot directly combine** (different scales)

---

**Solution 1: Reciprocal Rank Fusion (RRF)**

**Concept:** Combine based on **rank position**, not raw scores.

**Formula:**
```
RRF_score(doc) = Σ [ 1 / (k + rank_i) ]
```
- `k` = constant (typically 60)
- `rank_i` = position of document in each result list

**Example:**
```
Dense Results:          Sparse Results:
1. Doc_A (score: 0.92)  1. Doc_B (BM25: 18.5)
2. Doc_C (score: 0.88)  2. Doc_A (BM25: 15.2)
3. Doc_B (score: 0.85)  3. Doc_D (BM25: 12.1)

RRF Calculation:
Doc_A: 1/(60+1) + 1/(60+2) = 0.0164 + 0.0161 = 0.0325  [Appears in both, high ranks]
Doc_B: 1/(60+3) + 1/(60+1) = 0.0159 + 0.0164 = 0.0323  [Appears in both]
Doc_C: 1/(60+2) + 0        = 0.0161                    [Only in dense]
Doc_D: 0        + 1/(60+3) = 0.0159                    [Only in sparse]

Final Ranking: [Doc_A, Doc_B, Doc_C, Doc_D]
```

**Benefits:**
- No score normalization required
- Documents appearing in both lists naturally ranked higher
- Resistant to outliers (one very high score doesn't dominate)

**Limitations:**
- Treats both retrievers equally (cannot tune emphasis)

---

**Solution 2: Weighted Score Fusion**

**Concept:** Normalize scores, then combine with tunable weights.

**Formula:**
```
Combined_score = α × Normalized_Dense + (1-α) × Normalized_Sparse
```

**Normalization:**
```
Normalized_score = (score - min_score) / (max_score - min_score)
```

**Tuning α (weight parameter):**
- `α = 0.7`: Emphasize semantic understanding (natural language queries)
- `α = 0.5`: Balanced (default starting point)
- `α = 0.3`: Emphasize exact keyword matching (technical identifier queries)

**When to tune:**
- Build evaluation dataset (Module 07)
- Test different α values
- Select based on recall/precision on your domain

**Trade-off:**
- More control than RRF
- Requires normalization logic and tuning
- May need per-query-type tuning (complex)

**Recommendation:** Start with RRF (simpler). Only move to weighted fusion if evaluation shows need for tuning.

---

### Performance Characteristics

**Latency:**
- Dense search: ~50-100ms (approximate nearest neighbor on vector index)
- Sparse search: ~20-50ms (inverted index lookup, highly optimized)
- Parallel execution: ~100-150ms total (limited by slower component)

**Accuracy Gains:**
- Recall improvement over dense-only: Significant for technical content with exact identifiers
- Recall improvement over sparse-only: Significant for paraphrased/conceptual queries
- **Combined: Complementary strengths reduce failure modes**

**When Hybrid Helps Most:**
- Technical documentation with exact identifiers (error codes, API names, config keys)
- Mixed query types (both "how do I..." questions and "fix error X" lookups)
- Large corpora (100k+ docs) where dense search degrades at scale

**When You Might Skip Hybrid:**
- Purely narrative content (blog posts, articles) with no technical identifiers → Dense-only sufficient
- Purely keyword-based search (log search for exact strings) → Sparse-only sufficient
- Very small corpus (<1000 docs) where dense search is already highly accurate → Simplicity preferred

---

## Stage 2: Cross-Encoder Reranking

### Why Stage 1 Isn't Enough

**The "Distractors" Problem:**

Stage 1 (hybrid search) optimizes for **recall** - it casts a wide net to avoid missing the answer. But Top-100 includes many **false positives**:

```
Query: "database connection timeout root cause analysis"

Top-100 from Stage 1 includes:
  ✓ Rank 3: "Database timeout troubleshooting guide" (TRUE POSITIVE)
  ✗ Rank 7: "Database connection pool configuration" (DISTRACTOR - setup, not troubleshooting)
  ✗ Rank 12: "Timeout configuration parameters reference" (DISTRACTOR - config, not root cause)
  ✗ Rank 18: "Connection success rate monitoring" (DISTRACTOR - keyword overlap but opposite scenario)

Problem: LLM receives 10 chunks, 6 are distractors → Wrong answer or hallucination
```

**Why distractors rank high in Stage 1:**
- **Keyword overlap** without causal relationship
  - "Connection timeout" in config docs vs troubleshooting docs
- **Semantic similarity** without relevance
  - "Database performance" is semantically close but not about timeouts specifically
- **Bi-encoder limitation** (see below)

---

### Bi-Encoder vs. Cross-Encoder

**Bi-Encoder (used in Stage 1 dense search):**
```
Query    → Encoder_A → Vector_Q  ─┐
                                   ├─> Cosine Similarity
Document → Encoder_B → Vector_D  ─┘

Characteristics:
- Query and document encoded INDEPENDENTLY
- No interaction between query and document during encoding
- Fast: Document vectors precomputed, only query vector needed at search time
- Cannot detect subtle contradictions or causal relationships
```

**Cross-Encoder (used in Stage 2 reranking):**
```
[Query || Document] → Full Transformer → Relevance Score (0.0 - 1.0)
(concatenated as single input)

Characteristics:
- Query and document processed TOGETHER
- Bidirectional attention across both (every query token attends to every document token)
- Slow: Must process each query-document pair at query time
- Detects nuanced relevance, contradictions, causal relationships
```

---

### What Cross-Encoder Captures

**Example: Detecting Contradiction**
```
Query: "how to PREVENT database timeout"
Document: "After experiencing database timeout, restore from backup"

Bi-Encoder (Stage 1):
  - Semantic similarity: HIGH (both about "database timeout")
  - Ranked: Top-10

Cross-Encoder (Stage 2):
  - Relevance score: LOW (0.23)
  - Reasoning: Query asks for PREVENTION, document describes POST-FAILURE recovery
  - Ranked: Drops to ~40

Result: Contradiction detected, distractor filtered
```

**Example: Causal vs. Correlational**
```
Query: "what causes database connection pool exhaustion"
Document A: "Connection pool exhaustion leads to service degradation"
Document B: "To prevent pool exhaustion, implement connection limits and timeout policies"

Bi-Encoder: Both rank similarly (both mention "pool exhaustion")

Cross-Encoder:
  - Doc A: LOW score (describes EFFECT, not CAUSE)
  - Doc B: HIGH score (describes PREVENTIVE MEASURES - implies root causes)

Result: Causal reasoning improves ranking
```

---

### Architecture: How Reranking Works

**Input:** Top-100 candidates from Stage 1 (hybrid search)

**Process:**
```python
# Pseudocode
cross_encoder = load_model("cross-encoder/ms-marco-MiniLM-L-6-v2")

for doc in top_100_candidates:
    # Concatenate query and document
    input_text = f"{user_query} [SEP] {doc.content}"

    # Forward pass through transformer
    relevance_score = cross_encoder.predict(input_text)

    doc.rerank_score = relevance_score

# Re-sort by cross-encoder scores
final_results = sort(top_100_candidates, by=rerank_score, descending=True)

# Return top-K (typically 10-20)
return final_results[:10]
```

**Output:** Top-10 to Top-20 high-precision results

---

### Performance Characteristics

**Latency:**
- **Per document-pair:** ~5-10ms (depends on model size)
- **For 100 candidates:** ~500ms to 1000ms total
- **Acceptable for:** Human-facing queries, complex technical searches
- **Problematic for:** High-throughput APIs, latency-sensitive applications

**Accuracy Improvement:**
- Precision gains significant when distinguishing subtle relevance
- Critical for: Root cause analysis, troubleshooting, complex multi-clause queries

**Model Choices:**
- **Lightweight:** `cross-encoder/ms-marco-MiniLM-L-6-v2` (~100ms for 100 pairs)
- **High-quality:** `cross-encoder/ms-marco-electra-base` (~500ms for 100 pairs)
- **Trade-off:** Speed vs. accuracy

---

### When to Use Cross-Encoder Reranking

**Use when:**
- Queries are **complex and technical** (multi-clause, causal reasoning required)
- **False positives are costly** (wrong runbook could cause outages)
- **Latency budget allows** (+200-500ms acceptable)
- Evaluation shows Stage 1 retrieves relevant docs but ranks them poorly

**Skip when:**
- Queries are **simple keyword lookups** (exact error code search)
- **High-throughput APIs** (need <100ms end-to-end)
- **Stage 1 already achieves high precision** (small corpus, well-structured content)
- **Operational simplicity** is priority

**Decision framework:**
```
Can you accept +200-500ms latency?
  No → Skip reranking (or use lightweight model with fewer candidates)
  Yes → Continue

Are queries complex/technical with causal reasoning?
  Yes → Cross-encoder likely beneficial
  No → Evaluate on quality needs (may not need)

Have you measured Stage 1 precision on your domain?
  No → Measure first, establish baseline
  Yes, precision is low (<60%) → Cross-encoder recommended
  Yes, precision is high (>80%) → Cross-encoder may be overkill
```

---

## Multi-Vector Approaches: ColBERT Concept

### The Idea

Traditional dense retrieval (Module 03) produces **one vector per chunk**:
```
Document: "Kubernetes pod scheduling fails when node resources exhausted"
  → Single vector [0.12, -0.45, 0.78, ...]

Problem: All token meanings averaged into one vector
```

**ColBERT (Contextualized Late Interaction over BERT):**
```
Document: "Kubernetes pod scheduling fails when node resources exhausted"
  → Per-token vectors:
    "Kubernetes" → [0.23, 0.11, ...]
    "pod"        → [-0.45, 0.67, ...]
    "scheduling" → [0.12, -0.23, ...]
    ...

Query: "pod scheduling failure"
  → Per-token query vectors

Matching: MaxSim operation (maximum similarity between any query token and document token)
```

---

### Why This Helps

**Scenario: Exact phrase matching within semantic context**

```
Query: "connection refused error"

Standard Dense (single vector):
  - Matches documents generally about "connection errors"
  - May rank "connection timeout" equally high (similar overall semantics)

ColBERT (token-level vectors):
  - Specifically matches documents with phrase "connection refused"
  - Higher precision for exact phrase while maintaining semantic flexibility

Result: Better precision on technical queries with specific phrases
```

---

### Trade-offs

**Benefits:**
- **Token-level precision** for exact phrase matching
- **Semantic flexibility** maintained (contextualized token embeddings)
- **Better interpretability** (can see which tokens matched)

**Costs:**
- **Storage explosion:** Instead of 1 vector per chunk (1024 dimensions), store N vectors (one per token)
  - 100-token chunk: 100× storage vs. standard dense
- **Index complexity:** Specialized index structure required
- **Query latency:** MaxSim operation more expensive than cosine similarity

**When useful:**
- Queries frequently include **exact technical phrases** that must match precisely
- Corpus includes many **near-duplicate variants** requiring fine-grained distinction
- Storage and compute costs acceptable for quality gain

**When to skip:**
- Standard hybrid search + cross-encoder already achieves quality goals
- Storage costs prohibitive
- Operational complexity not justified by incremental gains

**Recommendation:** For most SRE wikis, hybrid search + cross-encoder is sufficient. ColBERT is specialized for scenarios requiring token-level precision (e.g., legal contracts, source code search).

---

## Parent-Child Retrieval: Solving Precision-Context Trade-off

### The Fundamental Problem

**Small chunks (256 tokens):**
- ✅ Precise embeddings (tight semantic focus)
- ✅ High retrieval precision (specific query matches specific chunk)
- ❌ Context fragmentation (missing prerequisites, warnings, related steps)

**Large chunks (1024+ tokens):**
- ✅ Complete context (all related information together)
- ❌ Diluted embeddings (multiple concepts averaged)
- ❌ Low retrieval precision (noisy matching)

**You cannot have both with single-tier chunking.**

---

### The Parent-Child Solution

**Core idea: Decouple search from context delivery**

```
┌─────────────────────────────────────────────────────┐
│ INGESTION PHASE                                     │
│                                                     │
│ Original Document (Parent - 1500 tokens):          │
│ ┌───────────────────────────────────────────────┐ │
│ │ # Database Disaster Recovery                  │ │
│ │                                                │ │
│ │ ## Prerequisites                               │ │
│ │ ⚠️ Approval required from VP Engineering      │ │
│ │ - Verify backups completed in last 24h        │ │
│ │ - Confirm DR drill mode activated             │ │
│ │                                                │ │
│ │ ## Emergency Database Drop Procedure           │ │
│ │ 1. Verify DR mode: check /etc/dr-mode         │ │
│ │ 2. Execute: DROP DATABASE production_db;      │ │
│ │ 3. Restore from backup within 4-hour RTO      │ │
│ └───────────────────────────────────────────────┘ │
│         │                                           │
│         ├─> Stored as Parent (parent_id: "p123")   │
│         │                                           │
│         └─> Split into Children (embedded):        │
│             Child_1 (256 tokens): Prerequisites    │
│             Child_2 (256 tokens): Drop procedure   │
│             Child_3 (256 tokens): Restore steps    │
│             Each child stores: parent_id = "p123"  │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ RETRIEVAL PHASE                                     │
│                                                     │
│ Query: "emergency database drop procedure"         │
│   ↓                                                 │
│ Vector search on CHILD chunks only                 │
│   ↓                                                 │
│ Match: Child_2 (score: 0.89)                       │
│   Metadata: parent_id = "p123"                     │
│   ↓                                                 │
│ Fetch PARENT document "p123"                       │
│   ↓                                                 │
│ LLM receives: Complete DR section INCLUDING        │
│   - ⚠️ Warning about VP approval                  │
│   - Prerequisites checklist                        │
│   - Full procedure with verification steps         │
└─────────────────────────────────────────────────────┘
```

---

### Why This Breaks the Trade-off

**Search phase (Precision):**
- Small child chunks (256 tokens) have **focused embeddings**
- Query "emergency database drop" precisely matches Child_2
- No noise from unrelated prerequisites or warnings diluting the vector

**Generation phase (Context):**
- Entire parent (1500 tokens) delivered to LLM
- Includes critical warnings, prerequisites, related context
- LLM can properly contextualize the procedure

**Result: Precise retrieval + Complete context**

---

### Critical Safety Use Case

**Without parent-child:**
```
Fixed 512-token chunking:

Chunk_42 (retrieved):
"## Emergency Database Drop Procedure
1. Verify DR mode: check /etc/dr-mode
2. Execute: DROP DATABASE production_db;
3. Restore from backup within 4-hour RTO"

Chunk_41 (NOT retrieved, in different window):
"⚠️ WARNING: Only execute during scheduled DR drills
Prerequisites:
- VP Engineering approval documented in ticket
- Backup verification completed in last 24h
- All stakeholders notified via #incident-response"

LLM Answer: Provides DROP DATABASE command without warnings → CATASTROPHIC
```

**With parent-child:**
```
Child chunk matched: "Execute: DROP DATABASE production_db"
  parent_id → "parent_doc_disaster_recovery_v3"

Parent retrieved (complete section):
"# Database Disaster Recovery - DR DRILL ONLY
⚠️ WARNING: Only execute during scheduled DR drills...
Prerequisites: VP approval, backup verification...
Procedure: [complete steps with warnings inline]"

LLM Answer: Includes all warnings and prerequisites → SAFE
```

---

### Implementation Schema

**Database Design (e.g., Qdrant, Weaviate, Elasticsearch):**

```json
// Collection 1: Child Chunks (Indexed and Searchable)
{
  "collection": "child_chunks",
  "documents": [
    {
      "id": "child_chunk_c2_p123",
      "vector": [0.12, -0.34, 0.78, ...],     // Dense embedding
      "sparse_vector": {...},                  // Optional: for hybrid
      "payload": {
        "content_snippet": "Execute: DROP DATABASE production_db; Restore from backup...",
        "parent_id": "parent_doc_p123",        // 🔑 Link to parent
        "chunk_index": 2,
        "heading_hierarchy": ["Database DR", "Emergency Drop Procedure"],
        "token_count": 247
      }
    }
  ]
}

// Collection 2: Parent Documents (NOT indexed, just stored)
{
  "collection": "parent_documents",
  "documents": [
    {
      "id": "parent_doc_p123",
      "full_text": "# Database Disaster Recovery\n\n⚠️ WARNING...\n\n## Prerequisites...\n\n## Emergency Database Drop Procedure...",
      "metadata": {
        "file_path": "runbooks/database-dr.md",
        "last_updated": "2024-11-15",
        "version": "3.2",
        "access_level": "sre-only"
      }
    }
  ]
}
```

---

### Retrieval Logic

```python
# Stage 1: Search child chunks
child_results = vector_db.search(
    collection="child_chunks",
    query_vector=query_embedding,
    limit=10,
    filters={"access_level": user.permissions}
)

# Stage 2: Extract unique parent IDs
parent_ids = set([chunk.payload.parent_id for chunk in child_results])

# Stage 3: Fetch parent documents
parent_docs = vector_db.fetch_by_ids(
    collection="parent_documents",
    ids=list(parent_ids)
)

# Stage 4: Assemble context for LLM (use PARENT content, not child snippets)
context = "\n\n---\n\n".join([
    f"Source: {parent.metadata.file_path}\n{parent.full_text}"
    for parent in parent_docs
])

# Stage 5: Generate answer
llm_response = llm.generate(
    prompt=user_query,
    context=context,
    instructions="Answer using only the provided context. Include warnings if present."
)
```

---

### Hierarchical Variant: Grandparent-Parent-Child

For very large documents:
```
Page (Grandparent) - Entire document (not indexed)
  ↓
Section (Parent) - Logical sections (not indexed)
  ↓
Proposition (Child) - Atomic facts (indexed and searchable)

Retrieval: Search propositions → Fetch sections → Optionally fetch full page
```

**When useful:**
- Very long documents (10k+ tokens)
- Hierarchical structure (book chapters, technical manuals)
- Need different context granularities for different query types

---

### When to Use Parent-Child

**Use when:**
- Content has **natural hierarchical structure** (sections, procedures, topics)
- **Context fragmentation causes safety issues** (operational runbooks, security procedures)
- Chunks naturally fall into **operational units** (complete procedures, full troubleshooting workflows)
- Evaluation shows standard chunking loses critical context

**Skip when:**
- Content is **flat and uniform** (logs, unstructured notes)
- Chunks are **already complete semantic units** (Q&A pairs, short articles)
- **Implementation complexity** not justified (small corpus, simple queries)

---

## Multi-Stage Retrieval Architectures

### Architecture 1: Single-Stage (Dense Only)

```
Query → Dense Vector Search → Top-K → LLM
```

**When sufficient:**
- Purely narrative content (no technical identifiers)
- Small corpus (<10k documents)
- Simple conceptual queries
- Latency critical (<50ms)

**Limitations:**
- Misses exact technical terms
- Lower recall on keyword-heavy queries

---

### Architecture 2: Two-Stage (Hybrid Search)

```
Query → Hybrid Search (Dense + Sparse) → RRF Fusion → Top-K → LLM
```

**When sufficient:**
- Mixed query types (conceptual + technical)
- Well-structured content with good chunking
- Medium corpus (10k-100k docs)
- Stage 1 precision already high (>70%)

**Limitations:**
- Still includes distractors in Top-K
- No mechanism to filter subtle irrelevance

---

### Architecture 3: Three-Stage (Hybrid + Reranking)

```
Query → Hybrid Search → Top-100 → Cross-Encoder Rerank → Top-10 → LLM
```

**When beneficial:**
- Complex technical queries requiring causal reasoning
- High cost of false positives (operational runbooks, security procedures)
- Latency budget allows +200-500ms
- Evaluation shows Stage 1 has high recall but low precision

**Performance profile:**
- Latency: ~300-600ms
- Precision: High (filters most distractors)
- Suitable for: Human-facing queries, troubleshooting workflows

---

### Architecture 4: Multi-Stage with Parent-Child

```
Query → Hybrid Search (child chunks) → Top-100 children
      → Cross-Encoder Rerank → Top-10 children
      → Fetch parent documents → Deduplicate
      → Front-and-back packing → Complete context → LLM
```

**When essential:**
- Content fragmentation causes safety issues
- Operational/security-critical documentation
- Hierarchical content structure (runbooks, procedures, manuals)
- Need both precision (child search) and context (parent delivery)

**Performance profile:**
- Latency: ~400-700ms
- Context quality: Maximum (complete, safe sections)
- Suitable for: SRE runbooks, incident response, disaster recovery procedures

---

### Decision Framework: Which Architecture?

```
START: Assess your requirements

Do queries include technical identifiers (error codes, configs)?
  No → Dense-only may suffice
  Yes → Hybrid search required

Is precision critical (false positives costly)?
  No → Two-stage (hybrid) sufficient
  Yes → Add cross-encoder reranking (three-stage)

Does context fragmentation cause safety issues?
  No → Standard chunking adequate
  Yes → Add parent-child retrieval

Is latency critical (<100ms required)?
  Yes → Simplify architecture (remove expensive stages)
  No → Can use full pipeline for maximum quality

Result: Select minimal architecture that meets quality needs
```

---

## Advanced: Front-and-Back Context Packing

### The "Lost-in-the-Middle" Problem

**Research finding:** LLMs exhibit U-shaped attention:
- **High attention:** Beginning and end of context
- **Low attention:** Middle sections ("lost in the middle")

**Naive packing (by relevance):**
```
Context for LLM:
  [Chunk 1 - Most relevant]     ← High attention
  [Chunk 2 - Second relevant]   ← Declining attention
  [Chunk 3 - Third relevant]    ← LOW attention (lost!)
  [Chunk 4 - Fourth relevant]   ← LOW attention (lost!)
  [Chunk 5 - Fifth relevant]    ← Moderate attention

Result: Chunks 3-4 may be ignored despite being relevant
```

---

### Optimal Packing Strategy

**Front-and-back interleaving:**
```
Retrieved chunks ranked: [C1, C2, C3, C4, C5, C6]

Packed order:
  [C1 - Most relevant]           ← FRONT (high attention)
  [C3 - Third relevant]          ← FRONT
  [C5 - Fifth relevant]          ← FRONT

  --- USER QUERY INSERTED HERE ---

  [C6 - Least relevant]          ← BACK
  [C4 - Fourth relevant]         ← BACK
  [C2 - Second most relevant]    ← BACK (high attention)
```

**Result:** Top-2 chunks (C1, C2) positioned at attention hotspots (very beginning, very end)

---

## Key Takeaways

### Core Principles

1. **Hybrid search is the production standard** for technical documentation
   - Dense handles semantic queries
   - Sparse handles exact identifiers
   - Combine with RRF for complementary strengths

2. **Cross-encoder reranking filters distractors**
   - Use bidirectional attention to detect subtle irrelevance
   - Add +200-500ms latency for significant precision gain
   - Essential for complex technical queries

3. **Parent-child retrieval solves precision-context trade-off**
   - Search small chunks (precision)
   - Deliver large parents (context)
   - Critical for safety in operational documentation

4. **Architecture complexity should match requirements**
   - Start simple (dense-only or hybrid)
   - Add stages only when evaluation shows need
   - Each stage has latency cost - justify with quality gain

### Design Decisions

**Choose architecture based on:**
- Query complexity (simple lookups vs. causal reasoning)
- Content type (narrative vs. technical procedures)
- False positive cost (informational vs. operational)
- Latency budget (interactive vs. batch)
- Corpus size (small vs. large-scale)

**Avoid cargo-culting:**
- Don't implement three-stage pipeline for 1000-document blog
- Don't skip hybrid search for technical docs with error codes
- Measure quality on your domain, add complexity only when justified

---

## Next Steps

**Module 05: Advanced Patterns** will cover when and why to add even more complexity:
- Self-RAG (self-reflective retrieval with LLM feedback)
- Multi-hop reasoning (breaking complex queries into sub-questions)
- Query transformation techniques (HyDE, multi-query expansion)
- When advanced patterns justify their complexity

**Module 08: Implementation Guide** will provide concrete schemas, pipelines, and technology choices for building these architectures in production.

**Before continuing**, ensure you understand:
- Why hybrid search combines complementary strengths
- When cross-encoder reranking justifies its latency cost
- How parent-child retrieval provides both precision and context
- The decision framework for selecting appropriate architecture complexity
