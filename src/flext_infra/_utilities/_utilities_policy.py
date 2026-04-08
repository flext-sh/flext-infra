"""Class-nesting policy validation utilities for the refactor subpackage.

Handles policy document loading, schema validation, and class nesting
policy enforcement.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path

from pydantic import ValidationError

from flext_cli import FlextCliUtilitiesYaml as _CliYaml
from flext_core import u
from flext_infra import (
    c,
    m,
    r,
    t,
)


class FlextInfraUtilitiesRefactorPolicy(_CliYaml):
    """Policy document loading and class-nesting policy enforcement."""

    _MODULE_FAMILY_KEYS: t.StrSequence = (
        "_models",
        "_utilities",
        "_dispatcher",
        "_decorators",
        "_runtime",
    )

    @staticmethod
    def default_class_policy_path() -> Path:
        """Return the default class-nesting policy YAML path."""
        return Path(__file__).resolve().parent.parent / "rules" / "class-policy-v2.yml"

    @staticmethod
    def load_validated_policy_document(
        policy_path: Path,
    ) -> r[Mapping[str, t.Infra.InfraValue]]:
        """Load and validate a YAML policy document."""
        raw = FlextInfraUtilitiesRefactorPolicy.yaml_load_mapping(policy_path)
        if not raw:
            return r[Mapping[str, t.Infra.InfraValue]].fail(
                f"Failed to load policy {policy_path}",
            )
        validated = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(raw)
        return r[Mapping[str, t.Infra.InfraValue]].ok(validated)

    @staticmethod
    def class_nesting_policy_by_family(
        policy_path: Path | None = None,
    ) -> Mapping[str, m.Infra.ClassNestingPolicy]:
        """Load the class-nesting policy matrix keyed by module family."""
        resolved_path = (
            policy_path
            if policy_path is not None
            else FlextInfraUtilitiesRefactorPolicy.default_class_policy_path()
        )
        loaded = FlextInfraUtilitiesRefactorPolicy.load_validated_policy_document(
            resolved_path,
        )
        if loaded.is_failure:
            return {}
        by_family: dict[str, m.Infra.ClassNestingPolicy] = {}
        for raw in FlextInfraUtilitiesRefactorPolicy._mapping_list_for_policy(
            loaded.value.get("policy_matrix"),
        ):
            try:
                policy = m.Infra.ClassNestingPolicy.model_validate(raw)
            except ValidationError:
                continue
            by_family[policy.family_name] = policy
        return by_family

    @staticmethod
    def _mapping_list_for_policy(
        value: t.Infra.InfraValue | None,
    ) -> list[Mapping[str, t.Infra.InfraValue]]:
        """Normalize policy fields that should contain mapping collections."""
        return list(FlextInfraUtilitiesRefactorPolicy.mapping_list(value))

    @staticmethod
    def module_family_from_path(path: str) -> str:
        """Resolve module family key from a source file path."""
        normalized = path.replace("\\", "/")
        for key in FlextInfraUtilitiesRefactorPolicy._MODULE_FAMILY_KEYS:
            if key in normalized:
                return key
        return "other_private"

    @staticmethod
    def mapping_list(
        value: t.Infra.InfraValue | None,
    ) -> Sequence[Mapping[str, t.Infra.InfraValue]]:
        """Normalize policy fields that should contain mapping collections."""
        if value is None:
            return []
        if not isinstance(value, list):
            msg = "expected Sequence[Mapping[str, t.Infra.InfraValue]] value"
            raise TypeError(msg)
        try:
            value_items: Sequence[t.Infra.InfraValue] = (
                t.Infra.INFRA_SEQ_ADAPTER.validate_python(value)
            )
        except ValidationError as exc:
            msg = "expected Sequence[Mapping[str, t.Infra.InfraValue]] value"
            raise ValueError(msg) from exc
        normalized: MutableSequence[Mapping[str, t.Infra.InfraValue]] = []
        for item in value_items:
            if not u.is_mapping(item):
                continue
            normalized.append(t.Infra.INFRA_MAPPING_ADAPTER.validate_python(item))
        return normalized

    @staticmethod
    def _class_nesting_target_matches(target_namespace: str, pattern: str) -> bool:
        """Check whether a target namespace matches a forbidden-target pattern."""
        if pattern.endswith(".*"):
            return target_namespace.lower().startswith(pattern[:-2].lower())
        return target_namespace == pattern

    @staticmethod
    def _class_nesting_violation(
        *,
        symbol: str,
        family: str,
        target_namespace: str,
        is_helper: bool,
        policy_by_family: Mapping[str, m.Infra.ClassNestingPolicy],
    ) -> t.StrMapping | None:
        """Build a policy violation payload when class nesting is forbidden."""
        policy = policy_by_family.get(family)
        if policy is None:
            return {
                c.Infra.ReportKeys.RULE_ID: f"precheck:{symbol}",
                c.Infra.ReportKeys.SOURCE_SYMBOL: symbol,
                c.Infra.ReportKeys.VIOLATION_TYPE: "unknown_module_family",
                c.Infra.ReportKeys.SUGGESTED_FIX: (
                    f"declare explicit policy for {family}"
                ),
            }
        operation = (
            c.Infra.ReportKeys.HELPER_CONSOLIDATION
            if is_helper
            else c.Infra.ReportKeys.CLASS_NESTING
        )
        if operation not in policy.allowed_operations:
            return {
                c.Infra.ReportKeys.RULE_ID: f"precheck:{symbol}",
                c.Infra.ReportKeys.SOURCE_SYMBOL: symbol,
                c.Infra.ReportKeys.VIOLATION_TYPE: "operation_not_allowed",
                c.Infra.ReportKeys.SUGGESTED_FIX: (
                    f"allow {operation} in policy for {family}"
                ),
            }
        if operation in policy.forbidden_operations:
            return {
                c.Infra.ReportKeys.RULE_ID: f"precheck:{symbol}",
                c.Infra.ReportKeys.SOURCE_SYMBOL: symbol,
                c.Infra.ReportKeys.VIOLATION_TYPE: "operation_forbidden",
                c.Infra.ReportKeys.SUGGESTED_FIX: (
                    f"remove {operation} from forbidden_operations for {family}"
                ),
            }
        if any(
            FlextInfraUtilitiesRefactorPolicy._class_nesting_target_matches(
                target_namespace,
                pattern,
            )
            for pattern in policy.forbidden_targets
        ):
            return {
                c.Infra.ReportKeys.RULE_ID: f"precheck:{symbol}",
                c.Infra.ReportKeys.SOURCE_SYMBOL: symbol,
                c.Infra.ReportKeys.VIOLATION_TYPE: "forbidden_target",
                c.Infra.ReportKeys.SUGGESTED_FIX: (
                    f"choose allowed target for family {family}"
                ),
            }
        return None

    @staticmethod
    def validate_class_nesting_entry(
        entry: t.StrMapping,
        *,
        policy_by_family: Mapping[str, m.Infra.ClassNestingPolicy] | None = None,
        policy_path: Path | None = None,
    ) -> t.Infra.Pair[bool, t.StrMapping | None]:
        """Validate one class/helper nesting entry against the family policy."""
        symbol = entry.get(c.Infra.ReportKeys.LOOSE_NAME, "") or entry.get(
            "helper_name",
            "",
        )
        target_namespace = entry.get(c.Infra.ReportKeys.TARGET_NAMESPACE, "")
        current_file = entry.get(c.Infra.ReportKeys.CURRENT_FILE, "")
        if not symbol or not target_namespace or not current_file:
            return (True, None)
        family = FlextInfraUtilitiesRefactorPolicy.module_family_from_path(current_file)
        if family == "other_private":
            return (True, None)
        policies = (
            policy_by_family
            if policy_by_family is not None
            else FlextInfraUtilitiesRefactorPolicy.class_nesting_policy_by_family(
                policy_path,
            )
        )
        violation = FlextInfraUtilitiesRefactorPolicy._class_nesting_violation(
            symbol=symbol,
            family=family,
            target_namespace=target_namespace,
            is_helper=bool(entry.get("helper_name", "")),
            policy_by_family=policies,
        )
        return (False, violation) if violation is not None else (True, None)


__all__ = ["FlextInfraUtilitiesRefactorPolicy"]
