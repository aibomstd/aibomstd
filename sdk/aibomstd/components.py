from dataclasses import dataclass, field
from typing import Optional
from datetime import date


@dataclass
class Digest:
    algorithm: str
    value: str

    def to_dict(self) -> dict:
        return {"algorithm": self.algorithm, "value": self.value}


@dataclass
class Identity:
    name: str
    provider: Optional[str] = None
    version: Optional[str] = None
    model_id: Optional[str] = None
    source: Optional[str] = None
    purl: Optional[str] = None
    uri: Optional[str] = None
    is_external: Optional[bool] = None
    digest: Optional[Digest] = None

    def to_dict(self) -> dict:
        d = {"name": self.name}
        if self.provider: d["provider"] = self.provider
        if self.version: d["version"] = self.version
        if self.model_id: d["model-id"] = self.model_id
        if self.source: d["source"] = self.source
        if self.purl: d["purl"] = self.purl
        if self.uri: d["uri"] = self.uri
        if self.is_external is not None: d["is-external"] = self.is_external
        if self.digest: d["digest"] = self.digest.to_dict()
        return d


@dataclass
class Citation:
    title: str
    url: Optional[str] = None
    type: Optional[str] = None
    year: Optional[int] = None

    def to_dict(self) -> dict:
        d = {"title": self.title}
        if self.url: d["url"] = self.url
        if self.type: d["type"] = self.type
        if self.year: d["year"] = self.year
        return d


@dataclass
class TrainingDataset:
    name: str
    uri: Optional[str] = None
    verified: Optional[bool] = None
    sensitivity: Optional[str] = None

    def to_dict(self) -> dict:
        d = {"name": self.name}
        if self.uri: d["uri"] = self.uri
        if self.verified is not None: d["verified"] = self.verified
        if self.sensitivity: d["sensitivity"] = self.sensitivity
        return d


@dataclass
class BaseModel:
    name: str
    version: Optional[str] = None
    provider: Optional[str] = None
    model_id: Optional[str] = None

    def to_dict(self) -> dict:
        d = {"name": self.name}
        if self.version: d["version"] = self.version
        if self.provider: d["provider"] = self.provider
        if self.model_id: d["model-id"] = self.model_id
        return d


@dataclass
class Provenance:
    training_datasets: list = field(default_factory=list)
    fine_tuned: Optional[bool] = None
    base_model: Optional[BaseModel] = None
    trained_by: Optional[str] = None
    trained_on: Optional[str] = None
    citations: list = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {}
        if self.training_datasets:
            d["training-datasets"] = [td.to_dict() for td in self.training_datasets]
        if self.fine_tuned is not None: d["fine-tuned"] = self.fine_tuned
        if self.base_model: d["base-model"] = self.base_model.to_dict()
        if self.trained_by: d["trained-by"] = self.trained_by
        if self.trained_on: d["trained-on"] = self.trained_on
        if self.citations:
            d["citations"] = [c.to_dict() for c in self.citations]
        return d


@dataclass
class License:
    id: Optional[str] = None
    name: Optional[str] = None
    url: Optional[str] = None
    osi_approved: Optional[bool] = None
    risk: Optional[str] = None
    commercial_use: Optional[bool] = None
    conditions: list = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {}
        if self.id: d["id"] = self.id
        if self.name: d["name"] = self.name
        if self.url: d["url"] = self.url
        if self.osi_approved is not None: d["osi-approved"] = self.osi_approved
        if self.risk: d["risk"] = self.risk
        if self.commercial_use is not None: d["commercial-use"] = self.commercial_use
        if self.conditions: d["conditions"] = self.conditions
        return d


@dataclass
class Service:
    name: Optional[str] = None
    endpoint: Optional[str] = None
    models_used: list = field(default_factory=list)
    data_leaves_boundary: Optional[bool] = None
    data_residency: Optional[str] = "unknown"
    data_residency_declared: bool = False
    data_residency_declared_by: Optional[str] = None
    data_residency_declared_on: Optional[str] = None
    data_residency_note: Optional[str] = None
    authenticated: Optional[bool] = None

    def to_dict(self) -> dict:
        d = {}
        if self.name: d["name"] = self.name
        if self.endpoint: d["endpoint"] = self.endpoint
        if self.models_used: d["models-used"] = self.models_used
        if self.data_leaves_boundary is not None:
            d["data-leaves-boundary"] = self.data_leaves_boundary
        d["data-residency"] = self.data_residency or "unknown"
        d["data-residency-declared"] = self.data_residency_declared
        d["data-residency-declared-by"] = self.data_residency_declared_by
        d["data-residency-declared-on"] = self.data_residency_declared_on
        d["data-residency-note"] = self.data_residency_note if not self.data_residency_declared else None
        if self.authenticated is not None: d["authenticated"] = self.authenticated
        return d

    def declare(self, residency: str, declared_by: Optional[str] = None) -> "Service":
        self.data_residency = residency
        self.data_residency_declared = True
        self.data_residency_declared_by = declared_by or "user"
        self.data_residency_declared_on = date.today().isoformat()
        self.data_residency_note = None
        return self


