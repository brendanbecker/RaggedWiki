#!/bin/bash
# Helper script to activate the existing sentence-embedding venv
# and install missing dependencies if needed

VENV_PATH="$HOME/.claude/skills/sentence-embedding/venv"

if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Error: Venv not found at $VENV_PATH"
    echo ""
    echo "Creating new local venv instead..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    exit 0
fi

echo "✓ Found existing venv at $VENV_PATH"
source "$VENV_PATH/bin/activate"

# Check if chromadb is installed
if ! python -c "import chromadb" 2>/dev/null; then
    echo "📦 Installing missing dependencies..."
    pip install -q -r requirements-minimal.txt
    echo "✓ Dependencies installed"
else
    echo "✓ All dependencies already installed"
fi

echo ""
echo "🚀 Virtual environment activated!"
echo ""
echo "Next steps:"
echo "  python ingest.py --input ../sre_wiki_example    # Index the wiki"
echo "  python query.py                                  # Query interface"
echo ""
