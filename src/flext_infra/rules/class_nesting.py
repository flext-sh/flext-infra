"""Class nesting refactor rule: move loose classes under namespace classes."""

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

_COERCE_KEYS: tuple[str, ...] = (
    c.Infra.ReportKeys.LOOSE_NAME,
    "helper_name",
    c.Infra.ReportKeys.TARGET_NAMESPACE,
    "target_name",
    c.Infra.ReportKeys.REWRITE_SCOPE,
    c.Infra.ReportKeys.CONFIDENCE,
)
_SECTION_KEYS: tuple[str, ...] = (
    c.Infra.ReportKeys.CLASS_NESTING,
    c.Infra.ReportKeys.HELPER_CONSOLIDATION,
)


class _PostCheckGate:
    """Inline post-check gate for class nesting validation."""

    def validate(
        self,
        result: m.Infra.Result,
        expected: t.Infra.ContainerDict,
    ) -> t.Infra.Pair[bool, t.StrSequence]:
        errors: MutableSequence[str] = []
        if not result.success:
            if result.error:
                return (False, [result.error])
            return (False, ["transform_failed"])
        if not result.modified:
            return (True, [])
        file_path = result.file_path
        post_checks = u.Infra.string_list(
            expected.get(c.Infra.ReportKeys.POST_CHECKS),
        )
        quality_gates = u.Infra.string_list(expected.get("quality_gates"))
        if self._check_enabled("imports_resolve", post_checks):
            errors.extend(self._validate_imports(file_path))
        source_symbol_raw = expected.get(c.Infra.ReportKeys.SOURCE_SYMBOL, "")
        source_symbol = source_symbol_raw if isinstance(source_symbol_raw, str) else ""
        expected_chain = u.Infra.string_list(expected.get("expected_base_chain"))
        if (
            source_symbol
            and expected_chain
            and self._check_enabled("mro_valid", post_checks)
        ):
            errors.extend(self._validate_mro(file_path, source_symbol, expected_chain))
        if self._check_enabled("lsp_diagnostics_clean", quality_gates):
            errors.extend(self._validate_types(file_path))
        return (not errors, errors)

    def _check_enabled(self, check_name: str, checks: t.StrSequence) -> bool:
        return check_name in checks

    def _validate_imports(self, file_path: Path) -> t.StrSequence:
        try:
            source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        except (OSError, UnicodeDecodeError):
            return [f"parse_error:{file_path}:parse_failed"]
        unresolved: MutableSequence[str] = []
        for lineno, line in enumerate(source.splitlines(), start=1):
            if c.Infra.SourceCode.BARE_IMPORT_FROM_RE.match(line):
                unresolved.append(f"line_{lineno}:invalid_import_from")
        return unresolved

    def _validate_mro(
        self,
        file_path: Path,
        class_name: str,
        expected_bases: t.StrSequence,
    ) -> t.StrSequence:
        try:
            source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        except (OSError, UnicodeDecodeError):
            return [f"mro_parse_error:{file_path}:parse_failed"]
        for match in c.Infra.SourceCode.CLASS_WITH_BASES_RE.finditer(source):
            if match.group(1) != class_name:
                continue
            bases_str = match.group(2)
            actual = [
                b.strip().split("[")[0].rsplit(".", maxsplit=1)[-1]
                for b in bases_str.split(",")
                if b.strip()
            ]
            actual_clean = [name for name in actual if name]
            expected_prefix = list(expected_bases)[: len(actual_clean)]
            if actual_clean != expected_prefix:
                return [
                    f"mro_mismatch:{class_name}:expected={expected_prefix}:actual={actual_clean}",
                ]
            return []
        return [f"class_not_found:{class_name}"]

    def _validate_types(self, file_path: Path) -> t.StrSequence:
        cmd = [sys.executable, "-m", "py_compile", str(file_path)]
        result = u.Infra.capture(cmd)
        return result.fold(
            on_failure=lambda e: [f"lsp_diagnostics_clean_failed:{e or ''}"],
            on_success=lambda _: [],
        )


