from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field
from yaml import safe_load


class CanonicalValueRule(BaseModel):
    value: int | str = Field(...)
    type: str = Field(...)
    canonical_ref: str = Field(...)
    semantic_names: list[str] = Field(default_factory=list)


class NsRule(BaseModel):
    id: str = Field(...)
    description: str = Field(...)
    fixable: bool = Field(...)
    fixable_exclusion: str | None = Field(default=None)


class ConstantsGovernanceConfig(BaseModel):
    version: str = Field(...)
    rules: list[NsRule] = Field(...)
    canonical_values: list[CanonicalValueRule] = Field(...)
    constants_class_pattern: str = Field(...)


_config_cache: dict[str, ConstantsGovernanceConfig] = {}
_GOVERNANCE_FILE = Path(__file__).parent.parent / "rules" / "constants-governance.yml"


def load_governance_config() -> ConstantsGovernanceConfig:
    cached = _config_cache.get("config")
    if cached is not None:
        return cached
    payload: object = safe_load(_GOVERNANCE_FILE.read_text("utf-8"))
    data: dict[str, object]
    if isinstance(payload, dict):
        data = {str(key): value for key, value in payload.items()}
    else:
        data = {}
    config = ConstantsGovernanceConfig.model_validate(data)
    _config_cache["config"] = config
    return config


def get_canonical_int_values() -> dict[int, str]:
    config = load_governance_config()
    return {
        entry.value: entry.canonical_ref
        for entry in config.canonical_values
        if entry.type == "int" and isinstance(entry.value, int)
    }


def get_canonical_str_values() -> dict[str, str]:
    config = load_governance_config()
    return {
        entry.value: entry.canonical_ref
        for entry in config.canonical_values
        if entry.type == "str" and isinstance(entry.value, str)
    }


def get_semantic_names(canonical_ref: str) -> frozenset[str]:
    config = load_governance_config()
    for entry in config.canonical_values:
        if entry.canonical_ref == canonical_ref:
            return frozenset(entry.semantic_names)
    return frozenset()


def get_constants_class_pattern() -> str:
    return load_governance_config().constants_class_pattern


def is_rule_fixable(rule_id: str, module: str) -> bool:
    config = load_governance_config()
    for rule in config.rules:
        if rule.id != rule_id:
            continue
        if not rule.fixable:
            return False
        if rule.fixable_exclusion is None:
            return True
        return not module.endswith(rule.fixable_exclusion)
    return False


__all__ = [
    "CanonicalValueRule",
    "ConstantsGovernanceConfig",
    "NsRule",
    "get_canonical_int_values",
    "get_canonical_str_values",
    "get_constants_class_pattern",
    "get_semantic_names",
    "is_rule_fixable",
    "load_governance_config",
]
