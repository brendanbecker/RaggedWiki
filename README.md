# RaggedWiki

This repository demonstrates a full RAG-ready SRE wiki implementation:

- **`docs/`** – reference artifacts explaining the ingestion/retrieval patterns:
  - `technique_deep_dive.md`: Layout-Aware Hierarchical chunking deep dive with mermaid diagrams.
  - `wiki_content_strategy.md`: Decision matrix mapping SRE content types to chunking strategies.
  - `rag_implementation_specs.md`: Vector schema + dedupe → pack → cite post-retrieval logic.
  - `processed/`: Sample outputs from the Document Parser skill (`structure.json`, `metadata.json`, `section_map.md`, and the original research doc) for dogfooding.
- **`document-parser/`** – the Document Parser skill used to chunk/annotate large Markdown files.
- **`sre_wiki_example/`** – dogfooded wiki scaffold showing best-practice folders (how-to, runbooks, process, incidents, event-prep, stakeholders, assets, app-specific knowledge) with template content that already satisfies the 400–900 token chunking guidance.

## Getting Started
1. Parse a new document:
   ```bash
   python3 document-parser/scripts/parse_document_structure.py <path/to/doc.md> \
     --output docs/processed/<doc>_structure.json \
     --map docs/processed/<doc>_section_map.md
   python3 document-parser/scripts/extract_metadata.py <path/to/doc.md> \
     --output docs/processed/<doc>_metadata.json
   ```
2. Review the outputs using the schema in `docs/rag_implementation_specs.md` and ingest them into your vector store.
3. Use files under `sre_wiki_example/` as templates for new runbooks, postmortems, process docs, event prep plans, stakeholder sheets, and service-specific knowledge bases.

## Remote
`origin` → `git@github.com:brendanbecker/RaggedWiki.git`
