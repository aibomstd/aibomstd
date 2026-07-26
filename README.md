# aibomstd

**The open standard for AI Bill of Materials.**

aibomstd defines how to describe, track, and govern the AI components
inside any software product — models, datasets, frameworks, and API
clients — across every team, tool, and compliance regime.

[![Schema CI](https://github.com/aibomstd/aibomstd/actions/workflows/validate-schema.yml/badge.svg)](https://github.com/aibomstd/aibomstd/actions)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/aibomstd)](https://pypi.org/project/aibomstd)

---

## What is aibomstd?

Most software teams today have no clear answer to:

- What AI models are running in our product?
- Which components send data outside our boundary?
- Are we compliant with the EU AI Act?
- What changed in our AI stack since last month?

aibomstd solves this with a lightweight, machine-readable standard —
a JSON schema that any team can adopt, any tool can generate, and
any auditor can read.

---

## Quick start

```bash
pip install aibomstd
```

```python
from aibomstd import AiBomBuilder
from aibomstd.components import ModelComponent, ApiClientComponent

bom = (
    AiBomBuilder(product="my-ai-product", version="1.0.0")
    .add_component(ModelComponent(
        name="llama-3-8b-instruct",
        version="3.0",
        provider="meta",
        data_leaves_boundary=False,
        data_residency="IN"
    ))
    .add_component(ApiClientComponent(
        name="gpt-4o",
        version="2024-05-13",
        provider="openai",
        data_leaves_boundary=True,
        data_residency="US"
    ))
)

print(bom.to_json())
```

---

## Four component types

| Type | What it covers |
|------|---------------|
| `model` | Any ML model — local, fine-tuned, or hosted |
| `dataset` | Training, evaluation, or retrieval datasets |
| `framework` | LangChain, LlamaIndex, Hugging Face, etc |
| `api-client` | External AI APIs — OpenAI, Anthropic, Gemini, etc |

---

## Novel fields vs CycloneDX

aibomstd extends existing SBOM standards with AI-specific fields:

- `data-leaves-boundary` — does data leave your infrastructure?
- `data-residency` — where does data reside? (IN / US / EU / UK)
- `compliance` — EU AI Act, NIST AI RMF, ISO 42001 mapping
- `pii-in-training-data` — boolean flag for privacy audits
- `provenance.citations` — academic paper references

---

## CLI

```bash
# Scan a repo and generate an AI BOM
aibomstd scan ./my-repo

# Validate an existing BOM
aibomstd validate my-product.aibom.json

# Convert from cisco-aibom format
aibomstd convert cisco-output.json

# Export to CycloneDX v1.7
aibomstd export --format cyclonedx my-product.aibom.json
```

---

## CI/CD integration

```yaml
# .github/workflows/aibom.yml
- name: Generate AI BOM
  uses: aibomstd/aibomstd-action@v1
  with:
    output: aibom.json
```

Works with GitHub Actions, GitLab CI, and Azure DevOps.

---

## Schema

The schema lives at `schema/v0.1/aibomstd.schema.json`.

Validate any BOM against it:

```bash
npx ajv validate -s schema/v0.1/aibomstd.schema.json -d my-product.aibom.json
```

---

## License

aibomstd uses a dual license model — the same proven approach used by
HashiCorp, Elastic, and GitLab.

### Open source (Apache 2.0)

The following are free to use, modify, distribute, and build on —
commercially or otherwise — with no restrictions:

| Component | License |
|-----------|---------|
| `schema/` — AI BOM standard | Apache 2.0 |
| `sdk/` — Python SDK | Apache 2.0 |
| `cli/` — CLI scanner | Apache 2.0 |
| `ci-plugins/` — GitHub Actions, GitLab CI, Azure DevOps | Apache 2.0 |

**You can adopt aibomstd as your internal standard, build products on
top of it, integrate it into commercial tools, and contribute back —
all without asking permission.**

### Commercial (BUSL 1.1)

The `cloud/` directory — the hosted policy engine, compliance report
generator, drift detection system, certification platform, and
enrichment database — is licensed under BUSL 1.1.

This means you cannot copy the `cloud/` code and run it as a competing
hosted SaaS. Everything else is fully open.

See [LICENSE-CLOUD](LICENSE-CLOUD) for full terms.

---

## Contributing

Contributions to the schema, SDK, CLI, and CI plugins are welcome.

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to get started.

---

## Links

- Website: https://aibomstd.com
- Schema: https://aibomstd.com/schema/v0.1/aibomstd.schema.json
- PyPI: https://pypi.org/project/aibomstd
- Email: aibomstd@gmail.com
