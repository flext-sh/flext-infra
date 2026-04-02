"""Redundant cast() call remover via rope regex replacement."""

from __future__ import annotations

from collections.abc import MutableSequence

from flext_infra import FlextInfraUtilitiesRope, t


class FlextInfraRedundantCastRemover:
    """Remove redundant cast() calls, replacing ``cast(Type, value)`` with ``value``.

    Uses rope's regex-based cast removal instead of CST visitors.
    """

    def __init__(self, removable_types: t.Infra.StrSet | None = None) -> None:
        """Initialize with optional set of type names whose casts are removable.

        When None, all cast() calls are removed regardless of target type.
        """
        self._removable_types = removable_types
        self.changes: MutableSequence[str] = []

    def transform(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> tuple[str, MutableSequence[str]]:
        """Remove cast() calls from source via rope.

        Returns (new_source, list_of_change_descriptions).
        """
        if self._removable_types is not None:
            return self._remove_typed_casts(rope_project, resource)
        source, count = FlextInfraUtilitiesRope.remove_redundant_cast(
            rope_project,
            resource,
            apply=True,
        )
        if count > 0:
            self.changes.append(f"Removed {count} redundant cast() calls")
        return source, self.changes

    def _remove_typed_casts(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> tuple[str, MutableSequence[str]]:
        """Remove only cast() calls targeting specific types."""
        source = resource.read()
        total = 0
        for type_name in self._removable_types or ():
            replaced, count = FlextInfraUtilitiesRope.replace_in_source(
                rope_project,
                resource,
                rf"\bcast\s*\(\s*{type_name}\s*,\s*([^)]+)\s*\)",
                r"\1",
                apply=True,
            )
            if count > 0:
                total += count
                self.changes.append(
                    f"Removed {count} redundant cast() for {type_name}",
                )
                source = replaced
        return source, self.changes


__all__ = ["FlextInfraRedundantCastRemover"]
