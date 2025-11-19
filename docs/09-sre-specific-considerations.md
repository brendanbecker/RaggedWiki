# Module 09: SRE-Specific Considerations

**Learning Objectives:**
- Apply content-specific chunking strategies to operational content types
- Understand why Infrastructure-as-Code requires AST-based splitting
- Implement Summary-Index pattern for high-entropy data (logs, stack traces)
- Structure runbooks and post-mortems for optimal retrieval
- Design multi-tenant, time-aware retrieval for operational environments

**Prerequisites:** Modules 01-06 (chunking strategies, retrieval architecture, production deployment)

**Time:** 45-60 minutes

---

## Introduction: Why SRE Content is Different

SRE and operations teams work with fundamentally different content than typical documentation:

- **Infrastructure-as-Code:** Syntax-sensitive, declarative, environment-specific
- **Logs and stack traces:** High-entropy, non-linguistic, volume-intensive
- **Runbooks:** Procedural, prerequisite-dependent, safety-critical
- **Post-mortems:** Narrative flow, temporal constraints, audit requirements
- **Monitoring alerts:** Template-based, context-heavy, time-sensitive

**Each content type breaks naive chunking strategies in different ways.**

This module provides content-specific patterns proven to work in production SRE environments. These aren't theoretical—they're battle-tested solutions to real operational failures.

---

## 1. Infrastructure as Code (IaC)

### The Problem

**Example: Terraform HCL**

```hcl
resource "aws_s3_bucket" "example" {
  bucket = "my-app-bucket"
  acl    = "private"

  versioning {
    enabled = true
  }

  lifecycle_rule {
    id      = "archive-old-versions"
    enabled = true

    noncurrent_version_expiration {
      days = 90
    }
  }

  tags = {
    Environment = "production"
    Service     = "data-pipeline"
  }
}
```

**Naive Fixed-Size Chunking (500 tokens):**

```
Chunk 1:
resource "aws_s3_bucket" "example" {
  bucket = "my-app-bucket"
  acl    = "private"

  versioning {
    enabled = true
  }

  lifecycle_rule {
    id      = "archive-old-versions"
---SPLIT---

Chunk 2:
    enabled = true

    noncurrent_version_expiration {
      days = 90
    }
  }
---SPLIT---
```

**Failures:**

1. **Syntax corruption:** Chunk 1 has unclosed braces, Chunk 2 starts mid-block
2. **Context loss:** Tags separated from resource definition
3. **Unusable for generation:** LLM can't apply partial, syntactically invalid code

**From Research:**

> "Standard text splitters often sever a resource block from its provider configuration or split a multi-line string in the middle, rendering the snippet useless for generation."

### Solution: AST-Based Splitting

**Concept:** Parse code into Abstract Syntax Tree, split at logical boundaries.

**Tools:**

- **Terraform (HCL):** `tree-sitter-hcl`, `hcl2` Python library
- **Kubernetes YAML:** `ruamel.yaml` (preserves structure and comments)
- **Ansible YAML:** Custom parser respecting playbook/role structure

**From Research:**

> "Tools like CodeSplitter or custom parsers utilizing tree-sitter-hcl parse the code into its logical components... The parser identifies the start and end of a logical block (e.g., a resource 'aws_s3_bucket' 'example' {...}). The entire block is treated as an atomic unit."

### Implementation: Terraform Chunking

```python
import hcl2
from tree_sitter import Language, Parser

def chunk_terraform(file_path):
    """Split Terraform file into resource blocks."""
    with open(file_path, 'r') as f:
        content = f.read()

    # Parse HCL
    try:
        parsed = hcl2.loads(content)
    except:
        # Fallback: Split on resource blocks with regex
        return fallback_terraform_split(content)

    chunks = []

    # Extract resource blocks
    for resource_type, resources in parsed.get('resource', {}).items():
        for resource_name, resource_config in resources.items():
            # Each resource is one chunk
            chunk_text = f"""
resource "{resource_type}" "{resource_name}" {{
  {format_hcl_block(resource_config)}
}}
"""
            chunks.append({
                'text': chunk_text,
                'metadata': {
                    'type': 'terraform_resource',
                    'resource_type': resource_type,
                    'resource_name': resource_name,
                    'file_path': file_path
                }
            })

    # Extract module blocks
    for module_name, module_config in parsed.get('module', {}).items():
        chunk_text = f"""
module "{module_name}" {{
  {format_hcl_block(module_config)}
}}
"""
        chunks.append({
            'text': chunk_text,
            'metadata': {
                'type': 'terraform_module',
                'module_name': module_name,
                'file_path': file_path
            }
        })

    return chunks
```

**Result:**

Each chunk contains a **complete, syntactically valid** resource or module block.

### Handling Large Blocks

**Problem:** Some resources exceed 900 tokens.

**Solution: Split at attribute level, preserve syntax**

```python
def split_large_resource(resource_block, max_tokens=900):
    """Split resource at attribute boundaries if too large."""
    if token_count(resource_block) <= max_tokens:
        return [resource_block]

    # Parse resource attributes
    attributes = parse_resource_attributes(resource_block)

    chunks = []
    current_chunk = {
        'header': resource_header(resource_block),  # resource "type" "name" {
        'attributes': []
    }
    current_tokens = token_count(current_chunk['header'])

    for attr_name, attr_value in attributes.items():
        attr_tokens = token_count(f"{attr_name} = {attr_value}")

        if current_tokens + attr_tokens > max_tokens:
            # Flush current chunk
            chunks.append(format_resource_chunk(current_chunk))
            # Start new chunk (same header, new attributes)
            current_chunk = {
                'header': resource_header(resource_block),
                'attributes': [(attr_name, attr_value)]
            }
            current_tokens = token_count(current_chunk['header']) + attr_tokens
        else:
            current_chunk['attributes'].append((attr_name, attr_value))
            current_tokens += attr_tokens

    chunks.append(format_resource_chunk(current_chunk))
    return chunks
```

