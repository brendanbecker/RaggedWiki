# RaggedWiki Module Implementation Prompts

These prompts are designed to be copy-pasted into separate Claude Code sessions to implement each phase of the modular documentation structure. Each prompt is self-contained and includes instructions to use the Document Parser subagent for research.

---

## Phase 1: Foundation Modules (Week 1-2)

### Prompt for Phase 1

```
I need you to implement Phase 1 of the RaggedWiki modular documentation plan, which creates the foundation modules (00, 01, 02). Read PLANNING.md for the complete specification.

Your task is to create three new module files in docs/:
1. 00-overview.md
2. 01-why-rag-fails.md
3. 02-chunking-strategies.md

Before you begin writing, use the Document Parser subagent to research:
- "What are the main failure modes of naive RAG systems discussed in the Executive Summary and RAG Techniques documents?"
- "What is the rationale for the 400-900 token range for Layout-Aware Hierarchical chunking?"
- "What are the four pillars of content analysis for selecting chunking strategies?"

Guidelines:
- Follow the philosophy in PLANNING.md: focus on WHY techniques work, not benchmark percentages
- Each module should be 30-60 minutes reading time (except 00-overview which is 10-15 min)
- Emphasize trade-offs and decision criteria
- Use real-world SRE examples (runbooks, IaC, logs, incidents)
- NO benchmark numbers like "+X% improvement" - explain concepts instead
- Include "When to use" sections with explicit decision criteria

For module 00-overview.md:
- Define three learning paths (Wiki Architects, RAG Implementers, SRE Documentation Teams)
- Clear learning objectives for the curriculum
- Prerequisites (basic RAG understanding)
- Module navigation guide

For module 01-why-rag-fails.md:
- Cover: context fragmentation, vocabulary mismatch, lost-in-the-middle, duplicates/staleness, chunk boundaries
- Explain WHY each failure mode happens and WHAT goes wrong
- Real-world failure examples from SRE context (anonymized)
- No statistics - focus on mechanisms

For module 02-chunking-strategies.md:
- Four main strategies: Layout-Aware Hierarchical, Code-Aware, Semantic, Fixed-Size Sliding Window
- Decision matrix based on Four Pillars: structure regularity, semantic density, query patterns, update frequency
- Trade-offs for each strategy (not performance claims)
- When to use each strategy with clear criteria
- Examples mapped to SRE content types

Cross-reference the existing docs/technique_deep_dive.md, docs/wiki_content_strategy.md, and docs/rag_implementation_specs.md for content to adapt (not copy verbatim), but rewrite following the new philosophy.

After creating the modules, update PLANNING.md to mark Phase 1 as complete.
```

---

## Phase 2: Core Architecture (Week 3-4)

### Prompt for Phase 2

```
I need you to implement Phase 2 of the RaggedWiki modular documentation plan, which covers core architecture modules (03, 04, 08). Read PLANNING.md for the complete specification.

Your task is to create three new module files in docs/:
1. 03-embedding-fundamentals.md
2. 04-retrieval-architecture.md
3. 08-implementation-guide.md

Before you begin writing, use the Document Parser subagent to research:
- "What are the key differences between dense and sparse vectors in RAG retrieval, and when should each be used?"
- "Explain the concept of hybrid search (BM25 + dense vectors) and why it improves recall over either approach alone"
- "What is the Parent-Child retrieval pattern and how does it balance precision and context?"
- "What are the stages of the 3-stage rocket retrieval architecture?"

Guidelines from PLANNING.md:
- Focus on concepts and trade-offs, NOT benchmarks
- Explain decision criteria for technology choices (not "use X" but "if you need Y, consider X because Z")
- Each module 30-60 minutes reading time
- Emphasize WHEN to use techniques based on requirements

For module 03-embedding-fundamentals.md:
- How embeddings work (vector representations of semantic meaning)
- Dense vs sparse trade-offs (semantic similarity vs exact matching)
- Model selection criteria (domain fit, context length, deployment model, multilingual)
- When to fine-tune (specialized terminology, vocabulary mismatch, domain jargon)
- Matryoshka embeddings concept (variable-length vectors)
- NO model comparison tables or benchmark leaderboards
- Focus on "choose based on your domain characteristics"

For module 04-retrieval-architecture.md:
- Hybrid search rationale (semantic + exact matching coverage)
- Cross-encoder reranking (why bidirectional attention is more accurate but slower)
- Multi-vector approaches (ColBERT concept for token-level precision)
- Parent-child retrieval (search small, return large)
- Architecture patterns: single-stage, two-stage, three-stage, multi-stage with parent-child
- Trade-offs: latency vs accuracy, index complexity vs recall quality
- When to skip complexity (simple domains, high-throughput requirements)

For module 08-implementation-guide.md:
- Schema design with justifications (dual abstract/full storage, metadata requirements)
- Pipeline stages (ingestion → chunking → embedding → indexing → retrieval → post-processing)
- Technology choices with DECISION CRITERIA not mandates:
  - Vector databases: "If you need X, consider Y because Z"
  - Embedding models: Selection framework
  - Chunking tools: When to use which
- Example architecture with data flow diagrams (use Mermaid)
- Configuration examples (no production secrets)

Use the Document Parser to extract relevant schema examples and pipeline patterns from the research documents, then adapt them to follow our philosophy (trade-offs and decisions, not prescriptive).

After creating the modules, update PLANNING.md to mark Phase 2 as complete.
```

