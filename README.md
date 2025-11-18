# RaggedWiki

This repository demonstrates a full RAG-ready SRE wiki implementation:

- **[`docs/`](docs/)** – reference artifacts explaining the ingestion/retrieval patterns:
  - [`technique_deep_dive.md`](docs/technique_deep_dive.md): Layout-Aware Hierarchical chunking deep dive with mermaid diagrams.
  - [`wiki_content_strategy.md`](docs/wiki_content_strategy.md): Decision matrix mapping SRE content types to chunking strategies.
  - [`rag_implementation_specs.md`](docs/rag_implementation_specs.md): Vector schema + dedupe → pack → cite post-retrieval logic.
  - [`processed/`](docs/processed/): Sample outputs from the Document Parser skill (`structure.json`, `metadata.json`, `section_map.md`, and the original research doc) for dogfooding.
- **[`sre_wiki_example/`](sre_wiki_example/)** – dogfooded wiki scaffold showing best-practice folders (how-to, runbooks, process, incidents, event-prep, stakeholders, assets, app-specific knowledge) with template content that already satisfies the 400–900 token chunking guidance.

## Getting Started
1. Read [`docs/technique_deep_dive.md`](docs/technique_deep_dive.md), [`docs/wiki_content_strategy.md`](docs/wiki_content_strategy.md), and [`docs/rag_implementation_specs.md`](docs/rag_implementation_specs.md) to understand the ingestion strategy, content mapping, and storage schema.
2. Explore [`docs/processed/`](docs/processed/) to see how a large Markdown document is structured/annotated after following those best practices.
3. Use the templates in [`sre_wiki_example/`](sre_wiki_example/) when adding new runbooks, postmortems, process docs, event prep plans, stakeholder sheets, and service-specific knowledge bases so future ingestion work already meets the guidelines.
