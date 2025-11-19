# Module 05: Advanced Patterns

**Learning Objectives:**
- Understand when advanced RAG patterns justify their complexity
- Evaluate trade-offs between retrieval quality and operational burden
- Apply decision frameworks to determine if your use case needs advanced techniques
- Recognize when simpler approaches are sufficient

**Prerequisites:** Modules 01-04 (basic chunking, embeddings, and retrieval architecture)

**Time:** 30-45 minutes

---

## Introduction: When Complexity is Justified

The techniques in this module add significant complexity to your RAG system. They increase latency, operational burden, and maintenance costs. **You should only adopt them when simpler approaches demonstrably fail.**

This module is not advocacy for "advanced = better." It's a framework for deciding **when** additional complexity solves real problems **and when** it's premature optimization.

**Critical Question:** Has your evaluation (Module 07) proven that basic retrieval fails on queries that matter to your users? If not, these patterns are likely overkill.

---

## 1. Self-RAG: Self-Reflective Retrieval

### What It Is

Self-RAG adds a **reflection loop** where the LLM evaluates its own retrieval results and decides whether to retrieve additional context.

**Basic Flow:**
1. Initial query → retrieval → generate answer
2. LLM evaluates: "Do I have enough information to answer this accurately?"
3. If NO: Generate refined query → retrieve again → update answer
4. Repeat until confidence threshold met or max iterations reached

**Example Scenario:**

```
User Query: "Why did the API gateway fail during Black Friday?"

Iteration 1:
- Retrieves: "API Gateway incident on 2024-11-29"
- LLM reflects: "I found the incident, but I don't see the root cause analysis."
- Action: Retrieve with query "API gateway root cause Black Friday"

Iteration 2:
- Retrieves: "Post-mortem: Database connection pool exhaustion"
- LLM reflects: "Now I have both the incident timeline and root cause."
- Action: Generate complete answer
```

### When It's Useful

**Use Self-RAG when:**

1. **Complex queries regularly need multi-document synthesis**
   - Example: "Compare authentication failures across all services last month"
   - Initial retrieval gets auth-service data, reflection identifies missing data for other services

2. **Initial retrieval frequently misses critical context**
   - Example: Runbook references prerequisite checks in a different document
   - LLM identifies gap and retrieves prerequisites

3. **Users accept 2-5x latency increase for better answers**
   - Interactive troubleshooting sessions (not real-time alerting)
   - Post-incident analysis (not oncall response)

**Skip Self-RAG when:**

- Queries are typically single-document lookups ("What's the restart procedure for auth-service?")
- Latency requirements are tight (<500ms response time)
- Basic retrieval already achieves >90% answer quality in your evaluation
- Operational team lacks capacity to debug multi-stage retrieval failures

### Trade-offs

| Benefit | Cost |
|---------|------|
| Handles incomplete initial retrieval gracefully | **2-5x latency** (multiple LLM calls + retrieval rounds) |
| Reduces "I don't have enough information" responses | **2-3x token costs** (reflection prompts + expanded context) |
| Enables multi-document reasoning automatically | **Complex debugging** (which iteration failed? why?) |
| Adapts to unexpected query needs | **Non-deterministic behavior** (iteration count varies) |

### Implementation Approaches

**Simple Reflection Prompt:**

```python
reflection_prompt = """
You retrieved the following context:
{retrieved_context}

For the user's question: {user_query}

Evaluate:
1. Is the information sufficient to answer accurately? (YES/NO)
2. If NO, what specific information is missing?
3. Generate a refined search query to find the missing information.

Format your response as JSON:
{
  "sufficient": true/false,
  "missing": "description of gap",
  "refined_query": "new search query or null"
}
"""
```

**Iteration Control:**

- **Max iterations:** 3 (prevent infinite loops)
- **Confidence threshold:** LLM scores sufficiency on 0-1 scale, stop at >0.85
- **Timeout:** Hard cutoff at 10 seconds total retrieval time

**When to Stop:**
- Sufficient information found
- Max iterations reached
- New retrieval returns no results (search space exhausted)
- User timeout threshold approaching

### Operational Considerations

**Monitoring:**
- Track average iterations per query (spike = retrieval quality degradation)
- Measure latency distribution (P95 latency shows worst-case user experience)
- Log reflection decisions (audit what gaps triggered re-retrieval)

