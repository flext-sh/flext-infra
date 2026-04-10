"""Static analysis helpers for Pydantic centralization refactors.

Centralizes the ``FlextInfraRefactorPydanticCentralizerAnalysis`` logic
into the MRO utility chain.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import operator
from collections.abc import Sequence
from pathlib import Path

from flext_infra import FlextInfraUtilitiesRope, c, m, t


class FlextInfraUtilitiesRefactorPydanticAnalysis:
    """Static analysis helpers for Pydantic centralization."""

    _PYDANTIC_MODEL_BASES: t.StrSequence = (
        "BaseModel",
        "RootModel",
        "TypedDict",
        "ArbitraryTypesModel",
        "FrozenModel",
        "ContractModel",
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
    def _is_dict_like_alias_regex(
        name: str,
        source: str,
        start: int,
        end: int,
        *,
        is_typings_scope: bool,
    ) -> m.Infra.AliasMove | None:
        if not is_typings_scope and not any(
            k in name.lower()
            for k in FlextInfraUtilitiesRefactorPydanticAnalysis._DICT_ALIAS_KEYS
        ):
            return None
        lines = source.splitlines()
        if start < 1 or end > len(lines):
            return None
        expr = "\n".join(lines[start - 1 : end])
        if not any(marker in expr for marker in ("Mapping[", "MutableMapping[")):
            return None
        alias_expr = expr.partition("=")[2].strip()
        if not alias_expr:
            return None

        return m.Infra.AliasMove(
            name=name,
            start=start,
            end=end,
            alias_expr=alias_expr,
        )

    @staticmethod
    def collect_moves(
        file_path: Path,
    ) -> t.Infra.Pair[Sequence[m.Infra.ClassMove], Sequence[m.Infra.AliasMove]]:
        """Scan a Python file for Pydantic model classes and dict-like aliases to centralize."""
        source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        lines = source.splitlines()
        with FlextInfraUtilitiesRope.open_project(file_path.parent) as rope_proj:
            resource = FlextInfraUtilitiesRope.get_resource_from_path(
                rope_proj, file_path
            )
            if resource is None:
                return ([], [])
            symbols = FlextInfraUtilitiesRope.get_module_symbols(rope_proj, resource)

        is_typings = file_path.name == "typings.py" or "_typings" in file_path.parts
        class_moves: list[m.Infra.ClassMove] = []
        alias_moves: list[m.Infra.AliasMove] = []
        pydantic_bases = (
            FlextInfraUtilitiesRefactorPydanticAnalysis._PYDANTIC_MODEL_BASES
        )

        for sym in sorted(symbols, key=operator.attrgetter("line")):
            if sym.kind == "class":
                # Check if this class inherits from a Pydantic base
                if sym.line < 1 or sym.line > len(lines):
                    continue
                class_line = lines[sym.line - 1]
                if any(base in class_line for base in pydantic_bases):
                    class_moves.append(
                        m.Infra.ClassMove(
                            name=sym.name,
                            start=sym.line,
                            end=sym.line,
                            source=class_line.strip(),
                            kind="model",
                        )
                    )
            elif sym.kind == "assignment":
                alias = FlextInfraUtilitiesRefactorPydanticAnalysis._is_dict_like_alias_regex(
                    sym.name,
                    source,
                    sym.line,
                    sym.line,
                    is_typings_scope=is_typings,
                )
                if alias is not None:
                    alias_moves.append(alias)

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
        except Exception as exc:
            if isinstance(exc, SyntaxError):
                failure_stats.parse_syntax_errors += 1
            elif isinstance(exc, UnicodeDecodeError):
                failure_stats.parse_encoding_errors += 1
            else:
                failure_stats.parse_io_errors += 1
            return None

    @staticmethod
    def insert_import_statements(
        source: str,
        import_statements: Sequence[str],
    ) -> str:
        """Insert missing imports after the top import block."""
        pending = [
            statement
            for statement in import_statements
            if statement and statement not in source
        ]
        if not pending:
            return source
        lines = source.splitlines()
        try:
            module = ast.parse(source)
        except SyntaxError:
            module = None
        body: list[ast.stmt] = list(module.body) if module is not None else []
        insertion_line = 0
        body_index = 0
        if body and isinstance(body[0], ast.Expr):
            value = getattr(body[0], "value", None)
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                insertion_line = body[0].end_lineno or 0
                body_index = 1
        while body_index < len(body):
            node = body[body_index]
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                break
            insertion_line = node.end_lineno or node.lineno
            body_index += 1
        before = lines[:insertion_line]
        after = lines[insertion_line:]
        block = list(pending)
        if before and before[-1].strip():
            block.insert(0, "")
        if after and after[0].strip():
            block.append("")
        return "\n".join([*before, *block, *after])

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
        if class_moves or alias_moves:
            updated = (
                FlextInfraUtilitiesRefactorPydanticAnalysis.insert_import_statements(
                    updated,
                    [import_statement],
                )
            )

        if source.endswith("\n") and (not updated.endswith("\n")):
            updated += "\n"
        return updated


__all__ = ["FlextInfraUtilitiesRefactorPydanticAnalysis"]
