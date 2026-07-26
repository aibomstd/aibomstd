from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid
import json

from .components import (
    ModelComponent,
    DatasetComponent,
    FrameworkComponent,
    ApiClientComponent,
    RiskFlag
)

SCHEMA_URL = "https://aibomstd.com/schema/v0.1/aibomstd.schema.json"
SPEC_VERSION = "0.1"


@dataclass
class AiBomBuilder:
    subject_name: str
    subject_type: str
    subject_version: Optional[str] = None
    subject_source: Optional[str] = None
    tool_name: str = "aibomstd-python"
    tool_version: str = "0.1.0"
    tool_vendor: str = "Chola AI"
    _components: list = field(default_factory=list)

    def add_component(
        self,
        component: ModelComponent | DatasetComponent | FrameworkComponent | ApiClientComponent
    ) -> "AiBomBuilder":
        self._components.append(component)
        return self

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self._build_document(), indent=indent)

    def to_dict(self) -> dict:
        return self._build_document()

    def to_html(self) -> str:
        from .output.html_renderer import to_html
        return to_html(self._build_document())

    def to_cyclonedx(self, indent: int = 2) -> str:
        from .output.cyclonedx import to_cyclonedx_json
        return to_cyclonedx_json(self._build_document(), indent=indent)

    def _build_document(self) -> dict:
        return {
            "aibomstd": {
                "specVersion": SPEC_VERSION,
                "schema": SCHEMA_URL,
                "serialNumber": f"urn:uuid:{uuid.uuid4()}",
                "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "tool": {
                    "name": self.tool_name,
                    "version": self.tool_version,
                    "vendor": self.tool_vendor
                },
                "subject": self._build_subject(),
                "components": [c.to_dict() for c in self._components],
                "summary": self._build_summary()
            }
        }

    def _build_subject(self) -> dict:
        d = {
            "name": self.subject_name,
            "type": self.subject_type
        }
        if self.subject_version is not None:
            d["version"] = self.subject_version
        if self.subject_source is not None:
            d["source"] = self.subject_source
        return d

    def _build_summary(self) -> dict:
        by_type = {
            "model": 0,
            "dataset": 0,
            "framework": 0,
            "api-client": 0
        }
        risk_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }
        license_summary = {
            "osi-approved": 0,
            "restricted": 0,
            "unknown": 0
        }
        data_leaves_boundary = False
        pii_in_training = False
        all_risks = []

        for c in self._components:
            component_dict = c.to_dict()
            component_type = component_dict.get("type")

            if component_type in by_type:
                by_type[component_type] += 1

            if component_type == "api-client":
                service = component_dict.get("service", {})
                if service.get("data-leaves-boundary"):
                    data_leaves_boundary = True

            if component_type == "model":
                provenance = component_dict.get("provenance", {})
                for ds in provenance.get("training-datasets", []):
                    if ds.get("sensitivity") == "PII":
                        pii_in_training = True

            license_info = component_dict.get("license", {})
            if license_info:
                if license_info.get("osi-approved") is True:
                    license_summary["osi-approved"] += 1
                elif license_info.get("risk") in ["medium", "high"]:
                    license_summary["restricted"] += 1
                elif license_info.get("id") == "unknown" or not license_info.get("id"):
                    license_summary["unknown"] += 1

            for risk in component_dict.get("risks", []):
                severity = risk.get("severity", "low")
                if severity in risk_counts:
                    risk_counts[severity] += 1
                all_risks.append(risk)

        risk_score = self._calculate_risk_score(risk_counts)

        return {
            "total-components": len(self._components),
            "by-type": by_type,
            "risk-score": risk_score,
            "risk-counts": risk_counts,
            "license-summary": license_summary,
            "data-leaves-boundary": data_leaves_boundary,
            "pii-in-training-data": pii_in_training,
            "shadow-ai-detected": False
        }

    def _calculate_risk_score(self, risk_counts: dict) -> str:
        if risk_counts["critical"] > 0:
            return "critical"
        if risk_counts["high"] > 0:
            return "high"
        if risk_counts["medium"] > 0:
            return "medium"
        if risk_counts["low"] > 0:
            return "low"
        return "none"