**Key Insight:** Even when splitting, maintain syntactic validity. Each chunk has complete `resource "type" "name" { ... }` structure.

### Environment Metadata: Critical for IaC

**From Research:**

> "A critical insight is that IaC code is often identical across environments (Dev, Staging, Prod), differentiated only by directory path or variable files. The ingestion pipeline must extract this context."

**Problem:**

```
terraform/
  prod/
    database.tf  # aws_db_instance "main" { instance_class = "db.m5.xlarge" }
  staging/
    database.tf  # aws_db_instance "main" { instance_class = "db.t3.medium" }
```

**Without environment metadata:**

Query: "What's the database instance type?"

Retrieved: Both prod and staging configs (identical resource names)

LLM: "The database instance type is db.m5.xlarge" ← **WRONG if user is in staging context**

**Solution: Extract environment from path**

```python
import re
from pathlib import Path

def extract_environment_metadata(file_path):
    """Extract environment and service context from file path."""
    path = Path(file_path)

    metadata = {
        'file_path': str(file_path),
        'environment': 'unknown',
        'service': 'unknown'
    }

    # Pattern: terraform/{environment}/{service}/
    path_parts = path.parts

    if 'prod' in path_parts or 'production' in path_parts:
        metadata['environment'] = 'production'
    elif 'staging' in path_parts or 'stage' in path_parts:
        metadata['environment'] = 'staging'
    elif 'dev' in path_parts or 'development' in path_parts:
        metadata['environment'] = 'development'

    # Extract service name (directory containing the file)
    if len(path_parts) > 1:
        metadata['service'] = path_parts[-2]

    return metadata

# Usage
chunk_metadata = extract_environment_metadata("terraform/prod/database/rds.tf")
# Result: {'environment': 'production', 'service': 'database'}
```

**Query Filtering:**

```python
def search_terraform(query, environment=None, service=None):
    """Search IaC with environment/service filtering."""
    filters = {'type': 'terraform_resource'}

    if environment:
        filters['environment'] = environment
    if service:
        filters['service'] = service

    return index.search(query, filter=filters)

# User context-aware query
results = search_terraform(
    "What's the database instance type?",
    environment="production"  # Only retrieve prod configs
)
```

**Critical:** Without environment metadata, LLMs **hallucinate cross-environment configurations**, leading to dangerous production operations.

### Kubernetes YAML: Schema-Aware Chunking

**From Research (Decision Matrix):**

> "Kubernetes YAML: Code-Aware Chunking with schema-aware parsers - Treat each manifest as the atomic unit so selectors, metadata, and spec blocks travel together"

**Strategy:** One manifest = one chunk (usually <900 tokens)

```python
import yaml

def chunk_kubernetes_manifest(file_path):
    """Split multi-document YAML into individual manifests."""
    with open(file_path, 'r') as f:
        # YAML files can contain multiple documents separated by ---
        documents = yaml.safe_load_all(f)

    chunks = []
    for doc in documents:
        if not doc:
            continue

        chunk_text = yaml.dump(doc, default_flow_style=False)

        chunks.append({
            'text': chunk_text,
            'metadata': {
                'type': 'kubernetes_manifest',
                'kind': doc.get('kind', 'unknown'),
                'name': doc.get('metadata', {}).get('name', 'unknown'),
                'namespace': doc.get('metadata', {}).get('namespace', 'default'),
                'file_path': file_path
            }
        })

    return chunks
```

**Why This Works:**

- Each manifest is semantically complete (metadata + spec)
- Selectors stay with their targets
- Labels and annotations preserved with resources
- Typical manifest is 200-700 tokens (fits target range)

**Handling Large Manifests:**

If a single manifest exceeds 900 tokens (large ConfigMaps, complex Deployments):

```python
def split_large_manifest(manifest_dict, max_tokens=900):
    """Split large manifest into metadata + spec chunks."""
    chunks = []

    # Chunk 1: Metadata + minimal spec
    metadata_chunk = {
        'apiVersion': manifest_dict['apiVersion'],
        'kind': manifest_dict['kind'],
        'metadata': manifest_dict['metadata']
    }

    chunks.append({
        'text': yaml.dump(metadata_chunk),
        'chunk_type': 'metadata',
        'parent_id': generate_manifest_id(manifest_dict)
    })

    # Chunk 2: Full spec (or split further if needed)
    spec_chunk = {
        'apiVersion': manifest_dict['apiVersion'],
        'kind': manifest_dict['kind'],
        'metadata': {'name': manifest_dict['metadata']['name']},  # Reference
        'spec': manifest_dict['spec']
    }

    chunks.append({
        'text': yaml.dump(spec_chunk),
        'chunk_type': 'spec',
        'parent_id': generate_manifest_id(manifest_dict)
    })

    return chunks
```

**Parent-child pattern:** Retrieve metadata chunk → fetch full manifest via parent_id.

### IaC Operational Patterns

**Dependency Tracking:**

```python
# Metadata enrichment
chunk_metadata = {
    'type': 'terraform_resource',
    'resource_type': 'aws_db_instance',
    'resource_name': 'main',
    'depends_on': ['aws_security_group.db_sg', 'aws_subnet.private'],
    'referenced_by': ['aws_lambda_function.data_processor']
}
```

**Use Case:** Query "What depends on this database?" → retrieve all resources in `referenced_by`.

**Access Control:**

```python
# Production IaC requires elevated access
chunk_metadata = {
    'environment': 'production',
    'access_control_list': ['sre-team', 'platform-engineering'],
    'sensitivity': 'high'
}

# Query filtering
results = index.search(
    query=user_query,
    filter={
        'access_control_list': {'in': user.teams}
    }
)
```

**Critical:** Prevent staging users from seeing production configs.

