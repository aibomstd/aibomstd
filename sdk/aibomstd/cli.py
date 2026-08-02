"""
aibomstd CLI — AI Bill of Materials scanner and validator.
"""
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Optional

from aibomstd import __version__ as _SDK_VERSION

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

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
    "openai":              {"provider": "openai",      "leaves": True},
    "anthropic":           {"provider": "anthropic",   "leaves": True},
    "google-generativeai": {"provider": "google",      "leaves": True},
    "google-cloud-aiplatform": {"provider": "google",  "leaves": True},
    "cohere":              {"provider": "cohere",       "leaves": True},
    "mistralai":           {"provider": "mistral",      "leaves": True},
    "together":            {"provider": "together",     "leaves": True},
    "groq":                {"provider": "groq",         "leaves": True},
    "replicate":           {"provider": "replicate",    "leaves": True},
    "boto3":               {"provider": "aws",          "leaves": True},
    "azure-ai-inference":  {"provider": "microsoft",    "leaves": True},
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
    "pydantic-ai":      {"provider": "pydantic"},
}

LOCAL_MODELS = {
    "torch":             {"provider": "pytorch",      "type": "framework"},
    "tensorflow":        {"provider": "google",       "type": "framework"},
    "transformers":      {"provider": "huggingface",  "type": "framework"},
    "diffusers":         {"provider": "huggingface",  "type": "framework"},
    "sentence-transformers": {"provider": "huggingface", "type": "framework"},
    "huggingface-hub":   {"provider": "huggingface",  "type": "framework"},
    "ollama":            {"provider": "ollama",       "type": "framework"},
    "llama-cpp-python":  {"provider": "ggerganov",    "type": "framework"},
    "vllm":              {"provider": "vllm-project", "type": "framework"},
}

