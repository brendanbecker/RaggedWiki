"""
Configuration for the Simple RAG System
"""

# Embedding Model Configuration
# sentence-transformers model from HuggingFace
# all-MiniLM-L6-v2: Fast, lightweight (80MB), good quality
# all-mpnet-base-v2: Better quality, slower, larger (420MB)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Alternative models:
# EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"  # Better quality
# EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"  # Multilingual

# Chunking Configuration
CHUNKING_STRATEGY = "layout-aware"  # Options: layout-aware, naive, abstract-first

# Layout-aware chunking parameters
LAYOUT_AWARE_HEADING_LEVEL = "h2"  # Split at H2 (##) boundaries
LAYOUT_AWARE_MAX_TOKENS = 900      # Maximum tokens per chunk
LAYOUT_AWARE_MIN_TOKENS = 200      # Minimum tokens per chunk (merge smaller sections)
LAYOUT_AWARE_MERGE_SMALL = True    # Merge sections <MIN_TOKENS with next section

# Naive fixed-size chunking parameters
NAIVE_CHUNK_SIZE = 512             # Tokens per chunk
NAIVE_OVERLAP = 50                 # Token overlap between chunks

# Abstract-first parameters
ABSTRACT_MAX_TOKENS = 200          # Maximum tokens for abstract
ABSTRACT_GENERATION_METHOD = "extractive"  # Options: extractive, llm (llm requires API)

# Retrieval Configuration
DEFAULT_TOP_K = 3                  # Number of results to return by default
MIN_SIMILARITY_SCORE = 0.3         # Minimum similarity threshold (0-1) - adjusted for L2 distance

# Metadata Extraction
EXTRACT_METADATA = True
EXTRACT_SERVICE_NAME = True        # Parse service name from metadata table
EXTRACT_SEVERITY = True            # Parse severity (SEV1, SEV2, etc.)
EXTRACT_ENVIRONMENT = True         # Parse environment (prod, staging, etc.)
EXTRACT_OWNER = True               # Parse owner team

# Metadata field patterns (regex patterns to match metadata)
METADATA_PATTERNS = {
    "service": r"\*\*Service:\*\*\s*(.+?)(?:\s*\||$)",
    "environment": r"\*\*Environment:\*\*\s*(.+?)(?:\s*\||$)",
    "severity": r"\*\*Severity:\*\*\s*(SEV[0-9])",
    "owner": r"\*\*Owner:\*\*\s*(.+?)(?:\s*\||$)",
}

# ChromaDB Configuration
CHROMADB_COLLECTION_NAME = "sre_wiki"
CHROMADB_PERSIST_DIRECTORY = "./chromadb_index"

# Document Processing
SUPPORTED_EXTENSIONS = [".md", ".markdown"]
EXCLUDE_PATTERNS = ["README.md", r"^\."]  # Files to skip during ingestion (README and dotfiles)

# Tokenization
# tiktoken encoding for token counting (matches OpenAI tokenization)
TIKTOKEN_ENCODING = "cl100k_base"  # GPT-4, GPT-3.5-turbo encoding

# Logging
LOG_LEVEL = "INFO"  # Options: DEBUG, INFO, WARNING, ERROR
VERBOSE_OUTPUT = True

# Performance
BATCH_SIZE = 32  # Embedding batch size for faster processing
MAX_WORKERS = 4  # Parallel workers for document processing
