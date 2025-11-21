# Simple RAG System for SRE Wiki

A lightweight, local RAG (Retrieval-Augmented Generation) system for the SRE Wiki example. Uses **Python + sentence-transformers + ChromaDB** — no API keys required, runs completely locally.

## Features

- **Local embedding model**: Uses sentence-transformers (no OpenAI API needed)
- **Vector database**: ChromaDB for similarity search
- **Layout-aware chunking**: Respects document structure (H2 section boundaries)
- **Metadata filtering**: Filter by service, severity, content type
- **Dual-storage**: Stores both abstracts and full sections (configurable)
- **Simple query interface**: Command-line and Python API

## Architecture

```
sre_wiki_example/
    ├── runbooks/*.md
    ├── how-to/*.md
    ├── incidents/*.md
    └── ...
         ↓
    [ingest.py]
         ↓
    Chunking (layout-aware, H2 boundaries)
         ↓
    Embedding (sentence-transformers/all-MiniLM-L6-v2)
         ↓
    Storage (ChromaDB vector database)
         ↓
    [query.py]
         ↓
    User Query → Similarity Search → Retrieved Chunks → Display
```

## Installation

### Prerequisites
- Python 3.8+
- ~100MB for ChromaDB index (embedding model may already be cached)

### Quick Setup (Recommended - Reuses Existing Venv)

**One-liner** (uses existing venv from `~/.claude/skills/sentence-embedding/`):

```bash
cd simple_rag_system && source ./activate-venv.sh
```

This automatically:
- ✅ Finds and activates the existing venv
- ✅ Installs only missing dependencies (~30 seconds)
- ✅ Saves ~500MB disk space (reuses sentence-transformers, torch, etc.)

**Manual setup** (same thing, step by step):

```bash
cd simple_rag_system
source ~/.claude/skills/sentence-embedding/venv/bin/activate
pip install -r requirements-minimal.txt
```

### Full Setup (From Scratch)

If you prefer a clean, isolated environment:

```bash
cd simple_rag_system

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all dependencies (~5 minutes, ~500MB)
pip install -r requirements.txt
```

**See [SETUP.md](SETUP.md) for detailed setup options and troubleshooting.**

**See [TESTING.md](TESTING.md) for verification steps and test queries to confirm everything works.**

## Usage

### 1. Index the Wiki

```bash
# Index all documents in sre_wiki_example/
python ingest.py --input ../sre_wiki_example --output ./chromadb_index

# Output:
# Processing: ../sre_wiki_example/runbooks/database-failover.md
#   → 6 sections chunked
#   → 6 embeddings generated
# Processing: ../sre_wiki_example/how-to/kubernetes-debugging-crashloop.md
#   → 8 sections chunked
#   → 8 embeddings generated
# ...
# Total: 17 documents, 94 chunks indexed
# Database saved to: ./chromadb_index
```

**Options**:
- `--strategy`: Chunking strategy (`layout-aware`, `naive`, `abstract-first`) — default: `layout-aware`
- `--model`: Embedding model — default: `sentence-transformers/all-MiniLM-L6-v2`
- `--chunk-size`: For naive chunking only (default: 512 tokens)

### 2. Query the System

```bash
# Interactive mode
python query.py

# Enter your query: How do I restart the auth service?
#
# Results (3 matches):
#
# [1] Score: 0.89 | Source: runbooks/auth-service-restart.md
# Section: Procedure
#
# ## Procedure
# ### Step 1: Validate Current Health
# 1. `kubectl get pods -n auth | grep auth-api`
# 2. `curl -sf https://auth.company.com/health`
# ...
#
# [2] Score: 0.76 | Source: how-to/zero-downtime-deployments.md
# Section: Rolling Update Strategy
# ...
```

**Command-line mode**:
```bash
python query.py --query "database failover procedure" --top-k 5
```

**Options**:
- `--query`: Query string (skip for interactive mode)
- `--top-k`: Number of results to return (default: 3)
- `--filter-service`: Filter by service name (e.g., `auth-service`)
- `--filter-type`: Filter by content type (`runbook`, `how-to`, `incident`)
- `--min-score`: Minimum similarity score threshold (default: 0.5)

### 3. Python API

```python
from simple_rag_system import RAGSystem

