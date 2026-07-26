# ============================================================
# FILE 4: examples/AGENTS.md
# Location: examples/ folder
# Action: Create new file
# ============================================================

# AGENTS.md — examples/

## Purpose
Reference BOM documents that validate
against aibomstd.schema.json v0.1.
Each example demonstrates a real-world
AI system scenario using fictional data.

## Conventions
- Filenames: kebab-case descriptive
  e.g. customer-support-ai.json
       fraud-detection-service.json
       image-classification-api.json
- Every file must be valid JSON
- Every file must pass schema validation
- Risk IDs format: AIBOM-RXXX sequential
- UUIDs must be valid v4 format
- All company names are fictional
- All hashes are illustrative only

## Current examples
customer-support-ai.json
  Fictional Acme Corp customer support system.
  Components: 2 models + 3 frameworks +
              2 api-clients + 1 dataset = 7 total
  Risk score: high
  Shows: data-leaves-boundary=true
         pii-in-training-data=true
         EU AI Act gaps
         GDPR data egress risk

## Adding new examples
1. Copy customer-support-ai.json as template
2. Change serialNumber UUID
3. Change subject.name and source
4. Update all bom-ref values
5. Validate against schema before committing
