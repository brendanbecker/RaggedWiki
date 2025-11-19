# Module 07: Evaluation Approach

**Learning Objective:** Understand how to validate RAG retrieval quality, build evaluation datasets, identify red flags, and implement continuous monitoring without relying on benchmark claims.

**Reading Time:** 30-45 minutes

**Prerequisites:** Modules 01-04 (understanding failure modes, chunking strategies, and retrieval architecture)

---

## Introduction: Why Evaluation Matters

You cannot improve what you don't measure. But measuring RAG quality is different from traditional software testing:

- **No single ground truth:** Relevance is subjective and context-dependent
- **Multiple failure modes:** Retrieval can fail, or succeed but provide incomplete context, or succeed but LLM still hallucinates
- **Domain-specific quality:** What constitutes "good retrieval" varies by use case
- **Evolving content:** Your wiki changes; evaluation must detect degradation over time

**Philosophy:** Focus on **how to validate** quality in your specific context, not achieving arbitrary percentage targets. Evaluation frameworks should be practical, continuous, and tailored to your failure modes.

---

## What to Measure

### 1. Recall@K: Did We Find the Answer?

**Definition:** Did the relevant information appear in the top-K results?

**Why it matters:** High recall means the retrieval system isn't missing the answer—it's in the candidate set even if not perfectly ranked. Low recall means the right content never had a chance.

**When to measure:**
- **Recall@10** is common for interactive use (users typically review ~10 results)
- **Recall@5** for higher-precision requirements
- **Recall@20** when using reranking (cast wide net, then narrow)

**Implementation example:**

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

**Quality indicators:**
- **Recall@10 < 0.85** suggests chunking fragmentation or embedding model mismatch
- **Degrading recall over time** indicates content changes broke retrieval

**Trade-off:** High recall is necessary but not sufficient. You can retrieve the right chunk but still get wrong answers if context is incomplete or LLM hallucinates.

---

### 2. Mean Reciprocal Rank (MRR): How Quickly Do We Find It?

**Definition:** How early does the first relevant result appear?

**Why it matters:** Users don't scroll endlessly. The first good answer should appear in positions 1-3, not position 27.

**Formula:** MRR = average of (1 / rank of first relevant result)

**Example:**
- Query 1: First relevant at position 1 → 1/1 = 1.0
- Query 2: First relevant at position 3 → 1/3 = 0.33
- Query 3: First relevant at position 10 → 1/10 = 0.10
- **MRR = (1.0 + 0.33 + 0.10) / 3 = 0.48**

**When to prioritize MRR:**
- Interactive applications where users see ranked lists
- When reranking isn't used (initial retrieval order matters)
- Comparing different retrieval architectures

**Trade-off:** MRR emphasizes top results. It doesn't tell you if **all** relevant information was retrieved (context completeness).

---

### 3. Context Completeness: Did We Retrieve All Necessary Pieces?

**Definition:** Did we retrieve enough context for the LLM to produce a complete, accurate answer?

**Why it matters:** A single chunk might mention "restart the service" without explaining the prerequisites or validation steps. Context fragmentation causes hallucinations.

**How to measure:**

**Option A: Multi-Chunk Recall**
```python
def measure_context_completeness(eval_dataset):
    """Check if ALL required chunks were retrieved."""
    complete = 0
    for query, required_chunk_ids in eval_dataset:
        results = index.search(query, k=20)
        retrieved_ids = {r.doc_id for r in results}

        if all(chunk_id in retrieved_ids for chunk_id in required_chunk_ids):
            complete += 1

    return complete / len(eval_dataset)
```

**Option B: Human Judgment**
- Present retrieved context to evaluators
- Ask: "Can you confidently answer the query with this context alone?"
- Track: Sufficient / Incomplete / Missing Critical Info

**Option C: LLM Self-Evaluation** (see Self-RAG pattern, Module 05)
```python
reflection_prompt = """
You retrieved the following context:
{retrieved_context}

For the user's question: {user_query}

Is the information sufficient to answer accurately?
- YES: Context is complete
- NO: Context is incomplete (specify what's missing)
"""
```

