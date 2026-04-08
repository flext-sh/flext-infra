"""Public codegen service mixin for the infra API facade."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import (
    FlextInfraCodegenCensus,
    FlextInfraCodegenConsolidator,
    FlextInfraCodegenDeduplicator,
    FlextInfraCodegenFixer,
    FlextInfraCodegenLazyInit,
    FlextInfraCodegenPipeline,
    FlextInfraCodegenPyTyped,
    FlextInfraCodegenScaffolder,
    FlextInfraConstantsCodegenQualityGate,
    m,
    p,
    t,
)

if TYPE_CHECKING:
    from flext_infra import FlextInfraCommandContext


class FlextInfraServiceCodegenMixin:
    """Expose codegen operations through the public infra facade."""

    def run_codegen_census(
        self: FlextInfraCommandContext[t.MutableContainerMapping],
        *,
        class_to_analyze: str | None = None,
        projects: Sequence[p.Infra.ProjectInfo] | None = None,
    ) -> Sequence[m.Infra.CensusReport]:
        """Run the public census API using the current facade context."""
        payload = dict(self.command_payload())
        if class_to_analyze is not None:
            payload["class_to_analyze"] = class_to_analyze
        service = FlextInfraCodegenCensus.model_validate(payload)
        return service.run(projects=projects)

    def run_codegen_scaffold(
        self: FlextInfraCommandContext[t.MutableContainerMapping],
        *,
        projects: Sequence[p.Infra.ProjectInfo] | None = None,
    ) -> Sequence[m.Infra.ScaffoldResult]:
        """Run project scaffolding through the public facade."""
        service = FlextInfraCodegenScaffolder.model_validate(self.command_payload())
        return service.run(
            dry_run=service.dry_run or not service.apply_changes, projects=projects
        )

    def fix_codegen_workspace(
        self: FlextInfraCommandContext[t.MutableContainerMapping],
    ) -> Sequence[m.Infra.AutoFixResult]:
        """Run namespace/codegen fixes across the current workspace."""
        return FlextInfraCodegenFixer.model_validate(
            self.command_payload(),
        ).fix_workspace()

    def generate_lazy_inits(
        self: FlextInfraCommandContext[t.MutableContainerMapping],
        *,
        check_only: bool | None = None,
    ) -> int:
        """Generate lazy ``__init__.py`` files through the public facade."""
        payload = dict(self.command_payload())
        if check_only is not None:
            payload["check_only"] = check_only
        service = FlextInfraCodegenLazyInit.model_validate(payload)
        return service.generate_inits(check_only=service.check_only)

    def update_py_typed(
        self: FlextInfraCommandContext[t.MutableContainerMapping],
        *,
        check_only: bool | None = None,
    ) -> int:
        """Refresh ``py.typed`` markers through the public facade."""
        payload = dict(self.command_payload())
        if check_only is not None:
            payload["check_only"] = check_only
        service = FlextInfraCodegenPyTyped.model_validate(payload)
        return service.run(check_only=service.check_only)

    def run_codegen_pipeline(
        self: FlextInfraCommandContext[t.MutableContainerMapping],
    ) -> r[str]:
        """Execute the full codegen pipeline through the public facade."""
        return FlextInfraCodegenPipeline.model_validate(
            self.command_payload()
        ).execute()

    def run_constants_quality_gate(
        self: FlextInfraCommandContext[t.MutableContainerMapping],
    ) -> r[bool]:
        """Execute the constants quality gate through the public facade."""
        return FlextInfraConstantsCodegenQualityGate.model_validate(
            self.command_payload(),
        ).execute()

    def consolidate_codegen(
        self: FlextInfraCommandContext[t.MutableContainerMapping],
    ) -> r[str]:
        """Consolidate constants through the public facade."""
        return FlextInfraCodegenConsolidator.model_validate(
            self.command_payload(),
        ).execute()

    def deduplicate_codegen(
        self: FlextInfraCommandContext[t.MutableContainerMapping],
    ) -> r[str]:
        """Deduplicate constants through the public facade."""
        return FlextInfraCodegenDeduplicator.model_validate(
            self.command_payload(),
        ).execute()


__all__: Sequence[str] = ("FlextInfraServiceCodegenMixin",)
