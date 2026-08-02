"""
aibomstd CLI — AI Bill of Materials scanner and validator.
"""
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

app = typer.Typer(
    name="aibomstd",
    help="AI Bill of Materials — scan, validate, and convert AI components.",
    no_args_is_help=True
)
console = Console()

# ─────────────────────────────────────────────
# AI component knowledge base
# ─────────────────────────────────────────────

API_CLIENTS = {
    "openai":           {"provider": "openai",    "data-residency": "US", "leaves": True},
    "anthropic":        {"provider": "anthropic", "data-residency": "US", "leaves": True},
    "google-generativeai": {"provider": "google", "data-residency": "US", "leaves": True},
    "google-cloud-aiplatform": {"provider": "google", "data-residency": "US", "leaves": True},
    "cohere":           {"provider": "cohere",    "data-residency": "US", "leaves": True},
    "mistralai":        {"provider": "mistral",   "data-residency": "EU", "leaves": True},
    "together":         {"provider": "together",  "data-residency": "US", "leaves": True},
    "groq":             {"provider": "groq",      "data-residency": "US", "leaves": True},
    "replicate":        {"provider": "replicate", "data-residency": "US", "leaves": True},
    "boto3":            {"provider": "aws",       "data-residency": "US", "leaves": True},
    "azure-ai-inference": {"provider": "microsoft", "data-residency": "US", "leaves": True},
}

FRAMEWORKS = {
    "langchain":        {"provider": "langchain-ai"},
    "langchain-core":   {"provider": "langchain-ai"},
    "langchain-community": {"provider": "langchain-ai"},
    "llama-index":      {"provider": "llamaindex"},
    "llama_index":      {"provider": "llamaindex"},
    "haystack-ai":      {"provider": "deepset"},
    "crewai":           {"provider": "crewai"},
    "autogen":          {"provider": "microsoft"},
    "semantic-kernel":  {"provider": "microsoft"},
    "dspy":             {"provider": "stanford-nlp"},
    "instructor":       {"provider": "instructor-ai"},
    "guidance":         {"provider": "microsoft"},
    "outlines":         {"provider": "dottxt-ai"},
    "pydantic-ai":      {"provider": "pydantic"},
}

LOCAL_MODELS = {
    "torch":            {"provider": "pytorch",   "type": "framework"},
    "tensorflow":       {"provider": "google",    "type": "framework"},
    "transformers":     {"provider": "huggingface", "type": "framework"},
    "diffusers":        {"provider": "huggingface", "type": "framework"},
    "sentence-transformers": {"provider": "huggingface", "type": "framework"},
    "huggingface-hub":  {"provider": "huggingface", "type": "framework"},
    "ollama":           {"provider": "ollama",    "type": "framework"},
    "llama-cpp-python": {"provider": "ggerganov", "type": "framework"},
    "ctransformers":    {"provider": "marella",   "type": "framework"},
    "vllm":             {"provider": "vllm-project", "type": "framework"},
    "unsloth":          {"provider": "unslothai", "type": "framework"},
    "axolotl":          {"provider": "axolotl-ai", "type": "framework"},
    "trl":              {"provider": "huggingface", "type": "framework"},
    "peft":             {"provider": "huggingface", "type": "framework"},
}

MODEL_FILE_EXTENSIONS = {
    ".gguf":        "llama.cpp quantized model",
    ".ggml":        "ggml model",
    ".bin":         "binary model weights",
    ".pt":          "PyTorch model",
    ".pth":         "PyTorch checkpoint",
    ".safetensors": "safetensors model",
    ".onnx":        "ONNX model",
    ".pb":          "TensorFlow protobuf",
    ".h5":          "Keras/HDF5 model",
    ".pkl":         "pickle model",
    ".joblib":      "joblib model",
}

DATA_FILE_EXTENSIONS = {
    ".jsonl":   "JSONL dataset",
    ".parquet": "Parquet dataset",
    ".arrow":   "Arrow dataset",
    ".csv":     "CSV dataset",
}

