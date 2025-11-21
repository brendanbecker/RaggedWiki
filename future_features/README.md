# Future Features & Enhancement Ideas

This directory contains ideas and specifications for features that would enhance the RaggedWiki project but are not currently prioritized for implementation. These are well-scoped ideas ready to be picked up when resources allow.

## Purpose

Use this directory to:
1. **Document good ideas** that emerge during development
2. **Prevent idea loss** (capture context while fresh)
3. **Enable future contributors** to find high-value work
4. **Maintain project focus** (defer non-critical work without forgetting it)

## How to Use This Directory

### Adding New Ideas
When you have an idea for a feature:
1. Create a markdown file: `YYYYMMDD-feature-name.md`
2. Use the template in `_TEMPLATE.md`
3. Include: problem statement, proposed solution, effort estimate, dependencies
4. Tag with priority: P1 (high value), P2 (medium value), P3 (nice-to-have)

### Implementing Features
When picking up a feature:
1. Review the specification
2. Update status from "Proposed" to "In Progress"
3. Move completed features to a `completed/` subdirectory with link to PR/commit

---

## Current Future Features

### 1. Validation & Analysis Tools (P1 - High Value)

**Status**: Proposed
**Effort**: 2-3 days
**Value**: High - helps users apply curriculum principles to their own wikis

#### Tools to Build

**1.1 Token Counter & Section Analyzer**
```bash
python tools/analyze_sections.py --input sre_wiki_example/runbooks/

# Output:
# runbooks/database-failover.md:
#   Section "Prerequisites": 420 tokens ✅ (optimal)
#   Section "Failover Procedure": 680 tokens ✅ (optimal)
#   Section "Rollback": 820 tokens ✅ (optimal)
# Overall: 3/3 sections in 400-900 token range
```

**Features**:
- Count tokens per section (H2 boundaries)
- Flag sections outside 400-900 token sweet spot
- Suggest section splits for >900 token sections
- Identify sections <400 tokens that could be merged

**Technology**: Python + tiktoken for token counting

---

**1.2 Metadata Completeness Checker**
```bash
python tools/check_metadata.py --input sre_wiki_example/

# Output:
# runbooks/database-failover.md: ✅ All required metadata present
#   - Service name: PostgreSQL Cluster
#   - Environment: prod-us-east
#   - Severity: SEV1
#   - Owner: sre-data
#
# runbooks/auth-service-restart.md: ⚠️  Missing: Last Tested date
```

**Features**:
- Validate metadata frontmatter/tables exist
- Check for required fields (service, environment, owner, severity for runbooks)
- Flag documents missing metadata
- Generate metadata templates for new documents

**Technology**: Python + frontmatter parsing

---

**1.3 Abstract Generator**
```bash
python tools/generate_abstracts.py --input sre_wiki_example/runbooks/database-failover.md

# Output:
# Section: Prerequisites
# Abstract (150 tokens): This section covers prerequisites for database failover...
#
# Section: Failover Procedure
# Abstract (180 tokens): This section contains the core failover execution steps...
```

**Features**:
- Auto-generate 100-200 token abstracts from sections
- Use local LLM (llama.cpp) or OpenAI API
- Validate abstract token count
- Insert abstracts into markdown as YAML frontmatter or JSON

**Technology**: Python + sentence-transformers or OpenAI API

---

**1.4 Chunking Strategy Validator**
```bash
python tools/validate_chunking.py --input sre_wiki_example/ --strategy layout-aware

# Output:
# Analyzing 17 documents with layout-aware strategy...
#
# Results:
#   - Average section size: 620 tokens (target: 400-900)
#   - Sections in range: 82% (target: >80%)
#   - Problematic sections: 3
#     - runbooks/api-gateway-rate-limit.md: "Configuration" (1,120 tokens)
#
# Recommendation: Split "Configuration" section into subsections
```

**Features**:
- Simulate chunking with different strategies
- Report token distribution statistics
- Identify outliers and suggest fixes
- Compare strategies side-by-side

**Technology**: Python + markdown parsing

---

### 2. Content Templates & Migration Guides (P2 - Medium Value)

**Status**: Proposed
**Effort**: 1-2 days
**Value**: Medium - helps new users create well-structured content

#### Templates to Create

**2.1 Content Type Templates**

Create templates for each content type in `templates/`:
- `runbook-template.md` - Service-specific operational playbook
- `how-to-template.md` - Reusable procedural guide
- `postmortem-template.md` - Incident analysis (already exists, enhance it)
- `architecture-doc-template.md` - System design documentation
- `service-overview-template.md` - Service metadata and dependencies

Each template includes:
- Metadata placeholders
- Recommended section structure
- Section size guidance (400-900 tokens)
- Examples of good vs. bad content

