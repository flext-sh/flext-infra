"""CLI entrypoint for the canonical flext-infra command surface."""

from __future__ import annotations

import sys
from types import MappingProxyType
from typing import ClassVar

from flext_cli import FlextCli, FlextCliSettings
from flext_core import FlextSettings
from flext_infra import (
    FlextInfraAccessorMigrationOrchestrator,
    FlextInfraBaseMkGenerator,
    FlextInfraBaseMkValidator,
    FlextInfraCodegenCensus,
    FlextInfraCodegenConsolidator,
    FlextInfraCodegenFixer,
    FlextInfraCodegenLazyInit,
    FlextInfraCodegenPipeline,
    FlextInfraCodegenPyprojectKeys,
    FlextInfraCodegenPyTyped,
    FlextInfraCodegenQualityGate,
    FlextInfraCodegenScaffolder,
    FlextInfraCodegenVersionFile,
    FlextInfraConfigFixer,
    FlextInfraDocAuditor,
    FlextInfraDocBuilder,
    FlextInfraDocFixer,
    FlextInfraDocGenerator,
    FlextInfraDocValidator,
    FlextInfraExtraPathsManager,
    FlextInfraInternalDependencySyncService,
    FlextInfraInventoryService,
    FlextInfraNamespaceEnforcer,
    FlextInfraOrchestratorService,
    FlextInfraProjectMigrator,
    FlextInfraPyprojectModernizer,
    FlextInfraPytestDiagExtractor,
    FlextInfraPythonVersionEnforcer,
    FlextInfraRefactorCensus,
    FlextInfraRefactorMigrateToClassMRO,
    FlextInfraReleaseOrchestrator,
    FlextInfraRuntimeDevDependencyDetector,
    FlextInfraSilentFailureValidator,
    FlextInfraSkillValidator,
    FlextInfraStubSupplyChain,
    FlextInfraSyncService,
    FlextInfraTextPatternScanner,
    FlextInfraValidateFreshImport,
    FlextInfraValidateImportCycles,
    FlextInfraValidateLazyMapFreshness,
    FlextInfraValidateMetadataDiscipline,
    FlextInfraValidateTierWhitelist,
    FlextInfraWorkspaceChecker,
    FlextInfraWorkspaceDetector,
    c,
    m,
    t,
    u,
)
from flext_infra.refactor.wrapper_root_namespace import (
    FlextInfraWrapperRootNamespaceRefactor,
)


