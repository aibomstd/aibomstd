import json
import uuid
from datetime import datetime, timezone
from typing import Optional

SPEC_VERSION = "0.1"
SCHEMA_URL = "https://aibomstd.com/schema/v0.1/aibomstd.schema.json"

CISCO_TO_AIBOMSTD_TYPE = {
    "model": "model",
    "ml_model": "model",
    "model_artifact": "model",
    "llm_endpoint": "api-client",
    "model_endpoint": "api-client",
    "agent": "model",
    "agent_proxy": "model",
    "embedding": "model",
    "dataset": "dataset",
    "knowledge_base": "dataset",
    "feature_store": "dataset",
    "tool": "framework",
    "mcp_server": "framework",
    "mcp_client": "api-client",
    "mcp_gateway": "api-client",
    "vector_store": "framework",
    "retriever": "framework",
    "memory": "framework",
    "prompt": "framework",
    "guardrail": "framework",
    "skill": "framework",
    "observability": "framework",
    "ml_pipeline": "framework",
    "dependency": "framework",
    "other": "framework"
}

EXTERNAL_TYPES = {
    "llm_endpoint",
    "model_endpoint",
    "mcp_client",
    "mcp_gateway"
}


class CiscoConverter:

    def convert(self, cisco_json: dict | str) -> dict:
        if isinstance(cisco_json, str):
            cisco_json = json.loads(cisco_json)

        components = self._extract_components(cisco_json)
        subject = self._extract_subject(cisco_json)
        converted_components = []

        for i, component in enumerate(components):
            converted = self._convert_component(component, i + 1)
            if converted:
                converted_components.append(converted)

        summary = self._build_summary(converted_components)

        return {
            "aibomstd": {
                "specVersion": SPEC_VERSION,
                "schema": SCHEMA_URL,
                "serialNumber": f"urn:uuid:{uuid.uuid4()}",
                "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "tool": {
                    "name": "aibomstd-cisco-converter",
                    "version": "0.1.0",
                    "vendor": "Chola AI"
                },
                "subject": subject,
                "components": converted_components,
                "summary": summary,
                "metadata": {
                    "notes": "Converted from cisco-aibom output using aibomstd CiscoConverter. Review all fields — some data may require manual verification."
                }
            }
        }

    def _extract_components(self, cisco_json: dict) -> list:
        if "components" in cisco_json:
            return cisco_json["components"]
        if "findings" in cisco_json:
            return cisco_json["findings"]
        if "results" in cisco_json:
            return cisco_json["results"]
        if isinstance(cisco_json, list):
            return cisco_json
        return []

    def _extract_subject(self, cisco_json: dict) -> dict:
        subject = {
            "name": "converted-from-cisco-aibom",
            "type": "repository"
        }
        if "metadata" in cisco_json:
            meta = cisco_json["metadata"]
            if "target" in meta:
                subject["name"] = meta["target"]
            if "scan_path" in meta:
                subject["source"] = meta["scan_path"]
                subject["name"] = meta["scan_path"].split("/")[-1]
        if "scan_target" in cisco_json:
            subject["name"] = cisco_json["scan_target"]
            subject["source"] = cisco_json["scan_target"]
        return subject

    def _convert_component(self, component: dict, index: int) -> Optional[dict]:
        cisco_type = component.get("type", "other")
        aibomstd_type = CISCO_TO_AIBOMSTD_TYPE.get(cisco_type, "framework")

        name = (
            component.get("name") or
            component.get("identifier") or
            component.get("model_name") or
            f"unknown-component-{index}"
        )

        bom_ref = f"{aibomstd_type}-{str(index).zfill(3)}"

        identity = {
            "name": name,
            "provider": component.get("provider") or component.get("source") or "unknown",
            "version": component.get("version"),
            "source": self._map_source(component),
            "uri": component.get("uri") or component.get("url") or component.get("model_id")
        }

        identity = {k: v for k, v in identity.items() if v is not None}

        if cisco_type in EXTERNAL_TYPES:
            identity["is-external"] = True

        converted = {
            "bom-ref": bom_ref,
            "type": aibomstd_type,
            "identity": identity,
            "risks": []
        }

        if aibomstd_type == "model":
            provenance = self._build_provenance(component)
            if provenance:
                converted["provenance"] = provenance

        license_info = self._build_license(component)
        if license_info:
            converted["license"] = license_info

        if cisco_type in EXTERNAL_TYPES:
            service = self._build_service(component)
            if service:
                converted["service"] = service
            converted["risks"].append({
                "id": f"AIBOM-R{str(index).zfill(3)}",
                "type": "data-egress",
                "severity": "high",
                "description": f"Component {name} calls external service. Data may leave infrastructure boundary. Verify data residency.",
                "recommendation": "Confirm data residency. Verify DPA with provider. Implement PII scrubbing if needed.",
                "regulation": "GDPR"
            })

        properties = self._build_properties(component, cisco_type)
        if properties:
            converted["properties"] = properties

        return converted

    def _map_source(self, component: dict) -> Optional[str]:
        source = component.get("source", "").lower()
        uri = component.get("uri", "").lower()
        combined = source + uri
        if "huggingface" in combined or "hf.co" in combined:
            return "huggingface"
        if "ollama" in combined:
            return "ollama"
        if "mlflow" in combined:
            return "mlflow"
        if "pypi" in combined:
            return "pypi"
        if "openai" in combined:
            return "pypi"
        if "anthropic" in combined:
            return "pypi"
        return "unknown"

    def _build_provenance(self, component: dict) -> Optional[dict]:
        provenance = {}
        datasets = component.get("training_data") or component.get("datasets") or []
        if datasets:
            provenance["training-datasets"] = [
                {"name": ds if isinstance(ds, str) else ds.get("name", "unknown")}
                for ds in datasets
            ]
        if component.get("base_model"):
            provenance["fine-tuned"] = True
            provenance["base-model"] = {
                "name": component["base_model"]
            }
        return provenance if provenance else None

    def _build_license(self, component: dict) -> Optional[dict]:
        license_id = (
            component.get("license") or
            component.get("license_type") or
            component.get("license_id")
        )
        if not license_id:
            return {"id": "unknown", "risk": "unknown"}
        license_id_lower = str(license_id).lower()
        if any(x in license_id_lower for x in ["apache", "mit", "bsd"]):
            risk = "none"
            osi = True
        elif any(x in license_id_lower for x in ["gpl", "agpl"]):
            risk = "high"
            osi = True
        elif "llama" in license_id_lower or "gemma" in license_id_lower:
            risk = "medium"
            osi = False
        else:
            risk = "unknown"
            osi = False
        return {
            "id": str(license_id),
            "osi-approved": osi,
            "risk": risk
        }

    def _build_service(self, component: dict) -> Optional[dict]:
        service = {}
        endpoint = (
            component.get("endpoint") or
            component.get("api_endpoint") or
            component.get("url")
        )
        if endpoint:
            service["endpoint"] = endpoint
        service["data-leaves-boundary"] = True
        service["data-residency"] = "unknown"
        models = component.get("models_used") or component.get("model_ids") or []
        if models:
            service["models-used"] = models if isinstance(models, list) else [models]
        return service if service else None

    def _build_properties(self, component: dict, cisco_type: str) -> Optional[dict]:
        props = {}
        props["cisco-aibom-type"] = cisco_type
        if component.get("confidence"):
            props["cisco-confidence"] = str(component["confidence"])
        if component.get("task"):
            props["task"] = component["task"]
        if component.get("architecture"):
            props["architecture"] = component["architecture"]
        return props if props else None

    def _build_summary(self, components: list) -> dict:
        by_type = {"model": 0, "dataset": 0, "framework": 0, "api-client": 0}
        risk_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        data_leaves = False
        pii_found = False

        for c in components:
            t = c.get("type")
            if t in by_type:
                by_type[t] += 1
            service = c.get("service", {})
            if service.get("data-leaves-boundary"):
                data_leaves = True
            prov = c.get("provenance", {})
            for ds in prov.get("training-datasets", []):
                if ds.get("sensitivity") == "PII":
                    pii_found = True
            for risk in c.get("risks", []):
                sev = risk.get("severity", "low")
                if sev in risk_counts:
                    risk_counts[sev] += 1

        if risk_counts["critical"] > 0:
            risk_score = "critical"
        elif risk_counts["high"] > 0:
            risk_score = "high"
        elif risk_counts["medium"] > 0:
            risk_score = "medium"
        elif risk_counts["low"] > 0:
            risk_score = "low"
        else:
            risk_score = "none"

        return {
            "total-components": len(components),
            "by-type": by_type,
            "risk-score": risk_score,
            "risk-counts": risk_counts,
            "data-leaves-boundary": data_leaves,
            "pii-in-training-data": pii_found,
            "shadow-ai-detected": False
        }