**Failure Modes:**
- **Infinite loops:** LLM never satisfied → enforce max iterations
- **Vague refinements:** LLM generates "get more information" instead of specific query → improve reflection prompt
- **Context explosion:** Each iteration retrieves 10 more chunks → limit retrieval per iteration

**Cost Modeling:**

If basic retrieval costs:
- 1 embedding call (query)
- 1 LLM call (generation)

Self-RAG costs:
- 3 embedding calls (original + 2 refinements)
- 4 LLM calls (2 reflections + 2 generations)
- **~4x cost** for complex queries

**Decision Point:** Is 4x cost justified by quality improvement in your evaluation?

---

## 2. Multi-Hop Reasoning

### What It Is

Multi-hop reasoning **decomposes complex queries** into sub-questions, retrieves context for each independently, then synthesizes a final answer.

**Example:**

```
User Query: "Compare authentication service performance during the Black Friday incident versus the Prime Day incident"

Decomposition:
1. "What was the auth service performance during Black Friday?"
2. "What was the auth service performance during Prime Day?"
3. "Synthesize comparison of findings from 1 and 2"

Each sub-question triggers independent retrieval.
```

### When It's Useful

**Use Multi-Hop when:**

1. **Queries require synthesis across documents**
   - "Compare X and Y"
   - "What changed between version A and version B?"
   - "How does Service X depend on Service Y?"

2. **Documents are semantically distant but logically related**
   - Example: Database post-mortem doesn't mention "API gateway," but both reference the same incident ID
   - Direct query "API gateway and database incident" fails to retrieve database post-mortem
   - Multi-hop: Query 1 finds incident ID from API gateway doc, Query 2 uses incident ID to find database doc

3. **Hierarchical information retrieval**
   - "Which services had auth failures?" (get list)
   - "For each service, what was the root cause?" (iterate over list)

**Skip Multi-Hop when:**

- Queries are typically self-contained ("How do I restart auth-service?")
- Documents already contain cross-references (runbooks link to prerequisites)
- Latency budget doesn't allow multiple retrieval rounds
- Query complexity doesn't justify decomposition overhead

### Knowledge Graph Integration

**Hybrid Approach:** Vector retrieval + graph traversal

**From Research Findings:**

> "In a complex outage scenario, a vector search might fail to connect a 'Database CPU Spike' in Service X with a 'Deployment' in Service Y. However, if the Knowledge Graph encodes the dependency that Service Y writes to Service X's database, a graph traversal (Breadth-First Search) can retrieve the deployment event as a potential root cause, even if the textual descriptions are dissimilar."

**When Knowledge Graphs Add Value:**

- **Service dependencies:** `auth-service --depends_on--> database-cluster`
- **Incident timelines:** `incident-123 --caused_by--> deployment-456`
- **Configuration relationships:** `prod-config --inherits_from--> base-config`

**Architecture Pattern:**

```
1. Initial vector search: Retrieve top-K semantically similar documents
2. Graph traversal: Follow relationships (dependencies, references, temporal links)
3. Expand retrieval: Fetch documents connected via graph edges
4. Synthesize: Combine direct matches + relationship-based discoveries
```

**Trade-off:** Knowledge graphs require **manual or semi-automated relationship extraction**. If your documents don't have structured dependencies (service maps, incident IDs, config hierarchies), the ROI is low.

### Implementation: Query Decomposition

**LLM-Based Decomposition:**

```python
decomposition_prompt = """
Break down this complex query into 2-4 independent sub-questions that can be answered separately.

User Query: {user_query}

Requirements:
- Each sub-question should be answerable from a single document or small set of documents
- Sub-questions should not depend on each other's answers
- Final synthesis step should combine sub-answers

Format as JSON:
{
  "sub_questions": ["Q1", "Q2", "Q3"],
  "synthesis_instruction": "How to combine answers"
}
"""
```

**Parallel vs Sequential Retrieval:**

**Parallel (faster):**
- All sub-questions retrieve simultaneously
- Works when sub-questions are independent
- Example: "Compare Service A and Service B" → query each in parallel

**Sequential (more flexible):**
- Answer to Q1 informs Q2
- Example: "What services failed?" → use answer to query "Why did [service] fail?"

### Trade-offs

| Benefit | Cost |
|---------|------|
| Handles complex analytical queries | **Latency:** N sub-questions = N retrieval rounds |
| Improves recall for multi-document reasoning | **Complexity:** Query planning can fail (bad decomposition) |
| Discovers relationships vector search misses | **Cost:** Multiple LLM calls for decomposition + synthesis |
| Enables iterative exploration | **Debugging:** Hard to trace why final answer is wrong |

