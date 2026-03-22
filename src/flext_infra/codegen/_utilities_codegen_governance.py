from __future__ import annotations

from pathlib import Path
from typing import ClassVar, Final

from yaml import safe_load

from flext_infra import m, t


class FlextInfraUtilitiesCodegenGovernance:
    _config_cache: ClassVar[dict[str, m.Infra.ConstantsGovernanceConfig]] = {}
    GOVERNANCE_FILE: Final[Path] = (
        Path(__file__).parent.parent / "rules" / "constants-governance.yml"
    )

    @staticmethod
    def load_governance_config() -> m.Infra.ConstantsGovernanceConfig:
        cached = FlextInfraUtilitiesCodegenGovernance._config_cache.get("config")
        if cached is not None:
            return cached
        raw: dict[str, t.NormalizedValue] = (
            safe_load(
                FlextInfraUtilitiesCodegenGovernance.GOVERNANCE_FILE.read_text("utf-8"),
            )
            or {}
        )
        config = m.Infra.ConstantsGovernanceConfig.model_validate(raw)
        FlextInfraUtilitiesCodegenGovernance._config_cache["config"] = config
        return config

    @staticmethod
    def get_canonical_int_values() -> dict[int, str]:
        config = FlextInfraUtilitiesCodegenGovernance.load_governance_config()
        return {
            entry.value: entry.canonical_ref
            for entry in config.canonical_values
            if entry.type == "int" and isinstance(entry.value, int)
        }

    @staticmethod
    def get_canonical_str_values() -> dict[str, str]:
        config = FlextInfraUtilitiesCodegenGovernance.load_governance_config()
        return {
            entry.value: entry.canonical_ref
            for entry in config.canonical_values
            if entry.type == "str" and isinstance(entry.value, str)
        }

    @staticmethod
    def get_semantic_names(canonical_ref: str) -> frozenset[str]:
        config = FlextInfraUtilitiesCodegenGovernance.load_governance_config()
        for entry in config.canonical_values:
            if entry.canonical_ref == canonical_ref:
                return frozenset(entry.semantic_names)
        return frozenset()

    @staticmethod
    def get_constants_class_pattern() -> str:
        return FlextInfraUtilitiesCodegenGovernance.load_governance_config().constants_class_pattern

    @staticmethod
    def is_rule_fixable(rule_id: str, module: str) -> bool:
        config = FlextInfraUtilitiesCodegenGovernance.load_governance_config()
        for rule in config.rules:
            if rule.id != rule_id:
                continue
            if not rule.fixable:
                return False
            if rule.fixable_exclusion is None:
                return True
            return not module.endswith(rule.fixable_exclusion)
        return False


__all__ = ["FlextInfraUtilitiesCodegenGovernance"]
