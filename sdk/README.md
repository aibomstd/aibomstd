# aibomstd Python SDK

Python SDK for the aibomstd open standard.
Generate AI Bill of Materials in 10 lines of code.

## Install

```bash
pip install aibomstd
```

## Quick start

```python
from aibomstd import (
    AiBomBuilder,
    ModelComponent,
    ApiClientComponent,
    FrameworkComponent,
    Identity,
    License,
    Service,
    RiskFlag
)

bom = AiBomBuilder(
    subject_name="my-ai-service",
    subject_type="repository",
    subject_version="1.0.0"
)

bom.add_component(
    ModelComponent(
        bom_ref="model-001",
        identity=Identity(
            name="llama-3-8b-instruct",
            provider="meta",
            version="3.0",
            source="huggingface",
            purl="pkg:huggingface/meta-llama/Meta-Llama-3-8B-Instruct@3.0"
        ),
        license=License(id="llama3", osi_approved=False, risk="medium")
    )
)

bom.add_component(
    ApiClientComponent(
        bom_ref="api-client-001",
        identity=Identity(
            name="openai",
            provider="openai",
            version="1.40.0",
            source="pypi",
            purl="pkg:pypi/openai@1.40.0",
            is_external=True
        ),
        service=Service(
            name="OpenAI API",
            endpoint="https://api.openai.com/v1",
            models_used=["gpt-4o"],
            data_leaves_boundary=True,
            data_residency="US"
        ),
        license=License(id="Apache-2.0", osi_approved=True, risk="none"),
        risks=[
            RiskFlag(
                id="AIBOM-R001",
                type="data-egress",
                severity="high",
                description="Data sent to OpenAI. US jurisdiction.",
                regulation="GDPR"
            )
        ]
    )
)

print(bom.to_json())
```

## Output formats

```python
bom.to_json()          # aibomstd JSON
bom.to_html()          # self-contained HTML report
bom.to_cyclonedx()     # CycloneDX v1.7 JSON
```

## Convert from cisco-aibom

```python
from aibomstd.converters.cisco import CiscoConverter
import json

cisco_output = json.load(open("cisco-scan-result.json"))
converter = CiscoConverter()
aibomstd_json = converter.convert(cisco_output)
print(json.dumps(aibomstd_json, indent=2))
```

## Schema

Every output document references:
`https://aibomstd.com/schema/v0.1/aibomstd.schema.json`

## License

Apache 2.0 — https://aibomstd.com