---

## 2. System Logs

### The Problem

**Example: Application Log**

```
2024-11-18 10:23:45.123 INFO  [auth-service] User login attempt: user_id=12345
2024-11-18 10:23:45.456 DEBUG [auth-service] Database query: SELECT * FROM users WHERE id=12345
2024-11-18 10:23:45.789 INFO  [auth-service] Login successful: user_id=12345, session_id=abc-def-ghi
2024-11-18 10:23:46.012 ERROR [payment-service] Connection refused: host=database.prod, port=5432
2024-11-18 10:23:46.234 ERROR [payment-service] Retry attempt 1/3 failed
2024-11-18 10:23:46.567 ERROR [payment-service] Retry attempt 2/3 failed
2024-11-18 10:23:46.890 ERROR [payment-service] Retry attempt 3/3 failed, giving up
2024-11-18 10:23:47.123 WARN  [payment-service] Transaction failed: transaction_id=tx-9876
```

**Challenges:**

1. **No structure:** Unlike runbooks with headers, logs are flat sequences
2. **High volume:** Gigabytes per day
3. **Temporal ordering critical:** Event B only makes sense after Event A
4. **High entropy:** UUIDs, timestamps, memory addresses change constantly

**From Research (Decision Matrix):**

> "System Logs: Fixed-Size Sliding Window with call-frame aware splitter - Logs flow linearly. Overlap prevents severing a stack trace header from its body. Sparse search (BM25) is critical for exact matching of high-entropy error IDs."

### Solution: Sliding Window with Timestamp Anchoring

**Strategy:**

- **Window size:** 512 tokens (~30-50 log lines)
- **Overlap:** 20% (100 tokens) to prevent boundary loss
- **Anchor:** Timestamp ensures temporal context

**Implementation:**

```python
from datetime import datetime

def chunk_logs_sliding_window(log_lines, window_tokens=512, overlap_tokens=100):
    """Chunk logs with sliding window, preserving temporal order."""
    chunks = []
    current_chunk = []
    current_tokens = 0

    for line in log_lines:
        line_tokens = token_count(line)

        if current_tokens + line_tokens > window_tokens:
            # Flush current chunk
            chunks.append({
                'text': '\n'.join(current_chunk),
                'metadata': {
                    'type': 'log',
                    'start_timestamp': extract_timestamp(current_chunk[0]),
                    'end_timestamp': extract_timestamp(current_chunk[-1]),
                    'line_count': len(current_chunk)
                }
            })

            # Create overlapping window
            overlap_lines = get_last_n_tokens(current_chunk, overlap_tokens)
            current_chunk = overlap_lines + [line]
            current_tokens = token_count('\n'.join(current_chunk))
        else:
            current_chunk.append(line)
            current_tokens += line_tokens

    # Flush final chunk
    if current_chunk:
        chunks.append({
            'text': '\n'.join(current_chunk),
            'metadata': {
                'type': 'log',
                'start_timestamp': extract_timestamp(current_chunk[0]),
                'end_timestamp': extract_timestamp(current_chunk[-1]),
                'line_count': len(current_chunk)
            }
        })

    return chunks
```

**Why Overlap Matters:**

Without overlap, an error and its stack trace could be split across chunks:

```
Chunk 1 (ends):
2024-11-18 10:23:46.890 ERROR [payment-service] Retry attempt 3/3 failed
---SPLIT---

Chunk 2 (starts):
2024-11-18 10:23:47.123 WARN  [payment-service] Transaction failed: tx-9876
```

**With overlap:** Chunk 2 includes the error context from Chunk 1.

### Temporal Query Filtering

**Critical for log retrieval:**

```python
def search_logs(query, start_time, end_time):
    """Search logs with temporal bounds."""
    return index.search(
        query=query,
        filter={
            'type': 'log',
            'start_timestamp': {'lte': end_time},
            'end_timestamp': {'gte': start_time}
        }
    )

# Example: Find errors during incident window
incident_start = datetime(2024, 11, 18, 10, 23, 0)
incident_end = datetime(2024, 11, 18, 10, 25, 0)

results = search_logs(
    "connection refused database",
    start_time=incident_start,
    end_time=incident_end
)
```

### Hybrid Search: Dense + Sparse

**From Research:**

> "Sparse search (BM25) is critical for exact matching of high-entropy error IDs."

**Example:**

Query: "Find logs with error code E1234"

**Dense-only retrieval:** Fails because "E1234" is high-entropy, no semantic meaning

**Sparse (BM25) retrieval:** Exact match on "E1234" succeeds

**Hybrid (Dense + Sparse):**

- Dense: Matches semantic content ("connection refused", "database error")
- Sparse: Matches exact identifiers ("E1234", "transaction_id=tx-9876")

**Best of both worlds.**

### Rolling Index for Logs

**From Module 06:**

Logs are time-series data with limited retention value.

**Strategy:**

- **Hot tier (0-7 days):** Indexed for real-time troubleshooting
- **Warm tier (8-30 days):** Indexed for post-incident analysis
- **Cold tier (31-90 days):** Archived, not indexed (query if needed)
- **Deleted (>90 days):** Purged

**Operational Benefit:** Bounded index size, predictable performance, cost control.

---

## 3. Stack Traces: The Summary-Index Pattern

### The Problem

**Example: Python Stack Trace**

```
Traceback (most recent call last):
  File "/app/payment_processor.py", line 142, in process_payment
    result = database.execute_transaction(tx_data)
  File "/app/database/connection.py", line 87, in execute_transaction
    conn = self.pool.get_connection()
  File "/usr/lib/python3.9/site-packages/psycopg2/pool.py", line 156, in get_connection
    return self._pool[key]
KeyError: 'connection_5a3f9b2c'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/app/api/routes.py", line 234, in handle_request
    return payment_processor.process_payment(request.data)
  File "/app/payment_processor.py", line 145, in process_payment
    self.logger.error(f"Transaction failed: {str(e)}")
psycopg2.OperationalError: connection pool exhausted (current: 20/20)
```

