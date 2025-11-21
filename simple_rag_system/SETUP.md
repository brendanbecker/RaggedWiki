# Setup Guide - Reusing Existing Virtual Environment

Since you already have sentence-transformers installed in `~/.claude/skills/sentence-embedding/venv`, we can reuse that environment and just install the additional dependencies we need.

## Option 1: Reuse Existing Venv (Recommended)

This reuses the venv from `~/.claude/skills/sentence-embedding/venv` which already has:
- ✅ sentence-transformers (5.1.2)
- ✅ torch (2.9.1)
- ✅ transformers (4.57.1)
- ✅ numpy, scipy, scikit-learn, tqdm

### Step 1: Activate the existing venv

```bash
cd simple_rag_system
source ~/.claude/skills/sentence-embedding/venv/bin/activate
```

### Step 2: Install only the missing dependencies

```bash
pip install -r requirements-minimal.txt
```

This installs only:
- chromadb
- tiktoken
- click
- rich
- python-frontmatter
- markdown
- pandas

**Total install time**: ~30 seconds (vs. ~5 minutes for fresh venv)
**Disk space saved**: ~500MB (sentence-transformers + torch already installed)

### Step 3: Run the system

```bash
# Index the wiki
python ingest.py --input ../sre_wiki_example

# Query
python query.py
```

---

## Option 2: Create Local Venv (If you prefer isolation)

If you prefer to keep this project's dependencies isolated:

```bash
cd simple_rag_system

# Create new venv
python3 -m venv venv
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

This downloads everything from scratch (~500MB).

---

## Option 3: Create Symlink to Shared Venv

Create a symlink so the venv appears local but uses the shared one:

```bash
cd simple_rag_system
ln -s ~/.claude/skills/sentence-embedding/venv venv

# Now you can activate it normally
source venv/bin/activate
pip install -r requirements-minimal.txt
```

---

## Recommended Approach

**Use Option 1** (reuse existing venv) because:
- ✅ Faster setup (~30 seconds vs. 5 minutes)
- ✅ Saves disk space (~500MB)
- ✅ sentence-transformers already downloaded and cached
- ✅ Embedding models already cached in `~/.cache/huggingface/`

The only downside is the venv is shared, but since we're only adding compatible packages (chromadb, tiktoken, etc.), there's no conflict risk.

---

## Verification

After setup, verify everything works:

```bash
# Activate venv
source ~/.claude/skills/sentence-embedding/venv/bin/activate

# Check imports
python -c "import sentence_transformers; import chromadb; import tiktoken; print('✓ All dependencies available')"

# Run test
python ingest.py --help
python query.py --help
```

Expected output:
```
✓ All dependencies available
Usage: ingest.py [OPTIONS]
...
```

---

## Quick Start Script

For convenience, here's a one-liner:

```bash
cd simple_rag_system && \
source ~/.claude/skills/sentence-embedding/venv/bin/activate && \
pip install -q chromadb tiktoken click rich python-frontmatter markdown pandas && \
python ingest.py --input ../sre_wiki_example && \
python query.py
```

This:
1. Changes to project directory
2. Activates existing venv
3. Installs missing packages quietly
4. Indexes the wiki
5. Launches interactive query mode

**Total time**: ~2 minutes
