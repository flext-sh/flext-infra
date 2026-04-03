"""Rule subclasses for the refactor engine.

Extracted from engine.py to isolate transformer instantiation from the
orchestration layer. Each rule overrides FlextInfraRefactorRule.apply()
and delegates to a specific rope-based transformer.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import override

from pydantic import TypeAdapter, ValidationError

from flext_infra import (
    FlextInfraChangeTracker,
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
    FlextInfraTypingAnnotationReplacer,
    c,
    m,
    t,
    u,
)

_SIG_MIGRATION_SEQ_ADAPTER: TypeAdapter[Sequence[m.Infra.SignatureMigration]] = (
    TypeAdapter(Sequence[m.Infra.SignatureMigration])
)


class FlextInfraRefactorMRORedundancyChecker(FlextInfraGenericTransformerRule):
    """Detect and fix nested classes inheriting from their parent namespace."""

    TRANSFORMER_CLASS: type[FlextInfraChangeTracker] = FlextInfraRefactorMRORemover


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
            self._ROPE_RULE_CLS(self.config)
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
        fix_action = u.Infra.get_str_key(
            self.config,
            c.Infra.ReportKeys.FIX_ACTION,
            lower=True,
        )
        if fix_action == "replace_object_annotations":
            return self._apply_text_transformer(
                FlextInfraTypingAnnotationReplacer(),
                source,
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
        project_root = u.Infra.discover_project_root_from_file(_file_path)
        core_package = (
            u.Infra.discover_core_package(project_root)
            if project_root
            else self._core_package()
        )
        transformer = FlextInfraTransformerTier0ImportFixer.Transformer(
            analysis=analysis,
            alias_to_submodule=self._alias_to_submodule(),
            core_package=core_package,
        )
        return u.Infra.apply_transformer_to_source(
            source,
            _file_path,
            transformer.transform,
        )

    def _tier0_modules(self) -> tuple[str, ...]:
        value = self.config.get("tier0_modules", [])
        if not isinstance(value, list):
            return (
                c.Infra.Files.CONSTANTS_PY,
                c.Infra.Files.TYPINGS_PY,
                c.Infra.Files.PROTOCOLS_PY,
            )
        return tuple(str(item) for item in value)

    def _core_aliases(self) -> tuple[str, ...]:
        value = self.config.get("core_aliases", [])
        if not isinstance(value, list):
            return tuple(c.Infra.NAMESPACE_SOURCE_UNIVERSAL_ALIASES)
        return tuple(str(item) for item in value)

    def _core_package(self) -> str:
        return str(self.config.get("core_package", c.Infra.Packages.CORE_UNDERSCORE))

    def _alias_to_submodule(self) -> t.StrMapping:
        value = self.config.get("alias_to_submodule", {})
        if not u.is_mapping(value):
            return dict[str, str]()
        return {str(key): str(item) for key, item in value.items()}


class FlextInfraRefactorSymbolPropagationRule(FlextInfraRefactorRule):
    """Apply declarative module/symbol renames for workspace-wide propagation."""

    @override
    def apply(
        self,
        source: str,
        _file_path: Path | None = None,
    ) -> t.Infra.TransformResult:
        typed_cfg: Mapping[str, t.Infra.InfraValue] = (
            t.Infra.INFRA_MAPPING_ADAPTER.validate_python(self.config)
        )
        target_modules = set(u.Infra.string_list(typed_cfg.get("target_modules", [])))
        try:
            module_renames: t.StrMapping = t.Infra.STR_MAPPING_ADAPTER.validate_python(
                typed_cfg.get("module_renames", {}),
            )
        except ValidationError:
            module_renames = dict[str, str]()
        try:
            symbol_renames: t.StrMapping = t.Infra.STR_MAPPING_ADAPTER.validate_python(
                typed_cfg.get("import_symbol_renames", {}),
            )
        except ValidationError:
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
        migrations_raw = self.config.get("signature_migrations", [])
        try:
            parsed: Sequence[m.Infra.SignatureMigration] = (
                _SIG_MIGRATION_SEQ_ADAPTER.validate_python(migrations_raw)
            )
        except ValidationError:
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
        """Apply method reordering transformer when order config is available."""
        order_config_raw = self.config.get("method_order") or self.config.get(
            "order",
            [],
        )
        try:
            order_config: Sequence[t.Infra.ContainerDict] = (
                t.Infra.CONTAINER_DICT_SEQ_ADAPTER.validate_python(order_config_raw)
            )
        except ValidationError:
            return (source, list[str]())
        if not order_config:
            return (source, list[str]())
        transformer = FlextInfraRefactorClassReconstructor(order_config=order_config)
        return self._apply_text_transformer(transformer, source)


__all__ = [
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
