"""Signature propagation transformer — declarative signature migrations."""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from typing import override

import libcst as cst
from libcst.metadata import QualifiedNameProvider

from flext_infra import m, t


class FlextInfraRefactorSignaturePropagator(cst.CSTTransformer):
    """Apply declarative signature migrations to callsites."""

    METADATA_DEPENDENCIES = (QualifiedNameProvider,)

    def __init__(
        self,
        *,
        migrations: Sequence[m.Infra.SignatureMigration],
        on_change: t.Infra.ChangeCallback = None,
    ) -> None:
        """Initialize transformer state for declarative signature migrations."""
        self._migrations = migrations
        self._on_change = on_change
        self.changes: MutableSequence[str] = []

    @override
    def leave_Call(
        self,
        original_node: cst.Call,
        updated_node: cst.Call,
    ) -> cst.BaseExpression:
        qualified_names = {
            item.name
            for item in self.get_metadata(
                QualifiedNameProvider,
                original_node.func,
                default=set(),
            )
        }
        simple_name = self._simple_callable_name(original_node.func)
        result_call = updated_node
        for migration in self._migrations:
            if not self._matches_migration(
                migration,
                qualified_names=qualified_names,
                simple_name=simple_name,
            ):
                continue
            migration_id = str(migration.id)
            keyword_renames = self._keyword_renames(migration)
            remove_keywords = self._remove_keywords(migration)
            add_keywords = self._add_keywords(migration)
            next_args: MutableSequence[cst.Arg] = []
            changed = False
            seen_keyword_names: t.Infra.StrSet = set()
            for arg in list(result_call.args):
                keyword_name = self._keyword_name(arg)
                if keyword_name is not None and keyword_name in remove_keywords:
                    changed = True
                    self._record_change(
                        f"[{migration_id}] Removed keyword: {keyword_name}",
                    )
                    continue
                if keyword_name is not None and keyword_name in keyword_renames:
                    renamed = keyword_renames[keyword_name]
                    next_args.append(arg.with_changes(keyword=cst.Name(renamed)))
                    seen_keyword_names.add(renamed)
                    changed = True
                    self._record_change(
                        f"[{migration_id}] Renamed keyword: {keyword_name} -> {renamed}",
                    )
                    continue
                next_args.append(arg)
                if keyword_name is not None:
                    seen_keyword_names.add(keyword_name)
            for key, value_literal in add_keywords.items():
                if key in seen_keyword_names:
                    continue
                next_args.append(
                    cst.Arg(
                        value=self._literal_expr(value_literal),
                        keyword=cst.Name(key),
                    ),
                )
                changed = True
                self._record_change(
                    f"[{migration_id}] Added keyword: {key}={value_literal}",
                )
            if changed:
                result_call = result_call.with_changes(args=tuple(next_args))
        return result_call

    def _add_keywords(
        self,
        migration: m.Infra.SignatureMigration,
    ) -> t.StrMapping:
        return migration.add_keywords

    def _keyword_name(self, arg: cst.Arg) -> str | None:
        if arg.keyword is None:
            return None
        return arg.keyword.value

    def _keyword_renames(
        self,
        migration: m.Infra.SignatureMigration,
    ) -> t.StrMapping:
        return migration.keyword_renames

    def _literal_expr(self, value: str) -> cst.BaseExpression:
        lowered = value.strip().lower()
        if lowered == "true":
            return cst.Name("True")
        if lowered == "false":
            return cst.Name("False")
        if lowered == "none":
            return cst.Name("None")
        if value.isdigit():
            return cst.Integer(value)
        if value.startswith('"') and value.endswith('"'):
            return cst.SimpleString(value)
        if value.startswith("'") and value.endswith("'"):
            return cst.SimpleString(value)
        return cst.Name(value)

    def _matches_migration(
        self,
        migration: m.Infra.SignatureMigration,
        *,
        qualified_names: t.Infra.StrSet,
        simple_name: str | None,
    ) -> bool:
        target_qualified = set(migration.target_qualified_names)
        target_simple = set(migration.target_simple_names)
        if target_qualified and qualified_names.intersection(target_qualified):
            return True
        return bool(
            simple_name is not None
            and target_simple
            and (simple_name in target_simple),
        )

    def _record_change(self, message: str) -> None:
        self.changes.append(message)
        if self._on_change is not None:
            self._on_change(message)

    def _remove_keywords(
        self,
        migration: m.Infra.SignatureMigration,
    ) -> t.Infra.StrSet:
        return set(migration.remove_keywords)

    def _simple_callable_name(self, expr: cst.BaseExpression) -> str | None:
        if isinstance(expr, cst.Name):
            return expr.value
        if isinstance(expr, cst.Attribute):
            return expr.attr.value
        return None


__all__ = ["FlextInfraRefactorSignaturePropagator"]
