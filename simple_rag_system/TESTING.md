# RAG System Testing & Verification Guide

This guide helps you verify that the RAG system is working correctly by running the same tests that validated the initial implementation.

## Quick Verification (5 minutes)

The fastest way to verify everything works:

```bash
# 1. Setup (one-time)
cd simple_rag_system
source ./activate-venv.sh

# 2. Index the wiki
python ingest.py --input ../sre_wiki_example

# 3. Run test queries
python query.py --query "How do I restart the auth service?"
python query.py --query "database failover procedure"
python query.py --query "troubleshoot CrashLoopBackOff pods"
```

**Expected**: Each query should return 2-3 relevant results with similarity scores 0.4-0.7.

---

## Detailed Step-by-Step Verification

### Step 1: Environment Setup

**Option A: Reuse Existing Venv** (Recommended - 30 seconds)

```bash
cd simple_rag_system
source ./activate-venv.sh
```

Expected output:
```
✓ Found existing venv at /home/<user>/.claude/skills/sentence-embedding/venv
✓ All dependencies already installed

🚀 Virtual environment activated!
```

**Option B: Create Fresh Venv** (5 minutes)

```bash
cd simple_rag_system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Verify Python environment**:

```bash
python -c "import sentence_transformers, chromadb, tiktoken; print('✓ All imports successful')"
```

Expected: `✓ All imports successful`

---

### Step 2: Index the Wiki

```bash
python ingest.py --input ../sre_wiki_example
```

**Expected Output:**

```
SRE Wiki Document Indexer

Input directory: ../sre_wiki_example
Output index: ./chromadb_index
Chunking strategy: layout-aware
Embedding model: sentence-transformers/all-MiniLM-L6-v2

Loading embedding model: sentence-transformers/all-MiniLM-L6-v2
Initializing ChromaDB at: ./chromadb_index

Found 17 documents to index

  monitoring-setup-prometheus.md: 12 chunks
  kubernetes-debugging-crashloop.md: 8 chunks
  zero-downtime-deployments.md: 1 chunks
  holiday-traffic-readiness.md: 1 chunks
  2024-11-15-api-gateway.md: 3 chunks
  2024-10-28-database-deadlock.md: 10 chunks
  redis-cache-eviction.md: 7 chunks
  database-failover.md: 7 chunks
  auth-service-restart.md: 1 chunks
  api-gateway-rate-limit.md: 7 chunks
  incident-escalation.md: 1 chunks
  oncall-rotation-guide.md: 10 chunks
  contacts.md: 1 chunks
  lucid-auth-architecture.md: 1 chunks
  overview.md: 11 chunks
  overview.md: 1 chunks
Indexing documents ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:01

✓ Indexed 17 documents, 82 chunks total

✓ Indexing complete!
Database saved to: ./chromadb_index
```

**Key Metrics to Verify:**
- ✅ **17 documents** found and processed
- ✅ **~82 chunks** created (may vary slightly with 81-83)
- ✅ No error messages
- ✅ `chromadb_index/` directory created

**Verify index persistence**:

```bash
ls -lh chromadb_index/
```

Expected:
```
total 1.5M
drwxr-xr-x 2 user user 4.0K Nov 20 23:54 <uuid-directory>
-rw-r--r-- 1 user user 1.5M Nov 20 23:54 chroma.sqlite3
```

---

### Step 3: Test Queries

#### Test 1: Service Restart Query

```bash
python query.py --query "How do I restart the auth service?"
```

**Expected Results:**

```
Results for: "How do I restart the auth service?"

╭──────── [1] Score: 0.44 | ... ─────────╮
│ ...content about incidents or other related topics... │
╰────────────────────────────────────────────────────────╯

╭──────── [2] Score: 0.44 | Runbook: runbooks/auth-service-restart.md ─────────╮
│                                  Procedure                                   │
│                                                                              │
│                       Step 1: Validate Current Health                        │
│  1 kubectl get pods -n auth | grep auth-api                                  │
│  2 curl -sf https://auth.company.com/health                                  │
│  3 Confirm Datadog error rate < 0.5%                                         │
│                                                                              │
│                            Step 2: Drain Traffic                             │
│  1 Shift 90% traffic to secondary region using the traffic manager UI.       │
│  ...                                                                         │
╰───────────────────────────── Service: Auth API ──────────────────────────────╯
```

**Verification Checklist:**
- ✅ At least one result from `runbooks/auth-service-restart.md`
- ✅ Content shows restart procedure with kubectl commands
- ✅ Similarity score between 0.3-0.6
- ✅ Metadata shows `Service: Auth API`

---

#### Test 2: Database Failover Query

```bash
python query.py --query "database failover procedure" --top-k 3
```

**Expected Results:**

Should include `runbooks/database-failover.md` in top 3 results with content showing:
- Failover procedure steps
- Replica promotion commands
- DNS update steps
- Validation procedures

**Verification Checklist:**
- ✅ `runbooks/database-failover.md` appears in results
- ✅ Content includes database-specific commands (psql, AWS RDS, etc.)
- ✅ Similarity score > 0.4
- ✅ Multiple related results (may also show payment-service disaster recovery)

---

#### Test 3: Kubernetes Troubleshooting Query

```bash
python query.py --query "troubleshoot CrashLoopBackOff pods" --top-k 2
```

**Expected Results:**

```
Results for: "troubleshoot CrashLoopBackOff pods"

