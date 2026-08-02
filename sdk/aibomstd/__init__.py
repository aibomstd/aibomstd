from importlib.metadata import version, PackageNotFoundError
from .builder import AiBomBuilder
from .components import (
    ModelComponent,
    DatasetComponent,
    FrameworkComponent,
    ApiClientComponent,
    Identity,
    Provenance,
    License,
    Service,
    RiskFlag,
    TrainingDataset,
    BaseModel,
    Citation,
    Digest
)

try:
    __version__ = version("aibomstd")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "AiBomBuilder",
    "ModelComponent",
    "DatasetComponent",
    "FrameworkComponent",
    "ApiClientComponent",
    "Identity",
    "Provenance",
    "License",
    "Service",
    "RiskFlag",
    "TrainingDataset",
    "BaseModel",
    "Citation",
    "Digest"
]
