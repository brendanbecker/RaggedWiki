# RAG Implementation Specifications for the SRE Wiki Backend

## Purpose
This spec translates the research blueprint into a concrete backend plan for the SRE Wiki so that ingestion, retrieval, and generation all honor the layout-aware, metadata-driven practices that eliminate the 9% recall penalty of naive chunking (`Enterprise RAG Recall Optimization Research.md:24`).

## Vector Storage Schema
Hybrid retrieval and Parent-Child promotion require storing both abstract and full-section vectors with rich metadata so we can pre-filter results by tenant, service, or time (`Enterprise RAG Recall Optimization Research.md:301`-`Enterprise RAG Recall Optimization Research.md:344`). We model each section once with two vector slots instead of two separate collections.

| Field | Type | Description / Notes | Source |
| --- | --- | --- | --- |
| `chunk_id` | UUID | Primary key for this record. | (`Enterprise RAG Recall Optimization Research.md:309`-`Enterprise RAG Recall Optimization Research.md:311`)
| `document_id` | UUID | Groups siblings that belong to the same wiki article. | (`Enterprise RAG Recall Optimization Research.md:309`)
| `section_id` | String | Stable identifier for the Markdown header (e.g., `auth.restart.step2`). | (`document-parser/references/chunking_principles.md:20`-`document-parser/references/chunking_principles.md:33`)
| `chunk_type` | Enum (`abstract`, `full_text`) | Indicates which embedding slots below are populated. | (Dual storage guidance `document-parser/references/chunking_principles.md:35`-`document-parser/references/chunking_principles.md:53`)
| `token_count` | Int | Enforced 400–900 range for full sections. | (`document-parser/references/chunking_principles.md:5`-`document-parser/references/chunking_principles.md:33`)
| `abstract_embedding` | Vector<float, 3072> | 100–200 token abstraction used for Stage‑1 sparse/dense fusion. | (`document-parser/references/chunking_principles.md:35`-`document-parser/references/chunking_principles.md:53`)
| `full_text_embedding` | Vector<float, 3072> | Lossless 400–900 token payload for Stage‑1.5/Stage‑2 reranking. | (Same as above)
| `parent_section_id` | String | Direct pointer for Parent-Child promotion so we can fetch the full “parent” context after a “child” hit. | (`Enterprise RAG Recall Optimization Research.md:235`-`Enterprise RAG Recall Optimization Research.md:244`)
| `breadcrumbs` | Array<String> | Hierarchical path used for UI citation and metadata filters. | (`document-parser/references/chunking_principles.md:57`-`document-parser/references/chunking_principles.md:61`)
| `section_level` | Int | Header depth (H1=1 … H6=6) for weighting. | (Layout-aware hierarchy guidance)
| `section_order` | Int | Maintains original order so we can re-pack adjacent chunks later. | (`Enterprise RAG Recall Optimization Research.md:198`-`Enterprise RAG Recall Optimization Research.md:205`)
| `content_type` | Enum (`runbook`, `postmortem`, `terraform`, `yaml`, `log`, …) | Used for boosted BM25 filters per strategy matrix. | (Matrix in `wiki_content_strategy.md`)
| `source_type` | Enum (`wiki`, `git`, `pagerduty`, `ticket`) | Helps target query rewrites (e.g., treat PagerDuty alerts differently). | (`Enterprise RAG Recall Optimization Research.md:312`)
| `service_name` | String | Name of the owning service to enable metadata pre-filtering. | (Metadata schema requirement `Enterprise RAG Recall Optimization Research.md:307`-`Enterprise RAG Recall Optimization Research.md:320`)
| `environment` | Enum (`prod`, `stage`, `dev`) | Filters context per tenant/environment boundaries. | (Same as above)
| `tenant_id` | String | Mandatory for Pool or Bridge multi-tenant architectures; MUST support pre-filtering to avoid recall failure. | (`Enterprise RAG Recall Optimization Research.md:332`-`Enterprise RAG Recall Optimization Research.md:344`)
| `access_control_list` | Array<String> | Security enforcement (teams, roles). Stored alongside the vector to avoid post-filter recall loss. | (`Enterprise RAG Recall Optimization Research.md:318`)
| `version_hash` | String | Git SHA or doc version so VersionRAG differentials can be computed. | (`Enterprise RAG Recall Optimization Research.md:315`-`Enterprise RAG Recall Optimization Research.md:318`)
| `temporal_start`, `temporal_end` | Datetime | Required for Time-Aware Retrieval filters when queries reference “current” state. | (`Enterprise RAG Recall Optimization Research.md:256`-`Enterprise RAG Recall Optimization Research.md:264`)
| `severity` | Enum (`INFO`, `WARN`, `SEV2`, …) | Allows BM25 to boost critical procedures. | (Metadata emphasis `Enterprise RAG Recall Optimization Research.md:301`-`Enterprise RAG Recall Optimization Research.md:305`)
| `tags` | Array<String> | Free-form keywords; stored redundantly for BM25 filters. | (Same as above)
| `created_at`, `updated_at` | Datetime | Audit trail plus a hook for TTL/index refresh decisions. | (`Enterprise RAG Recall Optimization Research.md:315`-`Enterprise RAG Recall Optimization Research.md:316`)
| `quality_flags` | JSON | Stores ingest metrics (merge_count, split_count, chunk_health_score) for monitoring the 400–900 token SLA. | (Chunk health instrumentation `document-parser/references/chunking_principles.md:23`-`document-parser/references/chunking_principles.md:33`)