class FlextInfraClassNestingRefactorRule:
    """Apply class-nesting transforms driven by YAML mapping files."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize rule with an optional path to the YAML config."""
        self._config_path = config_path or Path(__file__).with_name(
            "class-nesting-mappings.yml",
        )
        self._policy_path = Path(__file__).with_name("class-policy-v2.yml")
        self._post_check_gate = _PostCheckGate()
        self._cached_config: t.Infra.ContainerDict | None = None
        self._cached_policy_by_family: (
            Mapping[str, m.Infra.ClassNestingPolicy] | None
        ) = None

    def apply(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        dry_run: bool = False,
    ) -> m.Infra.Result:
        """Transform resource according to loaded mappings and policy."""
        fp = Path(rope_project.root.real_path) / resource.path
        try:
            source = u.Infra.read_source(resource)
            cfg = self._load_config()
            thr = self._confidence_threshold(cfg)
            cm = self._symbol_mappings(
                cfg,
                fp,
                thr,
                c.Infra.ReportKeys.CLASS_NESTING,
                c.Infra.ReportKeys.LOOSE_NAME,
            )
            hm = self._symbol_mappings(
                cfg, fp, thr, c.Infra.ReportKeys.HELPER_CONSOLIDATION, "helper_name"
            )
            violations = self._run_precheck(cfg, fp, thr)
            if violations:
                return m.Infra.Result(
                    file_path=fp,
                    success=False,
                    modified=False,
                    error="precheck_failed",
                    changes=violations,
                    refactored_code=None,
                )
            changes: MutableSequence[str] = []
            ns = self._apply_rope_transforms(source, cm, hm, changes)
            modified = ns != source
            if modified and not dry_run:
                pp = self._build_postcheck_payload(cfg, fp, thr)
                ok, errs = self._post_check_gate.validate(
                    m.Infra.Result(
                        file_path=fp,
                        success=True,
                        modified=True,
                        changes=changes,
                        refactored_code=ns,
                    ),
                    pp,
                )
                if not ok:
                    return m.Infra.Result(
                        file_path=fp,
                        success=False,
                        modified=False,
                        error="postcheck_failed",
                        changes=errs,
                        refactored_code=None,
                    )
                u.Infra.write_source(
                    rope_project, resource, ns, description="class nesting refactor"
                )
            return m.Infra.Result(
                file_path=fp,
                success=True,
                modified=modified,
                changes=changes,
                refactored_code=ns,
            )
        except Exception as exc:
            return m.Infra.Result(
                file_path=fp,
                success=False,
                modified=False,
                error=str(exc),
                changes=[],
                refactored_code=None,
            )

    def _apply_rope_transforms(
        self,
        source: str,
        class_map: t.MutableStrMapping,
        helper_map: t.MutableStrMapping,
        changes: MutableSequence[str],
    ) -> str:
        ns = source
        if class_map:
            nesting = FlextInfraRefactorClassNestingTransformer(class_map, {}, {})
            ns, class_changes = nesting.apply_to_source(ns)
            changes.extend(class_changes)
            propagation = FlextInfraNestedClassPropagationTransformer({
                name: f"{target_ns}.{name}" for name, target_ns in class_map.items()
            })
            ns, propagation_changes = propagation.apply_to_source(ns)
            changes.extend(propagation_changes)
        if helper_map:
            consolidation = FlextInfraHelperConsolidationTransformer(helper_map)
            ns, helper_changes = consolidation.apply_to_source(ns)
            changes.extend(helper_changes)
        return ns

    def _symbol_mappings(
        self,
        cfg: t.Infra.ContainerDict,
        fp: Path,
        thr: str,
        section: str,
        name_key: str,
    ) -> t.MutableStrMapping:
        result: t.MutableStrMapping = {}
        for entry in self._filter_entries(
            u.Infra.entry_list(cfg.get(section)), fp, thr
        ):
            name = entry.get(name_key)
            target = entry.get(c.Infra.ReportKeys.TARGET_NAMESPACE)
            if isinstance(name, str) and isinstance(target, str):
                result[name] = target
        return result

    def _run_precheck(
        self, cfg: t.Infra.ContainerDict, fp: Path, thr: str
    ) -> MutableSequence[str]:
        violations: MutableSequence[str] = []
        policy_by_family = self._policy_by_family()
        entries: MutableSequence[t.StrMapping] = []
        for key in _SECTION_KEYS:
            entries.extend(
                self._filter_entries(u.Infra.entry_list(cfg.get(key)), fp, thr)
            )
        for entry in entries:
            ok, v = u.Infra.validate_class_nesting_entry(
                entry,
                policy_by_family=policy_by_family,
            )
            if not ok and v is not None:
                violations.append(
                    "|".join([
                        v[c.Infra.ReportKeys.RULE_ID],
                        v[c.Infra.ReportKeys.SOURCE_SYMBOL],
                        v[c.Infra.ReportKeys.VIOLATION_TYPE],
                        v[c.Infra.ReportKeys.SUGGESTED_FIX],
                    ])
                )
        return violations

    def _filter_entries(
        self,
        raw: Sequence[t.StrMapping],
        fp: Path,
        thr: str,
    ) -> Sequence[t.StrMapping]:
        if not raw:
            return []
        mod = u.Infra.normalize_module_path(fp)
        accepted: MutableSequence[t.StrMapping] = []
        for entry in raw:
            cf = entry.get(c.Infra.ReportKeys.CURRENT_FILE)
            if cf is None:
                continue
            cm = u.Infra.normalize_module_path(Path(cf))
            if cm != mod and not mod.endswith(f"/{cm}"):
                continue
            conf = entry.get(c.Infra.ReportKeys.CONFIDENCE, c.Infra.Severity.LOW)
            if not self._confidence_ok(conf, thr):
                continue
            accepted.append(entry)
        return accepted

    def _load_config(self) -> t.Infra.ContainerDict:
        if self._cached_config is not None:
            return self._cached_config
        try:
            loaded = u.Infra.yaml_load_infra_mapping(self._config_path)
        except (OSError, TypeError) as exc:
            msg = "invalid class nesting mapping config"
            raise ValueError(msg) from exc
        config: MutableMapping[str, t.Infra.InfraValue] = {}
        ct = loaded.get("confidence_threshold")
        if isinstance(ct, str):
            config["confidence_threshold"] = ct
        for key in _SECTION_KEYS:
            raw = loaded.get(key)
            if isinstance(raw, list):
                try:
                    mappings = u.Infra.mapping_list(raw)
                    config[key] = [dict(e) for e in self._coerce(mappings)]
                except ValueError:
                    config[key] = list[t.Infra.InfraValue]()
        self._cached_config = config
        return config

    def _policy_by_family(self) -> Mapping[str, m.Infra.ClassNestingPolicy]:
        """Load and cache the validated policy matrix once per rule instance."""
        if self._cached_policy_by_family is None:
            self._cached_policy_by_family = u.Infra.class_nesting_policy_by_family(
                self._policy_path
            )
        return self._cached_policy_by_family

    @staticmethod
    def _coerce(
        entries: Sequence[Mapping[str, t.Infra.InfraValue]],
    ) -> Sequence[t.StrMapping]:
        result: MutableSequence[t.StrMapping] = []
        for typed in entries:
            cf = typed.get(c.Infra.ReportKeys.CURRENT_FILE)
            if not isinstance(cf, str):
                continue
            entry: t.MutableStrMapping = {c.Infra.ReportKeys.CURRENT_FILE: cf}
            for k in _COERCE_KEYS:
                v = typed.get(k)
                if isinstance(v, str):
                    entry[k] = v
            result.append(entry)
        return result

    def _confidence_threshold(self, config: t.Infra.ContainerDict) -> str:
        raw = config.get("confidence_threshold", c.Infra.Severity.LOW)
        if not isinstance(raw, str):
            msg = "confidence_threshold must be a string"
            raise TypeError(msg)
        candidate = u.norm_str(raw, case="lower")
        if candidate in c.Infra.CONFIDENCE_RANKS:
            return candidate
        msg = f"unsupported confidence_threshold: {raw}"
        raise ValueError(msg)

    @staticmethod
    def _confidence_ok(confidence: str, threshold: str) -> bool:
        return c.Infra.CONFIDENCE_RANKS.get(
            u.norm_str(confidence, case="lower"), 0
        ) >= c.Infra.CONFIDENCE_RANKS.get(threshold, 0)

    def _build_postcheck_payload(
        self, cfg: t.Infra.ContainerDict, fp: Path, thr: str
    ) -> t.Infra.ContainerDict:
        _ = (cfg, fp, thr)
        return {
            c.Infra.ReportKeys.SOURCE_SYMBOL: "",
            "expected_base_chain": list[str](),
            c.Infra.ReportKeys.POST_CHECKS: ["imports_resolve"],
            "quality_gates": ["lsp_diagnostics_clean"],
        }


__all__ = ["FlextInfraClassNestingRefactorRule"]
