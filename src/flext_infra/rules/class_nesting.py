"""Class nesting refactor rule: move loose classes under namespace classes."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

import libcst as cst
from pydantic import ValidationError

from flext_infra import (
    FlextInfraHelperConsolidationTransformer,
    FlextInfraPostCheckGate,
    FlextInfraPreCheckGate,
    FlextInfraRefactorClassNestingReconstructor,
    FlextInfraRefactorClassNestingTransformer,
    c,
    m,
    t,
    u,
)
from flext_infra.refactor._base_rule import INFRA_SEQ_ADAPTER


class FlextInfraClassNestingRefactorRule:
    """Apply class-nesting transforms driven by YAML mapping files."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize rule with an optional path to the YAML config."""
        self._config_path = config_path or Path(__file__).with_name(
            "class-nesting-mappings.yml",
        )
        self._policy_path = Path(__file__).with_name("class-policy-v2.yml")
        self._pre_check_gate = FlextInfraPreCheckGate()
        self._post_check_gate = FlextInfraPostCheckGate()
        self._cached_config: t.Infra.ContainerDict | None = None
        self._cached_policy_context: t.Infra.PolicyContext | None = None

    def apply(
        self,
        file_path: Path,
        *,
        dry_run: bool = False,
    ) -> m.Infra.Result:
        """Transform *file_path* according to loaded mappings and policy."""
        try:
            if file_path.suffix != c.Infra.Extensions.PYTHON:
                return m.Infra.Result(
                    file_path=file_path,
                    success=True,
                    modified=False,
                    changes=["Skipped non-Python file"],
                    refactored_code=None,
                )
            source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
            tree = u.Infra.parse_cst_from_source(source)
            if tree is None:
                return m.Infra.Result(
                    file_path=file_path,
                    success=True,
                    modified=False,
                    changes=[],
                    refactored_code=source,
                )
            mappings = self._load_config()
            confidence_threshold = self._confidence_threshold(mappings)
            class_mappings = self._class_nesting_mappings(
                mappings,
                file_path,
                confidence_threshold,
            )
            helper_mappings = self._helper_consolidation_mappings(
                mappings,
                file_path,
                confidence_threshold,
            )
            scope_entries = self._entries_for_scope(
                u.Infra.entry_list(
                    mappings.get(c.Infra.ReportKeys.CLASS_NESTING),
                ),
                file_path,
                confidence_threshold,
            )
            class_renames = (
                FlextInfraRefactorClassNestingReconstructor.class_rename_mappings(
                    scope_entries,
                )
            )
            policy_context = self._policy_context_from_document()
            class_families = self._families_for_scope(
                entries=self._entries_for_source_file(
                    u.Infra.entry_list(
                        mappings.get(c.Infra.ReportKeys.CLASS_NESTING),
                    ),
                    file_path,
                    confidence_threshold,
                ),
                symbol_key=c.Infra.ReportKeys.LOOSE_NAME,
            )
            helper_families = self._families_for_scope(
                entries=self._entries_for_source_file(
                    u.Infra.entry_list(
                        mappings.get(c.Infra.ReportKeys.HELPER_CONSOLIDATION),
                    ),
                    file_path,
                    confidence_threshold,
                ),
                symbol_key="helper_name",
            )
            precheck_violations = self._run_precheck(
                mappings,
                file_path,
                confidence_threshold,
            )
            if precheck_violations:
                return m.Infra.Result(
                    file_path=file_path,
                    success=False,
                    modified=False,
                    error="precheck_failed",
                    changes=precheck_violations,
                    refactored_code=None,
                )
            changes: MutableSequence[str] = []
            tree = self._apply_class_nesting(
                tree,
                class_mappings,
                changes,
                policy_context,
                class_families,
            )
            tree = self._apply_helper_consolidation(
                tree,
                helper_mappings,
                changes,
                policy_context,
                helper_families,
            )
            tree = FlextInfraRefactorClassNestingReconstructor.apply_nested_class_propagation(
                tree,
                class_renames,
                changes,
                policy_context,
                class_families,
            )
            result_code = tree.code
            modified = result_code != source
            if modified and (not dry_run):
                post_payload = self._build_postcheck_payload(
                    mappings,
                    file_path,
                    confidence_threshold,
                )
                post_ok, post_errors = self._post_check_gate.validate(
                    m.Infra.Result(
                        file_path=file_path,
                        success=True,
                        modified=True,
                        changes=changes,
                        refactored_code=result_code,
                    ),
                    post_payload,
                )
                if not post_ok:
                    return m.Infra.Result(
                        file_path=file_path,
                        success=False,
                        modified=False,
                        error="postcheck_failed",
                        changes=post_errors,
                        refactored_code=None,
                    )
            if modified and (not dry_run):
                u.write_file(file_path, result_code, encoding=c.Infra.Encoding.DEFAULT)
            return m.Infra.Result(
                file_path=file_path,
                success=True,
                modified=modified,
                changes=changes,
                refactored_code=result_code,
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

    def _load_config(self) -> t.Infra.ContainerDict:
        if self._cached_config is not None:
            return self._cached_config
        try:
            loaded = u.Infra.safe_load_yaml(self._config_path)
        except (OSError, TypeError) as exc:
            msg = "invalid class nesting mapping config"
            raise ValueError(msg) from exc
        config: MutableMapping[str, t.Infra.InfraValue] = {}
        confidence_threshold = loaded.get("confidence_threshold")
        if isinstance(confidence_threshold, str):
            config["confidence_threshold"] = confidence_threshold
        class_nesting_raw = loaded.get(c.Infra.ReportKeys.CLASS_NESTING)
        if isinstance(class_nesting_raw, list):
            try:
                typed_class_nesting: Sequence[t.Infra.InfraValue] = (
                    INFRA_SEQ_ADAPTER.validate_python(class_nesting_raw)
                )
                coerced_nesting: Sequence[t.Infra.InfraValue] = [
                    dict(e)
                    for e in self._coerce_entries(
                        u.Infra.mapping_list(typed_class_nesting),
                    )
                ]
                config[c.Infra.ReportKeys.CLASS_NESTING] = coerced_nesting
            except ValidationError:
                config[c.Infra.ReportKeys.CLASS_NESTING] = list[t.Infra.InfraValue]()
        helper_raw = loaded.get(c.Infra.ReportKeys.HELPER_CONSOLIDATION)
        if isinstance(helper_raw, list):
            try:
                typed_helper_entries: Sequence[t.Infra.InfraValue] = (
                    INFRA_SEQ_ADAPTER.validate_python(helper_raw)
                )
                coerced_helpers: Sequence[t.Infra.InfraValue] = [
                    dict(e)
                    for e in self._coerce_entries(
                        u.Infra.mapping_list(typed_helper_entries),
                    )
                ]
                config[c.Infra.ReportKeys.HELPER_CONSOLIDATION] = coerced_helpers
            except ValidationError:
                config[c.Infra.ReportKeys.HELPER_CONSOLIDATION] = list[
                    t.Infra.InfraValue
                ]()
        self._cached_config = config
        return config

    def _confidence_threshold(self, config: t.Infra.ContainerDict) -> str:
        raw = config.get("confidence_threshold", c.Infra.Severity.LOW)
        if not isinstance(raw, str):
            msg = "confidence_threshold must be a string"
            raise TypeError(msg)
        candidate = raw.strip().lower()
        if candidate in c.Infra.CONFIDENCE_RANKS:
            return candidate
        msg = f"unsupported confidence_threshold: {raw}"
        raise ValueError(msg)

    def _confidence_allowed(self, confidence: str, threshold: str) -> bool:
        confidence_rank = c.Infra.CONFIDENCE_RANKS.get(
            confidence.strip().lower(),
            0,
        )
        threshold_rank = c.Infra.CONFIDENCE_RANKS.get(threshold, 0)
        return confidence_rank >= threshold_rank

    def _class_nesting_mappings(
        self,
        config: t.Infra.ContainerDict,
        file_path: Path,
        confidence_threshold: str,
    ) -> MutableMapping[str, str]:
        mappings: MutableMapping[str, str] = {}
        for entry in self._entries_for_source_file(
            u.Infra.entry_list(config.get(c.Infra.ReportKeys.CLASS_NESTING)),
            file_path,
            confidence_threshold,
        ):
            loose_name = entry.get(c.Infra.ReportKeys.LOOSE_NAME)
            target_namespace = entry.get(c.Infra.ReportKeys.TARGET_NAMESPACE)
            if isinstance(loose_name, str) and isinstance(target_namespace, str):
                mappings[loose_name] = target_namespace
        return mappings

    def _run_precheck(
        self,
        config: t.Infra.ContainerDict,
        file_path: Path,
        confidence_threshold: str,
    ) -> MutableSequence[str]:
        violations: MutableSequence[str] = []
        entries: MutableSequence[Mapping[str, str]] = list(
            self._entries_for_source_file(
                u.Infra.entry_list(config.get(c.Infra.ReportKeys.CLASS_NESTING)),
                file_path,
                confidence_threshold,
            ),
        )
        helper_entries = self._entries_for_source_file(
            u.Infra.entry_list(
                config.get(c.Infra.ReportKeys.HELPER_CONSOLIDATION),
            ),
            file_path,
            confidence_threshold,
        )
        entries.extend(helper_entries)
        for entry in entries:
            ok, violation = self._pre_check_gate.validate_entry(entry)
            if not ok and violation is not None:
                violations.append(
                    "|".join([
                        violation[c.Infra.ReportKeys.RULE_ID],
                        violation[c.Infra.ReportKeys.SOURCE_SYMBOL],
                        violation[c.Infra.ReportKeys.VIOLATION_TYPE],
                        violation[c.Infra.ReportKeys.SUGGESTED_FIX],
                    ]),
                )
        return violations

    def _helper_consolidation_mappings(
        self,
        config: t.Infra.ContainerDict,
        file_path: Path,
        confidence_threshold: str,
    ) -> MutableMapping[str, str]:
        mappings: MutableMapping[str, str] = {}
        for entry in self._entries_for_source_file(
            u.Infra.entry_list(
                config.get(c.Infra.ReportKeys.HELPER_CONSOLIDATION),
            ),
            file_path,
            confidence_threshold,
        ):
            helper_name = entry.get("helper_name")
            target_namespace = entry.get(c.Infra.ReportKeys.TARGET_NAMESPACE)
            if isinstance(helper_name, str) and isinstance(target_namespace, str):
                mappings[helper_name] = target_namespace
        return mappings

    def _entries_for_source_file(
        self,
        raw_entries: Sequence[Mapping[str, str]],
        file_path: Path,
        confidence_threshold: str,
    ) -> Sequence[Mapping[str, str]]:
        entries = raw_entries
        if not entries:
            return []
        module_path = u.Infra.normalize_module_path(file_path)
        accepted: MutableSequence[Mapping[str, str]] = []
        for entry in entries:
            current_file = entry.get(c.Infra.ReportKeys.CURRENT_FILE)
            if current_file is None:
                continue
            current_module = u.Infra.normalize_module_path(Path(current_file))
            if current_module != module_path and (
                not module_path.endswith(f"/{current_module}")
            ):
                continue
            confidence = entry.get(c.Infra.ReportKeys.CONFIDENCE, c.Infra.Severity.LOW)
            if not self._confidence_allowed(confidence, confidence_threshold):
                continue
            accepted.append(entry)
        return accepted

    def _entries_for_scope(
        self,
        raw_entries: Sequence[Mapping[str, str]],
        file_path: Path,
        confidence_threshold: str,
    ) -> Sequence[Mapping[str, str]]:
        entries = raw_entries
        if not entries:
            return []
        accepted: MutableSequence[Mapping[str, str]] = []
        for entry in entries:
            confidence = entry.get(c.Infra.ReportKeys.CONFIDENCE, c.Infra.Severity.LOW)
            if not self._confidence_allowed(confidence, confidence_threshold):
                continue
            current_file = entry.get(c.Infra.ReportKeys.CURRENT_FILE, "")
            if not current_file:
                continue
            if not u.Infra.scope_applies_to_file(
                entry,
                Path(current_file),
                file_path,
            ):
                continue
            accepted.append(entry)
        return accepted

    def _coerce_entries(
        self,
        entries: Sequence[Mapping[str, t.Infra.InfraValue]],
    ) -> Sequence[Mapping[str, str]]:
        coerced: MutableSequence[Mapping[str, str]] = []
        for typed in entries:
            current_file = typed.get(c.Infra.ReportKeys.CURRENT_FILE)
            if not isinstance(current_file, str):
                continue
            entry: MutableMapping[str, str] = {
                c.Infra.ReportKeys.CURRENT_FILE: current_file,
            }
            loose_name = typed.get(c.Infra.ReportKeys.LOOSE_NAME)
            if isinstance(loose_name, str):
                entry[c.Infra.ReportKeys.LOOSE_NAME] = loose_name
            helper_name = typed.get("helper_name")
            if isinstance(helper_name, str):
                entry["helper_name"] = helper_name
            target_namespace = typed.get(c.Infra.ReportKeys.TARGET_NAMESPACE)
            if isinstance(target_namespace, str):
                entry[c.Infra.ReportKeys.TARGET_NAMESPACE] = target_namespace
            target_name = typed.get("target_name")
            if isinstance(target_name, str):
                entry["target_name"] = target_name
            rewrite_scope = typed.get(c.Infra.ReportKeys.REWRITE_SCOPE)
            if isinstance(rewrite_scope, str):
                entry[c.Infra.ReportKeys.REWRITE_SCOPE] = rewrite_scope
            confidence = typed.get(c.Infra.ReportKeys.CONFIDENCE)
            if isinstance(confidence, str):
                entry[c.Infra.ReportKeys.CONFIDENCE] = confidence
            coerced.append(entry)
        return coerced

    def _build_postcheck_payload(
        self,
        config: t.Infra.ContainerDict,
        file_path: Path,
        confidence_threshold: str,
    ) -> t.Infra.ContainerDict:
        payload: MutableMapping[str, t.Infra.InfraValue] = {
            c.Infra.ReportKeys.SOURCE_SYMBOL: "",
            "expected_base_chain": list[str](),
            c.Infra.ReportKeys.POST_CHECKS: ["imports_resolve", "mro_valid"],
            "quality_gates": ["lsp_diagnostics_clean"],
        }
        class_entries = self._entries_for_source_file(
            u.Infra.entry_list(config.get(c.Infra.ReportKeys.CLASS_NESTING)),
            file_path,
            confidence_threshold,
        )
        if not class_entries:
            return payload
        source_symbol = class_entries[0].get(c.Infra.ReportKeys.LOOSE_NAME, "")
        if not source_symbol:
            return payload
        payload[c.Infra.ReportKeys.SOURCE_SYMBOL] = source_symbol
        policy_doc = u.Infra.load_validated_policy_document(self._policy_path)
        rules = u.Infra.mapping_list(policy_doc.get(c.Infra.ReportKeys.RULES))
        for rule in rules:
            if rule.get(c.Infra.ReportKeys.SOURCE_SYMBOL, "") != source_symbol:
                continue
            base_chain: Sequence[t.Infra.InfraValue] = list(
                u.Infra.string_list(
                    rule.get("expected_base_chain"),
                ),
            )
            payload["expected_base_chain"] = base_chain
            post_checks_raw = rule.get(c.Infra.ReportKeys.POST_CHECKS, [])
            post_checks: MutableSequence[t.Infra.InfraValue] = []
            if not isinstance(post_checks_raw, list):
                continue
            typed_post_checks: Sequence[t.Infra.InfraValue] = (
                INFRA_SEQ_ADAPTER.validate_python(post_checks_raw)
            )
            checks = u.Infra.mapping_list(typed_post_checks)
            for check in checks:
                check_type = check.get("type")
                if isinstance(check_type, str):
                    post_checks.append(check_type)
            if post_checks:
                payload[c.Infra.ReportKeys.POST_CHECKS] = post_checks
            break
        return payload

    def _apply_class_nesting(
        self,
        tree: cst.Module,
        mappings: Mapping[str, str],
        changes: MutableSequence[str],
        policy_context: t.Infra.PolicyContext,
        class_families: Mapping[str, str],
    ) -> cst.Module:
        return self._apply_transformer(
            tree=tree,
            transformer=FlextInfraRefactorClassNestingTransformer(
                mappings=mappings,
                policy_context=policy_context,
                class_families=class_families,
            ),
            changes=changes,
            label="FlextInfraRefactorClassNestingTransformer",
            mapping_count=len(mappings),
        )

    def _apply_helper_consolidation(
        self,
        tree: cst.Module,
        mappings: Mapping[str, str],
        changes: MutableSequence[str],
        policy_context: t.Infra.PolicyContext,
        helper_families: Mapping[str, str],
    ) -> cst.Module:
        return self._apply_transformer(
            tree=tree,
            transformer=FlextInfraHelperConsolidationTransformer(
                helper_mappings=mappings,
                policy_context=policy_context,
                helper_families=helper_families,
            ),
            changes=changes,
            label="FlextInfraHelperConsolidationTransformer",
            mapping_count=len(mappings),
        )

    @staticmethod
    def _apply_transformer(
        *,
        tree: cst.Module,
        transformer: cst.CSTTransformer,
        changes: MutableSequence[str],
        label: str,
        mapping_count: int,
    ) -> cst.Module:
        updated_tree = tree.visit(transformer)
        if updated_tree.code != tree.code:
            changes.append(f"Applied {label} ({mapping_count} mappings)")
        return updated_tree

    def _policy_context_from_document(self) -> t.Infra.PolicyContext:
        """Load and cache per-family policy from YAML."""
        if self._cached_policy_context is not None:
            return self._cached_policy_context
        policy_doc = u.Infra.load_validated_policy_document(self._policy_path)
        policy_entries = u.Infra.mapping_list(policy_doc.get("policy_matrix"))
        policy_context: MutableMapping[str, t.Infra.ContainerDict] = {}
        for entry in policy_entries:
            family_name = entry.get("family_name")
            if not isinstance(family_name, str):
                continue
            policy_context[family_name] = entry
        self._cached_policy_context = policy_context
        return policy_context

    def _families_for_scope(
        self,
        *,
        entries: Sequence[Mapping[str, str]],
        symbol_key: str,
    ) -> MutableMapping[str, str]:
        families: MutableMapping[str, str] = {}
        for entry in entries:
            symbol = entry.get(symbol_key)
            current_file = entry.get(c.Infra.ReportKeys.CURRENT_FILE)
            if not isinstance(symbol, str) or not isinstance(current_file, str):
                continue
            families[symbol] = u.Infra.module_family_from_path(current_file)
        return families


__all__ = ["FlextInfraClassNestingRefactorRule"]
