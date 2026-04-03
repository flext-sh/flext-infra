"""CLI mixin for validate commands."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

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
    u,
)

if TYPE_CHECKING:
    import typer

_R = u.Infra.route  # shorthand


class FlextInfraCliValidate:
    """Validate CLI group — composed into FlextInfraCli via MRO."""

    def register_validate(self, app: typer.Typer) -> None:
        """Register validate commands on the given Typer app."""
        u.Infra.register_routes(
            app,
            [
                _R(
                    "basemk-validate",
                    "Validate base.mk sync",
                    m.Infra.ValidateBaseMkInput,
                    self._handle_basemk_validate,
                ),
                _R(
                    "inventory",
                    "Generate scripts inventory",
                    m.Infra.ValidateInventoryInput,
                    self._handle_inventory,
                ),
                _R(
                    "pytest-diag",
                    "Extract pytest diagnostics",
                    m.Infra.ValidatePytestDiagInput,
                    self._handle_pytest_diag,
                ),
                _R(
                    "scan",
                    "Scan text files for patterns",
                    m.Infra.ValidateScanInput,
                    self._handle_scan,
                ),
                _R(
                    "skill-validate",
                    "Validate a skill",
                    m.Infra.ValidateSkillValidateInput,
                    self._handle_skill_validate,
                ),
                _R(
                    "stub-validate",
                    "Validate stub supply chain",
                    m.Infra.ValidateStubValidateInput,
                    self._handle_stub_validate,
                ),
            ],
        )

    @staticmethod
    def _handle_basemk_validate(params: m.Infra.ValidateBaseMkInput) -> r[bool]:
        return (
            FlextInfraBaseMkValidator()
            .validate(u.Infra.resolve_workspace(params))
            .flat_map(u.Infra.check_report)
        )

    @staticmethod
    def _handle_inventory(params: m.Infra.ValidateInventoryInput) -> r[bool]:
        ws = u.Infra.resolve_workspace(params)
        output_dir = Path(params.output_dir).resolve() if params.output_dir else None
        return (
            FlextInfraInventoryService()
            .generate(ws, output_dir=output_dir)
            .map(lambda _: True)
        )

    @staticmethod
    def _handle_pytest_diag(params: m.Infra.ValidatePytestDiagInput) -> r[bool]:
        result = FlextInfraPytestDiagExtractor().extract(
            Path(params.junit), Path(params.log)
        )
        if result.is_failure:
            return r[bool].fail(result.error or "extraction failed")
        _write_diag_files(params, result.value)
        return r[bool].ok(True)

    @staticmethod
    def _handle_scan(params: m.Infra.ValidateScanInput) -> r[bool]:
        result = FlextInfraTextPatternScanner().scan(
            u.Infra.resolve_workspace(params),
            params.pattern,
            includes=params.include or [],
            excludes=params.exclude or [],
            match_mode=params.match,
        )
        if result.is_failure:
            return r[bool].fail(result.error or "scan failed")
        count = result.value.get("violation_count", 0)
        if isinstance(count, int) and count > 0:
            return r[bool].fail(f"Scan found {count} violation(s)")
        return r[bool].ok(True)

    @staticmethod
    def _handle_skill_validate(params: m.Infra.ValidateSkillValidateInput) -> r[bool]:
        return (
            FlextInfraSkillValidator()
            .validate(u.Infra.resolve_workspace(params), params.skill, mode=params.mode)
            .flat_map(u.Infra.check_report)
        )

    @staticmethod
    def _handle_stub_validate(params: m.Infra.ValidateStubValidateInput) -> r[bool]:
        ws = u.Infra.resolve_workspace(params)
        projects = None if params.all_projects else params.project
        dirs = [ws / name for name in projects] if projects else None
        return (
            FlextInfraStubSupplyChain()
            .validate(ws, project_dirs=dirs)
            .flat_map(u.Infra.check_report)
        )


def _write_diag_files(
    params: m.Infra.ValidatePytestDiagInput, data: m.Infra.PytestDiagnostics
) -> None:
    """Write diagnostic output files when paths are specified."""
    for param_name, attr_name, sep in [
        ("failed", "failed_cases", "\n\n"),
        ("errors", "error_traces", "\n\n"),
        ("warnings", "warning_lines", "\n"),
        ("slowest", "slow_entries", "\n"),
        ("skips", "skip_cases", "\n"),
    ]:
        path_str = getattr(params, param_name, None)
        if path_str:
            items = [s for s in getattr(data, attr_name, []) if isinstance(s, str)]
            u.write_file(
                Path(path_str),
                sep.join(items) + "\n",
                encoding=c.Infra.Encoding.DEFAULT,
            )
