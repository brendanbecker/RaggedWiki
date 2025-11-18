# Layout-Aware Hierarchical Strategy Deep Dive

## Why Layout-Aware Chunking Is Non-Negotiable for SRE Knowledge
Naive, fixed-size chunking makes recall losses irreversible because retrieval cannot stitch missing context back together, creating a documented 9% gap between best and worst approaches (`Enterprise RAG Recall Optimization Research.md:24`). The paper also shows that context-aware segmentation, such as agentic or structure-aware chunking, cuts incorrect assumptions by 92% because procedures are not split mid thought (`Enterprise RAG Recall Optimization Research.md:43`). Layout-Aware Hierarchical chunking follows that insight by respecting Markdown headers, breadcrumb order, and parent-child relationships so that every runbook or RCA excerpt keeps prerequisites, commands, and validation steps together (`document-parser/references/chunking_principles.md:18`-`document-parser/references/chunking_principles.md:34`).

## Token Envelope + Dual-Storage = Fewer Hallucinations
### The 400–900 Token Band
The Layout-Aware pipeline aggressively merges sections under 400 tokens and splits anything above 900, producing self-contained, semantically complete units that modern embedding models can encode without dilution (`document-parser/references/chunking_principles.md:5`-`document-parser/references/chunking_principles.md:33`). Keeping SRE procedures inside this window prevents the “small chunk = precision, large chunk = context” whiplash called out in the study (`Enterprise RAG Recall Optimization Research.md:30`-`Enterprise RAG Recall Optimization Research.md:33`). It also means 10–15 retrieved sections comfortably fit in a 32k–64k prompt, leaving headroom for the system prompt and citations.

### Dual Abstract + Full Section Storage
Each hierarchical unit is stored twice:
- **Abstract (100–200 tokens):** high-signal synopsis that titles the failure mode, stack component, and outcome; used for Stage‑1 sparse filters and Stage‑0 rerank previews (`document-parser/references/chunking_principles.md:35`-`document-parser/references/chunking_principles.md:53`).
- **Full Section (400–900 tokens):** the lossless payload containing commands, tables, and guardrails.

Running BM25 on abstracts avoids dragging noisy bodies into the first hop, which directly reduces hallucinations caused by partial matches. When a full section is retrieved, it already carries breadcrumbs (document path, parent section id, severity) so the LLM sees the entire remediation narrative instead of decontextualized fragments, mirroring the Parent-Child retrieval guarantee described in the paper (`Enterprise RAG Recall Optimization Research.md:235`-`Enterprise RAG Recall Optimization Research.md:246`).

## Implementation Blueprint
1. **Structure extraction:** Parse Markdown headers to build the hierarchy, capture breadcrumb strings, and attach `parent_section_id` metadata (`document-parser/references/chunking_principles.md:20`-`document-parser/references/chunking_principles.md:33`).
2. **Token balancing:** Merge undersized siblings and recursively split oversized parents until the 400–900 window is satisfied (`document-parser/references/chunking_principles.md:23`-`document-parser/references/chunking_principles.md:61`).
3. **Dual serialization:** Write the abstract/full-text pair plus metadata (`section_id`, `breadcrumbs`, `severity`, `service_owner`) so that vector and object stores stay in sync.
4. **Parent-Child indexing:** Embed only the “child” slices for high-precision retrieval, but keep pointers back to “parents” so the generator can recover full operational context (`Enterprise RAG Recall Optimization Research.md:235`-`Enterprise RAG Recall Optimization Research.md:244`).
5. **Quality checks:** Track the share of chunks inside the target window and alert whenever any service runbook yields more than 10% <400-token slices, because that signals a formatting issue that could reintroduce the 9% recall regression noted in the research.

## Quality Signals and Observability
- **Recall gap monitor:** Compare hybrid (BM25 + dense) hit rate against dense-only to verify the +12.7–20% recall improvement quoted for Stage‑1 systems (`Enterprise RAG Recall Optimization Research.md:74`-`Enterprise RAG Recall Optimization Research.md:125`).
- **Hallucination audits:** Sample answers where only abstracts were retrieved and confirm that the parent fetch supplied the full remediation steps; mismatches indicate missing linkage metadata.
- **Chunk health dashboard:** Plot chunk count, average tokens, and merge/split operations per ingest to surface documents drifting away from the 400–900 target.

## Mermaid: Ingestion Flow (Layout-Aware Hierarchical)
```mermaid
flowchart LR
    subgraph Ingestion
        A[Runbooks / RCAs / Design Docs] --> B[Header & Layout Parser]
        B --> C[Hierarchy Builder\n(parent_id + breadcrumbs)]
        C --> D{Token Check}
        D -->|<400| E[Merge with siblings]
        D -->|400-900| F[Finalize Section]
        D -->|>900| G[Recursive split on subheaders]
        E --> F
        G --> D
        F --> H[Abstract Generator\n(100-200 tokens)]
        F --> I[Full Section Store\n(400-900 tokens)]
        H --> J[Abstract Embedding Job]
        I --> K[Full Text Embedding Job]
        J --> L[(Vector DB: abstract_embedding)]
        K --> M[(Vector DB: full_text_embedding)]
        F --> N[(Object Store: canonical text\n+ parent_section_id + breadcrumbs)]
    end
    style B fill:#e0f7fa,stroke:#00838f
    style C fill:#e0f7fa,stroke:#00838f
    style D fill:#fff3e0,stroke:#ef6c00
    style F fill:#f1f8e9,stroke:#33691e
    style H fill:#ede7f6,stroke:#5e35b1
    style I fill:#ede7f6,stroke:#5e35b1
    style J fill:#fffde7,stroke:#f9a825
    style K fill:#fffde7,stroke:#f9a825
```

## Mermaid: Three-Stage Retrieval Flow
```mermaid
flowchart LR
    subgraph Query Orchestration
        Q[User Query] --> T0[Stage 0: Query Transforms\n(Multi-Query + Multi-HyDE)]
    end
    subgraph Retrieval
        T0 --> T1[Stage 1: Hybrid Search\nBM25 on abstracts + dense]
        T1 --> T15[Stage 1.5: Multi-Vector / MUVERA\nLate Interaction rerank]
        T15 --> T2[Stage 2: Cross-Encoder rerank\nTop 20 -> Top 5-10]
    end
    subgraph Post Retrieval
        T2 --> PR1[Deduplicate abstract/full pairs]
        PR1 --> PR2[Pack adjacent parents]
        PR2 --> PR3[Attach breadcrumbs + citations]
        PR3 --> Ctx[Context sent to LLM]
    end
    style T1 fill:#ffe0b2,stroke:#ef6c00
    style T15 fill:#e1f5fe,stroke:#0277bd
    style T2 fill:#f3e5f5,stroke:#6a1b9a
    style PR1 fill:#f1f8e9,stroke:#33691e
    style PR2 fill:#f1f8e9,stroke:#33691e
    style PR3 fill:#f1f8e9,stroke:#33691e
```

Layout-Aware Hierarchical chunking is therefore not just a formatting preference—it is the control that keeps each runbook’s causal chain intact, maximizes retrieval recall, and slashes hallucinations by ensuring that what the LLM reads is the same coherent story the on-call engineer wrote.
