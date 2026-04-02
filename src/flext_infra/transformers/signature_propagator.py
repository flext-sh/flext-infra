"""Signature propagation transformer — declarative signature migrations via rope.

Replaces CST-based call site rewriting with regex-based pattern matching
and rope's replace_in_source for keyword argument transformations.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import ClassVar

from flext_infra import FlextInfraChangeTrackingTransformer, m, t, u


class FlextInfraRefactorSignaturePropagator(FlextInfraChangeTrackingTransformer):
    """Apply declarative signature migrations to call sites via regex."""

    _KEYWORD_LITERALS: ClassVar[t.StrMapping] = {
        "true": "True",
        "false": "False",
        "none": "None",
    }

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
        for old_name, new_name in keyword_renames.items():
            pattern = re.compile(
                rf"(?<=\b{re.escape(simple_name)}\()"
                rf"(.*?)\b{re.escape(old_name)}\s*=",
                re.DOTALL,
            )
            if pattern.search(source):
                source = re.sub(
                    rf"\b{re.escape(old_name)}\s*=",
                    f"{new_name}=",
                    source,
                )
                self._record_change(
                    f"[{migration_id}] Renamed keyword: {old_name} -> {new_name}",
                )
        for kw in remove_keywords:
            pattern = re.compile(
                rf",?\s*\b{re.escape(kw)}\s*=[^,)]*",
            )
            new_source, count = pattern.subn("", source)
            if count > 0:
                source = new_source
                self._record_change(f"[{migration_id}] Removed keyword: {kw}")
        for key, value_literal in add_keywords.items():
            call_pattern = re.compile(
                rf"(\b{re.escape(simple_name)}\([^)]*)\)",
            )
            if not re.search(rf"\b{re.escape(key)}\s*=", source):
                normalized = self._normalize_literal(value_literal)
                source = call_pattern.sub(rf"\1, {key}={normalized})", source)
                self._record_change(
                    f"[{migration_id}] Added keyword: {key}={value_literal}",
                )
        return source

    def _normalize_literal(self, value: str) -> str:
        """Normalize a literal value string for insertion."""
        lowered = u.norm_str(value, case="lower")
        keyword_name = self._KEYWORD_LITERALS.get(lowered)
        if keyword_name is not None:
            return keyword_name
        if value.isdigit():
            return value
        if self._is_quoted_string(value):
            return value
        return value

    @staticmethod
    def _is_quoted_string(value: str) -> bool:
        """Check if value is a single- or double-quoted string literal."""
        return (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        )


__all__ = ["FlextInfraRefactorSignaturePropagator"]