**2.2 Migration Guide for Existing Wikis**

Create `guides/migrating-existing-wiki.md`:
- Step-by-step migration process
- Content audit checklist
- Section restructuring guide
- Before/after examples
- Common migration pitfalls

**2.3 Style Guide for RAG-Optimized Writing**

Create `guides/writing-for-rag.md`:
- Section sizing guidelines
- Hierarchical header usage
- Code block best practices
- Metadata embedding
- Self-contained section principles

---

### 3. Advanced RAG Features (P2 - Medium Value)

**Status**: Proposed (depends on basic RAG system completion)
**Effort**: 3-5 days
**Value**: Medium - demonstrates advanced RAG patterns from curriculum

#### Features to Add to RAG System

**3.1 Multi-Stage Retrieval Pipeline**
Implement BM25 + Dense Vector + Reranker pipeline:

```python
# Stage 1: BM25 (keyword-based, high recall)
bm25_results = bm25_search(query, top_k=100)

# Stage 2: Dense vector search (semantic, high precision)
vector_results = dense_search(query, top_k=100)

# Combine results with score fusion
combined = reciprocal_rank_fusion(bm25_results, vector_results)

# Stage 3: Rerank with cross-encoder (bidirectional attention)
reranked = cross_encoder_rerank(query, combined[:20], top_k=5)

return reranked
```

**Technology**:
- BM25: Elasticsearch or Whoosh
- Dense: sentence-transformers + ChromaDB
- Reranker: cross-encoder model

**3.2 Query Transformation**
Implement query rewriting for better retrieval:

```python
# Original query: "database is down"
# Transformed queries:
#   1. "database failover procedure"
#   2. "database outage troubleshooting"
#   3. "restore database availability"

# Retrieve for all queries, deduplicate results
```

**3.3 Metadata Filtering**
Allow filtering by metadata before embedding search:

```python
results = search(
    query="restart procedure",
    filters={
        "service": "auth-service",
        "severity": ["SEV1", "SEV2"],
        "content_type": "runbook"
    }
)
```

**3.4 Hybrid Search with Score Fusion**
Combine multiple search strategies:

```python
def hybrid_search(query, alpha=0.5):
    # Keyword search score
    bm25_score = bm25_search(query)

    # Semantic search score
    vector_score = vector_search(query)

    # Combine with weighted average
    final_score = alpha * bm25_score + (1-alpha) * vector_score
    return final_score
```

---

### 4. Evaluation & Benchmarking Tools (P1 - High Value)

**Status**: Proposed
**Effort**: 2-3 days
**Value**: High - demonstrates Module 07 (Evaluation) principles

#### Tools to Build

**4.1 Retrieval Quality Evaluation**

Create `tools/evaluate_retrieval.py`:

```python
# Define ground truth: query -> expected documents
test_cases = [
    {
        "query": "How do I fail over the database?",
        "expected_chunks": [
            "runbooks/database-failover.md#failover-procedure",
            "runbooks/database-failover.md#pre-failover-validation"
        ]
    },
    # ... more test cases
]

# Run evaluation
results = evaluate_retrieval(test_cases)

# Metrics:
# - Precision@K: How many retrieved docs are relevant?
# - Recall@K: How many relevant docs were retrieved?
# - MRR: Mean Reciprocal Rank of first relevant result
# - NDCG: Normalized Discounted Cumulative Gain
```

**4.2 Chunking Strategy Comparison**

Compare different chunking strategies on same queries:

```bash
python tools/compare_chunking.py \
  --strategies naive,layout-aware,abstract-first \
  --test-set test_queries.json

# Output:
# Strategy       | Precision@3 | Recall@5 | MRR   | Avg Latency
# -------------- | ----------- | -------- | ----- | -----------
# naive          | 0.42        | 0.58     | 0.35  | 45ms
# layout-aware   | 0.78        | 0.82     | 0.71  | 38ms
# abstract-first | 0.83        | 0.88     | 0.79  | 28ms
```

**4.3 Hallucination Detection**

Test if LLM generates content not present in retrieved chunks:

```python
def detect_hallucination(query, retrieved_chunks, llm_response):
    # Extract claims from LLM response
    claims = extract_claims(llm_response)

    # Check if each claim is grounded in retrieved chunks
    for claim in claims:
        if not is_supported(claim, retrieved_chunks):
            flag_hallucination(claim)
```

---

### 5. Interactive Demo & UI (P3 - Nice to Have)

**Status**: Proposed
**Effort**: 3-5 days
**Value**: Medium - makes project more accessible to non-technical users

#### Components

