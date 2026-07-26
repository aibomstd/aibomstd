# ============================================================
# FILE 3: AGENTS.md
# Location: root of repo
# Action: Create new file
# ============================================================

# AGENTS.md — aibomstd Root

## Project overview
aibomstd is an open standard, SDK, and CLI
for AI Bill of Materials (AI BOM).
Vendor-neutral. Offline. CI-native.
Apache 2.0 (OSS) and BUSL 1.1 (commercial).
https://aibomstd.com

## Repo structure
```
aibomstd.schema.json  ← JSON Schema spec v0.1
examples/             ← reference BOM documents
GOVERNANCE.md         ← license and governance
CONTRIBUTING.md       ← contribution guidelines
SECURITY.md           ← vulnerability disclosure
CITATION.cff          ← academic citation format
.github/workflows/    ← CI automation
```

## Conventions
- Schema field names: kebab-case always
- All examples must validate against schema
- Commit format: feat: / fix: / chore: / docs:
- Never break existing valid aibomstd.json files
- api-client is a novel type not in CycloneDX v1.7
- data-leaves-boundary is a novel field

## What AI agents should know
- Schema URL is permanent and never changes
- Four component types only in v0.1:
  model, dataset, framework, api-client
- Novel fields vs CycloneDX v1.7:
  api-client type, data-leaves-boundary,
  data-residency, compliance block,
  pii-in-training-data, citations
- All PRs need at least one example update
- No LLM dependency in scanner — ever
- Docker image target: under 50MB
