"""Shared base for docs phase services.

Single source of truth for the docs-specific ``output_dir`` default and for
the canonical phase-outcome propagation pattern. Phase services inherit
this base and call :meth:`_propagate_phase_outcome` instead of repeating
the same five-line ``execute()`` skeleton.
"""

from __future__ import annotations

from abc import ABC
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Annotated

from flext_infra import c, e, m, p, r
from flext_infra.base import FlextInfraProjectSelectionServiceBase


class FlextInfraDocServiceBase(FlextInfraProjectSelectionServiceBase[bool], ABC):
    """Shared abstract base for ``audit``, ``build``, ``fix``, ``generate``, ``validate``."""

    output_dir: Annotated[
        Path | None,
        m.Field(description="Docs output dir"),
    ] = Path(c.Infra.DEFAULT_DOCS_OUTPUT_DIR)

    @staticmethod
    def _propagate_phase_outcome(
        label: str,
        result: p.Result[Sequence[m.Infra.DocsPhaseReport]],
        *,
        failure_predicate: Callable[[m.Infra.DocsPhaseReport], bool] | None = None,
    ) -> p.Result[bool]:
        """Convert a verb result into a boolean execute() outcome.

        ``failure_predicate=None`` skips per-report aggregation entirely
        (used by ``fix`` and ``generate`` whose phase semantics treat WARN
        and OK as success). When provided, reports matching the predicate
        are counted and surfaced as a single ``e.fail_operation`` failure.
        """
        if result.failure:
            return e.fail_operation(label, result.error)
        if failure_predicate is not None:
            failures = sum(1 for report in result.value if failure_predicate(report))
            if failures:
                return e.fail_operation(label, f"{failures} failure(s)")
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraDocServiceBase"]
