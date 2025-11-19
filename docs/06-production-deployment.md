# Module 06: Production Deployment

**Learning Objectives:**
- Design incremental indexing strategies to avoid wasteful re-processing
- Implement deduplication at ingestion and retrieval time
- Handle document versioning and temporal queries
- Apply scaling patterns for high-volume production systems
- Optimize costs through informed architectural decisions
- Monitor RAG system health and debug quality degradation

**Prerequisites:** Modules 01-05 (chunking, embeddings, retrieval, implementation)

**Time:** 45-60 minutes

---

## Introduction: Operational Realities

Building a RAG system that works in your development environment is one thing. Running it in production with:

- 100,000+ documents growing daily
- Multiple teams with conflicting content versions
- Sub-second latency requirements
- Cost accountability
- 24/7 reliability expectations

...is entirely different.

This module addresses the operational challenges that emerge at scale. These aren't "nice to have" optimizations—they're requirements for production systems that must be reliable, cost-effective, and maintainable.

---

## 1. Incremental Indexing

### The Problem

**Naive approach:** When any document changes, re-process and re-index everything.

**Why this fails:**

- **Time:** Re-indexing 100,000 documents takes hours
- **Cost:** Embedding APIs charge per token—re-embedding unchanged content wastes money
- **Downtime:** Full re-index requires index rebuild or versioning
- **Resource contention:** Batch re-indexing spikes CPU/memory, impacting live queries

**Reality:** In production, documents change continuously. Runbooks get updated, new incidents get logged, configs get modified. You need **incremental updates**.

### Strategies

#### 1.1 Content Hashing

**Concept:** Detect which documents actually changed.

**Implementation:**

```python
import hashlib

def content_hash(document_text):
    """Generate stable hash of document content."""
    return hashlib.sha256(document_text.encode('utf-8')).hexdigest()

def needs_reindexing(doc_id, current_text, index):
    """Check if document changed since last index."""
    stored_hash = index.get_metadata(doc_id, 'content_hash')
    current_hash = content_hash(current_text)
    return stored_hash != current_hash
```

**Schema Addition:**

```json
{
  "chunk_id": "doc123_chunk002",
  "content_hash": "a3f5b8c9d2e1...",
  "indexed_at": "2024-11-18T10:30:00Z"
}
```

**Workflow:**

1. Document arrives for indexing
2. Compute content hash
3. Query index: "Does doc with this hash exist?"
4. **If yes:** Skip (already indexed)
5. **If no:** Process and index

**Caveat:** Metadata changes (update timestamp, access control) require re-indexing even if content unchanged. Hash content + metadata together if metadata is query-relevant.

#### 1.2 Change Detection via Git Integration

**For version-controlled content (runbooks, IaC, docs):**

```bash
# Detect changed files since last index
git diff --name-only HEAD~1 HEAD

# Process only changed files
changed_files = [
    "runbooks/auth-service-restart.md",
    "terraform/prod/database.tf"
]

for file in changed_files:
    reindex_document(file)
```

**Schema Addition:**

```json
{
  "chunk_id": "doc123_chunk002",
  "git_sha": "a3f5b8c9d2e1f4a7b3c8d9e2f1a4b7c8",
  "git_path": "runbooks/auth-service-restart.md"
}
```

**Operational Benefit:** Tie indexing to your CI/CD pipeline. On merge to main, automatically index changed docs.

#### 1.3 Upsert Operations

**Instead of:** Delete old chunks → Insert new chunks

**Use:** Upsert (update if exists, insert if new)

**Vector DB Support:**

Most vector databases support upsert with unique IDs:

```python
# Weaviate example
client.data_object.replace(
    class_name="Document",
    uuid=chunk_id,  # Deterministic ID
    data_object=chunk_data
)

# Pinecone example
index.upsert(
    vectors=[
        (chunk_id, embedding, metadata)
    ]
)
```

**Deterministic ID Generation:**

```python
def generate_chunk_id(doc_path, section_index):
    """Generate stable ID for chunk."""
    # Ensures same document + section always gets same ID
    return f"{hash(doc_path)}_{section_index}"
```

**Why This Matters:**

- No orphaned chunks from failed deletions
- Atomic updates (old chunk immediately replaced)
- Simpler error handling

### Trade-offs

| Approach | Benefit | Cost |
|----------|---------|------|
| **Content Hashing** | Skip unchanged docs entirely | Hash computation overhead; doesn't detect metadata-only changes |
| **Git Integration** | Leverages existing version control | Only works for version-controlled content; requires git access |
| **Upsert** | Atomic updates, no orphans | Requires deterministic IDs; some vector DBs have slower upsert than insert |

**Decision Point:** If your content is version-controlled, use git integration. Otherwise, content hashing is universal.

---

## 2. Deduplication

### The Problem

**Sources of duplication:**