DATA_DIRS = [
    "data", "dataset", "datasets", "training_data",
    "train", "eval", "evaluation", "corpus"
]


# ─────────────────────────────────────────────
# Scanner helpers
# ─────────────────────────────────────────────

def parse_requirements(path: Path) -> dict[str, str]:
    """Parse requirements.txt and return {package: version}."""
    deps = {}
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            # Remove extras like package[extra]
            line = re.sub(r"\[.*?\]", "", line)
            match = re.match(r"^([A-Za-z0-9_\-\.]+)\s*([><=!~^]+.*)?$", line)
            if match:
                name = match.group(1).lower().replace("_", "-")
                version = match.group(2).strip() if match.group(2) else "unknown"
                deps[name] = version
    except Exception:
        pass
    return deps


def parse_pyproject(path: Path) -> dict[str, str]:
    """Parse pyproject.toml dependencies."""
    deps = {}
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        # Find dependencies array
        in_deps = False
        for line in content.splitlines():
            if "dependencies" in line and "[" in line:
                in_deps = True
                continue
            if in_deps:
                if line.strip().startswith("]"):
                    in_deps = False
                    continue
                match = re.search(r'"([A-Za-z0-9_\-\.]+)\s*([><=!~^]+[^"]*)?', line)
                if match:
                    name = match.group(1).lower().replace("_", "-")
                    version = match.group(2).strip() if match.group(2) else "unknown"
                    deps[name] = version
    except Exception:
        pass
    return deps


