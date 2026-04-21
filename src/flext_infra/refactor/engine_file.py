"""Direct file-rule execution for the refactor engine."""

from __future__ import annotations

import sys
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

from flext_infra import (
    FlextInfraHelperConsolidationTransformer,
    FlextInfraNestedClassPropagationTransformer,
    FlextInfraRefactorClassNestingTransformer,
    c,
    m,
    t,
    u,
)


class FlextInfraClassNestingPostCheckGate:
    """Run post-transform validation gates for direct class-nesting execution."""

    @staticmethod
    def _read_source_safe(file_path: Path) -> str | None:
        try:
            return file_path.read_text(encoding=c.Infra.ENCODING_DEFAULT)
        except (OSError, UnicodeDecodeError):
            return None

    def validate(
        self,
        result: m.Infra.Result,
        expected: t.Infra.ContainerDict,
    ) -> t.Infra.Pair[bool, t.StrSequence]:
        """Validate post-check expectations against one transformed file result."""
        if not result.success:
            return (False, [result.error] if result.error else ["transform_failed"])
        if not result.modified:
            return (True, list[str]())
        file_path = result.file_path
        errors: MutableSequence[str] = []
        post_checks = u.Infra.string_list(expected.get(c.Infra.RK_POST_CHECKS))
        quality_gates = u.Infra.string_list(expected.get(c.Infra.RK_QUALITY_GATES))
        source_symbol = str(expected.get(c.Infra.RK_SOURCE_SYMBOL, ""))
        expected_chain = u.Infra.string_list(
            expected.get(c.Infra.RK_EXPECTED_BASE_CHAIN)
        )
        if c.Infra.RK_IMPORTS_RESOLVE in post_checks:
            errors.extend(self._validate_imports(file_path))
        if source_symbol and expected_chain and c.Infra.RK_MRO_VALID in post_checks:
            errors.extend(self._validate_mro(file_path, source_symbol, expected_chain))
        if c.Infra.RK_LSP_DIAGNOSTICS_CLEAN in quality_gates:
            errors.extend(self._validate_types(file_path))
        return (not errors, errors)

    def _validate_imports(self, file_path: Path) -> t.StrSequence:
        source = self._read_source_safe(file_path)
        if source is None:
            return [f"parse_error:{file_path}:parse_failed"]
        return [
            f"line_{lineno}:invalid_import_from"
            for lineno, line in enumerate(source.splitlines(), start=1)
            if c.Infra.BARE_IMPORT_FROM_RE.match(line)
        ]

    def _validate_mro(
        self,
        file_path: Path,
        class_name: str,
        expected_bases: t.StrSequence,
    ) -> t.StrSequence:
        source = self._read_source_safe(file_path)
        if source is None:
            return [f"mro_parse_error:{file_path}:parse_failed"]
        actual_clean = list(u.Infra.parse_class_bases(source, class_name))
        if not actual_clean:
            return [f"class_not_found:{class_name}"]
        expected_prefix = list(expected_bases)[: len(actual_clean)]
        if actual_clean != expected_prefix:
            return [
                f"mro_mismatch:{class_name}:expected={expected_prefix}:actual={actual_clean}",
            ]
        return list[str]()

    @staticmethod
    def _validate_types(file_path: Path) -> t.StrSequence:
        result = u.Cli.capture([sys.executable, "-m", "py_compile", str(file_path)])
        return (
            [f"lsp_diagnostics_clean_failed:{result.error or ''}"]
            if result.failure
            else list[str]()
        )