1. **Exact duplicates:** Same content indexed multiple times (ingestion bug, re-runs)
2. **Near-duplicates:** License headers, boilerplate, templated sections
3. **Conflicting versions:** Same document, different versions (old + new both indexed)

**Impact:**

- **Context pollution:** LLM receives 3 copies of the same information, wasting tokens
- **Precision degradation:** Retrieval returns redundant results instead of diverse information
- **User confusion:** "Why am I seeing the same thing three times?"

### Strategies

#### 2.1 Ingestion-Time Deduplication (Exact)

**Hash-based detection:**

```python
def ingest_chunk(chunk_text, metadata, index):
    """Deduplicate at ingestion time."""
    content_hash = hashlib.md5(chunk_text.encode('utf-8')).hexdigest()

    # Check if this exact content exists
    existing = index.query_by_hash(content_hash)

    if existing:
        # Content already indexed
        # Option 1: Skip entirely
        logger.info(f"Duplicate content, skipping: {content_hash}")
        return existing.chunk_id

        # Option 2: Add metadata reference to existing chunk
        index.update_metadata(
            chunk_id=existing.chunk_id,
            additional_sources=[metadata['doc_path']]
        )
        return existing.chunk_id
    else:
        # New content, index it
        return index.insert(chunk_text, metadata)
```

**Schema Addition:**

```json
{
  "chunk_id": "chunk_abc123",
  "content_hash": "d3b07384d113edec49eaa6238ad5ff00",
  "source_documents": [
    "runbooks/service-a/restart.md",
    "runbooks/service-b/restart.md"  # Same procedure, two locations
  ]
}
```

**When Useful:**

- License headers appear in every Terraform file
- Standard procedures copied across runbooks
- Template content (incident post-mortem structure)

#### 2.2 Ingestion-Time Deduplication (Near-Exact)

**SimHash for fuzzy matching:**

```python
from simhash import Simhash

def near_duplicate_detection(chunk_text, index, threshold=3):
    """Detect near-duplicates using SimHash."""
    chunk_simhash = Simhash(chunk_text)

    # Query index for similar hashes
    for existing_chunk in index.iterate_chunks():
        existing_simhash = Simhash(existing_chunk.text)
        hamming_distance = chunk_simhash.distance(existing_simhash)

        if hamming_distance <= threshold:
            # Near-duplicate detected
            return existing_chunk.chunk_id

    return None  # Not a duplicate
```

**Trade-off:**

- **Pro:** Catches boilerplate with minor variations ("© 2023" vs "© 2024")
- **Con:** Expensive to compute for every chunk; requires threshold tuning

**When Useful:**

- Content is frequently copy-pasted with minor edits
- Template-based documentation (post-mortems, runbooks)

**When to Skip:**

- Content is highly unique (incident reports, post-mortems with specific details)
- Ingestion speed is critical (near-duplicate detection is slower than exact hashing)

#### 2.3 Retrieval-Time Deduplication

**Problem:** Even with perfect ingestion-time dedup, retrieval can return duplicates:

- Parent-child retrieval: 3 child chunks point to same parent → parent retrieved 3 times
- Multi-query expansion: Same chunk matches 2 different query variants
- Overlapping chunks: Sliding window creates intentional overlap

**Solution: Post-retrieval deduplication**

**From Research:**

> "If multiple child chunks point to the same parent_id, the system should collapse them. Instead of retrieving Parent Doc A three times (triggered by Child 1, Child 2, and Child 5), retrieve it once."

**Implementation:**

```python
def deduplicate_retrieved_chunks(chunks):
    """Remove duplicate parent documents."""
    seen = {}  # parent_id -> highest scoring chunk

    for chunk in chunks:
        parent_id = chunk.metadata.get('parent_id', chunk.chunk_id)

        if parent_id not in seen:
            seen[parent_id] = chunk
        else:
            # Keep highest scoring variant
            if chunk.score > seen[parent_id].score:
                seen[parent_id] = chunk

    return list(seen.values())
```

**From Research (Implementation Spec):**

> "Group Stage-2 results by section_id. Keep the highest-scoring full_text chunk if present; otherwise keep the abstract. If multiple tenant_id or version_hash variants exist, prefer the newest updated_at that still satisfies the user's temporal filter."

**Operational Benefit:** Ensures LLM context contains diverse information, not repetitive content.

#### 2.4 Conflicting Versions

**Problem:** Old runbook says "restart with systemctl," new version says "use Kubernetes rolling restart." Both indexed.

**Impact:** LLM mixes old and new instructions → dangerous for production operations.

**Solution 1: Version Filtering (Prefer Latest)**

