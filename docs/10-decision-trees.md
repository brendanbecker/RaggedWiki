# Module 10: Decision Trees

**Learning Objective:** Quick reference flowcharts for selecting chunking strategies, retrieval architectures, and debugging quality issues.

**Reading Time:** 15-20 minutes

**Prerequisites:** Familiarity with Modules 01-07

---

## Introduction: How to Use These Decision Trees

These flowcharts are **quick reference tools** to guide common RAG system decisions. They are designed to:

- **Start with observable characteristics** (Does your content have headers? Can you accept 500ms latency?)
- **Branch on clear yes/no decisions** (avoiding subjective judgment calls)
- **End with actionable recommendations** (not "it depends")
- **Include trade-off context** in decision nodes (why this choice matters)

**When to use these:**
- **Planning a new RAG system:** Work through Decision 1 → 2 → 3 sequentially
- **Debugging quality issues:** Jump to Decision 4 (debugging flowchart)
- **Evaluating complexity trade-offs:** Use Decision 5 (advanced patterns)

**When NOT to rely solely on these:**
- Every domain has nuances—use these as starting points, not rigid rules
- For complex systems, you may need hybrid approaches (e.g., different strategies per content type)
- A/B test major decisions rather than trusting flowcharts alone

---

## Decision 1: Which Chunking Strategy Should I Use?

This flowchart applies the **Four Pillars Framework** (Module 02) to select the appropriate chunking strategy based on your content characteristics.

```mermaid
flowchart TD
    Start([Content to Chunk]) --> Q1{Does content have<br/>consistent structure?<br/><small>Headers, sections, or syntax</small>}

    Q1 -->|Yes| Q2{Is it code or<br/>configuration?<br/><small>Syntax-sensitive content</small>}
    Q1 -->|No| Q6{Is it narrative prose<br/>or unstructured?}

    Q2 -->|Yes - Code/IaC| Q3{Which type?}
    Q2 -->|No - Structured docs| Q4{How high is<br/>semantic density?<br/><small>Dependencies between sections</small>}

    Q3 -->|Terraform, K8s YAML,<br/>Scripts| CodeAware[✓ Code-Aware Chunking<br/><small>AST-based splitting</small><br/><br/>Preserves: Syntax validity<br/>Trade-off: Language-specific parsers<br/>Examples: Terraform modules, K8s manifests]
    Q3 -->|Config files<br/><small>JSON, YAML, TOML</small>| Q3b{Are values<br/>inter-dependent?}

    Q3b -->|Yes| CodeAware
    Q3b -->|No| FixedSize[✓ Fixed-Size Sliding Window<br/><small>Or simple key-value extraction</small><br/><br/>Preserves: Sequential context<br/>Trade-off: May split related configs<br/>Examples: Large JSON configs, logs]

    Q4 -->|High - Procedures<br/>require context| LayoutAware[✓ Layout-Aware Hierarchical<br/><small>Split on headers H1/H2/H3</small><br/><br/>Preserves: Complete operational units<br/>Trade-off: Variable chunk sizes<br/>Examples: Runbooks, design docs, API docs]
    Q4 -->|Medium - Somewhat<br/>independent sections| Q5{What are primary<br/>query patterns?}

    Q5 -->|Procedural<br/><small>How do I...?</small>| LayoutAware
    Q5 -->|Conceptual<br/><small>Explain X, Why Y?</small>| Semantic[✓ Semantic Chunking<br/><small>Detect topic boundaries</small><br/><br/>Preserves: Conceptual coherence<br/>Trade-off: Higher compute cost<br/>Examples: Analysis docs, long-form content]

    Q6 -->|Yes - No clear<br/>structure| Semantic
    Q6 -->|No - Sequential<br/>time-series| Q7{Is temporal ordering<br/>critical?}

    Q7 -->|Yes| FixedSize
    Q7 -->|No| Semantic

    style CodeAware fill:#e1f5e1
    style LayoutAware fill:#e1f5e1
    style Semantic fill:#fff3cd
    style FixedSize fill:#f8d7da
```

**Key Decision Points:**

1. **Structure Regularity:** Headers, syntax, schemas → Enables structure-aware approaches
2. **Content Type:** Code requires syntax preservation → Code-Aware mandatory
3. **Semantic Density:** High coupling → Keep complete sections together
4. **Query Patterns:** Procedural queries need complete procedures → Layout-Aware
5. **Temporal Ordering:** Logs, time-series → Fixed-Size Sliding Window

