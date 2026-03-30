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
from typing import Annotated

from flext_cli import cli
from flext_core import FlextRuntime, r
from pydantic import BaseModel, Field

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

_DEFAULT_OUTPUT_DIR = f"{c.Infra.Reporting.REPORTS_DIR_NAME}/docs"

# ── Input Models ─────────────────────────────────────────────


class AuditInput(BaseModel):
    """CLI input for audit — fields become CLI options."""

    workspace: Annotated[
        str | None, Field(default=None, description="Workspace root directory")
    ]
    project: Annotated[
        str | None, Field(default=None, description="Single project name")
    ]
    projects: Annotated[
        str | None, Field(default=None, description="Comma-separated project names")
    ]
    check: Annotated[bool, Field(default=False, description="Enable check mode")]
    strict: Annotated[bool, Field(default=False, description="Strict mode")]
    output_dir: Annotated[
        str,
        Field(default=_DEFAULT_OUTPUT_DIR, description="Output directory for reports"),
    ]


class FixInput(BaseModel):
    """CLI input for fix — fields become CLI options."""

    workspace: Annotated[
        str | None, Field(default=None, description="Workspace root directory")
    ]
    project: Annotated[
        str | None, Field(default=None, description="Single project name")
    ]
    projects: Annotated[
        str | None, Field(default=None, description="Comma-separated project names")
    ]
    apply: Annotated[bool, Field(default=False, description="Apply changes")]
    output_dir: Annotated[
        str,
        Field(default=_DEFAULT_OUTPUT_DIR, description="Output directory for reports"),
    ]


class BuildInput(BaseModel):
    """CLI input for build — fields become CLI options."""

    workspace: Annotated[
        str | None, Field(default=None, description="Workspace root directory")
    ]
    project: Annotated[
        str | None, Field(default=None, description="Single project name")
    ]
    projects: Annotated[
        str | None, Field(default=None, description="Comma-separated project names")
    ]
    output_dir: Annotated[
        str,
        Field(default=_DEFAULT_OUTPUT_DIR, description="Output directory for reports"),
    ]


class GenerateInput(BaseModel):
    """CLI input for generate — fields become CLI options."""

    workspace: Annotated[
        str | None, Field(default=None, description="Workspace root directory")
    ]
    project: Annotated[
        str | None, Field(default=None, description="Single project name")
    ]
    projects: Annotated[
        str | None, Field(default=None, description="Comma-separated project names")
    ]
    apply: Annotated[bool, Field(default=False, description="Apply changes")]
    output_dir: Annotated[
        str,
        Field(default=_DEFAULT_OUTPUT_DIR, description="Output directory for reports"),
    ]


class ValidateInput(BaseModel):
    """CLI input for validate — fields become CLI options."""

    workspace: Annotated[
        str | None, Field(default=None, description="Workspace root directory")
    ]
    project: Annotated[
        str | None, Field(default=None, description="Single project name")
    ]
    projects: Annotated[
        str | None, Field(default=None, description="Comma-separated project names")
    ]
    apply: Annotated[bool, Field(default=False, description="Apply changes")]
    check: Annotated[bool, Field(default=False, description="Enable check mode")]
    output_dir: Annotated[
        str,
        Field(default=_DEFAULT_OUTPUT_DIR, description="Output directory for reports"),
    ]


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
                model_cls=AuditInput,
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
                model_cls=FixInput,
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
                model_cls=BuildInput,
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
                model_cls=GenerateInput,
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
                model_cls=ValidateInput,
                handler=self._handle_validate,
                success_message="Validate completed successfully",
                failure_message="Validate failed",
            ),
        )

    @staticmethod
    def _handle_audit(params: AuditInput) -> r[bool]:
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
    def _handle_fix(params: FixInput) -> r[bool]:
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
    def _handle_build(params: BuildInput) -> r[bool]:
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
    def _handle_generate(params: GenerateInput) -> r[bool]:
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
    def _handle_validate(params: ValidateInput) -> r[bool]:
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
