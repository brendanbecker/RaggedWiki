# Module 02: Chunking Strategies

**Reading Time:** 45-60 minutes

**Prerequisites:** [Module 01: Why RAG Fails](01-why-rag-fails.md)

## Overview

Chunking is the process of dividing documents into smaller units for indexing and retrieval. The chunking strategy you choose directly impacts which failure modes you'll encounter and how severe they'll be.

This module presents four fundamental chunking strategies, explains when each is appropriate, and provides a decision framework for selecting the right strategy for your content types.

**Important:** There is no universal "best" chunking strategy. The right choice depends on your content's characteristics, how users query it, and what trade-offs you're willing to accept.

---

## The Four Fundamental Strategies

### 1. Layout-Aware Hierarchical Chunking
### 2. Code-Aware Chunking
### 3. Semantic Chunking
### 4. Fixed-Size Sliding Window Chunking

We'll explore each in depth, then provide a decision framework for selecting among them.

---

## Strategy 1: Layout-Aware Hierarchical Chunking

### What It Is

Layout-Aware Hierarchical chunking respects the document's inherent structure—headers, sections, and hierarchical organization—using these natural boundaries as chunk delimiters.

**Example:** A Markdown document:

```markdown
# Database Operations Guide

## Connection Pool Management

### Identifying Pool Exhaustion
[400 tokens of diagnostic content]

### Remediation Steps
[600 tokens of procedure]

### Post-Remediation Validation
[300 tokens of validation steps]

## Query Performance Optimization

### Identifying Slow Queries
[500 tokens of content]
```

Layout-Aware chunking produces chunks that align with section boundaries:
- Chunk 1: "Identifying Pool Exhaustion" (400 tokens)
- Chunk 2: "Remediation Steps" (600 tokens)
- Chunk 3: "Post-Remediation Validation" (300 tokens)
- Chunk 4: "Identifying Slow Queries" (500 tokens)

Each chunk carries metadata about its position in the hierarchy:
- Parent section: "Connection Pool Management"
- Grandparent section: "Database Operations Guide"
- Breadcrumb trail: "Database Operations Guide > Connection Pool Management > Remediation Steps"

### When to Use It

**Ideal for:**
- Runbooks and operational playbooks
- Post-mortems and incident reports
- Technical documentation with clear sections
- Design documents
- Policy documents
- Any content that uses hierarchical headers (H1, H2, H3...)

**Content characteristics:**
- Clear section structure with headers
- Logical boundaries between topics
- Hierarchical organization (parent-child relationships matter)
- Sections represent complete operational units

### How It Works

1. **Structure extraction:** Parse headers to build a document hierarchy
2. **Boundary identification:** Use header levels as primary split points
3. **Size balancing:**
   - If a section is too small (<400 tokens), merge with siblings or parent
   - If too large (>900 tokens), recursively split on sub-headers or paragraphs
4. **Metadata enrichment:** Attach parent IDs, breadcrumbs, section depth

### Trade-offs

**Benefits:**
- **Prevents context fragmentation:** Complete procedures stay together
- **Preserves prerequisites:** Warnings and requirements travel with procedures
- **Maintains logical coherence:** Each chunk is a self-contained concept
- **Enables parent-child retrieval:** Can retrieve precise child chunks but expand to full parent context when needed

**Costs:**
- **Requires structured content:** Doesn't work for unstructured prose or code
- **Variable chunk sizes:** Section lengths vary (though this can be a feature, not a bug)
- **More complex implementation:** Requires parsing document structure
- **Depends on consistent formatting:** Poor heading hygiene breaks the strategy

**Example trade-off:** You accept variable chunk sizes (200-800 tokens instead of uniform 512) in exchange for semantic completeness.

### Why It Addresses Key Failure Modes

- **Context fragmentation:** Sections aren't arbitrarily split
- **Chunk boundary problems:** Respects natural logical boundaries
- **Lost prerequisite warnings:** Prerequisites sections stay attached to procedure sections via hierarchy metadata

### Real-World SRE Example: Runbook Structure

**Before (Fixed-size chunking at 512 tokens):**

Chunk might split between "Prerequisites" and "Steps", losing the warning that this procedure requires maintenance mode.

