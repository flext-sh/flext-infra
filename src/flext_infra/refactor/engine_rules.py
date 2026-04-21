"""Rule subclasses for the refactor engine.

Extracted from engine.py to isolate transformer instantiation from the
orchestration layer. Each rule overrides FlextInfraRefactorRule.apply()
and delegates to a specific rope-based transformer.
"""

from __future__ import annotations

from collections.abc import (
    Mapping,
    Sequence,
)
from pathlib import Path
from typing import override

from flext_infra import (
    FlextInfraGenericTransformerRule,
    FlextInfraRefactorClassReconstructor,
    FlextInfraRefactorLegacyRemovalRule,
    FlextInfraRefactorMROClassMigrationRule,
    FlextInfraRefactorMRORemover,
    FlextInfraRefactorPatternCorrectionsRule,
    FlextInfraRefactorRule,
    FlextInfraRefactorSignaturePropagator,
    FlextInfraRefactorSymbolPropagator,
    FlextInfraRefactorTypingUnifier,
    FlextInfraTransformerTier0ImportFixer,
    c,
    m,
    t,
    u,
)


class FlextInfraRefactorMRORedundancyChecker(FlextInfraGenericTransformerRule):
    """Detect and fix nested classes inheriting from their parent namespace."""

    TRANSFORMER_CLASS: type[p.Infra.ChangeTracker] = FlextInfraRefactorMRORemover


class _RopeTextRuleBridge(FlextInfraRefactorRule):
    """Bridge: delegates to a rope-based rule via ``apply_transformer_to_source``."""

    _ROPE_RULE_CLS: type | None = None
    _NEEDS_CONFIG: bool = True

    @override
    def apply(
        self,
        source: str,
        _file_path: Path | None = None,
    ) -> t.Infra.TransformResult:
        if _file_path is None or self._ROPE_RULE_CLS is None:
            return (source, list[str]())
        rule = (
            self._ROPE_RULE_CLS(self.settings)
            if self._NEEDS_CONFIG
            else self._ROPE_RULE_CLS()
        )
        return u.Infra.apply_transformer_to_source(
            source,
            _file_path,
            lambda rp, res: rule.apply(rp, res, dry_run=True),
        )


class FlextInfraRefactorLegacyRemovalTextRule(_RopeTextRuleBridge):
    """Rope-based legacy-removal rule via text engine."""

    _ROPE_RULE_CLS = FlextInfraRefactorLegacyRemovalRule


class FlextInfraRefactorPatternCorrectionsTextRule(_RopeTextRuleBridge):
    """Rope-based pattern-corrections rule via text engine."""

    _ROPE_RULE_CLS = FlextInfraRefactorPatternCorrectionsRule


class FlextInfraRefactorMROClassMigrationTextRule(_RopeTextRuleBridge):
    """Rope-based MRO class-migration rule via text engine."""

    _ROPE_RULE_CLS = FlextInfraRefactorMROClassMigrationRule
    _NEEDS_CONFIG = False


class FlextInfraRefactorTypingUnificationRule(FlextInfraRefactorRule):
    """Unify duplicate type alias definitions into canonical t.* contracts."""

    @override
    def apply(
        self,
        source: str,
        _file_path: Path | None = None,
    ) -> t.Infra.TransformResult:
        transformer = FlextInfraRefactorTypingUnifier(
            canonical_map=c.Infra.TYPING_INLINE_UNION_CANONICAL_MAP,
            file_path=_file_path,
        )
        return self._apply_text_transformer(transformer, source)


class FlextInfraRefactorTypingAnnotationFixRule(FlextInfraRefactorRule):
    """Replace legacy typing annotations with canonical t.* contracts."""

    @override
    def apply(
        self,
        source: str,
        _file_path: Path | None = None,
    ) -> t.Infra.TransformResult:
        fix_action = u.Cli.json_get_str_key(
            self.settings,
            c.Infra.RK_FIX_ACTION,
            case="lower",
        )
        if fix_action == "replace_object_annotations":
            if _file_path is None:
                return (source, list[str]())

            def _transform(
                rope_project: t.Infra.RopeProject,
                resource: t.Infra.RopeResource,
            ) -> t.Infra.TransformResult:
                replacements: t.StrMapping = {
                    "t.Container": "t.ContainerValue",
                }
                updated_source, count = u.Infra.batch_replace_annotations(
                    rope_project,
                    resource,
                    replacements,
                    apply=True,
                )
                if count == 0:
                    return (updated_source, list[str]())
                return (
                    updated_source,
                    [
                        f"Replaced annotation: {old} -> {new}"
                        for old, new in replacements.items()
                    ],
                )

            return u.Infra.apply_transformer_to_source(
                source,
                _file_path,
                _transform,
            )
        return (source, list[str]())


