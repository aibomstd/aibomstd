from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Digest:
    algorithm: str
    value: str

    def to_dict(self) -> dict:
        return {
            "algorithm": self.algorithm,
            "value": self.value
        }


@dataclass
class TrainingDataset:
    name: str
    uri: Optional[str] = None
    verified: Optional[bool] = None
    sensitivity: Optional[str] = None

    def to_dict(self) -> dict:
        d = {"name": self.name}
        if self.uri is not None:
            d["uri"] = self.uri
        if self.verified is not None:
            d["verified"] = self.verified
        if self.sensitivity is not None:
            d["sensitivity"] = self.sensitivity
        return d


@dataclass
class BaseModel:
    name: str
    version: Optional[str] = None
    provider: Optional[str] = None
    model_id: Optional[str] = None

    def to_dict(self) -> dict:
        d = {"name": self.name}
        if self.version is not None:
            d["version"] = self.version
        if self.provider is not None:
            d["provider"] = self.provider
        if self.model_id is not None:
            d["model-id"] = self.model_id
        return d


@dataclass
class Citation:
    title: str
    url: Optional[str] = None
    type: Optional[str] = None
    year: Optional[int] = None

    def to_dict(self) -> dict:
        d = {"title": self.title}
        if self.url is not None:
            d["url"] = self.url
        if self.type is not None:
            d["type"] = self.type
        if self.year is not None:
            d["year"] = self.year
        return d


@dataclass
class Provenance:
    training_datasets: list[TrainingDataset] = field(default_factory=list)
    fine_tuned: Optional[bool] = None
    base_model: Optional[BaseModel] = None
    trained_by: Optional[str] = None
    trained_on: Optional[str] = None
    citations: list[Citation] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {}
        if self.training_datasets:
            d["training-datasets"] = [ds.to_dict() for ds in self.training_datasets]
        if self.fine_tuned is not None:
            d["fine-tuned"] = self.fine_tuned
        if self.base_model is not None:
            d["base-model"] = self.base_model.to_dict()
        if self.trained_by is not None:
            d["trained-by"] = self.trained_by
        if self.trained_on is not None:
            d["trained-on"] = self.trained_on
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
    conditions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {}
        if self.id is not None:
            d["id"] = self.id
        if self.name is not None:
            d["name"] = self.name
        if self.url is not None:
            d["url"] = self.url
        if self.osi_approved is not None:
            d["osi-approved"] = self.osi_approved
        if self.risk is not None:
            d["risk"] = self.risk
        if self.commercial_use is not None:
            d["commercial-use"] = self.commercial_use
        if self.conditions:
            d["conditions"] = self.conditions
        return d


@dataclass
class Service:
    name: Optional[str] = None
    endpoint: Optional[str] = None
    models_used: list[str] = field(default_factory=list)
    data_leaves_boundary: Optional[bool] = None
    data_residency: Optional[str] = None
    authenticated: Optional[bool] = None

    def to_dict(self) -> dict:
        d = {}
        if self.name is not None:
            d["name"] = self.name
        if self.endpoint is not None:
            d["endpoint"] = self.endpoint
        if self.models_used:
            d["models-used"] = self.models_used
        if self.data_leaves_boundary is not None:
            d["data-leaves-boundary"] = self.data_leaves_boundary
        if self.data_residency is not None:
            d["data-residency"] = self.data_residency
        if self.authenticated is not None:
            d["authenticated"] = self.authenticated
        return d


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
        if self.description is not None:
            d["description"] = self.description
        if self.recommendation is not None:
            d["recommendation"] = self.recommendation
        if self.regulation is not None:
            d["regulation"] = self.regulation
        return d


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
        if self.provider is not None:
            d["provider"] = self.provider
        if self.version is not None:
            d["version"] = self.version
        if self.model_id is not None:
            d["model-id"] = self.model_id
        if self.source is not None:
            d["source"] = self.source
        if self.purl is not None:
            d["purl"] = self.purl
        if self.uri is not None:
            d["uri"] = self.uri
        if self.is_external is not None:
            d["is-external"] = self.is_external
        if self.digest is not None:
            d["digest"] = self.digest.to_dict()
        return d


@dataclass
class ModelComponent:
    bom_ref: str
    identity: Identity
    provenance: Optional[Provenance] = None
    license: Optional[License] = None
    properties: dict = field(default_factory=dict)
    risks: list[RiskFlag] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {
            "bom-ref": self.bom_ref,
            "type": "model",
            "identity": self.identity.to_dict()
        }
        if self.provenance is not None:
            d["provenance"] = self.provenance.to_dict()
        if self.license is not None:
            d["license"] = self.license.to_dict()
        if self.properties:
            d["properties"] = self.properties
        d["risks"] = [r.to_dict() for r in self.risks]
        return d


@dataclass
class DatasetComponent:
    bom_ref: str
    identity: Identity
    license: Optional[License] = None
    properties: dict = field(default_factory=dict)
    risks: list[RiskFlag] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {
            "bom-ref": self.bom_ref,
            "type": "dataset",
            "identity": self.identity.to_dict()
        }
        if self.license is not None:
            d["license"] = self.license.to_dict()
        if self.properties:
            d["properties"] = self.properties
        d["risks"] = [r.to_dict() for r in self.risks]
        return d


@dataclass
class FrameworkComponent:
    bom_ref: str
    identity: Identity
    license: Optional[License] = None
    risks: list[RiskFlag] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {
            "bom-ref": self.bom_ref,
            "type": "framework",
            "identity": self.identity.to_dict()
        }
        if self.license is not None:
            d["license"] = self.license.to_dict()
        d["risks"] = [r.to_dict() for r in self.risks]
        return d


@dataclass
class ApiClientComponent:
    bom_ref: str
    identity: Identity
    service: Optional[Service] = None
    license: Optional[License] = None
    risks: list[RiskFlag] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {
            "bom-ref": self.bom_ref,
            "type": "api-client",
            "identity": self.identity.to_dict()
        }
        if self.service is not None:
            d["service"] = self.service.to_dict()
        if self.license is not None:
            d["license"] = self.license.to_dict()
        d["risks"] = [r.to_dict() for r in self.risks]
        return d
