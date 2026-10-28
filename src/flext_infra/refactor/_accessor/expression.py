"""Semantic expression planning for declared accessor migrations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT.
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import ast
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from typing import TYPE_CHECKING

from flext_infra import m, u
from flext_infra.refactor._accessor import FlextInfraRefactorAccessorOrigin

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import t


class FlextInfraRefactorAccessorExpression:
    """Plan field normalization from the typed semantic migration catalog."""

    @classmethod
    def _normalize_field_accessors(
        cls,
        rope_project: t.Infra.RopeProject,
        py_file: Path,
        source: str,
        rules: Sequence[m.Infra.AccessorMigrationRule],
    ) -> tuple[str, Sequence[m.Infra.AccessorMigrationChange]]:
        """Plan complete expression replacements from exact member identities.

        Returns:
            The proposed source and its actual owned transformation receipts.

        Raises:
            ValueError: If a selected rule or owned use cannot be resolved safely.

        """
        tree = ast.parse(source, filename=str(py_file))
        resolver = FlextInfraRefactorAccessorOrigin(rope_project)
        replacements: MutableSequence[tuple[int, int, str]] = []
        changes: MutableSequence[m.Infra.AccessorMigrationChange] = []
        imports: MutableMapping[str, str] = {}
        for node in ast.walk(tree):
            if not isinstance(node, ast.Attribute):
                continue
            for rule in rules:
                if node.attr != rule.source_name:
                    continue
                if not cls._matches_expression_rule(
                    rope_project, py_file, source, node, rule
                ):
                    continue
                prefix = rule.replacement_name.split(".", maxsplit=1)[0]
                resolver.require_normalizer_binding(
                    py_file, source, tree, node, rule=rule
                )
                if prefix in imports and imports[prefix] != rule.origin:
                    msg = f"Conflicting accessor normalizer origins: {prefix}"
                    raise ValueError(msg)
                imports[prefix] = rule.origin
                replacement = cls._expression_replacement(py_file, source, node, rule)
                replacements.append(replacement)
                changes.append(
                    m.Infra.AccessorMigrationChange(
                        file=str(py_file),
                        line=node.lineno,
                        original_name=rule.source_name,
                        replacement_name=replacement[2],
                        automated=True,
                        reason=rule.reason,
                    ),
                )
        updated_source = cls._apply_expression_replacements(
            py_file, source, replacements
        )
        return cls._import_normalizers(
            rope_project, py_file, updated_source, imports
        ), tuple(changes)

    @staticmethod
    def _matches_expression_rule(
        rope_project: t.Infra.RopeProject,
        py_file: Path,
        source: str,
        node: ast.Attribute,
        rule: m.Infra.AccessorMigrationRule,
    ) -> bool:
        """Prove declared member ownership, including removed inherited accessors.

        Returns:
            Whether the expression belongs to the selected declaration.

        Raises:
            TypeError: If a proven read-only accessor is written.
            ValueError: If the rule or owned backing field cannot be proven.

        """
        if rule.field is None or rule.declaring_class is None:
            msg = f"Incomplete accessor expression rule: {rule.source_name}"
            raise ValueError(msg)
        resolver = FlextInfraRefactorAccessorOrigin(rope_project)
        members = resolver.receiver_attributes(py_file, source, node.value)
        previous = members.get(rule.source_name)
        if previous is not None:
            if resolver.declaring_class(previous) != rule.declaring_class:
                return False
            owned = True
        else:
            owned = resolver.receiver_inherits(
                py_file, source, node.value, rule.declaring_class
            )
        backing = members.get(rule.field)
        if backing is None or (
            resolver.declaring_class(backing) != rule.declaring_class
        ):
            if owned:
                msg = (
                    "Owned accessor backing field is missing or overridden: "
                    f"{py_file}:{node.lineno}"
                )
                raise ValueError(msg)
            return False
        if not isinstance(node.ctx, ast.Load):
            msg = f"Owned read-only accessor is written: {py_file}:{node.lineno}"
            raise TypeError(msg)
        return True

    @staticmethod
    def _expression_replacement(
        py_file: Path,
        source: str,
        node: ast.Attribute,
        rule: m.Infra.AccessorMigrationRule,
    ) -> tuple[int, int, str]:
        """Plan the exact source span for an owned accessor expression.

        Returns:
            The start, end and replacement source.

        Raises:
            ValueError: If the original source span is unavailable.

        """
        receiver = ast.get_source_segment(source, node.value)
        segment = ast.get_source_segment(source, node)
        if receiver is None or segment is None:
            msg = f"Accessor source span is unavailable: {py_file}:{node.lineno}"
            raise ValueError(msg)
        if not isinstance(node.value, ast.Name):
            receiver = f"({receiver})"
        replacement = f"{rule.replacement_name}({receiver}.{rule.field})"
        start = u.Infra.source_offset(source, node)
        return start, start + len(segment), replacement

    @staticmethod
    def _apply_expression_replacements(
        py_file: Path,
        source: str,
        replacements: Sequence[tuple[int, int, str]],
    ) -> str:
        """Apply the complete non-overlapping expression plan.

        Returns:
            Source containing every planned expression replacement.

        Raises:
            ValueError: If owned expression spans overlap.

        """
        end_previous = 0
        for start, end, _replacement in sorted(replacements):
            if start < end_previous:
                msg = f"Overlapping owned accessor expressions: {py_file}"
                raise ValueError(msg)
            end_previous = end
        updated_source = source
        for start, end, replacement in sorted(replacements, reverse=True):
            updated_source = updated_source[:start] + replacement + updated_source[end:]
        return updated_source

    @staticmethod
    def _import_normalizers(
        rope_project: t.Infra.RopeProject,
        py_file: Path,
        updated_source: str,
        imports: Mapping[str, str],
    ) -> str:
        """Plan imports against the complete expression snapshot.

        Returns:
            The source with its required public normalizer imports.

        Raises:
            ValueError: If a planned import has no Rope resource.

        """
        for prefix, origin in imports.items():
            snapshot = u.Infra.snapshot_project(
                rope_project,
                {py_file: updated_source},
            )
            resource = u.Infra.resolve_resource_from_path(snapshot, py_file)
            if resource is None:
                msg = f"Accessor import source has no Rope resource: {py_file}"
                raise ValueError(msg)
            imported = u.Infra.add_import(
                snapshot,
                resource,
                origin,
                (prefix,),
                apply=False,
            )
            if imported is not None:
                updated_source = imported
        return updated_source


__all__: list[str] = ["FlextInfraRefactorAccessorExpression"]
