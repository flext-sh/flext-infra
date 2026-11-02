"""Documentation, GitHub workflow, maintenance, and validation CLI route ownership.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import c, docs, infra, m, maintenance, services, u
from flext_infra.docs.auditor import FlextInfraDocAuditor


class FlextInfraValidationRoutes:
    """Own documentation, GitHub workflow, maintenance, and validation routes."""

    @staticmethod
    def routes_for(group: str) -> tuple[m.Cli.ResultCommandRoute, ...]:
        """Construct only the selected public command family.

        Returns:
            Every declared route of the selected family.

        Raises:
            KeyError: If this owner does not declare the family.

        """
        if group == c.Infra.CLI_GROUP_VALIDATE:
            return services.FlextInfraValidationCommandRoutes.validate_command_routes
        if group == c.Infra.CLI_GROUP_DOCS:
            return (
                m.Cli.ResultCommandRoute(
                    name="collect",
                    help_text=(
                        "Collect associated plan sources "
                        "and publish authenticated projections"
                    ),
                    model_cls=m.Infra.DocsCollectRequest,
                    handler=docs.FlextInfraDocCollector.collect,
                    success_message="Configured plan sources collected and published",
                ),
                m.Cli.ResultCommandRoute(
                    name="generate",
                    help_text="Generate project docs through the publication "
                    "transaction",
                    model_cls=m.Infra.DocsGenerateRequest,
                    handler=docs.FlextInfraDocGenerator.execute_request,
                    success_formatter=lambda reports: (
                        u.Cli.json_dumps(u.normalize_to_json_value(reports)).value
                    ),
                    success_message="Generated documentation committed and verified",
                ),
                m.Cli.ResultCommandRoute(
                    name="fmt",
                    help_text=(
                        "Format documentation through the canonical markdown-format "
                        "gate"
                    ),
                    model_cls=docs.FlextInfraDocFormatter,
                    handler=infra.docs_format,
                    success_message="Format completed successfully",
                ),
                *tuple(
                    m.Cli.ResultCommandRoute(
                        name=route_name,
                        help_text=help_text,
                        model_cls=model_cls,
                        handler=model_cls.execute_command,
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
                            docs.FlextInfraDocFixer,
                            "Fix completed successfully",
                        ),
                        (
                            "build",
                            "Build MkDocs sites",
                            docs.FlextInfraDocBuilder,
                            "Build completed successfully",
                        ),
                        (
                            "serve",
                            "Serve one MkDocs site in dev mode (blocking preview)",
                            docs.FlextInfraDocServer,
                            "Serve completed successfully",
                        ),
                        (
                            "validate",
                            "Validate documentation",
                            docs.FlextInfraDocValidator,
                            "Validate completed successfully",
                        ),
                    )
                ),
            )
        if group == c.Infra.CLI_GROUP_MAINTENANCE:
            return (
                m.Cli.ResultCommandRoute(
                    name=c.Infra.VERB_RUN,
                    help_text="Enforce Python version constraints",
                    model_cls=maintenance.FlextInfraMaintenancePythonVersion,
                    handler=(
                        maintenance.FlextInfraMaintenancePythonVersion.execute_command
                    ),
                    success_message="Maintenance completed",
                ),
                m.Cli.ResultCommandRoute(
                    name=c.Infra.VERB_CLEAN,
                    help_text=(
                        "Report or remove declared disposables owned by this repository"
                    ),
                    model_cls=maintenance.FlextInfraMaintenanceClean,
                    handler=maintenance.FlextInfraMaintenanceClean.execute_command,
                    success_message="Clean completed",
                ),
                m.Cli.ResultCommandRoute(
                    name=c.Infra.VERB_SONARCLOUD_SYNC,
                    help_text=(
                        "Write the SSOT SonarCloud issue exclusions to the server-side "
                        "project settings (requires SONAR_TOKEN)"
                    ),
                    model_cls=maintenance.FlextInfraMaintenanceSonarcloud,
                    handler=maintenance.FlextInfraMaintenanceSonarcloud.execute_command,
                    success_message="SonarCloud issue exclusions match the SSOT",
                ),
                m.Cli.ResultCommandRoute(
                    name=c.Infra.VERB_SONARCLOUD_ISSUES,
                    help_text=(
                        "Read unresolved new-code SonarCloud issues (requires "
                        "SONAR_TOKEN)"
                    ),
                    model_cls=maintenance.FlextInfraMaintenanceSonarcloudIssues,
                    handler=(
                        maintenance.FlextInfraMaintenanceSonarcloudIssues.execute_command
                    ),
                    success_message="SonarCloud issue search completed",
                ),
            )
        raise KeyError(group)


__all__: list[str] = ["FlextInfraValidationRoutes"]