**After (Layout-Aware Hierarchical):**

```
Chunk: "Emergency Database Restart"
├─ Section: Prerequisites (200 tokens)
│  ├─ Must be in maintenance mode
│  └─ Requires DBA access
├─ Section: Steps (400 tokens)
│  └─ [restart procedure]
└─ Section: Validation (150 tokens)
   └─ [health checks]

Total: 750 tokens, complete operational unit
```

If the query matches "Steps", retrieval can expand to include Prerequisites as well, ensuring complete context.

---

## Strategy 2: Code-Aware Chunking

### What It Is

Code-Aware chunking uses syntax understanding (AST - Abstract Syntax Tree parsing) to split code and configuration files at logical boundaries: function definitions, class definitions, resource blocks, etc.

**Example:** A Terraform file:

```hcl
resource "aws_s3_bucket" "logs" {
  bucket = "company-logs"
  # ... 300 tokens of configuration ...
}

resource "aws_s3_bucket" "data" {
  bucket = "company-data"
  # ... 500 tokens of configuration ...
}

resource "aws_iam_policy" "access" {
  name = "s3_access"
  # ... 400 tokens of policy definition ...
}
```

Code-Aware chunking produces:
- Chunk 1: Complete `aws_s3_bucket.logs` resource (300 tokens)
- Chunk 2: Complete `aws_s3_bucket.data` resource (500 tokens)
- Chunk 3: Complete `aws_iam_policy.access` resource (400 tokens)

### When to Use It

**Ideal for:**
- Infrastructure as Code (Terraform, CloudFormation, Ansible)
- Kubernetes YAML manifests
- Application code in repositories
- Configuration files with structure
- CI/CD pipeline definitions

**Content characteristics:**
- Syntactic structure (braces, indentation, keywords)
- Logical units (functions, resources, classes)
- Syntax validity matters (incomplete code is useless)
- Strong dependencies between related blocks

### How It Works

1. **AST parsing:** Use language-specific parsers (tree-sitter, language parsers)
2. **Logical unit identification:** Extract functions, classes, resources as atomic units
3. **Size management:**
   - If a logical unit is too large, split at sub-block boundaries (methods within a class)
   - Keep indivisible blocks intact even if they exceed size targets
4. **Context preservation:** Include imports, parent class context, or provider blocks

### Trade-offs

**Benefits:**
- **Syntax preservation:** Retrieved chunks are valid, runnable code
- **Logical completeness:** Entire resource definitions or functions stay together
- **Semantic coherence:** Related configuration blocks travel together
- **Reduces hallucinated code:** LLM sees complete, real code rather than fragments

**Costs:**
- **Language-specific:** Requires parsers for each language
- **Complexity:** AST parsing is more complex than text splitting
- **Rigid boundaries:** Can't easily merge small functions or split large ones
- **Metadata requirements:** Need to track module paths, dependencies, environments

**Example trade-off:** You accept implementation complexity and language-specific parsing in exchange for syntactically valid, semantically complete code chunks.

### Why It Addresses Key Failure Modes

- **Chunk boundary problems:** Never splits mid-resource or mid-function
- **Context loss:** Environment, module, and provider context preserved in metadata
- **Vocabulary mismatch:** Resource names and configuration keys indexed exactly

### Real-World SRE Example: Terraform Module

**Before (Fixed-size chunking):**

```hcl
Chunk 1:
resource "aws_instance" "web" {
  ami           = "ami-12345"
  instance_type = "t2.micro"

# Chunk boundary here!

Chunk 2:
  tags = {
    Environment = "production"
    Critical    = "yes"
  }
}
```

The chunk boundary splits the resource definition, making both chunks syntactically invalid and semantically incomplete.

**After (Code-Aware chunking):**

```hcl
Chunk 1 (complete resource):
resource "aws_instance" "web" {
  ami           = "ami-12345"
  instance_type = "t2.micro"
  tags = {
    Environment = "production"
    Critical    = "yes"
  }
}

Metadata:
- environment: production
- resource_type: aws_instance
- module_path: modules/compute/web
```

The entire resource is one chunk, syntactically valid and ready to use.

---

## Strategy 3: Semantic Chunking

### What It Is

