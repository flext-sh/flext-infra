"""CLI entry point for core infrastructure services.

Usage:
    python -m flext_infra.validate basemk-validate [--workspace PATH]
    python -m flext_infra.validate inventory [--workspace PATH] [--output-dir PATH]
    python -m flext_infra.validate pytest-diag --junit PATH --log PATH
    python -m flext_infra.validate scan --workspace PATH --pattern REGEX
        --include GLOB [--exclude GLOB] [--match present|absent]
    python -m flext_infra.validate skill-validate --skill NAME [--workspace PATH]
        [--mode baseline|strict]
    python -m flext_infra.validate stub-validate [--workspace PATH]

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
    FlextInfraBaseMkValidator,
    FlextInfraInventoryService,
    FlextInfraPytestDiagExtractor,
    FlextInfraSkillValidator,
    FlextInfraStubSupplyChain,
    FlextInfraTextPatternScanner,
    c,
    m,
    t,
    u,
)

# ── Helpers ──────────────────────────────────────────────────


def _list_str(
    payload: m.Infra.InventoryReport | m.Infra.PytestDiagnostics,
    key: str,
) -> t.StrSequence:
    """Extract string list from payload attribute."""
    return [item for item in getattr(payload, key, []) if isinstance(item, str)]


# ── Input Models ─────────────────────────────────────────────


class BaseMkValidateInput(BaseModel):
    """CLI input for basemk-validate — fields become CLI options."""

    workspace: Annotated[
        str | None, Field(default=None, description="Workspace root directory")
    ]


class InventoryInput(BaseModel):
    """CLI input for inventory — fields become CLI options."""

    workspace: Annotated[
        str | None, Field(default=None, description="Workspace root directory")
    ]
    output_dir: Annotated[
        str | None, Field(default=None, description="Output directory")
    ]


class PytestDiagInput(BaseModel):
    """CLI input for pytest-diag — fields become CLI options."""

    junit: Annotated[str, Field(..., description="JUnit XML path")]
    log: Annotated[str, Field(..., description="Pytest log path")]
    failed: Annotated[
        str | None, Field(default=None, description="Path to write failed cases")
    ]
    errors: Annotated[
        str | None, Field(default=None, description="Path to write error traces")
    ]
    warnings: Annotated[
        str | None, Field(default=None, description="Path to write warnings")
    ]
    slowest: Annotated[
        str | None, Field(default=None, description="Path to write slowest entries")
    ]
    skips: Annotated[
        str | None, Field(default=None, description="Path to write skipped cases")
    ]


class ScanInput(BaseModel):
    """CLI input for scan — fields become CLI options."""

    workspace: Annotated[
        str | None, Field(default=None, description="Workspace root directory")
    ]
    pattern: Annotated[str, Field(..., description="Regex pattern")]
    include: Annotated[
        list[str] | None, Field(default=None, description="Include glob")
    ]
    exclude: Annotated[
        list[str] | None, Field(default=None, description="Exclude glob")
    ]
    match: Annotated[
        str,
        Field(
            default=c.Infra.MatchModes.PRESENT,
            description="Violation mode (present or absent)",
        ),
    ]


class SkillValidateInput(BaseModel):
    """CLI input for skill-validate — fields become CLI options."""

    workspace: Annotated[
        str | None, Field(default=None, description="Workspace root directory")
    ]
    skill: Annotated[str, Field(..., description="Skill folder name")]
    mode: Annotated[
        str,
        Field(
            default=c.Infra.Modes.BASELINE,
            description="Validation mode (baseline or strict)",
        ),
    ]


class StubValidateInput(BaseModel):
    """CLI input for stub-validate — fields become CLI options."""

    workspace: Annotated[
        str | None, Field(default=None, description="Workspace root directory")
    ]
    project: Annotated[
        list[str] | None, Field(default=None, description="Project to validate")
    ]
    all_projects: Annotated[
        bool, Field(default=False, description="Validate all projects", alias="all")
    ]


# ── Router ───────────────────────────────────────────────────


class FlextInfraValidateCli:
    """Declarative CLI router for core infrastructure services."""

    def __init__(self) -> None:
        """Initialize CLI app and register declarative routes."""
        self._app = cli.create_app_with_common_params(
            name="validate",
            help_text="Core infrastructure services",
        )
        self._register_commands()

    def run(self, args: t.StrSequence | None = None) -> r[bool]:
        """Execute the CLI application."""
        return cli.execute_app(self._app, prog_name="validate", args=args)

    def _register_commands(self) -> None:
        cli.register_result_route(
            self._app,
            route=m.Cli.ResultCommandRouteModel(
                name="basemk-validate",
                help_text="Validate base.mk sync",
                model_cls=BaseMkValidateInput,
                handler=self._handle_basemk_validate,
                success_message="base.mk validation passed",
                failure_message="base.mk validation failed",
            ),
        )
        cli.register_result_route(
            self._app,
            route=m.Cli.ResultCommandRouteModel(
                name="inventory",
                help_text="Generate scripts inventory",
                model_cls=InventoryInput,
                handler=self._handle_inventory,
                success_message="Inventory generated successfully",
                failure_message="Inventory generation failed",
            ),
        )
        cli.register_result_route(
            self._app,
            route=m.Cli.ResultCommandRouteModel(
                name="pytest-diag",
                help_text="Extract pytest diagnostics from JUnit and log files",
                model_cls=PytestDiagInput,
                handler=self._handle_pytest_diag,
                success_message="Pytest diagnostics extracted",
                failure_message="Pytest diagnostics extraction failed",
            ),
        )
        cli.register_result_route(
            self._app,
            route=m.Cli.ResultCommandRouteModel(
                name="scan",
                help_text="Scan text files for patterns",
                model_cls=ScanInput,
                handler=self._handle_scan,
                success_message="Scan completed with no violations",
                failure_message="Scan failed",
            ),
        )
        cli.register_result_route(
            self._app,
            route=m.Cli.ResultCommandRouteModel(
                name="skill-validate",
                help_text="Validate a skill",
                model_cls=SkillValidateInput,
                handler=self._handle_skill_validate,
                success_message="Skill validation passed",
                failure_message="Skill validation failed",
            ),
        )
        cli.register_result_route(
            self._app,
            route=m.Cli.ResultCommandRouteModel(
                name="stub-validate",
                help_text="Validate stub supply chain",
                model_cls=StubValidateInput,
                handler=self._handle_stub_validate,
                success_message="Stub validation passed",
                failure_message="Stub validation failed",
            ),
        )

    @staticmethod
    def _handle_basemk_validate(params: BaseMkValidateInput) -> r[bool]:
        resolved_workspace = Path(params.workspace) if params.workspace else Path.cwd()
        validator = FlextInfraBaseMkValidator()
        result = validator.validate(resolved_workspace)
        if result.is_failure:
            return r[bool].fail(result.error or "unknown error")
        report: m.Infra.ValidationReport = result.value
        if not report.passed:
            return r[bool].fail(report.summary)
        return r[bool].ok(True)

    @staticmethod
    def _handle_inventory(params: InventoryInput) -> r[bool]:
        resolved_workspace = Path(params.workspace) if params.workspace else Path.cwd()
        service = FlextInfraInventoryService()
        output_dir_path = (
            Path(params.output_dir).resolve() if params.output_dir else None
        )
        result = service.generate(resolved_workspace, output_dir=output_dir_path)
        if result.is_failure:
            return r[bool].fail(result.error or "unknown error")
        return r[bool].ok(True)

    @staticmethod
    def _handle_pytest_diag(params: PytestDiagInput) -> r[bool]:
        extractor = FlextInfraPytestDiagExtractor()
        result = extractor.extract(Path(params.junit), Path(params.log))
        if result.is_failure:
            return r[bool].fail(result.error or "unknown error")
        data: m.Infra.PytestDiagnostics = result.value
        if params.failed:
            u.write_file(
                Path(params.failed),
                "\n\n".join(_list_str(data, "failed_cases")) + "\n",
                encoding=c.Infra.Encoding.DEFAULT,
            )
        if params.errors:
            u.write_file(
                Path(params.errors),
                "\n\n".join(_list_str(data, "error_traces")) + "\n",
                encoding=c.Infra.Encoding.DEFAULT,
            )
        if params.warnings:
            u.write_file(
                Path(params.warnings),
                "\n".join(_list_str(data, "warning_lines")) + "\n",
                encoding=c.Infra.Encoding.DEFAULT,
            )
        if params.slowest:
            u.write_file(
                Path(params.slowest),
                "\n".join(_list_str(data, "slow_entries")) + "\n",
                encoding=c.Infra.Encoding.DEFAULT,
            )
        if params.skips:
            u.write_file(
                Path(params.skips),
                "\n".join(_list_str(data, "skip_cases")) + "\n",
                encoding=c.Infra.Encoding.DEFAULT,
            )
        return r[bool].ok(True)

    @staticmethod
    def _handle_scan(params: ScanInput) -> r[bool]:
        resolved_workspace = Path(params.workspace) if params.workspace else Path.cwd()
        scanner = FlextInfraTextPatternScanner()
        result = scanner.scan(
            resolved_workspace,
            params.pattern,
            includes=params.include or [],
            excludes=params.exclude or [],
            match_mode=params.match,
        )
        if result.is_failure:
            return r[bool].fail(result.error or "unknown error")
        data: t.ConfigurationMapping = result.value
        violation_count = data.get("violation_count", 0)
        if isinstance(violation_count, int) and violation_count > 0:
            return r[bool].fail(f"Scan found {violation_count} violation(s)")
        return r[bool].ok(True)

    @staticmethod
    def _handle_skill_validate(params: SkillValidateInput) -> r[bool]:
        resolved_workspace = Path(params.workspace) if params.workspace else Path.cwd()
        validator = FlextInfraSkillValidator()
        result = validator.validate(resolved_workspace, params.skill, mode=params.mode)
        if result.is_failure:
            return r[bool].fail(result.error or "unknown error")
        report: m.Infra.ValidationReport = result.value
        if not report.passed:
            return r[bool].fail(report.summary)
        return r[bool].ok(True)

    @staticmethod
    def _handle_stub_validate(params: StubValidateInput) -> r[bool]:
        resolved_workspace = Path(params.workspace) if params.workspace else Path.cwd()
        chain = FlextInfraStubSupplyChain()
        effective_projects = None if params.all_projects else params.project
        project_dirs = (
            [resolved_workspace / project_name for project_name in effective_projects]
            if effective_projects
            else None
        )
        result = chain.validate(resolved_workspace, project_dirs=project_dirs)
        if result.is_failure:
            return r[bool].fail(result.error or "unknown error")
        report: m.Infra.ValidationReport = result.value
        if not report.passed:
            return r[bool].fail(report.summary)
        return r[bool].ok(True)


# ── Entry Point ──────────────────────────────────────────────


def main(argv: t.StrSequence | None = None) -> int:
    """Run core infrastructure services."""
    FlextRuntime.ensure_structlog_configured()
    result = FlextInfraValidateCli().run(argv)
    return 0 if result.is_success else 1


if __name__ == "__main__":
    sys.exit(main())
