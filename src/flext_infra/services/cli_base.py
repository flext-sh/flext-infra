"""Shared helpers for thin service-dispatch mixins."""

from __future__ import annotations

from collections.abc import Callable

from flext_core import r
from flext_infra import s, t


class FlextInfraServiceCliRunnerMixin:
    """Shared dispatch helpers for thin CLI and service proxy mixins."""

    def _run_cli(
        self,
        runner: Callable[[t.StrSequence | None], int],
        args: t.StrSequence | None = None,
    ) -> int:
        """Execute one CLI runner with optional args."""
        return runner(args)

    @staticmethod
    def _dispatch_result[TResult: t.Infra.DomainOutput](
        params: s[TResult],
    ) -> r[TResult]:
        """Route validated service params through the canonical base executor."""
        return type(params).execute_command(params)


__all__: t.StrSequence = ("FlextInfraServiceCliRunnerMixin",)
