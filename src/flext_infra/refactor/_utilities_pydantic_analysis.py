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

import libcst as cst

from flext_infra import c, m, t
from flext_infra._utilities.parsing import FlextInfraUtilitiesParsing


class FlextInfraUtilitiesRefactorPydanticAnalysis:
    """Static analysis helpers for Pydantic centralization.

    Usage via namespace::

        from flext_infra import u

        violations = u.Infra.pydantic_scan_file_violations(path)
        moves = u.Infra.pydantic_collect_moves(path)
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
    def _pydantic_class_base_names(node: ast.ClassDef) -> t.Infra.StrSet:
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
    def _pydantic_is_model_like_base_name(base_name: str) -> bool:
        if (
            base_name
            in FlextInfraUtilitiesRefactorPydanticAnalysis._PYDANTIC_MODEL_BASES
        ):
            return True
        return bool(base_name.startswith("FlextModels."))

    @staticmethod
    def pydantic_is_top_level_model_class(node: ast.stmt) -> bool:
        """Return True when statement is a top-level model-like class."""
        if not isinstance(node, ast.ClassDef):
            return False
        base_names = (
            FlextInfraUtilitiesRefactorPydanticAnalysis._pydantic_class_base_names(
                node,
            )
        )
        return any(
            FlextInfraUtilitiesRefactorPydanticAnalysis._pydantic_is_model_like_base_name(
                base_name,
            )
            for base_name in base_names
        )

    @staticmethod
    def _pydantic_is_typings_scope(file_path: Path) -> bool:
        posix = file_path.as_posix()
        return posix.endswith(("/typings.py", "/_typings.py")) or "/typings/" in posix

    @staticmethod
    def _pydantic_is_dict_like_expr(expr: str) -> bool:
        return any(
            marker in expr for marker in ("Mapping[", "Mapping[", "MutableMapping[")
        )

    @staticmethod
    def _pydantic_is_dict_like_alias(
        node: ast.stmt,
        source: str,
        *,
        file_path: Path,
    ) -> m.Infra.AliasMove | None:
        keys = (
            "dict",
            "payload",
            "schema",
            "entry",
            "config",
            "metadata",
            "fixture",
            "case",
        )
        is_typings_scope = (
            FlextInfraUtilitiesRefactorPydanticAnalysis._pydantic_is_typings_scope(
                file_path,
            )
        )
        match node:
            case ast.TypeAlias():
                alias_name = node.name.id
                if (not is_typings_scope) and (
                    not any(token in alias_name.lower() for token in keys)
                ):
                    return None
                expr = ast.get_source_segment(source, node.value)
                if expr is None:
                    return None
                if not FlextInfraUtilitiesRefactorPydanticAnalysis._pydantic_is_dict_like_expr(
                    expr,
                ):
                    return None
                return m.Infra.AliasMove(
                    name=alias_name,
                    start=node.lineno,
                    end=node.end_lineno or node.lineno,
                    alias_expr=expr,
                )
            case ast.AnnAssign():
                if not isinstance(node.target, ast.Name):
                    return None
                alias_name = node.target.id
                if (not is_typings_scope) and (
                    not any(token in alias_name.lower() for token in keys)
                ):
                    return None
                if node.value is None:
                    return None
                expr = ast.get_source_segment(source, node.value)
                if expr is None:
                    return None
                if not FlextInfraUtilitiesRefactorPydanticAnalysis._pydantic_is_dict_like_expr(
                    expr,
                ):
                    return None
                annotation = ast.get_source_segment(source, node.annotation) or ""
                if ("TypeAlias" not in annotation) and (not is_typings_scope):
                    return None
                return m.Infra.AliasMove(
                    name=alias_name,
                    start=node.lineno,
                    end=node.end_lineno or node.lineno,
                    alias_expr=expr,
                )
            case ast.Assign():
                if len(node.targets) != 1:
                    return None
                if not isinstance(node.targets[0], ast.Name):
                    return None
                alias_name = node.targets[0].id
                if (not is_typings_scope) and (
                    not any(token in alias_name.lower() for token in keys)
                ):
                    return None
                expr = ast.get_source_segment(source, node.value)
                if expr is None:
                    return None
                if not FlextInfraUtilitiesRefactorPydanticAnalysis._pydantic_is_dict_like_expr(
                    expr,
                ):
                    return None
                return m.Infra.AliasMove(
                    name=alias_name,
                    start=node.lineno,
                    end=node.end_lineno or node.lineno,
                    alias_expr=expr,
                )
            case _:
                return None

    @staticmethod
    def _pydantic_typed_dict_factory_model(
        node: ast.Assign,
    ) -> m.Infra.ClassMove | None:
        if len(node.targets) != 1:
            return None
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            return None
        if not isinstance(node.value, ast.Call):
            return None
        func = node.value.func
        is_typed_dict_factory = False
        if isinstance(func, ast.Name):
            is_typed_dict_factory = func.id == "TypedDict"
        elif isinstance(func, ast.Attribute):
            is_typed_dict_factory = func.attr == "TypedDict"
        if not is_typed_dict_factory:
            return None
        if (
            len(node.value.args)
            < FlextInfraUtilitiesRefactorPydanticAnalysis._PYDANTIC_TYPED_DICT_MIN_ARGS
        ):
            return None
        field_map_arg = node.value.args[1]
        if not isinstance(field_map_arg, ast.Dict):
            return None
        field_lines: MutableSequence[str] = []
        total_false = False
        for kw in node.value.keywords:
            if (
                kw.arg == "total"
                and isinstance(kw.value, ast.Constant)
                and kw.value.value is False
            ):
                total_false = True
        for key_node, value_node in zip(
            field_map_arg.keys,
            field_map_arg.values,
            strict=True,
        ):
            if not isinstance(key_node, ast.Constant):
                continue
            key_value = key_node.value
            if not isinstance(key_value, str):
                continue
            annotation = ast.unparse(value_node)
            if total_false:
                field_lines.append(
                    f"    {key_value}: Annotated[{annotation} | None, Field(default=None)]",
                )
            else:
                field_lines.append(f"    {key_value}: {annotation}")
        if not field_lines:
            field_lines.append("    pass")
        rendered_fields = "\n".join(field_lines)
        rendered_class = (
            f"class {target.id}(BaseModel):\n"
            '    model_config = ConfigDict(extra="forbid")\n'
            f"{rendered_fields}\n"
        )
        return m.Infra.ClassMove(
            name=target.id,
            start=node.lineno,
            end=node.end_lineno or node.lineno,
            source=rendered_class,
            kind="typed_dict_factory",
        )

    @staticmethod
    def _pydantic_typed_dict_total_false(node: ast.ClassDef) -> bool:
        for keyword in node.keywords:
            if keyword.arg == "total" and isinstance(keyword.value, ast.Constant):
                return bool(keyword.value.value) is False
        return False

    @staticmethod
    def _pydantic_build_model_from_typed_dict(
        node: ast.ClassDef,
        source: str,
    ) -> str:
        total_false = FlextInfraUtilitiesRefactorPydanticAnalysis._pydantic_typed_dict_total_false(
            node,
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
    def pydantic_collect_moves(
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
                FlextInfraUtilitiesRefactorPydanticAnalysis._pydantic_typed_dict_factory_model(
                    stmt,
                )
                if isinstance(stmt, ast.Assign)
                else None
            )
            if typed_dict_factory_move is not None:
                class_moves.append(typed_dict_factory_move)
                continue
            if FlextInfraUtilitiesRefactorPydanticAnalysis.pydantic_is_top_level_model_class(
                stmt,
            ):
                if not isinstance(stmt, ast.ClassDef):
                    continue
                start = stmt.lineno
                end = stmt.end_lineno or stmt.lineno
                snippet = "\n".join(lines[start - 1 : end])
                base_names = FlextInfraUtilitiesRefactorPydanticAnalysis._pydantic_class_base_names(
                    stmt,
                )
                kind = "typed_dict" if "TypedDict" in base_names else "base_model"
                if kind == "typed_dict":
                    snippet = FlextInfraUtilitiesRefactorPydanticAnalysis._pydantic_build_model_from_typed_dict(
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
            alias_move = FlextInfraUtilitiesRefactorPydanticAnalysis._pydantic_is_dict_like_alias(
                stmt,
                source,
                file_path=file_path,
            )
            if alias_move is not None:
                alias_moves.append(alias_move)
        return (class_moves, alias_moves)

    @staticmethod
    def pydantic_collect_moves_safe(
        file_path: Path,
        *,
        failure_stats: m.Infra.CentralizerFailureStats,
    ) -> t.Infra.Pair[Sequence[m.Infra.ClassMove], Sequence[m.Infra.AliasMove]] | None:
        """Collect moves without raising, while recording parse failures."""
        try:
            return FlextInfraUtilitiesRefactorPydanticAnalysis.pydantic_collect_moves(
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
    def pydantic_scan_file_violations(file_path: Path) -> t.Infra.IntPair:
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
            if FlextInfraUtilitiesRefactorPydanticAnalysis.pydantic_is_top_level_model_class(
                stmt,
            ):
                model_class_count += 1
                continue
            if (
                FlextInfraUtilitiesRefactorPydanticAnalysis._pydantic_is_dict_like_alias(
                    stmt,
                    source,
                    file_path=file_path,
                )
                is not None
            ):
                dict_alias_count += 1
        return (model_class_count, dict_alias_count)

    @staticmethod
    def pydantic_rewrite_source(
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
            updated = (
                FlextInfraUtilitiesRefactorPydanticAnalysis._pydantic_insert_import(
                    updated,
                    import_statement,
                )
            )
        if source.endswith("\n") and (not updated.endswith("\n")):
            updated += "\n"
        return updated

    @staticmethod
    def _pydantic_insert_import(source: str, import_stmt: str) -> str:
        """Insert import statement preserving canonical ordering."""
        normalized = import_stmt.strip()
        if not normalized:
            return source
        module = FlextInfraUtilitiesParsing.parse_cst_from_source(source)
        if module is None:
            return source
        try:
            parsed = cst.parse_statement(f"{normalized}\n")
        except cst.ParserSyntaxError:
            return source
        if not isinstance(parsed, cst.SimpleStatementLine):
            return source
        for stmt in module.body:
            if not isinstance(stmt, cst.SimpleStatementLine):
                continue
            if cst.Module(body=[stmt]).code.strip() == normalized:
                return source
        insert_idx = 0
        for idx, stmt in enumerate(module.body):
            is_docstring = (
                isinstance(stmt, cst.SimpleStatementLine)
                and len(stmt.body) == 1
                and isinstance(stmt.body[0], cst.Expr)
                and isinstance(
                    stmt.body[0].value,
                    (cst.SimpleString, cst.ConcatenatedString),
                )
            )
            is_import = isinstance(stmt, cst.SimpleStatementLine) and any(
                isinstance(s, (cst.Import, cst.ImportFrom)) for s in stmt.body
            )
            is_future = False
            if isinstance(stmt, cst.SimpleStatementLine):
                for s in stmt.body:
                    if (
                        isinstance(s, cst.ImportFrom)
                        and isinstance(s.module, cst.Name)
                        and s.module.value == "__future__"
                    ):
                        is_future = True
            if is_docstring or is_future or is_import:
                insert_idx = idx + 1
                continue
            break
        new_body = [*module.body[:insert_idx], parsed, *module.body[insert_idx:]]
        return module.with_changes(body=new_body).code


__all__ = ["FlextInfraUtilitiesRefactorPydanticAnalysis"]