Semantic chunking uses embedding similarity to detect topic shifts, splitting content when the semantic meaning changes significantly rather than at fixed token counts or structural boundaries.

**How it detects boundaries:**
1. Embed each sentence individually
2. Calculate similarity between consecutive sentences
3. When similarity drops below a threshold, insert a chunk boundary
4. Group sentences between boundaries into chunks

**Example:** A long-form post-mortem narrative:

```
[Sentences 1-5: Describing the initial symptoms - high similarity]
→ Chunk 1: "Initial Symptoms" (350 tokens)

[Sentences 6-8: Describing investigation process - similarity drop from sentence 5 to 6]
→ Chunk 2: "Investigation" (280 tokens)

[Sentences 9-15: Describing root cause - similarity drop from sentence 8 to 9]
→ Chunk 3: "Root Cause Analysis" (520 tokens)
```

### When to Use It

**Ideal for:**
- Narrative post-mortems without clear section headers
- Long-form analysis documents
- Unstructured reports
- Content where topics shift mid-paragraph
- Documents with inconsistent formatting

**Content characteristics:**
- Narrative flow rather than hierarchical structure
- Topics change without explicit markers
- Conceptual boundaries matter more than format
- Sections don't use consistent headers

### How It Works

1. **Sentence embedding:** Generate embeddings for each sentence
2. **Similarity calculation:** Compute cosine similarity between consecutive sentences
3. **Threshold-based splitting:** When similarity drops below threshold (e.g., <0.7), create boundary
4. **Chunk assembly:** Group sentences between boundaries

### Trade-offs

**Benefits:**
- **Topic coherence:** Chunks represent conceptually unified topics
- **Works without structure:** Doesn't require headers or formatting
- **Adaptive boundaries:** Finds natural topic shifts
- **Semantic completeness:** Each chunk covers one topic thoroughly

**Costs:**
- **Computationally expensive:** Requires embedding every sentence during ingestion
- **Tuning required:** Threshold selection is dataset-specific
- **Unpredictable sizes:** Chunk lengths vary widely
- **Ingestion latency:** Much slower than rule-based approaches
- **False boundaries:** Can split when similarity dips due to sentence structure, not topic shift

**Example trade-off:** You accept significantly higher ingestion cost and complexity in exchange for topic-coherent chunks in unstructured content.

### Why It Addresses Key Failure Modes

- **Context fragmentation:** Topics stay together even without headers
- **Semantic coherence:** Natural topical boundaries respected
- **Lost-in-the-middle:** Smaller, focused chunks improve LLM attention (though this varies)

### Limitations

**When it fails:**
- Short sentences with high similarity might not trigger splits even when topics actually change
- Long digressions within a topic might force splits
- Requires good threshold tuning for each content type
- Doesn't handle multi-topic sections well

### Real-World SRE Example: Post-Mortem Narrative

**Content without clear headers:**

```
The incident began at 14:23 UTC when monitoring alerts fired for the payment API. Initial response team confirmed elevated error rates affecting approximately 15% of transactions. Database queries showed normal performance. Network telemetry indicated no unusual patterns. [...]

Further investigation revealed that a recent deployment had introduced a subtle race condition in the connection pool management code. Under specific timing conditions, connections were being returned to the pool in a corrupted state. This only manifested under production load levels. [...]

The root cause was traced to a third-party library upgrade included in the previous week's deployment. The new version had changed the thread-safety guarantees of the connection pool interface without documenting the breaking change. [...]
```

Semantic chunking detects topic shifts:
- Chunk 1: Initial symptoms and immediate response
- Chunk 2: Investigation findings
- Chunk 3: Root cause identification

Even without headers, the content is split at natural conceptual boundaries.

---

## Strategy 4: Fixed-Size Sliding Window Chunking

### What It Is

Fixed-Size Sliding Window creates chunks of uniform size with overlapping content at boundaries. Each chunk contains N tokens, and consecutive chunks overlap by M tokens.

**Example:** A system log file with 512-token chunks and 128-token overlap:

```
Chunk 1: Tokens 0-511    (512 tokens)
Chunk 2: Tokens 384-895  (512 tokens, overlaps 128 with Chunk 1)
Chunk 3: Tokens 768-1279 (512 tokens, overlaps 128 with Chunk 2)
...
```