**Multi-Strategy Systems:**

Many wikis contain multiple content types. Consider:
- **Layout-Aware** for 60% of content (runbooks, design docs, post-mortems)
- **Code-Aware** for 30% (Terraform, K8s manifests, scripts)
- **Fixed-Size** for 10% (logs, stack traces, unstructured notes)

Route content to appropriate strategy based on file type, metadata, or content analysis.

---

## Decision 2: Do I Need Hybrid Search?

This flowchart helps determine if you should implement **hybrid retrieval** (dense vector + sparse BM25) or if single-stage dense-only retrieval suffices.

```mermaid
flowchart TD
    Start([Evaluate Search Needs]) --> Q1{Do queries include<br/>exact identifiers?<br/><small>Error codes, configs, UUIDs</small>}

    Q1 -->|Yes - Frequently| Hybrid[✓ Hybrid Search Required<br/><small>Dense vectors + BM25 sparse</small><br/><br/>Why: Exact matching for identifiers<br/>Trade-off: Index complexity, fusion logic<br/>Fusion: Reciprocal Rank Fusion RRF]
    Q1 -->|No - Rarely| Q2{Is content highly<br/>technical with jargon?<br/><small>Domain-specific terminology</small>}

    Q2 -->|Yes| Q3{Can you fine-tune<br/>embedding model on<br/>your domain?}
    Q2 -->|No - General language| Q4{Are queries purely<br/>conceptual/semantic?<br/><small>No keyword requirements</small>}

    Q3 -->|Yes - Have resources| Q3a{Will fine-tuning cover<br/>ALL technical terms?}
    Q3 -->|No - Use off-the-shelf| Hybrid

    Q3a -->|Confident| DenseOnly[✓ Dense-Only May Suffice<br/><small>Fine-tuned model handles jargon</small><br/><br/>Benefit: Simpler architecture<br/>Risk: May still miss rare identifiers<br/>Recommendation: Monitor zero-results]
    Q3a -->|Uncertain| HybridSafe[✓ Hybrid Search Recommended<br/><small>Safety net for edge cases</small><br/><br/>Why: Sparse catches what dense misses<br/>Trade-off: Complexity vs. coverage]

    Q4 -->|Yes| DenseOnly
    Q4 -->|No - Mixed| Q5{What's failure cost<br/>of missing exact match?}

    Q5 -->|High - Operational<br/>or safety critical| Hybrid
    Q5 -->|Low - Informational| DenseOptional[✓ Dense-Only with Monitoring<br/><small>Add hybrid if zero-results spike</small><br/><br/>Start simple: Dense-only<br/>Monitor: Zero-result rate, identifier misses<br/>Upgrade: Add BM25 if issues emerge]

    style Hybrid fill:#e1f5e1
    style HybridSafe fill:#e1f5e1
    style DenseOnly fill:#fff3cd
    style DenseOptional fill:#fff3cd
```

**Key Decision Points:**

1. **Exact Identifier Requirements:** Error codes, K8s annotations, configuration keys require sparse search
2. **Technical Jargon:** Domain-specific vocabulary may not embed well → Hybrid provides safety
3. **Fine-Tuning Capability:** If you can fine-tune embeddings on your domain, dense-only may work
4. **Failure Cost:** High-stakes environments (SRE, medical, legal) should default to hybrid
5. **Monitoring:** Start simple (dense-only), add hybrid if zero-result rate >5-10%

**In Practice:**

For **SRE/technical wikis**, hybrid search is almost always recommended because:
- Queries mix conceptual ("why is X slow?") with exact identifiers ("error 0x80040154")
- Technical terms may not be in general embedding model vocabulary
- Safety-critical context (wrong answer can cause outages)

For **general knowledge bases** (HR policies, onboarding docs), dense-only often suffices.

---

## Decision 3: When Should I Add Cross-Encoder Reranking?

Cross-encoder reranking provides **higher precision** by performing bidirectional attention on query-document pairs, but adds **latency**. This flowchart helps decide when the trade-off is worthwhile.

