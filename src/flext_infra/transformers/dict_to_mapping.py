"""Dict-to-Mapping annotation transformer via rope regex replacement."""

from __future__ import annotations

import re
from collections.abc import MutableSequence

from flext_infra import c, t, u


class FlextInfraDictToMappingTransformer:
    """Transform ``dict[K, V]`` annotations to ``Mapping[K, V]`` via rope.

    Uses regex word-boundary replacement. Does not rewrite mutated parameters
    (mutation detection requires static analysis beyond this transformer's scope).
    """

    def __init__(self, *, include_return_annotations: bool = False) -> None:
        """Initialize with return-annotation rewriting toggle."""
        self._include_return_annotations = include_return_annotations
        self.changes: MutableSequence[str] = []

    def transform(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> tuple[str, MutableSequence[str]]:
        """Replace dict annotations with Mapping via rope.

        Returns (new_source, list_of_change_descriptions).
        """
        pattern = r"\bdict\["
        source, count = u.replace_in_source(
            rope_project,
            resource,
            pattern,
            "Mapping[",
            apply=True,
        )
        if count > 0:
            self.changes.append(
                f"Converted {count} dict[...] annotations to Mapping[...]",
            )
            self._ensure_mapping_import(rope_project, resource)
        return source, self.changes

    @staticmethod
    def _ensure_mapping_import(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> None:
        """Add ``from collections.abc import Mapping`` if not already present."""
        source = resource.read()
        if "from collections.abc import" in source and "Mapping" in source:
            return
        if "from collections.abc import" not in source:
            u.replace_in_source(
                rope_project,
                resource,
                rf"^({re.escape(c.Infra.SourceCode.FUTURE_ANNOTATIONS)}\n)",
                r"\1\nfrom collections.abc import Mapping\n",
                apply=True,
            )


__all__ = ["FlextInfraDictToMappingTransformer"]