**Challenges:**

1. **High entropy:** Memory addresses (`0x7f3a2b1c8d40`), hex codes, UUIDs
2. **Non-linguistic:** Dense vector embeddings degrade on random tokens
3. **Voluminous:** 50-100 lines per trace
4. **Repetitive:** Same stack frames appear in thousands of traces

**From Research:**

> "Stack traces represent a high-entropy data class that defies standard vectorization. They are often voluminous, repetitive, and dense with non-natural language tokens (hex codes, memory addresses)... Embedding a raw 50-line stack trace often dilutes the vector space."

### Solution: Summary-Index Pattern

**From Research - Four-Step Process:**

> "1. **Extraction:** During ingestion, a regex parser extracts the **Exception Type** (e.g., java.net.ConnectException) and the **Top 3 Stack Frames**.
> 2. **Embedding:** Only this summary is embedded into the vector store.
> 3. **Storage:** The full, raw stack trace is stored as a 'Parent' document.
> 4. **Retrieval:** The user's query matches the summary (e.g., 'connection error'), but the RAG system retrieves the full parent stack trace for the LLM to analyze."

**Implementation:**

```python
import re

def extract_stack_trace_summary(stack_trace_text):
    """Extract exception type and top stack frames."""
    lines = stack_trace_text.strip().split('\n')

    # Extract exception type (last line typically)
    exception_type = "Unknown"
    exception_message = ""

    for line in reversed(lines):
        if ':' in line and not line.strip().startswith('File'):
            parts = line.split(':', 1)
            exception_type = parts[0].strip()
            exception_message = parts[1].strip() if len(parts) > 1 else ""
            break

    # Extract top 3 stack frames
    stack_frames = []
    for line in lines:
        if line.strip().startswith('File'):
            # Parse: File "/path/file.py", line 123, in function_name
            match = re.search(r'File "([^"]+)", line (\d+), in (\w+)', line)
            if match:
                file_path, line_num, func_name = match.groups()
                stack_frames.append(f"{func_name} ({file_path}:{line_num})")

            if len(stack_frames) >= 3:
                break

    # Create summary
    summary = f"""
Exception: {exception_type}
Message: {exception_message}
Stack Frames:
  {stack_frames[0] if len(stack_frames) > 0 else 'N/A'}
  {stack_frames[1] if len(stack_frames) > 1 else 'N/A'}
  {stack_frames[2] if len(stack_frames) > 2 else 'N/A'}
""".strip()

    return summary

# Example usage
stack_trace = """<full 50-line stack trace>"""

summary = extract_stack_trace_summary(stack_trace)
# Summary (~100 tokens):
# Exception: psycopg2.OperationalError
# Message: connection pool exhausted (current: 20/20)
# Stack Frames:
#   process_payment (payment_processor.py:142)
#   execute_transaction (connection.py:87)
#   get_connection (pool.py:156)

# Index summary (child)
child_chunk = {
    'chunk_id': 'trace_summary_abc123',
    'text': summary,
    'chunk_type': 'stack_trace_summary',
    'parent_id': 'trace_full_abc123'
}

# Store full trace (parent)
parent_chunk = {
    'chunk_id': 'trace_full_abc123',
    'text': stack_trace,  # Full 50 lines
    'chunk_type': 'stack_trace_full'
}
```

**Retrieval Flow:**

1. User query: "Why is payment service failing with connection errors?"
2. Vector search matches **summary** (low-entropy, semantic: "connection pool exhausted")
3. System retrieves **parent_id** → fetches full stack trace
4. LLM receives full trace for analysis

**Why This Works:**

- **Retrieval stage:** Match against clean, low-entropy summaries
- **Generation stage:** Provide full, high-entropy details for accurate diagnosis
- **Result:** Precision in retrieval, completeness in context

### Sparse Search for Exception Types

**From Research (Decision Matrix):**

> "Stack Traces: Sparse (BM25) Only - Dense vectors degrade on hex addresses and variable paths. Keyword matching on Exception Classes (e.g., NullPointerException) and line numbers is far more effective."

**Metadata Enrichment:**

```python
child_chunk = {
    'chunk_id': 'trace_summary_abc123',
    'text': summary,
    'chunk_type': 'stack_trace_summary',
    'parent_id': 'trace_full_abc123',
    'metadata': {
        'exception_type': 'psycopg2.OperationalError',
        'exception_message': 'connection pool exhausted',
        'top_function': 'process_payment',
        'service': 'payment-service',
        'timestamp': '2024-11-18T10:23:47Z'
    }
}
```

**Sparse Search (BM25):**

Query: "psycopg2.OperationalError"

→ Exact match on `exception_type` metadata → retrieves relevant traces

**Hybrid Search:**

- **Dense:** "connection pool problems" (semantic)
- **Sparse:** "psycopg2.OperationalError" (exact exception type)

**Combined:** Best recall.

### Deduplication for Stack Traces

**Problem:** Same exception, 1000 occurrences → index bloated with duplicates.

**Solution: Hash-based deduplication on exception signature**

```python
def stack_trace_signature(exception_type, stack_frames):
    """Generate stable signature for deduplication."""
    # Combine exception type + top 3 stack frames
    signature_parts = [exception_type] + stack_frames[:3]
    signature = '|'.join(signature_parts)
    return hashlib.md5(signature.encode()).hexdigest()

# Example
sig = stack_trace_signature(
    "psycopg2.OperationalError",
    ["process_payment:142", "execute_transaction:87", "get_connection:156"]
)
# sig = "a3f5b8c9d2e1f4a7b3c8d9e2f1a4b7c8"

# Check if signature exists
existing = index.query_by_signature(sig)
if existing:
    # Increment occurrence count instead of indexing again
    index.increment_count(existing.chunk_id)
else:
    # New exception signature, index it
    index.insert(summary_chunk)
```

