# Contributing to aibomstd

Thank you for your interest in contributing to aibomstd.

aibomstd is an open standard for AI Bill of Materials. The goal is for
it to become the universal way the industry describes, tracks, and governs
AI components — models, datasets, frameworks, and API clients — across
every product, team, and compliance regime.

That only happens if the community builds on it, challenges it, and
improves it together. Every contribution matters.

---

## What you can do with aibomstd

aibomstd is designed to be used freely as a standard:

- **Use the schema** in your own products, tools, and pipelines
- **Build on the SDK** to generate, validate, or transform AI BOMs
- **Integrate the CLI** into your CI/CD workflows
- **Create your own tooling** on top of the standard — dashboards,
  scanners, exporters, converters — commercial or open source
- **Adopt it as your internal standard** without asking permission
- **Contribute improvements** to the schema, SDK, CLI, or CI plugins

The schema, SDK, CLI, and CI plugins are licensed under **Apache 2.0**.
This means you have full freedom to use, modify, distribute, and build
on them — commercially or otherwise — with no restrictions.

---

## What is not open source

The `cloud/` directory — which contains the hosted policy engine,
compliance report generator, drift detection system, certification
platform, and enrichment database — is licensed under **BUSL 1.1**.

This means you cannot copy the `cloud/` code and run it as a
competing hosted SaaS product. Everything outside `cloud/` is
fully open and has no such restriction.

This is the same model used by HashiCorp (Terraform), Elastic, and
GitLab: open standard + open tooling + commercial hosted layer.

---

## How to contribute

### Schema (schema/)

The schema is the heart of the standard. Contributions here have
the highest impact.

- Open an issue to propose a new field or component type
- Follow the discussion — schema changes affect everyone who has
  adopted the standard, so we discuss before merging
- All schema changes must be accompanied by:
  - Updated example BOM in `examples/`
  - Updated CI validation in `.github/workflows/validate-schema.yml`
  - A note in `CHANGELOG.md`

### SDK (sdk/)

The Python SDK is the primary way developers interact with aibomstd.

- Bug fixes and new component support are always welcome
- New output formats (SPDX, CycloneDX extensions, etc) are welcome
- All contributions must include tests in `sdk/tests/`
- Run the test suite before submitting:
  ```
  cd sdk
  pip install -e ".[dev]"
  pytest
  ```

### CLI (cli/)

The CLI is the primary way aibomstd integrates into CI/CD pipelines.

- New scan targets and integrations are welcome
- Keep the Docker image under 50MB
- No LLM calls in the CLI — offline and deterministic only

### CI Plugins (ci-plugins/)

- GitHub Actions plugin lives in `.github/workflows/`
- GitLab CI and Azure DevOps plugins get their own repos at Month 5
- Contributions for new CI platforms are welcome

### Documentation (docs/)

Clear documentation is as important as the code.

- Fix typos, improve examples, add use cases
- All docs contributions are welcome without prior discussion

---

## Contribution process

1. **Open an issue first** for anything beyond a small fix
   Discuss the change before writing code — especially for schema changes
2. **Fork the repo** and create a branch
3. **Write tests** for any code change
4. **Submit a pull request** with a clear description
5. **Sign the DCO** — add `Signed-off-by: Your Name <email>` to commits
   This certifies you wrote the contribution and have the right to
   submit it under Apache 2.0

---

## Code of conduct

Be direct. Be constructive. Assume good faith.
Disrespectful behaviour will not be tolerated.

---

## Questions

Open an issue or email aibomstd@gmail.com
