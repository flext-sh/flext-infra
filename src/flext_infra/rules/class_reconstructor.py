"""Pre-check gate and class nesting reconstruction utilities.

FlextInfraPreCheckGate and FlextInfraRefactorClassNestingReconstructor are
used by class_nesting.py. The thin wrapper FlextInfraRefactorClassReconstructorRule
has been inlined into engine.py.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

import libcst as cst
from pydantic import JsonValue, ValidationError

from flext_infra import (
    INFRA_MAPPING_ADAPTER,
    FlextInfraNestedClassPropagationTransformer,
    c,
    m,
    t,
    u,
)


class FlextInfraPreCheckGate:
    """Gate that validates class nesting entries against a YAML policy matrix."""

    def __init__(self, policy_path: Path | None = None) -> None:
        """Initialize with optional custom policy path."""
        self._policy_path = policy_path or Path(__file__).with_name(
            "class-policy-v2.yml",
        )
        self._schema_path = self._policy_path.with_name("class-policy-v2.schema.json")
        self._policy_by_family: Mapping[str, m.Infra.ClassNestingPolicy] = (
            self._load_policy()
        )

    def validate_entry(
        self,
        entry: t.StrMapping,
    ) -> t.Infra.Pair[bool, t.StrMapping | None]:
        """Validate a single class-nesting entry against the loaded policy."""
        source_symbol = entry.get(c.Infra.ReportKeys.LOOSE_NAME, "")
        helper_symbol = entry.get("helper_name", "")
        symbol = source_symbol or helper_symbol
        target_namespace = entry.get(c.Infra.ReportKeys.TARGET_NAMESPACE, "")
        current_file = entry.get(c.Infra.ReportKeys.CURRENT_FILE, "")
        if not symbol or not target_namespace or (not current_file):
            return (True, None)
        module_family = u.Infra.module_family_from_path(current_file)
        if module_family == "other_private":
            return (True, None)
        violation = self._check_policy_violation(
            entry_symbol=symbol,
            module_family=module_family,
            target_namespace=target_namespace,
            is_helper=bool(helper_symbol),
        )
        if violation is not None:
            return (False, violation)
        return (True, None)

    def _check_policy_violation(
        self,
        *,
        entry_symbol: str,
        module_family: str,
        target_namespace: str,
        is_helper: bool,
    ) -> t.StrMapping | None:
        """Return a violation dict if policy is violated, else None."""
        policy = self._policy_by_family.get(module_family)
        if policy is None:
            return self._violation(
                entry_symbol,
                "unknown_module_family",
                f"declare explicit policy for {module_family}",
            )
        operation = (
            c.Infra.ReportKeys.HELPER_CONSOLIDATION
            if is_helper
            else c.Infra.ReportKeys.CLASS_NESTING
        )
        if operation not in policy.allowed_operations:
            return self._violation(
                entry_symbol,
                "operation_not_allowed",
                f"allow {operation} in policy for {module_family}",
            )
        if operation in policy.forbidden_operations:
            return self._violation(
                entry_symbol,
                "operation_forbidden",
                f"remove {operation} from forbidden_operations for {module_family}",
            )
        if any(
            self._target_matches(target_namespace, pattern)
            for pattern in policy.forbidden_targets
        ):
            return self._violation(
                entry_symbol,
                "forbidden_target",
                f"choose allowed target for family {module_family}",
            )
        return None

    @staticmethod
    def _violation(symbol: str, violation_type: str, fix: str) -> t.StrMapping:
        """Build a standardized precheck violation dict."""
        return {
            c.Infra.ReportKeys.RULE_ID: f"precheck:{symbol}",
            c.Infra.ReportKeys.SOURCE_SYMBOL: symbol,
            c.Infra.ReportKeys.VIOLATION_TYPE: violation_type,
            c.Infra.ReportKeys.SUGGESTED_FIX: fix,
        }

    def _load_policy(self) -> Mapping[str, m.Infra.ClassNestingPolicy]:
        try:
            loaded = u.Infra.safe_load_yaml(self._policy_path)
        except (OSError, TypeError):
            return {}
        loaded_dict: Mapping[str, t.Infra.InfraValue] = (
            INFRA_MAPPING_ADAPTER.validate_python(dict(loaded))
        )
        if not self._schema_valid(loaded_dict):
            return {}
        policy_matrix = u.Infra.mapping_list(loaded_dict.get("policy_matrix"))
        by_family: MutableMapping[str, m.Infra.ClassNestingPolicy] = {}
        for raw in policy_matrix:
            try:
                policy = m.Infra.ClassNestingPolicy.model_validate(raw)
            except ValidationError:
                continue
            by_family[policy.family_name] = policy
        return by_family

    def _schema_valid(self, loaded: Mapping[str, t.Infra.InfraValue]) -> bool:
        schema_result = u.Infra.read_json(self._schema_path)
        if schema_result.is_failure:
            return True
        schema: Mapping[str, JsonValue] = dict(schema_result.value)
        top_required = u.Infra.string_list(schema.get("required"))
        if not u.Infra.has_required_fields(loaded, top_required):
            return False
        definitions_raw: JsonValue | None = schema.get("definitions")
        if not u.is_mapping(definitions_raw):
            return False
        required_defs = self._extract_definition_requirements(definitions_raw)
        if required_defs is None:
            return False
        policy_entry_required, class_rule_required = required_defs
        return self._all_entries_valid(
            loaded,
            policy_entry_required,
            class_rule_required,
        )

    @staticmethod
    def _extract_definition_requirements(
        definitions: Mapping[str, JsonValue],
    ) -> tuple[t.StrSequence, t.StrSequence] | None:
        """Extract required field lists from schema definitions. None if invalid."""
        policy_entry_raw: JsonValue | None = definitions.get("policyEntry")
        class_rule_raw: JsonValue | None = definitions.get("classRule")
        if not u.is_mapping(policy_entry_raw) or not u.is_mapping(
            class_rule_raw,
        ):
            return None
        return (
            u.Infra.string_list(policy_entry_raw.get("required")),
            u.Infra.string_list(class_rule_raw.get("required")),
        )

    @staticmethod
    def _all_entries_valid(
        loaded: Mapping[str, t.Infra.InfraValue],
        policy_entry_required: t.StrSequence,
        class_rule_required: t.StrSequence,
    ) -> bool:
        """Validate all policy_matrix and rules entries against required fields."""
        policy_matrix = u.Infra.mapping_list(loaded.get("policy_matrix"))
        if not all(
            u.Infra.has_required_fields(entry, policy_entry_required)
            for entry in policy_matrix
        ):
            return False
        rules = u.Infra.mapping_list(loaded.get(c.Infra.ReportKeys.RULES))
        return all(
            u.Infra.has_required_fields(rule, class_rule_required) for rule in rules
        )

    def _target_matches(self, target_namespace: str, pattern: str) -> bool:
        if pattern.endswith(".*"):
            return target_namespace.lower().startswith(pattern[:-2].lower())
        return target_namespace == pattern


class FlextInfraRefactorClassNestingReconstructor:
    """Reconstruct class nesting by applying rename mappings and propagation."""

    @staticmethod
    def class_rename_mappings(
        entries: Sequence[t.StrMapping],
    ) -> t.StrMapping:
        """Build a mapping of loose class names to their nested target names."""
        mappings: t.MutableStrMapping = {}
        for entry in entries:
            loose_name = entry.get(c.Infra.ReportKeys.LOOSE_NAME)
            target_namespace = entry.get(c.Infra.ReportKeys.TARGET_NAMESPACE)
            target_name = entry.get("target_name")
            if not isinstance(loose_name, str):
                continue
            if not isinstance(target_namespace, str):
                continue
            if not isinstance(target_name, str):
                continue
            mappings[loose_name] = f"{target_namespace}.{target_name}"
        return mappings

    @staticmethod
    def apply_nested_class_propagation(
        tree: cst.Module,
        mappings: t.StrMapping,
        changes: MutableSequence[str],
        policy_context: t.Infra.PolicyContext,
        class_families: t.StrMapping,
    ) -> cst.Module:
        """Apply nested class propagation transforms using the given rename mappings."""
        transformer = FlextInfraNestedClassPropagationTransformer(
            class_renames=mappings,
            policy_context=policy_context,
            class_families=class_families,
        )
        updated_tree = tree.visit(transformer)
        if updated_tree.code != tree.code:
            changes.append(
                f"Applied FlextInfraNestedClassPropagationTransformer ({len(mappings)} renames)",
            )
        return updated_tree


__all__ = [
    "FlextInfraPreCheckGate",
    "FlextInfraRefactorClassNestingReconstructor",
]