The overlap ensures that content near chunk boundaries appears in multiple chunks.

### When to Use It

**Ideal for:**
- System logs
- Stack traces
- Time-series data
- Content with no inherent structure
- Continuous streams of text
- When consistency and predictability matter more than semantic coherence

**Content characteristics:**
- Linear, sequential content
- No hierarchical structure or headers
- Temporal ordering is important
- Individual entries are relatively independent
- High volume, automated ingestion

### How It Works

1. **Fixed window:** Define chunk size (e.g., 512 tokens)
2. **Overlap definition:** Define overlap (e.g., 128 tokens = 25%)
3. **Sliding:** Move the window by (chunk_size - overlap) tokens each step
4. **Metadata:** Attach timestamp or position markers

### Trade-offs

**Benefits:**
- **Deterministic:** Same input always produces same chunks
- **Simple implementation:** No parsing or analysis required
- **Predictable sizes:** All chunks are uniform
- **Boundary insurance:** Overlap prevents total information loss at boundaries
- **Fast ingestion:** No computational overhead

**Costs:**
- **Arbitrary boundaries:** Ignores content semantics and structure
- **Context fragmentation:** Procedures, explanations, or concepts may be split
- **Storage redundancy:** Overlap means storing duplicate content
- **No semantic coherence:** Chunks don't represent logical units
- **Requires overlap tuning:** Too little overlap misses context, too much wastes storage

**Example trade-off:** You accept context fragmentation and storage redundancy in exchange for simplicity, speed, and boundary protection.

### Why Overlap Matters

**Without overlap (strict 512-token chunks):**

```
Chunk 1: [...tokens 450-512 contain half of a stack trace]
Chunk 2: [tokens 0-62 contain the other half of the stack trace...]
```

A query matching the stack trace might retrieve only one chunk, getting an incomplete trace.

**With overlap (128-token overlap):**

```
Chunk 1: [...tokens 384-512 contain the full stack trace]
Chunk 2: [tokens 384-512 are duplicated, containing the full stack trace...]
```

Now either chunk retrieval gets the complete stack trace.

### Why It Addresses (Some) Failure Modes