**Metadata:**

```python
{
    'exception_signature': 'a3f5b8c9d2e1f4a7b3c8d9e2f1a4b7c8',
    'occurrence_count': 1247,
    'first_seen': '2024-11-15T08:30:00Z',
    'last_seen': '2024-11-18T10:23:47Z'
}
```

**Query Enhancement:**

Retrieved summary shows: "This exception occurred 1247 times between Nov 15-18" → LLM knows it's a recurring issue.

---

## 4. Runbooks and Playbooks

### The Problem

**Example: Auth Service Restart Runbook**

```markdown
# Auth Service Restart Procedure

## Prerequisites

⚠️ WARNING: Do not restart during peak hours (9 AM - 6 PM EST)

Required access:
- Production Kubernetes cluster (role: sre-operator)
- Incident Slack channel (#incidents)

Verification:
- Check current error rate: `kubectl logs -n prod auth-service | grep ERROR | wc -l`
- If error rate >100/min, proceed. Otherwise, investigate first.

## Procedure

1. Notify team in #incidents: "Restarting auth-service in prod"

2. Perform rolling restart:
   ```bash
   kubectl rollout restart deployment/auth-service -n prod
   ```

3. Monitor rollout:
   ```bash
   kubectl rollout status deployment/auth-service -n prod
   ```

4. Verify pods are healthy:
   ```bash
   kubectl get pods -n prod -l app=auth-service
   ```
   Expected: All pods in "Running" state

## Validation

- Check error rate dropped: `kubectl logs -n prod auth-service | grep ERROR | wc -l`
- Verify login endpoint: `curl https://api.example.com/health/auth`
- Monitor dashboard: https://grafana.example.com/d/auth-service

## Rollback

If validation fails:

1. Revert to previous deployment:
   ```bash
   kubectl rollout undo deployment/auth-service -n prod
   ```

2. Escalate to #oncall-escalation
```

**Challenges:**

1. **Prerequisites must stay with procedure:** If split, users miss warnings
2. **Steps must remain sequential:** Step 3 depends on Step 2 completing
3. **Commands must stay with explanations:** "Run X" without "why X" is dangerous
4. **Safety-critical:** Wrong retrieval can cause production outages

**Naive Fixed-Size Chunking Failure:**

```
Chunk 1 (Prerequisites):
Prerequisites, verification checks
---SPLIT---

Chunk 2 (Procedure):
Steps 1-4
---SPLIT---

Chunk 3 (Validation + Rollback):
Validation, rollback procedure
```

**Query:** "How do I restart auth-service?"

**Retrieved:** Chunk 2 only (procedure steps)

**Missing:** Prerequisites (⚠️ peak hours warning), validation, rollback

**Result:** User restarts during peak hours without monitoring → outage.

### Solution: Layout-Aware Hierarchical Chunking

**From Module 02:**

Respect document structure, keep prerequisites with procedures.

**Strategy:**

- **H2 sections (## Prerequisites, ## Procedure) = semantic boundaries**
- Keep each section intact if <900 tokens
- If section >900 tokens, split at H3 subsections
- Use parent-child: H2 sections (children) link to full runbook (parent)

**Implementation:**

```python
def chunk_runbook(markdown_content, max_tokens=900):
    """Chunk runbook respecting hierarchical structure."""
    # Parse markdown into sections
    sections = parse_markdown_sections(markdown_content)

    chunks = []
    for section in sections:
        section_tokens = token_count(section['content'])

        if section_tokens <= max_tokens:
            # Section fits in one chunk
            chunks.append({
                'text': section['content'],
                'metadata': {
                    'type': 'runbook_section',
                    'section_title': section['title'],
                    'section_level': section['level'],  # H1, H2, H3
                    'parent_id': generate_runbook_id(markdown_content)
                }
            })
        else:
            # Section too large, split at subsections
            subsections = split_at_subsections(section)
            for subsection in subsections:
                chunks.append({
                    'text': subsection['content'],
                    'metadata': {
                        'type': 'runbook_subsection',
                        'section_title': section['title'],
                        'subsection_title': subsection['title'],
                        'parent_id': generate_runbook_id(markdown_content)
                    }
                })

    return chunks
```

**Parent-Child Enhancement:**

When "Procedure" section is retrieved, also fetch "Prerequisites" and "Validation":

```python
def retrieve_runbook_with_context(query, k=5):
    """Retrieve runbook sections + related sections."""
    # Initial retrieval
    results = index.search(query, k=k)

    # Expand to include related sections
    expanded = []
    for result in results:
        if result.metadata['type'] == 'runbook_section':
            # Fetch sibling sections from same runbook
            parent_id = result.metadata['parent_id']
            siblings = index.query(filter={'parent_id': parent_id})

            # Include Prerequisites, Procedure, Validation, Rollback
            for sibling in siblings:
                if sibling.metadata['section_title'] in [
                    'Prerequisites', 'Procedure', 'Validation', 'Rollback'
                ]:
                    expanded.append(sibling)

    return deduplicate(expanded)
