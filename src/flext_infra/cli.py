"""Canonical centralized CLI dispatcher for flext-infra."""

from __future__ import annotations

import importlib
import sys
from collections.abc import Callable
from types import MappingProxyType
from typing import ClassVar

from flext_cli import cli as cli_service
from flext_core import FlextLogger
from flext_infra.constants import c
from flext_infra.typings import t


class FlextInfraCli:
    """Single CLI entry surface for every flext-infra command group."""

    app_name: ClassVar[str] = "flext-infra"
    _HELP_FLAGS: ClassVar[frozenset[str]] = frozenset({"-h", "--help"})
    _SHARED_BOOL_FLAGS: ClassVar[frozenset[str]] = frozenset({
        "--apply",
        "--dry-run",
        "--diff",
    })
    _SHARED_VALUE_FLAGS: ClassVar[frozenset[str]] = frozenset({
        "--workspace",
        "--project",
    })
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
    _GROUP_REGISTRARS: ClassVar[t.StrMapping] = MappingProxyType({
        "basemk": "flext_infra.basemk.cli:FlextInfraCliBasemk:register_basemk",
        "codegen": "flext_infra.codegen.cli:FlextInfraCliCodegen:register_codegen",
        "validate": "flext_infra.validate.cli:FlextInfraCliValidate:register_validate",
        c.Infra.Directories.DOCS: "flext_infra.docs.cli:FlextInfraCliDocs:register_docs",
        "github": "flext_infra.github.cli:FlextInfraCliGithub:register_github",
        "maintenance": (
            "flext_infra.workspace.maintenance.cli:"
            "FlextInfraCliMaintenance:register_maintenance"
        ),
        "refactor": "flext_infra.refactor.cli:FlextInfraCliRefactor:register_refactor",
        c.Infra.ReportKeys.RELEASE: "flext_infra.release.cli:FlextInfraCliRelease:register_release",
        c.Infra.ReportKeys.WORKSPACE: "flext_infra.workspace.cli:FlextInfraCliWorkspace:register_workspace",
    })
    _GROUP_RUNNERS: ClassVar[t.StrMapping] = MappingProxyType({
        c.Infra.Verbs.CHECK: "flext_infra.check.cli:FlextInfraCliCheck:run",
        "deps": "flext_infra.deps.cli:FlextInfraCliDeps:run",
    })

    @staticmethod
    def _run_group_runner(spec: str, args: t.StrSequence | None) -> int:
        """Load and run a ``module:class:method`` CLI entrypoint."""
        module_path, class_name, method_name = spec.split(":")
        module = importlib.import_module(module_path)
        group_type = getattr(module, class_name)
        runner: Callable[[t.StrSequence | None], int] = getattr(
            group_type(),
            method_name,
        )
        return runner(args)

    @staticmethod
    def _register_group(spec: str, app: t.Cli.CliApp) -> None:
        """Load and register a lazy CLI group on the shared Typer app."""
        module_path, class_name, method_name = spec.split(":")
        module = importlib.import_module(module_path)
        group_type = getattr(module, class_name)
        registrar: Callable[[t.Cli.CliApp], None] = getattr(
            group_type(),
            method_name,
        )
        registrar(app)

    def main(self, args: t.StrSequence | None = None) -> int:
        """Run the centralized dispatcher."""
        FlextLogger.ensure_structlog_configured()
        cli_args = list(args) if args is not None else sys.argv[1:]
        if not cli_args:
            self.print_help()
            return 1
        if cli_args[0] in self._HELP_FLAGS:
            self.print_help()
            return 0
        group, group_args = cli_args[0], cli_args[1:]
        if group in self._GROUP_RUNNERS:
            return self._run_group_runner(self._GROUP_RUNNERS[group], group_args)
        if group not in self.GROUPS:
            cli_service.display_message(
                f"unknown group '{group}'",
                c.Cli.MessageTypes.ERROR,
            )
            self.print_help()
            return 1
        return self._run_group(group, group_args)

    @classmethod
    def print_help(cls) -> None:
        """Display the canonical command groups."""
        cli_service.display_message(
            "Usage: flext-infra <group> [subcommand] [args...]",
            c.Cli.MessageTypes.INFO,
        )
        cli_service.display_message("Groups", c.Cli.MessageTypes.INFO)
        for group in sorted(cls.GROUPS):
            cli_service.display_message(
                f"  {group:<16}{cls.GROUPS[group]}",
                c.Cli.MessageTypes.INFO,
            )

    @classmethod
    def _normalize_group_args(cls, args: t.StrSequence) -> t.StrSequence:
        """Move shared flags placed before a Typer subcommand behind the subcommand."""
        if not args:
            return list[str]()
        prefix_tokens: list[str] = []
        index = 0
        while index < len(args):
            token = args[index]
            normalized = token.split("=", 1)[0]
            if normalized in cls._SHARED_BOOL_FLAGS:
                prefix_tokens.append(token)
                index += 1
                continue
            if normalized in cls._SHARED_VALUE_FLAGS:
                prefix_tokens.append(token)
                if "=" not in token and index + 1 < len(args):
                    prefix_tokens.append(args[index + 1])
                    index += 2
                else:
                    index += 1
                continue
            if token.startswith("-"):
                break
            subcommand = token
            suffix_tokens = list(args[index + 1 :])
            return [subcommand, *prefix_tokens, *suffix_tokens]
        return list(args)

    def _run_group(self, group: str, args: t.StrSequence) -> int:
        """Execute a registered flext-cli group."""
        app = cli_service.create_app_with_common_params(
            name=f"{self.app_name} {group}",
            help_text=self.GROUPS[group],
        )
        self._register_group(self._GROUP_REGISTRARS[group], app)
        normalized_args = self._normalize_group_args(args)
        if not normalized_args:
            _ = cli_service.execute_app(
                app,
                prog_name=f"{self.app_name} {group}",
                args=["--help"],
            )
            return 1
        result = cli_service.execute_app(
            app,
            prog_name=f"{self.app_name} {group}",
            args=normalized_args,
        )
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


_package = sys.modules.get("flext_infra")
if _package is not None:
    setattr(_package, "main", main)


__all__ = ["FlextInfraCli", "main"]