**5.1 Web Interface for RAG System**
- Streamlit or Gradio web app
- Query input box
- Display retrieved chunks with similarity scores
- Show LLM response with sources
- Toggle chunking strategies in real-time

**5.2 Chunking Visualizer**
- Upload markdown file
- Visualize how different strategies chunk it
- Show token counts per chunk
- Highlight sections outside sweet spot
- Export chunked output

**5.3 Documentation Browser**
- Browse sre_wiki_example/ content
- Search with RAG system
- View chunk metadata
- See which chunks were retrieved for each query

---

### 6. Real-World Integration Examples (P2 - Medium Value)

**Status**: Proposed
**Effort**: 5-7 days
**Value**: Medium - demonstrates end-to-end integration

#### Integrations to Build

**6.1 Confluence Wiki Connector**
- Export Confluence pages via API
- Convert Confluence HTML to markdown
- Apply layout-aware chunking
- Ingest into RAG system
- Bi-directional sync (update detection)

**6.2 GitHub Wiki Connector**
- Clone GitHub wiki repository
- Parse markdown files
- Extract metadata from frontmatter
- Chunk and index
- Incremental updates via git pull

**6.3 Notion Connector**
- Export Notion database via API
- Convert Notion blocks to markdown
- Preserve hierarchical structure
- Chunk and index

**6.4 Slack Integration**
- Slack bot that answers questions using RAG
- User asks: "How do I restart the auth service?"
- Bot retrieves relevant runbook chunks
- Returns answer with source links

---

### 7. Production Deployment Examples (P2 - Medium Value)

**Status**: Proposed
**Effort**: 4-6 days
**Value**: Medium - shows Module 06 (Production Deployment) in action

#### Examples to Build

**7.1 Docker Compose Stack**
- ChromaDB container
- RAG API container
- Frontend container
- Nginx reverse proxy
- Volume mounts for persistence

**7.2 Kubernetes Deployment**
- Deployment manifests
- Service definitions
- Ingress configuration
- Persistent volume claims
- ConfigMap for embeddings model

**7.3 Incremental Indexing**
```python
# Detect changed files
changed_files = detect_changes(since=last_index_time)

# Re-chunk and re-index only changed files
for file in changed_files:
    chunks = chunk_file(file)
    index(chunks)

# Update timestamp
save_last_index_time(now())
```

**7.4 Deduplication**
```python
# Detect duplicate chunks via embedding similarity
for new_chunk in new_chunks:
    similar = find_similar(new_chunk, threshold=0.95)
    if similar:
        merge_or_skip(new_chunk, similar)
```

---

### 8. Curriculum Enhancements (P3 - Nice to Have)

**Status**: Proposed
**Effort**: Ongoing
**Value**: Medium - keeps curriculum current

#### Enhancements

**8.1 Code Examples in Modules**
- Add Python/TypeScript code snippets to modules
- Show concrete implementations of concepts
- Provide copy-paste-able examples

**8.2 Interactive Exercises**
- Jupyter notebooks for hands-on learning
- "Try it yourself" sections in modules
- Quiz questions with answer keys

**8.3 Video Walkthroughs**
- Screen recordings demonstrating concepts
- Chunking strategy comparisons (visual)
- RAG system implementation walkthrough

**8.4 Case Studies**
- Real-world RAG system implementations
- Lessons learned from production deployments
- Interview-style content with practitioners

---

## Prioritization Framework

When deciding what to work on next, consider:

1. **Educational Value**: Does it help users learn RAG principles?
2. **Practical Value**: Does it solve a real problem users face?
3. **Implementation Effort**: Is the ROI high enough?
4. **Dependencies**: Are prerequisites already in place?
5. **Maintenance Burden**: How much ongoing work is required?

### Quick Wins (High Value, Low Effort)
- Token counter tool (P1, 1 day)
- Content templates (P2, 1 day)
- Abstract generator (P1, 1-2 days)

### High Impact (High Value, High Effort)
- Multi-stage retrieval (P2, 3-5 days)
- Evaluation framework (P1, 2-3 days)
- Real-world integrations (P2, 5-7 days)

### Deferred (Lower Priority)
- Interactive demo UI (P3)
- Video walkthroughs (P3)
- Notion connector (P2 but low demand)

---

## Contributing

To propose a new feature:
1. Create a file in `future_features/` using the template
2. Tag with priority (P1/P2/P3)
3. Estimate effort in days
4. Describe problem and solution
5. Optional: Create proof-of-concept in `future_features/experiments/`

To implement a feature:
1. Move file from `future_features/` to `in_progress/`
2. Update status and assign owner
3. Create implementation branch
4. Move to `completed/` when done (link to PR)

---

## Template

See `_TEMPLATE.md` for the feature proposal template.
