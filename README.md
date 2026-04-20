# FLEXT-Infra

**FLEXT-Infra** is the infrastructure tooling library for the FLEXT ecosystem, providing build automation, code generation, workspace management, and quality validation for all FLEXT projects.

**Version**: 0.12.0-dev | Part of the [FLEXT](https://github.com/flext-sh/flext) ecosystem.

## Key Features

- **Build Automation**: Standardized `base.mk` generation for consistent project builds.
- **Code Generation**: Automated `__init__.py` lazy-export generation and code scaffolding.
- **Dependency Management**: `pyproject.toml` modernization and workspace-wide dependency synchronization.
- **Quality Validation**: Multi-gate validation (ruff, mypy, pyright, pyrefly) with configurable scopes.
- **Workspace Sync**: Cross-project configuration synchronization and drift detection.

## Documentation SSOT

`flext-infra` treats documentation as code and uses two primary sources of truth:

1. `pyproject.toml` metadata (project identity, version, packaging metadata)
2. Python docstrings (module/class/function behavior contracts)

Generated docs consume these inputs directly (see `flext-infra/docs/index.md` and
`flext-infra/docs/api-reference/README.md`).

### Docstring Automation

The workspace already ships docstring automation helpers under `scripts/`:

- `scripts/validate_docstrings.py` — audits missing/invalid docstrings
- `scripts/fix_docstrings.py` — inserts safe placeholder docstrings
- `scripts/ai_docstring_generator.py` — assisted generation with validation

Use these with quality gates to keep docstrings as reliable SSOT inputs.

### Recommended Maintenance Flow

1. Update code and docstrings in `src/`
2. Ensure package metadata is current in `pyproject.toml`
3. Run validation gates (including docstring-related checks)
4. Regenerate documentation artifacts via workspace automation

## CLI

Use the centralized entrypoint:

```bash
flext-infra <group> <command> [options]
```

Examples:

```bash
flext-infra basemk render --projects-name flext-core
flext-infra check run --projects flext-core
flext-infra codegen init --workspace .
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
