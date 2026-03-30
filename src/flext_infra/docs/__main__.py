"""CLI entry point for documentation services.

Usage:
    python -m flext_infra docs audit --workspace flext-core
    python -m flext_infra docs fix --workspace flext-core --apply
    python -m flext_infra docs build --workspace flext-core
    python -m flext_infra docs generate --workspace flext-core --apply
    python -m flext_infra docs validate --workspace flext-core

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

from flext_cli import cli
from flext_core import FlextRuntime, r

from flext_infra import (
    FlextInfraDocAuditor,
    FlextInfraDocBuilder,
    FlextInfraDocFixer,
    FlextInfraDocGenerator,
    FlextInfraDocValidator,
    c,
    m,
    t,
)

# ── Router ───────────────────────────────────────────────────


class FlextInfraDocsCli:
    """Declarative CLI router for documentation services."""

    def __init__(self) -> None:
        """Initialize CLI app and register declarative routes."""
        self._app = cli.create_app_with_common_params(
            name="docs",
            help_text="Documentation management services",
        )
        self._register_commands()

    def run(self, args: t.StrSequence | None = None) -> r[bool]:
        """Execute the CLI application."""
        return cli.execute_app(self._app, prog_name="docs", args=args)

    def _register_commands(self) -> None:
        cli.register_result_route(
            self._app,
            route=m.Cli.ResultCommandRouteModel(
                name="audit",
                help_text="Audit documentation for broken links and forbidden terms",
                model_cls=m.Infra.DocsAuditInput,
                handler=self._handle_audit,
                success_message="Audit completed successfully",
                failure_message="Audit failed",
            ),
        )
        cli.register_result_route(
            self._app,
            route=m.Cli.ResultCommandRouteModel(
                name="fix",
                help_text="Fix documentation issues",
                model_cls=m.Infra.DocsFixInput,
                handler=self._handle_fix,
                success_message="Fix completed successfully",
                failure_message="Fix failed",
            ),
        )
        cli.register_result_route(
            self._app,
            route=m.Cli.ResultCommandRouteModel(
                name="build",
                help_text="Build MkDocs sites",
                model_cls=m.Infra.DocsBuildInput,
                handler=self._handle_build,
                success_message="Build completed successfully",
                failure_message="Build failed",
            ),
        )
        cli.register_result_route(
            self._app,
            route=m.Cli.ResultCommandRouteModel(
                name="generate",
                help_text="Generate project docs",
                model_cls=m.Infra.DocsGenerateInput,
                handler=self._handle_generate,
                success_message="Generate completed successfully",
                failure_message="Generate failed",
            ),
        )
        cli.register_result_route(
            self._app,
            route=m.Cli.ResultCommandRouteModel(
                name="validate",
                help_text="Validate documentation",
                model_cls=m.Infra.DocsValidateInput,
                handler=self._handle_validate,
                success_message="Validate completed successfully",
                failure_message="Validate failed",
            ),
        )

    @staticmethod
    def _handle_audit(params: m.Infra.DocsAuditInput) -> r[bool]:
        resolved_workspace = Path(params.workspace) if params.workspace else Path.cwd()
        auditor = FlextInfraDocAuditor()
        result = auditor.audit(
            workspace_root=resolved_workspace,
            project=params.project,
            projects=params.projects,
            output_dir=params.output_dir,
            check="all" if params.check else "",
            strict=params.strict,
        )
        if result.is_failure:
            return r[bool].fail(result.error or "audit failed")
        failures = sum(1 for report in result.value if not report.passed)
        if failures:
            return r[bool].fail(f"Audit found {failures} failure(s)")
        return r[bool].ok(True)

    @staticmethod
    def _handle_fix(params: m.Infra.DocsFixInput) -> r[bool]:
        resolved_workspace = Path(params.workspace) if params.workspace else Path.cwd()
        fixer = FlextInfraDocFixer()
        result = fixer.fix(
            workspace_root=resolved_workspace,
            project=params.project,
            projects=params.projects,
            output_dir=params.output_dir,
            apply=params.apply,
        )
        if result.is_failure:
            return r[bool].fail(result.error or "fix failed")
        return r[bool].ok(True)

    @staticmethod
    def _handle_build(params: m.Infra.DocsBuildInput) -> r[bool]:
        resolved_workspace = Path(params.workspace) if params.workspace else Path.cwd()
        builder = FlextInfraDocBuilder()
        result = builder.build(
            workspace_root=resolved_workspace,
            project=params.project,
            projects=params.projects,
            output_dir=params.output_dir,
        )
        if result.is_failure:
            return r[bool].fail(result.error or "build failed")
        failures = sum(
            1 for report in result.value if report.result == c.Infra.Status.FAIL
        )
        if failures:
            return r[bool].fail(f"Build had {failures} failure(s)")
        return r[bool].ok(True)

    @staticmethod
    def _handle_generate(params: m.Infra.DocsGenerateInput) -> r[bool]:
        resolved_workspace = Path(params.workspace) if params.workspace else Path.cwd()
        generator = FlextInfraDocGenerator()
        result = generator.generate(
            workspace_root=resolved_workspace,
            project=params.project,
            projects=params.projects,
            output_dir=params.output_dir,
            apply=params.apply,
        )
        if result.is_failure:
            return r[bool].fail(result.error or "generate failed")
        return r[bool].ok(True)

    @staticmethod
    def _handle_validate(params: m.Infra.DocsValidateInput) -> r[bool]:
        resolved_workspace = Path(params.workspace) if params.workspace else Path.cwd()
        validator = FlextInfraDocValidator()
        result = validator.validate(
            workspace_root=resolved_workspace,
            project=params.project,
            projects=params.projects,
            output_dir=params.output_dir,
            check="all" if params.check else "",
            apply=params.apply,
        )
        if result.is_failure:
            return r[bool].fail(result.error or "validate failed")
        failures = sum(
            1 for report in result.value if report.result == c.Infra.Status.FAIL
        )
        if failures:
            return r[bool].fail(f"Validate found {failures} failure(s)")
        return r[bool].ok(True)


# ── Entry Point ──────────────────────────────────────────────


def main(argv: t.StrSequence | None = None) -> int:
    """Entry point for documentation CLI."""
    FlextRuntime.ensure_structlog_configured()
    result = FlextInfraDocsCli().run(argv)
    return 0 if result.is_success else 1


if __name__ == "__main__":
    sys.exit(main())
