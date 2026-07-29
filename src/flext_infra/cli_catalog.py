"""Lightweight canonical CLI descriptors and structural command selection."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import ClassVar


def _descriptors(
    values: dict[str, dict[str, str]],
) -> Mapping[str, Mapping[str, str]]:
    return MappingProxyType({
        group: MappingProxyType(commands) for group, commands in values.items()
    })


class CliCatalog:
    """Own public groups, commands, help text, and pre-import argv selection."""

    help_flags: ClassVar[frozenset[str]] = frozenset({"-h", "--help"})
    shared_bool_flags: ClassVar[frozenset[str]] = frozenset({
        "--apply",
        "--apply-typings",
        "--audit",
        "--check",
        "--check-only",
        "--dry-run",
        "--fail-fast",
        "--no-fail",
        "--no-pip-check",
        "--quiet",
        "--rewrite-constraints",
        "--skip-check",
        "--skip-comments",
        "--typings",
        "--verbose",
    })
    shared_value_flags: ClassVar[frozenset[str]] = frozenset({
        "--base",
        "--branch",
        "--checks",
        "--docstring-min",
        "--format",
        "--gates",
        "--json-output",
        "--module",
        "--namespace",
        "--operation",
        "--output",
        "--output-dir",
        "--project",
        "--projects",
        "--pyright-args",
        "--report",
        "--reports-dir",
        "--root",
        "--ruff-args",
        "--what",
        "--workspace",
    })
    group_descriptions: ClassVar[Mapping[str, str]] = MappingProxyType({
        "basemk": "Base.mk template generation",
        "check": "Lint gates and pyrefly settings management",
        "codegen": "Code generation and workspace standardization",
        "validate": "Infrastructure validators and diagnostics",
        "deps": "Dependency detection and modernization",
        "docs": "Documentation audit, fix, build, generate, validate",
        "github": "GitHub workflows, linting, and PR automation",
        "maintenance": "Python version enforcement",
        "refactor": "Declarative refactoring and modernization",
        "release": "Release orchestration",
        "workspace": "Workspace detection, sync, orchestration, migration",
    })
    transaction_apply_routes: ClassVar[frozenset[str]] = frozenset({
        "check:fix-enforcement",
        "check:fix-pyrefly-settings",
        "codegen:auto-fix",
        "codegen:consolidate",
        "codegen:init",
        "codegen:new",
        "codegen:pipeline",
        "codegen:py-typed",
        "codegen:scaffold",
        "codegen:version-file",
        "deps:extra-paths",
        "deps:modernize",
        "refactor:accessor-migrate",
        "refactor:apply-renames",
        "refactor:migrate-mro",
        "refactor:modernize-cli",
        "refactor:modernize-logging",
        "refactor:modernize-patterns",
        "refactor:modernize-pydantic",
        "refactor:modernize-result-di",
        "refactor:namespace-enforce",
        "refactor:wrapper-root-namespace",
        "workspace:migrate",
        "workspace:sync",
    })
    transaction_mode_routes: ClassVar[frozenset[str]] = frozenset({
        "codegen:conform"
    })
    command_descriptions: ClassVar[Mapping[str, Mapping[str, str]]] = _descriptors({
        "basemk": {
            "generate": "Generate base.mk content from the canonical template",
        },
        "check": {
            "run": "Run workspace quality gates",
            "fix-pyrefly-settings": "Repair [tool.pyrefly] blocks",
            "fix-enforcement": "Auto-fix enforcement-catalog violations",
        },
        "codegen": {
            "conform": "Conform generated project and workspace files",
            "new": "Create a new FLEXT project from the canonical templates",
            "init": "Generate/refresh PEP 562 lazy-import __init__.py files",
            "census": "Count namespace violations across workspace projects",
            "scaffold": "Generate missing base modules in src/ and tests/",
            "auto-fix": "Auto-fix namespace violations (move Finals/TypeVars)",
            "py-typed": "Create/remove PEP 561 py.typed markers",
            "pipeline": "Run full codegen pipeline",
            "constants-quality-gate": "Run constants migration quality gate",
            "consolidate": (
                "Consolidate inline constants into c.Infra.* references"
            ),
            "version-file": (
                "Generate __version__.py from project-metadata SSOT"
            ),
        },
        "deps": {
            "detect": "Detect runtime vs dev dependencies",
            "extra-paths": "Synchronize pyright/mypy extraPaths",
            "modernize": "Modernize workspace pyproject files",
        },
        "docs": {
            "audit": "Audit documentation for broken links and forbidden terms",
            "fix": "Fix documentation issues",
            "build": "Build MkDocs sites",
            "generate": "Generate project docs",
            "serve": "Serve one MkDocs site in dev mode (blocking preview)",
            "validate": "Validate documentation",
        },
        "github": {
            "workflows": "Sync GitHub workflow files across workspace",
            "lint": "Lint GitHub workflow files",
            "pr": "Manage pull requests for a single project",
            "pr-workspace": "Manage pull requests across workspace projects",
        },
        "maintenance": {
            "run": "Enforce Python version constraints",
        },
        "validate": {
            "basemk-validate": "Validate base.mk sync",
            "inventory": "Generate scripts inventory",
            "runtime-census": (
                "Post-import Beartype enforcement census for flext_* modules"
            ),
            "pytest-diag": "Extract pytest diagnostics",
            "scan": "Scan text files for patterns",
            "skill-validate": "Validate a skill",
            "silent-failure": "Validate silent failure sentinel returns",
            "stub-validate": "Validate stub supply chain",
            "fresh-import": "Guard 7: fresh-process import smoke test",
            "import-cycles": "Guard 1: ROPE-backed import cycle detector",
            "lazy-map-freshness": "Guard 2/3: lazy-map freshness validator",
            "namespace": "Guard: static namespace rules (NS-000..003) via rope",
            "tier-whitelist": (
                "Guard 5: tier-whitelist/abstraction-boundary enforcer"
            ),
            "metadata-discipline": (
                "Guard 8: centralized metadata parser discipline"
            ),
            "manual-cmd": (
                "Manual-command blocker (§5): pre-commit config drift gate"
            ),
        },
        "refactor": {
            "apply-renames": "Check or apply an old,new CSV rename list",
            "migrate-mro": "Migrate loose declarations into MRO facade classes",
            "namespace-enforce": (
                "Scan workspace for namespace governance violations"
            ),
            "census": "Run a Rope-only workspace census for Python objects",
            "accessor-migrate": (
                "Preview or apply automated get_/set_/is_ migration"
            ),
            "wrapper-root-namespace": (
                "Normalize wrapper alias imports to wrapper root and "
                "flatten *.Core.Tests paths"
            ),
            "modernize-patterns": (
                "Fix u.Cli.print(), pdb, bare except and open() encoding "
                "in library code"
            ),
            "modernize-pydantic": (
                "Migrate Pydantic v1/legacy patterns to Pydantic v2"
            ),
            "modernize-logging": "Migrate logging usage to u.fetch_logger",
            "modernize-result-di": (
                "Migrate result-flow and dependency-injector patterns "
                "to FLEXT canonical forms"
            ),
            "modernize-cli": (
                "Remove banned CLI helper imports and route u.Cli.print() "
                "to cli.display_text()"
            ),
        },
        "release": {
            "run": "Run release orchestration CLI flow",
        },
        "workspace": {
            "verify-environment": "Verify live workspace editable provenance",
            "detect": "Detect workspace or standalone mode",
            "sync": "Sync base.mk to project root",
            "orchestrate": "Run make verb across projects",
            "serialize-make": (
                "Run one state-sensitive Make verb under its checkout lock"
            ),
            "migrate": "Migrate workspace projects to flext_infra tooling",
            "worktree": "Manage repository-local development worktrees",
        },
    })
    factory_modules: ClassVar[Mapping[str, Mapping[str, str]]] = _descriptors({
        "basemk": {"generate": "flext_infra.basemk.generator"},
        "check": {
            "run": "flext_infra.check.workspace_check",
            "fix-pyrefly-settings": "flext_infra.deps.fix_pyrefly_config",
            "fix-enforcement": "flext_infra.fixers.orchestrator",
        },
        "codegen": {
            "conform": "flext_infra.codegen.conform",
            "new": "flext_infra.codegen.project_new",
            "init": "flext_infra.codegen.lazy_init",
            "census": "flext_infra.codegen.census",
            "scaffold": "flext_infra.codegen.scaffolder",
            "auto-fix": "flext_infra.codegen.fixer",
            "py-typed": "flext_infra.codegen.py_typed",
            "pipeline": "flext_infra.codegen.pipeline",
            "constants-quality-gate": (
                "flext_infra.codegen.constants_quality_gate"
            ),
            "consolidate": "flext_infra.codegen.consolidator",
            "version-file": "flext_infra.codegen.version_file",
        },
        "deps": {
            "detect": "flext_infra.deps.detector",
            "extra-paths": "flext_infra.deps.extra_paths",
            "modernize": "flext_infra.deps.modernizer",
        },
        "docs": {
            "audit": "flext_infra.docs.auditor",
            "fix": "flext_infra.docs.fixer",
            "build": "flext_infra.docs.builder",
            "generate": "flext_infra.docs.generator",
            "serve": "flext_infra.docs.server",
            "validate": "flext_infra.docs.validator",
        },
        "github": {
            "workflows": "flext_infra.utilities",
            "lint": "flext_infra.utilities",
            "pr": "flext_infra.utilities",
            "pr-workspace": "flext_infra.utilities",
        },
        "maintenance": {
            "run": "flext_infra.maintenance.python_version",
        },
        "validate": {
            "basemk-validate": "flext_infra.validate.basemk_validator",
            "inventory": "flext_infra.validate.inventory",
            "runtime-census": "flext_infra.validate.runtime_census",
            "pytest-diag": "flext_infra.validate.pytest_diag",
            "scan": "flext_infra.validate.scanner",
            "skill-validate": "flext_infra.validate.skill_validator",
            "silent-failure": "flext_infra.validate.silent_failure",
            "stub-validate": "flext_infra.validate.stub_chain",
            "fresh-import": "flext_infra.validate.fresh_import",
            "import-cycles": "flext_infra.validate.import_cycles",
            "lazy-map-freshness": "flext_infra.validate.lazy_map_freshness",
            "namespace": "flext_infra.validate.namespace_validator",
            "tier-whitelist": "flext_infra.validate.tier_whitelist",
            "metadata-discipline": (
                "flext_infra.validate.metadata_discipline"
            ),
            "manual-cmd": "flext_infra.validate.manual_command",
        },
        "refactor": {
            "apply-renames": "flext_infra.codemod.rules.refactor.apply_renames",
            "migrate-mro": "flext_infra.refactor.migrate_to_class_mro",
            "namespace-enforce": "flext_infra.refactor.namespace_enforcer",
            "census": "flext_infra.refactor.census",
            "accessor-migrate": "flext_infra.refactor.accessor_migration",
            "wrapper-root-namespace": (
                "flext_infra.refactor.wrapper_root_namespace"
            ),
            "modernize-patterns": (
                "flext_infra.transformers.pattern_modernizer"
            ),
            "modernize-pydantic": (
                "flext_infra.transformers.pydantic_modernizer"
            ),
            "modernize-logging": (
                "flext_infra.transformers.logging_modernizer"
            ),
            "modernize-result-di": (
                "flext_infra.transformers.result_di_modernizer"
            ),
            "modernize-cli": "flext_infra.transformers.cli_modernizer",
        },
        "release": {"run": "flext_infra.release.orchestrator"},
        "workspace": {
            "verify-environment": (
                "flext_infra.workspace.environment_provenance"
            ),
            "detect": "flext_infra.workspace.detector",
            "sync": "flext_infra.workspace.sync",
            "orchestrate": "flext_infra.workspace.orchestrator",
            "serialize-make": "flext_infra.workspace.make_serialization",
            "migrate": "flext_infra.workspace.migrator",
            "worktree": "flext_infra.worktree",
        },
    })

    @classmethod
    def description(cls, group: str, command: str) -> str:
        """Return one canonical command description."""
        return cls.command_descriptions[group][command]

    @classmethod
    def factory_module(cls, group: str, command: str) -> str:
        """Return the only implementation module allowed after selection."""
        return cls.factory_modules[group][command]

    @classmethod
    def option_value(cls, args: Sequence[str], name: str) -> str | None:
        """Resolve one structured option value without treating it as a command."""
        for index, argument in enumerate(args):
            if argument == name and index + 1 < len(args):
                return args[index + 1]
            prefix = f"{name}="
            if argument.startswith(prefix):
                return argument.removeprefix(prefix)
        return None

    @classmethod
    def positional_command(cls, args: Sequence[str]) -> str | None:
        """Return the first positional token after structurally skipping options."""
        skip_value = False
        for argument in args:
            if skip_value:
                skip_value = False
                continue
            if argument in cls.shared_value_flags:
                skip_value = True
                continue
            if argument in cls.shared_bool_flags or argument in cls.help_flags:
                continue
            if any(
                argument.startswith(f"{option}=")
                for option in cls.shared_value_flags
            ):
                continue
            if argument.startswith("-"):
                continue
            return argument
        return None

    @classmethod
    def selected_command(cls, group: str, args: Sequence[str]) -> str | None:
        """Resolve the exact command before importing any runtime facade."""
        what = cls.option_value(args, "--what")
        if what is not None and group == "check":
            return "run"
        if what is not None and group == "validate":
            return what
        return cls.positional_command(args)


__all__: tuple[str, ...] = ("CliCatalog",)