### Storage Considerations
- **Index Layout:** Qdrant/Weaviate multi-vector field or Milvus hybrid index so we can store both `abstract_embedding` and `full_text_embedding` per record and choose dynamically per retrieval hop (`Enterprise RAG Recall Optimization Research.md:74`-`Enterprise RAG Recall Optimization Research.md:125`).
- **Pre-filter Support:** Vendor must support filtered ANN queries so `tenant_id`, `service_name`, `environment`, and `access_control_list` reduce the candidate pool *before* vector similarities are computed, preventing the recall failure described in the metadata section (`Enterprise RAG Recall Optimization Research.md:323`-`Enterprise RAG Recall Optimization Research.md:330`).
- **Temporal Indexing:** Keep a secondary B-Tree (or Elasticsearch index) on `temporal_start`/`temporal_end` so Stage‑0 query transforms can add “where updated_at >= now()-30d” filters for freshness (`Enterprise RAG Recall Optimization Research.md:256`-`Enterprise RAG Recall Optimization Research.md:264`).

## Retrieval & Post-Retrieval Pipeline
The online pipeline follows the three-stage loop (Query Transform → Hybrid Search → Cross-Encoder) before entering a deterministic post-processing phase to guarantee clean context for the LLM (`Enterprise RAG Recall Optimization Research.md:94`-`Enterprise RAG Recall Optimization Research.md:125`, `Enterprise RAG Recall Optimization Research.md:198`-`Enterprise RAG Recall Optimization Research.md:229`).

### Stage Summary (for context)
1. **Stage 0 – Query Transforms:** Multi-Query + Multi-HyDE rewrites expand sparse/dense coverage (+11.2% accuracy) before any retrieval happens (`Enterprise RAG Recall Optimization Research.md:94`-`Enterprise RAG Recall Optimization Research.md:100`).
2. **Stage 1 – Hybrid Search:** BM25 over abstracts plus dense over `abstract_embedding`, fused with RRF to hit the +12.7–20% recall uplift (`Enterprise RAG Recall Optimization Research.md:74`-`Enterprise RAG Recall Optimization Research.md:125`).
3. **Stage 1.5 – Multi-Vector Late Interaction:** Optional ColBERT/MUVERA score injection for finer token-level matches when queries are extremely specific (`Enterprise RAG Recall Optimization Research.md:85`-`Enterprise RAG Recall Optimization Research.md:93`).
4. **Stage 2 – Cross-Encoder Rerank:** ms-marco-class models down-select the top 5–10 final sections so the generator receives precision-optimized context (+20–35% accuracy) (`Enterprise RAG Recall Optimization Research.md:102`-`Enterprise RAG Recall Optimization Research.md:116`).

### Post-Retrieval Logic (Dedupe → Pack → Cite)
1. **Deduplicate**
   - **Goal:** Remove redundant versions of the same section (e.g., abstract + full text, or overlapping children) before they hit the prompt.
   - **Algorithm:** Group Stage‑2 results by `section_id`. Keep the highest-scoring `full_text` chunk if present; otherwise keep the abstract. If multiple `tenant_id` or `version_hash` variants exist, prefer the newest `updated_at` that still satisfies the user’s temporal filter to respect Time-Aware retrieval rules (`Enterprise RAG Recall Optimization Research.md:256`-`Enterprise RAG Recall Optimization Research.md:264`).
   - **Rationale:** Prevents “context pollution” where the LLM reads partial duplicates—a root cause of hallucinations identified in the trade-off section (`Enterprise RAG Recall Optimization Research.md:30`-`Enterprise RAG Recall Optimization Research.md:33`).

2. **Pack**
   - **Goal:** Reconstruct contiguous context blocks so that sequential instructions survive the “lost-in-the-middle” problem when inserted into the prompt (`Enterprise RAG Recall Optimization Research.md:198`-`Enterprise RAG Recall Optimization Research.md:229`).
   - **Algorithm:** Sort deduped results by `(document_id, section_order)`. Merge adjacent sections that share the same `parent_section_id` and are within a configurable token budget (e.g., 1,400 tokens). When only a child chunk is retrieved, automatically append its parent chunk’s abstract to satisfy the Parent-Child contract (`Enterprise RAG Recall Optimization Research.md:235`-`Enterprise RAG Recall Optimization Research.md:244`).
   - **Prompt Layout:** Apply the “Front-and-Back” packing order so the most relevant chunks sit at the beginning and end of the context window, maximizing recall in long prompts (`Enterprise RAG Recall Optimization Research.md:198`-`Enterprise RAG Recall Optimization Research.md:205`).

3. **Cite**
   - **Goal:** Attach authoritative breadcrumbs so responders can click back to the canonical wiki section and so the LLM can reference sources explicitly, reducing hallucinations.
   - **Metadata Assembly:** For each packed block, emit `{document_title} › {breadcrumbs.join(" / ")} (v{version_hash}, updated {updated_at})` plus deep-link anchors such as `https://wiki/sre/{document_id}#{section_id}`. Include `tenant_id` when the stack is in Pool/Bridge mode to make cross-tenant leakage impossible (`Enterprise RAG Recall Optimization Research.md:332`-`Enterprise RAG Recall Optimization Research.md:344`).
   - **Security Check:** Before finalizing the context payload, ensure the caller’s access token intersects with `access_control_list`; otherwise replace the chunk with an authorization error stub.

4. **Telemetry Hooks**
   - Emit structured logs capturing the number of chunks per stage, dedupe drops, pack merges, and citations added so we can monitor contextual recall/precision overtime (`Enterprise RAG Recall Optimization Research.md:346`-`Enterprise RAG Recall Optimization Research.md:379`).

With this schema and post-retrieval discipline, the SRE Wiki backend inherits the layout awareness, metadata rigor, and retrieval precision the research paper and chunking guidance demand, ensuring every generated answer cites the correct section while avoiding recall regressions.