---

## Phase 3: Advanced & Operational (Week 5-6)

### Prompt for Phase 3

```
I need you to implement Phase 3 of the RaggedWiki modular documentation plan, which covers advanced patterns and operational concerns (05, 06, 09). Read PLANNING.md for the complete specification.

Your task is to create three new module files in docs/:
1. 05-advanced-patterns.md
2. 06-production-deployment.md
3. 09-sre-specific-considerations.md

Before you begin writing, use the Document Parser subagent to research:
- "What is Self-RAG (Self-Reflective Retrieval-Augmented Generation) and when is it useful?"
- "Explain multi-hop retrieval and query transformation techniques like HyDE"
- "What are the key production deployment challenges for RAG systems at scale?"
- "How should Infrastructure-as-Code (Terraform, Kubernetes YAML) be chunked and why?"
- "What is the Summary-Index pattern for handling stack traces and high-entropy data?"

Guidelines from PLANNING.md:
- Focus on WHEN complexity is justified, not that advanced = better
- Operational realities over theoretical perfection
- SRE-specific patterns with real-world context
- Trade-offs for every technique (latency, cost, maintenance burden)

For module 05-advanced-patterns.md:
- Self-RAG: LLM identifies missing info and re-retrieves
  - When useful: complex queries, incomplete initial retrieval common
  - Trade-offs: latency (multiple cycles), cost, complexity
- Multi-hop reasoning: breaking complex queries into sub-questions
  - When useful: synthesis across documents ("compare A and B")
  - Trade-offs: query planning complexity, multiple retrieval rounds
- Query transformation: HyDE, multi-query expansion, vocabulary alignment
  - When useful: vocabulary mismatch, ambiguous queries
  - Trade-offs: additional LLM calls, result merging
- Neighbor chunk expansion: retrieve adjacent chunks
  - When useful: procedures spanning chunks, context dependencies
  - Trade-offs: more tokens consumed, deduplication needed
- Decision framework: "When is complexity justified?"
  - Query complexity, acceptable latency, failure rate, operational maturity

For module 06-production-deployment.md:
- Incremental indexing (why re-indexing everything is wasteful)
- Deduplication: exact, near-exact, conflicting versions (prevents context pollution)
- Version control: handling document evolution, temporal queries
- Scaling patterns: sharding, hierarchical indexing, ANN tuning
- Cost considerations: where costs come from, optimization levers (NOT specific dollar amounts)
- Content freshness: TTL policies, update propagation, staleness detection
- Monitoring and observability: what to track, red flags, debugging approaches

For module 09-sre-specific-considerations.md:
- Infrastructure as Code (Terraform/YAML):
  - Problem: syntax fragmentation
  - Solution: AST-based splitting, environment metadata
- System logs:
  - Problem: no structure, high volume, temporal ordering
  - Solution: sliding window, summary-index pattern
- Stack traces:
  - Problem: high entropy, non-linguistic
  - Solution: summary-index (exception type + top frames)
- Runbooks and playbooks:
  - Problem: prerequisites and steps must stay together
  - Solution: hierarchical chunking, parent-child
- Post-mortems:
  - Problem: narrative flow, audit requirements
  - Solution: layout-aware to preserve structure
- Operational patterns: freshness, access control, multi-tenant, time-aware retrieval

Use the Document Parser to extract specific patterns and examples from the RAG Techniques document, especially the SRE-specific sections and the Summary-Index pattern for stack traces.

After creating the modules, update PLANNING.md to mark Phase 3 as complete.
```

---

## Phase 4: Validation & Tools (Week 7-8)

### Prompt for Phase 4

