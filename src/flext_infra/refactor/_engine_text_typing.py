"""Text-rule executors for typing/annotation modernization — extracted concern."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import (
    FlextInfraRefactorTypingUnifier,
    c,
    m,
    p,
    t,
    u,
)


class FlextInfraRefactorTextTypingMixin:
    """Future-annotations, MRO-migration, and typing/annotation fix rules.

    Composed into FlextInfraRefactorTextExecutor via inheritance; the facade's
    ``_apply_text_rule_selection`` dispatcher resolves these through MRO, and
    these methods borrow ``_apply_change_tracker_transformer`` from the facade.
    """

    _SINGLE_LINE_DOCSTRING_MIN_LENGTH = 3

    if TYPE_CHECKING:

        @staticmethod
        def _apply_change_tracker_transformer(
            transformer: p.Infra.ChangeTracker,
            source: str,
        ) -> t.Infra.TransformResult: ...

    @staticmethod
    def _apply_future_annotations(source: str) -> t.Infra.TransformResult:
        """Apply future annotations."""
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
                    > FlextInfraRefactorTextTypingMixin._SINGLE_LINE_DOCSTRING_MIN_LENGTH
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
        """Apply mro class migration."""
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

    def _apply_typing_unification(
        self, source: str, file_path: Path
    ) -> t.Infra.TransformResult:
        """Apply typing unification."""
        return self._apply_change_tracker_transformer(
            FlextInfraRefactorTypingUnifier(
                canonical_map=c.Infra.TYPING_INLINE_UNION_CANONICAL_MAP,
                file_path=file_path,
            ),
            source,
        )

    def _apply_typing_annotation_fix(
        self,
        settings: t.MappingKV[str, t.Infra.InfraValue],
        source: str,
        file_path: Path,
    ) -> t.Infra.TransformResult:
        """Apply typing annotation fix."""
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
        """Replace object annotations."""
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
        """Remove redundant casts."""
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
        """Replace mapping annotations."""
        _ = rope_project
        source = resource.read()
        total = 0
        source, alias_count = c.Infra.DICT_STR_JSONVALUE_RE.subn(
            "t.JsonMapping",
            source,
        )
        total += alias_count
        source, generic_count = c.Infra.DICT_GENERIC_RE.subn("t.MappingKV[", source)
        total += generic_count
        if total > 0 and source != resource.read():
            resource.write(source)
        if total == 0:
            return (source, list[str]())
        return (
            source,
            [f"Converted {total} dict annotations to Mapping/t.JsonMapping"],
        )


__all__: list[str] = ["FlextInfraRefactorTextTypingMixin"]