```mermaid
flowchart TD
    Start([Evaluate Reranking Need]) --> Q1{Can you accept<br/>100-500ms additional<br/>latency per query?}

    Q1 -->|No - Need <100ms| Q1a{Is this high-throughput<br/>API or interactive UI?}
    Q1 -->|Yes - Latency OK| Q2{Are queries complex<br/>and technical?<br/><small>Multi-concept, ambiguous</small>}

    Q1a -->|API - High volume| Skip[✗ Skip Reranking<br/><small>Latency too costly</small><br/><br/>Alternative: Optimize stage 1+2<br/>Consider: Async reranking for logging<br/>Trade-off: Speed over max precision]
    Q1a -->|UI - Interactive| Q1b{Are false positives<br/>very costly?<br/><small>Wrong answer = danger</small>}

    Q1b -->|Yes - Safety critical| RerankerRequired[✓ Cross-Encoder Required<br/><small>Despite latency</small><br/><br/>Why: Precision critical for safety<br/>Mitigation: Cache frequent queries<br/>Alternative: Lightweight reranker model]
    Q1b -->|No| Skip

    Q2 -->|Yes - Complex| Q3{What's current precision?<br/><small>Measure on eval dataset</small>}
    Q2 -->|No - Simple lookups| Q4{Is stage 1+2 retrieval<br/>already high precision?<br/><small>Precision@10 > 0.80</small>}

    Q3 -->|Precision@10 < 0.70| RerankerHigh[✓ Cross-Encoder Recommended<br/><small>High impact expected</small><br/><br/>Why: Complex queries benefit most<br/>Expect: +15-25% precision improvement<br/>Implementation: Rerank top-20 to top-10]
    Q3 -->|Precision@10 > 0.80| Q5{Are false positives<br/>in top results<br/>a major issue?}

    Q4 -->|Yes - Precision good| OptionalReranker[△ Reranking Optional<br/><small>Marginal benefit</small><br/><br/>Current system works well<br/>Reranking may improve slightly<br/>Decision: A/B test to validate]
    Q4 -->|No - Precision poor| Q6{What's causing<br/>low precision?}

    Q5 -->|Yes - Frustrating users| RerankerModerate[✓ Cross-Encoder Recommended<br/><small>Polish top results</small><br/><br/>Use case: Remove near-misses from top-5<br/>Latency: Acceptable for better UX<br/>Monitor: User feedback, click-through]
    Q5 -->|No - Acceptable| OptionalReranker

    Q6 -->|Chunking fragmentation| FixChunking[✗ Fix Chunking First<br/><small>Don't mask problem with reranking</small><br/><br/>Root cause: Chunks incomplete/fragmented<br/>Solution: Improve chunking strategy<br/>Then: Re-evaluate need for reranking]
    Q6 -->|Ranking quality| RerankerHigh
    Q6 -->|Vocabulary mismatch| AddHybrid[✗ Add Hybrid Search First<br/><small>Sparse may solve issue</small><br/><br/>Issue: Dense embeddings miss keywords<br/>Solution: BM25 + Dense hybrid<br/>Then: Re-evaluate reranking]

    style RerankerRequired fill:#e1f5e1
    style RerankerHigh fill:#e1f5e1
    style RerankerModerate fill:#e1f5e1
    style OptionalReranker fill:#fff3cd
    style Skip fill:#f8d7da
    style FixChunking fill:#f8d7da
    style AddHybrid fill:#fff3cd
```

**Key Decision Points:**

1. **Latency Budget:** Reranking adds 100-500ms. Can your application tolerate this?
2. **Query Complexity:** Simple lookups don't benefit much; complex technical queries benefit significantly
3. **Current Precision:** If Precision@10 < 0.70, reranking likely helps. If >0.80, marginal benefit.
4. **Root Cause Analysis:** Don't use reranking to mask chunking or vocabulary problems
5. **Safety Criticality:** High-stakes domains (medical, SRE) may require reranking despite latency cost

**Implementation Recommendations:**

**When Using Reranking:**
- Retrieve top-20 with stage 1+2 (hybrid search)
- Rerank to top-10 with cross-encoder
- Cache frequent queries to amortize latency
- Use lightweight models (MiniLM) for speed-sensitive applications

**When Skipping Reranking:**
- Optimize hybrid retrieval (tune BM25/dense weighting)
- Improve chunking quality (may have bigger impact than reranking)
- Monitor precision; add reranking later if quality degrades