### Operational Considerations

**When Multi-Hop Fails:**

- **Poor decomposition:** LLM creates overlapping or dependent sub-questions
- **Retrieval failure:** One sub-question returns no results → partial answer only
- **Synthesis errors:** LLM contradicts itself when combining sub-answers

**Mitigation:**
- Validate decomposition quality (test on synthetic queries)
- Implement fallback: If sub-question fails, continue with partial information
- Log decomposition decisions for debugging

**Decision Point:** Can you achieve the same quality by improving chunking to keep related information together? If yes, fix chunking instead of adding multi-hop.

---

## 3. Query Transformation

### What It Is

**Rewrite the user's query before retrieval** to improve match quality.

### Techniques

#### 3.1 HyDE (Hypothetical Document Embeddings)

**Concept:** Generate a fake answer to the user's question, then search for documents similar to that fake answer.

**Example:**

```
User Query: "How do I restart the auth service?"

HyDE Generation (LLM creates hypothetical answer):
"To restart the auth service, SSH to the primary node and run:
sudo systemctl restart auth-service
Then verify with: systemctl status auth-service"

Embedding: Encode this hypothetical answer → search for similar documents
```

**Why It Works:**

Users ask questions ("How do I...?"). Documents contain answers ("Run this command..."). Question embeddings and answer embeddings live in different semantic spaces.

HyDE bridges the gap: Search using answer-space embeddings instead of question-space embeddings.

**From Research:**

> "Multi-Query + Multi-HyDE rewrites expand sparse/dense coverage (+11.2% accuracy) before any retrieval happens"

**When Useful:**

- Users phrase queries as questions, but documents are procedural (runbooks, how-tos)
- Vocabulary mismatch: Users say "connection refused," docs say "network socket error"
- Conceptual queries: "Why is my service slow?" → HyDE generates "CPU usage high, memory leak, database timeout" → finds relevant docs

**Trade-offs:**

| Benefit | Cost |
|---------|------|
| Bridges question-answer semantic gap | **Latency:** Extra LLM call before retrieval |
| Improves recall when vocabulary differs | **Hallucination risk:** Fake answer may be wrong, biasing retrieval |
| Works well for "how to" queries | **Doesn't help if answer is completely novel** (no similar docs exist) |

**When to Skip:**

- Documents already match query vocabulary (technical logs, error codes)
- Latency budget <200ms (HyDE adds 100-300ms)
- Users provide very specific identifiers (incident IDs, hostnames) → exact match works

#### 3.2 Multi-Query Expansion

**Concept:** Rephrase the query multiple ways, retrieve with each variant, merge results.

**Example:**

```
User Query: "auth service down"

Expansions:
1. "authentication service outage"
2. "login failures authorization"
3. "user authentication unavailable"
4. "auth-service restart procedure"

Retrieve with all 4 queries → deduplicate → rerank merged results
```

**Why It Works:**

Different phrasings retrieve different documents. Expanding coverage reduces the risk of missing the best match due to vocabulary choice.

**When Useful:**

- Ambiguous queries that could mean multiple things
- Domain with high vocabulary variance (users say "login," "auth," "SSO," "identity" interchangeably)
- Low confidence in initial query quality (user is exploring, not sure what terms to use)

**Trade-offs:**

| Benefit | Cost |
|---------|------|
| Increases recall (retrieves more relevant docs) | **Latency:** 3-5x retrieval calls |
| Reduces sensitivity to query phrasing | **Deduplication complexity** (same doc retrieved via multiple queries) |
| Helps exploratory search | **Precision can drop** (more results = more noise) |

**Result Merging:**

Use **Reciprocal Rank Fusion (RRF)** to combine results from multiple query variants:

```python
def reciprocal_rank_fusion(results_per_query, k=60):
    scores = {}
    for query_results in results_per_query:
        for rank, doc_id in enumerate(query_results):
            if doc_id not in scores:
                scores[doc_id] = 0
            scores[doc_id] += 1 / (rank + k)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

**Decision Point:** If your evaluation shows basic retrieval already has high recall (>85%), multi-query expansion adds cost without benefit.

#### 3.3 Domain Vocabulary Alignment

**Concept:** Map user terms to technical terms before retrieval.

**Example:**

```
User Query: "Why is login broken?"

Vocabulary mapping:
- "login" → ["authentication", "auth-service", "SSO", "identity-provider"]
- "broken" → ["failure", "error", "timeout", "unavailable"]

