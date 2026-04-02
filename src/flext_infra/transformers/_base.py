"""Base class for rope-based transformers with change-tracking."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import MutableSequence, Sequence

from flext_infra import t


class FlextInfraChangeTrackingTransformer:
    """Mixin providing change-tracking with optional callback.

    Provides ``changes`` list and ``_record_change`` method.
    Subclasses that need a rope ``transform()`` contract should
    inherit :class:`FlextInfraRopeTransformer` instead.
    """

    def __init__(self, *, on_change: t.Infra.ChangeCallback = None) -> None:
        self._on_change = on_change
        self.changes: MutableSequence[str] = []

    def _record_change(self, message: str) -> None:
        self.changes.append(message)
        if self._on_change is not None:
            self._on_change(message)


class FlextInfraRopeTransformer(FlextInfraChangeTrackingTransformer):
    """Base for all rope transformers — tracks changes and invokes callback."""

    @abstractmethod
    def transform(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> tuple[str, Sequence[str]]:
        """Apply transformation, return (new_source, list_of_change_descriptions)."""
        ...


__all__ = ["FlextInfraChangeTrackingTransformer", "FlextInfraRopeTransformer"]
