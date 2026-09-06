"""Direct file-rule execution for the refactor service."""

from __future__ import annotations

import sys
from pathlib import Path

from flext_infra import c, m, t, u
from flext_infra.refactor.class_nesting_analyzer import (
    FlextInfraRefactorClassNestingAnalyzer,
)
from flext_infra.transformers.class_nesting import (
    FlextInfraRefactorClassNestingTransformer,
)
from flext_infra.transformers.nested_class_propagation import (
    FlextInfraNestedClassPropagationTransformer,
)


class FlextInfraClassNestingPostCheckGate:
    """Run post-transform validation gates for direct class-nesting execution."""

    def validate(
        self, result: m.Infra.Result, expected: t.JsonMapping
    ) -> t.Pair[bool, t.StrSequence]:
        """Validate post-check expectations against one transformed file result."""
        if not result.success:
            return (False, [result.error] if result.error else ["transform_failed"])
        if not result.modified:
            return (True, list[str]())
        file_path = result.file_path
        errors: t.MutableSequenceOf[str] = []
        post_checks = u.Infra.string_list(expected.get(c.Infra.RK_POST_CHECKS))
        quality_gates = u.Infra.string_list(expected.get(c.Infra.RK_QUALITY_GATES))
        source_symbol = str(expected.get(c.Infra.RK_SOURCE_SYMBOL, ""))
        expected_chain = u.Infra.string_list(
            expected.get(c.Infra.RK_EXPECTED_BASE_CHAIN)
        )
        if c.Infra.RK_IMPORTS_RESOLVE in post_checks:
            errors.extend(self._validate_imports(file_path))
        if source_symbol and expected_chain and c.Infra.RK_FLEXT_VALID in post_checks:
            errors.extend(
                self._validate_flext(file_path, source_symbol, expected_chain)
            )
        if c.Infra.RK_LSP_DIAGNOSTICS_CLEAN in quality_gates:
            errors.extend(self._validate_types(file_path))
        return (not errors, errors)

    def _validate_imports(self, file_path: Path) -> t.StrSequence:
        """Validate imports."""
        read = u.Cli.files_read_text(file_path)
        if read.failure:
            return [f"parse_error:{file_path}:parse_failed"]
        source = read.value
        return [
            f"line_{lineno}:invalid_import_from"
            for lineno, line in enumerate(source.splitlines(), start=1)
            if c.Infra.BARE_IMPORT_FROM_RE.match(line)
        ]

    def _validate_flext(
        self, file_path: Path, class_name: str, expected_bases: t.StrSequence
    ) -> t.StrSequence:
        """Validate flext."""
        read = u.Cli.files_read_text(file_path)
        if read.failure:
            return [f"flext_parse_error:{file_path}:parse_failed"]
        actual_clean = list(u.Infra.parse_class_bases(read.value, class_name))
        if not actual_clean:
            return [f"class_not_found:{class_name}"]
        expected_prefix = list(expected_bases)[: len(actual_clean)]
        if actual_clean != expected_prefix:
            return [
                f"flext_mismatch:{class_name}:expected={expected_prefix}:actual={actual_clean}"
            ]
        return list[str]()

    @staticmethod
    def _validate_types(file_path: Path) -> t.StrSequence:
        """Validate types."""
        result = u.Cli.capture([sys.executable, "-m", "py_compile", str(file_path)])
        return (
            [f"lsp_diagnostics_clean_failed:{result.error or ''}"]
            if result.failure
            else list[str]()
        )