# Initialize
rag = RAGSystem(index_path="./chromadb_index")

# Query
results = rag.query(
    query="How do I troubleshoot CrashLoopBackOff?",
    top_k=3,
    filters={"content_type": "how-to"}
)

# Results are list of dicts
for result in results:
    print(f"Score: {result['score']}")
    print(f"Source: {result['source']}")
    print(f"Content: {result['content']}")
    print("---")
```

## Chunking Strategies

### Layout-Aware (Recommended)

Chunks at H2 (`##`) section boundaries. Preserves complete semantic units.

```python
python ingest.py --strategy layout-aware
```

**Pros**:
- Preserves document structure
- Complete procedures/sections in each chunk
- Natural semantic boundaries
- Optimal for procedural content (runbooks, how-tos)

**Cons**:
- Variable chunk sizes (may have some <400 or >900 token chunks)
- Requires well-structured documents with consistent headers

### Naive Fixed-Size

Splits at fixed token count with overlap.

```python
python ingest.py --strategy naive --chunk-size 512
```

**Pros**:
- Predictable chunk sizes
- Works on any content (even unstructured)

**Cons**:
- Breaks procedures mid-step
- Context fragmentation
- Poor retrieval quality for structured docs

### Abstract-First (Experimental)

Generates abstracts for each section, stores both abstract and full content.

```python
python ingest.py --strategy abstract-first
```

**Pros**:
- Hierarchical retrieval (search abstracts first)
- Better precision (fewer false positives)
- Faster retrieval (smaller search space)

**Cons**:
- 25% more storage (abstracts + full content)
- Requires LLM for abstract generation (currently uses simple extraction)

## Configuration

Edit `config.py` to customize:

```python
# Embedding model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# Alternatives:
# - "sentence-transformers/all-mpnet-base-v2" (better quality, slower)
# - "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2" (multilingual)

# Chunking parameters
LAYOUT_AWARE_MAX_TOKENS = 900  # Max tokens per section
LAYOUT_AWARE_MIN_TOKENS = 200  # Min tokens per section (merge smaller)

# Retrieval parameters
DEFAULT_TOP_K = 3
MIN_SIMILARITY_SCORE = 0.5

# Metadata extraction
EXTRACT_SERVICE_NAME = True  # Parse service name from metadata
EXTRACT_SEVERITY = True      # Parse severity (SEV1, SEV2, etc.)
```

## Metadata Schema

Each chunk includes metadata for filtering:

```json
{
    "chunk_id": "runbooks-database-failover-s3",
    "source_file": "runbooks/database-failover.md",
    "section_title": "Failover Procedure",
    "heading_level": "h2",
    "content_type": "runbook",
    "service_name": "PostgreSQL Cluster",
    "environment": "prod-us-east",
    "severity": "SEV1",
    "owner": "sre-data",
    "tokens": 680,
    "contains_code": true
}
```

## Performance

### Indexing
- **Example wiki (17 docs, 94 chunks)**: ~30 seconds on laptop
- **Embedding generation**: ~0.3 seconds per chunk (all-MiniLM-L6-v2)
- **Database storage**: ~5MB for 94 chunks

### Querying
- **Similarity search**: ~10-30ms per query
- **Top-3 retrieval**: <50ms end-to-end
- **Memory usage**: ~200MB (model + index loaded)

## Evaluation

Run evaluation to measure retrieval quality:

```bash
python evaluate.py --test-set test_queries.json

# Output:
# Evaluating 20 test queries...
#
# Metrics:
#   Precision@3: 0.78
#   Recall@5:    0.82
#   MRR:         0.71
#   Avg Score:   0.84
#
# Per-Query Results:
#   Query: "database failover steps"
#     Retrieved: 3/3 relevant (Precision: 1.0)
#     Missed: 0 relevant docs
# ...
```

## Example Queries

Good queries to try:

