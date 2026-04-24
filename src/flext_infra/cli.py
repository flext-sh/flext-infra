"""CLI entrypoint for the canonical flext-infra command surface."""

from __future__ import annotations

import sys
from types import MappingProxyType
from typing import ClassVar

from flext_cli import FlextCli, FlextCliSettings, u
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
    FlextInfraCodegenScaffolder,
    FlextInfraCodegenVersionFile,
    FlextInfraConfigFixer,
    FlextInfraConstantsCodegenQualityGate,
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
    FlextInfraUtilitiesDependencyPathSync,
    FlextInfraUtilitiesGithub,
    FlextInfraUtilitiesGithubPr,
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
)


def _route(
    *,
    handler: t.Cli.ResultRouteHandler,
    help_text: str,
    model_cls: type[m.BaseModel],
    name: str,
    success_message: str | None = None,
) -> m.Cli.ResultCommandRoute:
    return m.Cli.ResultCommandRoute(
        name=name,
        help_text=help_text,
        model_cls=model_cls,
        handler=handler,
        success_message=success_message,
    )


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
            _route(
                name="generate",
                help_text="Generate base.mk content from the canonical template",
                model_cls=FlextInfraBaseMkGenerator,
                handler=lambda params: params.execute(),
                success_message="base.mk generation complete",
            ),
        ),
        c.Infra.CLI_GROUP_CHECK: (
            _route(
                name=c.Infra.VERB_RUN,
                help_text="Run workspace quality gates",
                model_cls=m.Infra.RunCommand,
                handler=lambda params: FlextInfraWorkspaceChecker.execute_command(
                    params
                ),
            ),
            _route(
                name="fix-pyrefly-settings",
                help_text="Repair [tool.pyrefly] blocks",
                model_cls=m.Infra.FixPyreflyConfigCommand,
                handler=lambda params: FlextInfraConfigFixer.execute_command(params),
            ),
        ),
        c.Infra.CLI_GROUP_CODEGEN: (
            _route(
                name="init",
                help_text="Generate/refresh PEP 562 lazy-import __init__.py files",
                model_cls=FlextInfraCodegenLazyInit,
                handler=lambda params: FlextInfraCodegenLazyInit.execute_command(
                    params
                ),
                success_message="init complete",
            ),
            _route(
                name="census",
                help_text="Count namespace violations across workspace projects",
                model_cls=FlextInfraCodegenCensus,
                handler=lambda params: FlextInfraCodegenCensus.execute_command(params),
            ),
            _route(
                name="scaffold",
                help_text="Generate missing base modules in src/ and tests/",
                model_cls=FlextInfraCodegenScaffolder,
                handler=lambda params: FlextInfraCodegenScaffolder.execute_command(
                    params
                ),
            ),
            _route(
                name="auto-fix",
                help_text="Auto-fix namespace violations (move Finals/TypeVars)",
                model_cls=FlextInfraCodegenFixer,
                handler=lambda params: FlextInfraCodegenFixer.execute_command(params),
            ),
            _route(
                name="py-typed",
                help_text="Create/remove PEP 561 py.typed markers",
                model_cls=FlextInfraCodegenPyTyped,
                handler=lambda params: FlextInfraCodegenPyTyped.execute_command(params),
                success_message="py-typed markers updated",
            ),
            _route(
                name="pipeline",
                help_text="Run full codegen pipeline",
                model_cls=FlextInfraCodegenPipeline,
                handler=lambda params: FlextInfraCodegenPipeline.execute_command(
                    params
                ),
            ),
            _route(
                name="constants-quality-gate",
                help_text="Run constants migration quality gate",
                model_cls=FlextInfraConstantsCodegenQualityGate,
                handler=lambda params: (
                    FlextInfraConstantsCodegenQualityGate.execute_command(params)
                ),
                success_message="constants quality gate passed",
            ),
            _route(
                name="consolidate",
                help_text="Consolidate inline constants into c.Infra.* references",
                model_cls=FlextInfraCodegenConsolidator,
                handler=lambda params: FlextInfraCodegenConsolidator.execute_command(
                    params
                ),
            ),
            _route(
                name="pyproject-keys",
                help_text="Generate [tool.flext.*] tables in pyproject.toml",
                model_cls=FlextInfraCodegenPyprojectKeys,
                handler=lambda params: FlextInfraCodegenPyprojectKeys.execute_command(
                    params
                ),
                success_message="pyproject-keys generation complete",
            ),
            _route(
                name="version-file",
                help_text="Generate __version__.py from project-metadata SSOT",
                model_cls=FlextInfraCodegenVersionFile,
                handler=lambda params: FlextInfraCodegenVersionFile.execute_command(
                    params
                ),
                success_message="version-file generation complete",
            ),
        ),
        c.Infra.CLI_GROUP_DEPS: (
            _route(
                name="detect",
                help_text="Detect runtime vs dev dependencies",
                model_cls=FlextInfraRuntimeDevDependencyDetector,
                handler=lambda params: (
                    FlextInfraRuntimeDevDependencyDetector.execute_command(params)
                ),
            ),
            _route(
                name="extra-paths",
                help_text="Synchronize pyright/mypy extraPaths",
                model_cls=FlextInfraExtraPathsManager,
                handler=lambda params: FlextInfraExtraPathsManager.execute_command(
                    params
                ),
            ),
            _route(
                name="internal-sync",
                help_text="Synchronize internal FLEXT dependencies",
                model_cls=FlextInfraInternalDependencySyncService,
                handler=lambda params: (
                    FlextInfraInternalDependencySyncService.execute_command(params)
                ),
            ),
            _route(
                name="modernize",
                help_text="Modernize workspace pyproject files",
                model_cls=FlextInfraPyprojectModernizer,
                handler=lambda params: FlextInfraPyprojectModernizer.execute_command(
                    params
                ),
            ),
            _route(
                name="path-sync",
                help_text="Rewrite internal FLEXT dependency paths",
                model_cls=m.Infra.PathSyncCommand,
                handler=lambda params: (
                    FlextInfraUtilitiesDependencyPathSync.execute_command(params)
                ),
            ),
        ),
        c.Infra.CLI_GROUP_DOCS: (
            _route(
                name="audit",
                help_text="Audit documentation for broken links and forbidden terms",
                model_cls=FlextInfraDocAuditor,
                handler=lambda params: FlextInfraDocAuditor.execute_command(params),
                success_message="Audit completed successfully",
            ),
            _route(
                name="fix",
                help_text="Fix documentation issues",
                model_cls=FlextInfraDocFixer,
                handler=lambda params: FlextInfraDocFixer.execute_command(params),
                success_message="Fix completed successfully",
            ),
            _route(
                name="build",
                help_text="Build MkDocs sites",
                model_cls=FlextInfraDocBuilder,
                handler=lambda params: FlextInfraDocBuilder.execute_command(params),
                success_message="Build completed successfully",
            ),
            _route(
                name="generate",
                help_text="Generate project docs",
                model_cls=FlextInfraDocGenerator,
                handler=lambda params: FlextInfraDocGenerator.execute_command(params),
                success_message="Generate completed successfully",
            ),
            _route(
                name="validate",
                help_text="Validate documentation",
                model_cls=FlextInfraDocValidator,
                handler=lambda params: FlextInfraDocValidator.execute_command(params),
                success_message="Validate completed successfully",
            ),
        ),
        c.Infra.CLI_GROUP_GITHUB: (
            _route(
                name="workflows",
                help_text="Sync GitHub workflow files across workspace",
                model_cls=m.Infra.GithubWorkflowSyncRequest,
                handler=FlextInfraUtilitiesGithub.sync_github_workflows,
            ),
            _route(
                name=c.Infra.LINT_SECTION,
                help_text="Lint GitHub workflow files",
                model_cls=m.Infra.GithubWorkflowLintRequest,
                handler=FlextInfraUtilitiesGithub.lint_github_workflows,
            ),
            _route(
                name=c.Infra.PR,
                help_text="Manage pull requests for a single project",
                model_cls=m.Infra.GithubPullRequestRequest,
                handler=FlextInfraUtilitiesGithubPr.run_github_pull_request,
            ),
            _route(
                name="pr-workspace",
                help_text="Manage pull requests across workspace projects",
                model_cls=m.Infra.GithubPullRequestWorkspaceRequest,
                handler=FlextInfraUtilitiesGithubPr.run_github_workspace_pull_requests,
            ),
        ),
        c.Infra.CLI_GROUP_MAINTENANCE: (
            _route(
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
            _route(
                name="migrate-mro",
                help_text="Migrate loose declarations into MRO facade classes",
                model_cls=m.Infra.RefactorMigrateMroInput,
                handler=lambda params: (
                    FlextInfraRefactorMigrateToClassMRO.execute_command(params)
                ),
            ),
            _route(
                name="namespace-enforce",
                help_text="Scan workspace for namespace governance violations",
                model_cls=m.Infra.RefactorNamespaceEnforceInput,
                handler=lambda params: FlextInfraNamespaceEnforcer.execute_command(
                    params
                ),
            ),
            _route(
                name="census",
                help_text="Run a Rope-only workspace census for Python objects",
                model_cls=FlextInfraRefactorCensus,
                handler=lambda params: FlextInfraRefactorCensus.execute_command(params),
            ),
            _route(
                name="accessor-migrate",
                help_text="Preview or apply automated get_/set_/is_ migration",
                model_cls=FlextInfraAccessorMigrationOrchestrator,
                handler=lambda params: (
                    FlextInfraAccessorMigrationOrchestrator.execute_command(params)
                ),
            ),
        ),
        c.Infra.CLI_GROUP_RELEASE: (
            _route(
                name=c.Infra.VERB_RUN,
                help_text="Run release orchestration CLI flow",
                model_cls=FlextInfraReleaseOrchestrator,
                handler=lambda params: FlextInfraReleaseOrchestrator.execute_command(
                    params
                ),
                success_message="Release completed successfully",
            ),
        ),
        c.Infra.CLI_GROUP_VALIDATE: (
            _route(
                name="basemk-validate",
                help_text="Validate base.mk sync",
                model_cls=FlextInfraBaseMkValidator,
                handler=lambda params: FlextInfraBaseMkValidator.execute_command(
                    params
                ),
            ),
            _route(
                name="inventory",
                help_text="Generate scripts inventory",
                model_cls=FlextInfraInventoryService,
                handler=lambda params: FlextInfraInventoryService.execute_command(
                    params
                ),
            ),
            _route(
                name="pytest-diag",
                help_text="Extract pytest diagnostics",
                model_cls=FlextInfraPytestDiagExtractor,
                handler=lambda params: FlextInfraPytestDiagExtractor.execute_command(
                    params
                ),
            ),
            _route(
                name="scan",
                help_text="Scan text files for patterns",
                model_cls=FlextInfraTextPatternScanner,
                handler=lambda params: FlextInfraTextPatternScanner.execute_command(
                    params
                ),
            ),
            _route(
                name="skill-validate",
                help_text="Validate a skill",
                model_cls=FlextInfraSkillValidator,
                handler=lambda params: FlextInfraSkillValidator.execute_command(params),
            ),
            _route(
                name="silent-failure",
                help_text="Validate silent failure sentinel returns",
                model_cls=FlextInfraSilentFailureValidator,
                handler=lambda params: FlextInfraSilentFailureValidator.execute_command(
                    params
                ),
            ),
            _route(
                name="stub-validate",
                help_text="Validate stub supply chain",
                model_cls=FlextInfraStubSupplyChain,
                handler=lambda params: FlextInfraStubSupplyChain.execute_command(
                    params
                ),
            ),
            _route(
                name="fresh-import",
                help_text="Guard 7: fresh-process import smoke test",
                model_cls=FlextInfraValidateFreshImport,
                handler=lambda params: FlextInfraValidateFreshImport.execute_command(
                    params
                ),
            ),
            _route(
                name="import-cycles",
                help_text="Guard 1: ROPE-backed import cycle detector",
                model_cls=FlextInfraValidateImportCycles,
                handler=lambda params: FlextInfraValidateImportCycles.execute_command(
                    params
                ),
            ),
            _route(
                name="lazy-map-freshness",
                help_text="Guard 2/3: lazy-map freshness validator",
                model_cls=FlextInfraValidateLazyMapFreshness,
                handler=lambda params: (
                    FlextInfraValidateLazyMapFreshness.execute_command(params)
                ),
            ),
            _route(
                name="tier-whitelist",
                help_text="Guard 5: tier-whitelist/abstraction-boundary enforcer",
                model_cls=FlextInfraValidateTierWhitelist,
                handler=lambda params: FlextInfraValidateTierWhitelist.execute_command(
                    params
                ),
            ),
            _route(
                name="metadata-discipline",
                help_text="Guard 8: centralized metadata parser discipline",
                model_cls=FlextInfraValidateMetadataDiscipline,
                handler=lambda params: (
                    FlextInfraValidateMetadataDiscipline.execute_command(params)
                ),
            ),
        ),
        c.Infra.CLI_GROUP_WORKSPACE: (
            _route(
                name="detect",
                help_text="Detect workspace or standalone mode",
                model_cls=FlextInfraWorkspaceDetector,
                handler=lambda params: FlextInfraWorkspaceDetector.execute_command(
                    params
                ),
            ),
            _route(
                name="sync",
                help_text="Sync base.mk to project root",
                model_cls=FlextInfraSyncService,
                handler=lambda params: FlextInfraSyncService.execute_command(params),
            ),
            _route(
                name="orchestrate",
                help_text="Run make verb across projects",
                model_cls=FlextInfraOrchestratorService,
                handler=lambda params: FlextInfraOrchestratorService.execute_command(
                    params
                ),
            ),
            _route(
                name="migrate",
                help_text="Migrate workspace projects to flext_infra tooling",
                model_cls=FlextInfraProjectMigrator,
                handler=lambda params: FlextInfraProjectMigrator.execute_command(
                    params
                ),
            ),
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
            self._CLI_SERVICE.display_message(
                f"unknown group '{group}'",
                c.Cli.MessageTypes.ERROR,
            )
            self.print_help()
            return 1
        return self._run_group(group, group_args)

    @classmethod
    def print_help(cls) -> None:
        """Display the canonical command groups."""
        cls._CLI_SERVICE.display_message(
            "Usage: flext-infra <group> [subcommand] [args...]",
            c.Cli.MessageTypes.INFO,
        )
        cls._CLI_SERVICE.display_message("Groups", c.Cli.MessageTypes.INFO)
        for group in sorted(cls.GROUPS):
            cls._CLI_SERVICE.display_message(
                f"  {group:<16}{cls.GROUPS[group]}",
                c.Cli.MessageTypes.INFO,
            )

    @classmethod
    def _normalize_group_args(cls, args: t.StrSequence) -> list[str]:
        reordered: list[str] = u.Cli.reorder_prefixed_options(
            args,
            bool_options=tuple(cls._SHARED_BOOL_FLAGS),
            value_options=tuple(cls._SHARED_VALUE_FLAGS),
        )
        return reordered

    def _register_group_commands(self, group: str, app: t.Cli.CliApp) -> None:
        self._CLI_SERVICE.register_result_routes(app, self._GROUP_COMMANDS[group])

    def _run_group(self, group: str, args: t.StrSequence) -> int:
        """Execute a registered flext-cli group."""
        app = self._CLI_SERVICE.create_app_with_common_params(
            name=f"{self.app_name} {group}",
            help_text=self.GROUPS[group],
            settings=self._cli_settings(),
        )
        self._register_group_commands(group, app)
        normalized_args = self._normalize_group_args(args)
        if not normalized_args:
            _ = self._CLI_SERVICE.execute_app(
                app,
                prog_name=f"{self.app_name} {group}",
                args=["--help"],
            )
            return 1
        result = self._CLI_SERVICE.execute_app(
            app,
            prog_name=f"{self.app_name} {group}",
            args=normalized_args,
        )
        if result.success:
            return 0
        error_message = result.error
        if error_message:
            self._CLI_SERVICE.display_message(
                error_message,
                c.Cli.MessageTypes.ERROR,
            )
        return 2 if error_message and u.Cli.cli_usage_error(error_message) else 1


def main(args: t.StrSequence | None = None) -> int:
    """Run the canonical flext-infra CLI."""
    return FlextInfraCli().main(args)


__all__: list[str] = ["FlextInfraCli", "main"]
