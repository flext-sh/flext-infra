# FLEXT-Infra

**FLEXT-Infra** is the infrastructure tooling library for the FLEXT ecosystem, providing build automation, code generation, workspace management, and quality validation for all FLEXT projects.

**Version**: 0.12.0-dev | Part of the [FLEXT](https://github.com/flext-sh/flext) ecosystem.

## Key Features

- **Build Automation**: Standardized `base.mk` generation for consistent project builds.
- **Code Generation**: Automated `__init__.py` lazy-export generation and code scaffolding.
- **Dependency Management**: `pyproject.toml` modernization and workspace-wide dependency synchronization.
- **Quality Validation**: Multi-gate validation (ruff, mypy, pyright, pyrefly) with configurable scopes.
- **Workspace Sync**: Cross-project configuration synchronization and drift detection.

## CLI

Use the centralized entrypoint:

```bash
flext-infra <group> <command> [options]
```

Examples:

```bash
flext-infra basemk render --project-name flext-core
flext-infra check run --projects flext-core
flext-infra codegen lazy-init --workspace .
flext-infra validate inventory --workspace .
flext-infra docs audit --workspace .
flext-infra workspace sync --workspace .
```

## Installation

```bash
poetry add flext-infra
```

## License

MIT License - see [LICENSE](LICENSE) for details.