@dataclass
class RiskFlag:
    id: str
    type: str
    severity: str
    description: Optional[str] = None
    recommendation: Optional[str] = None
    regulation: Optional[str] = None

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "type": self.type,
            "severity": self.severity
        }
        if self.description: d["description"] = self.description
        if self.recommendation: d["recommendation"] = self.recommendation
        if self.regulation: d["regulation"] = self.regulation
        return d


@dataclass
class ModelComponent:
    name: str
    version: Optional[str] = None
    provider: Optional[str] = None
    identity: Optional[Identity] = None
    provenance: Optional[Provenance] = None
    license: Optional[License] = None
    service: Optional[Service] = None
    risks: list = field(default_factory=list)
    data_leaves_boundary: bool = False
    data_residency: str = "local"

    def to_dict(self) -> dict:
        identity = self.identity or Identity(
            name=self.name,
            provider=self.provider,
            version=self.version
        )
        d = {
            "bom-ref": f"model-{self.name}",
            "type": "model",
            "identity": identity.to_dict()
        }
        if self.provenance: d["provenance"] = self.provenance.to_dict()
        if self.license: d["license"] = self.license.to_dict()
        if self.service: d["service"] = self.service.to_dict()
        elif self.data_leaves_boundary is not None:
            d["service"] = Service(
                data_leaves_boundary=self.data_leaves_boundary,
                data_residency=self.data_residency,
                data_residency_note="Not declared during scan. Run: aibomstd declare to update." if not False else None
            ).to_dict()
        if self.risks: d["risks"] = [r.to_dict() if hasattr(r, 'to_dict') else r for r in self.risks]
        return d


@dataclass
class DatasetComponent:
    name: str
    version: Optional[str] = None
    provider: Optional[str] = None
    identity: Optional[Identity] = None
    provenance: Optional[Provenance] = None
    license: Optional[License] = None
    risks: list = field(default_factory=list)

    def to_dict(self) -> dict:
        identity = self.identity or Identity(
            name=self.name,
            provider=self.provider,
            version=self.version
        )
        d = {
            "bom-ref": f"dataset-{self.name}",
            "type": "dataset",
            "identity": identity.to_dict()
        }
        if self.provenance: d["provenance"] = self.provenance.to_dict()
        if self.license: d["license"] = self.license.to_dict()
        if self.risks: d["risks"] = [r.to_dict() if hasattr(r, 'to_dict') else r for r in self.risks]
        return d


@dataclass
class FrameworkComponent:
    name: str
    version: Optional[str] = None
    provider: Optional[str] = None
    identity: Optional[Identity] = None
    license: Optional[License] = None
    risks: list = field(default_factory=list)

    def to_dict(self) -> dict:
        identity = self.identity or Identity(
            name=self.name,
            provider=self.provider,
            version=self.version
        )
        d = {
            "bom-ref": f"framework-{self.name}",
            "type": "framework",
            "identity": identity.to_dict()
        }
        if self.license: d["license"] = self.license.to_dict()
        if self.risks: d["risks"] = [r.to_dict() if hasattr(r, 'to_dict') else r for r in self.risks]
        return d


@dataclass
class ApiClientComponent:
    name: str
    version: Optional[str] = None
    provider: Optional[str] = None
    identity: Optional[Identity] = None
    license: Optional[License] = None
    service: Optional[Service] = None
    risks: list = field(default_factory=list)
    data_leaves_boundary: bool = True
    data_residency: str = "unknown"

    def to_dict(self) -> dict:
        identity = self.identity or Identity(
            name=self.name,
            provider=self.provider,
            version=self.version,
            is_external=True
        )
        d = {
            "bom-ref": f"api-client-{self.name}",
            "type": "api-client",
            "identity": identity.to_dict()
        }
        if self.license: d["license"] = self.license.to_dict()
        service = self.service or Service(
            data_leaves_boundary=self.data_leaves_boundary,
            data_residency=self.data_residency,
            data_residency_declared=False,
            data_residency_note="Not declared. Run: aibomstd declare to update."
        )
        d["service"] = service.to_dict()
        if self.risks: d["risks"] = [r.to_dict() if hasattr(r, 'to_dict') else r for r in self.risks]
        return d