```
I need you to implement Phase 4 of the RaggedWiki modular documentation plan, which covers evaluation and decision tools (07, 10). Read PLANNING.md for the complete specification.

Your task is to create two new module files in docs/:
1. 07-evaluation-approach.md
2. 10-decision-trees.md

Before you begin writing, use the Document Parser subagent to research:
- "What metrics should be used to evaluate RAG retrieval quality beyond simple accuracy?"
- "How can synthetic datasets be generated for evaluating RAG systems?"
- "What are the key monitoring signals for detecting RAG system degradation?"
- "What decision criteria should guide the choice of chunking strategy?"

Guidelines from PLANNING.md:
- Focus on HOW to validate, not "achieving X% accuracy"
- Continuous monitoring and degradation detection over one-time benchmarks
- Practical evaluation approaches for real-world systems
- Decision trees as quick reference tools

For module 07-evaluation-approach.md:
- What to measure:
  - Recall@K: Did we find relevant information? (not "achieve 90%")
  - MRR: How early does first relevant result appear?
  - Context completeness: Did we retrieve all necessary pieces?
  - Answer quality: Did LLM produce correct response?
- How to validate:
  - Synthetic datasets (LLM-generated queries): pros/cons, how to create
  - Human evaluation: ground truth but expensive
  - A/B testing: real-world validation, isolation requirements
  - Regression testing: ensuring quality doesn't degrade
- Building evaluation datasets:
  - Curate from tickets, logs, real questions
  - Synthetic generation prompts
  - Edge cases: version mismatches, ambiguous queries, missing info
- Red flags to monitor:
  - Zero results (retrieval failure)
  - Wrong version retrieved (temporal filtering issues)
  - Security leaks (cross-tenant, access control)
  - Hallucinations (unsupported answers)
- Continuous monitoring approach:
  - Detect degradation when content changes
  - Track query patterns over time
  - Identify systematic gaps in coverage

For module 10-decision-trees.md:
Create Mermaid flowcharts for:
1. "Which chunking strategy?" - Based on structure, content type, query patterns
2. "Do I need hybrid search?" - Based on exact match requirements
3. "When to add cross-encoder reranking?" - Based on latency tolerance and query complexity
4. "Is my retrieval quality degrading?" (debugging guide) - Flowchart through common issues
5. "Should I use advanced patterns?" - Based on failure modes and requirements

Each flowchart should:
- Start with observable characteristics or requirements
- Branch on clear yes/no decisions
- End with actionable recommendations
- Include trade-off considerations in decision nodes

Use clear, concise language suitable for quick reference.
Include a brief introduction explaining how to use the decision trees.

Use the Document Parser to extract decision criteria and trade-offs from the research documents to inform the flowchart logic.

After creating the modules, update PLANNING.md to mark Phase 4 as complete and the entire curriculum as finished.
```

---

## Final Integration Prompt

### Prompt for Final Integration

```
Now that all four phases of the RaggedWiki modular documentation are complete, I need you to:

1. Create a master README.md in docs/ that:
   - Links to all 11 modules in order
   - Provides navigation for the three learning paths (Wiki Architects, RAG Implementers, SRE Teams)
   - Includes a quick-start guide ("Start here if you...")
   - References the old docs in docs/archive/ for those who need them

2. Move the old documentation:
   - Create docs/archive/ directory
   - Move technique_deep_dive.md, wiki_content_strategy.md, rag_implementation_specs.md to archive
   - Add DEPRECATED.md in archive explaining the migration and linking to new modules

3. Update the root CLAUDE.md:
   - Point to docs/README.md for the new structure
   - Keep the SRE-specific guidance
   - Add note about the modular curriculum

4. Create a PROGRESS.md document that:
   - Shows completion status of all phases
   - Links to each module
   - Tracks any remaining TODOs or enhancements
   - Provides feedback mechanism for improvements

5. Quality check:
   - Verify all cross-references between modules work
   - Ensure consistent terminology across modules
   - Check that Mermaid diagrams render correctly
   - Validate that no benchmark percentages slipped through
   - Confirm each module has clear learning objectives

Use the Document Parser if you need to verify any concepts or cross-references against the source research documents.

After completion, provide a summary of:
- All files created
- All files moved/archived
- Any issues encountered
- Suggestions for future maintenance
```

---

## Notes on Using These Prompts

### Context Management
Each phase prompt is designed to be self-contained, but you should:
1. Always have PLANNING.md available in the session
2. The Document Parser subagent can access the full research documents
3. Each phase builds on previous phases, so complete them in order

### Document Parser Usage Pattern
The prompts instruct the agent to:
1. First query the Document Parser for specific concepts
2. Use that research to inform writing
3. Focus on extracting WHY/WHEN/TRADE-OFFS, not performance numbers
4. Adapt examples to SRE context

### Quality Checks Between Phases
After each phase, you should:
- Read through the generated modules
- Check adherence to philosophy (no benchmark percentages)
- Verify 30-60 minute reading time
- Ensure decision frameworks are present
- Test Mermaid diagrams render correctly

### Customization
Feel free to add to any prompt:
- Specific examples from your environment
- Additional SRE content types to cover
- Domain-specific requirements
- Organizational terminology preferences

### Iteration
These are starting prompts. You may need to:
- Ask follow-up questions to refine output
- Request expansions on specific sections
- Adjust tone or detail level
- Add more real-world examples

The Document Parser is your research assistant - use it liberally to ensure accuracy while maintaining our philosophy of teaching concepts over benchmarks.