class FlextInfraRefactorTier0ImportFixRule(FlextInfraRefactorRule):
    """Enforce tier-0 import conventions via rope-based transformation."""

    @override
    def apply(
        self,
        source: str,
        _file_path: Path | None = None,
    ) -> t.Infra.TransformResult:
        if _file_path is None:
            return (source, list[str]())
        analyzer = FlextInfraTransformerTier0ImportFixer.Analyzer(
            file_path=_file_path,
            tier0_modules=self._tier0_modules(),
            core_aliases=self._core_aliases(),
        )
        analysis = analyzer.build_analysis()
        if not analysis.has_violations:
            return (source, list[str]())
        transformer = FlextInfraTransformerTier0ImportFixer.Transformer(
            analysis=analysis,
            alias_to_submodule=self._alias_to_submodule(),
            core_package=self._core_package(),
        )
        return u.Infra.apply_transformer_to_source(
            source,
            _file_path,
            transformer.transform,
        )

    def _tier0_modules(self) -> tuple[str, ...]:
        value = self.settings.get("tier0_modules", [])
        if not isinstance(value, list):
            return (
                c.Infra.CONSTANTS_PY,
                c.Infra.TYPINGS_PY,
                c.Infra.PROTOCOLS_PY,
            )
        return tuple(str(item) for item in value)

    def _core_aliases(self) -> tuple[str, ...]:
        value = self.settings.get("core_aliases", [])
        if not isinstance(value, list):
            return tuple(c.Infra.NAMESPACE_SOURCE_UNIVERSAL_ALIASES)
        return tuple(str(item) for item in value)

    def _core_package(self) -> str:
        return str(self.settings.get("core_package", c.Infra.PKG_CORE_UNDERSCORE))

    def _alias_to_submodule(self) -> t.StrMapping:
        value = self.settings.get("alias_to_submodule", {})
        mapping_value = u.Cli.json_as_mapping(value)
        if not mapping_value:
            return dict[str, str]()
        return {str(key): str(item) for key, item in mapping_value.items()}


class FlextInfraRefactorSymbolPropagationRule(FlextInfraRefactorRule):
    """Apply declarative module/symbol renames for workspace-wide propagation."""

    @override
    def apply(
        self,
        source: str,
        _file_path: Path | None = None,
    ) -> t.Infra.TransformResult:
        typed_cfg: Mapping[str, t.Infra.InfraValue] = (
            t.Infra.INFRA_MAPPING_ADAPTER.validate_python(self.settings)
        )
        target_modules = set(u.Infra.string_list(typed_cfg.get("target_modules", [])))
        try:
            module_renames: t.StrMapping = t.Infra.STR_MAPPING_ADAPTER.validate_python(
                typed_cfg.get("module_renames", {}),
            )
        except c.ValidationError:
            module_renames = dict[str, str]()
        try:
            symbol_renames: t.StrMapping = t.Infra.STR_MAPPING_ADAPTER.validate_python(
                typed_cfg.get("import_symbol_renames", {}),
            )
        except c.ValidationError:
            symbol_renames = dict[str, str]()
        if not target_modules and not module_renames and not symbol_renames:
            return (source, list[str]())
        transformer = FlextInfraRefactorSymbolPropagator(
            target_modules=target_modules,
            module_renames=module_renames,
            import_symbol_renames=symbol_renames,
        )
        return self._apply_text_transformer(transformer, source)


class FlextInfraRefactorSignaturePropagationRule(FlextInfraRefactorRule):
    """Apply declarative signature migrations in a generic, workspace-safe way."""

    @override
    def apply(
        self,
        source: str,
        _file_path: Path | None = None,
    ) -> t.Infra.TransformResult:
        migrations_raw = self.settings.get("signature_migrations", [])
        try:
            typed_items = t.Infra.CONTAINER_DICT_SEQ_ADAPTER.validate_python(
                migrations_raw,
            )
            parsed: Sequence[m.Infra.SignatureMigration] = [
                m.Infra.SignatureMigration.model_validate(item) for item in typed_items
            ]
        except c.ValidationError:
            return (source, list[str]())
        migrations = [item for item in parsed if item.enabled]
        if not migrations:
            return (source, list[str]())
        transformer = FlextInfraRefactorSignaturePropagator(migrations=migrations)
        new_source = transformer.apply_to_source(source)
        return (new_source, list(transformer.changes))


class FlextInfraRefactorClassReconstructorRule(FlextInfraRefactorRule):
    """Apply class method ordering reconstruction to matching class nodes."""

    @override
    def apply(
        self,
        source: str,
        _file_path: Path | None = None,
    ) -> t.Infra.TransformResult:
        """Apply method reordering transformer when order settings is available."""
        order_config_raw = self.settings.get("method_order") or self.settings.get(
            "order",
            [],
        )
        try:
            order_config: Sequence[t.Infra.ContainerDict] = (
                t.Infra.CONTAINER_DICT_SEQ_ADAPTER.validate_python(order_config_raw)
            )
        except c.ValidationError:
            return (source, list[str]())
        if not order_config:
            return (source, list[str]())
        transformer = FlextInfraRefactorClassReconstructor(order_config=order_config)
        return self._apply_text_transformer(transformer, source)


__all__: list[str] = [
    "FlextInfraRefactorClassReconstructorRule",
    "FlextInfraRefactorLegacyRemovalTextRule",
    "FlextInfraRefactorMROClassMigrationTextRule",
    "FlextInfraRefactorMRORedundancyChecker",
    "FlextInfraRefactorPatternCorrectionsTextRule",
    "FlextInfraRefactorSignaturePropagationRule",
    "FlextInfraRefactorSymbolPropagationRule",
    "FlextInfraRefactorTier0ImportFixRule",
    "FlextInfraRefactorTypingAnnotationFixRule",
    "FlextInfraRefactorTypingUnificationRule",
]
