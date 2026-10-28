"""Shared service foundation for flext-infra command services.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Self, override

from flext_core import FlextService

from flext_infra import FlextInfraBasePayload, c, m, p, r, settings
from flext_infra._utilities import FlextInfraUtilitiesBase


class FlextInfraServiceBase[TDomainResult](
    FlextService[TDomainResult],
    m.Infra.CommandContext,
    FlextInfraBasePayload,
):
    """Domain command context shared by all flext-infra CLI services.

    Provides settings/bootstrap and normalized fields for workspace location,
    apply/dry-run toggles, output formatting, and project filtering.
    """

    @classmethod
    def runtime_bootstrap_options(cls) -> p.RuntimeBootstrapOptions:
        """Bootstrap service runtime using the shared CLI settings namespace.

        Returns:
            The resulting ``p.RuntimeBootstrapOptions``.

        """
        # flext-j47u: configure the inherited runtime once; no settings proxy/property.
        return m.RuntimeBootstrapOptions(settings_type=type(settings))

    @property
    def fail_fast(self) -> bool:
        """Stop at the first failure as an invariant, never a CLI choice."""
        return c.Infra.SERVICE_FAIL_FAST

    def _filtered_projects(
        self,
        projects: Sequence[p.Infra.ProjectInfo],
    ) -> Sequence[p.Infra.ProjectInfo]:
        """Apply the comma-separated ``project_filter`` when one is configured.

        Returns:
            The resulting ``Sequence[p.Infra.ProjectInfo]``.

        """
        if self.project_filter is None:
            return projects
        selected = set(
            FlextInfraUtilitiesBase.normalize_cli_values(self.project_filter)
        )
        return [project for project in projects if project.name in selected]

    @staticmethod
    def _report_execution[ReportT: p.Infra.ValidationReportOutcome](
        report_result: p.Result[ReportT],
    ) -> p.Result[bool]:
        """Map one validation report onto the boolean outcome a validator returns.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if report_result.failure:
            return r[bool].from_failure(report_result)
        report = report_result.unwrap()
        return r[bool].ok(value=True) if report.passed else r[bool].fail(report.summary)

    @override
    def execute(self) -> p.Result[TDomainResult]:
        """Execute the service contract and return a typed result."""
        raise NotImplementedError

    @property
    def log(self) -> p.Logger:
        """Service logger through the canonical FlextService kernel."""
        return self.logger

    @classmethod
    def execute_command(cls, params: Self) -> p.Result[TDomainResult]:
        """Execute the validated CLI service instance directly.

        Returns:
            The resulting ``p.Result[TDomainResult]``.

        """
        return params.execute()


s = FlextInfraServiceBase

__all__: list[str] = ["FlextInfraServiceBase", "s"]