Expanded Query: "authentication failure OR auth-service error OR SSO timeout OR identity-provider unavailable"
```

**When Useful:**

- Large vocabulary gap between users and documentation (users = business terms, docs = technical terms)
- Highly specialized domain (medical, legal, finance) with jargon
- Multi-lingual environments (query in English, some docs in Spanish)

**Implementation:**

- **Static dictionary:** Curated term mappings (manual or crowdsourced)
- **LLM-based expansion:** Prompt LLM to translate user terms to technical equivalents
- **Learned mappings:** Fine-tune embedding model on query-document pairs from your domain

**Trade-offs:**

| Benefit | Cost |
|---------|------|
| Handles user-expert vocabulary mismatch | **Maintenance burden:** Dictionary requires updates as domain evolves |
| Improves accessibility for non-experts | **Over-expansion risk:** Too many synonyms add noise |
| Reduces "zero results" failures | **Context-dependent mappings:** "Check" in banking vs infrastructure |

**Decision Point:** Start with evaluation. If users frequently get zero results for queries that should match existing docs, vocabulary alignment is justified.

---

## 4. Neighbor Chunk Expansion

### What It Is

Retrieve not just the matching chunk, but also **adjacent chunks** (before/after in the document).

**Example:**

```
Document Structure:
- Chunk 1: Prerequisites (users must have sudo access)
- Chunk 2: Restart Procedure (systemctl restart auth-service) ← MATCH
- Chunk 3: Validation (check logs for "started successfully")

User Query: "How do I restart auth-service?"

Without Expansion: Retrieve Chunk 2 only → user misses prerequisites and validation
With Expansion: Retrieve Chunks 1, 2, 3 → complete procedure
```

### When It's Useful

**Use Neighbor Expansion when:**

1. **Procedures span multiple chunks**
   - Chunking had to split at 900 tokens, but procedure is 1200 tokens
   - Prerequisites, steps, and validation live in different chunks

2. **Context dependencies**
   - Code example references variable defined in previous chunk
   - Runbook step references warning in previous section

3. **Boundary loss is common**
   - Evaluation shows LLM frequently says "I don't see the full context"
   - Users complain answers are incomplete

**Skip Neighbor Expansion when:**

- Chunks are already semantically complete (parent-child retrieval handles this better)
- Token budget is tight (expansion can double context size)
- Documents have clear section boundaries that chunking respects

### Implementation

**Chunk Metadata:**

```json
{
  "chunk_id": "doc123_chunk002",
  "prev_chunk_id": "doc123_chunk001",
  "next_chunk_id": "doc123_chunk003",
  "parent_id": "doc123"
}
```

**Retrieval Logic:**

```python
def retrieve_with_neighbors(query, k=5, expand_neighbors=1):
    # Initial retrieval
    matches = vector_search(query, k=k)

    # Expand to neighbors
    expanded = set()
    for chunk in matches:
        expanded.add(chunk.chunk_id)
        if expand_neighbors >= 1 and chunk.prev_chunk_id:
            expanded.add(chunk.prev_chunk_id)
        if expand_neighbors >= 1 and chunk.next_chunk_id:
            expanded.add(chunk.next_chunk_id)
        if expand_neighbors >= 2 and chunk.prev_chunk_id:
            prev = get_chunk(chunk.prev_chunk_id)
            if prev.prev_chunk_id:
                expanded.add(prev.prev_chunk_id)
        # ... continue for expand_neighbors depth

    return fetch_chunks(expanded)
