"""Signature propagation transformer."""

from __future__ import annotations

import ast
from collections.abc import Sequence
from operator import itemgetter

from flext_infra import FlextInfraChangeTrackingTransformer, m, t, u


class FlextInfraRefactorSignaturePropagator(FlextInfraChangeTrackingTransformer):
    """Apply declarative signature migrations to call sites via regex."""

    def __init__(
        self,
        *,
        migrations: Sequence[m.Infra.SignatureMigration],
        on_change: t.Infra.ChangeCallback = None,
    ) -> None:
        """Initialize transformer state for declarative signature migrations."""
        super().__init__(on_change=on_change)
        self._migrations = migrations

    def apply_to_source(self, source: str) -> str:
        """Apply all migrations to source text and return transformed source."""
        result = source
        for migration in self._migrations:
            result = self._apply_migration(result, migration)
        return result

    def _apply_migration(
        self,
        source: str,
        migration: m.Infra.SignatureMigration,
    ) -> str:
        """Apply a single migration to source text."""
        migration_id = str(migration.id)
        keyword_renames = dict(migration.keyword_renames)
        remove_keywords = set(migration.remove_keywords)
        add_keywords = dict(migration.add_keywords)
        if not keyword_renames and not remove_keywords and not add_keywords:
            return source
        targets = set(migration.target_simple_names) | set(
            migration.target_qualified_names
        )
        for target in targets:
            simple_name = target.rsplit(".", 1)[-1] if "." in target else target
            source = self._rewrite_calls(
                source,
                simple_name=simple_name,
                migration_id=migration_id,
                keyword_renames=keyword_renames,
                remove_keywords=remove_keywords,
                add_keywords=add_keywords,
            )
        return source

    def _rewrite_calls(
        self,
        source: str,
        *,
        simple_name: str,
        migration_id: str,
        keyword_renames: t.MutableStrMapping,
        remove_keywords: t.Infra.StrSet,
        add_keywords: t.MutableStrMapping,
    ) -> str:
        """Rewrite keyword arguments in calls to simple_name."""
        try:
            module = ast.parse(source)
        except SyntaxError:
            return source
        line_offsets = self._line_offsets(source)
        edits: list[tuple[int, int, str]] = []
        for node in ast.walk(module):
            if not isinstance(node, ast.Call):
                continue
            if not self._matches_target(node.func, simple_name):
                continue
            replacement, changed = self._rewrite_call_node(
                node,
                keyword_renames=keyword_renames,
                remove_keywords=remove_keywords,
                add_keywords=add_keywords,
            )
            if not changed:
                continue
            start = self._offset(
                line_offsets,
                node.lineno,
                node.col_offset,
            )
            end = self._offset(
                line_offsets,
                node.end_lineno or node.lineno,
                node.end_col_offset or node.col_offset,
            )
            edits.append((start, end, replacement))
            self._record_change(f"[{migration_id}] Updated call: {simple_name}(...)")
        updated = source
        for start, end, replacement in sorted(
            edits,
            key=itemgetter(0),
            reverse=True,
        ):
            updated = updated[:start] + replacement + updated[end:]
        return updated

    @staticmethod
    def _matches_target(func: t.Infra.AstExpr, simple_name: str) -> bool:
        """Return whether a call target matches the migrated simple name."""
        if isinstance(func, ast.Name):
            return func.id == simple_name
        if isinstance(func, ast.Attribute):
            return func.attr == simple_name
        return False

    def _rewrite_call_node(
        self,
        node: t.Infra.AstCall,
        *,
        keyword_renames: t.MutableStrMapping,
        remove_keywords: t.Infra.StrSet,
        add_keywords: t.MutableStrMapping,
    ) -> tuple[str, bool]:
        rewritten_keywords: list[t.Infra.AstKeyword] = []
        changed = False
        for keyword in node.keywords:
            if keyword.arg is None:
                rewritten_keywords.append(keyword)
                continue
            renamed = keyword_renames.get(keyword.arg, keyword.arg)
            if renamed != keyword.arg:
                changed = True
            if keyword.arg in remove_keywords or renamed in remove_keywords:
                changed = True
                continue
            rewritten_keywords.append(ast.keyword(arg=renamed, value=keyword.value))
        present_keywords = {
            keyword.arg for keyword in rewritten_keywords if keyword.arg is not None
        }
        for key, value_literal in add_keywords.items():
            if key in present_keywords:
                continue
            rewritten_keywords.append(
                ast.keyword(arg=key, value=self._literal_expr(value_literal))
            )
            changed = True
        if not changed:
            return ast.unparse(node), False
        rewritten_call = ast.Call(
            func=node.func,
            args=node.args,
            keywords=rewritten_keywords,
        )
        return ast.unparse(rewritten_call), True

    @staticmethod
    def _literal_expr(value_literal: str) -> t.Infra.AstExpr:
        """Parse an expression literal used by add_keywords."""
        try:
            parsed = ast.parse(value_literal, mode="eval")
        except SyntaxError:
            return ast.Constant(value=u.norm_str(value_literal))
        return parsed.body

    @staticmethod
    def _line_offsets(source: str) -> Sequence[int]:
        offsets = [0]
        for line in source.splitlines(keepends=True):
            offsets.append(offsets[-1] + len(line))
        return offsets

    @staticmethod
    def _offset(line_offsets: Sequence[int], line: int, column: int) -> int:
        return line_offsets[line - 1] + column


__all__ = ["FlextInfraRefactorSignaturePropagator"]