```

**Result:** User query retrieves complete operational context, not fragmented steps.

### Safety-Critical Metadata

```python
chunk_metadata = {
    'type': 'runbook_section',
    'section_title': 'Procedure',
    'runbook_name': 'auth-service-restart',
    'service': 'auth-service',
    'environment': 'production',
    'risk_level': 'high',  # Low/Medium/High
    'requires_prerequisites': True,
    'has_rollback': True
}
```

**Query Enhancement:**

If `requires_prerequisites = True`, system automatically fetches "Prerequisites" section even if not directly matched.

### Validation: Ensure Procedures Aren't Split Mid-Step

**Problem:** Step 2 split from Step 3.

**Solution: Step-aware splitting**

```python
def validate_procedure_chunks(chunks):
    """Ensure procedure steps aren't fragmented."""
    for chunk in chunks:
        if 'Procedure' in chunk.metadata['section_title']:
            # Check if chunk contains complete numbered list
            text = chunk['text']
            steps = re.findall(r'^\d+\.\s', text, re.MULTILINE)

            # Verify steps are consecutive
            step_numbers = [int(s.strip('. ')) for s in steps]
            if step_numbers != list(range(min(step_numbers), max(step_numbers) + 1)):
                logger.warning(f"Procedure steps fragmented: {step_numbers}")
                # Trigger re-chunking with larger window
```

---

## 5. Post-Mortems and Incident Reports

### The Problem

**Post-mortems have narrative structure:**

1. **Executive Summary:** What happened, impact, resolution
2. **Timeline:** Chronological events
3. **Root Cause Analysis:** Technical deep-dive
4. **Action Items:** Preventive measures
5. **Appendix:** Logs, stack traces, metrics

**Requirements:**

- **Audit trail:** Regulatory compliance, legal requirements
- **Temporal queries:** "What incidents involved database failures in Q3?"
- **Cross-referencing:** Link to related incidents, services, runbooks
- **Preserve narrative flow:** RCA depends on understanding timeline

**From Research:**

> "Post-mortems and incident reports: Layout-aware to preserve Executive Summary, Timeline, RCA"

### Solution: Layout-Aware Chunking + Temporal Tagging

**Strategy:**

- **Each major section = one chunk** (Executive Summary, Timeline, RCA, etc.)
- Sections typically 400-900 tokens (fit target range)
- If section >900 tokens (long timeline), split at sub-events
- Preserve parent-child: Section chunks link to full post-mortem

**Implementation:**

```python
def chunk_postmortem(markdown_content):
    """Chunk post-mortem preserving narrative structure."""
    sections = parse_markdown_sections(markdown_content)

    # Extract incident metadata from frontmatter
    metadata = extract_frontmatter(markdown_content)

    chunks = []
    for section in sections:
        chunks.append({
            'text': section['content'],
            'metadata': {
                'type': 'postmortem_section',
                'section_title': section['title'],
                'incident_id': metadata['incident_id'],
                'incident_date': metadata['incident_date'],
                'severity': metadata['severity'],
                'services_affected': metadata['services_affected'],
                'parent_id': f"postmortem_{metadata['incident_id']}"
            }
        })

    return chunks
```

**Example Frontmatter:**

```yaml
---
incident_id: INC-2024-11-15-001
incident_date: 2024-11-15
severity: SEV-1
services_affected:
  - auth-service
  - payment-service
tags:
  - database
  - connection-pool
  - production
---
```

### Temporal Queries

**Use Case:** "Find all database-related incidents in the past 6 months"

```python
def search_postmortems(query, start_date, end_date, tags=None):
    """Search post-mortems with temporal and tag filtering."""
    filters = {
        'type': 'postmortem_section',
        'incident_date': {'gte': start_date, 'lte': end_date}
    }

    if tags:
        filters['tags'] = {'in': tags}

    return index.search(query, filter=filters)

# Example
results = search_postmortems(
    query="database connection failures",
    start_date="2024-06-01",
    end_date="2024-11-30",
    tags=["database", "production"]
)
```

### Cross-Referencing Incidents

**Metadata Linking:**

```python
chunk_metadata = {
    'incident_id': 'INC-2024-11-15-001',
    'related_incidents': ['INC-2024-10-03-005', 'INC-2024-09-12-003'],
    'related_runbooks': ['database-failover', 'connection-pool-tuning'],
    'services_affected': ['auth-service', 'payment-service']
}
```

**Query Enhancement:**

When post-mortem is retrieved, system can:

1. Fetch related incidents ("This happened before: INC-2024-10-03")
2. Fetch relevant runbooks ("Remediation procedure: database-failover")
3. Fetch service documentation ("About auth-service architecture")

**LLM Context:**

```
Retrieved Post-Mortem: INC-2024-11-15-001

Root Cause: Connection pool exhaustion in PostgreSQL

Related Incidents (similar pattern):
- INC-2024-10-03-005: Same root cause, different trigger
- INC-2024-09-12-003: Connection pool issue, auth-service

Relevant Runbooks:
- database-failover: Procedure for handling DB failures
- connection-pool-tuning: How to adjust pool settings

Services Affected:
- auth-service (primary impact)
- payment-service (cascading failure)
```

**Result:** LLM can synthesize patterns across incidents, suggest preventive measures.

### Version Control for Compliance

**Post-mortems are often amended:**

- Initial draft (1 hour after incident)
- Updated RCA (2 days after)
- Final version with action items (1 week after)

**Schema:**

```python
{
    'chunk_id': 'postmortem_INC-001_v3',
    'incident_id': 'INC-2024-11-15-001',
    'version': 3,
    'created_at': '2024-11-15T12:00:00Z',
    'updated_at': '2024-11-22T10:00:00Z',
    'status': 'final',  # draft, in_review, final, archived
    'version_notes': 'Added action items from retrospective'
}
```

**Query:**

- **Current queries:** Retrieve `status = 'final'` only
- **Audit queries:** "Show evolution of INC-001 post-mortem" → retrieve all versions

---

## 6. Monitoring Alerts and Oncall Documentation

### The Problem

**Alerts are template-based:**

```yaml
alert: DatabaseConnectionPoolExhaustion
expr: postgres_pool_connections_active / postgres_pool_connections_max > 0.95
for: 5m
labels:
  severity: critical
  service: auth-service
  team: platform-engineering
