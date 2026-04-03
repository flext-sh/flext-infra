"""Class-nesting policy validation utilities for the refactor subpackage.

Handles policy document loading, schema validation, and class nesting
policy enforcement.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from pydantic import JsonValue, ValidationError

from flext_core import FlextUtilities
from flext_infra import (
    FlextInfraUtilitiesIo,
    FlextInfraUtilitiesYaml,
    c,
    m,
    t,
)


class FlextInfraUtilitiesRefactorPolicy:
    """Policy document loading and class-nesting policy enforcement."""

    @staticmethod
    def policy_document_schema_valid(
        loaded: Mapping[str, t.Infra.InfraValue],
        schema_path: Path,
    ) -> bool:
        schema_result = FlextInfraUtilitiesIo.read_json(schema_path)
        if schema_result.is_failure:
            return False
        raw_schema: Mapping[str, JsonValue] = schema_result.value
        schema: Mapping[str, t.Infra.InfraValue] = dict(raw_schema)
        from flext_infra import FlextInfraUtilitiesRefactor  # noqa: PLC0415

        top_required = FlextInfraUtilitiesRefactor.string_list(
            schema.get("required", []),
        )
        if not FlextInfraUtilitiesRefactor.has_required_fields(loaded, top_required):
            return False
        definitions_raw = schema.get("definitions", {})
        if not FlextUtilities.is_mapping(definitions_raw):
            return False
        try:
            definitions = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(definitions_raw)
        except ValidationError:
            return False

        def _definition_required(key: str) -> t.StrSequence | None:
            raw = definitions.get(key, {})
            if not FlextUtilities.is_mapping(raw):
                return None
            validated: Mapping[str, t.Infra.InfraValue] = (
                t.Infra.INFRA_MAPPING_ADAPTER.validate_python(raw)
            )
            return FlextInfraUtilitiesRefactor.string_list(
                validated.get("required", []),
            )

        def _all_have_required(field: str, required: t.StrSequence) -> bool:
            return all(
                FlextInfraUtilitiesRefactor.has_required_fields(entry, required)
                for entry in FlextInfraUtilitiesRefactor.mapping_list(
                    loaded.get(field),
                )
            )

        policy_req = _definition_required("policyEntry")
        rule_req = _definition_required("classRule")
        if policy_req is None or rule_req is None:
            return False
        return _all_have_required(
            "policy_matrix",
            policy_req,
        ) and _all_have_required(c.Infra.ReportKeys.RULES, rule_req)

    @staticmethod
    def load_validated_policy_document(policy_path: Path) -> t.Infra.ContainerDict:
        try:
            loaded = FlextInfraUtilitiesYaml.safe_load_yaml(policy_path)
        except (OSError, TypeError) as exc:
            msg = f"failed to read policy document: {policy_path}"
            raise ValueError(msg) from exc
        raw_dict: Mapping[str, t.Infra.InfraValue] = dict(loaded)
        loaded_dict: t.Infra.ContainerDict = (
            t.Infra.INFRA_MAPPING_ADAPTER.validate_python(
                raw_dict,
            )
        )
        schema_path = policy_path.with_name("class-policy-v2.schema.json")
        if not FlextInfraUtilitiesRefactorPolicy.policy_document_schema_valid(
            loaded_dict,
            schema_path,
        ):
            msg = "policy document failed schema validation"
            raise ValueError(msg)
        return loaded_dict

    @staticmethod
    def default_class_policy_path() -> Path:
        """Return the canonical class-nesting policy document path."""
        return Path(__file__).resolve().parent.parent / "rules" / "class-policy-v2.yml"

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
        try:
            loaded = FlextInfraUtilitiesRefactorPolicy.load_validated_policy_document(
                resolved_path
            )
        except ValueError:
            return {}
        by_family: dict[str, m.Infra.ClassNestingPolicy] = {}
        for raw in FlextInfraUtilitiesRefactorPolicy._mapping_list_for_policy(
            loaded.get("policy_matrix"),
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
        """Thin wrapper to call mapping_list from the main facade."""
        from flext_infra import FlextInfraUtilitiesRefactor  # noqa: PLC0415

        return list(FlextInfraUtilitiesRefactor.mapping_list(value))

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
        from flext_infra import FlextInfraUtilitiesRefactor  # noqa: PLC0415

        symbol = entry.get(c.Infra.ReportKeys.LOOSE_NAME, "") or entry.get(
            "helper_name",
            "",
        )
        target_namespace = entry.get(c.Infra.ReportKeys.TARGET_NAMESPACE, "")
        current_file = entry.get(c.Infra.ReportKeys.CURRENT_FILE, "")
        if not symbol or not target_namespace or not current_file:
            return (True, None)
        family = FlextInfraUtilitiesRefactor.module_family_from_path(current_file)
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