- **Mitigates chunk boundary problems:** Overlap reduces (doesn't eliminate) information loss
- **Works for unstructured content:** When no other structure is available
- **Preserves temporal flow:** Sequential chunks maintain chronological order

### Real-World SRE Example: Log Analysis

**System logs:**

```
2024-01-15 14:23:01 INFO  Service started successfully
2024-01-15 14:23:15 WARN  High memory usage: 85%
2024-01-15 14:23:16 ERROR Connection pool exhausted
2024-01-15 14:23:16 ERROR Failed to process request ID=12345
2024-01-15 14:23:17 ERROR Stack trace follows:
    at com.company.service.Handler.process(Handler.java:145)
    at com.company.pool.ConnectionManager.acquire(ConnectionManager.java:89)
    [...10 more lines of stack trace...]
2024-01-15 14:23:20 INFO  Attempting recovery
```

Fixed-size chunking with overlap ensures:
- The ERROR followed by stack trace stays together in at least one chunk
- Temporal context (the WARN preceding the ERROR) is preserved via overlap
- Query for "connection pool exhausted" retrieves relevant log context

---

## The Four Pillars: A Decision Framework

To select the right chunking strategy, analyze your content across four dimensions:

### Pillar 1: Structure Regularity

**What to assess:** How consistently organized is the content?

**Evaluation scale:**
- **High:** Clear headers, consistent formatting, hierarchical organization
- **Medium:** Some structure but irregular (not all sections use headers)
- **Low:** Unstructured prose, no markers
- **None:** Purely sequential (logs, time-series)

**Impact on strategy:**
- **High structure** → Layout-Aware Hierarchical
- **Medium structure** → Layout-Aware or Semantic (depends on other pillars)
- **Low structure** → Semantic Chunking
- **No structure** → Fixed-Size Sliding Window

**Example questions:**
- Do documents use H1/H2/H3 headers consistently?
- Is there a standard template (e.g., all runbooks follow the same structure)?
- Can you predict section types (Prerequisites, Steps, Validation)?

### Pillar 2: Semantic Density

**What to assess:** How tightly coupled is the information? How much context is needed?

**Evaluation scale:**
- **Very high:** Every line matters, strong dependencies (code, IaC)
- **High:** Concepts build on each other, prerequisites matter (runbooks)
- **Medium:** Related ideas, but paragraphs are somewhat independent
- **Low:** Individual entries are self-contained (logs)

**Impact on strategy:**
- **Very high density** → Code-Aware (preserves syntax and dependencies)
- **High density** → Layout-Aware Hierarchical (keeps related concepts together)
- **Medium density** → Semantic or Layout-Aware (depends on structure)
- **Low density** → Fixed-Size Sliding Window (individual entries don't need full context)

**Example questions:**
- If you split this content arbitrarily, is it dangerous or just suboptimal?
- Do procedures require prerequisites to be safe?
- Are concepts self-contained or do they depend on surrounding context?

### Pillar 3: Query Patterns

**What to assess:** How will users search for and use this content?

**Query type categories:**
- **Procedural:** "How do I...?" (need complete procedures)
- **Diagnostic:** "Why is X failing?" (need causal chains)
- **Lookup:** "What is the value of...?" (need exact matching)
- **Comparative:** "Difference between X and Y?" (need multiple complete explanations)

**Impact on strategy:**
- **Procedural/Diagnostic queries** → Layout-Aware Hierarchical (complete operational units)
- **Lookup queries** → Code-Aware or Fixed-Size (exact values, identifiers)
- **Mixed queries** → Hybrid approach or Layout-Aware with metadata

**Example questions:**
- Do queries need exact matches (error codes) or semantic matches (concepts)?
- Are users looking for procedures or facts?
- Do answers require multi-step reasoning or simple retrieval?

### Pillar 4: Update Frequency & Temporal Dynamics

**What to assess:** How often does content change? Does time matter?

**Evaluation scale:**
- **Static:** Rarely changes (architectural principles)
- **Versioned:** Periodic updates with version significance (API docs v1, v2)
- **Dynamic:** Frequent updates (pricing, metrics)
- **Streaming:** Continuous updates (logs, monitoring)

**Impact on strategy:**
- **Static/Versioned** → Layout-Aware or Code-Aware (structure more important than update mechanism)
- **Dynamic** → Requires metadata for recency, but chunking strategy depends on other pillars
- **Streaming** → Fixed-Size Sliding Window (handles continuous ingestion, preserves temporal order)

**Example questions:**
- How often does this content change?
- Do old versions need to remain accessible?
- Is temporal ordering critical to understanding?
- Do queries reference specific time periods?

---

## Decision Matrix: Content Type → Strategy

| Content Type | Structure | Density | Query Pattern | Update Frequency | Recommended Strategy |
|---|---|---|---|---|---|
| **Runbooks** | High | High | Procedural | Versioned | **Layout-Aware Hierarchical** |
| **Post-mortems** | Medium-High | Medium | Diagnostic/Narrative | Static | **Layout-Aware** or **Semantic** |
| **Terraform/IaC** | Syntactic | Very High | Lookup/Procedural | Dynamic | **Code-Aware** |
| **Kubernetes YAML** | Syntactic | Very High | Lookup | Dynamic | **Code-Aware** |
| **System Logs** | None | Low | Diagnostic/Temporal | Streaming | **Fixed-Size Sliding Window** |
| **Stack Traces** | Linear | Medium | Lookup/Diagnostic | Static | **Fixed-Size Sliding Window** |
| **Design Docs** | High | Medium | Conceptual | Static | **Layout-Aware Hierarchical** |
| **API Docs** | High | Medium | Lookup/Procedural | Versioned | **Layout-Aware Hierarchical** |

---

## Applying the Framework: Examples

### Example 1: SRE Runbooks

**Analysis:**
- **Structure:** High (consistent sections: Prerequisites, Steps, Validation)
- **Density:** High (procedures unsafe without full context)
- **Query Pattern:** Procedural ("how do I fix X?")
- **Update Frequency:** Versioned (quarterly reviews, incident-driven updates)

**Decision:** Layout-Aware Hierarchical

**Rationale:**
- Structure supports it (clear headers)
- Density requires it (unsafe to split procedures)
- Query pattern benefits from complete operational units
- Versioning handled via metadata, not chunking strategy

**Implementation:**
- Split on H2/H3 headers
- Keep sections 400-900 tokens
- Attach breadcrumbs for parent-child retrieval
- Metadata: service_owner, severity, last_updated

### Example 2: Infrastructure as Code (Terraform)

**Analysis:**
- **Structure:** Syntactic (HCL resources and modules)
- **Density:** Very High (syntax errors render chunks useless)
- **Query Pattern:** Lookup ("what's the config for X resource?")
- **Update Frequency:** Dynamic (multiple updates per day)

**Decision:** Code-Aware

**Rationale:**
- Syntax preservation is non-negotiable
- Resource blocks are logical units
- Queries need complete, valid configurations
- Environment metadata critical for filtering (prod vs. staging)

**Implementation:**
- AST-based splitting on resource boundaries
- Keep entire resources intact even if >900 tokens
- Metadata: environment, module_path, resource_type
- Separate index per environment to prevent cross-contamination

### Example 3: System Logs

**Analysis:**
- **Structure:** None (sequential timestamps)
- **Density:** Low (individual log lines often independent)
- **Query Pattern:** Diagnostic + temporal ("what happened before error X?")
- **Update Frequency:** Streaming (continuous)

**Decision:** Fixed-Size Sliding Window

**Rationale:**
- No structure to preserve
- Temporal ordering is critical
- Overlap prevents splitting stack traces
- High volume requires simple, fast ingestion

**Implementation:**
- 512-token chunks with 128-token (25%) overlap
- Anchor windows on timestamp boundaries when possible
- Metadata: timestamp range, service, log level
- Hybrid retrieval (BM25 for error codes + dense for descriptions)

---

## Common Pitfalls

### Pitfall 1: "One Size Fits All"

**Mistake:** Using the same chunking strategy (often fixed-size 512 tokens) for all content.

**Why it fails:** Your wiki contains fundamentally different content types. Runbooks need layout-aware splitting; logs need sliding windows.

**Solution:** Content-aware pipeline that routes different content types to different chunking strategies.

### Pitfall 2: Ignoring Trade-offs

**Mistake:** Choosing semantic chunking because it sounds sophisticated, without considering the ingestion cost.

**Why it fails:** Embedding every sentence in 10,000 documents might add hours to ingestion and significant compute cost, for content that would work fine with layout-aware splitting.

**Solution:** Evaluate whether the benefits justify the costs for each content type.

### Pitfall 3: Over-optimizing Chunk Size

**Mistake:** Spending days tuning whether chunks should be 487 or 523 tokens.

**Why it fails:** The 400-900 token range is a guideline, not a precise target. Other factors (structure preservation, semantic coherence) matter more.

**Solution:** Target the range, but prioritize logical completeness over hitting an exact number.

### Pitfall 4: Ignoring Metadata

**Mistake:** Chunking correctly but not attaching metadata (breadcrumbs, service owners, environments).

**Why it fails:** Even well-chunked content can't be filtered or contextualized without metadata.

**Solution:** Metadata design is as important as chunking strategy.

---

## Key Takeaways

1. **Match strategy to content characteristics:** The Four Pillars framework helps you analyze content and select appropriately

2. **Every strategy has trade-offs:** There is no "best" strategy—only appropriate vs. inappropriate for your context

3. **Structure preservation matters:** Respecting document structure (when it exists) prevents context fragmentation

4. **Overlap is insurance:** When you can't avoid arbitrary boundaries (logs, unstructured content), overlap mitigates damage

5. **Metadata completes the picture:** Even perfect chunks need rich metadata for filtering and context assembly

6. **Different content needs different strategies:** Don't force all content through one chunker

---

## What's Next

Now that you understand chunking strategies and can select appropriate approaches for different content types, future modules will cover:

- **Embedding selection:** Choosing embedding models based on your content and query patterns
- **Retrieval architecture:** Multi-stage pipelines that compensate for chunking limitations
- **Production deployment:** Handling updates, versioning, and deduplication at scale

The goal is a comprehensive understanding of how chunking, retrieval, and context assembly work together to build robust RAG systems that minimize failure modes while accepting appropriate trade-offs for your requirements.