```python
def deduplicate_by_version(chunks):
    """Keep only newest version of each document."""
    by_document = {}  # doc_path -> chunk

    for chunk in chunks:
        doc_path = chunk.metadata['doc_path']

        if doc_path not in by_document:
            by_document[doc_path] = chunk
        else:
            # Compare timestamps
            existing_ts = by_document[doc_path].metadata['updated_at']
            new_ts = chunk.metadata['updated_at']

            if new_ts > existing_ts:
                by_document[doc_path] = chunk

    return list(by_document.values())
```

**Schema Requirements:**

```json
{
  "chunk_id": "chunk_abc123",
  "doc_path": "runbooks/auth-service-restart.md",
  "version_hash": "git_sha_a3f5b8c9",
  "updated_at": "2024-11-18T10:30:00Z"
}
```

**Solution 2: Explicit Versioning + Deprecation**

**For critical content (runbooks, procedures):**

```json
{
  "chunk_id": "chunk_abc123",
  "doc_path": "runbooks/auth-service-restart.md",
  "version": "2.1",
  "status": "active",  // or "deprecated", "archived"
  "deprecation_date": null
}
```

**Query Filter:**

```python
# Only retrieve active versions
results = index.search(
    query=user_query,
    filter={"status": "active"}
)
```

**Operational Pattern:**

When updating a runbook:
1. Mark old version as "deprecated"
2. Set deprecation_date = today
3. Index new version as "active"
4. After 30 days, archive or delete deprecated versions

**Why 30 days?** Gives time to catch errors in new version, allows rollback if needed.

### Summary: Deduplication Strategy by Use Case

| Use Case | Strategy | When to Apply |
|----------|----------|---------------|
| **License headers, boilerplate** | Exact hash dedup (ingestion) | Always |
| **Template content with minor variations** | Near-duplicate (SimHash) | If templates are prevalent |
| **Parent-child retrieval** | Post-retrieval parent collapse | Always with parent-child pattern |
| **Multi-query expansion** | Post-retrieval chunk_id dedup | Always with multi-query |
| **Version conflicts** | Temporal filtering + version metadata | Critical for operational docs |

---

## 3. Version Control and Temporal Queries

### The Problem

**SRE Reality:** Yesterday's runbook may be dangerous today.

**Example:**

- **Nov 1:** "Restart auth-service with: `systemctl restart auth-service`"
- **Nov 15:** Migrated to Kubernetes: "Restart with: `kubectl rollout restart deployment/auth-service`"
- **User query (Nov 20):** "How do I restart auth-service?"

**If both versions are indexed:** LLM may mix instructions → user tries `systemctl` on K8s cluster → fails.

### Solution 1: Time-Weighted Reranking

**Penalize old content in ranking:**

**From Research:**

> "In Stage 2 (Reranking), the scoring function should include a decay parameter based on the last_updated metadata timestamp. Documents that are older should receive a penalty in the final ranking, pushing newer solutions to the top."

**Implementation:**

```python
import math
from datetime import datetime, timezone

def time_weighted_score(base_score, updated_at, decay_days=30):
    """Apply temporal decay to retrieval score."""
    now = datetime.now(timezone.utc)
    age_days = (now - updated_at).days

    # Exponential decay: score drops 50% every decay_days
    decay_factor = math.exp(-age_days / decay_days)

    return base_score * decay_factor

# Example
chunk_score = 0.85  # High semantic match
chunk_updated = datetime(2024, 10, 1, tzinfo=timezone.utc)  # 48 days old

adjusted_score = time_weighted_score(chunk_score, chunk_updated, decay_days=30)
# Result: 0.85 * 0.31 = 0.26 (significantly downranked)
```

**Tuning `decay_days`:**

