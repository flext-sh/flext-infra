"""Base class for rope-based transformers with change-tracking."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import MutableSequence

from flext_infra import FlextInfraTypes


class FlextInfraChangeTrackingTransformer:
    """Mixin providing change-tracking with optional callback.

    Provides ``changes`` list and ``_record_change`` method.
    Subclasses that need a rope ``transform()`` contract should
    inherit :class:`FlextInfraRopeTransformer` instead.
    """

    def __init__(
        self,
        *,
        on_change: FlextInfraTypes.Infra.ChangeCallback = None,
    ) -> None:
        """Initialize change tracking with an optional callback."""
        self._on_change = on_change
        self.changes: MutableSequence[str] = []

    def _record_change(self, message: str) -> None:
        self.changes.append(message)
        if self._on_change is not None:
            self._on_change(message)


class FlextInfraRopeTransformer(FlextInfraChangeTrackingTransformer):
    """Base for all rope transformers — tracks changes and invokes callback.

    Subclasses that follow the ``read → apply_to_source → write`` pattern
    need only implement ``apply_to_source`` and set ``_description``.
    The default ``transform()`` handles the boilerplate.
    """

    _description: str = "transformation"

    @abstractmethod
    def apply_to_source(self, source: str) -> FlextInfraTypes.Infra.TransformResult:
        """Apply transformation to in-memory source."""
        ...

    def transform(
        self,
        rope_project: FlextInfraTypes.Infra.RopeProject,
        resource: FlextInfraTypes.Infra.RopeResource,
    ) -> FlextInfraTypes.Infra.TransformResult:
        """Read → apply_to_source → write if changed. Override for custom logic."""
        _ = rope_project
        source = resource.read()
        updated, changes = self.apply_to_source(source)
        if updated != source and changes:
            resource.write(updated)
        return updated, changes


__all__: list[str] = [
    "FlextInfraChangeTrackingTransformer",
    "FlextInfraRopeTransformer",
]
