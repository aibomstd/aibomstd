import pytest
import json
from aibomstd.builder import AiBomBuilder
from aibomstd.components import (
    ModelComponent,
    FrameworkComponent,
    ApiClientComponent,
    DatasetComponent,
    Identity,
    Provenance,
    License,
    Service,
    RiskFlag,
    TrainingDataset
)


def make_model():
    return ModelComponent(
        bom_ref="model-001",
        identity=Identity(
            name="llama-3-8b",
            provider="meta",
            version="3.0",
            source="huggingface",
            purl="pkg:huggingface/meta-llama/Llama-3-8B@3.0"
        ),
        provenance=Provenance(
            training_datasets=[
                TrainingDataset(name="CommonCrawl", verified=True, sensitivity="public")
            ],
            fine_tuned=False,
            trained_by="meta-ai-research"
        ),
        license=License(
            id="llama3",
            osi_approved=False,
            risk="medium",
            commercial_use=True
        ),
        risks=[
            RiskFlag(
                id="AIBOM-R001",
                type="license",
                severity="medium",
                description="Non-OSI license.",
                regulation="internal"
            )
        ]
    )


def make_api_client():
    return ApiClientComponent(
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
            data_residency="US",
            authenticated=True
        ),
        license=License(id="Apache-2.0", osi_approved=True, risk="none"),
        risks=[
            RiskFlag(
                id="AIBOM-R002",
                type="data-egress",
                severity="high",
                description="Data sent to OpenAI.",
                regulation="GDPR"
            )
        ]
    )


def make_framework():
    return FrameworkComponent(
        bom_ref="framework-001",
        identity=Identity(
            name="transformers",
            provider="huggingface",
            version="4.44.2",
            source="pypi",
            purl="pkg:pypi/transformers@4.44.2"
        ),
        license=License(id="Apache-2.0", osi_approved=True, risk="none"),
        risks=[]
    )


class TestAiBomBuilder:

    def test_builder_creates_valid_document(self):
        builder = AiBomBuilder(
            subject_name="test-service",
            subject_type="repository"
        )
        result = builder.to_dict()
        assert "aibomstd" in result
        doc = result["aibomstd"]
        assert doc["specVersion"] == "0.1"
        assert doc["schema"] == "https://aibomstd.com/schema/v0.1/aibomstd.schema.json"
        assert doc["subject"]["name"] == "test-service"
        assert doc["subject"]["type"] == "repository"

    def test_serial_number_is_valid_uuid(self):
        builder = AiBomBuilder(subject_name="test", subject_type="repository")
        result = builder.to_dict()
        sn = result["aibomstd"]["serialNumber"]
        assert sn.startswith("urn:uuid:")
        assert len(sn) == 45

    def test_add_model_component(self):
        builder = AiBomBuilder(subject_name="test", subject_type="repository")
        builder.add_component(make_model())
        result = builder.to_dict()
        components = result["aibomstd"]["components"]
        assert len(components) == 1
        assert components[0]["type"] == "model"
        assert components[0]["bom-ref"] == "model-001"
        assert components[0]["identity"]["name"] == "llama-3-8b"

    def test_add_api_client_component(self):
        builder = AiBomBuilder(subject_name="test", subject_type="repository")
        builder.add_component(make_api_client())
        result = builder.to_dict()
        components = result["aibomstd"]["components"]
        assert components[0]["type"] == "api-client"
        assert components[0]["service"]["data-leaves-boundary"] is True
        assert components[0]["service"]["data-residency"] == "US"

    def test_summary_counts_components_correctly(self):
        builder = AiBomBuilder(subject_name="test", subject_type="repository")
        builder.add_component(make_model())
        builder.add_component(make_api_client())
        builder.add_component(make_framework())
        result = builder.to_dict()
        summary = result["aibomstd"]["summary"]
        assert summary["total-components"] == 3
        assert summary["by-type"]["model"] == 1
        assert summary["by-type"]["api-client"] == 1
        assert summary["by-type"]["framework"] == 1

    def test_summary_detects_data_leaves_boundary(self):
        builder = AiBomBuilder(subject_name="test", subject_type="repository")
        builder.add_component(make_api_client())
        result = builder.to_dict()
        assert result["aibomstd"]["summary"]["data-leaves-boundary"] is True

    def test_summary_no_data_egress_when_no_api_client(self):
        builder = AiBomBuilder(subject_name="test", subject_type="repository")
        builder.add_component(make_model())
        result = builder.to_dict()
        assert result["aibomstd"]["summary"]["data-leaves-boundary"] is False

    def test_summary_detects_pii_in_training(self):
        model = ModelComponent(
            bom_ref="model-pii",
            identity=Identity(name="internal-model", provider="internal"),
            provenance=Provenance(
                training_datasets=[
                    TrainingDataset(name="customer-data", sensitivity="PII")
                ]
            ),
            license=License(id="internal", risk="none")
        )
        builder = AiBomBuilder(subject_name="test", subject_type="repository")
        builder.add_component(model)
        result = builder.to_dict()
        assert result["aibomstd"]["summary"]["pii-in-training-data"] is True

    def test_risk_score_high_when_high_risk_exists(self):
        builder = AiBomBuilder(subject_name="test", subject_type="repository")
        builder.add_component(make_api_client())
        result = builder.to_dict()
        assert result["aibomstd"]["summary"]["risk-score"] == "high"

    def test_risk_score_none_when_no_risks(self):
        builder = AiBomBuilder(subject_name="test", subject_type="repository")
        builder.add_component(make_framework())
        result = builder.to_dict()
        assert result["aibomstd"]["summary"]["risk-score"] == "none"

    def test_to_json_produces_valid_json(self):
        builder = AiBomBuilder(subject_name="test", subject_type="repository")
        builder.add_component(make_model())
        json_str = builder.to_json()
        parsed = json.loads(json_str)
        assert "aibomstd" in parsed

    def test_chaining_add_component(self):
        builder = AiBomBuilder(subject_name="test", subject_type="repository")
        result = (
            builder
            .add_component(make_model())
            .add_component(make_api_client())
            .add_component(make_framework())
            .to_dict()
        )
        assert result["aibomstd"]["summary"]["total-components"] == 3

    def test_empty_components_list(self):
        builder = AiBomBuilder(subject_name="test", subject_type="repository")
        result = builder.to_dict()
        assert result["aibomstd"]["components"] == []
        assert result["aibomstd"]["summary"]["total-components"] == 0
        assert result["aibomstd"]["summary"]["risk-score"] == "none"