1. **Operational**: "How do I restart the auth service?"
2. **Troubleshooting**: "What should I do if CrashLoopBackOff occurs?"
3. **Incident**: "What was the cause of the database deadlock incident?"
4. **Monitoring**: "How do I set up Prometheus for a new service?"
5. **Architecture**: "What are the dependencies of the payment service?"

## Limitations

### Current Limitations
- **No LLM response generation**: Only retrieves chunks, doesn't generate answers (add LLM integration for full RAG)
- **Simple abstract generation**: Abstract-first mode uses first N tokens, not smart summarization
- **No incremental updates**: Re-indexes entire wiki on each run (add change detection)
- **Basic metadata extraction**: Relies on structured metadata in docs (improve parser)

### Future Enhancements
See `../future_features/` for planned improvements:
- Multi-stage retrieval (BM25 + dense + reranker)
- Query transformation and expansion
- Hybrid search with score fusion
- Deduplication for similar chunks
- Incremental indexing

## Architecture Decisions

### Why sentence-transformers?
- **Local**: No API calls, works offline
- **Free**: No usage costs
- **Fast**: Inference on CPU is <1 second per query
- **Quality**: Good enough for educational/demo purposes
- **Variety**: Many pre-trained models available

### Why ChromaDB?
- **Lightweight**: Embedded database, no separate server
- **Simple**: Easy to set up and use
- **Sufficient**: Handles 10k+ documents easily
- **Metadata filtering**: Native support for filtering by metadata
- **Persistence**: Saves to disk, no data loss

### Why layout-aware chunking?
- **Quality**: Preserves semantic completeness
- **Natural**: Aligns with how documents are written
- **Retrieval**: Chunks match user mental model of content
- **Educational**: Demonstrates curriculum principles

## Troubleshooting

### "Model download failed"
- Check internet connection
- Model downloads from HuggingFace Hub (requires outbound HTTPS)
- Retry after network issue is resolved

### "No results for query"
- Lower `--min-score` threshold (default: 0.5)
- Check if documents were indexed successfully
- Try more specific queries (avoid very general terms)

### "Slow query performance"
- First query is slower (model loading)
- Subsequent queries are fast (<50ms)
- Larger databases (>10k chunks) may need optimization

### "Out of memory"
- Use smaller embedding model: `all-MiniLM-L6-v2` (default, 80MB)
- Reduce `--top-k` value
- Chunk documents more aggressively (smaller sections)

## Files

```
simple_rag_system/
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── config.py              # Configuration settings
├── ingest.py              # Document indexing script
├── query.py               # Query interface
├── chunker.py             # Chunking strategies implementation
├── embedder.py            # Embedding generation
├── metadata_extractor.py  # Parse metadata from docs
├── evaluate.py            # Retrieval quality evaluation
├── test_queries.json      # Test queries for evaluation
└── chromadb_index/        # Vector database (created after first ingest)
```

## Verification & Testing

**New to the system?** Follow the [TESTING.md](TESTING.md) guide to verify everything works:

```bash
# Quick verification (5 minutes)
source ./activate-venv.sh
python ingest.py --input ../sre_wiki_example
python query.py --query "How do I restart the auth service?"
```

The testing guide includes:
- ✅ Step-by-step verification
- ✅ Expected outputs for each step
- ✅ Test queries with expected results
- ✅ Troubleshooting common issues
- ✅ Performance benchmarks

## Next Steps

After running the basic system:
1. **Verify it works**: Follow [TESTING.md](TESTING.md) to confirm correct behavior
2. **Try different chunking strategies**: Compare naive vs. layout-aware
3. **Experiment with queries**: See what retrieves well vs. poorly
4. **Add your own wiki content**: Index your team's documentation
5. **Integrate an LLM**: Add response generation (e.g., using llama.cpp or OpenAI API)
6. **Measure quality**: Run evaluation on your test queries
7. **Optimize**: Tune chunk sizes, embedding model, similarity threshold

## Contributing

Contributions welcome! Priority areas:
- Improved abstract generation (use summarization model)
- Incremental indexing (detect changed files)
- BM25 + dense hybrid search
- Web UI (Streamlit/Gradio)
- Integration with Slack/Discord

## License

MIT License - see ../LICENSE for details
