"""Public check service mixin for the infra API facade."""

from __future__ import annotations

from collections.abc import Sequence

from flext_infra import FlextInfraCliCheck, t


class FlextInfraServiceCheckMixin:
    """Expose check CLI execution through the public infra facade."""

    def run_check_cli(self, args: t.StrSequence | None = None) -> int:
        """Run the canonical check CLI entrypoint."""
        return FlextInfraCliCheck.run(args)


__all__: Sequence[str] = ("FlextInfraServiceCheckMixin",)
