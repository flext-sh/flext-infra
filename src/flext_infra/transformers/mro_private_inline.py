"""Private-symbol inlining and qualified reference transformers — rope-based."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import override

from flext_infra import t, u
from flext_infra.transformers._base import FlextInfraRopeTransformer


class FlextInfraRefactorMROPrivateInlineTransformer(FlextInfraRopeTransformer):
    """Inline configured private-name values after MRO migration.

    Replaces bare references to private constants with their literal values
    using rope regex replacement with word boundaries.
    """

    def __init__(
        self,
        *,
        replacement_values: Mapping[str, str],
        on_change: t.Infra.ChangeCallback = None,
    ) -> None:
        """Initialize with symbol-to-value mapping for private constant inlining."""
        super().__init__(on_change=on_change)
        self._replacement_values = replacement_values

    @override
    def transform(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> tuple[str, Sequence[str]]:
        """Apply private constant inlining. Returns (new_source, changes)."""
        source = u.Infra.read_source(resource)

        for name, value in self._replacement_values.items():
            pattern = re.compile(rf"\b{re.escape(name)}\b")
            new_source, count = pattern.subn(value, source)
            if count > 0 and new_source != source:
                self._record_change(f"Inlined private constant: {name} -> {value}")
                source = new_source

        if source != u.Infra.read_source(resource):
            u.Infra.write_source(
                rope_project,
                resource,
                source,
                description="mro private inline",
            )
        return source, list(self.changes)


class FlextInfraRefactorMROQualifiedReferenceTransformer(FlextInfraRopeTransformer):
    """Replace bare name references with qualified facade paths after migration.

    Skips definition positions (type alias names, annotation targets, assignment
    targets) so only reference occurrences are renamed.
    """

    def __init__(
        self,
        *,
        renames: Mapping[str, str],
        on_change: t.Infra.ChangeCallback = None,
    ) -> None:
        """Initialize with symbol-to-qualified-expression rename mapping."""
        super().__init__(on_change=on_change)
        self._renames = renames

    @override
    def transform(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> tuple[str, Sequence[str]]:
        """Apply qualified reference rewrites. Returns (new_source, changes)."""
        source = u.Infra.read_source(resource)

        for old_name, qualified_path in self._renames.items():
            # Skip definition sites: `type X = ...`, `X: ... = ...`, `X = ...`
            pattern = re.compile(
                rf"(?<!class\s)(?<!def\s)(?<!\.)(?<!import\s)"
                rf"\b{re.escape(old_name)}\b"
                rf"(?!\s*[=:](?!=))",
            )
            new_source, count = pattern.subn(qualified_path, source)
            if count > 0 and new_source != source:
                self._record_change(
                    f"Qualified reference: {old_name} -> {qualified_path}",
                )
                source = new_source

        if source != u.Infra.read_source(resource):
            u.Infra.write_source(
                rope_project,
                resource,
                source,
                description="mro qualified reference",
            )
        return source, list(self.changes)


__all__ = [
    "FlextInfraRefactorMROPrivateInlineTransformer",
    "FlextInfraRefactorMROQualifiedReferenceTransformer",
]
