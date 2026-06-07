"""Text-rule executors for import/symbol/signature propagation — extracted concern."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import (
    FlextInfraRefactorClassReconstructor,
    FlextInfraRefactorImportModernizer,
    FlextInfraRefactorLazyImportFixer,
    FlextInfraRefactorSignaturePropagator,
    FlextInfraRefactorSymbolPropagator,
    FlextInfraTransformerTier0ImportFixer,
    c,
    m,
    p,
    t,
    u,
)


class FlextInfraRefactorTextPropagateMixin:
    """Import-modernizer / tier0-fix / symbol+signature+class propagation rules.

    Composed into FlextInfraRefactorTextExecutor via inheritance; the facade's
    ``_apply_text_rule_selection`` dispatcher resolves these through MRO, and
    these methods borrow ``_apply_change_tracker_transformer`` from the facade.
    """

    if TYPE_CHECKING:

        @staticmethod
        def _apply_change_tracker_transformer(
            transformer: p.Infra.ChangeTracker,
            source: str,
        ) -> t.Infra.TransformResult: ...

    def _apply_import_modernizer(
        self,
        settings: t.MappingKV[str, t.Infra.InfraValue],
        source: str,
    ) -> t.Infra.TransformResult:
        """Apply import modernizer."""
        settings_mapping = t.Cli.JSON_MAPPING_ADAPTER.validate_python(settings)
        fix_action = u.Cli.json_get_str_key(
            settings_mapping, c.Infra.RK_FIX_ACTION, case="lower"
        )
        if fix_action == "hoist_to_module_top":
            return self._apply_change_tracker_transformer(
                FlextInfraRefactorLazyImportFixer(),
                source,
            )
        metadata = u.read_project_constants("flext-infra")
        runtime_aliases = set(metadata.RUNTIME_ALIAS_NAMES)
        blocked = set(u.Infra.collect_blocked_aliases(source, runtime_aliases))
        blocked.update(u.Infra.collect_shadowed_aliases(source, runtime_aliases))
        forbidden = settings.get(c.Infra.RK_FORBIDDEN_IMPORTS)
        if forbidden is None:
            forbidden = t.Cli.JSON_LIST_ADAPTER.validate_python([
                t.Cli.JSON_MAPPING_ADAPTER.validate_python(settings),
            ])
        parsed_rules = tuple(u.Infra.parse_forbidden_rules(forbidden))
        modernizer = FlextInfraRefactorImportModernizer(
            imports_to_remove=[
                mod
                for rule_config in parsed_rules
                for mod in (
                    [rule_config.module]
                    + (
                        [rule_config.module.split(".", 1)[0]]
                        if "." in rule_config.module
                        else []
                    )
                )
            ],
            symbols_to_replace={
                key: value
                for rule_config in parsed_rules
                for key, value in rule_config.symbol_mapping.items()
            },
            runtime_aliases=runtime_aliases,
            blocked_aliases=blocked,
        )
        return modernizer.apply_to_source(source)

    def _apply_tier0_import_fix(
        self,
        settings: t.MappingKV[str, t.Infra.InfraValue],
        source: str,
        file_path: Path,
    ) -> t.Infra.TransformResult:
        """Apply tier0 import fix."""
        analyzer = FlextInfraTransformerTier0ImportFixer.Analyzer(
            file_path=file_path,
            tier0_modules=self._tuple_setting(
                settings,
                c.Infra.RK_TIER0_MODULES,
                (c.Infra.CONSTANTS_PY, c.Infra.TYPINGS_PY, c.Infra.PROTOCOLS_PY),
            ),
            core_aliases=self._tuple_setting(
                settings,
                c.Infra.RK_CORE_ALIASES,
                tuple(
                    u.read_project_constants(
                        "flext-infra"
                    ).UNIVERSAL_ALIAS_PARENT_SOURCES
                ),
            ),
        )
        analysis = analyzer.build_analysis()
        if not analysis.has_violations:
            return (source, list[str]())
        transformer = FlextInfraTransformerTier0ImportFixer.Transformer(
            analysis=analysis,
            alias_to_submodule=self._mapping_setting(
                settings, c.Infra.RK_ALIAS_TO_SUBMODULE
            ),
            core_package=str(
                settings.get(c.Infra.RK_CORE_PACKAGE, c.Infra.PKG_CORE_UNDERSCORE)
            ),
        )
        return u.Infra.apply_transformer_to_source(
            source, file_path, transformer.transform
        )

    def _apply_symbol_propagation(
        self,
        settings: t.MappingKV[str, t.Infra.InfraValue],
        source: str,
    ) -> t.Infra.TransformResult:
        """Apply symbol propagation."""
        transformer = FlextInfraRefactorSymbolPropagator(
            target_modules=set(
                u.Infra.string_list(settings.get(c.Infra.RK_TARGET_MODULES, []))
            ),
            module_renames=self._mapping_setting(settings, c.Infra.RK_MODULE_RENAMES),
            import_symbol_renames=self._mapping_setting(
                settings, c.Infra.RK_IMPORT_SYMBOL_RENAMES
            ),
        )
        return self._apply_change_tracker_transformer(transformer, source)

    def _apply_signature_propagation(
        self,
        settings: t.MappingKV[str, t.Infra.InfraValue],
        source: str,
    ) -> t.Infra.TransformResult:
        """Apply signature propagation."""
        try:
            typed_items = t.Infra.CONTAINER_DICT_SEQ_ADAPTER.validate_python(
                settings.get(c.Infra.RK_SIGNATURE_MIGRATIONS, []),
            )
        except c.ValidationError:
            return (source, list[str]())
        parsed = [
            m.Infra.SignatureMigration.model_validate(item) for item in typed_items
        ]
        migrations: t.SequenceOf[m.Infra.SignatureMigration] = [
            item for item in parsed if item.enabled
        ]
        if not migrations:
            return (source, list[str]())
        transformer = FlextInfraRefactorSignaturePropagator(migrations=migrations)
        return (transformer.apply_to_source(source), list(transformer.changes))

    def _apply_class_reconstructor(
        self,
        settings: t.MappingKV[str, t.Infra.InfraValue],
        source: str,
    ) -> t.Infra.TransformResult:
        """Apply class reconstructor."""
        try:
            order_config = t.Infra.CONTAINER_DICT_SEQ_ADAPTER.validate_python(
                settings.get(c.Infra.RK_METHOD_ORDER)
                or settings.get(c.Infra.RK_ORDER, []),
            )
        except c.ValidationError:
            return (source, list[str]())
        if not order_config:
            return (source, list[str]())
        return self._apply_change_tracker_transformer(
            FlextInfraRefactorClassReconstructor(order_config=order_config),
            source,
        )

    @staticmethod
    def _tuple_setting(
        settings: t.MappingKV[str, t.Infra.InfraValue],
        key: str,
        default: t.StrTuple,
    ) -> t.StrTuple:
        """Return tuple-valued setting."""
        value = settings.get(key, list(default))
        return (
            tuple(str(item) for item in value)
            if isinstance(value, list)
            else tuple(default)
        )

    @staticmethod
    def _mapping_setting(
        settings: t.MappingKV[str, t.Infra.InfraValue],
        key: str,
    ) -> t.StrMapping:
        """Mapping setting."""
        mapping_value = u.Cli.json_as_mapping(settings.get(key, {}))
        normalized_mapping: dict[str, str] = {
            item_key: str(item_value) for item_key, item_value in mapping_value.items()
        }
        return normalized_mapping


__all__: list[str] = ["FlextInfraRefactorTextPropagateMixin"]