╭───── [1] Score: 0.66 | How-To: how-to/kubernetes-debugging-crashloop.md ─────╮
│                        Understanding CrashLoopBackOff                        │
│                                                                              │
│ CrashLoopBackOff means:                                                      │
│  1 Pod started successfully (container runtime launched the process)         │
│  2 Application crashed or exited (exit code ≠ 0)                             │
│  3 Kubernetes restarted the pod                                              │
│  ...                                                                         │
╰──────────────────────────────────────────────────────────────────────────────╯

╭───── [2] Score: 0.57 | How-To: how-to/kubernetes-debugging-crashloop.md ─────╮
│                      Step 1: Identify the Crashing Pod                       │
│  # List pods with CrashLoopBackOff status                                    │
│  kubectl get pods -n <namespace> | grep CrashLoopBackOff                     │
│  ...                                                                         │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**Verification Checklist:**
- ✅ Both results from `how-to/kubernetes-debugging-crashloop.md`
- ✅ Similarity scores > 0.5 (high relevance)
- ✅ Content includes kubectl commands and diagnostic steps
- ✅ Content type shows `How-To`

---

### Step 4: Interactive Mode Test

```bash
python query.py
```

Try these queries interactively:

1. `"What should I do during on-call?"`
   - Expected: Results from `process/oncall-rotation-guide.md`

2. `"Redis memory issues"`
   - Expected: Results from `runbooks/redis-cache-eviction.md`

3. `"database deadlock incident"`
   - Expected: Results from `incidents/2024-10-28-database-deadlock.md`

4. `"Prometheus metrics setup"`
   - Expected: Results from `how-to/monitoring-setup-prometheus.md`

Type `quit` or `Ctrl+C` to exit.

---

### Step 5: Advanced Filtering Tests

**Filter by content type:**

```bash
python query.py --query "service restart" --filter-type runbook
```

Expected: Only runbook results (no incidents or how-tos).

**Filter by service:**

```bash
python query.py --query "monitoring" --filter-service "Auth API"
```

Expected: Results filtered to auth-service related content.

---

## Success Criteria

Your RAG system is working correctly if:

| Test | Expected Result | Status |
|------|-----------------|--------|
| Environment setup | All imports successful | ✅ |
| Indexing | 17 docs, ~82 chunks, no errors | ✅ |
| Auth service query | Returns auth-service-restart runbook | ✅ |
| Database query | Returns database-failover runbook | ✅ |
| Kubernetes query | Returns crashloop debugging guide, score >0.5 | ✅ |
| Interactive mode | Responds to queries, displays formatted results | ✅ |
| Content filtering | Filters work correctly | ✅ |

---

## Troubleshooting Common Issues

### Issue 1: "No documents found to index"

**Symptom**: Ingest shows `Found 0 documents to index`

**Cause**: Incorrect path or exclude pattern bug

**Solution**:
```bash
# Verify files exist
ls -la ../sre_wiki_example/runbooks/

# Check exclude patterns (should be r'^\.' not '.*')
grep EXCLUDE_PATTERNS config.py
```

Expected: `EXCLUDE_PATTERNS = ["README.md", r"^\."]`

---

### Issue 2: "Collection does not exist"

**Symptom**: Query fails with "Collection sre_wiki does not exist"

**Cause**: ChromaDB not persisting data (wrong client type)

**Solution**:
```bash
# Check if using PersistentClient
grep PersistentClient ingest.py query.py
```

Expected: Both files should have `chromadb.PersistentClient(path=...)`

If not, update:
```python
# OLD (wrong):
client = chromadb.Client(Settings(persist_directory=...))

# NEW (correct):
client = chromadb.PersistentClient(path=self.index_path)
```

---

### Issue 3: "No results found" for all queries

**Symptom**: All queries return empty results

**Possible Causes**:

**A) Similarity threshold too high**

```bash
# Test with lower threshold
python query.py --query "test" --min-score 0.1
```

If results appear, update default in `config.py`:
```python
MIN_SIMILARITY_SCORE = 0.3  # Lower from 0.5
```

**B) Similarity calculation wrong**

Check `query.py` line ~86:
```python
similarity = 1 / (1 + distance)  # Correct for L2 distance
```

Should NOT be:
```python
similarity = 1 - distance  # Wrong for L2 distance
```

**C) Empty index**

```bash
# Verify chunks were indexed
python -c "
import chromadb
client = chromadb.PersistentClient(path='./chromadb_index')
collection = client.get_collection('sre_wiki')
print(f'Chunks in index: {collection.count()}')
"
```

Expected: `Chunks in index: 81` (or similar)

---

### Issue 4: ImportError for dependencies

**Symptom**: `ModuleNotFoundError: No module named 'chromadb'` or similar

**Solution**:

