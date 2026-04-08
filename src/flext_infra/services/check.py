"""Public check service mixin for the infra API facade."""

from __future__ import annotations

from collections.abc import Sequence

from flext_infra import FlextInfraCliCheck, t
from flext_infra.services._cli_base import FlextInfraServiceCliRunnerMixin


class FlextInfraServiceCheckMixin(FlextInfraServiceCliRunnerMixin):
    """Expose check CLI execution through the public infra facade."""

    def run_check_cli(self, args: t.StrSequence | None = None) -> int:
        """Run the canonical check CLI entrypoint."""
        return self._run_cli(FlextInfraCliCheck.run, args)


__all__: Sequence[str] = ("FlextInfraServiceCheckMixin",)