class FlextInfraRefactorFileExecutor:
    """Execute declarative Rope-backed file rules directly from kind + settings."""

    _class_nesting_policy_by_family: t.MappingKV[str, m.Infra.ClassNestingPolicy] | None
    _class_nesting_gate: FlextInfraClassNestingPostCheckGate | None

    def _apply_file_rule_selection(
        self,
        kind: c.Infra.RefactorFileRuleKind,
        settings: t.MappingKV[str, t.Infra.InfraValue],
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        dry_run: bool = False,
    ) -> m.Infra.Result:
        """Apply file rule selection."""
        _ = (kind, settings)
        return self._apply_class_nesting(rope_project, resource, dry_run=dry_run)

    def _apply_class_nesting(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        dry_run: bool = False,
    ) -> m.Infra.Result:
        """Apply class nesting."""
        root_real_path = getattr(getattr(rope_project, "root", None), "real_path", None)
        project_root = Path(root_real_path) if isinstance(root_real_path, str) else None
        file_path = (
            project_root / resource.path
            if project_root is not None
            else Path(resource.real_path)
        )
        try:
            return self._apply_class_nesting_checked(
                resource, file_path, dry_run=dry_run
            )
        except c.EXC_BROAD_IO_TYPE as exc:
            return m.Infra.Result(
                file_path=file_path,
                success=False,
                modified=False,
                error=str(exc),
                changes=[],
                refactored_code=None,
            )

    def _apply_class_nesting_checked(
        self, resource: t.Infra.RopeResource, file_path: Path, *, dry_run: bool
    ) -> m.Infra.Result:
        """Apply class nesting after the public error boundary."""
        source = resource.read()
        nesting = FlextInfraRefactorClassNestingAnalyzer.analyze_files([file_path])
        violations = self._class_nesting_precheck(nesting.violations)
        if violations:
            return m.Infra.Result(
                file_path=file_path,
                success=False,
                modified=False,
                error="precheck_failed",
                changes=violations,
                refactored_code=None,
            )
        changes: t.MutableSequenceOf[str] = []
        class_map: t.MutableStrMapping = {
            violation.class_name: violation.target_namespace
            for violation in nesting.violations
        }
        updated = self._apply_class_nesting_transforms(source, class_map, changes)
        modified = updated != source
        if modified and not dry_run:
            postcheck_result = self._run_class_nesting_postcheck(
                file_path=file_path, updated=updated, changes=changes
            )
            if postcheck_result is not None:
                return postcheck_result
            resource.write(updated)
        return m.Infra.Result(
            file_path=file_path,
            success=True,
            modified=modified,
            changes=changes,
            refactored_code=updated,
        )

    def _run_class_nesting_postcheck(
        self, *, file_path: Path, updated: str, changes: t.StrSequence
    ) -> m.Infra.Result | None:
        """Run postchecks for a modified class-nesting result."""
        expected_base_chain: t.JsonValueList = []
        post_checks: t.JsonValueList = [c.Infra.RK_IMPORTS_RESOLVE]
        quality_gates: t.JsonValueList = [c.Infra.RK_LSP_DIAGNOSTICS_CLEAN]
        payload_values: t.JsonMapping = {
            c.Infra.RK_SOURCE_SYMBOL: "",
            c.Infra.RK_EXPECTED_BASE_CHAIN: expected_base_chain,
            c.Infra.RK_POST_CHECKS: post_checks,
            c.Infra.RK_QUALITY_GATES: quality_gates,
        }
        payload = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(payload_values)
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
        if ok:
            return None
        return m.Infra.Result(
            file_path=file_path,
            success=False,
            modified=False,
            error="postcheck_failed",
            changes=errs,
            refactored_code=None,
        )

    def _class_nesting_policy(self) -> t.MappingKV[str, m.Infra.ClassNestingPolicy]:
        """Class nesting policy."""
        if self._class_nesting_policy_by_family is None:
            rules_dir = Path(__file__).resolve().parent.parent / c.Infra.RK_RULES
            self._class_nesting_policy_by_family = (
                u.Infra.class_nesting_policy_by_family(
                    rules_dir / c.Infra.CLASS_NESTING_POLICY_FILENAME
                )
            )
        return self._class_nesting_policy_by_family

    def _class_nesting_precheck(
        self, nesting: t.SequenceOf[m.Infra.ClassNestingViolation]
    ) -> t.MutableSequenceOf[str]:
        """Reject a plan whose derived targets the family policy forbids.

        A loose class whose module declares no family has nowhere to nest, so
        it is reported as a violation of its own instead of being silently
        skipped or aimed at a guessed namespace.
        """
        violations: t.MutableSequenceOf[str] = []
        for item in nesting:
            if not item.target_namespace:
                violations.append(
                    "|".join((
                        f"precheck:{item.class_name}",
                        item.class_name,
                        "no_target_namespace",
                        f"declare the facade family in __all__ of {item.file}",
                    ))
                )
                continue
            ok, violation = u.Infra.validate_class_nesting_entry(
                {
                    c.Infra.RK_CURRENT_FILE: item.file,
                    c.Infra.RK_LOOSE_NAME: item.class_name,
                    c.Infra.RK_TARGET_NAMESPACE: item.target_namespace,
                    c.Infra.RK_CONFIDENCE: item.confidence,
                },
                policy_by_family=self._class_nesting_policy(),
            )
            if not ok and violation is not None:
                violation_parts: list[str] = [
                    violation[c.Infra.RK_RULE_ID],
                    violation[c.Infra.RK_SOURCE_SYMBOL],
                    violation[c.Infra.RK_VIOLATION_TYPE],
                    violation[c.Infra.RK_SUGGESTED_FIX],
                ]
                violations.append("|".join(violation_parts))
        return violations

    def _apply_class_nesting_transforms(
        self,
        source: str,
        class_map: t.MutableStrMapping,
        changes: t.MutableSequenceOf[str],
    ) -> str:
        """Nest every loose class under its derived facade and repoint references."""
        if not class_map:
            return source
        nesting = FlextInfraRefactorClassNestingTransformer(class_map, {}, {})
        updated, class_changes = nesting.apply_to_source(source)
        changes.extend(class_changes)
        propagation_map: t.MutableStrMapping = {
            name: f"{target}.{name}" for name, target in class_map.items()
        }
        propagation = FlextInfraNestedClassPropagationTransformer(propagation_map)
        updated, propagation_changes = propagation.apply_to_source(updated)
        changes.extend(propagation_changes)
        return updated


__all__: list[str] = [
    "FlextInfraClassNestingPostCheckGate",
    "FlextInfraRefactorFileExecutor",
]