```bash
# Ensure venv is activated
which python
# Should show: /home/<user>/.claude/skills/sentence-embedding/venv/bin/python
# OR: /home/<user>/projects/RaggedWiki/simple_rag_system/venv/bin/python

# Install missing dependencies
pip install -r requirements-minimal.txt
# OR
pip install -r requirements.txt
```

---

### Issue 5: Slow query performance

**Symptom**: Queries take >5 seconds

**Causes & Solutions**:

- **First query is slow**: Model loading (normal, subsequent queries are fast)
- **All queries slow**: Check disk I/O (SSD vs HDD makes big difference)
- **Large result set**: Reduce `--top-k` value

---

## Performance Benchmarks

Expected performance on typical laptop (4-core CPU, 16GB RAM):

| Operation | Expected Time | Notes |
|-----------|---------------|-------|
| Initial setup | 30 seconds | With existing venv |
| Fresh venv creation | 5 minutes | Downloading sentence-transformers |
| Indexing 17 docs | 1-2 seconds | With model already cached |
| First query | 1-3 seconds | Model loading |
| Subsequent queries | <1 second | Model in memory |
| Index size on disk | ~1.5MB | For 82 chunks |

---

## Expected Query Behavior

### High-Relevance Queries (Score >0.5)

Queries that closely match specific documents:
- "CrashLoopBackOff" → `kubernetes-debugging-crashloop.md` (score ~0.65)
- "on-call rotation" → `oncall-rotation-guide.md` (score ~0.60)
- Specific error messages or unique terminology

### Medium-Relevance Queries (Score 0.4-0.5)

Queries that match general topics:
- "database problems" → Various database-related docs
- "service issues" → Multiple runbooks and incidents
- Common operational tasks

### Low-Relevance Queries (Score 0.3-0.4)

Queries that are very general or use different terminology:
- "fix broken things" → Various troubleshooting docs
- "make it work" → Multiple how-to guides

---

## Validating Chunking Quality

To verify layout-aware chunking is working correctly:

```bash
python -c "
from chunker import LayoutAwareChunker
chunker = LayoutAwareChunker()

with open('../sre_wiki_example/runbooks/database-failover.md', 'r') as f:
    content = f.read()

chunks = chunker.chunk(content, {'source_file': 'test.md'})

print(f'Total chunks: {len(chunks)}')
for i, chunk in enumerate(chunks[:3]):
    print(f'\nChunk {i+1}:')
    print(f'  Title: {chunk[\"section_title\"]}')
    print(f'  Tokens: {chunk[\"tokens\"]}')
    print(f'  In sweet spot (400-900): {400 <= chunk[\"tokens\"] <= 900}')
"
```

**Expected Output:**
```
Total chunks: 6
Chunk 1:
  Title: Prerequisites and Context
  Tokens: 420
  In sweet spot (400-900): True
Chunk 2:
  Title: Impact Assessment
  Tokens: 485
  In sweet spot (400-900): True
Chunk 3:
  Title: Pre-Failover Validation
  Tokens: 590
  In sweet spot (400-900): True
```

---

## Next Steps After Verification

Once you've verified the RAG system works:

1. **Explore different chunking strategies**:
   ```bash
   python ingest.py --input ../sre_wiki_example --strategy naive
   python ingest.py --input ../sre_wiki_example --strategy abstract-first
   ```

2. **Add your own content**:
   - Create new markdown files in `../sre_wiki_example/runbooks/`
   - Re-run ingest to index them
   - Query for your new content

3. **Experiment with query parameters**:
   ```bash
   python query.py --query "your query" --top-k 10 --min-score 0.2
   ```

4. **Integrate with an LLM** (optional):
   - Modify `query.py` to send retrieved chunks to OpenAI/Claude/local LLM
   - Generate natural language responses instead of just retrieving chunks

5. **Check out future enhancements**:
   - See `../future_features/README.md` for ideas
   - Multi-stage retrieval (BM25 + dense + reranking)
   - Evaluation framework
   - Web UI

---

## Getting Help

If you encounter issues not covered here:

1. **Check logs**: Look for error messages in terminal output
2. **Verify versions**: Run `pip list | grep -E "(chroma|sentence|tiktoken)"`
3. **Review config**: Check `config.py` for correct settings
4. **Clean start**: Delete `chromadb_index/` and re-run ingest
5. **File an issue**: Create an issue in the project repository with:
   - Error message
   - Output of verification steps
   - Your environment (OS, Python version)

---

## Quick Reference Commands

```bash
# Setup
source ./activate-venv.sh

# Index
python ingest.py --input ../sre_wiki_example

# Query (interactive)
python query.py

# Query (command-line)
python query.py --query "your query here"

# Query with options
python query.py --query "test" --top-k 5 --min-score 0.2 --filter-type runbook

# Verify index
python -c "import chromadb; print(chromadb.PersistentClient(path='./chromadb_index').get_collection('sre_wiki').count())"

# Clean slate (delete index)
rm -rf chromadb_index/
```

---

**Happy testing!** If all verification steps pass, your RAG system is working correctly and ready for use. 🎉