class FlextInfraCli(FlextCli):
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
        "--module",
        "--namespace",
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
    GROUPS: ClassVar[t.StrMapping] = MappingProxyType({
        c.Infra.CLI_GROUP_BASEMK: "Base.mk template generation",
        c.Infra.CLI_GROUP_CHECK: "Lint gates and pyrefly settings management",
        c.Infra.CLI_GROUP_CODEGEN: "Code generation and workspace standardization",
        c.Infra.CLI_GROUP_VALIDATE: "Infrastructure validators and diagnostics",
        c.Infra.CLI_GROUP_DEPS: "Dependency detection, sync, and modernization",
        c.Infra.CLI_GROUP_DOCS: "Documentation audit, fix, build, generate, validate",
        c.Infra.CLI_GROUP_GITHUB: "GitHub workflows, linting, and PR automation",
        c.Infra.CLI_GROUP_MAINTENANCE: "Python version enforcement",
        c.Infra.CLI_GROUP_REFACTOR: "Declarative refactoring and modernization",
        c.Infra.CLI_GROUP_RELEASE: "Release orchestration",
        c.Infra.CLI_GROUP_WORKSPACE: "Workspace detection, sync, orchestration, migration",
    })
    _GROUP_COMMANDS: ClassVar[dict[str, tuple[m.Cli.ResultCommandRoute, ...]]] = {
        c.Infra.CLI_GROUP_BASEMK: (
            m.Cli.ResultCommandRoute(
                name="generate",
                help_text="Generate base.mk content from the canonical template",
                model_cls=FlextInfraBaseMkGenerator,
                handler=lambda params: params.execute(),
                success_message="base.mk generation complete",
            ),
        ),
        c.Infra.CLI_GROUP_CHECK: (
            m.Cli.ResultCommandRoute(
                name=c.Infra.VERB_RUN,
                help_text="Run workspace quality gates",
                model_cls=m.Infra.RunCommand,
                handler=lambda params: FlextInfraWorkspaceChecker.execute_command(
                    params
                ),
            ),
            m.Cli.ResultCommandRoute(
                name="fix-pyrefly-settings",
                help_text="Repair [tool.pyrefly] blocks",
                model_cls=m.Infra.FixPyreflyConfigCommand,
                handler=lambda params: FlextInfraConfigFixer.execute_command(params),
            ),
        ),
        c.Infra.CLI_GROUP_CODEGEN: tuple(
            m.Cli.ResultCommandRoute(
                name=route_name,
                help_text=help_text,
                model_cls=model_cls,
                handler=lambda params, mc=model_cls: mc.execute_command(params),
                success_message=success_message,
            )
            for route_name, help_text, model_cls, success_message in (
                (
                    "init",
                    "Generate/refresh PEP 562 lazy-import __init__.py files",
                    FlextInfraCodegenLazyInit,
                    "init complete",
                ),
                (
                    "census",
                    "Count namespace violations across workspace projects",
                    FlextInfraCodegenCensus,
                    None,
                ),
                (
                    "scaffold",
                    "Generate missing base modules in src/ and tests/",
                    FlextInfraCodegenScaffolder,
                    None,
                ),
                (
                    "auto-fix",
                    "Auto-fix namespace violations (move Finals/TypeVars)",
                    FlextInfraCodegenFixer,
                    None,
                ),
                (
                    "py-typed",
                    "Create/remove PEP 561 py.typed markers",
                    FlextInfraCodegenPyTyped,
                    "py-typed markers updated",
                ),
                (
                    "pipeline",
                    "Run full codegen pipeline",
                    FlextInfraCodegenPipeline,
                    None,
                ),
                (
                    "constants-quality-gate",
                    "Run constants migration quality gate",
                    FlextInfraCodegenQualityGate,
                    "constants quality gate passed",
                ),
                (
                    "consolidate",
                    "Consolidate inline constants into c.Infra.* references",
                    FlextInfraCodegenConsolidator,
                    None,
                ),
                (
                    "pyproject-keys",
                    "Generate [tool.flext.*] tables in pyproject.toml",
                    FlextInfraCodegenPyprojectKeys,
                    "pyproject-keys generation complete",
                ),
                (
                    "version-file",
                    "Generate __version__.py from project-metadata SSOT",
                    FlextInfraCodegenVersionFile,
                    "version-file generation complete",
                ),
            )
        ),
        c.Infra.CLI_GROUP_DEPS: (
            *(
                m.Cli.ResultCommandRoute(
                    name=route_name,
                    help_text=help_text,
                    model_cls=model_cls,
                    handler=lambda params, mc=model_cls: mc.execute_command(params),
                )
                for route_name, help_text, model_cls in (
                    (
                        "detect",
                        "Detect runtime vs dev dependencies",
                        FlextInfraRuntimeDevDependencyDetector,
                    ),
                    (
                        "extra-paths",
                        "Synchronize pyright/mypy extraPaths",
                        FlextInfraExtraPathsManager,
                    ),
                    (
                        "internal-sync",
                        "Synchronize internal FLEXT dependencies",
                        FlextInfraInternalDependencySyncService,
                    ),
                    (
                        "modernize",
                        "Modernize workspace pyproject files",
                        FlextInfraPyprojectModernizer,
                    ),
                )
            ),
            # path-sync uses ``u.Infra.execute_command`` instead of the model's
            # own classmethod (single-callable contract owned by utilities).
            m.Cli.ResultCommandRoute(
                name="path-sync",
                help_text="Rewrite internal FLEXT dependency paths",
                model_cls=m.Infra.PathSyncCommand,
                handler=lambda params: u.Infra.execute_command(params),
            ),
        ),
        c.Infra.CLI_GROUP_DOCS: tuple(
            m.Cli.ResultCommandRoute(
                name=route_name,
                help_text=help_text,
                model_cls=model_cls,
                handler=lambda params, mc=model_cls: mc.execute_command(params),
                success_message=success_message,
            )
            for route_name, help_text, model_cls, success_message in (
                (
                    "audit",
                    "Audit documentation for broken links and forbidden terms",
                    FlextInfraDocAuditor,
                    "Audit completed successfully",
                ),
                (
                    "fix",
                    "Fix documentation issues",
                    FlextInfraDocFixer,
                    "Fix completed successfully",
                ),
                (
                    "build",
                    "Build MkDocs sites",
                    FlextInfraDocBuilder,
                    "Build completed successfully",
                ),
                (
                    "generate",
                    "Generate project docs",
                    FlextInfraDocGenerator,
                    "Generate completed successfully",
                ),
                (
                    "validate",
                    "Validate documentation",
                    FlextInfraDocValidator,
                    "Validate completed successfully",
                ),
            )
        ),
        c.Infra.CLI_GROUP_GITHUB: (
            m.Cli.ResultCommandRoute(
                name="workflows",
                help_text="Sync GitHub workflow files across workspace",
                model_cls=m.Infra.GithubWorkflowSyncRequest,
                handler=u.Infra.sync_github_workflows,
            ),
            m.Cli.ResultCommandRoute(
                name=c.Infra.LINT_SECTION,
                help_text="Lint GitHub workflow files",
                model_cls=m.Infra.GithubWorkflowLintRequest,
                handler=u.Infra.lint_github_workflows,
            ),
            m.Cli.ResultCommandRoute(
                name=c.Infra.PR,
                help_text="Manage pull requests for a single project",
                model_cls=m.Infra.GithubPullRequestRequest,
                handler=u.Infra.run_github_pull_request,
            ),
            m.Cli.ResultCommandRoute(
                name="pr-workspace",
                help_text="Manage pull requests across workspace projects",
                model_cls=m.Infra.GithubPullRequestWorkspaceRequest,
                handler=u.Infra.run_github_workspace_pull_requests,
            ),
        ),
        c.Infra.CLI_GROUP_MAINTENANCE: (
            m.Cli.ResultCommandRoute(
                name=c.Infra.VERB_RUN,
                help_text="Enforce Python version constraints",
                model_cls=FlextInfraPythonVersionEnforcer,
                handler=lambda params: FlextInfraPythonVersionEnforcer.execute_command(
                    params
                ),
                success_message="Maintenance completed",
            ),
        ),
        c.Infra.CLI_GROUP_REFACTOR: (
            # ``migrate-mro`` and ``namespace-enforce`` register one input model
            # but dispatch to a different orchestrator's classmethod; the rest
            # follow the model_cls.execute_command default.
            m.Cli.ResultCommandRoute(
                name="migrate-mro",
                help_text="Migrate loose declarations into MRO facade classes",
                model_cls=m.Infra.RefactorMigrateMroInput,
                handler=lambda params: (
                    FlextInfraRefactorMigrateToClassMRO.execute_command(params)
                ),
            ),
            m.Cli.ResultCommandRoute(
                name="namespace-enforce",
                help_text="Scan workspace for namespace governance violations",
                model_cls=m.Infra.RefactorNamespaceEnforceInput,
                handler=lambda params: FlextInfraNamespaceEnforcer.execute_command(
                    params
                ),
            ),
            *(
                m.Cli.ResultCommandRoute(
                    name=route_name,
                    help_text=help_text,
                    model_cls=model_cls,
                    handler=lambda params, mc=model_cls: mc.execute_command(params),
                )
                for route_name, help_text, model_cls in (
                    (
                        "census",
                        "Run a Rope-only workspace census for Python objects",
                        FlextInfraRefactorCensus,
                    ),
                    (
                        "accessor-migrate",
                        "Preview or apply automated get_/set_/is_ migration",
                        FlextInfraAccessorMigrationOrchestrator,
                    ),
                )
            ),
            m.Cli.ResultCommandRoute(
                name="wrapper-root-namespace",
                help_text=(
                    "Normalize wrapper alias imports to wrapper root and "
                    "flatten *.Core.Tests paths"
                ),
                model_cls=FlextInfraWrapperRootNamespaceRefactor,
                handler=lambda params: params.execute(),
            ),
        ),
        c.Infra.CLI_GROUP_RELEASE: (
            m.Cli.ResultCommandRoute(
                name=c.Infra.VERB_RUN,
                help_text="Run release orchestration CLI flow",
                model_cls=FlextInfraReleaseOrchestrator,
                handler=lambda params: FlextInfraReleaseOrchestrator.execute_command(
                    params
                ),
                success_message="Release completed successfully",
            ),
        ),
        c.Infra.CLI_GROUP_VALIDATE: tuple(
            m.Cli.ResultCommandRoute(
                name=route_name,
                help_text=help_text,
                model_cls=model_cls,
                handler=lambda params, mc=model_cls: mc.execute_command(params),
            )
            for route_name, help_text, model_cls in (
                (
                    "basemk-validate",
                    "Validate base.mk sync",
                    FlextInfraBaseMkValidator,
                ),
                (
                    "inventory",
                    "Generate scripts inventory",
                    FlextInfraInventoryService,
                ),
                (
                    "pytest-diag",
                    "Extract pytest diagnostics",
                    FlextInfraPytestDiagExtractor,
                ),
                (
                    "scan",
                    "Scan text files for patterns",
                    FlextInfraTextPatternScanner,
                ),
                (
                    "skill-validate",
                    "Validate a skill",
                    FlextInfraSkillValidator,
                ),
                (
                    "silent-failure",
                    "Validate silent failure sentinel returns",
                    FlextInfraSilentFailureValidator,
                ),
                (
                    "stub-validate",
                    "Validate stub supply chain",
                    FlextInfraStubSupplyChain,
                ),
                (
                    "fresh-import",
                    "Guard 7: fresh-process import smoke test",
                    FlextInfraValidateFreshImport,
                ),
                (
                    "import-cycles",
                    "Guard 1: ROPE-backed import cycle detector",
                    FlextInfraValidateImportCycles,
                ),
                (
                    "lazy-map-freshness",
                    "Guard 2/3: lazy-map freshness validator",
                    FlextInfraValidateLazyMapFreshness,
                ),
                (
                    "tier-whitelist",
                    "Guard 5: tier-whitelist/abstraction-boundary enforcer",
                    FlextInfraValidateTierWhitelist,
                ),
                (
                    "metadata-discipline",
                    "Guard 8: centralized metadata parser discipline",
                    FlextInfraValidateMetadataDiscipline,
                ),
            )
        ),
        c.Infra.CLI_GROUP_WORKSPACE: tuple(
            m.Cli.ResultCommandRoute(
                name=route_name,
                help_text=help_text,
                model_cls=model_cls,
                handler=lambda params, mc=model_cls: mc.execute_command(params),
            )
            for route_name, help_text, model_cls in (
                (
                    "detect",
                    "Detect workspace or standalone mode",
                    FlextInfraWorkspaceDetector,
                ),
                (
                    "sync",
                    "Sync base.mk to project root",
                    FlextInfraSyncService,
                ),
                (
                    "orchestrate",
                    "Run make verb across projects",
                    FlextInfraOrchestratorService,
                ),
                (
                    "migrate",
                    "Migrate workspace projects to flext_infra tooling",
                    FlextInfraProjectMigrator,
                ),
            )
        ),
    }

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
            self.display_message(
                f"unknown group '{group}'",
                c.Cli.MessageTypes.ERROR,
            )
            self.print_help()
            return 1
        return self._run_group(group, group_args)

    def print_help(self) -> None:
        """Display the canonical command groups."""
        self.display_message(
            "Usage: flext-infra <group> [subcommand] [args...]",
            c.Cli.MessageTypes.INFO,
        )
        self.display_message("Groups", c.Cli.MessageTypes.INFO)
        for group in sorted(self.GROUPS):
            self.display_message(
                f"  {group:<16}{self.GROUPS[group]}",
                c.Cli.MessageTypes.INFO,
            )

    def _normalize_group_args(self, args: t.StrSequence) -> list[str]:
        reordered: list[str] = u.Cli.reorder_prefixed_options(
            args,
            bool_options=tuple(self._SHARED_BOOL_FLAGS),
            value_options=tuple(self._SHARED_VALUE_FLAGS),
        )
        return reordered

    def _register_group_commands(self, group: str, app: t.Cli.CliApp) -> None:
        self.register_result_routes(app, self._GROUP_COMMANDS[group])

    def _run_group(self, group: str, args: t.StrSequence) -> int:
        """Execute a registered flext-cli group."""
        app = self.create_app_with_common_params(
            name=f"{self.app_name} {group}",
            help_text=self.GROUPS[group],
            settings=self._cli_settings(),
        )
        self._register_group_commands(group, app)
        normalized_args = self._normalize_group_args(args)
        if not normalized_args:
            _ = self.execute_app(
                app,
                prog_name=f"{self.app_name} {group}",
                args=["--help"],
            )
            return 1
        result = self.execute_app(
            app,
            prog_name=f"{self.app_name} {group}",
            args=normalized_args,
        )
        if result.success:
            return 0
        error_message = result.error
        if error_message:
            self.display_message(
                error_message,
                c.Cli.MessageTypes.ERROR,
            )
        return 2 if error_message and u.Cli.cli_usage_error(error_message) else 1


def main(args: t.StrSequence | None = None) -> int:
    """Run the canonical flext-infra CLI."""
    cli_args = list(args) if args is not None else sys.argv[1:]
    return FlextInfraCli().main(cli_args)


__all__: list[str] = ["FlextInfraCli", "main"]
