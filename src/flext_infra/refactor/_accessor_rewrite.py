"""Origin-proven token rewriting for declared accessor migrations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT.
"""

from __future__ import annotations

import io
from operator import itemgetter
from tokenize import NAME, generate_tokens
from typing import TYPE_CHECKING, ClassVar

from flext_infra import c, m, u
from flext_infra.refactor._accessor_expression import (
    FlextInfraAccessorMigrationExpressionMixin,
)
from flext_infra.refactor._accessor_origin import FlextInfraAccessorOriginResolver
from flext_infra.refactor._accessor_warnings import (
    FlextInfraAccessorMigrationWarningsMixin,
)

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import t


class FlextInfraAccessorMigrationRewriteMixin(
    FlextInfraAccessorMigrationExpressionMixin,
    FlextInfraAccessorMigrationWarningsMixin,
):
    """Compose token renames, expression planning, and manual review detection."""

    _AUTOMATED_RULES: ClassVar[t.VariadicTuple[m.Infra.AccessorMigrationRule]] = tuple(
        m.Infra.AccessorMigrationRule(
            source_name=src,
            replacement_name=repl,
            reason=reason,
            origin="flext_core",
        )
        for src, (repl, reason) in c.ENFORCEMENT_ACCESSOR_RENAMES.items()
    )
    _SKIPPED_ORIGIN_REASON: ClassVar[str] = (
        "Skipped homonym: resolves to {definition}; only {origin}-owned "
        "definitions are renamed automatically"
    )

    def _apply_automated_rewrites(
        self,
        rope_project: t.Infra.RopeProject,
        py_file: Path,
        source: str,
    ) -> t.Pair[str, t.SequenceOf[m.Infra.AccessorMigrationChange]]:
        """Apply the declared semantic migrations.

        Returns:
            The proposed source and its migration receipts.
        """
        resource = u.Infra.resolve_resource_from_path(rope_project, py_file)
        if resource is None:
            return source, ()
        resolver = FlextInfraAccessorOriginResolver(rope_project)
        updated_source = source
        changes: t.MutableSequenceOf[m.Infra.AccessorMigrationChange] = []
        declared = self._expression_catalog()
        for rule in (*self._AUTOMATED_RULES, *declared):
            if rule.operation != "rename":
                continue
            updated_source, rule_changes = self._rename_symbol_tokens(
                updated_source,
                rule=rule,
                file_path=py_file,
                resolver=resolver,
            )
            changes.extend(rule_changes)
        expression_rules = tuple(
            rule for rule in declared if rule.operation == "normalize-field"
        )
        if expression_rules:
            snapshot = u.Infra.snapshot_project(
                rope_project,
                {py_file: updated_source},
            )
            updated_source, expression_changes = self._normalize_field_accessors(
                snapshot,
                py_file,
                updated_source,
                expression_rules,
            )
            changes.extend(expression_changes)
        return updated_source, tuple(changes)

    @classmethod
    def _rename_symbol_tokens(
        cls,
        source: str,
        *,
        rule: m.Infra.AccessorMigrationRule,
        file_path: Path,
        resolver: FlextInfraAccessorOriginResolver,
    ) -> t.Pair[str, t.SequenceOf[m.Infra.AccessorMigrationChange]]:
        """Rename only origin-owned occurrences of one rule's source name.

        Returns:
            The proposed source and actual rename or review receipts.
        """
        token_changes: t.MutableSequenceOf[m.Infra.AccessorMigrationChange] = []
        rewrite_ranges: t.MutableSequenceOf[t.Triple[int, int, str]] = []
        skipped_by_definition: dict[str, int] = {}
        for token in generate_tokens(io.StringIO(source).readline):
            if token.type != NAME or token.string != rule.source_name:
                continue
            line, column = token.start
            start = cls._offset_from_position(source, line, column)
            end = start + len(rule.source_name)
            definition = resolver.occurrence_origin(file_path, start)
            if definition is None or not resolver.within_origin(
                definition,
                origin=rule.origin,
            ):
                skipped_by_definition[definition or "an unresolved module"] = line
                continue
            rewrite_ranges.append((start, end, rule.replacement_name))
            token_changes.append(
                m.Infra.AccessorMigrationChange(
                    file=str(file_path),
                    line=line,
                    original_name=rule.source_name,
                    replacement_name=rule.replacement_name,
                    automated=True,
                    reason=rule.reason,
                ),
            )
        for definition, first_line in sorted(
            skipped_by_definition.items(),
            key=itemgetter(1),
        ):
            token_changes.append(
                m.Infra.AccessorMigrationChange(
                    file=str(file_path),
                    line=first_line,
                    original_name=rule.source_name,
                    replacement_name="",
                    automated=False,
                    reason=cls._SKIPPED_ORIGIN_REASON.format(
                        definition=definition,
                        origin=rule.origin,
                    ),
                ),
            )
        if not rewrite_ranges:
            return source, tuple(token_changes)
        updated_source = source
        for start, end, replacement in sorted(
            rewrite_ranges,
            key=itemgetter(0),
            reverse=True,
        ):
            updated_source = updated_source[:start] + replacement + updated_source[end:]
        return updated_source, tuple(token_changes)

    @staticmethod
    def _offset_from_position(source: str, line: int, column: int) -> int:
        """Resolve a token's character offset.

        Returns:
            The source offset corresponding to the token position.
        """
        source_lines = source.splitlines(keepends=True)
        line_offset = sum(len(item) for item in source_lines[: line - 1])
        return line_offset + column


__all__: list[str] = ["FlextInfraAccessorMigrationRewriteMixin"]
