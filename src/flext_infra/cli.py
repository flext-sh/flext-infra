"""CLI entrypoint for the canonical flext-infra command surface."""

from __future__ import annotations

import sys
from types import MappingProxyType
from typing import ClassVar

from flext_cli import FlextCli, FlextCliSettings, cli, u
from flext_core import FlextSettings

from flext_infra import c, infra, t


class FlextInfraCli:
    """Single CLI entry surface for every flext-infra command group."""

    app_name: ClassVar[str] = "flext-infra"
    _HELP_FLAGS: ClassVar[frozenset[str]] = frozenset({"-h", "--help"})
    _SHARED_BOOL_FLAGS: ClassVar[frozenset[str]] = frozenset({
        "--apply",
        "--check",
        "--check-only",
        "--dry-run",
        "--diff",
        "--fail-fast",
        "--verbose",
        "--quiet",
        "--no-fail",
        "--typings",
        "--apply-typings",
        "--no-pip-check",
        "--skip-check",
        "--skip-comments",
        "--audit",
        "--rollback",
    })
    _SHARED_VALUE_FLAGS: ClassVar[frozenset[str]] = frozenset({
        "--workspace",
        "--projects",
        "--project",
        "--gates",
        "--format",
        "--output",
        "--report",
        "--output-dir",
        "--json-output",
        "--reports-dir",
        "--ruff-args",
        "--pyright-args",
    })
    _CLI_SERVICE: ClassVar[FlextCli] = FlextCli()
    GROUPS: ClassVar[t.StrMapping] = MappingProxyType({
        "basemk": "Base.mk template generation",
        c.Infra.VERB_CHECK: "Lint gates and pyrefly settings management",
        "codegen": "Code generation and workspace standardization",
        "validate": "Infrastructure validators and diagnostics",
        "deps": "Dependency detection, sync, and modernization",
        c.Infra.DIR_DOCS: "Documentation audit, fix, build, generate, validate",
        "github": "GitHub workflows, linting, and PR automation",
        "maintenance": "Python version enforcement",
        "refactor": "Declarative refactoring and modernization",
        c.Infra.RK_RELEASE: "Release orchestration",
        c.Infra.RK_WORKSPACE: "Workspace detection, sync, orchestration, migration",
    })

    @staticmethod
    def _cli_settings() -> FlextCliSettings:
        return FlextSettings.fetch_global().fetch_namespace("cli", FlextCliSettings)

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
        if group not in self.GROUPS:
            cli.display_message(
                f"unknown group '{group}'",
                c.Cli.MessageTypes.ERROR,
            )
            self.print_help()
            return 1
        return self._run_group(group, group_args)

    @classmethod
    def print_help(cls) -> None:
        """Display the canonical command groups."""
        cli.display_message(
            "Usage: flext-infra <group> [subcommand] [args...]",
            c.Cli.MessageTypes.INFO,
        )
        cli.display_message("Groups", c.Cli.MessageTypes.INFO)
        for group in sorted(cls.GROUPS):
            cli.display_message(
                f"  {group:<16}{cls.GROUPS[group]}",
                c.Cli.MessageTypes.INFO,
            )

    @classmethod
    def _normalize_group_args(cls, args: t.StrSequence) -> list[str]:
        return u.Cli.reorder_prefixed_options(
            args,
            bool_options=tuple(cls._SHARED_BOOL_FLAGS),
            value_options=tuple(cls._SHARED_VALUE_FLAGS),
        )

    def _run_group(self, group: str, args: t.StrSequence) -> int:
        """Execute a registered flext-cli group."""
        app = self._CLI_SERVICE.create_app_with_common_params(
            name=f"{self.app_name} {group}",
            help_text=self.GROUPS[group],
            settings=self._cli_settings(),
        )
        infra.register_group(group, app)
        normalized_args = self._normalize_group_args(args)
        if not normalized_args:
            _ = cli.execute_app(
                app,
                prog_name=f"{self.app_name} {group}",
                args=["--help"],
            )
            return 1
        result = cli.execute_app(
            app,
            prog_name=f"{self.app_name} {group}",
            args=normalized_args,
        )
        if result.success:
            return 0
        error_message = result.error
        if error_message:
            cli.display_message(error_message, c.Cli.MessageTypes.ERROR)
        return 2 if error_message and u.Cli.cli_usage_error(error_message) else 1


def main(args: t.StrSequence | None = None) -> int:
    """Run the canonical flext-infra CLI."""
    return FlextInfraCli().main(args)


__all__: list[str] = ["FlextInfraCli", "main"]
