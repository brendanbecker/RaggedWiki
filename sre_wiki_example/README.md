# SRE Wiki Example Scaffold

This tree mirrors the best practices captured in `docs/technique_deep_dive.md`, `docs/wiki_content_strategy.md`, and `docs/rag_implementation_specs.md`. Each folder corresponds to a content type from the decision matrix so that ingestion can apply the right chunking strategy and metadata tags automatically.

```
sre_wiki_example/
├── README.md                 # Start here – explains folders and templates
├── how-to/                   # Reusable procedural guides (“How do I…?”)
├── runbooks/                 # Service-specific operational playbooks
├── process/                  # Org-wide workflows (incident escalation, release approvals)
├── incidents/                # Postmortems + RCA templates
├── event-prep/               # Large-event readiness plans and checklists
├── stakeholders/             # Contact sheets for teams/vendors
├── apps/                     # Service-specific institutional knowledge
│   └── auth-service/
└── assets/                   # Metadata for diagrams (Lucid, etc.)
```

Use these conventions when adding real documents:
- **Layout-Aware Hierarchical** (runbooks, how-to, process, incidents, event-prep): Keep consistent headers (H1 title, H2 sections, H3 steps) so each chunk lands in the 400–900 token window with abstracts of 100–200 tokens.
- **Code-Aware** (files under `apps/<service>/` can link to IaC or scripts stored elsewhere) to preserve complete logical units.
- **Metadata completeness**: Each Markdown file includes frontmatter-esque tables or callouts for `service_name`, `environment`, `severity`, and stakeholder info so the data schema in `docs/rag_implementation_specs.md` can be populated without guesswork.

The sample files below act as templates to dogfood the ingestion stack.
