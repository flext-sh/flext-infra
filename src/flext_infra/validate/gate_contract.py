"""Gate contract validation service.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated, override

from flext_core import r
from flext_infra import c, m, p
from flext_infra.base import s
from flext_infra.validate.gate_contract_checks import FlextInfraGateContractChecksMixin
from flext_infra.validate.gate_contract_models import FlextInfraGateContractModels
from flext_infra.validate.gate_contract_report import FlextInfraGateContractReportMixin
from flext_infra.validate.gate_contract_scan import FlextInfraGateContractScanMixin


class FlextInfraGateContractValidator(
    s[bool],
    FlextInfraGateContractScanMixin,
    FlextInfraGateContractChecksMixin,
    FlextInfraGateContractReportMixin,
):
    """Validate workspace gate scripts against the scripts-infra contract."""

    check_all: Annotated[
        bool, m.Field(description="Validate scripts that are not validators or fixers")
    ] = False
    mode: Annotated[c.Infra.OperationMode, m.Field(description="Validation mode")] = (
        c.Infra.OperationMode.BASELINE
    )

    def run(self) -> FlextInfraGateContractModels.RunResult:
        """Run validation and return the CLI outcome."""
        root = self.workspace_root.resolve()
        if not root.exists() or not root.is_dir():
            msg = f"root directory not found: {root}"
            raise FlextInfraGateContractModels.UsageError(msg)

        scripts = self._tracked_scripts(root)
        results = tuple(
            self._validate_script(root, script, check_all=self.check_all)
            for script in scripts
        )
        self._print_results(results)
        report_result = self._write_report(root, results, str(self.mode))
        if report_result.failure:
            msg = f"failed to write report: {report_result.error}"
            raise FlextInfraGateContractModels.InfraError(msg)
        report_path = report_result.value

        summary = self._summary_for(results)
        self._print_summary(summary, report_path)
        exit_code = (
            int(c.Infra.ScriptExitCode.FAIL)
            if summary.errors > 0
            else int(c.Infra.ScriptExitCode.PASS)
        )
        return FlextInfraGateContractModels.RunResult(
            exit_code=exit_code, violation_count=summary.errors
        )

    @override
    def execute(self) -> p.Result[bool]:
        """Execute validation as a service."""
        try:
            outcome = self.run()
        except (
            FlextInfraGateContractModels.UsageError,
            FlextInfraGateContractModels.InfraError,
        ) as exc:
            return r[bool].fail(str(exc))
        if outcome.exit_code == int(c.Infra.ScriptExitCode.PASS):
            return r[bool].ok(True)
        return r[bool].fail(f"gate contract found {outcome.violation_count} error(s)")


__all__: list[str] = ["FlextInfraGateContractValidator"]
