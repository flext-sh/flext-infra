"""Per-identity authentication of operator-decided lint exemptions.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, u

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraReadonlyNamespace:
    """Authenticate exempt findings from source and native Rope identity.

    Identities are derived from the reported findings, never from a hand
    registry; nothing is exempt by rule name or by file. Ruff remains the
    diagnostic authority.
    """

    @classmethod
    def exempt_identities(
        cls,
        project_dir: Path,
        findings: t.SequenceOf[p.Infra.Issue],
    ) -> frozenset[t.Pair[t.Triple[Path, int, int], str]]:
        """Authenticate the findings an operator-decided exemption names.

        Two rules, one owner, both decided by the operator on 2026-10-25 and
        both authenticated per identity from source, never by name or file:

        - ``non-pep695-type-alias`` ("Exceção UP040 por identidade"): a PEP 613
          facade class publication, authenticated by the facade owner;
        - ``invalid-function-name`` ("property + exceção N802"): a read-only
          settings-protocol namespace branch, i.e. a ``@property`` getter of a
          ``typing.Protocol`` class taking only ``self``, with a declaration-only
          body and a return annotation that resolves to a class by native Rope
          identity.

        Returns:
            ``((path, row, column), rule)`` for each authenticated finding.

        """
        alias_rule = c.Infra.RUFF_NON_PEP695_TYPE_ALIAS
        naming_rule = c.Infra.RUFF_INVALID_FUNCTION_NAME
        rows: t.MutableMappingKV[str, t.MutableMappingKV[Path, set[int]]] = {
            alias_rule: {},
            naming_rule: {},
        }
        for finding in findings:
            if finding.code in rows:
                rows[finding.code].setdefault(Path(finding.file).resolve(), set()).add(
                    finding.line
                )
        exempt: set[t.Pair[t.Triple[Path, int, int], str]] = set()
        if rows[alias_rule]:
            exempt.update(
                (identity, alias_rule)
                for identity in u.Infra.facade_class_publications(
                    project_dir,
                    {
                        path: frozenset(lines)
                        for path, lines in rows[alias_rule].items()
                    },
                )
            )
        if rows[naming_rule]:
            exempt.update(
                (identity, naming_rule)
                for identity in cls._settings_branch_getters(
                    project_dir, rows[naming_rule]
                )
            )
        return frozenset(exempt)

    @classmethod
    def _settings_branch_getters(
        cls,
        project_dir: Path,
        rows: t.MappingKV[Path, set[int]],
    ) -> frozenset[t.Triple[Path, int, int]]:
        """Authenticate read-only settings-protocol branches at reported rows.

        Returns:
            Path, row and one-based name column of each authenticated getter.

        """
        getters: set[t.Triple[Path, int, int]] = set()
        with u.Infra.open_project(project_dir) as rope_project:
            for path, wanted in sorted(rows.items()):
                resource = u.Infra.resolve_resource_from_path(rope_project, path)
                if resource is None:
                    continue
                source = resource.read()
                tree = ast.parse(source, filename=str(path))
                if not cls._typing_symbol(tree, "Protocol"):
                    continue
                scope = u.Infra.build_string_module(
                    rope_project, source, resource=resource
                ).get_scope()
                for owner in ast.walk(tree):
                    if not (
                        isinstance(owner, ast.ClassDef)
                        and any(
                            isinstance(base, ast.Name) and base.id == "Protocol"
                            for base in owner.bases
                        )
                    ):
                        continue
                    for member in owner.body:
                        if not (
                            isinstance(member, ast.FunctionDef)
                            and member.lineno in wanted
                            and cls._readonly_getter_shape(tree, member)
                            and isinstance(member.returns, ast.Name | ast.Attribute)
                        ):
                            continue
                        returned = u.Infra.resolve_symbol(scope, member.returns)
                        if returned is not None and u.Infra.abstract_class(
                            returned.get_object()
                        ):
                            getters.add((
                                path,
                                member.lineno,
                                member.col_offset + len("def ") + 1,
                            ))
        return frozenset(getters)

    @classmethod
    def _readonly_getter_shape(cls, tree: ast.Module, node: ast.FunctionDef) -> bool:
        """Report whether a function is a declaration-only instance getter.

        Returns:
            Whether ``node`` is an unshadowed builtin ``@property`` taking only
            ``self`` whose body declares nothing.

        """
        args = node.args
        return (
            [arg.arg for arg in (*args.posonlyargs, *args.args)] == ["self"]
            and not (
                args.defaults
                or args.kw_defaults
                or args.kwonlyargs
                or args.vararg
                or args.kwarg
                or node.type_params
            )
            and len(node.decorator_list) == 1
            and isinstance(node.decorator_list[0], ast.Name)
            and node.decorator_list[0].id == "property"
            and not cls._bindings(tree, "property")
            and all(
                isinstance(statement, ast.Pass)
                or (
                    isinstance(statement, ast.Expr)
                    and isinstance(statement.value, ast.Constant)
                    and (
                        statement.value.value is Ellipsis
                        or isinstance(statement.value.value, str)
                    )
                )
                for statement in node.body
            )
        )

    @staticmethod
    def _bindings(tree: ast.AST, name: str) -> list[ast.AST]:
        """Include imports and stores, not just function declarations.

        Returns:
            Every potentially competing binding of the spelling.

        """
        return [
            node
            for node in ast.walk(tree)
            if (isinstance(node, c.Infra.AST_DEFINITION_TYPES) and node.name == name)
            or (
                isinstance(node, ast.Name)
                and isinstance(node.ctx, c.Infra.AST_UNBINDING_CONTEXT_TYPES)
                and node.id == name
            )
            or (
                isinstance(node, ast.Attribute)
                and isinstance(node.ctx, c.Infra.AST_UNBINDING_CONTEXT_TYPES)
                and node.attr == name
            )
            or (isinstance(node, ast.arg) and node.arg == name)
            or (
                isinstance(node, ast.alias)
                and (
                    node.name == "*" or (node.asname or node.name.split(".")[0]) == name
                )
            )
            or (isinstance(node, ast.ExceptHandler) and node.name == name)
            or (isinstance(node, ast.MatchAs) and node.name == name)
            or (isinstance(node, ast.MatchStar) and node.name == name)
            or (isinstance(node, ast.MatchMapping) and node.rest == name)
        ]

    @classmethod
    def _typing_symbol(cls, tree: ast.Module, name: str) -> bool:
        imports = [
            alias
            for node in tree.body
            if isinstance(node, ast.ImportFrom)
            and node.module in {"typing", "typing_extensions"}
            and not node.level
            for alias in node.names
            if alias.name == name and alias.asname is None
        ]
        return bool(imports) and cls._bindings(tree, name) == imports


__all__ = ["FlextInfraReadonlyNamespace"]
