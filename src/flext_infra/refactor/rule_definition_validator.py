"""Validation of declarative refactor rule definitions."""

from __future__ import annotations

from collections.abc import Mapping

from flext_infra import c, t, u


class FlextInfraRefactorRuleDefinitionValidator:
    """Validator for declarative refactor rule definitions."""

    def validate_rule_definition(
        self,
        rule_def: Mapping[str, t.Infra.InfraValue],
    ) -> str | None:
        """Return validation error text or None when rule definition is valid."""
        rule_id = str(rule_def.get(c.Infra.RK_ID, c.Infra.DEFAULT_UNKNOWN))
        fix_action = u.Infra.get_str_key(rule_def, c.Infra.RK_FIX_ACTION, case="lower")
        if not fix_action:
            return None
        if fix_action in c.Infra.PROPAGATION_FIX_ACTIONS:
            if fix_action == "propagate_symbol_renames" and (
                not u.is_mapping(rule_def.get("import_symbol_renames"))
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
