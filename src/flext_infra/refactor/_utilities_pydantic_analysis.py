"""Static analysis helpers for Pydantic centralization refactors.

Centralizes the ``FlextInfraRefactorPydanticCentralizerAnalysis`` logic
into the MRO utility chain.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

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
    def _get_ast_tree(source: str, file_path: Path) -> object | None:
        try:
            rope_proj = FlextInfraUtilitiesRope.init_rope_project(file_path.parent)
            try:
                pycore = FlextInfraUtilitiesRope.get_pycore(rope_proj)
                return getattr(pycore, "get_string_module")(source).get_ast()
            finally:
                rope_proj.close()
        except Exception:
            return None

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

        return m.Infra.AliasMove(
            name=name,
            start=start,
            end=end,
            alias_expr=expr,
        )

    @staticmethod
    def collect_moves(
        file_path: Path,
    ) -> t.Infra.Pair[Sequence[m.Infra.ClassMove], Sequence[m.Infra.AliasMove]]:
        """Scan a Python file for Pydantic model classes and dict-like aliases to centralize."""
        source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        lines = source.splitlines()
        rope_proj = FlextInfraUtilitiesRope.init_rope_project(file_path.parent)
        try:
            resource = FlextInfraUtilitiesRope.get_resource_from_path(
                rope_proj, file_path
            )
            if resource is None:
                return ([], [])
            symbols = FlextInfraUtilitiesRope.get_module_symbols(rope_proj, resource)
        finally:
            rope_proj.close()

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
    def scan_file_violations(file_path: Path) -> t.Infra.IntPair:
        """Return counts of model and dict-alias violations in one file."""
        try:
            class_moves, alias_moves = (
                FlextInfraUtilitiesRefactorPydanticAnalysis.collect_moves(file_path)
            )
            return (len(class_moves), len(alias_moves))
        except Exception:
            return (0, 0)

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
            updated = import_statement + "\n" + updated

        if source.endswith("\n") and (not updated.endswith("\n")):
            updated += "\n"
        return updated


__all__ = ["FlextInfraUtilitiesRefactorPydanticAnalysis"]
