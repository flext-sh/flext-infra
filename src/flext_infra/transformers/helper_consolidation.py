"""Helper consolidation transformer — rope-based implementation."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import override

from flext_infra import (
    FlextInfraRopeTransformer,
    m,
    t,
    u,
)


class FlextInfraHelperConsolidationTransformer(FlextInfraRopeTransformer):
    """Move top-level helper functions into target namespace classes."""

    def __init__(
        self,
        helper_mappings: t.StrMapping,
        policy_context: t.Infra.PolicyContext | None = None,
        helper_families: t.StrMapping | None = None,
        on_change: t.Infra.ChangeCallback = None,
    ) -> None:
        """Initialize with helper-to-namespace mappings and optional policy."""
        super().__init__(on_change=on_change)
        self._mappings = helper_mappings
        self._policy_context = policy_context
        self._families = helper_families or {}

    _description = "helper consolidation"

    @override
    def apply_to_source(self, source: str) -> t.Infra.TransformResult:
        """Apply helper consolidation to in-memory source without persisting."""
        updated = source
        collected: dict[str, list[str]] = defaultdict(list)
        for name, ns in self._mappings.items():
            if not u.Infra.has_toplevel_definition(updated, name, kind="function"):
                continue
            if not self._policy_ok(name, ns, "enable_helper_consolidation"):
                continue
            if not self._sig_allowed(updated, name):
                continue
            collected[ns].append(name)
        for namespace, helpers in collected.items():
            for name in helpers:
                func_src = u.Infra.extract_definition(updated, name, kind="function")
                if func_src is None:
                    continue
                updated = u.Infra.remove_definition(updated, name, kind="function")
                func_src = u.Infra.ensure_decorator(func_src)
                indented = u.Infra.indent_block(func_src)
                updated = u.Infra.append_to_class_body(updated, namespace, indented)
                self._record_change(f"Moved {name} into {namespace}")
        updated = self._rewrite_calls(updated)
        return updated, list(self.changes)

    def _rewrite_calls(self, source: str) -> str:
        for name, ns in self._mappings.items():
            if not self._policy_ok(name, ns, "allow_helper_call_rewrite"):
                continue
            pat = re.compile(rf"(?<!\.)(?<!class\s)(?<!def\s)\b{re.escape(name)}\s*\(")
            new = pat.sub(f"{ns}.{name}(", source)
            if new != source:
                self._record_change(f"Rewritten call: {name}() -> {ns}.{name}()")
                source = new
        return source

    def _policy_ok(self, name: str, target_ns: str, attr: str) -> bool:
        policy = self._policy_for(name)
        if policy is None:
            return True
        if not getattr(policy, attr, True):
            return False
        return u.Infra.target_allowed(
            policy=policy,
            target_namespace=target_ns,
        )

    def _sig_allowed(self, source: str, name: str) -> bool:
        policy = self._policy_for(name)
        if policy is None or not policy.require_signature_validation:
            return True
        sig_pat = re.compile(rf"def\s+{re.escape(name)}\s*\(([^)]*)\)", re.DOTALL)
        match = sig_pat.search(source)
        if match is None:
            return True
        params_str = match.group(1)
        param_names = u.Infra.parse_param_names(params_str)
        if any(r not in param_names for r in policy.required_parameters):
            return False
        if any(f in param_names for f in policy.forbidden_parameters):
            return False
        if not policy.allow_vararg and "*args" in params_str:
            return False
        return not (not policy.allow_kwarg and "**" in params_str)

    def _policy_for(self, name: str) -> m.Infra.ClassNestingPolicy | None:
        return u.Infra.policy_for_symbol(
            policy_context=self._policy_context,
            symbol_families=self._families,
            symbol_name=name,
        )


__all__ = ["FlextInfraHelperConsolidationTransformer"]
