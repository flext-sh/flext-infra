"""Nested class reference propagation transformer — rope-based implementation."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import override

from flext_infra import (
    FlextInfraRopeTransformer,
    t,
    u,
)


class FlextInfraNestedClassPropagationTransformer(FlextInfraRopeTransformer):
    """Propagate import and name references after classes are nested into namespaces.

    After class nesting, ``from module import OldClass`` becomes
    ``from module import Namespace`` and bare ``OldClass`` references
    become ``Namespace.OldClass``.
    """

    def __init__(
        self,
        class_renames: t.StrMapping,
        policy_context: t.Infra.PolicyContext | None = None,
        class_families: t.StrMapping | None = None,
        on_change: t.Infra.ChangeCallback = None,
    ) -> None:
        """Initialize with class rename mappings and optional policy context."""
        super().__init__(on_change=on_change)
        self._class_renames = class_renames
        self._policy_context = policy_context
        self._class_families = class_families or {}

    _description = "nested class propagation"

    @override
    def apply_to_source(self, source: str) -> t.Infra.TransformResult:
        """Apply reference propagation to in-memory source without persisting."""
        self.changes.clear()
        updated = source
        for old_name, rename_to in self._class_renames.items():
            if not self._should_propagate(old_name, "propagate_imports"):
                continue
            if self._blocked_by_prefix(old_name):
                continue
            rename_parts = rename_to.split(".")
            namespace = rename_parts[0]
            aliases = self._find_import_aliases(updated, old_name=old_name)
            updated = self._rewrite_import(
                updated, old_name=old_name, namespace=namespace
            )
            if self._should_propagate(old_name, "propagate_name_references"):
                updated = self._qualify_name_references(
                    updated,
                    old_name=old_name,
                    qualified=rename_to,
                )
                updated = self._qualify_return_annotations(
                    updated,
                    old_name=old_name,
                    qualified=rename_to,
                )
                nested_name = rename_parts[-1]
                for alias_name in aliases:
                    qualified_alias = f"{alias_name}.{nested_name}"
                    updated = self._qualify_alias_references(
                        updated,
                        alias_name=alias_name,
                        qualified=qualified_alias,
                    )
                    updated = self._qualify_return_annotations(
                        updated,
                        old_name=alias_name,
                        qualified=qualified_alias,
                    )
            if self._should_propagate(old_name, "propagate_attribute_references"):
                updated = self._qualify_attribute_references(
                    updated,
                    old_name=old_name,
                    rename_parts=rename_parts,
                    aliases=aliases,
                )
        return updated, list(self.changes)

    def _rewrite_import(self, source: str, *, old_name: str, namespace: str) -> str:
        """Rewrite ``from mod import OldName`` to ``from mod import Namespace``."""
        pattern = re.compile(
            rf"(from\s+\S+\s+import\s+(?:.*?,\s*)?)"
            rf"\b{re.escape(old_name)}\b"
            rf"((?:\s*,.*)?)",
        )
        new_source = pattern.sub(rf"\g<1>{namespace}\2", source)
        if new_source != source:
            self._record_change(f"Rewired import: {old_name} -> {namespace}")
        return new_source

    def _qualify_name_references(
        self,
        source: str,
        *,
        old_name: str,
        qualified: str,
    ) -> str:
        """Replace bare ``OldName`` with ``Namespace.Nested`` in non-definition sites."""
        pattern = re.compile(
            rf"(?<!class\s)(?<!def\s)(?<!\.)(?<!import\s)"
            rf"\b{re.escape(old_name)}\b"
            rf"(?!\s*[=:](?!=))",
        )
        new_source, count = pattern.subn(qualified, source)
        if count > 0 and new_source != source:
            self._record_change(f"Qualified reference: {old_name} -> {qualified}")
        return new_source

    def _find_import_aliases(self, source: str, *, old_name: str) -> Sequence[str]:
        """Collect local aliases bound from ``from x import OldName as Alias``."""
        pattern = re.compile(
            rf"from\s+\S+\s+import\s+[^\n]*\b{re.escape(old_name)}\b\s+as\s+"
            rf"([A-Za-z_]\w*)",
        )
        return [match.group(1) for match in pattern.finditer(source)]

    def _qualify_alias_references(
        self,
        source: str,
        *,
        alias_name: str,
        qualified: str,
    ) -> str:
        """Replace bare alias usage with ``Alias.Nested`` outside import lines."""
        pattern = re.compile(
            rf"(?<!class\s)(?<!def\s)(?<!\.)(?<!import\s)(?<!as\s)"
            rf"\b{re.escape(alias_name)}\b"
            rf"(?!\s*[=:](?!=))",
        )
        lines = source.splitlines(keepends=True)
        changed = False
        rewritten: list[str] = []
        for line in lines:
            if line.lstrip().startswith("from ") and " import " in line:
                rewritten.append(line)
                continue
            new_line, count = pattern.subn(qualified, line)
            changed = changed or count > 0
            rewritten.append(new_line)
        new_source = "".join(rewritten)
        if changed and new_source != source:
            self._record_change(
                f"Qualified alias reference: {alias_name} -> {qualified}",
            )
        return new_source

    def _qualify_return_annotations(
        self,
        source: str,
        *,
        old_name: str,
        qualified: str,
    ) -> str:
        """Replace ``-> OldName`` with ``-> Namespace.OldName`` in signatures."""
        pattern = re.compile(rf"(->\s*)\b{re.escape(old_name)}\b")
        new_source, count = pattern.subn(rf"\1{qualified}", source)
        if count > 0 and new_source != source:
            self._record_change(
                f"Qualified return annotation: {old_name} -> {qualified}",
            )
        return new_source

    def _qualify_attribute_references(
        self,
        source: str,
        *,
        old_name: str,
        rename_parts: Sequence[str],
        aliases: Sequence[str],
    ) -> str:
        """Qualify attribute-style references like ``module.OldName``."""
        # Match: something.OldName (attribute access)
        attr_pattern = re.compile(
            rf"(\w+)\.\b{re.escape(old_name)}\b",
        )
        namespace = rename_parts[0]
        alias_names = set(aliases)
        suffix = ".".join(rename_parts)
        new_source = attr_pattern.sub(
            lambda match: (
                match.group(0)
                if match.group(1) == namespace or match.group(1) in alias_names
                else f"{match.group(1)}.{suffix}"
            ),
            source,
        )
        if new_source != source:
            self._record_change(
                f"Qualified attribute reference: .{old_name} -> .{suffix}",
            )
        return new_source

    def _should_propagate(self, symbol_name: str, policy_key: str) -> bool:
        """Check policy for a specific propagation mode."""
        policy = u.Infra.policy_for_symbol(
            policy_context=self._policy_context,
            symbol_families=self._class_families,
            symbol_name=symbol_name,
        )
        if policy is None:
            return True
        if policy_key == "propagate_imports":
            return policy.propagate_imports
        if policy_key == "propagate_name_references":
            return policy.propagate_name_references
        if policy_key == "propagate_attribute_references":
            return policy.propagate_attribute_references
        return False

    def _blocked_by_prefix(self, symbol_name: str) -> bool:
        """Check if symbol is blocked by prefix policy."""
        policy = u.Infra.policy_for_symbol(
            policy_context=self._policy_context,
            symbol_families=self._class_families,
            symbol_name=symbol_name,
        )
        if policy is None:
            return False
        return any(symbol_name.startswith(p) for p in policy.blocked_reference_prefixes)


__all__: list[str] = ["FlextInfraNestedClassPropagationTransformer"]