---

## Decision 4: Is My Retrieval Quality Degrading? (Debugging Guide)

Use this flowchart when you notice quality issues: users complaining, increased zero-results, hallucinations, or failing regression tests.

```mermaid
flowchart TD
    Start([Quality Issue Detected]) --> Q1{What symptom<br/>are you observing?}

    Q1 -->|Zero results<br/>increasing| ZeroResults[Check: Zero-Result Rate]
    Q1 -->|Wrong answers<br/>despite retrieval| WrongAnswers[Check: Answer Quality]
    Q1 -->|Correct chunks retrieved<br/>but not in answer| LostMiddle[Check: Lost-in-the-Middle]
    Q1 -->|Stale or outdated<br/>content retrieved| Staleness[Check: Content Freshness]
    Q1 -->|Metrics degraded<br/><small>Recall, Precision dropped</small>| Metrics[Check: Recent Changes]

    ZeroResults --> ZQ1{Remove all metadata<br/>filters and retry.<br/>Results now?}

    ZQ1 -->|Yes - Results appear| FilterIssue[Root Cause: Metadata Filtering Too Strict<br/><br/>Investigation:<br/>- Check tenant_id, access_level filters<br/>- Verify metadata completeness in index<br/>- Review access control logic<br/><br/>Solution:<br/>- Relax overly strict filters<br/>- Fix missing metadata at ingestion]
    ZQ1 -->|No - Still zero| ZQ2{Try sparse search<br/><small>BM25 only</small><br/>Results now?}

    ZQ2 -->|Yes - Sparse works| EmbeddingIssue[Root Cause: Dense Embedding Vocabulary Mismatch<br/><br/>Investigation:<br/>- Extract technical terms from query<br/>- Check if terms are domain-specific jargon<br/>- Test query with different embedding model<br/><br/>Solution:<br/>- Enable hybrid search BM25 + Dense<br/>- Consider fine-tuning embeddings<br/>- Add query expansion for synonyms]
    ZQ2 -->|No - Still zero| IndexCompleteness[Root Cause: Content Not Indexed<br/><br/>Investigation:<br/>- Check if document exists in source<br/>- Verify ingestion pipeline ran recently<br/>- Review ingestion logs for errors<br/>- Confirm index chunk count vs expected<br/><br/>Solution:<br/>- Re-run ingestion pipeline<br/>- Fix pipeline failures<br/>- Verify deduplication not over-aggressive]

    WrongAnswers --> WQ1{Are retrieved chunks<br/>relevant and correct?<br/><small>Check retrieval logs</small>}

    WQ1 -->|Yes - Retrieval OK| LLMIssue[Root Cause: LLM Generation Problem<br/><br/>Investigation:<br/>- Review LLM prompts<br/>- Check if context is complete<br/>- Test with grounding check<br/>- Verify no conflicting info in context<br/><br/>Solution:<br/>- Improve prompts: Cite sources, refuse if unsure<br/>- Add grounding validation<br/>- Improve context assembly dedup]
    WQ1 -->|No - Wrong chunks| WQ2{Are similar-looking<br/>but irrelevant docs<br/>retrieved?}

    WQ2 -->|Yes| RankingIssue[Root Cause: Ranking/Precision Problem<br/><br/>Investigation:<br/>- Check if correct doc appears in top-20<br/>- Review metadata filters effectiveness<br/>- Measure Precision@10<br/><br/>Solution:<br/>- Add cross-encoder reranking<br/>- Tune hybrid search weighting<br/>- Improve metadata filtering]
    WQ2 -->|No - Completely<br/>irrelevant| ChunkingIssue[Root Cause: Chunking Fragmentation<br/><br/>Investigation:<br/>- Check chunk sizes avg tokens<br/>- Review if procedures split mid-step<br/>- Verify complete sections preserved<br/><br/>Solution:<br/>- Switch to layout-aware chunking<br/>- Increase target chunk size<br/>- Implement parent-child retrieval]

    LostMiddle --> LMQ1{How many chunks<br/>are you passing<br/>to LLM?}

    LMQ1 -->|>10 chunks| ContextOverload[Root Cause: Too Much Context Lost-in-Middle<br/><br/>Investigation:<br/>- Test with fewer chunks 5-7<br/>- Check if relevant info is in middle positions<br/>- Review LLM context window limits<br/><br/>Solution:<br/>- Reduce to top-5 or top-7 chunks<br/>- Add cross-encoder reranking refine top<br/>- Use parent-child retrieve small, expand<br/>- Summarize less-relevant chunks]
    LMQ1 -->|<10 chunks| LMQ2{Are chunks properly<br/>ordered and deduplicated?}

    LMQ2 -->|No - Duplicates<br/>or disorder| AssemblyIssue[Root Cause: Context Assembly Problem<br/><br/>Investigation:<br/>- Check deduplication logic<br/>- Review chunk ordering by relevance<br/>- Verify breadcrumb metadata<br/><br/>Solution:<br/>- Implement/fix deduplication<br/>- Sort by relevance score<br/>- Add section packing merge adjacent]
    LMQ2 -->|Yes - Clean context| PromptIssue[Root Cause: Prompt Engineering Issue<br/><br/>Investigation:<br/>- Test with explicit instruction to use all context<br/>- Check if LLM has attention bias<br/>- Try different prompt structures<br/><br/>Solution:<br/>- Restructure prompt put key info first<br/>- Explicitly reference all chunks<br/>- Consider summarization pre-processing]

    Staleness --> SQ1{Check metadata:<br/>Are old versions<br/>marked deprecated?}

    SQ1 -->|No - Missing flags| MetadataIssue[Root Cause: Version Metadata Missing<br/><br/>Investigation:<br/>- Check version, deprecated fields in schema<br/>- Review ingestion metadata attachment<br/>- Verify update pipeline propagates changes<br/><br/>Solution:<br/>- Add version and deprecated metadata<br/>- Filter deprecated=true at search time<br/>- Implement content review workflow]
    SQ1 -->|Yes - Properly flagged| SQ2{Are deprecated docs<br/>filtered at search?}

    SQ2 -->|No - Not filtering| FilterMissing[Root Cause: Temporal Filtering Not Enabled<br/><br/>Investigation:<br/>- Review search query construction<br/>- Check metadata filter application<br/>- Verify filter syntax<br/><br/>Solution:<br/>- Add filter: deprecated != true<br/>- Boost recent content: recency multiplier<br/>- Default to current version]
    SQ2 -->|Yes - Filtering works| RankingBias[Root Cause: Old Content Ranks Higher<br/><br/>Investigation:<br/>- Compare embedding similarity scores<br/>- Check if old doc more detailed better<br/>- Review query transformation effects<br/><br/>Solution:<br/>- Apply recency boost to scores<br/>- Improve current docs add detail<br/>- Consider temporal decay function]

    Metrics --> MQ1{What changed recently?}

    MQ1 -->|Chunking logic<br/>updated| ChunkingChange[Root Cause: Chunking Strategy Changed<br/><br/>Investigation:<br/>- Compare chunk size distribution before/after<br/>- Sample chunks: are they fragmented?<br/>- Review what logic changed<br/><br/>Solution:<br/>- Revert if degraded significantly<br/>- Re-tune chunk size parameters<br/>- Re-run evaluation dataset<br/>- Consider gradual rollout]
    MQ1 -->|Embedding model<br/>updated| EmbeddingChange[Root Cause: Embedding Model Changed Without Re-Index<br/><br/>Investigation:<br/>- Verify index was re-embedded<br/>- Check model compatibility old vs new<br/>- Test queries with new model<br/><br/>Solution:<br/>- Re-embed entire corpus with new model<br/>- Do NOT mix embeddings from different models<br/>- A/B test before full migration]
    MQ1 -->|Content added/changed| ContentDrift[Root Cause: New Content Vocabulary Drift<br/><br/>Investigation:<br/>- Check if new content uses different terminology<br/>- Measure query success on old vs new content<br/>- Review content quality consistency<br/><br/>Solution:<br/>- Standardize terminology in new content<br/>- Update query transformation synonyms<br/>- Consider fine-tuning if drift significant<br/>- Content style guide enforcement]
    MQ1 -->|Index grew significantly| ScalingIssue[Root Cause: Index Size Growth Affects Quality<br/><br/>Investigation:<br/>- Check chunk count growth rate<br/>- Measure ANN recall parameters effect<br/>- Review duplicate ingestion<br/><br/>Solution:<br/>- Tune ANN parameters HNSW ef_search<br/>- Increase retrieval K compensate<br/>- Implement hierarchical indexing<br/>- Review deduplication effectiveness]

    style FilterIssue fill:#fff3cd
    style EmbeddingIssue fill:#f8d7da
    style IndexCompleteness fill:#f8d7da
    style LLMIssue fill:#fff3cd
    style RankingIssue fill:#fff3cd
    style ChunkingIssue fill:#f8d7da
    style ContextOverload fill:#fff3cd
    style AssemblyIssue fill:#fff3cd
    style PromptIssue fill:#fff3cd
    style MetadataIssue fill:#f8d7da
    style FilterMissing fill:#fff3cd
    style RankingBias fill:#fff3cd
    style ChunkingChange fill:#f8d7da
    style EmbeddingChange fill:#f8d7da
    style ContentDrift fill:#fff3cd
    style ScalingIssue fill:#fff3cd
```

