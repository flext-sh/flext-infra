"""Class nesting transformer — rope-based implementation."""

from __future__ import annotations

import textwrap
from collections import defaultdict
from typing import TYPE_CHECKING, override

from flext_infra import c, u
from flext_infra.transformers.base import FlextInfraRopeTransformer

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraRefactorClassNestingTransformer(FlextInfraRopeTransformer):
    """Transform top-level classes into nested classes under namespace parents."""

    def __init__(
        self, mappings: t.StrMapping, on_change: t.Infra.ChangeCallback = None
    ) -> None:
        """Initialize with class-to-namespace mappings."""
        super().__init__(on_change=on_change)
        self._mappings = mappings

    @override
    def transform(
        self, rope_project: t.Infra.RopeProject, resource: t.Infra.RopeResource
    ) -> t.Infra.TransformResult:
        """Apply class nesting. Returns (new_source, changes)."""
        source = resource.read()
        class_infos = u.Infra.get_class_info(rope_project, resource)
        updated, changes = self.apply_to_source(
            source, existing_names={info.name for info in class_infos}
        )
        if updated != source and changes:
            resource.write(updated)
        return updated, changes

    @override
    def apply_to_source(
        self, source: str, *, existing_names: set[str] | None = None
    ) -> t.Infra.TransformResult:
        """Apply class nesting to in-memory source without persisting."""
        if existing_names is None:
            existing_names = set(c.Infra.CLASS_NAME_RE.findall(source))
        collected: dict[str, list[str]] = defaultdict(list)
        for class_name, target_namespace in self._mappings.items():
            if class_name not in existing_names:
                continue
            collected[target_namespace].append(class_name)
        if not collected:
            no_changes: list[str] = []
            return source, no_changes
        updated = source
        for namespace, class_names in collected.items():
            ns_exists = namespace in existing_names
            updated = self._nest_classes(
                updated,
                namespace=namespace,
                class_names=class_names,
                ns_exists=ns_exists,
            )
            existing_names.add(namespace)
        return updated, list(self.changes)

    def _nest_classes(
        self,
        source: str,
        *,
        namespace: str,
        class_names: t.StrSequence,
        ns_exists: bool,
    ) -> str:
        """Nest classes."""
        extracted: list[str] = []
        for class_name in class_names:
            block = u.Infra.extract_definition(source, class_name, kind="class")
            if block is None:
                continue
            extracted.append(textwrap.indent(block, "    "))
            source = u.Infra.remove_definition(source, class_name, kind="class")
            self._record_change(f"Nested {class_name} into {namespace}")
        if not extracted:
            return source
        nested_block = "\n".join(extracted)
        if ns_exists:
            appended: str = u.Infra.append_to_class_body(
                source, namespace, nested_block
            )
            return appended
        return source.rstrip("\n") + f"\n\nclass {namespace}:\n{nested_block}\n"


__all__: list[str] = ["FlextInfraRefactorClassNestingTransformer"]