```

**Deduplication:**

If Chunk 2 and Chunk 3 both match the query, expanding Chunk 2 retrieves Chunk 3. Don't include Chunk 3 twice.

### Trade-offs

| Benefit | Cost |
|---------|------|
| Prevents boundary loss | **Token usage:** Expands context by 2-3x |
| Ensures complete procedures retrieved | **Precision drop:** Neighbors may be irrelevant |
| Reduces "incomplete information" failures | **Deduplication complexity** |
| Simple to implement | **Only works if chunks are sequential** (fails for randomly ordered documents) |

### Alternative: Parent-Child Retrieval

**Comparison:**

**Neighbor Expansion:**
- Retrieves specific chunks + immediate neighbors
- Good for linear documents (runbooks, how-tos)
- Lower token cost (only expands by 1-2 chunks)

**Parent-Child Retrieval (Module 04):**
- Retrieves entire parent document when child matches
- Good for hierarchical documents (posts-mortems, design docs)
- Higher token cost (entire parent may be 2000+ tokens)

**Decision:** If documents are linear and procedures span 2-3 chunks, use neighbor expansion. If documents are hierarchical and child chunks need full document context, use parent-child.

---

## 5. Decision Framework: When is Complexity Justified?

### The Evaluation-First Principle

**Do not implement advanced patterns without first proving basic retrieval fails.**

**Process:**

1. **Build evaluation dataset** (Module 07): 50-100 representative queries
2. **Measure basic retrieval quality:** Recall@10, MRR, answer accuracy
3. **Identify failure modes:** Which queries fail? Why?
4. **Map failures to patterns:** Does the failure match a pattern's use case?
5. **Implement pattern:** Only for proven failure modes
6. **Measure improvement:** Did the pattern actually help?

### Decision Matrix

| Failure Mode | Pattern to Consider | Evaluation Metric |
|--------------|---------------------|-------------------|
| "I don't have enough information" (incomplete retrieval) | **Self-RAG** | Reduction in incomplete answers |
| Complex queries need synthesis across docs | **Multi-Hop** | Recall@10 for multi-doc queries |
| Questions don't match answer vocabulary | **HyDE** | Recall improvement on "how to" queries |
| Ambiguous queries get zero results | **Multi-Query Expansion** | Reduction in zero-result rate |
| Procedures split across chunks | **Neighbor Expansion** | Answer completeness score |
| Users and docs use different terms | **Vocabulary Alignment** | Zero-result rate for known-good queries |

### Complexity Budget

**Each pattern adds:**

- **Development time:** 1-4 weeks per pattern (design, implement, test)
- **Operational burden:** New failure modes to monitor and debug
- **Latency:** 100ms-2000ms per pattern
- **Cost:** 2x-5x embedding/LLM costs

**Team Capacity Assessment:**

Can your team maintain this complexity?

- **Small team (1-2 engineers):** Stick to basic retrieval + one advanced pattern if critical
- **Medium team (3-5 engineers):** Can support 2-3 patterns with good monitoring
- **Large team (6+ engineers):** Can support full suite with dedicated RAG platform team

### The "Simple First" Checklist

Before implementing any advanced pattern, verify you've exhausted simpler improvements:

- [ ] **Chunking quality:** Are chunks semantically complete? (Module 02)
- [ ] **Embedding model:** Is it appropriate for your domain? (Module 03)
- [ ] **Hybrid search:** Are you using both dense and sparse retrieval? (Module 04)
- [ ] **Metadata filtering:** Are you filtering by tenant, environment, freshness? (Module 06)
- [ ] **Cross-encoder reranking:** Have you tried reranking? (Module 04)
- [ ] **Parent-child retrieval:** Are you returning enough context? (Module 04)

**Only proceed to advanced patterns if:**

✅ All above are implemented and tuned
✅ Evaluation shows specific failure modes
✅ Latency budget allows additional complexity
✅ Team can maintain and debug the pattern

---

## 6. Latency Budgeting

### Pattern Latency Profiles

| Pattern | Added Latency | Acceptable Use Cases |
|---------|---------------|----------------------|
| **Basic Retrieval** | 50-150ms | Real-time API, oncall alerts |
| **+ HyDE** | +100-300ms | Interactive search, troubleshooting |
| **+ Multi-Query (3 variants)** | +50-200ms | Exploratory search |
| **+ Self-RAG (avg 2 iterations)** | +200-1000ms | Post-incident analysis, research |
| **+ Multi-Hop (3 sub-queries)** | +300-900ms | Complex analytical queries |
| **+ Cross-Encoder Rerank** | +100-500ms | High-stakes decisions |

### User Experience Thresholds

- **<200ms:** Feels instant (real-time oncall)
- **200-500ms:** Acceptable for interactive use (troubleshooting)
- **500-1000ms:** Noticeable delay but tolerable (research, analysis)
- **1000-2000ms:** Frustrating for interactive use (batch only)
- **>2000ms:** Unacceptable for human-facing queries

**Decision Point:** If your users are oncall engineers responding to incidents, 2000ms latency is unacceptable. Advanced patterns must be reserved for post-incident analysis, not real-time response.

---

## 7. Cost Modeling

### Cost Components per Pattern

**Baseline (Simple Retrieval):**
- 1 embedding API call (query)
- 1 vector search operation
- 1 LLM generation call
- **Cost:** $0.001 per query (example)

**With Advanced Patterns:**

| Pattern | Embedding Calls | LLM Calls | Multiplier |
|---------|-----------------|-----------|------------|
| **HyDE** | +1 (fake answer) | +1 (generate fake answer) | ~2x |
| **Multi-Query (3x)** | +2 (variants) | +1 (generate variants) | ~2.5x |
| **Self-RAG (2 iterations)** | +2 (refinements) | +3 (reflections + gens) | ~4x |
| **Multi-Hop (3 sub-queries)** | +2 (sub-queries) | +2 (decomposition + synthesis) | ~3x |

**Combined Patterns:**

If you stack HyDE + Multi-Query + Self-RAG:
- **Latency:** 500ms + 200ms + 1000ms = 1700ms
- **Cost:** 2x × 2.5x × 4x = **20x baseline**

**Decision Point:** Is a 20x cost increase justified by quality improvement? Often the answer is "no" for most queries, but "yes" for a small subset of complex queries.

**Optimization:** Apply advanced patterns selectively based on query complexity classification.

---

## 8. Practical Guidance: Incremental Adoption

### Phase 1: Measure Baseline

1. Implement basic retrieval (Modules 01-04)
2. Build evaluation dataset (Module 07)
3. Measure: Recall@10, MRR, answer quality
4. Identify top 10 failure cases

**Don't proceed until you have quantitative baseline.**

### Phase 2: Single Pattern Trial

1. Choose ONE pattern that addresses your top failure mode
2. Implement minimal viable version
3. Measure improvement on evaluation dataset
4. If improvement <10%, pattern is not worth the complexity

### Phase 3: Selective Application

Don't apply advanced patterns to all queries. **Classify queries and route accordingly:**

```python
def classify_query_complexity(query):
    """Route query to appropriate retrieval strategy."""
    if is_simple_lookup(query):
        # "What is the restart command for auth-service?"
        return "basic_retrieval"
    elif is_comparative(query):
        # "Compare Service A and Service B"
        return "multi_hop"
    elif is_exploratory(query):
        # "Why is my service slow?"
        return "self_rag"
    else:
        return "basic_retrieval"
