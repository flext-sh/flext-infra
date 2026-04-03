"""MRO redeclaration remover transformer — rope-based implementation."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import override

from flext_infra import FlextInfraRopeTransformer, t, u


class FlextInfraRefactorMRORemover(FlextInfraRopeTransformer):
    """Remove nested class bases that redundantly reference the parent class.

    For each top-level class, scans nested classes whose base list
    references the parent and strips that base via rope regex replacement.
    """

    @override
    def transform(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> tuple[str, Sequence[str]]:
        """Apply MRO redeclaration removal. Returns (new_source, changes)."""
        source = u.read_source(resource)
        class_infos = u.get_class_info(rope_project, resource)
        if not class_infos:
            return source, []

        for parent_info in class_infos:
            parent_name = parent_info.name
            nested_names = u.get_class_nested_classes(
                rope_project,
                resource,
                parent_name,
            )
            for nested_name in nested_names:
                source = self._strip_parent_base(
                    rope_project,
                    resource,
                    source,
                    parent_name=parent_name,
                    nested_class=nested_name,
                )

        if source != u.read_source(resource) and self.changes:
            u.write_source(
                rope_project,
                resource,
                source,
                description="mro remover",
            )
        return source, list(self.changes)

    def _strip_parent_base(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        source: str,
        *,
        parent_name: str,
        nested_class: str,
    ) -> str:
        """Remove base referencing parent_name from nested_class definition."""
        nested_bases = u.get_class_bases(
            rope_project,
            resource,
            nested_class,
        )
        has_parent_base = any(
            base == parent_name or base.startswith(f"{parent_name}.")
            for base in nested_bases
        )
        if not has_parent_base:
            return source

        # Remove the base class referencing parent, or strip all bases if only one
        remaining = [
            b
            for b in nested_bases
            if b != parent_name and not b.startswith(f"{parent_name}.")
        ]
        pattern = re.compile(
            rf"^(\s*class\s+{re.escape(nested_class)})\s*\([^)]*\)\s*:",
            re.MULTILINE,
        )
        if remaining:
            bases_str = ", ".join(remaining)
            replacement = rf"\1({bases_str}):"
        else:
            replacement = r"\1:"

        new_source, count = pattern.subn(replacement, source, count=1)
        if count > 0 and new_source != source:
            self._record_change(f"Fixed MRO redeclaration: {nested_class}")
            return new_source
        return source


__all__ = ["FlextInfraRefactorMRORemover"]
