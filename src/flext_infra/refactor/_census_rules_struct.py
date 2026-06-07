"""Census structural rule scanners (compatibility + MRO) — extracted concern."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import (
    FlextInfraCompatibilityAliasDetector,
    FlextInfraMROCompletenessDetector,
    m,
    p,
    t,
)


class FlextInfraRefactorCensusRulesStructMixin:
    """Compatibility-alias + MRO-completeness rule scanners for one module.

    Composed into FlextInfraRefactorCensus via inheritance; borrows the
    detector-context + violation/fix builders from sibling mixins via MRO.
    """

    if TYPE_CHECKING:
        @staticmethod
        def _detector_context(
            rope: p.Infra.RopeWorkspaceDsl,
            file_path: Path,
            *,
            convention: m.Infra.RopeModuleConvention | None = None,
            parse_failures: t.MutableSequenceOf[m.Infra.ParseFailureViolation]
            | None = None,
        ) -> m.Infra.DetectorContext: ...
        @staticmethod
        def _raw_violation(
            *,
            project: str,
            object_name: str,
            object_kind: str,
            kind: str,
            file_path: Path,
            line: int,
            description: str,
            fixable: bool = False,
            fix_action: str = "",
        ) -> m.Infra.Census.Violation: ...
        @staticmethod
        def _fix_key(
            file_path: Path, object_name: str, action: str = ""
        ) -> str: ...
        @staticmethod
        def _named_object(
            objects: tuple[m.Infra.Census.Object, ...], name: str
        ) -> m.Infra.Census.Object | None: ...

    def _rule_compatibility_alias(
        self,
        rope: p.Infra.RopeWorkspaceDsl,
        file_path: Path,
        *,
        project_name: str,
        objects: tuple[m.Infra.Census.Object, ...] | None,
        applied: frozenset[str],
        selected_kinds: frozenset[str],
        symbol_index: dict[str, tuple[str, int]],
        convention: m.Infra.RopeModuleConvention,
    ) -> tuple[list[m.Infra.Census.Violation], list[m.Infra.Census.Fix]]:
        """Detect + plan fixes for compatibility-alias violations."""
        ctx = self._detector_context(rope, file_path, convention=convention)
        violations: list[m.Infra.Census.Violation] = []
        fixes: list[m.Infra.Census.Fix] = []
        for detector_violation in FlextInfraCompatibilityAliasDetector.detect_file(ctx):
            matched = (
                self._named_object(objects, detector_violation.alias_name)
                if objects is not None
                else None
            )
            object_kind = matched.kind if matched is not None else "assignment"
            if matched is None:
                target_symbol = symbol_index.get(detector_violation.target_name)
                if target_symbol is not None and target_symbol[0] in {
                    "class",
                    "function",
                }:
                    object_kind = target_symbol[0]
            if selected_kinds and object_kind not in selected_kinds:
                continue
            action = "rewrite_compatibility_alias"
            violations.append(
                self._raw_violation(
                    project=project_name,
                    object_name=detector_violation.alias_name,
                    object_kind=object_kind,
                    kind="compatibility_alias",
                    file_path=file_path,
                    line=detector_violation.line,
                    description=(
                        "Compatibility alias "
                        f"'{detector_violation.alias_name}' should use "
                        f"'{detector_violation.target_name}' directly"
                    ),
                    fixable=True,
                    fix_action=action,
                )
            )
            fixes.append(
                m.Infra.Census.Fix(
                    object_name=detector_violation.alias_name,
                    action=action,
                    source_file=str(file_path),
                    files_changed=1,
                    applied=self._fix_key(
                        file_path,
                        detector_violation.alias_name,
                        action,
                    )
                    in applied,
                )
            )
        return violations, fixes

    def _rule_mro_completeness(
        self,
        rope: p.Infra.RopeWorkspaceDsl,
        file_path: Path,
        *,
        project_name: str,
        objects: tuple[m.Infra.Census.Object, ...] | None,
        applied: frozenset[str],
        selected_kinds: frozenset[str],
        symbol_index: dict[str, tuple[str, int]],
        convention: m.Infra.RopeModuleConvention,
    ) -> tuple[list[m.Infra.Census.Violation], list[m.Infra.Census.Fix]]:
        """Detect + plan fixes for MRO-completeness violations."""
        parse_failures: list[m.Infra.ParseFailureViolation] = []
        mro_ctx = self._detector_context(
            rope,
            file_path,
            parse_failures=parse_failures,
            convention=convention,
        )
        violations: list[m.Infra.Census.Violation] = []
        fixes: list[m.Infra.Census.Fix] = []
        for detector_violation in FlextInfraMROCompletenessDetector.detect_file(
            mro_ctx,
        ):
            matched = (
                self._named_object(objects, detector_violation.facade_class)
                if objects is not None
                else None
            )
            object_kind = matched.kind if matched is not None else "class"
            if selected_kinds and object_kind not in selected_kinds:
                continue
            symbol = symbol_index.get(detector_violation.facade_class)
            action = "rewrite_mro_completeness"
            violations.append(
                self._raw_violation(
                    project=project_name,
                    object_name=detector_violation.facade_class,
                    object_kind=object_kind,
                    kind="mro_completeness",
                    file_path=file_path,
                    line=(
                        matched.line
                        if matched is not None
                        else symbol[1]
                        if symbol is not None
                        else detector_violation.line
                    ),
                    description=detector_violation.suggestion,
                    fixable=True,
                    fix_action=action,
                )
            )
            fixes.append(
                m.Infra.Census.Fix(
                    object_name=detector_violation.facade_class,
                    action=action,
                    source_file=str(file_path),
                    files_changed=1,
                    applied=self._fix_key(
                        file_path,
                        detector_violation.facade_class,
                        action,
                    )
                    in applied,
                )
            )
        return violations, fixes


__all__: list[str] = ["FlextInfraRefactorCensusRulesStructMixin"]
