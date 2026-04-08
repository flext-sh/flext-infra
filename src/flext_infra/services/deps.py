"""Public dependency service mixin for the infra API facade."""

from __future__ import annotations

from collections.abc import Sequence

from flext_infra import FlextInfraCliDeps, t
from flext_infra.services._cli_base import FlextInfraServiceCliRunnerMixin


class FlextInfraServiceDepsMixin(FlextInfraServiceCliRunnerMixin):
    """Expose dependency CLI execution through the public infra facade."""

    def run_deps_cli(self, args: t.StrSequence | None = None) -> int:
        """Run the canonical dependency CLI entrypoint."""
        return self._run_cli(FlextInfraCliDeps.run, args)


__all__: Sequence[str] = ("FlextInfraServiceDepsMixin",)
