"""Public API facade for flext-infra."""

from __future__ import annotations

from typing import ClassVar, Self, override

from flext_core import r
from flext_infra import (
    FlextInfraCliBasemk,
    FlextInfraCliCodegen,
    FlextInfraCliDocs,
    FlextInfraCliGithub,
    FlextInfraCliMaintenance,
    FlextInfraCliRefactor,
    FlextInfraCliRelease,
    FlextInfraCliValidate,
    FlextInfraCliWorkspace,
    FlextInfraCommandContext,
    FlextInfraServiceBasemkMixin,
    FlextInfraServiceCheckMixin,
    FlextInfraServiceCodegenMixin,
    FlextInfraServiceDepsMixin,
    FlextInfraServiceDocsMixin,
    FlextInfraServiceGithubMixin,
    FlextInfraServiceRefactorMixin,
    FlextInfraServiceReleaseMixin,
    FlextInfraServiceValidateMixin,
    FlextInfraServiceWorkspaceMixin,
    t,
)


class FlextInfra(
    FlextInfraCliBasemk,
    FlextInfraCliCodegen,
    FlextInfraCliDocs,
    FlextInfraCliGithub,
    FlextInfraCliMaintenance,
    FlextInfraCliRefactor,
    FlextInfraCliRelease,
    FlextInfraCliValidate,
    FlextInfraCliWorkspace,
    FlextInfraServiceBasemkMixin,
    FlextInfraServiceCheckMixin,
    FlextInfraServiceCodegenMixin,
    FlextInfraServiceDepsMixin,
    FlextInfraServiceDocsMixin,
    FlextInfraServiceGithubMixin,
    FlextInfraServiceRefactorMixin,
    FlextInfraServiceReleaseMixin,
    FlextInfraServiceValidateMixin,
    FlextInfraServiceWorkspaceMixin,
    FlextInfraCommandContext[t.MutableContainerMapping],
):
    """Thin public MRO facade over infra services and CLI groups."""

    _instance: ClassVar[Self | None] = None

    @classmethod
    def get_instance(cls) -> Self:
        """Return the shared infra facade instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @override
    def execute(self) -> r[t.MutableContainerMapping]:
        """Execute a lightweight facade health report."""
        report: t.MutableContainerMapping = {
            "service": "flext-infra",
            "status": "ok",
            "workspace_root": str(self.workspace_root),
            "apply_changes": self.apply_changes,
        }
        return r[t.MutableContainerMapping].ok(report)


infra = FlextInfra.get_instance()

__all__ = ["FlextInfra", "infra"]