**Common Root Causes Summary:**

| Symptom | Most Likely Cause | First Action |
|---------|-------------------|--------------|
| **Zero results** | Vocabulary mismatch, content not indexed | Try sparse search; check index completeness |
| **Wrong answers** | LLM hallucination, chunking fragmentation | Check if retrieved chunks are correct |
| **Lost-in-middle** | Too many chunks, poor ordering | Reduce to top-5, add reranking |
| **Stale content** | Missing version metadata, no temporal filtering | Add `deprecated` flags, filter at search |
| **Metrics degraded** | Recent code/content change | Review recent changes, compare before/after |

---

## Decision 5: Should I Use Advanced Patterns?

Advanced patterns (Self-RAG, multi-hop, query transformation) add **complexity**. This flowchart helps determine when the benefits justify the costs.

```mermaid
flowchart TD
    Start([Evaluate Advanced Patterns]) --> Q0{Is basic retrieval<br/>failing on important<br/>queries?<br/><small>Measured, not assumed</small>}

    Q0 -->|No - Basic works| StickSimple[✗ Stick with Basic Approach<br/><small>Don't add unnecessary complexity</small><br/><br/>Why: Simpler is better if it works<br/>Action: Monitor quality, iterate on basics<br/>Re-evaluate: If quality degrades]
    Q0 -->|Yes - Clear failures| Q1{What's the primary<br/>failure mode?}

    Q1 -->|Initial retrieval incomplete<br/>Missing information| Q2{Do queries require<br/>iterative refinement?<br/><small>Follow-up questions emerge</small>}
    Q1 -->|Need to reason across<br/>multiple documents| Q3{Are queries inherently<br/>multi-document?<br/><small>Compare, synthesize, aggregate</small>}
    Q1 -->|Vocabulary mismatch<br/>Zero results common| Q4{Is it technical jargon<br/>or conceptual gap?}
    Q1 -->|Chunk boundaries lose<br/>context dependencies| Q5{Are procedures/concepts<br/>split across chunks?}

    Q2 -->|Yes - Complex queries| SelfRAG[✓ Self-RAG Recommended<br/><small>LLM detects gaps, re-retrieves</small><br/><br/>Use case: Exploratory queries<br/>Trade-off: Multiple retrieval cycles, latency<br/>Implementation: Reflection prompts, iterative<br/><br/>Example: Why is service slow?<br/>Initial: Service docs<br/>Reflection: Missing metrics<br/>Re-retrieve: Performance data]
    Q2 -->|No - Single-shot OK| Q2b{Can you pre-identify<br/>missing info patterns?}

    Q2b -->|Yes| QueryExpansion[✓ Query Expansion Pre-emptive<br/><small>Add known synonyms/related terms</small><br/><br/>Simpler than Self-RAG<br/>Trade-off: Requires domain knowledge<br/>Implementation: Synonym mapping, templates]
    Q2b -->|No| SelfRAG

    Q3 -->|Yes - Comparative<br/>or synthesis queries| MultiHop[✓ Multi-Hop Reasoning Recommended<br/><small>Decompose into sub-questions</small><br/><br/>Use case: Compare X vs Y, Aggregate data<br/>Trade-off: Query planning complexity<br/>Implementation: LLM decomposes, retrieves each<br/><br/>Example: Compare auth-service and auth-gateway<br/>Sub-Q1: Retrieve auth-service docs<br/>Sub-Q2: Retrieve auth-gateway docs<br/>Synthesize: Compare both]
    Q3 -->|No - Single doc OK| Q3b{Is failure due to<br/>missing relationships?}

    Q3b -->|Yes| GraphRAG[△ Consider Graph RAG<br/><small>Entity relationships, knowledge graph</small><br/><br/>Use case: Tracing dependencies, impact analysis<br/>Trade-off: High implementation complexity<br/>Alternative: Improve metadata linking]
    Q3b -->|No| StickSimple

    Q4 -->|Technical jargon| Q4a{Have you tried<br/>hybrid search BM25?}
    Q4 -->|Conceptual gap| Q4b{Is query phrasing<br/>very different from<br/>doc language?}

    Q4a -->|No - Dense only| AddHybridFirst[✗ Add Hybrid Search First<br/><small>BM25 handles exact terms</small><br/><br/>Simpler than query transformation<br/>Solves: Technical identifier misses<br/>Then: Re-evaluate if still failing]
    Q4a -->|Yes - Hybrid fails too| HyDE[✓ HyDE Query Transformation<br/><small>Generate hypothetical answer, search</small><br/><br/>Use case: Query-doc vocabulary mismatch<br/>Trade-off: Extra LLM call, complexity<br/>Implementation: LLM generates fake answer, embed<br/><br/>Example Query: How to fix slow queries?<br/>HyDE: Generate fake answer with SQL terms<br/>Search: Matches docs with SQL optimization]

    Q4b -->|Yes - Very different| MultiQuery[✓ Multi-Query Expansion<br/><small>Rephrase query multiple ways</small><br/><br/>Use case: Ambiguous or terse queries<br/>Trade-off: Multiple embeddings, result merging<br/>Implementation: LLM generates 3-5 variants<br/><br/>Example Query: auth down<br/>Variants:<br/>- authentication service outage<br/>- login failures authorization<br/>- auth-service restart procedure]
    Q4b -->|No - Phrasing similar| VocabMapping[✓ Domain Vocabulary Mapping<br/><small>User terms → Technical terms</small><br/><br/>Use case: Known synonym patterns<br/>Trade-off: Maintenance overhead<br/>Implementation: Lookup table, expand query<br/><br/>Example: Users say restart → Docs say rollout]

    Q5 -->|Yes - Fragmentation<br/>is the problem| Q5a{Can you improve<br/>chunking strategy?<br/><small>Fix root cause</small>}
    Q5 -->|No - Boundaries OK| StickSimple

    Q5a -->|Yes - Switch to<br/>layout-aware| FixChunkingFirst[✗ Fix Chunking First<br/><small>Don't mask problem with complexity</small><br/><br/>Root cause: Wrong chunking strategy<br/>Solution: Layout-aware or code-aware<br/>Then: Re-evaluate if still need advanced patterns]
    Q5a -->|No - Can't change<br/>legacy content| ParentChild[✓ Parent-Child Retrieval<br/><small>Search small, return large</small><br/><br/>Use case: Precision vs context trade-off<br/>Trade-off: Index complexity, storage overhead<br/>Implementation: Child chunks link to parents<br/><br/>Example:<br/>Search: Small precise chunks matches better<br/>Return: Full parent section complete context]

    style SelfRAG fill:#fff3cd
    style MultiHop fill:#fff3cd
    style HyDE fill:#fff3cd
    style MultiQuery fill:#fff3cd
    style ParentChild fill:#fff3cd
    style GraphRAG fill:#f8d7da
    style StickSimple fill:#e1f5e1
    style AddHybridFirst fill:#e1f5e1
    style FixChunkingFirst fill:#e1f5e1
    style QueryExpansion fill:#fff3cd
    style VocabMapping fill:#fff3cd
```

