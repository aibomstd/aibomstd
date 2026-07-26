import json
from datetime import datetime, timezone
import uuid


CYCLONEDX_VERSION = "1.7"
BOM_FORMAT = "CycloneDX"

AIBOMSTD_TO_CDX_TYPE = {
    "model": "machine-learning-model",
    "dataset": "data",
    "framework": "framework",
    "api-client": "library"
}


def to_cyclonedx(aibomstd_dict: dict) -> dict:
    doc = aibomstd_dict.get("aibomstd", {})
    subject = doc.get("subject", {})
    tool = doc.get("tool", {})
    components = doc.get("components", [])

    cdx = {
        "bomFormat": BOM_FORMAT,
        "specVersion": CYCLONEDX_VERSION,
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tools": [
                {
                    "vendor": tool.get("vendor", "Chola AI"),
                    "name": tool.get("name", "aibomstd"),
                    "version": tool.get("version", "0.1.0")
                }
            ],
            "component": {
                "type": "application",
                "name": subject.get("name", "unknown"),
                "version": subject.get("version", "")
            }
        },
        "components": []
    }

    for component in components:
        cdx_component = _convert_component(component)
        cdx["components"].append(cdx_component)

    return cdx


def _convert_component(component: dict) -> dict:
    aibomstd_type = component.get("type", "model")
    cdx_type = AIBOMSTD_TO_CDX_TYPE.get(aibomstd_type, "library")

    identity = component.get("identity", {})
    license_info = component.get("license", {})
    provenance = component.get("provenance", {})
    service = component.get("service", {})
    properties = component.get("properties", {})
    risks = component.get("risks", [])

    cdx_component = {
        "type": cdx_type,
        "bom-ref": component.get("bom-ref", ""),
        "name": identity.get("name", ""),
        "version": identity.get("version", ""),
        "supplier": {
            "name": identity.get("provider", "unknown")
        } if identity.get("provider") else None
    }

    if identity.get("purl"):
        cdx_component["purl"] = identity["purl"]

    if identity.get("digest"):
        cdx_component["hashes"] = [
            {
                "alg": identity["digest"]["algorithm"].upper(),
                "content": identity["digest"]["value"]
            }
        ]

    if license_info.get("id"):
        cdx_component["licenses"] = [
            {"license": {"id": license_info["id"]}}
        ]

    if aibomstd_type == "api-client":
        cdx_component["isExternal"] = True

    extra_props = []

    if service.get("data-leaves-boundary") is not None:
        extra_props.append({
            "name": "aibomstd:data-leaves-boundary",
            "value": str(service["data-leaves-boundary"]).lower()
        })

    if service.get("data-residency"):
        extra_props.append({
            "name": "aibomstd:data-residency",
            "value": service["data-residency"]
        })

    if service.get("endpoint"):
        extra_props.append({
            "name": "aibomstd:service-endpoint",
            "value": service["endpoint"]
        })

    for key, value in properties.items():
        extra_props.append({
            "name": f"aibomstd:{key}",
            "value": str(value)
        })

    if extra_props:
        cdx_component["properties"] = extra_props

    if aibomstd_type == "model" and provenance:
        datasets = provenance.get("training-datasets", [])
        model_card = {}
        if datasets:
            model_card["modelParameters"] = {
                "datasets": [
                    {
                        "type": "dataset",
                        "name": ds.get("name", ""),
                        "contents": {
                            "url": ds.get("uri", "")
                        }
                    }
                    for ds in datasets
                ]
            }
        if model_card:
            cdx_component["modelCard"] = model_card

    cdx_component = {k: v for k, v in cdx_component.items() if v is not None}

    return cdx_component


def to_cyclonedx_json(aibomstd_dict: dict, indent: int = 2) -> str:
    return json.dumps(to_cyclonedx(aibomstd_dict), indent=indent)
