"""Direct text-rule execution for the refactor engine."""

from __future__ import annotations

from pathlib import Path
from typing import override

from flext_infra import (
    FlextInfraRefactorLegacyTextOps,
    FlextInfraRefactorMRORemover,
    c,
    p,
    t,
    u,
)
from flext_infra.refactor._engine_text_propagate import (
    FlextInfraRefactorTextPropagateMixin,
)
from flext_infra.refactor._engine_text_typing import (
    FlextInfraRefactorTextTypingMixin,
)


class FlextInfraRefactorTextExecutor(
    FlextInfraRefactorLegacyTextOps,
    FlextInfraRefactorTextTypingMixin,
    FlextInfraRefactorTextPropagateMixin,
):
    """Execute declarative text rules directly from kind + settings."""

    def _apply_text_rule_selection(
        self,
        kind: c.Infra.RefactorRuleKind,
        settings: t.MappingKV[str, t.Infra.InfraValue],
        source: str,
        file_path: Path,
    ) -> t.Infra.TransformResult:
        """Apply text rule selection."""
        match kind:
            case c.Infra.RefactorRuleKind.FUTURE_ANNOTATIONS:
                result = self._apply_future_annotations(source)
            case c.Infra.RefactorRuleKind.MRO_CLASS_MIGRATION:
                result = self._apply_mro_class_migration(source, file_path)
            case c.Infra.RefactorRuleKind.LEGACY_REMOVAL:
                result = self._apply_legacy_removal(settings, source)
            case c.Infra.RefactorRuleKind.IMPORT_MODERNIZER:
                result = self._apply_import_modernizer(settings, source)
            case c.Infra.RefactorRuleKind.CLASS_RECONSTRUCTOR:
                result = self._apply_class_reconstructor(settings, source)
            case c.Infra.RefactorRuleKind.PATTERN_CORRECTIONS:
                result = self._apply_pattern_corrections(settings, source, file_path)
            case c.Infra.RefactorRuleKind.TYPING_UNIFICATION:
                result = self._apply_typing_unification(source, file_path)
            case c.Infra.RefactorRuleKind.TYPING_ANNOTATION_FIX:
                result = self._apply_typing_annotation_fix(settings, source, file_path)
            case c.Infra.RefactorRuleKind.TIER0_IMPORT_FIX:
                result = self._apply_tier0_import_fix(settings, source, file_path)
            case c.Infra.RefactorRuleKind.SYMBOL_PROPAGATION:
                result = self._apply_symbol_propagation(settings, source)
            case c.Infra.RefactorRuleKind.SIGNATURE_PROPAGATION:
                result = self._apply_signature_propagation(settings, source)
            case c.Infra.RefactorRuleKind.MRO_REDUNDANCY:
                result = self._apply_change_tracker_transformer(
                    FlextInfraRefactorMRORemover(),
                    source,
                )
            case _:
                result = (source, list[str]())
        return result

    @override
    @staticmethod
    def _apply_change_tracker_transformer(
        transformer: p.Infra.ChangeTracker,
        source: str,
    ) -> t.Infra.TransformResult:
        """Apply change tracker transformer."""
        apply_fn = getattr(transformer, "apply_to_source", None)
        if callable(apply_fn):
            result = apply_fn(source)
            new_source = (
                result[0]
                if isinstance(result, tuple) and result and isinstance(result[0], str)
                else source
            )
            return (new_source, list(getattr(transformer, "changes", list[str]())))
        return (source, list[str]())

    def _apply_pattern_corrections(
        self,
        settings: t.MappingKV[str, t.Infra.InfraValue],
        source: str,
        file_path: Path,
    ) -> t.Infra.TransformResult:
        """Apply pattern corrections."""
        settings_mapping = t.Cli.JSON_MAPPING_ADAPTER.validate_python(settings)
        fix_action = u.Cli.json_get_str_key(
            settings_mapping, c.Infra.RK_FIX_ACTION, case="lower"
        )
        if fix_action == "fix_silent_failure_sentinels":
            return u.Infra.apply_transformer_to_source(
                source,
                file_path,
                lambda rope_project, resource: u.Infra.fix_silent_failure_sentinels(
                    rope_project,
                    resource,
                    apply=True,
                ),
            )
        if fix_action == "remove_redundant_casts":
            return u.Infra.apply_transformer_to_source(
                source,
                file_path,
                self._remove_redundant_casts,
            )
        return u.Infra.apply_transformer_to_source(
            source,
            file_path,
            self._replace_mapping_annotations,
        )


__all__: list[str] = ["FlextInfraRefactorTextExecutor"]