**Key Decision Principle:**

**Always ask:** "Can I solve this by improving basics (chunking, hybrid search, reranking) before adding advanced complexity?"

**Pattern Recommendations:**

| Pattern | When to Use | Complexity | Latency Impact |
|---------|-------------|------------|----------------|
| **Self-RAG** | Iterative queries, missing info common | Medium | High (multiple retrieval rounds) |
| **Multi-Hop** | Comparative/synthesis queries | Medium | High (multiple sub-queries) |
| **HyDE** | Query-doc vocabulary mismatch | Low | Medium (1 extra LLM call) |
| **Multi-Query** | Ambiguous or terse queries | Low | Medium (multiple embeddings) |
| **Parent-Child** | Chunk boundary fragmentation | Medium | Low (index pre-built) |
| **Graph RAG** | Entity relationships, dependencies | Very High | High (graph traversal) |

**Implementation Order:**

If multiple patterns seem applicable:
1. **Fix basics first:** Chunking, hybrid search, reranking
2. **Add lightweight patterns:** HyDE, multi-query expansion
3. **Add iterative patterns:** Self-RAG, multi-hop (if basics + lightweight still fail)
4. **Consider graph patterns:** Only if relationships are critical and basics fail

---

## Quick Reference Summary

### Choosing Chunking Strategy
1. **Structured docs with headers?** → Layout-Aware Hierarchical
2. **Code or IaC?** → Code-Aware (AST-based)
3. **Unstructured narrative?** → Semantic Chunking
4. **Logs, time-series, no structure?** → Fixed-Size Sliding Window

