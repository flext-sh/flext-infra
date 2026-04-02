"""Nested class reference propagation transformer — rope-based implementation."""

from __future__ import annotations

import re
from collections.abc import Sequence

from flext_infra import (
    FlextInfraRefactorTransformerPolicyUtilities,
    FlextInfraUtilitiesRope,
    t,
)
from flext_infra.transformers._base import FlextInfraRopeTransformer


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

    def transform(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> tuple[str, Sequence[str]]:
        """Apply reference propagation. Returns (new_source, changes)."""
        source = FlextInfraUtilitiesRope.read_source(resource)

        for old_name, rename_to in self._class_renames.items():
            if not self._should_propagate(old_name, "propagate_imports"):
                continue
            if self._blocked_by_prefix(old_name):
                continue

            rename_parts = rename_to.split(".")
            namespace = rename_parts[0]

            # Phase 1: Rewrite imports
            source = self._rewrite_import(
                source, old_name=old_name, namespace=namespace
            )

            # Phase 2: Qualify bare name references
            if self._should_propagate(old_name, "propagate_name_references"):
                source = self._qualify_name_references(
                    source,
                    old_name=old_name,
                    qualified=rename_to,
                )

            # Phase 3: Qualify attribute references
            if self._should_propagate(old_name, "propagate_attribute_references"):
                source = self._qualify_attribute_references(
                    source,
                    old_name=old_name,
                    rename_parts=rename_parts,
                )

        if source != FlextInfraUtilitiesRope.read_source(resource) and self.changes:
            FlextInfraUtilitiesRope.write_source(
                rope_project,
                resource,
                source,
                description="nested class propagation",
            )
        return source, list(self.changes)

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

    def _qualify_attribute_references(
        self,
        source: str,
        *,
        old_name: str,
        rename_parts: Sequence[str],
    ) -> str:
        """Qualify attribute-style references like ``module.OldName``."""
        # Match: something.OldName (attribute access)
        attr_pattern = re.compile(
            rf"(\w+)\.\b{re.escape(old_name)}\b",
        )
        suffix_parts = rename_parts[1:] if len(rename_parts) > 1 else rename_parts
        suffix = ".".join(suffix_parts)
        new_source = attr_pattern.sub(rf"\1.{suffix}", source)
        if new_source != source:
            self._record_change(
                f"Qualified attribute reference: .{old_name} -> .{suffix}",
            )
        return new_source

    def _should_propagate(self, symbol_name: str, policy_key: str) -> bool:
        """Check policy for a specific propagation mode."""
        policy = FlextInfraRefactorTransformerPolicyUtilities.policy_for_symbol(
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
        policy = FlextInfraRefactorTransformerPolicyUtilities.policy_for_symbol(
            policy_context=self._policy_context,
            symbol_families=self._class_families,
            symbol_name=symbol_name,
        )
        if policy is None:
            return False
        return any(symbol_name.startswith(p) for p in policy.blocked_reference_prefixes)


__all__ = ["FlextInfraNestedClassPropagationTransformer"]
