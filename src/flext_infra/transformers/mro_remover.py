"""MRO redeclaration remover transformer — rope-based implementation."""

from __future__ import annotations

import re
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
    ) -> t.Infra.TransformResult:
        """Apply MRO redeclaration removal. Returns (new_source, changes)."""
        source = resource.read()
        class_infos = u.Infra.get_class_info(rope_project, resource)
        if not class_infos:
            no_changes: list[str] = []
            return source, no_changes

        for parent_info in class_infos:
            parent_name = parent_info.name
            nested_names = u.Infra.get_class_nested_classes(
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

        if source != resource.read() and self.changes:
            resource.write(source)
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
        nested_bases = u.Infra.get_class_bases(
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
