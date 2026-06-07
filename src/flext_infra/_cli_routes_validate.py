"""Validate-cluster CLI route definitions for flext-infra."""

from __future__ import annotations

from flext_infra import (
    FlextInfraBaseMkValidator,
    FlextInfraDocAuditor,
    FlextInfraDocBuilder,
    FlextInfraDocFixer,
    FlextInfraDocGenerator,
    FlextInfraDocValidator,
    FlextInfraInventoryService,
    FlextInfraManualCommandValidator,
    FlextInfraPytestDiagExtractor,
    FlextInfraPythonVersionEnforcer,
    FlextInfraSilentFailureValidator,
    FlextInfraSkillValidator,
    FlextInfraStubSupplyChain,
    FlextInfraTextPatternScanner,
    FlextInfraValidateFreshImport,
    FlextInfraValidateImportCycles,
    FlextInfraValidateLazyMapFreshness,
    FlextInfraValidateMetadataDiscipline,
    FlextInfraValidateTierWhitelist,
    c,
    m,
    u,
)

ROUTES: dict[str, tuple[m.Cli.ResultCommandRoute, ...]] = {
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
            (
                "manual-cmd",
                "Manual-command blocker (§5): pre-commit config drift gate",
                FlextInfraManualCommandValidator,
            ),
        )
    ),
}

__all__: list[str] = ["ROUTES"]
