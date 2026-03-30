"""CLI mixin for validate commands."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import cli
from flext_core import r

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

if TYPE_CHECKING:
    import typer


def _list_str(
    payload: m.Infra.InventoryReport | m.Infra.PytestDiagnostics,
    key: str,
) -> t.StrSequence:
    """Extract string list from payload attribute."""
    return [item for item in getattr(payload, key, []) if isinstance(item, str)]


class FlextInfraCliValidate:
    """Validate CLI group — composed into FlextInfraCli via MRO."""

    def register_validate(self, app: typer.Typer) -> None:
        """Register validate commands on the given Typer app."""
        cli.register_result_route(
            app,
            route=m.Cli.ResultCommandRouteModel(
                name="basemk-validate",
                help_text="Validate base.mk sync",
                model_cls=m.Infra.ValidateBaseMkInput,
                handler=self._handle_basemk_validate,
                success_message="base.mk validation passed",
                failure_message="base.mk validation failed",
            ),
        )
        cli.register_result_route(
            app,
            route=m.Cli.ResultCommandRouteModel(
                name="inventory",
                help_text="Generate scripts inventory",
                model_cls=m.Infra.ValidateInventoryInput,
                handler=self._handle_inventory,
                success_message="Inventory generated successfully",
                failure_message="Inventory generation failed",
            ),
        )
        cli.register_result_route(
            app,
            route=m.Cli.ResultCommandRouteModel(
                name="pytest-diag",
                help_text="Extract pytest diagnostics from JUnit and log files",
                model_cls=m.Infra.ValidatePytestDiagInput,
                handler=self._handle_pytest_diag,
                success_message="Pytest diagnostics extracted",
                failure_message="Pytest diagnostics extraction failed",
            ),
        )
        cli.register_result_route(
            app,
            route=m.Cli.ResultCommandRouteModel(
                name="scan",
                help_text="Scan text files for patterns",
                model_cls=m.Infra.ValidateScanInput,
                handler=self._handle_scan,
                success_message="Scan completed with no violations",
                failure_message="Scan failed",
            ),
        )
        cli.register_result_route(
            app,
            route=m.Cli.ResultCommandRouteModel(
                name="skill-validate",
                help_text="Validate a skill",
                model_cls=m.Infra.ValidateSkillValidateInput,
                handler=self._handle_skill_validate,
                success_message="Skill validation passed",
                failure_message="Skill validation failed",
            ),
        )
        cli.register_result_route(
            app,
            route=m.Cli.ResultCommandRouteModel(
                name="stub-validate",
                help_text="Validate stub supply chain",
                model_cls=m.Infra.ValidateStubValidateInput,
                handler=self._handle_stub_validate,
                success_message="Stub validation passed",
                failure_message="Stub validation failed",
            ),
        )

    @staticmethod
    def _handle_basemk_validate(params: m.Infra.ValidateBaseMkInput) -> r[bool]:
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
    def _handle_inventory(params: m.Infra.ValidateInventoryInput) -> r[bool]:
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
    def _handle_pytest_diag(params: m.Infra.ValidatePytestDiagInput) -> r[bool]:
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
    def _handle_scan(params: m.Infra.ValidateScanInput) -> r[bool]:
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
    def _handle_skill_validate(
        params: m.Infra.ValidateSkillValidateInput,
    ) -> r[bool]:
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
    def _handle_stub_validate(
        params: m.Infra.ValidateStubValidateInput,
    ) -> r[bool]:
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