annotations:
  summary: "Connection pool at {{ $value }}% capacity"
  description: |
    The PostgreSQL connection pool for {{ $labels.service }} is at {{ $value }}% capacity.

    Impact: New connections will fail, causing authentication failures.

    Immediate Actions:
    1. Check for slow queries: `SELECT * FROM pg_stat_activity WHERE state='active' ORDER BY query_start;`
    2. Kill long-running queries if safe: `SELECT pg_terminate_backend(pid);`
    3. Restart service if pool doesn't recover: `kubectl rollout restart deployment/auth-service`

    Runbook: https://wiki.example.com/runbooks/database-connection-pool

    Escalation: If issue persists >15 minutes, escalate to #oncall-escalation
```

**Challenges:**

- **Table-heavy:** Structured metadata (severity, service, team)
- **Context-heavy:** Impact, actions, escalation path must stay together
- **Cross-references:** Links to runbooks, dashboards
- **Time-sensitive:** Oncall engineer needs complete info immediately

### Solution: Per-Alert Chunking with Metadata Enrichment

**Strategy:**

- **One alert = one chunk** (typically 300-600 tokens)
- Extract structured metadata (severity, service, team)
- Preserve complete context (signal, threshold, response)

**Implementation:**

```python
def chunk_alert(alert_yaml):
    """Chunk monitoring alert with metadata extraction."""
    alert = yaml.safe_load(alert_yaml)

    chunk_text = f"""
Alert: {alert['alert']}

Expression: {alert['expr']}
Duration: {alert.get('for', 'immediate')}

Severity: {alert['labels']['severity']}
Service: {alert['labels']['service']}
Team: {alert['labels']['team']}

Summary: {alert['annotations']['summary']}

Description:
{alert['annotations']['description']}
""".strip()

    chunk_metadata = {
        'type': 'monitoring_alert',
        'alert_name': alert['alert'],
        'severity': alert['labels']['severity'],
        'service': alert['labels']['service'],
        'team': alert['labels']['team'],
        'has_runbook': 'runbook' in alert['annotations'].get('description', '').lower()
    }

    return {
        'text': chunk_text,
        'metadata': chunk_metadata
    }
```

**Query Filtering:**

```python
def search_alerts(query, severity=None, service=None, team=None):
    """Search alerts with metadata filtering."""
    filters = {'type': 'monitoring_alert'}

    if severity:
        filters['severity'] = severity
    if service:
        filters['service'] = service
    if team:
        filters['team'] = team

    return index.search(query, filter=filters)

# Oncall query
results = search_alerts(
    query="database connection issues",
    severity="critical",
    service="auth-service"
)
```

**Operational Benefit:** Oncall engineer asks "What should I do about database connection errors?" → retrieves alert with complete response procedure.

---

## 7. Operational Patterns for SRE Content

### 7.1 Freshness Requirements by Content Type

| Content Type | Update Frequency | Freshness Requirement | Strategy |
|--------------|------------------|----------------------|----------|
| **IaC (Terraform/K8s)** | Weekly to monthly | Critical (stale = dangerous) | Webhook re-indexing on git push |
| **Runbooks** | Monthly to quarterly | Critical | Time-weighted reranking (decay_days=30) |
| **Post-Mortems** | One-time (then stable) | Medium | Temporal tagging, no decay |
| **Logs** | Continuous (streaming) | High for recent, low for old | Rolling index (hot/warm/cold) |
| **Stack Traces** | Continuous | Medium | Deduplication by signature, occurrence tracking |
| **Monitoring Alerts** | Quarterly | High | Version control, deprecation flags |

### 7.2 Access Control Patterns

**Multi-Tenant Isolation:**

```python
chunk_metadata = {
    'tenant_id': 'team-platform-engineering',
    'access_control_list': ['platform-engineering', 'sre-team'],
    'sensitivity': 'high'  # low, medium, high, restricted
}

# Query with access control
results = index.search(
    query=user_query,
    filter={
        'tenant_id': user.team,  # Only retrieve team's content
        'access_control_list': {'in': user.teams}  # Or shared content
    }
)
```

**Environment-Based Access:**

```python
# Junior SREs can't access production IaC
if user.role == 'junior-sre':
    filters['environment'] = {'in': ['development', 'staging']}
else:
    filters['environment'] = {'in': ['development', 'staging', 'production']}
```

**Critical:** Production runbooks/IaC leaking to unauthorized users is a security incident.

### 7.3 Time-Aware Retrieval

**Current State vs Historical Queries:**

```python
def intelligent_temporal_filter(query, user_context):
    """Apply time filtering based on query intent."""

    # Detect query intent
    if any(word in query.lower() for word in ['how', 'what', 'current', 'now']):
        # User wants current information
        cutoff = datetime.now() - timedelta(days=30)
        return {'updated_at': {'gte': cutoff}}

    elif any(word in query.lower() for word in ['incident', 'outage', 'during']):
        # User investigating historical event
        # Extract date from query or user context
        incident_date = extract_date_from_query(query) or user_context.get('incident_date')
        if incident_date:
            # Retrieve content as it existed during incident
            return {
                'valid_from': {'lte': incident_date},
                'valid_until': {'gte': incident_date}  # or null
            }

    else:
        # Default: prefer recent, but include older content
        return {}  # No filter, rely on time-weighted reranking
```

**Example:**

- Query: "How do I restart auth-service?" → Retrieve current runbook
- Query: "How did we restart auth-service during the Nov 15 incident?" → Retrieve runbook as it existed on Nov 15

### 7.4 Service-Scoped Retrieval

**Oncall Context:**

```python
def oncall_aware_search(query, user):
    """Scope retrieval to user's oncall responsibilities."""
    # Detect which service user is oncall for
    oncall_services = get_oncall_services(user)

    if oncall_services:
        # Prioritize content for oncall services
        results_oncall = index.search(
            query=query,
            filter={'service': {'in': oncall_services}},
            k=10
        )

        # Fallback: Retrieve broader content if oncall results insufficient
        if len(results_oncall) < 5:
            results_broader = index.search(query=query, k=10)
            return merge_and_rerank(results_oncall, results_broader)
        else:
            return results_oncall
    else:
        # User not oncall, return general results
        return index.search(query=query, k=10)
