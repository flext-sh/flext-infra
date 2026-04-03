# pyright: reportMissingTypeStubs=false
"""Source-level Rope rewrite helpers."""

from __future__ import annotations

import re
from collections.abc import Sequence
from operator import itemgetter
from pathlib import Path

from flext_infra import FlextInfraUtilitiesDiscovery, FlextInfraUtilitiesRopeCore, c, t


class FlextInfraUtilitiesRopeSource(FlextInfraUtilitiesRopeCore):
    """Text-oriented helpers shared by Rope-backed refactors."""

    @staticmethod
    def read_source(resource: t.Infra.RopeResource) -> str:
        """Read source from a rope resource."""
        return resource.read()

    @staticmethod
    def write_source(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        content: str,
        *,
        description: str = "rope transform",
    ) -> bool:
        """Write content to resource via ChangeSet. Returns True if changed."""
        if content == resource.read():
            return False
        FlextInfraUtilitiesRopeSource.apply_source_change(
            rope_project,
            resource,
            content,
            description=description,
        )
        return True

    @staticmethod
    def replace_in_source(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        pattern: str | re.Pattern[str],
        replacement: str,
        *,
        apply: bool = True,
    ) -> tuple[str, int]:
        """Regex replace in source. Returns (new_source, count)."""
        source = resource.read()
        compiled = re.compile(pattern) if isinstance(pattern, str) else pattern
        new_source, count = compiled.subn(replacement, source)
        if count > 0 and apply and new_source != source:
            FlextInfraUtilitiesRopeSource.apply_source_change(
                rope_project,
                resource,
                new_source,
                description=f"replace pattern in <{resource.path}>",
            )
        return new_source, count

    @staticmethod
    def get_class_body_lines(
        resource: t.Infra.RopeResource,
        class_name: str,
    ) -> Sequence[str] | None:
        """Extract body lines of a class (excluding the class definition line)."""
        lines = resource.read().splitlines()
        in_class = False
        indent = 0
        body: list[str] = []
        for line in lines:
            if not in_class:
                stripped = line.lstrip()
                if stripped.startswith((f"class {class_name}", f"class {class_name}(")):
                    in_class = True
                    indent = len(line) - len(stripped) + 4
                continue
            if not line.strip():
                body.append("")
                continue
            current_indent = len(line) - len(line.lstrip())
            if current_indent < indent and line.strip():
                break
            body.append(line)
        return body or None

    @staticmethod
    def remove_module_level_aliases(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        allow: t.Infra.StrSet | None = None,
        apply: bool = True,
    ) -> tuple[str, Sequence[str]]:
        """Remove module-level ``X = Y`` identity aliases."""
        allow_set = allow or set()
        source = resource.read()
        kept: list[str] = []
        removed: list[str] = []
        alias_pattern = re.compile(r"^([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\s*$")
        scope_depth = 0
        for line in source.splitlines(keepends=True):
            stripped = line.strip()
            if stripped.startswith(("class ", "def ")):
                scope_depth += 1
            if scope_depth > 0:
                kept.append(line)
                continue
            match = alias_pattern.match(stripped)
            if match is None:
                kept.append(line)
                continue
            target, value = match.group(1), match.group(2)
            if (
                target != value
                or target in allow_set
                or target in {c.Infra.Dunders.VERSION, c.Infra.Dunders.ALL}
            ):
                kept.append(line)
            else:
                removed.append(f"{target} = {value}")
        if not removed:
            return source, []
        new_source = "".join(kept)
        if apply:
            FlextInfraUtilitiesRopeSource.apply_source_change(
                rope_project,
                resource,
                new_source,
                description=f"remove {len(removed)} aliases in <{resource.path}>",
            )
        return new_source, removed

    @staticmethod
    def batch_replace_annotations(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        replacements: t.StrMapping,
        *,
        apply: bool = True,
    ) -> tuple[str, int]:
        """Apply multiple annotation replacements in one pass."""
        source = resource.read()
        total = 0
        for old_annotation, new_annotation in replacements.items():
            pattern = re.compile(rf"\b{re.escape(old_annotation)}\b")
            source, count = pattern.subn(new_annotation, source)
            total += count
        if total > 0 and apply and source != resource.read():
            FlextInfraUtilitiesRopeSource.apply_source_change(
                rope_project,
                resource,
                source,
                description=f"batch replace {total} annotations in <{resource.path}>",
            )
        return source, total

    @staticmethod
    def remove_redundant_cast(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        apply: bool = True,
    ) -> tuple[str, int]:
        """Remove ``cast(Type, value)`` calls, replacing with just ``value``."""
        pattern = re.compile(r"\bcast\s*\(\s*[^,]+\s*,\s*([^)]+)\s*\)")
        return FlextInfraUtilitiesRopeSource.replace_in_source(
            rope_project,
            resource,
            pattern,
            r"\1",
            apply=apply,
        )

    @staticmethod
    def rewrite_source_at_offsets(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        changes: Sequence[tuple[int, int, str]],
        *,
        apply: bool = True,
    ) -> str:
        """Apply offset-based edits (start, end, replacement) to source."""
        source = resource.read()
        for start, end, replacement in sorted(
            changes,
            key=itemgetter(0),
            reverse=True,
        ):
            source = source[:start] + replacement + source[end:]
        if apply and source != resource.read():
            FlextInfraUtilitiesRopeSource.apply_source_change(
                rope_project,
                resource,
                source,
                description=f"rewrite {len(changes)} regions in <{resource.path}>",
            )
        return source

    @classmethod
    def apply_transformer_to_source(
        cls,
        source: str,
        file_path: Path,
        transformer_fn: t.Infra.RopeTransformFn,
    ) -> tuple[str, t.StrSequence]:
        """Run a rope transformer against source text via a temporary context."""
        workspace_root = FlextInfraUtilitiesDiscovery.discover_project_root_from_file(
            file_path,
        )
        if workspace_root is None:
            return (source, [])
        rope_project = cls.init_rope_project(workspace_root)
        try:
            resource = cls.get_resource_from_path(rope_project, file_path)
            if resource is None:
                return (source, [])
            if resource.read() != source:
                cls.apply_source_change(
                    rope_project,
                    resource,
                    source,
                    description="sync source",
                )
            new_source, changes = transformer_fn(rope_project, resource)
            return (new_source, list(changes))
        finally:
            rope_project.close()


__all__ = ["FlextInfraUtilitiesRopeSource"]
