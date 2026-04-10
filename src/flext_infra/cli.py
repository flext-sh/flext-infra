"""CLI entrypoint for the canonical flext-infra command surface."""

from __future__ import annotations

import importlib
import sys
from collections.abc import Callable
from types import MappingProxyType
from typing import ClassVar

from flext_cli import FlextCliSettings, cli as cli_service
from flext_core import FlextLogger, FlextSettings
from flext_infra import c, t


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
        self._group_registrars: t.MappingKV[
            str,
            Callable[[t.Cli.CliApp], None],
        ] = MappingProxyType({
            "basemk": self._register_basemk,
            c.Infra.Verbs.CHECK: self._register_check,
            "codegen": self._register_codegen,
            "deps": self._register_deps,
            "validate": self._register_validate,
            c.Infra.Directories.DOCS: self._register_docs,
            "github": self._register_github,
            "maintenance": self._register_maintenance,
            "refactor": self._register_refactor,
            c.Infra.ReportKeys.RELEASE: self._register_release,
            c.Infra.ReportKeys.WORKSPACE: self._register_workspace,
        })

    @staticmethod
    def _cli_settings() -> FlextCliSettings:
        """Return the shared CLI settings namespace without importing the API facade."""
        return FlextSettings.get_global().get_namespace("cli", FlextCliSettings)

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
            config=self._cli_settings(),
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

    @staticmethod
    def _register_basemk(app: t.Cli.CliApp) -> None:
        cli_module = importlib.import_module("flext_infra.basemk.cli")
        cli_module.FlextInfraCliBasemk().register_basemk(app)

    @staticmethod
    def _register_check(app: t.Cli.CliApp) -> None:
        cli_module = importlib.import_module("flext_infra.check.workspace_check_cli")
        cli_module.FlextInfraCliCheck().register_check(app)

    @staticmethod
    def _register_codegen(app: t.Cli.CliApp) -> None:
        cli_module = importlib.import_module("flext_infra.codegen.cli")
        cli_module.FlextInfraCliCodegen().register_codegen(app)

    @staticmethod
    def _register_deps(app: t.Cli.CliApp) -> None:
        cli_module = importlib.import_module("flext_infra.deps.cli")
        cli_module.FlextInfraCliDeps().register_deps(app)

    @staticmethod
    def _register_docs(app: t.Cli.CliApp) -> None:
        api_module = importlib.import_module("flext_infra.api")
        api_module.infra.register_docs(app)

    @staticmethod
    def _register_github(app: t.Cli.CliApp) -> None:
        cli_module = importlib.import_module("flext_infra.github.cli")
        service_module = importlib.import_module("flext_infra.services.github")

        class _GithubCli(
            cli_module.FlextInfraCliGithub,
            service_module.FlextInfraServiceGithubMixin,
        ):
            pass

        _GithubCli().register_github(app)

    @staticmethod
    def _register_maintenance(app: t.Cli.CliApp) -> None:
        cli_module = importlib.import_module("flext_infra.maintenance.cli")
        cli_module.FlextInfraCliMaintenance().register_maintenance(app)

    @staticmethod
    def _register_refactor(app: t.Cli.CliApp) -> None:
        cli_module = importlib.import_module("flext_infra.refactor.cli")
        cli_module.FlextInfraCliRefactor().register_refactor(app)

    @staticmethod
    def _register_release(app: t.Cli.CliApp) -> None:
        cli_module = importlib.import_module("flext_infra.release.cli")
        cli_module.FlextInfraCliRelease().register_release(app)

    @staticmethod
    def _register_validate(app: t.Cli.CliApp) -> None:
        cli_module = importlib.import_module("flext_infra.validate.cli")
        cli_module.FlextInfraCliValidate().register_validate(app)

    @staticmethod
    def _register_workspace(app: t.Cli.CliApp) -> None:
        cli_module = importlib.import_module("flext_infra.workspace.cli")
        service_module = importlib.import_module("flext_infra.services.workspace")

        class _WorkspaceCli(
            cli_module.FlextInfraCliWorkspace,
            service_module.FlextInfraServiceWorkspaceMixin,
        ):
            pass

        _WorkspaceCli().register_workspace(app)


def main(args: t.StrSequence | None = None) -> int:
    """Run the canonical flext-infra CLI."""
    return FlextInfraCli().main(args)


__all__ = ["FlextInfraCli", "main"]
