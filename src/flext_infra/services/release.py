"""Public release service mixin for the infra API facade."""

from __future__ import annotations

from collections.abc import Sequence

from flext_core import r
from flext_infra import FlextInfraReleaseOrchestrator


class FlextInfraServiceReleaseMixin:
    """Expose release orchestration through the public infra facade."""

    def run_release(self, params: FlextInfraReleaseOrchestrator) -> r[bool]:
        """Run release orchestration through the public facade."""
        return params.execute()


__all__: Sequence[str] = ("FlextInfraServiceReleaseMixin",)
