"""Validation of declarative refactor rule definitions."""

from __future__ import annotations

from collections.abc import Mapping

from pydantic import JsonValue

from flext_infra.constants import c


class FlextInfraRefactorRuleDefinitionValidator:
    def validate_rule_definition(
        self,
        rule_def: Mapping[str, JsonValue],
    ) -> str | None:
        """Return validation error text or None when rule definition is valid."""
        rule_id = str(rule_def.get(c.Infra.ReportKeys.ID, c.Infra.Defaults.UNKNOWN))
        fix_action = (
            str(rule_def.get(c.Infra.ReportKeys.FIX_ACTION, "")).strip().lower()
        )
        if not fix_action:
            return None
        if fix_action in c.Infra.PROPAGATION_FIX_ACTIONS:
            if fix_action == "propagate_symbol_renames" and (
                not isinstance(rule_def.get("import_symbol_renames"), dict)
            ):
                return f"{rule_id}: import_symbol_renames must be a mapping"
            if fix_action == "propagate_signature_migrations":
                migrations = rule_def.get("signature_migrations")
                if not isinstance(migrations, list) or not migrations:
                    return f"{rule_id}: signature_migrations must be a non-empty list"
        if fix_action == "remove_redundant_casts":
            targets = rule_def.get("redundant_type_targets")
            if not isinstance(targets, list) or not targets:
                return f"{rule_id}: redundant_type_targets must be a non-empty list"
        return None


__all__ = ["FlextInfraRefactorRuleDefinitionValidator"]
