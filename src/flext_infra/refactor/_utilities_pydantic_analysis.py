"""Static analysis helpers for Pydantic centralization refactors.

Centralizes the ``FlextInfraRefactorPydanticCentralizerAnalysis`` logic
into the MRO utility chain.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import operator
from collections.abc import MutableSequence, Sequence
from pathlib import Path

from flext_infra import FlextInfraUtilitiesParsing, c, m, t


class FlextInfraUtilitiesRefactorPydanticAnalysis:
    """Static analysis helpers for Pydantic centralization.

    Usage via namespace::

        from flext_infra import u

        violations = u.Infra.scan_file_violations(path)
        moves = u.Infra.collect_moves(path)
    """

    _PYDANTIC_MODEL_BASES: t.StrSequence = (
        "BaseModel",
        "RootModel",
        "TypedDict",
        "ArbitraryTypesModel",
        "FrozenModel",
        "FrozenStrictModel",
    )
    _PYDANTIC_TYPED_DICT_MIN_ARGS: int = 2

    @staticmethod
    def _class_base_names(node: ast.ClassDef) -> t.Infra.StrSet:
        names: t.Infra.StrSet = set()
        for base in node.bases:
            if isinstance(base, ast.Name):
                names.add(base.id)
            elif isinstance(base, ast.Attribute):
                names.add(base.attr)
                root = ast.unparse(base)
                if root:
                    names.add(root)
        return names

    @staticmethod
    def is_top_level_model_class(node: ast.stmt) -> bool:
        """Return True when statement is a top-level model-like class."""
        if not isinstance(node, ast.ClassDef):
            return False
        base_names = FlextInfraUtilitiesRefactorPydanticAnalysis._class_base_names(
            node,
        )
        model_bases = FlextInfraUtilitiesRefactorPydanticAnalysis._PYDANTIC_MODEL_BASES
        return any(
            bn in model_bases or bn.startswith("FlextModels.") for bn in base_names
        )

    _DICT_ALIAS_KEYS: tuple[str, ...] = (
        "dict",
        "payload",
        "schema",
        "entry",
        "config",
        "metadata",
        "fixture",
        "case",
    )

    @staticmethod
    def _extract_alias_candidate(
        node: ast.stmt,
        source: str,
        *,
        is_typings_scope: bool,
    ) -> tuple[str, str] | None:
        """Extract (alias_name, expr) from an alias-like node, or None."""
        keys = FlextInfraUtilitiesRefactorPydanticAnalysis._DICT_ALIAS_KEYS
        dict_markers = ("Mapping[", "MutableMapping[")
        match node:
            case ast.TypeAlias():
                alias_name = node.name.id
                value_node = node.value
            case ast.AnnAssign(target=ast.Name() as target, value=value) if (
                value is not None
            ):
                alias_name = target.id
                annotation = ast.get_source_segment(source, node.annotation) or ""
                if "TypeAlias" not in annotation and not is_typings_scope:
                    return None
                value_node = value
            case ast.Assign(targets=[ast.Name() as target]):
                alias_name = target.id
                value_node = node.value
            case _:
                return None
        if not is_typings_scope and not any(
            token in alias_name.lower() for token in keys
        ):
            return None
        expr = ast.get_source_segment(source, value_node)
        if expr is None or not any(marker in expr for marker in dict_markers):
            return None
        return (alias_name, expr)

    @staticmethod
    def _is_dict_like_alias(
        node: ast.stmt,
        source: str,
        *,
        file_path: Path,
    ) -> m.Infra.AliasMove | None:
        posix = file_path.as_posix()
        is_typings_scope = (
            posix.endswith(("/typings.py", "/_typings.py")) or "/typings/" in posix
        )
        result = FlextInfraUtilitiesRefactorPydanticAnalysis._extract_alias_candidate(
            node,
            source,
            is_typings_scope=is_typings_scope,
        )
        if result is None:
            return None
        alias_name, expr = result
        return m.Infra.AliasMove(
            name=alias_name,
            start=node.lineno,
            end=node.end_lineno or node.lineno,
            alias_expr=expr,
        )

    @staticmethod
    def _typed_dict_factory_model(
        node: ast.Assign,
    ) -> m.Infra.ClassMove | None:
        extracted = (
            FlextInfraUtilitiesRefactorPydanticAnalysis._extract_typed_dict_call(
                node,
            )
        )
        if extracted is None:
            return None
        target_name, field_map, keywords = extracted
        total_false = any(
            kw.arg == "total"
            and isinstance(kw.value, ast.Constant)
            and kw.value.value is False
            for kw in keywords
        )
        rendered_class = (
            FlextInfraUtilitiesRefactorPydanticAnalysis._render_typed_dict_class(
                target_name,
                field_map,
                total_false=total_false,
            )
        )
        return m.Infra.ClassMove(
            name=target_name,
            start=node.lineno,
            end=node.end_lineno or node.lineno,
            source=rendered_class,
            kind="typed_dict_factory",
        )

    @staticmethod
    def _extract_typed_dict_call(
        node: ast.Assign,
    ) -> tuple[str, ast.Dict, Sequence[ast.keyword]] | None:
        """Extract (target_name, field_dict, keywords) from a TypedDict factory call."""
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            return None
        target = node.targets[0]
        if not isinstance(node.value, ast.Call):
            return None
        func = node.value.func
        is_td = (isinstance(func, ast.Name) and func.id == "TypedDict") or (
            isinstance(func, ast.Attribute) and func.attr == "TypedDict"
        )
        if not is_td:
            return None
        if (
            len(node.value.args)
            < FlextInfraUtilitiesRefactorPydanticAnalysis._PYDANTIC_TYPED_DICT_MIN_ARGS
        ):
            return None
        field_map_arg = node.value.args[1]
        if not isinstance(field_map_arg, ast.Dict):
            return None
        return (target.id, field_map_arg, node.value.keywords)

    @staticmethod
    def _render_typed_dict_class(
        name: str,
        field_map: ast.Dict,
        *,
        total_false: bool,
    ) -> str:
        """Render a BaseModel class from TypedDict factory fields."""
        field_lines: MutableSequence[str] = []
        for key_node, value_node in zip(
            field_map.keys,
            field_map.values,
            strict=True,
        ):
            if not isinstance(key_node, ast.Constant):
                continue
            key_value = key_node.value
            if not isinstance(key_value, str):
                continue
            ann = ast.unparse(value_node)
            line = (
                f"    {key_value}: Annotated[{ann} | None, Field(default=None)]"
                if total_false
                else f"    {key_value}: {ann}"
            )
            field_lines.append(
                line,
            )
        if not field_lines:
            field_lines.append("    pass")
        rendered_fields = "\n".join(field_lines)
        return (
            f"class {name}(BaseModel):\n"
            '    model_config = ConfigDict(extra="forbid")\n'
            f"{rendered_fields}\n"
        )

    @staticmethod
    def _typed_dict_total_false(node: ast.ClassDef) -> bool:
        for keyword in node.keywords:
            if keyword.arg == "total" and isinstance(keyword.value, ast.Constant):
                return bool(keyword.value.value) is False
        return False

    @staticmethod
    def _build_model_from_typed_dict(
        node: ast.ClassDef,
        source: str,
    ) -> str:
        total_false = (
            FlextInfraUtilitiesRefactorPydanticAnalysis._typed_dict_total_false(
                node,
            )
        )
        fields: MutableSequence[str] = []
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                ann = ast.get_source_segment(source, stmt.annotation)
                if ann is None:
                    continue
                if total_false:
                    fields.append(
                        f"    {stmt.target.id}: Annotated[{ann} | None, Field(default=None)]",
                    )
                else:
                    fields.append(f"    {stmt.target.id}: {ann}")
        if not fields:
            fields.append("    pass")
        body = "\n".join(fields)
        return f'class {node.name}(BaseModel):\n    model_config = ConfigDict(extra="forbid")\n{body}\n'

    @staticmethod
    def collect_moves(
        file_path: Path,
    ) -> t.Infra.Pair[Sequence[m.Infra.ClassMove], Sequence[m.Infra.AliasMove]]:
        """Collect class and alias moves required for centralization."""
        source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        tree = FlextInfraUtilitiesParsing.parse_ast_from_source(source)
        if tree is None:
            msg = "Failed to parse source"
            raise SyntaxError(msg)
        lines = source.splitlines()
        class_moves: MutableSequence[m.Infra.ClassMove] = []
        alias_moves: MutableSequence[m.Infra.AliasMove] = []
        for stmt in tree.body:
            typed_dict_factory_move = (
                FlextInfraUtilitiesRefactorPydanticAnalysis._typed_dict_factory_model(
                    stmt,
                )
                if isinstance(stmt, ast.Assign)
                else None
            )
            if typed_dict_factory_move is not None:
                class_moves.append(typed_dict_factory_move)
                continue
            if FlextInfraUtilitiesRefactorPydanticAnalysis.is_top_level_model_class(
                stmt,
            ):
                if not isinstance(stmt, ast.ClassDef):
                    continue
                start = stmt.lineno
                end = stmt.end_lineno or stmt.lineno
                snippet = "\n".join(lines[start - 1 : end])
                base_names = (
                    FlextInfraUtilitiesRefactorPydanticAnalysis._class_base_names(
                        stmt,
                    )
                )
                kind = "typed_dict" if "TypedDict" in base_names else "base_model"
                if kind == "typed_dict":
                    snippet = FlextInfraUtilitiesRefactorPydanticAnalysis._build_model_from_typed_dict(
                        stmt,
                        source,
                    )
                class_moves.append(
                    m.Infra.ClassMove(
                        name=stmt.name,
                        start=start,
                        end=end,
                        source=snippet,
                        kind=kind,
                    ),
                )
                continue
            alias_move = (
                FlextInfraUtilitiesRefactorPydanticAnalysis._is_dict_like_alias(
                    stmt,
                    source,
                    file_path=file_path,
                )
            )
            if alias_move is not None:
                alias_moves.append(alias_move)
        return (class_moves, alias_moves)

    @staticmethod
    def collect_moves_safe(
        file_path: Path,
        *,
        failure_stats: m.Infra.CentralizerFailureStats,
    ) -> t.Infra.Pair[Sequence[m.Infra.ClassMove], Sequence[m.Infra.AliasMove]] | None:
        """Collect moves without raising, while recording parse failures."""
        try:
            return FlextInfraUtilitiesRefactorPydanticAnalysis.collect_moves(
                file_path,
            )
        except SyntaxError:
            failure_stats.parse_syntax_errors += 1
            return None
        except UnicodeDecodeError:
            failure_stats.parse_encoding_errors += 1
            return None
        except OSError:
            failure_stats.parse_io_errors += 1
            return None

    @staticmethod
    def scan_file_violations(file_path: Path) -> t.Infra.IntPair:
        """Return counts of model and dict-alias violations in one file."""
        try:
            source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        except (UnicodeDecodeError, OSError):
            return (0, 0)
        tree = FlextInfraUtilitiesParsing.parse_ast_from_source(source)
        if tree is None:
            return (0, 0)
        model_class_count = 0
        dict_alias_count = 0
        for stmt in tree.body:
            if FlextInfraUtilitiesRefactorPydanticAnalysis.is_top_level_model_class(
                stmt,
            ):
                model_class_count += 1
                continue
            if (
                FlextInfraUtilitiesRefactorPydanticAnalysis._is_dict_like_alias(
                    stmt,
                    source,
                    file_path=file_path,
                )
                is not None
            ):
                dict_alias_count += 1
        return (model_class_count, dict_alias_count)

    @staticmethod
    def rewrite_source(
        file_path: Path,
        class_moves: Sequence[m.Infra.ClassMove],
        alias_moves: Sequence[m.Infra.AliasMove],
        *,
        import_statement: str,
    ) -> str:
        """Rewrite source after extracting moved classes and aliases."""
        source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        lines = source.splitlines()
        ranges = sorted(
            [(m.start, m.end) for m in class_moves]
            + [(a.start, a.end) for a in alias_moves],
            key=operator.itemgetter(0),
            reverse=True,
        )
        for start, end in ranges:
            del lines[start - 1 : end]
        updated = "\n".join(lines)
        moved_names = [m.name for m in class_moves] + [a.name for a in alias_moves]
        if moved_names:
            updated = FlextInfraUtilitiesParsing.insert_import_statement(
                updated,
                import_statement,
            )
        if source.endswith("\n") and (not updated.endswith("\n")):
            updated += "\n"
        return updated


__all__ = ["FlextInfraUtilitiesRefactorPydanticAnalysis"]
