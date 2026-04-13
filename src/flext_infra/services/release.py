"""Public release service mixin for the infra API facade."""

from __future__ import annotations

from flext_infra import FlextInfraReleaseOrchestrator, p, t


class FlextInfraServiceReleaseMixin:
    """Expose release orchestration through the public infra facade."""

    def run_release(self, params: FlextInfraReleaseOrchestrator) -> p.Result[bool]:
        """Run release orchestration through the public facade."""
        return params.execute()


__all__: t.StrSequence = ("FlextInfraServiceReleaseMixin",)
