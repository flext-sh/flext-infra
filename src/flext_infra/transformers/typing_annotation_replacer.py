"""Replace forbidden annotation patterns with canonical typing contracts via rope."""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence

from flext_infra import FlextInfraUtilitiesRope, t


class FlextInfraTypingAnnotationReplacer:
    """Replace legacy typing annotations (Any, object, cast) with strict t.* contracts.

    Uses rope word-boundary replacement instead of CST visitors.
    Default replacements target ``t.NormalizedValue`` -> ``t.ContainerValue``.
    """

    DEFAULT_REPLACEMENTS: Mapping[str, str] = {
        "t.NormalizedValue": "t.ContainerValue",
    }

    def __init__(
        self,
        *,
        replacements: Mapping[str, str] | None = None,
        on_change: t.Infra.ChangeCallback = None,
    ) -> None:
        """Initialize with annotation replacement map and optional callback."""
        self._replacements = replacements or self.DEFAULT_REPLACEMENTS
        self._on_change = on_change
        self.modified: bool = False
        self.changes: MutableSequence[str] = []

    def transform(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> tuple[str, MutableSequence[str]]:
        """Apply all annotation replacements via rope batch replace.

        Returns (new_source, list_of_change_descriptions).
        """
        source, total = FlextInfraUtilitiesRope.batch_replace_annotations(
            rope_project,
            resource,
            self._replacements,
            apply=True,
        )
        if total > 0:
            self.modified = True
            for old, new in self._replacements.items():
                msg = f"Replaced annotation: {old} -> {new}"
                self.changes.append(msg)
                if self._on_change is not None:
                    self._on_change(msg)
        return source, self.changes


__all__ = ["FlextInfraTypingAnnotationReplacer"]
