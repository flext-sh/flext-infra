"""Class nesting transformer — rope-based implementation."""

from __future__ import annotations

import textwrap
from collections import defaultdict
from collections.abc import Sequence
from typing import override

from flext_infra import (
    FlextInfraRefactorTransformerPolicyUtilities,
    FlextInfraRopeTransformer,
    m,
    t,
    u,
)


class FlextInfraRefactorClassNestingTransformer(FlextInfraRopeTransformer):
    """Transform top-level classes into nested classes under namespace parents."""

    def __init__(
        self,
        mappings: t.StrMapping,
        policy_context: t.Infra.PolicyContext,
        class_families: t.StrMapping,
        on_change: t.Infra.ChangeCallback = None,
    ) -> None:
        """Initialize with class-to-namespace mappings and policy context."""
        super().__init__(on_change=on_change)
        self._mappings = mappings
        self._policy_context = policy_context
        self._class_families = class_families

    @override
    def transform(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> tuple[str, Sequence[str]]:
        """Apply class nesting. Returns (new_source, changes)."""
        source = u.read_source(resource)
        class_infos = u.get_class_info(rope_project, resource)
        existing_names = {info.name for info in class_infos}

        collected: dict[str, list[str]] = defaultdict(list)
        for class_name, target_namespace in self._mappings.items():
            if class_name not in existing_names:
                continue
            if not self._is_nesting_allowed(class_name, target_namespace):
                continue
            collected[target_namespace].append(class_name)

        if not collected:
            return source, []

        for namespace, class_names in collected.items():
            if not self._ns_op_allowed(class_names, namespace, "creation"):
                continue
            ns_exists = namespace in existing_names
            if ns_exists and not self._ns_op_allowed(class_names, namespace, "merge"):
                continue
            source = self._nest_classes(
                source,
                namespace=namespace,
                class_names=class_names,
                ns_exists=ns_exists,
            )
            existing_names.add(namespace)

        if source != u.read_source(resource) and self.changes:
            u.write_source(
                rope_project,
                resource,
                source,
                description="class nesting",
            )
        return source, list(self.changes)

    def _nest_classes(
        self,
        source: str,
        *,
        namespace: str,
        class_names: Sequence[str],
        ns_exists: bool,
    ) -> str:
        extracted: list[str] = []
        for class_name in class_names:
            block = u.extract_definition(source, class_name, kind="class")
            if block is None:
                continue
            extracted.append(textwrap.indent(block, "    "))
            source = u.remove_definition(source, class_name, kind="class")
            self._record_change(f"Nested {class_name} into {namespace}")
        if not extracted:
            return source
        nested_block = "\n".join(extracted)
        if ns_exists:
            return u.append_to_class_body(source, namespace, nested_block)
        return source.rstrip("\n") + f"\n\nclass {namespace}:\n{nested_block}\n"

    def _is_nesting_allowed(self, class_name: str, target_namespace: str) -> bool:
        policy = self._policy_for(class_name)
        if policy is None:
            return True
        if not policy.enable_class_nesting:
            return False
        return FlextInfraRefactorTransformerPolicyUtilities.target_allowed(
            policy=policy,
            target_namespace=target_namespace,
        )

    def _ns_op_allowed(
        self,
        class_names: Sequence[str],
        target_namespace: str,
        operation: str,
    ) -> bool:
        for class_name in class_names:
            policy = self._policy_for(class_name)
            if policy is None:
                continue
            if operation == "creation" and not policy.allow_namespace_creation:
                return False
            if operation == "merge" and not policy.allow_existing_namespace_merge:
                return False
            if not FlextInfraRefactorTransformerPolicyUtilities.target_allowed(
                policy=policy,
                target_namespace=target_namespace,
            ):
                return False
        return True

    def _policy_for(self, symbol_name: str) -> m.Infra.ClassNestingPolicy | None:
        return FlextInfraRefactorTransformerPolicyUtilities.policy_for_symbol(
            policy_context=self._policy_context,
            symbol_families=self._class_families,
            symbol_name=symbol_name,
        )


__all__ = ["FlextInfraRefactorClassNestingTransformer"]