class FlextInfraRefactorFileExecutor:
    """Execute declarative Rope-backed file rules directly from kind + settings."""

    _class_nesting_config: t.Infra.ContainerDict | None
    _class_nesting_policy_by_family: Mapping[str, m.Infra.ClassNestingPolicy] | None
    _class_nesting_gate: FlextInfraClassNestingPostCheckGate | None

    def _apply_file_rule_selection(
        self,
        kind: c.Infra.RefactorFileRuleKind,
        settings: Mapping[str, t.Infra.InfraValue],
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        dry_run: bool = False,
    ) -> m.Infra.Result:
        _ = settings
        if kind == c.Infra.RefactorFileRuleKind.CLASS_NESTING:
            return self._apply_class_nesting(rope_project, resource, dry_run=dry_run)
        return m.Infra.Result(
            file_path=Path(resource.real_path),
            success=True,
            modified=False,
            changes=[],
            refactored_code=resource.read(),
        )

    def _apply_class_nesting(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        dry_run: bool = False,
    ) -> m.Infra.Result:
        root_real_path = getattr(getattr(rope_project, "root", None), "real_path", None)
        project_root = Path(root_real_path) if isinstance(root_real_path, str) else None
        file_path = (
            project_root / resource.path
            if project_root is not None
            else Path(resource.real_path)
        )
        try:
            source = resource.read()
            config = self._load_class_nesting_config()
            threshold = self._class_nesting_threshold(config)
            class_map = self._class_nesting_symbol_map(
                config,
                file_path,
                threshold,
                c.Infra.RK_CLASS_NESTING,
                c.Infra.RK_LOOSE_NAME,
            )
            helper_map = self._class_nesting_symbol_map(
                config,
                file_path,
                threshold,
                c.Infra.RK_HELPER_CONSOLIDATION,
                c.Infra.RK_HELPER_NAME,
            )
            violations = self._class_nesting_precheck(config, file_path, threshold)
            if violations:
                return m.Infra.Result(
                    file_path=file_path,
                    success=False,
                    modified=False,
                    error="precheck_failed",
                    changes=violations,
                    refactored_code=None,
                )
            changes: MutableSequence[str] = []
            updated = self._apply_class_nesting_transforms(
                source, class_map, helper_map, changes
            )
            modified = updated != source
            if modified and not dry_run:
                payload = t.Infra.INFRA_MAPPING_ADAPTER.validate_python({
                    c.Infra.RK_SOURCE_SYMBOL: "",
                    c.Infra.RK_EXPECTED_BASE_CHAIN: list[str](),
                    c.Infra.RK_POST_CHECKS: [c.Infra.RK_IMPORTS_RESOLVE],
                    c.Infra.RK_QUALITY_GATES: [c.Infra.RK_LSP_DIAGNOSTICS_CLEAN],
                })
                gate = self._class_nesting_gate or FlextInfraClassNestingPostCheckGate()
                self._class_nesting_gate = gate
                ok, errs = gate.validate(
                    m.Infra.Result(
                        file_path=file_path,
                        success=True,
                        modified=True,
                        changes=changes,
                        refactored_code=updated,
                    ),
                    payload,
                )
                if not ok:
                    return m.Infra.Result(
                        file_path=file_path,
                        success=False,
                        modified=False,
                        error="postcheck_failed",
                        changes=errs,
                        refactored_code=None,
                    )
                resource.write(updated)
            return m.Infra.Result(
                file_path=file_path,
                success=True,
                modified=modified,
                changes=changes,
                refactored_code=updated,
            )
        except Exception as exc:
            return m.Infra.Result(
                file_path=file_path,
                success=False,
                modified=False,
                error=str(exc),
                changes=[],
                refactored_code=None,
            )

    def _load_class_nesting_config(self) -> t.Infra.ContainerDict:
        if self._class_nesting_config is not None:
            return self._class_nesting_config
        rules_dir = Path(__file__).resolve().parent.parent / c.Infra.RK_RULES
        loaded = u.Cli.yaml_load_mapping(
            rules_dir / c.Infra.CLASS_NESTING_MAPPINGS_FILENAME
        )
        settings: MutableMapping[str, t.Infra.InfraValue] = {}
        threshold = loaded.get(c.Infra.RK_CONFIDENCE_THRESHOLD)
        if isinstance(threshold, str):
            settings[c.Infra.RK_CONFIDENCE_THRESHOLD] = threshold
        for key in c.Infra.NESTING_SECTION_KEYS:
            raw = loaded.get(key)
            if isinstance(raw, list):
                settings[key] = [
                    dict(entry)
                    for entry in self._coerce_class_nesting_entries(
                        u.Cli.json_as_mapping_list(raw)
                    )
                ]
        self._class_nesting_config = settings
        return settings

    def _class_nesting_policy(self) -> Mapping[str, m.Infra.ClassNestingPolicy]:
        if self._class_nesting_policy_by_family is None:
            rules_dir = Path(__file__).resolve().parent.parent / c.Infra.RK_RULES
            self._class_nesting_policy_by_family = (
                u.Infra.class_nesting_policy_by_family(
                    rules_dir / c.Infra.CLASS_NESTING_POLICY_FILENAME
                )
            )
        return self._class_nesting_policy_by_family

    def _class_nesting_precheck(
        self,
        config: t.Infra.ContainerDict,
        file_path: Path,
        threshold: str,
    ) -> MutableSequence[str]:
        entries: MutableSequence[t.StrMapping] = []
        for key in c.Infra.NESTING_SECTION_KEYS:
            entries.extend(
                self._filter_class_nesting_entries(
                    u.Infra.entry_list(config.get(key)), file_path, threshold
                )
            )
        violations: MutableSequence[str] = []
        for entry in entries:
            ok, violation = u.Infra.validate_class_nesting_entry(
                entry, policy_by_family=self._class_nesting_policy()
            )
            if not ok and violation is not None:
                violations.append(
                    "|".join([
                        violation[c.Infra.RK_RULE_ID],
                        violation[c.Infra.RK_SOURCE_SYMBOL],
                        violation[c.Infra.RK_VIOLATION_TYPE],
                        violation[c.Infra.RK_SUGGESTED_FIX],
                    ])
                )
        return violations

    def _class_nesting_symbol_map(
        self,
        config: t.Infra.ContainerDict,
        file_path: Path,
        threshold: str,
        section: str,
        name_key: str,
    ) -> t.MutableStrMapping:
        result: t.MutableStrMapping = {}
        for entry in self._filter_class_nesting_entries(
            u.Infra.entry_list(config.get(section)), file_path, threshold
        ):
            name = entry.get(name_key)
            target = entry.get(c.Infra.RK_TARGET_NAMESPACE)
            if isinstance(name, str) and isinstance(target, str):
                result[name] = target
        return result

    def _filter_class_nesting_entries(
        self,
        raw: Sequence[t.StrMapping],
        file_path: Path,
        threshold: str,
    ) -> Sequence[t.StrMapping]:
        module_path = u.Infra.normalize_module_path(file_path)
        result: MutableSequence[t.StrMapping] = []
        for entry in raw:
            current_file = entry.get(c.Infra.RK_CURRENT_FILE)
            if not isinstance(current_file, str):
                continue
            current_module = u.Infra.normalize_module_path(Path(current_file))
            if current_module != module_path and not module_path.endswith(
                f"/{current_module}"
            ):
                continue
            confidence = entry.get(c.Infra.RK_CONFIDENCE, c.Infra.SeverityLevel.LOW)
            if c.Infra.CONFIDENCE_RANKS.get(
                u.norm_str(confidence, case="lower"), 0
            ) < c.Infra.CONFIDENCE_RANKS.get(threshold, 0):
                continue
            result.append(entry)
        return result

    def _apply_class_nesting_transforms(
        self,
        source: str,
        class_map: t.MutableStrMapping,
        helper_map: t.MutableStrMapping,
        changes: MutableSequence[str],
    ) -> str:
        updated = source
        if class_map:
            nesting = FlextInfraRefactorClassNestingTransformer(class_map, {}, {})
            updated, class_changes = nesting.apply_to_source(updated)
            changes.extend(class_changes)
            propagation = FlextInfraNestedClassPropagationTransformer({
                name: f"{target}.{name}" for name, target in class_map.items()
            })
            updated, propagation_changes = propagation.apply_to_source(updated)
            changes.extend(propagation_changes)
        if helper_map:
            consolidation = FlextInfraHelperConsolidationTransformer(helper_map)
            updated, helper_changes = consolidation.apply_to_source(updated)
            changes.extend(helper_changes)
        return updated

    @staticmethod
    def _coerce_class_nesting_entries(
        entries: Sequence[Mapping[str, t.Infra.InfraValue]],
    ) -> Sequence[t.StrMapping]:
        result: MutableSequence[t.StrMapping] = []
        for typed in entries:
            current_file = typed.get(c.Infra.RK_CURRENT_FILE)
            if not isinstance(current_file, str):
                continue
            entry: t.MutableStrMapping = {c.Infra.RK_CURRENT_FILE: current_file}
            for key in c.Infra.NESTING_COERCE_KEYS:
                value = typed.get(key)
                if isinstance(value, str):
                    entry[key] = value
            result.append(entry)
        return result

    @staticmethod
    def _class_nesting_threshold(settings: t.Infra.ContainerDict) -> str:
        raw = settings.get(c.Infra.RK_CONFIDENCE_THRESHOLD, c.Infra.SeverityLevel.LOW)
        if not isinstance(raw, str):
            msg = "confidence_threshold must be a string"
            raise TypeError(msg)
        candidate = u.norm_str(raw, case="lower")
        if candidate not in c.Infra.CONFIDENCE_RANKS:
            msg = f"unsupported confidence_threshold: {raw}"
            raise ValueError(msg)
        return candidate


__all__: list[str] = [
    "FlextInfraClassNestingPostCheckGate",
    "FlextInfraRefactorFileExecutor",
]
