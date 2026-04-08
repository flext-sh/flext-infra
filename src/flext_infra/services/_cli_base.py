"""Shared helpers for CLI-exposing service mixins."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from flext_infra import t


class FlextInfraServiceCliRunnerMixin:
    """Shared CLI runner for simple ``FlextInfraCli*.run`` wrappers."""

    def _run_cli(
        self,
        runner: Callable[[t.StrSequence | None], int],
        args: t.StrSequence | None = None,
    ) -> int:
        """Execute one CLI runner with optional args."""
        return runner(args)


__all__: Sequence[str] = ("FlextInfraServiceCliRunnerMixin",)
