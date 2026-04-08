"""Canonical centralized CLI dispatcher for flext-infra."""

from __future__ import annotations

import sys
from collections.abc import Callable
from types import MappingProxyType
from typing import ClassVar

from flext_cli import cli as cli_service
from flext_core import FlextLogger
from flext_infra import c, infra, t


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
        "--projects",
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

    def __init__(self) -> None:
        """Initialize the thin CLI router over the public infra facade."""
        self._service = infra
        self._group_registrars: t.MappingKV[
            str,
            Callable[[t.Cli.CliApp], None],
        ] = MappingProxyType({
            "basemk": self._service.register_basemk,
            "codegen": self._service.register_codegen,
            "validate": self._service.register_validate,
            c.Infra.Directories.DOCS: self._service.register_docs,
            "github": self._service.register_github,
            "maintenance": self._service.register_maintenance,
            "refactor": self._service.register_refactor,
            c.Infra.ReportKeys.RELEASE: self._service.register_release,
            c.Infra.ReportKeys.WORKSPACE: self._service.register_workspace,
        })
        self._group_runners: t.MappingKV[
            str,
            Callable[[t.StrSequence | None], int],
        ] = MappingProxyType({
            c.Infra.Verbs.CHECK: self._service.run_check_cli,
            "deps": self._service.run_deps_cli,
        })

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
        runner = self._group_runners.get(group)
        if runner is not None:
            return runner(group_args)
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
            config=self._service.settings,
        )
        self._group_registrars[group](app)
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
