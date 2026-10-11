"""Validate-command CLI route ownership.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import ClassVar

from flext_infra import (
    FlextInfraCProfileReport,
    FlextInfraInventoryService,
    FlextInfraPytestDiagExtractor,
    FlextInfraRuntimeCensusValidator,
    FlextInfraSkillValidator,
    FlextInfraStubSupplyChain,
    FlextInfraTextPatternScanner,
    FlextInfraValidateFreshImport,
    FlextInfraValidateLazyMapFreshness,
    infra,
    m,
    p,
    r,
    t,
)


class FlextInfraValidationCommandRoutes:
    """Own the complete validate command tuple."""

    @staticmethod
    def _validate_namespace_command(
        request: m.Infra.NamespaceValidateCommand,
    ) -> p.Result[m.Infra.ValidationReport]:
        """Run namespace validation through the rule engine.

        Returns:
            The resulting ``p.Result[m.Infra.ValidationReport]``.

        """
        result = infra.validate_namespace(request)
        if result.failure:
            return r[m.Infra.ValidationReport].from_failure(result)
        report = result.unwrap()
        if report.passed:
            return r[m.Infra.ValidationReport].ok(report)
        details = "\n".join((report.summary, *report.violations))
        return r[m.Infra.ValidationReport].fail(details)

    validate_command_routes: ClassVar[t.VariadicTuple[m.Cli.ResultCommandRoute]] = (
        tuple(
            m.Cli.ResultCommandRoute(
                name=route_name,
                help_text=help_text,
                model_cls=model_cls,
                handler=handler,
            )
            for route_name, help_text, model_cls, handler in (
                (
                    "cprofile-report",
                    "Render a bounded cProfile report",
                    FlextInfraCProfileReport,
                    FlextInfraCProfileReport.execute,
                ),
                (
                    "inventory",
                    "Generate scripts inventory",
                    FlextInfraInventoryService,
                    FlextInfraInventoryService.execute,
                ),
                (
                    "runtime-census",
                    "Post-import Beartype enforcement census for flext_* modules",
                    FlextInfraRuntimeCensusValidator,
                    FlextInfraRuntimeCensusValidator.execute,
                ),
                (
                    "pytest-diag",
                    "Extract pytest diagnostics",
                    FlextInfraPytestDiagExtractor,
                    FlextInfraPytestDiagExtractor.execute,
                ),
                (
                    "scan",
                    "Scan text files for patterns",
                    FlextInfraTextPatternScanner,
                    FlextInfraTextPatternScanner.execute,
                ),
                (
                    "skill-validate",
                    "Validate a skill",
                    FlextInfraSkillValidator,
                    FlextInfraSkillValidator.execute,
                ),
                (
                    "stub-validate",
                    "Validate stub supply chain",
                    FlextInfraStubSupplyChain,
                    FlextInfraStubSupplyChain.execute,
                ),
                (
                    "fresh-import",
                    "Guard 7: fresh-process import smoke test",
                    FlextInfraValidateFreshImport,
                    FlextInfraValidateFreshImport.execute,
                ),
                (
                    "lazy-map-freshness",
                    "Guard 2/3: lazy-map freshness validator",
                    FlextInfraValidateLazyMapFreshness,
                    FlextInfraValidateLazyMapFreshness.execute,
                ),
                (
                    "namespace",
                    "Guard: namespace laws of the rule catalog",
                    m.Infra.NamespaceValidateCommand,
                    _validate_namespace_command,
                ),
            )
        )
    )


__all__: list[str] = ["FlextInfraValidationCommandRoutes"]