### Deciding on Hybrid Search
1. **Exact identifiers in queries error codes, configs?** → Hybrid required
2. **Highly technical jargon?** → Hybrid recommended
3. **General language, purely conceptual?** → Dense-only may suffice
4. **When unsure?** → Start dense-only, monitor zero-results, add hybrid if >5-10%

### Adding Cross-Encoder Reranking
1. **Latency budget <100ms?** → Skip unless safety-critical
2. **Precision@10 already >0.80?** → Optional (marginal benefit)
3. **Complex technical queries + Precision@10 <0.70?** → Highly recommended
4. **Low precision from chunking issues?** → Fix chunking first, then re-evaluate

### Debugging Quality Degradation
1. **Zero results?** → Check filters, try sparse-only, verify index completeness
2. **Wrong answers?** → Check if retrieved chunks are correct (retrieval vs. LLM issue)
3. **Lost-in-middle?** → Reduce context to top-5, add reranking
4. **Stale content?** → Add version metadata, filter `deprecated=true`
5. **Metrics dropped?** → Review recent changes (code, content, model updates)

### Considering Advanced Patterns
1. **Basic retrieval works?** → Stick with simple approach
2. **Missing info common?** → Self-RAG (iterative retrieval)
3. **Multi-doc synthesis needed?** → Multi-Hop reasoning
4. **Vocabulary mismatch?** → Try hybrid first, then HyDE/multi-query
5. **Chunk boundaries lose context?** → Fix chunking first, then parent-child if needed