- **Fast-moving content (cloud configs, APIs):** decay_days=14 (2 weeks)
- **Stable content (architecture docs):** decay_days=180 (6 months)
- **Regulatory content (compliance procedures):** decay_days=365+ (or don't decay at all)

### Solution 2: Explicit Version Filtering

**Allow users to specify time bounds:**

```python
# Query for current information
results = index.search(
    query="How do I restart auth-service?",
    filter={
        "updated_at": {"gte": "2024-11-01"}  # Only docs updated after Nov 1
    }
)

# Query for historical information (incident investigation)
results = index.search(
    query="How did we restart auth-service during the Oct 15 incident?",
    filter={
        "updated_at": {"gte": "2024-10-01", "lte": "2024-10-31"}
    }
)
```

**Use Case: Post-Incident Investigation**

When investigating an incident from October, you need the runbook *as it existed in October*, not the current version.

**Schema:**

```json
{
  "chunk_id": "chunk_abc123",
  "doc_path": "runbooks/auth-service-restart.md",
  "version_hash": "git_sha_a3f5b8c9",
  "created_at": "2024-09-01T00:00:00Z",
  "updated_at": "2024-10-15T14:30:00Z",
  "valid_from": "2024-10-15T14:30:00Z",
  "valid_until": null  // null = currently valid
}
```

**Versioning Workflow:**

1. New version indexed: `valid_from = now, valid_until = null`
2. Old version updated: `valid_until = now`
3. Query with time bound: Filter by `valid_from <= query_time <= valid_until`

### Solution 3: Rolling Index for High-Volume Logs

**For time-series data (logs, metrics, alerts):**

**From Research:**

> "For high-volume log data, a 'Rolling Index' strategy is required. Data older than a defined retention period (e.g., 30 days) should be automatically purged or moved to a 'Cold Tier' collection to maintain index performance and relevance."

**Architecture:**

```
Hot Tier (0-7 days):    Fast SSD, indexed for real-time queries
Warm Tier (8-30 days):  Slower storage, still indexed
Cold Tier (31-90 days): Archive storage, not indexed (query if needed)
Deleted (>90 days):     Purged
```

**Implementation:**

```python
# Daily cron job
def roll_index():
    """Move old data to cold tier, delete ancient data."""
    now = datetime.now(timezone.utc)

    # Move to warm tier
    warm_cutoff = now - timedelta(days=7)
    hot_to_warm = index.query(
        filter={"indexed_at": {"lt": warm_cutoff}, "tier": "hot"}
    )
    for chunk in hot_to_warm:
        move_to_tier(chunk, "warm")

    # Move to cold tier
    cold_cutoff = now - timedelta(days=30)
    warm_to_cold = index.query(
        filter={"indexed_at": {"lt": cold_cutoff}, "tier": "warm"}
    )
    for chunk in warm_to_cold:
        move_to_cold_storage(chunk)
        index.delete(chunk.chunk_id)

    # Delete old data
    delete_cutoff = now - timedelta(days=90)
    to_delete = cold_storage.query(
        filter={"indexed_at": {"lt": delete_cutoff}}
    )
    cold_storage.delete_many(to_delete)
```

**Operational Benefit:**

- Keeps index size bounded (better query performance)
- Reduces storage costs (cold tier is cheaper)
- Enforces retention policies (compliance, GDPR)

### Trade-offs

| Approach | Benefit | Cost |
|----------|---------|------|
| **Time-Weighted Reranking** | Automatic freshness bias | Requires tuning decay parameter; may over-penalize stable docs |
| **Explicit Version Filtering** | Precise temporal queries | Requires user to specify time bounds; complex for casual users |
| **Rolling Index** | Bounded index size, predictable performance | Data loss after retention period; cold tier queries are slow |

**Decision Point:** For operational docs (runbooks, configs), use time-weighted reranking + version metadata. For logs/metrics, use rolling index.

---

## 4. Scaling Patterns

### When to Worry About Scale

**Thresholds where naive approaches fail:**

- **10,000+ documents:** Full re-indexing takes hours
- **100,000+ documents:** Vector search latency degrades without tuning
- **1M+ documents:** Single-index architecture becomes bottleneck
- **High query volume (>100 QPS):** Need horizontal scaling, caching

### 4.1 Sharding

**Concept:** Partition index into multiple smaller indices.

**Sharding Strategies:**

**By Tenant (Multi-Tenancy):**

```
Index Structure:
- index_tenant_teamA (10k docs)
- index_tenant_teamB (15k docs)
- index_tenant_teamC (8k docs)
```

**Query Routing:**

```python
def query_by_tenant(user_query, tenant_id):
    """Route query to tenant-specific index."""
    index = get_index(f"index_tenant_{tenant_id}")
    return index.search(user_query)
```

**Benefit:** Perfect isolation, scales horizontally, simpler access control

**By Service/Domain:**

```
Index Structure:
- index_auth_service (5k docs)
- index_payment_service (7k docs)
- index_database (3k docs)
```

**Query Routing:**

```python
def query_by_service(user_query, service_name=None):
    """Route query to service-specific index."""
    if service_name:
        # User specified service context
        index = get_index(f"index_{service_name}")
        return index.search(user_query)
    else:
        # Query all indices, merge results
        all_results = []
        for service in ["auth", "payment", "database"]:
            index = get_index(f"index_{service}")
            results = index.search(user_query, k=5)
            all_results.extend(results)
        return rerank_and_deduplicate(all_results, k=10)
```

**Benefit:** Domain expertise, smaller index = faster queries

**By Time (Logs/Metrics):**

```
Index Structure:
- index_2024_11_18 (today's logs)
- index_2024_11_17 (yesterday)
- index_2024_11_16
```

**Query Routing:**

```python
def query_by_timerange(user_query, start_date, end_date):
    """Query relevant time-partitioned indices."""
    indices = get_indices_for_range(start_date, end_date)

    all_results = []
    for index in indices:
        results = index.search(user_query, k=10)
        all_results.extend(results)

    return rerank_and_deduplicate(all_results, k=20)
```

**Benefit:** Time-based queries only touch relevant indices, old indices can be archived

### 4.2 Hierarchical Indexing

**Concept:** Two-stage retrieval using document-level and chunk-level indices.

**Architecture:**

```
Stage 1: Document-Level Index
- One vector per document (average of chunk embeddings or summary embedding)
- Fast: 100k documents → retrieve top 100 documents

Stage 2: Chunk-Level Index
- Within top 100 documents, search chunks
- Precise: 10k chunks (from 100 docs) → retrieve top 10 chunks
```

**Implementation:**

```python
def hierarchical_search(user_query, k=10):
    """Two-stage hierarchical retrieval."""
    # Stage 1: Document-level filter
    doc_results = doc_index.search(user_query, k=100)
    doc_ids = [r.doc_id for r in doc_results]

    # Stage 2: Chunk-level retrieval within top docs
    chunk_results = chunk_index.search(
        query=user_query,
        filter={"doc_id": {"in": doc_ids}},
        k=k
    )

    return chunk_results
```

**Benefit:**

- Reduces search space (10M chunks → 100 docs → 10k chunks → 10 results)
- Faster than flat search over all chunks
- Natural fit for parent-child retrieval pattern

**Trade-off:** Two retrieval calls add latency; document-level index may filter out relevant chunks if document summary is poor

### 4.3 ANN Parameter Tuning

**Approximate Nearest Neighbor (ANN) indices trade recall for speed.**

**HNSW (Hierarchical Navigable Small World) Parameters:**

**`ef_construction` (build time):**
- Higher = better graph connectivity = better recall
- Default: 100-200
- High-quality use case: 400-800 (slower build, better recall)

**`M` (max connections per node):**
- Higher = more connections = better recall, larger index
- Default: 16
- High-quality use case: 32-64

**`ef_search` (query time):**
- Higher = explore more paths = better recall, slower queries
- Default: 50-100
- High-quality use case: 200-500

**Tuning Process:**

1. **Measure baseline recall** on evaluation dataset
2. **Increase `ef_search`** until recall plateaus
3. **If recall still insufficient**, increase `M` and rebuild index
4. **Balance:** Find minimum `ef_search` that meets recall target

**Example:**

```python
# Low-quality, fast
index = HNSWIndex(M=16, ef_construction=100, ef_search=50)
# Recall@10: 0.85, Latency: 20ms

# High-quality, slower
index = HNSWIndex(M=32, ef_construction=400, ef_search=200)
# Recall@10: 0.95, Latency: 80ms

# Decision: Is +0.10 recall worth +60ms latency?
```

### 4.4 Caching

**Query Result Caching:**

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def cached_search(query_hash, k):
    """Cache frequent queries."""
    return index.search(query_from_hash(query_hash), k=k)

def search_with_cache(user_query, k=10):
    query_hash = hashlib.md5(user_query.encode()).hexdigest()
    return cached_search(query_hash, k)
```

**When Useful:**

- Frequently repeated queries ("How do I restart auth-service?")
- Documentation search (same questions asked repeatedly)
- Public-facing RAG (limited query diversity)

**When to Skip:**

- Highly dynamic content (logs, real-time data)
- Personalized queries (tenant-specific, access-controlled)
- Large query diversity (every query is unique)

**Invalidation:**

```python
def on_document_update(doc_id):
    """Invalidate cache when document changes."""
    # Option 1: Clear entire cache (simple, wasteful)
    cached_search.cache_clear()

    # Option 2: Track which queries hit which docs, invalidate selectively
    affected_queries = query_doc_tracker.get_queries_for_doc(doc_id)
    for query_hash in affected_queries:
        cached_search.cache_info()  # Manual invalidation
```

### Scaling Summary

| Pattern | When to Apply | Complexity |
|---------|---------------|------------|
| **Sharding (tenant)** | Multi-tenant SaaS, >100k docs | Medium (routing logic) |
| **Sharding (service)** | Microservices architecture, domain isolation | Medium (service detection) |
| **Sharding (time)** | High-volume logs, time-series data | Low (simple date logic) |
| **Hierarchical indexing** | >1M chunks, parent-child pattern already in use | Medium (two-stage retrieval) |
| **ANN tuning** | Recall <90%, latency budget allows | Low (parameter tuning) |
| **Query caching** | Repeated queries, stable content | Low (LRU cache) |

**Decision Framework:**

1. **<100k docs:** No scaling needed, focus on chunking quality
2. **100k-1M docs:** Tune ANN parameters, consider sharding by tenant/service
3. **>1M docs:** Mandatory sharding + hierarchical indexing
4. **High QPS:** Add caching, horizontal scale query nodes

---

## 5. Cost Considerations

### Cost Drivers

**Where money goes in RAG systems:**

1. **Embedding API costs** (if using OpenAI, Cohere, etc.)
2. **Vector database storage** (per GB/month)
3. **Compute for indexing** (CPU/GPU for embedding generation)
4. **Compute for queries** (vector search, reranking)
5. **LLM generation** (answering queries)

### Optimization Strategies

#### 5.1 Batch Embedding Generation

**Don't:** Embed one chunk at a time (high latency, poor throughput)

**Do:** Batch 100-1000 chunks per API call

```python
# Inefficient
for chunk in chunks:
    embedding = openai.Embedding.create(input=chunk.text)

# Efficient
chunk_texts = [c.text for c in chunks]
embeddings = openai.Embedding.create(input=chunk_texts)  # Batch call
```

**Savings:** 10x throughput improvement, same cost

#### 5.2 Self-Hosted Embeddings

**API Costs (example):**
- OpenAI `text-embedding-3-small`: $0.02 per 1M tokens
- Cohere `embed-english-v3.0`: $0.10 per 1M tokens

**Self-Hosted Costs:**
- GPU instance (A10G): $1.00/hour = $720/month
- Can embed 10M+ tokens/hour

**Break-even:** If you embed >36M tokens/month, self-hosting is cheaper

**Models for self-hosting:**
- `sentence-transformers/all-MiniLM-L6-v2` (lightweight, fast)
- `BAAI/bge-large-en-v1.5` (high quality)
- `intfloat/e5-large-v2` (good balance)

#### 5.3 Storage Optimization

**Vector Compression:**

Most vector DBs support quantization:

```
Full precision (float32): 1024 dimensions × 4 bytes = 4 KB per vector
Quantized (uint8):        1024 dimensions × 1 byte = 1 KB per vector
```

**Savings:** 75% storage reduction

**Trade-off:** ~2-5% recall loss (usually acceptable)

**Matryoshka Embeddings:**

Use variable-length vectors for hierarchical search:

```
Document-level index: 256-dim vectors (smaller, faster)
Chunk-level index:    1024-dim vectors (full precision)
```

**Savings:** 75% reduction in document-level index size

#### 5.4 Retrieval Cost Control

**Cross-encoder reranking is expensive:**

- Processes each query-document pair through transformer
- For k=100 results, 100 forward passes

**Optimization:** Rerank fewer candidates

```python
# Expensive: Rerank 100 candidates
hybrid_results = hybrid_search(query, k=100)
reranked = cross_encoder.rerank(query, hybrid_results)

# Cheaper: Rerank top 20 candidates
hybrid_results = hybrid_search(query, k=20)
reranked = cross_encoder.rerank(query, hybrid_results)
```

**Decision:** Measure if reranking beyond top-20 improves quality. Often it doesn't.

#### 5.5 LLM Generation Costs

**Where most cost goes:** Feeding large contexts to LLMs

**Optimization: Context Packing**

**From Research (Implementation Spec):**

> "Merge adjacent sections from the same document before passing to the LLM. If Chunks 3, 4, and 5 from Document X all appear in the result set, concatenate them into one context block to reduce redundant document framing overhead."

**Example:**

**Before packing:**
```
Context:
Document: auth-service-runbook.md, Section 2: Prerequisites
[500 tokens]

Document: auth-service-runbook.md, Section 3: Restart Procedure
[600 tokens]

Document: auth-service-runbook.md, Section 4: Validation
[400 tokens]

Total: 1500 tokens + 3 × document framing overhead
```

**After packing:**
```
Context:
Document: auth-service-runbook.md, Sections 2-4
[1500 tokens]

Total: 1500 tokens + 1 × document framing overhead
```

**Savings:** Reduced token count (eliminates redundant framing), better coherence

### Cost Modeling Example

**Scenario:** 100,000 documents, 10,000 queries/month

**Indexing Costs (one-time + updates):**

- 100k documents × 500 tokens/doc (average) = 50M tokens
- Embedding cost: $0.02 per 1M tokens = **$1.00**
- Monthly updates: 10% churn = 10k docs = **$0.10/month**

**Query Costs:**

- 10k queries/month
- Average 3 chunks retrieved per query = 30k chunk retrievals
- Vector search: Negligible (self-hosted or included in DB cost)
- LLM generation: 10k queries × 2000 tokens context × $0.50 per 1M tokens = **$10.00/month**

**Total: ~$11/month** (LLM generation dominates)

**Optimization Impact:**

- Reduce context from 2000 → 1500 tokens via packing: **25% savings → $8.25/month**
- Cache 30% of queries: **30% savings → $7.70/month**

**Key Insight:** Focus optimization on LLM generation costs (context reduction, caching), not embedding costs.

---

## 6. Content Freshness

### TTL (Time-To-Live) Policies

**Concept:** Auto-expire content after a certain age.

**Use Cases:**

- **Incident alerts:** Expire after 30 days (no longer actionable)
- **Temporary procedures:** "Black Friday readiness" expires after Dec 1
- **Beta documentation:** Expires when feature reaches GA

**Implementation:**

```python
# Schema
{
  "chunk_id": "chunk_abc123",
  "expires_at": "2024-12-01T00:00:00Z"
}

# Query filter
def search_active_content(query):
    now = datetime.now(timezone.utc)
    return index.search(
        query=query,
        filter={"expires_at": {"gte": now}}
    )
```

**Operational Pattern:**

Daily cron job purges expired content:

```python
def purge_expired():
    now = datetime.now(timezone.utc)
    expired = index.query(filter={"expires_at": {"lt": now}})
    index.delete_many([c.chunk_id for c in expired])
```

### Update Propagation

**Problem:** Document updated in git, but index still has old version.

**Solution: Webhook-Triggered Re-Indexing**

```python
# GitHub webhook handler
@app.post("/webhook/github")
def handle_github_push(event):
    """Re-index changed files on git push."""
    changed_files = event['commits'][0]['modified']

    for file_path in changed_files:
        if file_path.endswith('.md'):
            # Fetch updated content
            content = fetch_file_from_github(file_path)
            # Re-index
            reindex_document(file_path, content)

    return {"status": "ok"}
```

**Latency:** Index updates within seconds of git push

### Staleness Detection

**Metric:** How old is the average retrieved chunk?

```python
def monitor_content_freshness(retrieved_chunks):
    """Alert if retrieved content is too old."""
    now = datetime.now(timezone.utc)
    ages = [(now - c.metadata['updated_at']).days for c in retrieved_chunks]

    avg_age = sum(ages) / len(ages)
    max_age = max(ages)

    if avg_age > 90:
        alert("Average retrieved content is >90 days old")
    if max_age > 180:
        alert("Retrieved content includes docs >180 days old")
```

**Red Flag:** If average age increases over time, your content is going stale.

**Response:** Audit which documents are out of date, prioritize updates.

---

## 7. Monitoring and Observability

### What to Track

#### 7.1 Query Metrics

**Zero-result rate:**

```python
def track_zero_results(query, results):
    if len(results) == 0:
        metrics.increment('rag.zero_results')
        logger.warning(f"Zero results for query: {query}")
```

**Red Flag:** Increasing zero-result rate indicates:

- Content gaps (missing documentation)
- Vocabulary mismatch (queries use terms not in docs)
- Index corruption

**Low-result rate (< 5 results):**

Similarly track queries returning very few results.

#### 7.2 Retrieval Quality

**Top-K Recall (requires labeled data):**

```python
def measure_recall_at_k(eval_dataset, k=10):
    """Measure if relevant docs appear in top-K."""
    correct = 0
    for query, expected_doc_ids in eval_dataset:
        results = index.search(query, k=k)
        retrieved_ids = {r.doc_id for r in results}

        if any(doc_id in retrieved_ids for doc_id in expected_doc_ids):
            correct += 1

    return correct / len(eval_dataset)
```

**Red Flag:** Recall@10 dropping from 0.90 → 0.75 indicates quality degradation.

**Causes:**

- New content with different vocabulary (need embedding model update)
- Index corruption
- Chunking changes that fragmented content

#### 7.3 Latency Distribution

**Track P50, P95, P99:**

```python
from prometheus_client import Histogram

query_latency = Histogram(
    'rag_query_latency_seconds',
    'RAG query latency distribution',
    buckets=[0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]
)

@query_latency.time()
def search(query):
    return index.search(query)
```

**Red Flag:** P95 latency increasing indicates:

- Index size growth (need sharding or ANN tuning)
- Resource contention (need more query nodes)
- Slow queries (need query optimization)

#### 7.4 Index Health

**Chunk count over time:**

```python
def monitor_index_size():
    chunk_count = index.count()
    metrics.gauge('rag.index.chunk_count', chunk_count)
```

**Red Flag:** Unexpected spikes (indexing duplicates) or drops (data loss)

**Chunk size distribution:**

```python
def monitor_chunk_sizes(chunks):
    sizes = [len(c.text.split()) for c in chunks]
    avg_size = sum(sizes) / len(sizes)
    metrics.gauge('rag.chunk.avg_tokens', avg_size)
```

**Red Flag:** Average size drifting from 400-900 token target indicates chunking logic changed

#### 7.5 Deduplication Effectiveness

**From Research:**

> "Emit structured logs capturing the number of chunks per stage, dedupe drops, pack merges, and citations added so we can monitor contextual recall/precision over time."

**Implementation:**

```python
def log_retrieval_pipeline(query, results):
    logger.info({
        "query": query,
        "initial_results": len(results['initial']),
        "dedupe_drops": len(results['duplicates_removed']),
        "pack_merges": len(results['packed']),
        "final_chunks": len(results['final']),
        "latency_ms": results['latency']
    })
```

**Dashboard:** Track dedupe rate over time. If it drops to 0%, dedup logic may be broken.

### Red Flags: What Indicates Problems

| Metric | Threshold | Likely Cause |
|--------|-----------|--------------|
| **Zero-result rate** | >5% | Vocabulary mismatch, content gaps, index issues |
| **Recall@10** | <0.85 | Chunking fragmentation, embedding model mismatch |
| **P95 latency** | >1000ms | Index size growth, resource contention |
| **Avg chunk age** | >90 days | Content going stale, update pipeline broken |
| **Dedupe rate** | Sudden drop | Deduplication logic failure |
| **Index size** | Unexpected spike | Duplicate ingestion, missing dedup |

### Debugging Workflow

**Issue:** Recall@10 dropped from 0.90 → 0.75

**Investigation:**

1. **Check recent changes:** Did we update chunking logic? Change embedding model?
2. **Sample failing queries:** Which queries now fail that used to work?
3. **Inspect retrieved results:** Are they completely irrelevant, or just lower quality?
4. **Check index health:** Is index size stable? Any corruption?
5. **Review content changes:** Did we add new content with different vocabulary?

**Common Root Causes:**

- Chunking changes fragmented previously complete sections
- Embedding model updated without re-indexing
- New content uses terminology not in old content (vocabulary drift)
- Deduplication removed relevant content by mistake

---

## 8. Operational Runbook

### Daily Operations

**Monitoring Checklist:**

- [ ] Check zero-result rate dashboard
- [ ] Review P95 latency trends
- [ ] Audit content freshness (average age of retrieved chunks)
- [ ] Check index size for unexpected growth

**Alerts to Configure:**

- Zero-result rate >10% (hourly)
- Recall@10 drop >5% (daily)
- P95 latency >2x baseline (5-minute window)
- Index size growth >20%/day (indicates duplicate ingestion)

### Weekly Operations

**Quality Audits:**

- [ ] Run evaluation dataset (Module 07) and track Recall@10
- [ ] Review sample queries for quality issues
- [ ] Audit deduplication effectiveness (check for redundant results)
- [ ] Verify version filtering (newest content appearing first?)

### Monthly Operations

**Capacity Planning:**

- [ ] Review index size growth trend
- [ ] Forecast when sharding will be needed
- [ ] Audit storage costs vs budget
- [ ] Review query volume trends

**Content Health:**

- [ ] Identify stale content (>90 days since update)
- [ ] Audit for deprecated documents still in index
- [ ] Review conflict reports (same doc, multiple versions)

### Incident Response

**Scenario: Recall@10 drops suddenly**

1. **Check recent deployments:** Did we change chunking/embedding?
2. **Sample 10 failing queries:** Run them manually, inspect results
3. **Compare against baseline:** Do same queries work on old index?
4. **If yes:** Rollback recent changes
5. **If no:** Content or query distribution changed
6. **Investigate content changes:** What new documents were added?

**Scenario: P95 latency spikes**

1. **Check index size:** Did it grow unexpectedly?
2. **Check ANN parameters:** Are we searching efficiently?
3. **Check resource usage:** Is DB under load?
4. **Sample slow queries:** Are specific queries slow, or all queries?
5. **If specific queries slow:** Optimize those queries (better filtering)
6. **If all queries slow:** Scale database resources or tune ANN

---

## Summary

Production RAG systems require:

1. **Incremental indexing:** Content hashing or git integration to avoid wasteful re-processing
2. **Deduplication:** At ingestion (exact/near-exact) and retrieval (parent collapse, version filtering)
3. **Version control:** Temporal metadata, time-weighted reranking, rolling indices for logs
4. **Scaling:** Sharding (tenant/service/time), hierarchical indexing, ANN tuning, caching
5. **Cost optimization:** Batch embeddings, self-host if high volume, compress vectors, pack context
6. **Freshness:** TTL policies, webhook-driven updates, staleness monitoring
7. **Observability:** Track zero-results, recall, latency, index health, deduplication effectiveness

**Core Principle:** Operational excellence beats algorithmic sophistication. A well-monitored, incrementally updated, properly deduplicated RAG system with basic retrieval outperforms an advanced system with poor operational hygiene.

**Next Module:** [09-sre-specific-considerations.md](09-sre-specific-considerations.md) - Domain-specific patterns for SRE/operations content

---

## Discussion Questions

1. Your index has 500k documents. Users complain queries are slow (P95 = 2000ms). What's your debugging process?

2. You discover 30% of retrieved chunks are exact duplicates (same content, different source files). How do you fix this at ingestion time vs retrieval time?

3. An incident from 6 months ago is being investigated. The runbook has been updated 3 times since then. How do you ensure users retrieve the version that existed during the incident?

4. Your team indexes 10M tokens/month via OpenAI API at $0.02/1M tokens ($0.20/month). A colleague proposes self-hosting embeddings on a GPU instance ($720/month). Is this cost-effective? At what volume does it make sense?