```

**Result:** 80% of queries use fast, cheap basic retrieval. 20% use expensive advanced patterns only when needed.

### Phase 4: Monitor and Refine

Track:
- Pattern usage distribution (are 80% of queries going to expensive paths?)
- Latency per pattern (is Self-RAG averaging 4 iterations instead of 2?)
- Cost per pattern (is HyDE costing more than expected?)
- Quality improvement (did Recall@10 actually improve?)

**Iterate:** Remove patterns that don't deliver value. Optimize patterns that do.

---

## Summary

| Pattern | When to Use | Primary Trade-off |
|---------|-------------|-------------------|
| **Self-RAG** | Complex queries need multi-document synthesis; users accept 2-5x latency | **Latency vs Completeness** |
| **Multi-Hop** | Analytical queries require decomposition ("compare X and Y") | **Complexity vs Synthesis Quality** |
| **HyDE** | Question-answer vocabulary mismatch; procedural content | **Latency vs Recall** |
| **Multi-Query** | Ambiguous queries; high vocabulary variance | **Cost vs Recall** |
| **Neighbor Expansion** | Procedures span chunk boundaries; linear documents | **Token Usage vs Completeness** |
| **Vocabulary Alignment** | User-expert terminology gap; zero-result failures | **Maintenance vs Accessibility** |

**Core Principle:** Advanced patterns are powerful tools for specific failure modes. They are not default best practices. Evaluate first, optimize chunking and basic retrieval second, add complexity only when demonstrably necessary.

**Next Module:** [06-production-deployment.md](06-production-deployment.md) - Operational realities of running RAG at scale

---

## Discussion Questions

1. Your evaluation shows 15% of queries fail due to incomplete retrieval. Self-RAG could fix this but adds 1000ms latency. Your users are oncall engineers. Do you implement it?

2. You're considering HyDE for a documentation search system. Baseline retrieval has 78% Recall@10. HyDE improves it to 84% but doubles latency. Is it worth it?

3. Your team is 2 engineers. You've identified use cases for Self-RAG, Multi-Hop, and Multi-Query expansion. Which ONE do you implement first, and why?

4. A colleague proposes implementing all advanced patterns "just in case we need them later." How do you respond?

**Answers in next module... or better yet, answer them with evaluation data from your own system.**