```

**Benefit:** Oncall engineer for auth-service queries "connection errors" → retrieves auth-service runbooks first, even if other services have similar errors.

### 7.5 Incident-Linked Retrieval

**During active incidents:**

```python
def incident_context_retrieval(query, active_incident=None):
    """Enhance retrieval with active incident context."""
    if active_incident:
        # Retrieve content related to active incident
        incident_metadata = get_incident_metadata(active_incident)

        filters = {
            'service': {'in': incident_metadata['services_affected']},
            'tags': {'in': incident_metadata['tags']}
        }

        # Combine query-based retrieval with incident-context retrieval
        query_results = index.search(query, k=5)
        incident_results = index.search(
            query=query,
            filter=filters,
            k=5
        )

        return merge_and_deduplicate(query_results, incident_results)
    else:
        return index.search(query, k=10)
```

**Example:**

Active incident: INC-2024-11-18-003 (auth-service, database, SEV-1)

Query: "connection pool"

→ Retrieves:
1. Auth-service runbooks
2. Database troubleshooting guides
3. Previous incidents with "database" tag
4. Connection pool tuning documentation

**Result:** Incident-specific context automatically prioritized.

---

## 8. Content Type Decision Matrix

### Quick Reference: Which Strategy for Which Content?

| Content Type | Primary Challenge | Recommended Strategy | Key Metadata | Retrieval Pattern |
|--------------|-------------------|---------------------|--------------|-------------------|
| **Terraform/IaC** | Syntax fragmentation | AST-based (Code-Aware) | `environment`, `resource_type` | Hybrid (Dense + Sparse) |
| **Kubernetes YAML** | Schema integrity | Per-manifest chunking | `kind`, `namespace`, `name` | Hybrid |
| **Application Logs** | No structure, high volume | Sliding window (512 tokens, 20% overlap) | `start_timestamp`, `end_timestamp` | Hybrid, temporal filter |
| **Stack Traces** | High entropy, non-linguistic | Summary-Index | `exception_type`, `occurrence_count` | Sparse (BM25) on summary |
| **Runbooks** | Prerequisites must stay with steps | Layout-Aware Hierarchical | `service`, `risk_level`, `requires_prerequisites` | Dense + parent-child |
| **Post-Mortems** | Narrative flow, audit trail | Layout-Aware Hierarchical | `incident_id`, `incident_date`, `severity` | Dense + temporal filter |
| **Monitoring Alerts** | Template-heavy, context-critical | Per-alert chunking | `severity`, `service`, `team` | Dense + metadata filter |

### When to Use Summary-Index Pattern

**Apply Summary-Index when:**

✅ Content is high-entropy (UUIDs, hex codes, memory addresses)
✅ Content is voluminous (50+ lines) but only small portion is semantically relevant
✅ Queries are natural language, but content is non-linguistic
✅ Full context needed for generation, but not for matching

**Examples:**

- Stack traces: Summary = exception type + top frames, Full = 50-line trace
- Large config files: Summary = key settings, Full = 1000-line config
- Database query plans: Summary = slow query + table, Full = EXPLAIN output

**Skip Summary-Index when:**

- Content is already concise (<500 tokens)
- Entire content is semantically relevant
- Queries match content vocabulary (no abstraction gap)

---

## Summary

SRE content requires content-specific chunking strategies:

1. **Infrastructure-as-Code:** AST-based splitting preserves syntax, environment metadata prevents cross-environment hallucinations
2. **Logs:** Sliding window with timestamp anchoring, hybrid search for high-entropy IDs, rolling index for volume control
3. **Stack Traces:** Summary-Index pattern (match on summaries, retrieve full traces), sparse search on exception types, deduplication by signature
4. **Runbooks:** Layout-Aware Hierarchical preserves prerequisites with procedures, parent-child ensures complete context
5. **Post-Mortems:** Layout-Aware preserves narrative, temporal tagging enables historical queries, cross-referencing links related incidents
6. **Monitoring Alerts:** Per-alert chunking with metadata enrichment, severity/service filtering for oncall contexts

**Operational Patterns:**

- **Freshness:** Time-weighted reranking for runbooks, rolling indices for logs
- **Access Control:** Multi-tenant isolation, environment-based restrictions
- **Time-Aware Retrieval:** Current state vs historical queries
- **Service-Scoped:** Prioritize oncall services, incident-linked context

**Core Principle:** One chunking strategy cannot handle the diversity of SRE content. Match strategy to content characteristics using the decision matrix.

**Next Module:** [Module 10: Decision Trees](10-decision-trees.md) — Quick-reference flowcharts for selecting chunking strategies, retrieval architectures, and debugging quality issues

---

## Discussion Questions

1. Your team manages 500 Terraform files across dev/staging/prod environments. Users complain that queries return production configs when they're working in staging. What's your fix?

2. You're indexing application logs (10 GB/day). Current approach: Fixed-size chunking with no overlap. Oncall engineers report incomplete stack traces in retrieved results. How do you fix this?

3. Post-mortem from 6 months ago is retrieved when users ask "current database configuration." The post-mortem describes an old architecture. What went wrong, and how do you prevent it?

4. Stack traces are 90% of your index size. Each unique trace is indexed 1000+ times. Your vector DB bill is $5000/month. How do you reduce costs without losing retrieval quality?

5. A runbook has 5 sections: Prerequisites (200 tokens), Procedure (600 tokens), Validation (300 tokens), Rollback (400 tokens), Troubleshooting (800 tokens). How do you chunk this to ensure complete operational context is retrieved?