MODEL_FILE_EXTENSIONS = {
    ".gguf": "llama.cpp quantized model",
    ".ggml": "ggml model",
    ".bin":  "binary model weights",
    ".pt":   "PyTorch model",
    ".pth":  "PyTorch checkpoint",
    ".safetensors": "safetensors model",
    ".onnx": "ONNX model",
    ".pb":   "TensorFlow protobuf",
    ".h5":   "Keras/HDF5 model",
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

VALID_RESIDENCIES = ["US", "EU", "IN", "UK", "SG", "AU", "JP", "CA", "BR", "unknown"]


# ─────────────────────────────────────────────
# Scanner helpers
# ─────────────────────────────────────────────

def parse_requirements(path: Path) -> dict[str, str]:
    deps = {}
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
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
    deps = {}
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
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
    models = []
    skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv"}
    try:
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for fname in files:
                ext = Path(fname).suffix.lower()
                if ext in MODEL_FILE_EXTENSIONS:
                    fpath = Path(root) / fname
                    size_mb = fpath.stat().st_size / (1024 * 1024)
                    if size_mb > 1:
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
    datasets = []
    skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv"}
    try:
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            root_path = Path(root)
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
    providers = []
    env_files = list(repo_path.glob("**/.env*"))
    patterns = {
        "openai":      r"OPENAI_API_KEY",
        "anthropic":   r"ANTHROPIC_API_KEY",
        "google":      r"GOOGLE_API_KEY|GEMINI_API_KEY",
        "cohere":      r"COHERE_API_KEY",
        "mistral":     r"MISTRAL_API_KEY",
        "groq":        r"GROQ_API_KEY",
        "replicate":   r"REPLICATE_API_TOKEN",
        "together":    r"TOGETHER_API_KEY",
        "huggingface": r"HUGGINGFACE_TOKEN|HF_TOKEN",
        "aws":         r"AWS_ACCESS_KEY_ID",
    }
    for env_file in env_files[:5]:
        try:
            content = env_file.read_text(encoding="utf-8", errors="ignore")
            for provider, pattern in patterns.items():
                if re.search(pattern, content):
                    if provider not in providers:
                        providers.append(provider)
        except Exception:
            pass
    return providers


def prompt_residency(
    component_name: str,
    timeout: int = 10
) -> tuple[str, bool]:
    """
    Prompt user for residency declaration.
    Returns (residency, declared) tuple.
    Times out after `timeout` seconds.
    """
    import threading

    result = {"value": "unknown", "declared": False}

    def get_input():
        try:
            valid = "/".join(VALID_RESIDENCIES)
            val = Prompt.ask(
                f"\n  [yellow]Where does [bold]{component_name}[/bold] process your data?[/yellow]\n"
                f"  [{valid}] ([dim]{timeout}s timeout, Enter to skip[/dim])",
                default="skip",
                console=console
            )
            if val and val.upper() in [r.upper() for r in VALID_RESIDENCIES]:
                result["value"] = val.upper()
                result["declared"] = True
        except Exception:
            pass

    thread = threading.Thread(target=get_input, daemon=True)
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        console.print(f"  [dim]Timeout — {component_name} residency set to unknown[/dim]")

    return result["value"], result["declared"]


def build_aibom(
    repo_name: str,
    repo_path: Path,
    all_deps: dict[str, str],
    model_files: list[dict],
    dataset_files: list[dict],
    env_providers: list[str],
    declare_map: dict[str, str] = None,
    interactive: bool = True
) -> dict:
    import uuid
    from datetime import datetime, timezone

    declare_map = declare_map or {}
    components = []
    today = date.today().isoformat()

    def make_service(provider_name: str, leaves: bool) -> dict:
        """Build service block with residency declaration."""
        # Priority: --declare flag > interactive prompt > unknown
        if provider_name in declare_map:
            residency = declare_map[provider_name].upper()
            declared = True
            declared_by = "cli-flag"
            declared_on = today
            note = None
        elif interactive and leaves:
            residency, declared = prompt_residency(provider_name)
            declared_by = "scan-prompt" if declared else None
            declared_on = today if declared else None
            note = None if declared else \
                f"Not declared. Run: aibomstd declare {repo_name}.aibom.json {provider_name} --residency US"
        else:
            residency = "unknown"
            declared = False
            declared_by = None
            declared_on = None
            note = f"Not declared. Run: aibomstd declare {repo_name}.aibom.json {provider_name} --residency US"

        return {
            "data-leaves-boundary": leaves,
            "data-residency": residency,
            "data-residency-declared": declared,
            "data-residency-declared-by": declared_by,
            "data-residency-declared-on": declared_on,
            "data-residency-note": note
        }

    # API clients
    for pkg, version in all_deps.items():
        if pkg in API_CLIENTS:
            info = API_CLIENTS[pkg]
            components.append({
                "type": "api-client",
                "name": pkg,
                "version": version.lstrip(">=^~<! ") or "unknown",
                "provider": info["provider"],
                "service": make_service(pkg, info["leaves"]),
                "license": {"id": "proprietary", "osi-approved": False},
                "risks": [{
                    "id": f"DATA-EGRESS-{info['provider'].upper()}",
                    "severity": "high",
                    "description": f"Data leaves boundary to {info['provider']}"
                }]
            })

    # Frameworks
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
                    "data-residency": "local",
                    "data-residency-declared": True,
                    "data-residency-declared-by": "auto",
                    "data-residency-declared-on": today,
                    "data-residency-note": None
                },
                "license": {"id": "Apache-2.0", "osi-approved": True},
                "risks": []
            })

    # Shadow AI from .env
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
                "service": make_service(provider, True),
                "license": {"id": "proprietary", "osi-approved": False},
                "risks": [{
                    "id": f"DATA-EGRESS-{provider.upper()}-ENV",
                    "severity": "high",
                    "description": f"API key in .env — data may leave boundary to {provider}"
                }],
                "notes": "Detected via .env — not in package dependencies"
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
                "data-residency": "local",
                "data-residency-declared": True,
                "data-residency-declared-by": "auto",
                "data-residency-declared-on": today,
                "data-residency-note": None
            },
            "license": {"id": "unknown", "osi-approved": False},
            "risks": [{
                "id": "LICENSE-UNKNOWN",
                "severity": "medium",
                "description": "Model file — license and provenance unknown"
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
                "description": "Dataset file — license and sensitivity unknown"
            }]
        })

    # Summary
    data_leaves = any(
        c.get("service", {}).get("data-leaves-boundary")
        for c in components
    )
    undeclared = [
        c["name"] for c in components
        if c.get("service", {}).get("data-leaves-boundary")
        and not c.get("service", {}).get("data-residency-declared")
    ]
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
            "generated": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tool": {
                "name": "aibomstd-cli",
                "version": _SDK_VERSION,
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
                "shadow-ai-detected": len(env_providers) > 0,
                "residency-undeclared": undeclared
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
    declare: Optional[list[str]] = typer.Option(None, "--declare", "-d",
        help="Declare residency inline: --declare openai=EU --declare anthropic=US"),
    no_interactive: bool = typer.Option(False, "--no-interactive",
        help="Skip interactive residency prompts (CI/CD mode)"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress progress output"),
):
    """Scan a repository and generate an AI Bill of Materials."""

    repo_path = Path(path).resolve()
    if not repo_path.exists():
        console.print(f"[red]Error: path '{path}' does not exist.[/red]")
        raise typer.Exit(1)

    # Parse --declare flags into dict
    declare_map = {}
    if declare:
        for item in declare:
            if "=" in item:
                pkg, res = item.split("=", 1)
                declare_map[pkg.strip().lower()] = res.strip().upper()

    if not quiet:
        console.print(Panel.fit(
            "[bold green]aibomstd scan[/bold green]",
            subtitle=str(repo_path)
        ))

    all_deps: dict[str, str] = {}
    dep_files = {
        "requirements.txt":     parse_requirements,
        "requirements-dev.txt": parse_requirements,
        "pyproject.toml":       parse_pyproject,
        "package.json":         parse_package_json,
    }

    found_files = []
    for filename, parser in dep_files.items():
        fpath = repo_path / filename
        if fpath.exists():
            found_files.append(filename)
            all_deps.update(parser(fpath))

    if not quiet and found_files:
        console.print(f"[dim]Found dependency files: {', '.join(found_files)}[/dim]")
        console.print(f"[dim]Total packages scanned: {len(all_deps)}[/dim]")

    if not quiet:
        console.print("[dim]Scanning for model files...[/dim]")
    model_files = find_model_files(repo_path)

    if not quiet:
        console.print("[dim]Scanning for dataset files...[/dim]")
    dataset_files = find_dataset_files(repo_path)

    if not quiet:
        console.print("[dim]Scanning .env files for API keys...[/dim]")
    env_providers = find_env_api_keys(repo_path)

    # Interactive mode only if terminal and not suppressed
    interactive = not no_interactive and sys.stdin.isatty()

    repo_name = repo_path.name
    bom = build_aibom(
        repo_name, repo_path, all_deps,
        model_files, dataset_files, env_providers,
        declare_map=declare_map,
        interactive=interactive
    )

    components = bom["aibomstd"]["components"]
    summary = bom["aibomstd"]["summary"]

    if not quiet:
        if components:
            table = Table(title=f"AI Components found in {repo_name}")
            table.add_column("Component", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Provider")
            table.add_column("Boundary", style="yellow")
            table.add_column("Residency")
            table.add_column("Declared", style="green")
            table.add_column("Risk", style="red")

            for c in components:
                svc = c.get("service", {})
                boundary = "leaves" if svc.get("data-leaves-boundary") else "internal"
                residency = svc.get("data-residency", "unknown")
                declared = "✓" if svc.get("data-residency-declared") else "✗"
                risks = c.get("risks", [])
                risk_level = risks[0]["severity"] if risks else "none"
                table.add_row(
                    c["name"], c["type"],
                    c.get("provider", "unknown"),
                    boundary, residency, declared, risk_level
                )
            console.print(table)
        else:
            console.print("[yellow]No AI components detected.[/yellow]")

        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"  Total components : {summary['total-components']}")
        console.print(f"  API clients      : {summary['by-type']['api-client']}")
        console.print(f"  Frameworks       : {summary['by-type']['framework']}")
        console.print(f"  Models           : {summary['by-type']['model']}")
        console.print(f"  Datasets         : {summary['by-type']['dataset']}")
        console.print(f"  Data egress      : {'[red]YES[/red]' if summary['data-leaves-boundary'] else '[green]NO[/green]'}")
        console.print(f"  Shadow AI        : {'[red]YES[/red]' if summary['shadow-ai-detected'] else '[green]NO[/green]'}")
        console.print(f"  Risk score       : [{'red' if summary['risk-score'] in ['high','critical'] else 'yellow' if summary['risk-score'] == 'medium' else 'green'}]{summary['risk-score'].upper()}[/]")

        undeclared = summary.get("residency-undeclared", [])
        if undeclared:
            console.print(f"\n[yellow]⚠ Residency undeclared for: {', '.join(undeclared)}[/yellow]")
            console.print(f"[dim]  Declare now:  aibomstd declare {repo_name}.aibom.json {undeclared[0]} --residency US[/dim]")
            console.print(f"[dim]  Or next scan: aibomstd scan . --declare {undeclared[0]}=US[/dim]")

    output_path = output or f"{repo_name}.aibom.json"
    Path(output_path).write_text(json.dumps(bom, indent=2), encoding="utf-8")

    if not quiet:
        console.print(f"\n[green]Generated:[/green] {output_path}")
        console.print(f"[dim]Validate:  aibomstd validate {output_path}[/dim]")


