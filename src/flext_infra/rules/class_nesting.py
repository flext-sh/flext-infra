"""Class nesting refactor rule: move loose classes under namespace classes."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

from flext_infra import (
    FlextInfraPostCheckGate,
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


class FlextInfraClassNestingRefactorRule:
    """Apply class-nesting transforms driven by YAML mapping files."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize rule with an optional path to the YAML config."""
        self._config_path = config_path or Path(__file__).with_name(
            "class-nesting-mappings.yml",
        )
        self._policy_path = Path(__file__).with_name("class-policy-v2.yml")
        self._post_check_gate = FlextInfraPostCheckGate()
        self._cached_config: t.Infra.ContainerDict | None = None

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
            source = u.read_source(resource)
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
            ns = self._apply_rope_transforms(
                rope_project, resource, source, cm, hm, changes
            )
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
                u.write_source(
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
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        source: str,
        class_map: t.MutableStrMapping,
        helper_map: t.MutableStrMapping,
        changes: MutableSequence[str],
    ) -> str:
        ns = source
        for label, mapping in (
            ("class nesting", class_map),
            ("helper consolidation", helper_map),
        ):
            if not mapping:
                continue
            for name, target_ns in mapping.items():
                ns, _ = u.replace_in_source(
                    rope_project,
                    resource,
                    rf"\b{name}\b",
                    f"{target_ns}.{name}",
                    apply=False,
                )
            if ns != source:
                changes.append(f"Applied {label} ({len(mapping)} mappings)")
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
        for entry in self._filter_entries(u.entry_list(cfg.get(section)), fp, thr):
            name = entry.get(name_key)
            target = entry.get(c.Infra.ReportKeys.TARGET_NAMESPACE)
            if isinstance(name, str) and isinstance(target, str):
                result[name] = target
        return result

    def _run_precheck(
        self, cfg: t.Infra.ContainerDict, fp: Path, thr: str
    ) -> MutableSequence[str]:
        violations: MutableSequence[str] = []
        policy_by_family = u.class_nesting_policy_by_family(self._policy_path)
        entries: MutableSequence[t.StrMapping] = []
        for key in _SECTION_KEYS:
            entries.extend(self._filter_entries(u.entry_list(cfg.get(key)), fp, thr))
        for entry in entries:
            ok, v = u.validate_class_nesting_entry(
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
        mod = u.normalize_module_path(fp)
        accepted: MutableSequence[t.StrMapping] = []
        for entry in raw:
            cf = entry.get(c.Infra.ReportKeys.CURRENT_FILE)
            if cf is None:
                continue
            cm = u.normalize_module_path(Path(cf))
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
            loaded = u.safe_load_yaml(self._config_path)
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
                    mappings = u.mapping_list(raw)
                    config[key] = [dict(e) for e in self._coerce(mappings)]
                except ValueError:
                    config[key] = list[t.Infra.InfraValue]()
        self._cached_config = config
        return config

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
        payload: MutableMapping[str, t.Infra.InfraValue] = {
            c.Infra.ReportKeys.SOURCE_SYMBOL: "",
            "expected_base_chain": list[str](),
            c.Infra.ReportKeys.POST_CHECKS: ["imports_resolve", "mro_valid"],
            "quality_gates": ["lsp_diagnostics_clean"],
        }
        entries = self._filter_entries(
            u.entry_list(cfg.get(c.Infra.ReportKeys.CLASS_NESTING)), fp, thr
        )
        if not entries:
            return payload
        sym = entries[0].get(c.Infra.ReportKeys.LOOSE_NAME, "")
        if not sym:
            return payload
        payload[c.Infra.ReportKeys.SOURCE_SYMBOL] = sym
        doc = u.load_validated_policy_document(self._policy_path)
        for rule in u.mapping_list(doc.get(c.Infra.ReportKeys.RULES)):
            if rule.get(c.Infra.ReportKeys.SOURCE_SYMBOL, "") == sym:
                payload["expected_base_chain"] = list(
                    u.string_list(rule.get("expected_base_chain"))
                )
                break
        return payload


__all__ = ["FlextInfraClassNestingRefactorRule"]
