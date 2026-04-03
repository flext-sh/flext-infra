"""Canonical centralized CLI dispatcher for flext-infra."""

from __future__ import annotations

import sys
from types import MappingProxyType
from typing import ClassVar

from flext_cli import cli
from flext_infra import (
    FlextInfraCliBasemk,
    FlextInfraCliCheck,
    FlextInfraCliCodegen,
    FlextInfraCliDeps,
    FlextInfraCliDocs,
    FlextInfraCliGithub,
    FlextInfraCliMaintenance,
    FlextInfraCliRefactor,
    FlextInfraCliRelease,
    FlextInfraCliValidate,
    FlextInfraCliWorkspace,
    FlextInfraConstants as c,
    FlextInfraTypes as t,
    FlextInfraUtilities as u,
)


class FlextInfraCli(
    FlextInfraCliBasemk,
    FlextInfraCliCodegen,
    FlextInfraCliDocs,
    FlextInfraCliGithub,
    FlextInfraCliMaintenance,
    FlextInfraCliRefactor,
    FlextInfraCliRelease,
    FlextInfraCliValidate,
    FlextInfraCliWorkspace,
):
    """Single CLI entry surface for every flext-infra command group."""

    app_name: ClassVar[str] = "flext-infra"
    _HELP_FLAGS: ClassVar[frozenset[str]] = frozenset({"-h", "--help"})
    _USAGE_ERROR_MARKERS: ClassVar[tuple[str, ...]] = (
        "No such option",
        "No such command",
        "Missing option",
        "Missing argument",
        "Got unexpected extra argument",
        "unrecognized arguments",
        "CLI exited with code 2",
    )
    GROUPS: ClassVar[t.StrMapping] = MappingProxyType({
        "basemk": "Base.mk template generation",
        c.Infra.Verbs.CHECK: "Lint gates and pyrefly config management",
        "codegen": "Code generation and workspace standardization",
        "validate": "Infrastructure validators and diagnostics",
        "deps": "Dependency detection, sync, and modernization",
        c.Infra.Directories.DOCS: "Documentation audit, fix, build, generate, validate",
        "github": "GitHub workflows, linting, and PR automation",
        "maintenance": "Python version enforcement",
        "refactor": "Declarative refactoring and modernization",
        c.Infra.ReportKeys.RELEASE: "Release orchestration",
        c.Infra.ReportKeys.WORKSPACE: "Workspace detection, sync, orchestration, migration",
    })

    def main(self, args: t.StrSequence | None = None) -> int:
        """Run the centralized dispatcher."""
        u.ensure_structlog_configured()
        cli_args = list(args) if args is not None else sys.argv[1:]
        if not cli_args:
            self.print_help()
            return 1
        if cli_args[0] in self._HELP_FLAGS:
            self.print_help()
            return 0
        group, group_args = cli_args[0], cli_args[1:]
        if group == c.Infra.Verbs.CHECK:
            return FlextInfraCliCheck.run(group_args)
        if group == "deps":
            return FlextInfraCliDeps.run(group_args)
        if group not in self.GROUPS:
            u.error(f"unknown group '{group}'")
            self.print_help()
            return 1
        return self._run_group(group, group_args)

    @classmethod
    def print_help(cls) -> None:
        """Display the canonical command groups."""
        u.info("Usage: flext-infra <group> [subcommand] [args...]")
        u.header("Groups")
        for group in sorted(cls.GROUPS):
            u.info(f"  {group:<16}{cls.GROUPS[group]}")

    def _run_group(self, group: str, args: t.StrSequence) -> int:
        """Execute a registered flext-cli group."""
        app = cli.create_app_with_common_params(
            name=f"{self.app_name} {group}",
            help_text=self.GROUPS[group],
        )
        if group == "basemk":
            self.register_basemk(app)
        elif group == "codegen":
            self.register_codegen(app)
        elif group == "validate":
            self.register_validate(app)
        elif group == c.Infra.Directories.DOCS:
            self.register_docs(app)
        elif group == "github":
            self.register_github(app)
        elif group == "maintenance":
            self.register_maintenance(app)
        elif group == "refactor":
            self.register_refactor(app)
        elif group == c.Infra.ReportKeys.RELEASE:
            self.register_release(app)
        elif group == c.Infra.ReportKeys.WORKSPACE:
            self.register_workspace(app)
        if not args:
            _ = cli.execute_app(
                app, prog_name=f"{self.app_name} {group}", args=["--help"]
            )
            return 1
        result = cli.execute_app(app, prog_name=f"{self.app_name} {group}", args=args)
        if result.is_success:
            return 0
        return 2 if self._is_usage_error(result.error or "") else 1

    @classmethod
    def _is_usage_error(cls, message: str) -> bool:
        """Return True when the normalized error looks like a usage failure."""
        return any(marker in message for marker in cls._USAGE_ERROR_MARKERS)


def main(args: t.StrSequence | None = None) -> int:
    """Run the canonical flext-infra CLI."""
    return FlextInfraCli().main(args)
