"""Direct text-rule execution for the refactor engine."""

from __future__ import annotations

import re
from collections.abc import (
    Mapping,
    Sequence,
)
from pathlib import Path

from flext_infra import (
    FlextInfraRefactorClassReconstructor,
    FlextInfraRefactorImportModernizer,
    FlextInfraRefactorLazyImportFixer,
    FlextInfraRefactorMRORemover,
    FlextInfraRefactorSignaturePropagator,
    FlextInfraRefactorSymbolPropagator,
    FlextInfraRefactorTypingUnifier,
    FlextInfraTransformerTier0ImportFixer,
    c,
    m,
    p,
    t,
    u,
)

from .engine_legacy import FlextInfraRefactorLegacyTextOps


class FlextInfraRefactorTextExecutor(FlextInfraRefactorLegacyTextOps):
    """Execute declarative text rules directly from kind + settings."""

    _SINGLE_LINE_DOCSTRING_MIN_LENGTH = 3

    def _apply_text_rule_selection(
        self,
        kind: c.Infra.RefactorRuleKind,
        settings: Mapping[str, t.Infra.InfraValue],
        source: str,
        file_path: Path,
    ) -> t.Infra.TransformResult:
        match kind:
            case c.Infra.RefactorRuleKind.FUTURE_ANNOTATIONS:
                return self._apply_future_annotations(source)
            case c.Infra.RefactorRuleKind.MRO_CLASS_MIGRATION:
                return self._apply_mro_class_migration(source, file_path)
            case c.Infra.RefactorRuleKind.LEGACY_REMOVAL:
                return self._apply_legacy_removal(settings, source)
            case c.Infra.RefactorRuleKind.IMPORT_MODERNIZER:
                return self._apply_import_modernizer(settings, source)
            case c.Infra.RefactorRuleKind.CLASS_RECONSTRUCTOR:
                return self._apply_class_reconstructor(settings, source)
            case c.Infra.RefactorRuleKind.PATTERN_CORRECTIONS:
                return self._apply_pattern_corrections(settings, source, file_path)
            case c.Infra.RefactorRuleKind.TYPING_UNIFICATION:
                return self._apply_typing_unification(source, file_path)
            case c.Infra.RefactorRuleKind.TYPING_ANNOTATION_FIX:
                return self._apply_typing_annotation_fix(settings, source, file_path)
            case c.Infra.RefactorRuleKind.TIER0_IMPORT_FIX:
                return self._apply_tier0_import_fix(settings, source, file_path)
            case c.Infra.RefactorRuleKind.SYMBOL_PROPAGATION:
                return self._apply_symbol_propagation(settings, source)
            case c.Infra.RefactorRuleKind.SIGNATURE_PROPAGATION:
                return self._apply_signature_propagation(settings, source)
            case c.Infra.RefactorRuleKind.MRO_REDUNDANCY:
                return self._apply_change_tracker_transformer(
                    FlextInfraRefactorMRORemover(),
                    source,
                )
            case _:
                return (source, list[str]())

    @staticmethod
    def _apply_change_tracker_transformer(
        transformer: p.Infra.ChangeTracker,
        source: str,
    ) -> t.Infra.TransformResult:
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

    @staticmethod
    def _apply_future_annotations(source: str) -> t.Infra.TransformResult:
        future_import = c.Infra.FUTURE_ANNOTATIONS
        lines = [line for line in source.splitlines() if line.strip() != future_import]
        insert_idx = 0
        in_docstring = False
        docstring_char = ""
        for index, line in enumerate(lines):
            stripped = line.strip()
            if in_docstring:
                if stripped.endswith(docstring_char):
                    in_docstring = False
                    insert_idx = index + 1
                continue
            if stripped.startswith(('"""', "'''")):
                doc_char = '"""' if stripped.startswith('"""') else "'''"
                if (
                    stripped.endswith(doc_char)
                    and len(stripped)
                    > FlextInfraRefactorTextExecutor._SINGLE_LINE_DOCSTRING_MIN_LENGTH
                ):
                    insert_idx = index + 1
                    continue
                in_docstring = True
                docstring_char = doc_char
                continue
            if not stripped:
                continue
            insert_idx = index
            break
        insert_idx = min(insert_idx, len(lines))
        new_lines = list(lines)
        if insert_idx > 0 and new_lines[insert_idx - 1].strip():
            new_lines.insert(insert_idx, "")
            insert_idx += 1
        new_lines.insert(insert_idx, future_import)
        if insert_idx + 1 < len(new_lines) and new_lines[insert_idx + 1].strip():
            new_lines.insert(insert_idx + 1, "")
        updated = "\n".join(new_lines) + "\n"
        if updated == source:
            return (source, list[str]())
        return (updated, ["Ensured: from __future__ import annotations"])

    @staticmethod
    def _apply_mro_class_migration(
        source: str, file_path: Path
    ) -> t.Infra.TransformResult:
        if file_path.name != c.Infra.CONSTANTS_PY:
            return (source, list[str]())
        candidates = u.Infra.find_final_candidates(source)
        if not candidates:
            return (source, list[str]())
        scan_result = m.Infra.MROScanReport(
            file=str(file_path),
            module="",
            constants_class=u.Infra.first_constants_class_name(source),
            candidates=tuple(candidates),
        )
        updated, migration, _ = u.Infra.migrate_file(scan_result=scan_result)
        if not migration.moved_symbols or updated == source:
            return (source, list[str]())
        return (
            updated,
            [
                f"migrated constants into facade class: {', '.join(migration.moved_symbols)}"
            ],
        )

    def _apply_import_modernizer(
        self,
        settings: Mapping[str, t.Infra.InfraValue],
        source: str,
    ) -> t.Infra.TransformResult:
        settings_mapping = t.Cli.JSON_MAPPING_ADAPTER.validate_python(settings)
        fix_action = u.Cli.json_get_str_key(
            settings_mapping, c.Infra.RK_FIX_ACTION, case="lower"
        )
        if fix_action == "hoist_to_module_top":
            return self._apply_change_tracker_transformer(
                FlextInfraRefactorLazyImportFixer(),
                source,
            )
        runtime_aliases = set(c.RUNTIME_ALIAS_NAMES)
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

    def _apply_pattern_corrections(
        self,
        settings: Mapping[str, t.Infra.InfraValue],
        source: str,
        file_path: Path,
    ) -> t.Infra.TransformResult:
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

    def _apply_typing_unification(
        self, source: str, file_path: Path
    ) -> t.Infra.TransformResult:
        return self._apply_change_tracker_transformer(
            FlextInfraRefactorTypingUnifier(
                canonical_map=c.Infra.TYPING_INLINE_UNION_CANONICAL_MAP,
                file_path=file_path,
            ),
            source,
        )

    def _apply_typing_annotation_fix(
        self,
        settings: Mapping[str, t.Infra.InfraValue],
        source: str,
        file_path: Path,
    ) -> t.Infra.TransformResult:
        settings_mapping = t.Cli.JSON_MAPPING_ADAPTER.validate_python(settings)
        fix_action = u.Cli.json_get_str_key(
            settings_mapping, c.Infra.RK_FIX_ACTION, case="lower"
        )
        if fix_action != "replace_object_annotations":
            return (source, list[str]())
        return u.Infra.apply_transformer_to_source(
            source,
            file_path,
            lambda rope_project, resource: self._replace_object_annotations(
                rope_project, resource
            ),
        )

    @staticmethod
    def _replace_object_annotations(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> t.Infra.TransformResult:
        updated_source, count = u.Infra.batch_replace_annotations(
            rope_project,
            resource,
            {"t.JsonValue": "t.JsonValue"},
            apply=True,
        )
        if count == 0:
            return (updated_source, list[str]())
        return (
            updated_source,
            ["Replaced annotation: t.JsonValue -> t.JsonValue"],
        )

    @staticmethod
    def _remove_redundant_casts(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> t.Infra.TransformResult:
        updated_source, count = u.Infra.remove_redundant_cast(
            rope_project,
            resource,
            apply=True,
        )
        if count == 0:
            return (updated_source, list[str]())
        return (updated_source, [f"Removed {count} redundant cast() calls"])

    @staticmethod
    def _replace_mapping_annotations(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> t.Infra.TransformResult:
        _ = rope_project
        source = resource.read()
        total = 0
        alias_pattern = re.compile(r"\b(?:dict|Dict)\[str,\s*t\.JsonValue\]")
        source, alias_count = alias_pattern.subn("t.JsonMapping", source)
        total += alias_count
        generic_pattern = re.compile(r"\b(?:dict|Dict)\[")
        source, generic_count = generic_pattern.subn("Mapping[", source)
        total += generic_count
        if total > 0 and source != resource.read():
            resource.write(source)
        if total == 0:
            return (source, list[str]())
        return (
            source,
            [f"Converted {total} dict annotations to Mapping/t.JsonMapping"],
        )

    def _apply_tier0_import_fix(
        self,
        settings: Mapping[str, t.Infra.InfraValue],
        source: str,
        file_path: Path,
    ) -> t.Infra.TransformResult:
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
                tuple(c.Infra.NAMESPACE_SOURCE_UNIVERSAL_ALIASES),
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
        settings: Mapping[str, t.Infra.InfraValue],
        source: str,
    ) -> t.Infra.TransformResult:
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
        settings: Mapping[str, t.Infra.InfraValue],
        source: str,
    ) -> t.Infra.TransformResult:
        try:
            typed_items = t.Infra.CONTAINER_DICT_SEQ_ADAPTER.validate_python(
                settings.get(c.Infra.RK_SIGNATURE_MIGRATIONS, []),
            )
        except c.ValidationError:
            return (source, list[str]())
        parsed = [
            m.Infra.SignatureMigration.model_validate(item) for item in typed_items
        ]
        migrations: Sequence[m.Infra.SignatureMigration] = [
            item for item in parsed if item.enabled
        ]
        if not migrations:
            return (source, list[str]())
        transformer = FlextInfraRefactorSignaturePropagator(migrations=migrations)
        return (transformer.apply_to_source(source), list(transformer.changes))

    def _apply_class_reconstructor(
        self,
        settings: Mapping[str, t.Infra.InfraValue],
        source: str,
    ) -> t.Infra.TransformResult:
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
        settings: Mapping[str, t.Infra.InfraValue],
        key: str,
        default: t.StrSequence,
    ) -> tuple[str, ...]:
        value = settings.get(key, list(default))
        return (
            tuple(str(item) for item in value)
            if isinstance(value, list)
            else tuple(default)
        )

    @staticmethod
    def _mapping_setting(
        settings: Mapping[str, t.Infra.InfraValue],
        key: str,
    ) -> t.StrMapping:
        mapping_value = u.Cli.json_as_mapping(settings.get(key, {}))
        normalized_mapping: dict[str, str] = {
            item_key: str(item_value) for item_key, item_value in mapping_value.items()
        }
        return normalized_mapping


__all__: list[str] = ["FlextInfraRefactorTextExecutor"]
