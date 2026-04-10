"""Rule loader for flext_infra.refactor."""

from __future__ import annotations

import fnmatch
from collections.abc import Callable, Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

from pydantic import ValidationError

from flext_infra import (
    FlextInfraClassNestingRefactorRule,
    FlextInfraRefactorRule,
    FlextInfraRefactorRuleDefinitionValidator,
    c,
    m,
    r,
    t,
    u,
)


class FlextInfraUtilitiesRefactorRuleLoader:
    """Load and resolve refactor rules from YAML configuration files."""

    _ENGINE_REGISTRY_FILENAME: str = "engine-registry.yml"
    _ENGINE_CONFIG_KEYS: tuple[str, ...] = (
        "project_scan_dirs",
        "ignore_patterns",
        "file_extensions",
    )

    def __init__(self, config_path: Path) -> None:
        """Initialize with path to the refactor engine configuration file."""
        self.config_path = config_path

    def load_config(self) -> r[Mapping[str, t.Infra.InfraValue]]:
        """Load and validate the refactor engine configuration."""
        try:
            loaded = u.Cli.yaml_load_mapping(self.config_path)
            normalized: MutableMapping[str, t.Infra.InfraValue] = dict(
                t.Infra.INFRA_MAPPING_ADAPTER.validate_python(dict(loaded)),
            )
            scope_raw = normalized.get("refactor_engine")
            scope_map = u.Infra.normalize_str_mapping(scope_raw)
            scope_map = {
                key: value
                for key, value in scope_map.items()
                if key in self._ENGINE_CONFIG_KEYS
            }
            scope = m.Infra.EngineConfig.model_validate(scope_map)
            normalized["refactor_engine"] = scope.model_dump(mode="python")
            return r[Mapping[str, t.Infra.InfraValue]].ok(normalized)
        except (OSError, TypeError, ValueError) as exc:
            return r[Mapping[str, t.Infra.InfraValue]].fail(
                f"Failed to load config: {exc}",
            )

    def extract_engine_file_filters(
        self,
        config: t.Infra.InfraValue,
    ) -> t.Infra.Pair[t.StrSequence, t.StrSequence]:
        """Extract ignore patterns and file extensions from engine config."""
        scope = self._resolve_engine_config(config)
        return (list(scope.ignore_patterns), list(scope.file_extensions))

    def extract_project_scan_dirs(self, config: t.Infra.InfraValue) -> t.StrSequence:
        """Extract project scan directories from engine config."""
        scope = self._resolve_engine_config(config)
        return list(scope.project_scan_dirs)

    def load_engine_registry(self) -> r[Mapping[str, t.Infra.InfraValue]]:
        """Load declarative engine dispatch metadata from rules directory."""
        package_registry = self._package_rules_dir() / self._ENGINE_REGISTRY_FILENAME
        candidates = [self._resolve_rules_dir() / self._ENGINE_REGISTRY_FILENAME]
        if package_registry not in candidates:
            candidates.append(package_registry)
        for registry_path in candidates:
            if not registry_path.is_file():
                continue
            try:
                loaded = u.Cli.yaml_load_mapping(registry_path)
                normalized = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(dict(loaded))
                return r[Mapping[str, t.Infra.InfraValue]].ok(normalized)
            except (OSError, TypeError, ValueError) as exc:
                return r[Mapping[str, t.Infra.InfraValue]].fail(
                    f"Failed to load engine registry: {exc}",
                )
        return r[Mapping[str, t.Infra.InfraValue]].fail(
            "Failed to load engine registry: no engine-registry.yml found",
        )

    def load_rules(
        self,
        rule_filters: t.StrSequence,
        validator: FlextInfraRefactorRuleDefinitionValidator,
        build_rule: Callable[
            [Mapping[str, t.Infra.InfraValue]],
            FlextInfraRefactorRule | None,
        ],
        build_file_rules: Callable[[], Sequence[FlextInfraClassNestingRefactorRule]],
        skip_rule_definition: Callable[[Mapping[str, t.Infra.InfraValue]], bool],
    ) -> r[
        tuple[
            Sequence[FlextInfraRefactorRule],
            Sequence[FlextInfraClassNestingRefactorRule],
        ]
    ]:
        """Load rules from YAML files, validate, and build rule instances."""
        try:
            rules_dir = self._resolve_rules_dir()
            if not rules_dir.is_dir():
                return r[
                    t.Infra.Pair[
                        Sequence[FlextInfraRefactorRule],
                        Sequence[FlextInfraClassNestingRefactorRule],
                    ]
                ].fail(f"Rules directory not found: {rules_dir}")
            loaded_rules: MutableSequence[FlextInfraRefactorRule] = []
            loaded_file_rules = build_file_rules()
            unknown_rules: MutableSequence[str] = []
            for rule_file in sorted(rules_dir.glob("*.yml")):
                if rule_file.name == self._ENGINE_REGISTRY_FILENAME:
                    continue
                try:
                    rule_config: Mapping[str, t.Infra.InfraValue] = (
                        t.Infra.INFRA_MAPPING_ADAPTER.validate_python(
                            dict(u.Cli.yaml_load_mapping(rule_file))
                        )
                    )
                except (OSError, TypeError):
                    continue
                typed_rules = self._coerce_rule_definitions(
                    rule_config.get(c.Infra.ReportKeys.RULES),
                )
                for typed_rule_def in typed_rules:
                    if c.Infra.ReportKeys.ID not in typed_rule_def:
                        continue
                    if not typed_rule_def.get(c.Infra.ReportKeys.ENABLED, True):
                        continue
                    rule_id = str(typed_rule_def[c.Infra.ReportKeys.ID]).strip()
                    rule_id_lower = rule_id.lower()
                    matches_active_filters = not rule_filters or any(
                        fnmatch.fnmatch(rule_id_lower, active_filter.lower())
                        or active_filter.lower() in rule_id_lower
                        for active_filter in rule_filters
                    )
                    if skip_rule_definition(typed_rule_def):
                        continue
                    if not matches_active_filters:
                        continue
                    rule_validation = validator.validate_rule_definition(typed_rule_def)
                    if rule_validation is not None:
                        unknown_rules.append(rule_validation)
                        continue
                    rule = build_rule(typed_rule_def)
                    if rule is None:
                        unknown_rules.append(
                            str(
                                typed_rule_def.get(
                                    c.Infra.ReportKeys.ID,
                                    c.Infra.Defaults.UNKNOWN,
                                ),
                            ),
                        )
                        continue
                    loaded_rules.append(rule)
            if unknown_rules:
                unknown = ", ".join(sorted(unknown_rules))
                return r[
                    t.Infra.Pair[
                        Sequence[FlextInfraRefactorRule],
                        Sequence[FlextInfraClassNestingRefactorRule],
                    ]
                ].fail(f"Unknown rule mapping for: {unknown}")
            return r[
                t.Infra.Pair[
                    Sequence[FlextInfraRefactorRule],
                    Sequence[FlextInfraClassNestingRefactorRule],
                ]
            ].ok((loaded_rules, loaded_file_rules))
        except Exception as exc:
            return r[
                t.Infra.Pair[
                    Sequence[FlextInfraRefactorRule],
                    Sequence[FlextInfraClassNestingRefactorRule],
                ]
            ].fail(f"Failed to load rules: {exc}")

    def _resolve_rules_dir(self) -> Path:
        local_rules_dir = self.config_path.parent / c.Infra.ReportKeys.RULES
        if local_rules_dir.is_dir():
            return local_rules_dir
        return self._package_rules_dir()

    @staticmethod
    def _package_rules_dir() -> Path:
        return Path(__file__).resolve().parent.parent / c.Infra.ReportKeys.RULES

    def _resolve_engine_config(
        self,
        config: t.Infra.InfraValue,
    ) -> m.Infra.EngineConfig:
        config_map = u.Infra.normalize_str_mapping(config)
        scope_raw = config_map.get("refactor_engine")
        scope_map = u.Infra.normalize_str_mapping(scope_raw)
        scope_map = {
            key: value
            for key, value in scope_map.items()
            if key in self._ENGINE_CONFIG_KEYS
        }
        return m.Infra.EngineConfig.model_validate(scope_map)

    @staticmethod
    def _coerce_rule_definitions(
        value: t.Infra.InfraValue | None,
    ) -> Sequence[Mapping[str, t.Infra.InfraValue]]:
        try:
            entries: Sequence[t.Infra.InfraValue] = (
                t.Infra.INFRA_SEQ_ADAPTER.validate_python(value)
            )
        except ValidationError:
            return []
        definitions: MutableSequence[Mapping[str, t.Infra.InfraValue]] = []
        for item in entries:
            normalized = u.Infra.normalize_str_mapping(item)
            if not normalized:
                continue
            definitions.append(normalized)
        return definitions


__all__ = ["FlextInfraUtilitiesRefactorRuleLoader"]