def parse_package_json(path: Path) -> dict[str, str]:
    """Parse package.json dependencies."""
    deps = {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        for section in ["dependencies", "devDependencies"]:
            for name, version in data.get(section, {}).items():
                deps[name.lower()] = version
    except Exception:
        pass
    return deps


def find_model_files(repo_path: Path) -> list[dict]:
    """Find model files in the repo."""
    models = []
    skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv", ".env"}
    try:
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for fname in files:
                ext = Path(fname).suffix.lower()
                if ext in MODEL_FILE_EXTENSIONS:
                    fpath = Path(root) / fname
                    size_mb = fpath.stat().st_size / (1024 * 1024)
                    if size_mb > 1:  # skip tiny files
                        models.append({
                            "name": fname,
                            "path": str(fpath.relative_to(repo_path)),
                            "format": MODEL_FILE_EXTENSIONS[ext],
                            "size_mb": round(size_mb, 1)
                        })
    except Exception:
        pass
    return models


def find_dataset_files(repo_path: Path) -> list[dict]:
    """Find dataset files in the repo."""
    datasets = []
    skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv"}
    try:
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            root_path = Path(root)
            # Check if in a known data directory
            in_data_dir = any(d in root_path.parts for d in DATA_DIRS)
            for fname in files:
                ext = Path(fname).suffix.lower()
                if ext in DATA_FILE_EXTENSIONS and in_data_dir:
                    fpath = root_path / fname
                    size_mb = fpath.stat().st_size / (1024 * 1024)
                    datasets.append({
                        "name": fname,
                        "path": str(fpath.relative_to(repo_path)),
                        "format": DATA_FILE_EXTENSIONS[ext],
                        "size_mb": round(size_mb, 1)
                    })
    except Exception:
        pass
    return datasets


def find_env_api_keys(repo_path: Path) -> list[str]:
    """Detect API key patterns in .env files."""
    providers = []
    env_files = list(repo_path.glob("**/.env*"))
    patterns = {
        "openai":    r"OPENAI_API_KEY",
        "anthropic": r"ANTHROPIC_API_KEY",
        "google":    r"GOOGLE_API_KEY|GEMINI_API_KEY",
        "cohere":    r"COHERE_API_KEY",
        "mistral":   r"MISTRAL_API_KEY",
        "groq":      r"GROQ_API_KEY",
        "replicate": r"REPLICATE_API_TOKEN",
        "together":  r"TOGETHER_API_KEY",
        "huggingface": r"HUGGINGFACE_TOKEN|HF_TOKEN",
        "aws":       r"AWS_ACCESS_KEY_ID",
    }
    for env_file in env_files[:5]:  # limit to 5 files
        try:
            content = env_file.read_text(encoding="utf-8", errors="ignore")
            for provider, pattern in patterns.items():
                if re.search(pattern, content):
                    if provider not in providers:
                        providers.append(provider)
        except Exception:
            pass
    return providers


def build_aibom(
    repo_name: str,
    repo_path: Path,
    all_deps: dict[str, str],
    model_files: list[dict],
    dataset_files: list[dict],
    env_providers: list[str]
) -> dict:
    """Build the aibomstd JSON document from scan results."""
    import uuid
    from datetime import datetime, timezone

    components = []

    # API clients from deps
    for pkg, version in all_deps.items():
        if pkg in API_CLIENTS:
            info = API_CLIENTS[pkg]
            components.append({
                "type": "api-client",
                "name": pkg,
                "version": version.lstrip(">=^~<! ") or "unknown",
                "provider": info["provider"],
                "service": {
                    "data-leaves-boundary": info["leaves"],
                    "data-residency": info["data-residency"],
                    "endpoint": f"https://api.{info['provider']}.com"
                },
                "license": {"id": "proprietary", "osi-approved": False},
                "risks": [{
                    "id": f"DATA-EGRESS-{info['provider'].upper()}",
                    "severity": "high",
                    "description": f"Data leaves boundary to {info['provider']} ({info['data-residency']})"
                }]
            })

    # Frameworks from deps
    for pkg, version in all_deps.items():
        if pkg in FRAMEWORKS:
            info = FRAMEWORKS[pkg]
            components.append({
                "type": "framework",
                "name": pkg,
                "version": version.lstrip(">=^~<! ") or "unknown",
                "provider": info["provider"],
                "license": {"id": "MIT", "osi-approved": True},
                "risks": []
            })

    # Local model frameworks
    for pkg, version in all_deps.items():
        if pkg in LOCAL_MODELS:
            info = LOCAL_MODELS[pkg]
            components.append({
                "type": info["type"],
                "name": pkg,
                "version": version.lstrip(">=^~<! ") or "unknown",
                "provider": info["provider"],
                "service": {
                    "data-leaves-boundary": False,
                    "data-residency": "local"
                },
                "license": {"id": "Apache-2.0", "osi-approved": True},
                "risks": []
            })

    # API clients detected from .env files not in deps
    for provider in env_providers:
        already = any(
            c.get("provider") == provider
            for c in components
            if c["type"] == "api-client"
        )
        if not already:
            components.append({
                "type": "api-client",
                "name": f"{provider}-api-client",
                "version": "unknown",
                "provider": provider,
                "service": {
                    "data-leaves-boundary": True,
                    "data-residency": "unknown"
                },
                "license": {"id": "proprietary", "osi-approved": False},
                "risks": [{
                    "id": f"DATA-EGRESS-{provider.upper()}-ENV",
                    "severity": "high",
                    "description": f"API key detected in .env — data may leave boundary to {provider}"
                }],
                "notes": "Detected via .env file — not found in package dependencies"
            })

    # Model files
    for mf in model_files:
        components.append({
            "type": "model",
            "name": mf["name"],
            "version": "unknown",
            "provider": "unknown",
            "format": mf["format"],
            "path": mf["path"],
            "size-mb": mf["size_mb"],
            "service": {
                "data-leaves-boundary": False,
                "data-residency": "local"
            },
            "license": {"id": "unknown", "osi-approved": False},
            "risks": [{
                "id": "LICENSE-UNKNOWN",
                "severity": "medium",
                "description": "Model file found — license and provenance unknown"
            }]
        })

    # Dataset files
    for df in dataset_files:
        components.append({
            "type": "dataset",
            "name": df["name"],
            "version": "unknown",
            "provider": "unknown",
            "format": df["format"],
            "path": df["path"],
            "size-mb": df["size_mb"],
            "license": {"id": "unknown", "osi-approved": False},
            "risks": [{
                "id": "DATASET-LICENSE-UNKNOWN",
                "severity": "medium",
                "description": "Dataset file found — license and sensitivity unknown"
            }]
        })

    # Summary
    data_leaves = any(
        c.get("service", {}).get("data-leaves-boundary")
        for c in components
    )
    by_type = {"model": 0, "dataset": 0, "framework": 0, "api-client": 0}
    risk_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for c in components:
        t = c.get("type")
        if t in by_type:
            by_type[t] += 1
        for r in c.get("risks", []):
            sev = r.get("severity", "low")
            if sev in risk_counts:
                risk_counts[sev] += 1

    risk_score = "none"
    for level in ["critical", "high", "medium", "low"]:
        if risk_counts[level] > 0:
            risk_score = level
            break

    return {
        "aibomstd": {
            "specVersion": "0.1",
            "schema": "https://aibomstd.com/schema/v0.1/aibomstd.schema.json",
            "serialNumber": f"urn:uuid:{uuid.uuid4()}",
            "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tool": {
                "name": "aibomstd-cli",
                "version": "0.1.0",
                "vendor": "aibomstd Project"
            },
            "subject": {
                "name": repo_name,
                "type": "application",
                "source": str(repo_path.resolve())
            },
            "components": components,
            "summary": {
                "total-components": len(components),
                "by-type": by_type,
                "risk-score": risk_score,
                "risk-counts": risk_counts,
                "data-leaves-boundary": data_leaves,
                "pii-in-training-data": False,
                "shadow-ai-detected": len(env_providers) > 0
            }
        }
    }


# ─────────────────────────────────────────────
# CLI commands
# ─────────────────────────────────────────────

@app.command()
def scan(
    path: str = typer.Argument(".", help="Path to repository to scan"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress progress output"),
):
    """Scan a repository and generate an AI Bill of Materials."""

    repo_path = Path(path).resolve()
    if not repo_path.exists():
        console.print(f"[red]Error: path '{path}' does not exist.[/red]")
        raise typer.Exit(1)

    if not quiet:
        console.print(Panel.fit(
            "[bold green]aibomstd scan[/bold green]",
            subtitle=str(repo_path)
        ))

    all_deps: dict[str, str] = {}

    # Scan dependency files
    dep_files = {
        "requirements.txt": parse_requirements,
        "requirements-dev.txt": parse_requirements,
        "requirements-prod.txt": parse_requirements,
        "pyproject.toml": parse_pyproject,
        "setup.py": parse_requirements,
        "package.json": parse_package_json,
    }

    found_files = []
    for filename, parser in dep_files.items():
        fpath = repo_path / filename
        if fpath.exists():
            found_files.append(filename)
            deps = parser(fpath)
            all_deps.update(deps)

    if not quiet and found_files:
        console.print(f"[dim]Found dependency files: {', '.join(found_files)}[/dim]")
        console.print(f"[dim]Total packages scanned: {len(all_deps)}[/dim]")

    # Scan for model files
    if not quiet:
        console.print("[dim]Scanning for model files...[/dim]")
    model_files = find_model_files(repo_path)

    # Scan for dataset files
    if not quiet:
        console.print("[dim]Scanning for dataset files...[/dim]")
    dataset_files = find_dataset_files(repo_path)

    # Scan .env for API keys
    if not quiet:
        console.print("[dim]Scanning .env files for API keys...[/dim]")
    env_providers = find_env_api_keys(repo_path)

    # Build BOM
    repo_name = repo_path.name
    bom = build_aibom(
        repo_name, repo_path, all_deps,
        model_files, dataset_files, env_providers
    )

    components = bom["aibomstd"]["components"]
    summary = bom["aibomstd"]["summary"]

    # Print results table
    if not quiet:
        if components:
            table = Table(title=f"AI Components found in {repo_name}")
            table.add_column("Component", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Provider")
            table.add_column("Boundary", style="yellow")
            table.add_column("Risk", style="red")

            for c in components:
                boundary = "leaves" if c.get("service", {}).get("data-leaves-boundary") else "internal"
                risks = c.get("risks", [])
                risk_level = risks[0]["severity"] if risks else "none"
                table.add_row(
                    c["name"],
                    c["type"],
                    c.get("provider", "unknown"),
                    boundary,
                    risk_level
                )
            console.print(table)
        else:
            console.print("[yellow]No AI components detected.[/yellow]")
            console.print("[dim]Tip: Make sure requirements.txt or pyproject.toml exists.[/dim]")

        # Print summary
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"  Total components : {summary['total-components']}")
        console.print(f"  Models           : {summary['by-type']['model']}")
        console.print(f"  Datasets         : {summary['by-type']['dataset']}")
        console.print(f"  Frameworks       : {summary['by-type']['framework']}")
        console.print(f"  API clients      : {summary['by-type']['api-client']}")
        console.print(f"  Data egress      : {'[red]YES[/red]' if summary['data-leaves-boundary'] else '[green]NO[/green]'}")
        console.print(f"  Shadow AI        : {'[red]YES[/red]' if summary['shadow-ai-detected'] else '[green]NO[/green]'}")
        console.print(f"  Risk score       : [{'red' if summary['risk-score'] in ['high','critical'] else 'yellow' if summary['risk-score'] == 'medium' else 'green'}]{summary['risk-score'].upper()}[/]")

    # Write output
    output_path = output or f"{repo_name}.aibom.json"
    Path(output_path).write_text(json.dumps(bom, indent=2), encoding="utf-8")

    if not quiet:
        console.print(f"\n[green]Generated:[/green] {output_path}")
        console.print(f"[dim]Validate: aibomstd validate {output_path}[/dim]")

    return bom


@app.command()
def validate(
    path: str = typer.Argument(..., help="Path to .aibom.json file to validate"),
):
    """Validate an aibomstd BOM file against the schema."""
    import jsonschema
    import urllib.request

    bom_path = Path(path)
    if not bom_path.exists():
        console.print(f"[red]Error: file '{path}' not found.[/red]")
        raise typer.Exit(1)

    try:
        bom = json.loads(bom_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[dim]Validating {path}...[/dim]")

    # Try to fetch schema
    schema_url = "https://aibomstd.com/schema/v0.1/aibomstd.schema.json"
    try:
        with urllib.request.urlopen(schema_url, timeout=5) as r:
            schema = json.loads(r.read())
        jsonschema.validate(instance=bom, schema=schema)
        console.print(f"[green]Valid[/green] — {path} passes aibomstd schema v0.1")
    except urllib.error.URLError:
        # Offline mode — basic structure check
        if "aibomstd" in bom and "components" in bom["aibomstd"]:
            console.print(f"[green]Valid (offline check)[/green] — basic structure OK")
        else:
            console.print(f"[red]Invalid[/red] — missing required 'aibomstd.components' key")
            raise typer.Exit(1)
    except jsonschema.ValidationError as e:
        console.print(f"[red]Invalid[/red] — {e.message}")
        raise typer.Exit(1)


@app.command()
def convert(
    path: str = typer.Argument(..., help="Path to cisco-aibom JSON file"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Convert a cisco-aibom file to aibomstd format."""
    from .converters.cisco_converter import CiscoConverter

    input_path = Path(path)
    if not input_path.exists():
        console.print(f"[red]Error: file '{path}' not found.[/red]")
        raise typer.Exit(1)

    try:
        cisco_data = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON: {e}[/red]")
        raise typer.Exit(1)

    converter = CiscoConverter()
    bom = converter.convert(cisco_data)

    output_path = output or input_path.stem + ".aibom.json"
    Path(output_path).write_text(json.dumps(bom, indent=2), encoding="utf-8")

    console.print(f"[green]Converted:[/green] {path} → {output_path}")


@app.command()
def version():
    """Show aibomstd version."""
    console.print("aibomstd 0.1.0")


if __name__ == "__main__":
    app()