**Warning signs:**
- Answers are correct but incomplete ("missing the safety warning")
- Users frequently follow up with "what about [missing step]?"
- LLM hedges: "The procedure might involve..." (lack of confidence from incomplete context)

---

### 4. Answer Quality: Did the LLM Produce a Correct Response?

**Definition:** Given the retrieved context, did the LLM generate an accurate, safe, complete answer?

**Why this is separate from retrieval quality:**
- Retrieval can succeed but LLM hallucinates anyway
- Retrieval can fail but LLM admits "I don't have enough information" (good behavior)
- Answer quality depends on both retrieval AND generation

**How to measure:**

**Human Evaluation (Gold Standard):**
- Subject matter experts judge answers
- Scale: Correct / Partially Correct / Incorrect / Hallucinated / Refused (appropriately)
- Track hallucination rate separately

**Automated Proxy Metrics:**
- **Citation accuracy:** Did the LLM correctly cite sources?
- **Grounding check:** Are all claims present in retrieved context? (LLM-as-judge)
- **Consistency:** Does the same query produce the same answer? (variance indicates instability)

**Failure mode tracking:**

| Failure Mode | Retrieval OK? | Answer OK? | Root Cause |
|--------------|---------------|------------|------------|
| Hallucination | ✓ (correct context) | ✗ (fabricated details) | LLM generation issue, prompt engineering |
| Missing info | ✗ (incomplete context) | ✗ (can't answer fully) | Chunking fragmentation, retrieval failure |
| Refused appropriately | ✗ (no relevant context) | ✓ (said "I don't know") | Good behavior, but retrieval failed |
| Wrong version | ✗ (outdated content) | ✗ (dangerous advice) | Temporal filtering failure |

---

### 5. Precision@K: How Many Retrieved Results Are Relevant?

**Definition:** What fraction of the top-K results are actually relevant?

**Why it matters:** Low precision wastes LLM context window on irrelevant information, increasing costs and potentially confusing the model.

**Formula:** Precision@K = (number of relevant docs in top-K) / K

**When to prioritize precision:**
- When context window is limited (need to maximize signal-to-noise ratio)
- When processing costs are high (fewer tokens to LLM = lower cost)
- When irrelevant context frequently misleads the LLM

**Trade-off with recall:** Optimizing for precision (strict filters) may reduce recall (miss relevant content). Balance depends on your use case.

---

## How to Validate Quality

### 1. Synthetic Datasets: LLM-Generated Queries

**Concept:** Use an LLM to generate test queries from your documents, then measure if your RAG system retrieves the source documents.

**How to create:**

```python
synthetic_query_prompt = """
You are a technical user searching a wiki. Generate 3-5 realistic queries that this document should answer.

Document Title: {document.title}
Document Content (excerpt): {document.text[:500]}

Requirements:
1. Use realistic phrasing (how users actually search)
2. Mix specific (lookup) and conceptual (diagnostic) queries
3. Include queries users might ask BEFORE finding this doc

Output format:
- Query 1: ...
- Query 2: ...
"""
```

**Pros:**
- **Scalable:** Generate thousands of test cases automatically
- **Coverage:** Systematically test entire corpus
- **Reproducible:** Regression testing on same queries over time
- **Edge case generation:** Prompt for ambiguous queries, version mismatches, etc.

**Cons:**
- **Vocabulary mismatch:** LLM-generated queries may not match real user language
- **Query complexity:** May be too well-formed compared to actual user queries
- **Ground truth limitations:** Assumes the source document is the correct answer (might not be)
- **Evaluation drift:** LLM generating queries AND evaluating answers can create circular validation

**When to use:**
- **Baseline regression testing:** Ensure quality doesn't degrade when content or code changes
- **Coverage testing:** Verify all major content is retrievable somehow
- **A/B comparison:** Compare two retrieval approaches on same synthetic queries

**When NOT to rely solely on synthetic:**
- Real user queries often have typos, abbreviations, and domain jargon that synthetic queries miss
- Synthetic queries may not reflect actual confusion points or knowledge gaps

---

### 2. Human Evaluation: Subject Matter Expert Judgment

**Concept:** Domain experts manually judge whether retrieved results and generated answers are correct.

**Process:**
1. Sample queries (real or synthetic)
2. Retrieve top-K results
3. Present to evaluators with rubric
4. Collect judgments (relevant / not relevant for each result)

**Rubric example:**

| Rating | Definition | Example |
|--------|------------|---------|
| Highly Relevant | Directly answers query, complete context | Runbook for exact issue user asked about |
| Relevant | Related but incomplete or tangential | Mentions the service but different failure mode |
| Marginally Relevant | Correct domain but doesn't help | General docs about the service, not the specific issue |
| Not Relevant | Completely unrelated | Different service or topic |

**Pros:**
- **Ground truth:** Experts know what "correct" means in your domain
- **Nuance:** Can judge context completeness, safety implications, version correctness
- **Qualitative insights:** Experts notice failure patterns you wouldn't detect with metrics

**Cons:**
- **Expensive:** Expert time is costly and limited
- **Slow:** Can't evaluate thousands of queries
- **Subjective:** Different experts may disagree (measure inter-rater agreement)
- **Not continuous:** Can't run on every query in production

**When to use:**
- **Ground truth dataset creation:** Curate 50-200 high-quality query-document pairs
- **Validation of synthetic datasets:** Check if synthetic queries are realistic
- **Major system changes:** Before/after comparison when changing chunking or retrieval
- **Failure analysis:** Deep dive on queries flagged by automated monitoring

---

### 3. A/B Testing: Real-World Production Validation

**Concept:** Deploy two retrieval approaches simultaneously, randomly route queries, compare outcomes.

**Setup:**
- **Variant A:** Current production system
- **Variant B:** New approach (different chunking, retrieval architecture, embedding model)
- **Traffic split:** 50/50 or 90/10 (safety)
- **Metrics:** Track recall, latency, zero-result rate, user feedback

**Isolation requirements:**

**Critical:** Ensure apples-to-apples comparison
- **Same query set:** Random assignment per query (not per user session, to avoid confounders)
- **Same LLM:** Don't change generation model during test
- **Same content:** Use same document corpus (don't test new chunking on updated content)
- **Statistical significance:** Run long enough for meaningful sample size

**Example:**
```python
def route_query(query):
    variant = random.choice(['A', 'B'])

    if variant == 'A':
        results = current_index.search(query)
    else:
        results = new_index.search(query)

    # Log for analysis
    metrics.track_experiment(variant, query, results)
    return results
```

**Pros:**
- **Real-world validation:** Measures impact on actual users with real queries
- **Holistic:** Captures latency, user satisfaction, downstream effects
- **Objective:** Removes experimenter bias

**Cons:**
- **Requires traffic:** Need sufficient query volume for statistical power
- **Risk:** Poor variant B degrades user experience
- **Confounders:** Content changes, user behavior shifts can skew results
- **Complex infrastructure:** Need duplicate indexes, experiment tracking, analysis pipelines

**When to use:**
- **Major architecture changes:** Switching from single-stage to hybrid retrieval
- **Embedding model updates:** Validate that new model improves retrieval in your domain
- **Final validation:** After synthetic and human evaluation pass, verify in production

---

### 4. Regression Testing: Ensuring Quality Doesn't Degrade

**Concept:** Maintain a fixed evaluation dataset, run it on every code or content change, alert on degradation.

**Process:**
1. Curate **golden dataset:** 50-200 query-document pairs
   - Include common queries
   - Include past failures (now fixed)
   - Include edge cases (version mismatches, ambiguous queries)
2. Baseline metrics: Measure current system performance
3. **CI/CD integration:** Run evaluation on every chunking logic change, content update, or dependency upgrade
4. **Regression alerts:** If Recall@10 drops >5%, block deployment

**Example golden dataset entry:**

```yaml
- query: "How do I restart auth-service in production?"
  relevant_chunks:
    - doc_id: "runbooks/auth-service-restart-v3"
      must_include: true  # Critical chunk
    - doc_id: "runbooks/auth-service-prerequisites"
      should_include: true  # Important context
  version: "current"  # Ensure latest version retrieved, not v2

- query: "What does error code 0x80040154 mean?"
  relevant_chunks:
    - doc_id: "errors/0x80040154-class-not-registered"
      must_include: true
  exclusions:
    - doc_id: "errors/0x80040155-different-error"  # Similar ID, wrong result
```

**Metrics to track over time:**
- **Recall@10:** Are we still finding the right documents?
- **MRR:** Is the first relevant result still appearing early?
- **Zero-result rate:** Are we failing to find answers more often?
- **Latency:** Is retrieval slowing down?

**When to use:**
- **Continuous integration:** Every code change, content update, dependency upgrade
- **Long-term monitoring:** Weekly snapshots to detect gradual degradation
- **Before production deployment:** Gate releases on regression test pass

---

## Building Evaluation Datasets

### 1. Curate From Real Usage

**Best source: Actual user queries**

**Where to find them:**
- **Support tickets:** Questions users asked support teams
- **Search logs:** If you have an existing search system, mine the logs
- **Slack/chat history:** Questions asked in internal channels
- **Onboarding questions:** What new employees ask

**Curation process:**
1. **Collect raw queries:** 500-1000 real queries
2. **De-duplicate:** Remove near-duplicates (paraphrasing)
3. **Annotate with ground truth:** SMEs label which documents should be retrieved
4. **Balance query types:**
   - Procedural: "How do I...?"
   - Diagnostic: "Why is X failing?"
   - Lookup: "What is the value of...?"
   - Comparative: "Difference between X and Y?"
5. **Include failure cases:** Queries that currently fail (zero results or wrong answers)

**Pros:** Represents actual user needs, realistic phrasing and typos

**Cons:** Requires significant manual effort, may have gaps in coverage

---

### 2. Synthetic Generation: Prompts for Creating Test Queries

**Basic synthetic query generation:**

```python
def generate_synthetic_queries(document):
    prompt = f"""
You are a DevOps engineer searching a technical wiki.

Document: {document.title}
Content (excerpt): {document.text[:800]}

Generate 5 realistic search queries that users would ask to find this document:
1. A direct procedural query ("How do I...")
2. A diagnostic query ("Why does X fail when...")
3. A lookup query ("What is the [specific value/config]...")
4. A conceptual query (rephrased, no exact keywords)
5. An ambiguous query (could match multiple documents)

Use realistic language (abbreviations, technical jargon, imperfect grammar).
"""

    return llm.generate(prompt)
```

**Advanced: Edge case generation**

**Version mismatch queries:**
```python
edge_case_prompt = """
This document exists in 3 versions:
- v1 (deprecated, 2022): Uses systemctl restart
- v2 (current, 2023): Uses kubectl rollout restart
- v3 (beta, 2024): Uses ArgoCD sync

Generate queries that:
1. Should retrieve v2 by default (no version specified)
2. Might accidentally match v1 (legacy terminology)
3. Explicitly request v3
"""
```

**Ambiguous query generation:**
```python
ambiguous_prompt = """
Generate queries that could plausibly match BOTH of these documents:
- Document A: "API Gateway 502 errors"
- Document B: "Load Balancer 502 errors"

Example: "Why am I getting 502 errors?" (ambiguous - which service?)
"""
```

**Missing information queries:**
```python
missing_info_prompt = """
Generate queries that would require combining these 3 documents:
1. Incident timeline for 2024-01-15 outage
2. Root cause analysis (database connection pool exhaustion)
3. Remediation playbook (increase pool size)

Example: "What caused the January 15 outage and how do I prevent it?"
"""
```

---

### 3. Edge Cases: Critical Scenarios to Test

**A. Version Mismatches**

**Scenario:** Old runbook says "restart with systemctl," new version says "use Kubernetes rolling restart." User searches "how to restart auth-service."

**Test case:**
```yaml
query: "restart auth-service"
expected_behavior:
  - retrieve: "runbooks/auth-service-restart-v3" (newest)
  - exclude: "runbooks/auth-service-restart-v1" (deprecated)
metadata_filter:
  version: "current"
  deprecated: false
```

**Why it matters:** Retrieving outdated content can be **dangerous** in operational contexts.

**B. Ambiguous Queries**

**Scenario:** "auth service down" could mean:
- Authentication service outage
- Authorization failures
- User login unavailable
- auth-service pod restart procedure

**Test case:**
```yaml
query: "auth service down"
acceptable_results:  # Any of these is reasonable
  - "runbooks/authentication-service-outage"
  - "runbooks/auth-service-restart"
  - "incidents/2024-01-auth-service-downtime"
unacceptable_results:  # These are wrong
  - "design-docs/authorization-architecture"  # Related but not actionable
```

**Why it matters:** Tests if retrieval handles ambiguity gracefully (multiple valid results vs. one wrong result).

**C. Missing Information**

**Scenario:** Query requires synthesis across multiple documents that weren't designed to be retrieved together.

**Test case:**
```yaml
query: "Compare auth-service and auth-gateway performance during Black Friday incident"
required_chunks:
  - "incidents/2024-black-friday-postmortem"
  - "metrics/auth-service-performance-nov-2024"
  - "metrics/auth-gateway-performance-nov-2024"
success_criteria:
  - All three chunks retrieved in top-20
  - LLM synthesizes comparison correctly
```

**Why it matters:** Tests multi-hop retrieval, context assembly, and LLM reasoning.

**D. Exact Identifier Precision**

**Scenario:** Error codes, Kubernetes annotations, configuration keys must match exactly.

**Test case:**
```yaml
query: "error 0x80040154"
must_retrieve: "errors/0x80040154-class-not-registered"
must_not_retrieve: "errors/0x80040155-interface-not-registered"  # Similar but different

query: "nginx.ingress.kubernetes.io/force-ssl-redirect"
must_retrieve: "k8s/ingress-annotations-reference"
must_match_exact_annotation: true
```

**Why it matters:** Tests hybrid search (sparse/BM25) effectiveness for high-entropy identifiers.

**E. Cross-Tenant Leakage (Security)**

**Scenario:** Multi-tenant system must NOT retrieve content from other tenants.

**Test case:**
```yaml
query: "database credentials"
user_tenant: "team-A"
must_retrieve_only:
  - tenant_id: "team-A"
must_not_retrieve:
  - tenant_id: "team-B"
  - tenant_id: "team-C"
security_critical: true  # Alert on failure
```

**Why it matters:** Security failure. Access control must be enforced at retrieval time.

---

## Red Flags to Monitor

### 1. Zero Results: Complete Retrieval Failure

**What it means:** No documents matched the query at all.

**Thresholds:**
- **Hourly alert:** >10% zero-result rate
- **Daily warning:** >5% zero-result rate
- **Baseline normal:** 1-3% (some queries are genuinely unanswerable)

**Common root causes:**
- **Vocabulary mismatch:** User terminology doesn't match document language (sparse search would help)
- **Index completeness:** Content hasn't been indexed yet (ingestion pipeline broken)
- **Metadata over-filtering:** Access control rules too strict (legitimate content filtered out)
- **Embedding model mismatch:** Domain-specific jargon not understood by general embedding model

**Investigation steps:**
```python
def analyze_zero_results(query):
    # 1. Check if ANY content exists on this topic
    broad_search = index.search(query, filters=None, k=100)  # Remove all filters

    if len(broad_search) > 0:
        # Content exists, but was filtered out
        print("Cause: Metadata filtering too strict")
        print(f"Found {len(broad_search)} results without filters")

    # 2. Check if query contains known vocabulary
    terms = extract_technical_terms(query)
    for term in terms:
        if term not in embedding_model_vocabulary:
            print(f"Warning: '{term}' may not be in embedding model vocabulary")

    # 3. Try sparse search only
    sparse_results = index.sparse_search(query, k=10)
    if len(sparse_results) > 0:
        print("Cause: Dense embedding failed, sparse search succeeded")
        print("Recommendation: Ensure hybrid search is enabled")
```

---

### 2. Wrong Version Retrieved: Temporal Filtering Issues

**What it means:** User got deprecated, outdated, or dangerous content instead of current version.

**Example:** Runbook from 2022 says "manually edit the database," current runbook says "use the migration script."

**Detection:**
```python
def detect_stale_retrieval(query, results, threshold_days=180):
    now = datetime.now(timezone.utc)

    for result in results:
        age_days = (now - result.metadata['updated_at']).days

        if age_days > threshold_days:
            alert(
                f"Retrieved document is {age_days} days old",
                query=query,
                doc_id=result.doc_id,
                version=result.metadata.get('version')
            )

        # Check if newer version exists
        if result.metadata.get('deprecated'):
            newer_version = find_current_version(result.doc_id)
            if newer_version:
                alert(
                    f"Retrieved deprecated content. Current version: {newer_version}",
                    query=query,
                    retrieved=result.doc_id,
                    should_retrieve=newer_version
                )
```

**Root causes:**
- **Metadata missing:** `deprecated: true` flag not set on old docs
- **Temporal filtering not enabled:** Search doesn't prioritize recent content
- **Version metadata absent:** Can't distinguish v1 from v3
- **Content not updated:** Old doc has higher embedding similarity (more detailed, better written)

**Mitigation:**
- Implement `deprecated` flag and filter at search time
- Boost recent content: `score = base_score * recency_multiplier`
- Version metadata in schema: `version`, `is_current`, `superseded_by`
- Periodic content audits: Flag docs >365 days old without recent review

---

### 3. Security Leaks: Cross-Tenant or Access Control Failures

**What it means:** User retrieved content they shouldn't have permission to see.

**Critical scenarios:**
- **Cross-tenant leakage:** Team A sees Team B's credentials or configurations
- **Environment leakage:** Developer sees production secrets
- **Confidentiality breach:** Public user sees internal documentation

**Detection:**

```python
def validate_access_control(user, query, results):
    for result in results:
        # Check tenant isolation
        if result.metadata['tenant_id'] != user.tenant_id:
            security_alert(
                severity="CRITICAL",
                issue="Cross-tenant leakage",
                user=user.id,
                retrieved_tenant=result.metadata['tenant_id'],
                doc_id=result.doc_id
            )

        # Check access level
        if result.metadata['access_level'] == 'confidential' and user.clearance < 3:
            security_alert(
                severity="HIGH",
                issue="Access control violation",
                user=user.id,
                doc_access_level=result.metadata['access_level'],
                user_clearance=user.clearance
            )
```

**Root causes:**
- **Access control in post-filtering:** Vectors searched, then filtered → reduces recall AND leaks data to vector index
- **Metadata missing:** `tenant_id` or `access_level` not stored with chunks
- **Filter bypass:** Bug in metadata filtering logic
- **Index pollution:** Content indexed with wrong metadata

**Mitigation:**
- **Access control at index time:** Store permissions with vectors, filter during search (not after)
- **Separate indexes per tenant:** Physical isolation (expensive but secure)
- **Audit logs:** Track all retrievals with user ID and result metadata
- **Regular security tests:** Attempt cross-tenant queries, verify zero results

---

### 4. Hallucinations: LLM Generates Unsupported Answers

**What it means:** LLM fabricates information not present in retrieved context.

**Example:**
- Retrieved context: "Restart the service using kubectl rollout restart"
- LLM answer: "Restart the service using kubectl rollout restart. **Wait 5 minutes before checking status.**" (The "5 minutes" is fabricated)

**Detection:**

**Automated grounding check:**
```python
grounding_check_prompt = """
Retrieved Context:
{retrieved_context}

Generated Answer:
{llm_answer}

Task: Identify any claims in the Generated Answer that are NOT supported by the Retrieved Context.

Output format:
- Supported claims: [list]
- Unsupported claims (hallucinations): [list]
"""

result = evaluator_llm.check(grounding_check_prompt)
if result.unsupported_claims:
    metrics.increment('rag.hallucinations')
    log_hallucination(query, context, answer, unsupported_claims)
```

**Human evaluation:**
- Periodic sampling: 50 queries/week
- SMEs judge: Correct / Partially Correct / Hallucinated
- Track hallucination rate over time

**Root causes:**
- **Context fragmentation:** LLM fills gaps when context is incomplete
- **Conflicting information:** Retrieved chunks contradict each other, LLM invents compromise
- **Prompt issues:** LLM not instructed to refuse when unsure
- **Training data leakage:** LLM "remembers" information from training, not retrieved context

**Mitigation:**
- **Improve chunking:** Ensure complete operational units (prerequisites + procedure + validation)
- **Citation enforcement:** Require LLM to cite sources; verify citations are real
- **Prompt engineering:** "Only use provided context. If unsure, say 'I don't have enough information.'"
- **Post-processing:** Automated grounding checks before returning answers

**Acceptable hallucination rate:** Depends on risk tolerance. Operational runbooks should aim for <5%. General documentation might tolerate 10-15%.

---

## Continuous Monitoring: Detecting Degradation Over Time

Evaluation isn't a one-time test—it's an ongoing process. Content changes, users change, and retrieval quality can degrade silently.

### 1. Detect Degradation When Content Changes

**Scenario:** Your wiki grows from 1,000 to 10,000 documents. Retrieval quality degrades because:
- More candidates → harder to rank correctly
- Similar content → precision drops
- Index parameters tuned for 1K docs, not 10K

**Monitoring approach:**

```python
def monitor_content_growth():
    current_count = index.count_chunks()
    last_count = metrics.get('index.chunk_count.last_week')

    growth_rate = (current_count - last_count) / last_count

    if growth_rate > 0.5:  # >50% growth in a week
        alert("Significant content growth detected. Recommend re-tuning:")
        alert(f"  - ANN parameters (HNSW ef_search may need increase)")
        alert(f"  - Retrieval top-K (might need K=20 instead of K=10)")
        alert(f"  - Re-run evaluation dataset to measure impact")
```

**Actions to take:**
- **Re-baseline evaluation:** Run regression tests, expect recall to drop slightly
- **Tune retrieval parameters:** Increase K, adjust ANN recall/speed trade-off
- **Consider hierarchical indexing:** Document-level then chunk-level retrieval (see Module 06)

---

### 2. Track Query Patterns Over Time

**Scenario:** Users start asking about a new service you deployed. Existing content doesn't cover it. Zero-result rate spikes.

**Monitoring:**

```python
def analyze_query_trends():
    # Extract topics from queries (using LLM or keyword extraction)
    current_week_topics = extract_topics(recent_queries)
    last_week_topics = extract_topics(previous_queries)

    new_topics = set(current_week_topics) - set(last_week_topics)

    for topic in new_topics:
        # Check if we have content on this topic
        test_query = f"documentation about {topic}"
        results = index.search(test_query, k=5)

        if len(results) == 0 or results[0].score < 0.6:
            alert(f"Emerging topic with poor coverage: {topic}")
            alert(f"Recommendation: Create documentation for {topic}")
```

**What to track:**
- **Topic distribution:** Are queries shifting to new services, tools, or failure modes?
- **Query complexity:** Are queries getting longer, more technical, more ambiguous?
- **Zero-result queries:** Which topics consistently fail?

**Response actions:**
- **Content gap analysis:** Identify missing documentation
- **Query transformation:** Add domain vocabulary mappings for new topics
- **User education:** If users ask unanswerable questions, explain what docs exist

---

### 3. Identify Systematic Gaps in Coverage

**Scenario:** Certain types of queries consistently fail, revealing patterns in missing content.

**Analysis:**

```python
def find_coverage_gaps(failed_queries):
    # Cluster failed queries by topic
    clusters = cluster_queries(failed_queries)

    for cluster in clusters:
        if cluster.size > 10:  # >10 queries on same topic failed
            print(f"Coverage gap detected: {cluster.topic}")
            print(f"  Example queries: {cluster.examples[:3]}")
            print(f"  Recommendation: Create content covering:")
            print(f"    - {cluster.suggested_sections}")
```

**Common gap patterns:**

**A. Troubleshooting gaps:**
- Queries: "How do I debug X?" "Why does X fail when Y?"
- Gap: You have architecture docs and API references, but no troubleshooting guides

**B. Environment-specific gaps:**
- Queries: "How to deploy to staging?" "Production credentials location?"
- Gap: Documentation assumes production; staging/dev environments undocumented

**C. Integration gaps:**
- Queries: "How does Service A call Service B?" "What's the auth flow between X and Y?"
- Gap: Individual service docs exist, but integration patterns undocumented

**D. Historical context gaps:**
- Queries: "Why did we migrate from X to Y?" "What was the original design decision?"
- Gap: Current state documented, but decision history and rationale missing

**Response actions:**
- **Prioritize content creation:** Focus on high-frequency gap topics
- **Template creation:** Standardize troubleshooting sections, environment-specific docs
- **Metadata enrichment:** Tag content with coverage areas to identify gaps systematically

---

## Practical Evaluation Workflow

**Step 1: Build Your Golden Dataset (Week 1)**
- Collect 50-100 real user queries (from tickets, logs, chat)
- SMEs annotate with ground truth (which docs should be retrieved)
- Balance query types (procedural, diagnostic, lookup, comparative)
- Include 10-15 edge cases (version mismatches, ambiguous, missing info)

**Step 2: Baseline Your System (Week 1)**
- Run golden dataset through current system
- Measure: Recall@10, MRR, zero-result rate, latency
- Human evaluation: 20 queries, judge answer quality
- **This is your baseline.** All future changes compare to this.

**Step 3: Continuous Regression Testing (Ongoing)**
- Integrate golden dataset into CI/CD
- Run on every chunking change, content update, dependency upgrade
- Alert if Recall@10 drops >5% or zero-result rate increases >3%

**Step 4: Production Monitoring (Ongoing)**
- Track zero-result rate, low-confidence queries, latency
- Weekly review of failed queries (manual inspection)
- Monthly evaluation: Re-run golden dataset, update with new real queries

**Step 5: Quarterly Deep Dives (Every 3 months)**
- Human evaluation: 50 queries judged by SMEs
- Coverage gap analysis: Cluster failed queries, identify missing content
- Synthetic dataset refresh: Generate new edge cases based on recent content
- A/B test major changes before full rollout

---

## When NOT to Obsess Over Metrics

**Philosophy reminder:** Evaluation is a means to an end (reliable, useful retrieval), not an end itself.

**Avoid these traps:**

**Trap 1: Optimizing for benchmarks instead of user value**
- **Example:** Spending weeks tuning to get Recall@10 from 0.87 to 0.89, but users are happy and no one complained
- **Instead:** Focus engineering time on content gaps, not marginal metric improvements

**Trap 2: Chasing percentages across domains**
- **Example:** "Research paper X achieved 92% recall, why are we only at 85%?"
- **Reality:** Different domains, different content, different user needs. Your 85% might be excellent for your context.
- **Instead:** Track trends (are we improving or degrading?), not absolute comparisons

**Trap 3: Ignoring qualitative feedback**
- **Example:** Metrics look good (Recall@10 = 0.90) but users complain answers are incomplete
- **Reality:** Metrics measure retrieval, not answer quality. Context completeness might be the issue.
- **Instead:** Combine quantitative metrics with user feedback and human evaluation

**Trap 4: Over-fitting to golden dataset**
- **Example:** Tweaking system to perfectly answer your 100 test queries, but degrading on real queries
- **Instead:** Ensure golden dataset represents real diversity; refresh periodically with new queries

---

## Summary: Key Takeaways

1. **Measure what matters:** Recall@K (did we find it?), MRR (how fast?), context completeness (enough info?), answer quality (correct response?).

2. **Validate with multiple methods:**
   - Synthetic datasets: Scalable regression testing
   - Human evaluation: Ground truth for critical decisions
   - A/B testing: Real-world validation
   - Continuous monitoring: Detect degradation over time

3. **Build practical evaluation datasets:**
   - Curate from real usage (tickets, logs, questions)
   - Generate synthetic queries for coverage
   - Include edge cases (versions, ambiguity, missing info, security)

4. **Monitor red flags:**
   - Zero results: Retrieval failure
   - Wrong version: Temporal filtering issues
   - Security leaks: Access control failures
   - Hallucinations: Context fragmentation or LLM issues

5. **Continuous improvement:**
   - Track query patterns over time
   - Detect content gaps systematically
   - Run regression tests on every change
   - Don't optimize metrics for their own sake—focus on user value

**Next Steps:**
- **Module 08 (Implementation Guide):** See concrete evaluation pipeline implementation
- **Module 10 (Decision Trees):** Use debugging flowchart when quality degrades

---

**Reading Time:** ~35 minutes

**You should now be able to:**
- ✓ Design an evaluation framework for your RAG system
- ✓ Build evaluation datasets with real and synthetic queries
- ✓ Identify and investigate quality degradation
- ✓ Implement continuous monitoring without obsessing over benchmarks