---

## Summary: Using These Decision Trees Effectively

**Best Practices:**

1. **Start Simple:** Work through Decision 1 → 2 → 3 in order. Don't jump to advanced patterns (Decision 5) without establishing basics.

2. **Measure Before Deciding:** Decision trees reference metrics (Precision@10, zero-result rate). **Measure your system** before making choices.

3. **Fix Root Causes:** If debugging (Decision 4) points to chunking or filtering issues, **fix those first** rather than adding complexity.

4. **Iterate:** Implement one decision, measure impact, then proceed. Don't implement all recommendations simultaneously.

5. **Context Matters:** These are guidelines, not rigid rules. Your domain may have unique characteristics.

**Anti-Patterns to Avoid:**

- ❌ Adding cross-encoder reranking without measuring current precision
- ❌ Implementing Self-RAG when basic retrieval hasn't been evaluated
- ❌ Using semantic chunking for structured content with clear headers
- ❌ Skipping hybrid search in technical domains with exact identifiers
- ❌ Deploying advanced patterns without A/B testing against simpler approaches

**Next Steps:**

- **Before implementation:** Use Decisions 1-3 to plan your architecture
- **During operation:** Use Decision 4 to debug quality issues
- **When evaluating complexity:** Use Decision 5 to justify advanced patterns

Return to **Module 02** for detailed chunking trade-offs, **Module 04** for retrieval architecture details, and **Module 07** for evaluation frameworks to measure the decisions you make here.

---

**Reading Time:** ~18 minutes

**You should now be able to:**
- ✓ Select appropriate chunking strategies for your content
- ✓ Decide when hybrid search and reranking are justified
- ✓ Debug retrieval quality issues systematically
- ✓ Evaluate when advanced patterns are worth the complexity
