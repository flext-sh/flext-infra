"""Validation, docs, GitHub, and maintenance CLI routes for flext-infra.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import c, m, u
from flext_infra._constants.cli_routes_validate_commands import VALIDATE_COMMAND_ROUTES
from flext_infra.docs.auditor import FlextInfraDocAuditor
from flext_infra.docs.builder import FlextInfraDocBuilder
from flext_infra.docs.fixer import FlextInfraDocFixer
from flext_infra.docs.generator import FlextInfraDocGenerator
from flext_infra.docs.server import FlextInfraDocServer
from flext_infra.docs.validator import FlextInfraDocValidator
from flext_infra.maintenance.python_version import FlextInfraPythonVersionEnforcer

VALIDATE_ROUTES: dict[str, tuple[m.Cli.ResultCommandRoute, ...]] = {
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
                "serve",
                "Serve one MkDocs site in dev mode (blocking preview)",
                FlextInfraDocServer,
                "Serve completed successfully",
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
            handler=FlextInfraPythonVersionEnforcer.execute_command,
            success_message="Maintenance completed",
        ),
    ),
    c.Infra.CLI_GROUP_VALIDATE: VALIDATE_COMMAND_ROUTES,
}
__all__: list[str] = []
