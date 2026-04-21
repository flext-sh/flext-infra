"""Public API facade for flext-infra."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, ClassVar, Self, override

from flext_core import r

from flext_infra import (
    FlextInfraConstantsBase,
    FlextInfraServiceRopeMixin,
    p,
    s,
    t,
)

_PYDANTIC_TYPES_MARKER: Annotated[int, "runtime-namespace"] = 0
_PYDANTIC_PATH_MARKER: Path | None = None
_PYDANTIC_CONSTANTS_MARKER: type[FlextInfraConstantsBase] = FlextInfraConstantsBase


class FlextInfra(
    FlextInfraServiceRopeMixin,
    s[t.ScalarMapping],
):
    """Thin public MRO facade over infra services."""

    app_name: ClassVar[str] = "flext-infra"
    _instance: ClassVar[Self | None] = None

    @classmethod
    def fetch_global(cls) -> Self:
        """Return the shared infra facade instance (canonical domain verb)."""
        if cls._instance is None:
            cls._instance = cls.model_validate({})
        return cls._instance

    @override
    def execute(self) -> p.Result[t.ScalarMapping]:
        """Execute a lightweight facade health report."""
        report: t.ScalarMapping = {
            "service": "flext-infra",
            "status": "ok",
            "workspace_root": str(self.workspace_root),
            "apply_changes": self.apply_changes,
        }
        return r[t.ScalarMapping].ok(report)


infra = FlextInfra.fetch_global()


__all__: list[str] = ["FlextInfra", "infra"]
