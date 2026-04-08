"""Public dependency service mixin for the infra API facade."""

from __future__ import annotations

from collections.abc import Sequence

from flext_infra import FlextInfraCliDeps, t


class FlextInfraServiceDepsMixin:
    """Expose dependency CLI execution through the public infra facade."""

    def run_deps_cli(self, args: t.StrSequence | None = None) -> int:
        """Run the canonical dependency CLI entrypoint."""
        return FlextInfraCliDeps.run(args)


__all__: Sequence[str] = ("FlextInfraServiceDepsMixin",)
