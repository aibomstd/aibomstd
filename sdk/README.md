# aibomstd

**The open standard for AI Bill of Materials.**

Scan any repo and instantly know what AI components are running,
which send data outside your boundary, and what your compliance risk is.

[![CI](https://github.com/aibomstd/aibomstd/actions/workflows/validate-schema.yml/badge.svg)](https://github.com/aibomstd/aibomstd/actions)
[![PyPI](https://img.shields.io/pypi/v/aibomstd)](https://pypi.org/project/aibomstd)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](https://github.com/aibomstd/aibomstd/blob/main/LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/aibomstd)](https://pypi.org/project/aibomstd)

---

## Install

```bash
pip install aibomstd
```

---

## CLI — scan a repo in seconds

```bash
aibomstd scan ./my-repo
```

```
┌─────────────────────┬────────────┬──────────────┬──────────┬────────┐
│ Component           │ Type       │ Provider     │ Boundary │ Risk   │
├─────────────────────┼────────────┼──────────────┼──────────┼────────┤
│ openai              │ api-client │ openai       │ leaves   │ high   │
│ anthropic           │ api-client │ anthropic    │ leaves   │ high   │
│ langchain           │ framework  │ langchain-ai │ internal │ none   │
│ torch               │ framework  │ pytorch      │ internal │ none   │
│ llama-3-8b.gguf     │ model      │ unknown      │ internal │ medium │
│ training.jsonl      │ dataset    │ unknown      │ internal │ medium │
└─────────────────────┴────────────┴──────────────┴──────────┴────────┘

Summary:
  Total components : 6
  Data egress      : YES
  Shadow AI        : YES
  Risk score       : HIGH

Generated: my-repo.aibom.json
```

---

## What it detects

| Component type | Examples |
|---------------|---------|
| `api-client` | openai, anthropic, cohere, mistral, groq |
| `framework` | langchain, llama-index, transformers, ollama |
| `model` | .gguf, .safetensors, .pt, .onnx files |
| `dataset` | .jsonl, .parquet, .arrow files in data/ folders |
| Shadow AI | API keys in .env not declared in dependencies |

Auto-detects `data-leaves-boundary` and `data-residency` for every component.

---

## Other CLI commands

```bash
# Validate a BOM file against the schema
aibomstd validate my-repo.aibom.json

# Check version
aibomstd version
```

---

## SDK — generate BOMs in Python

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

print(bom.to_json())       # aibomstd JSON
bom.to_html()              # self-contained HTML report
bom.to_cyclonedx()         # CycloneDX v1.7 JSON
```

---

## Schema

Every output document references the canonical schema:

```
https://aibomstd.com/schema/v0.1/aibomstd.schema.json
```

---

## License

Apache 2.0 — [https://aibomstd.com](https://aibomstd.com)
