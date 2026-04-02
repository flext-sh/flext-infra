"""Static analysis helpers for Pydantic centralization refactors.

Centralizes the ``FlextInfraRefactorPydanticCentralizerAnalysis`` logic
into the MRO utility chain.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import operator
from collections.abc import MutableSequence, Sequence
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
        "FrozenStrictModel",
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
    def is_top_level_model_class(node: object) -> bool:
        """Return True when statement is a top-level model-like class."""
        if node.__class__.__name__ != "ClassDef":
            return False

        base_names: t.Infra.StrSet = set()
        for base in getattr(node, "bases", []):
            bname = base.__class__.__name__
            if bname == "Name":
                base_names.add(getattr(base, "id", ""))
            elif bname == "Attribute":
                base_names.add(getattr(base, "attr", ""))
                # A quick unparse alternative for FlextModels.BaseModel etc
                root_id = getattr(getattr(base, "value", None), "id", "")
                if root_id:
                    base_names.add(f"{root_id}.{getattr(base, 'attr', '')}")

        model_bases = FlextInfraUtilitiesRefactorPydanticAnalysis._PYDANTIC_MODEL_BASES
        return any(
            bn in model_bases or bn.startswith("FlextModels.") for bn in base_names
        )

    @staticmethod
    def _is_dict_like_alias_regex(
        name: str, source: str, start: int, end: int, is_typings_scope: bool
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
        """Collect class and alias moves required for centralization."""
        source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        tree = FlextInfraUtilitiesRefactorPydanticAnalysis._get_ast_tree(
            source, file_path
        )
        if tree is None:
            msg = "Failed to parse source"
            raise SyntaxError(msg)

        lines = source.splitlines()
        class_moves: MutableSequence[m.Infra.ClassMove] = []
        alias_moves: MutableSequence[m.Infra.AliasMove] = []

        posix = file_path.as_posix()
        is_typings_scope = (
            posix.endswith(("/typings.py", "/_typings.py")) or "/typings/" in posix
        )

        for stmt in getattr(tree, "body", []):
            node_type = stmt.__class__.__name__
            start = getattr(stmt, "lineno", -1)
            end = getattr(stmt, "end_lineno", getattr(stmt, "lineno", start))
            if start == -1:
                continue

            if FlextInfraUtilitiesRefactorPydanticAnalysis.is_top_level_model_class(
                stmt
            ):
                name = getattr(stmt, "name", "")
                snippet = "\n".join(lines[start - 1 : end])
                # Check if it was a typeddict base
                kind = "base_model"
                for base in getattr(stmt, "bases", []):
                    if getattr(base, "id", "") == "TypedDict":
                        kind = "typed_dict"
                        break
                # Very simple naive conversion if TypedDict -> BaseModel
                if kind == "typed_dict":
                    fields: MutableSequence[str] = []
                    for s in getattr(stmt, "body", []):
                        if s.__class__.__name__ == "AnnAssign":
                            tgt = getattr(s, "target", None)
                            if tgt and tgt.__class__.__name__ == "Name":
                                fields.append(
                                    f"    {tgt.id}: Any"
                                )  # Simplified for now
                    body = "\n".join(fields) or "    pass"
                    snippet = f'class {name}(BaseModel):\n    model_config = ConfigDict(extra="forbid")\n{body}\n'

                class_moves.append(
                    m.Infra.ClassMove(
                        name=name, start=start, end=end, source=snippet, kind=kind
                    )
                )
                continue

            # Check typing aliases
            target_name = ""
            if node_type == "TypeAlias":
                target_name = getattr(getattr(stmt, "name", None), "id", "")
            elif node_type == "Assign":
                targets = getattr(stmt, "targets", [])
                if targets and targets[0].__class__.__name__ == "Name":
                    target_name = getattr(targets[0], "id", "")
            elif node_type == "AnnAssign":
                target = getattr(stmt, "target", None)
                if target and target.__class__.__name__ == "Name":
                    target_name = getattr(target, "id", "")

            if target_name:
                alias_move = FlextInfraUtilitiesRefactorPydanticAnalysis._is_dict_like_alias_regex(
                    target_name, source, start, end, is_typings_scope
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