@app.command()
def declare(
    bom_file: str = typer.Argument(..., help="Path to .aibom.json file to update"),
    component: str = typer.Argument(..., help="Component name to declare residency for"),
    residency: str = typer.Option(..., "--residency", "-r",
        help=f"Residency to declare: {', '.join(VALID_RESIDENCIES)}"),
    by: Optional[str] = typer.Option(None, "--by", "-b",
        help="Who is making this declaration (email or name)"),
):
    """Declare data residency for a component in an existing BOM file."""

    bom_path = Path(bom_file)
    if not bom_path.exists():
        console.print(f"[red]Error: '{bom_file}' not found.[/red]")
        raise typer.Exit(1)

    residency = residency.upper()
    if residency not in VALID_RESIDENCIES:
        console.print(f"[red]Invalid residency '{residency}'. Choose from: {', '.join(VALID_RESIDENCIES)}[/red]")
        raise typer.Exit(1)

    try:
        bom = json.loads(bom_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON: {e}[/red]")
        raise typer.Exit(1)

    components = bom.get("aibomstd", {}).get("components", [])
    found = False

    for c in components:
        if c.get("name", "").lower() == component.lower():
            if "service" not in c:
                c["service"] = {}
            c["service"]["data-residency"] = residency
            c["service"]["data-residency-declared"] = True
            c["service"]["data-residency-declared-by"] = by or "user"
            c["service"]["data-residency-declared-on"] = date.today().isoformat()
            c["service"]["data-residency-note"] = None
            found = True
            break

    if not found:
        console.print(f"[red]Component '{component}' not found in BOM.[/red]")
        console.print(f"[dim]Available: {', '.join(c.get('name') for c in components)}[/dim]")
        raise typer.Exit(1)

    # Update undeclared list in summary
    summary = bom.get("aibomstd", {}).get("summary", {})
    undeclared = summary.get("residency-undeclared", [])
    if component in undeclared:
        undeclared.remove(component)
    summary["residency-undeclared"] = undeclared

    bom_path.write_text(json.dumps(bom, indent=2), encoding="utf-8")
    console.print(f"[green]✓ Declared:[/green] {component} → {residency}")
    if by:
        console.print(f"[dim]  By: {by} on {date.today().isoformat()}[/dim]")
    console.print(f"[dim]  File updated: {bom_file}[/dim]")


@app.command()
def validate(
    path: str = typer.Argument(..., help="Path to .aibom.json file to validate"),
):
    """Validate an aibomstd BOM file against the schema."""
    import jsonschema
    import urllib.request

    bom_path = Path(path)
    if not bom_path.exists():
        console.print(f"[red]Error: '{path}' not found.[/red]")
        raise typer.Exit(1)

    try:
        bom = json.loads(bom_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[dim]Validating {path}...[/dim]")

    schema_url = "https://aibomstd.com/schema/v0.1/aibomstd.schema.json"
    try:
        with urllib.request.urlopen(schema_url, timeout=5) as r:
            schema = json.loads(r.read())
        jsonschema.validate(instance=bom, schema=schema)
        console.print(f"[green]✓ Valid[/green] — {path} passes aibomstd schema v0.1")
    except urllib.error.URLError:
        if "aibomstd" in bom and "components" in bom["aibomstd"]:
            console.print(f"[green]✓ Valid (offline)[/green] — basic structure OK")
        else:
            console.print(f"[red]✗ Invalid[/red] — missing required keys")
            raise typer.Exit(1)
    except jsonschema.ValidationError as e:
        console.print(f"[red]✗ Invalid[/red] — {e.message}")
        raise typer.Exit(1)


@app.command()
def version():
    """Show aibomstd version."""
    console.print(f"aibomstd {_SDK_VERSION}")


if __name__ == "__main__":
    app()
