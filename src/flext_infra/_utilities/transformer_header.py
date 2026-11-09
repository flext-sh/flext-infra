"""Canonical Python module header analysis and import injection.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import operator
from collections.abc import MutableSequence

from flext_infra import c
from flext_infra._utilities import FlextInfraUtilitiesTransformerHeaderParser
from flext_infra._utilities._rope import FlextInfraUtilitiesRopeAnalysis
from flext_infra.protocols_bootstrap import annotation_reference_only


class FlextInfraUtilitiesTransformerHeader(FlextInfraUtilitiesTransformerHeaderParser):
    """Inject canonical aliases only when the source actually uses them."""

    @classmethod
    def ensure_future_annotations(cls, source: str) -> str:
        """Return source with exactly one correctly positioned future import.

        Returns:
            Source with exactly one correctly positioned future import.

        """
        module = ast.parse(source)
        imports = [
            node
            for node in ast.walk(module)
            if isinstance(node, ast.ImportFrom)
            and node.module == "__future__"
            and any(alias.name == "annotations" for alias in node.names)
        ]
        if len(imports) == 1:
            header = (
                module.body[1:]
                if ast.get_docstring(module) is not None
                else module.body
            )
            for node in header:
                if not isinstance(node, ast.ImportFrom) or node.module != "__future__":
                    break
                if node is imports[0]:
                    return source
        normalized = cls._remove_future_annotations_lines(source)
        body = normalized.splitlines(keepends=True)
        info = cls._parse_header(normalized)
        offset = max(
            info.span.shebang_end,
            info.span.encoding_end,
            info.span.comments_end,
            info.span.docstring_end,
        )
        line_index = normalized[:offset].count("\n")
        future_line = f"{c.Infra.FUTURE_ANNOTATIONS}\n"
        if info.span.docstring_end:
            while line_index < len(body) and not body[line_index].strip():
                del body[line_index]
            insert_lines = ["\n", future_line]
            if line_index < len(body):
                insert_lines.append("\n")
            body[line_index:line_index] = insert_lines
        else:
            body.insert(line_index, future_line)
        return "".join(body)

    @classmethod
    def ensure_alias_import(
        cls,
        source: str,
        module: str | None,
        alias: str,
        *,
        runtime_required: bool = False,
    ) -> str:
        """Bind one used import with its required runtime availability.

        ``module=None`` retains the native ``import`` form; other values name
        the ``from`` provider. ``alias`` is one native import item, including
        its optional declared ``as`` binding.

        Returns:
            Source with the required runtime or deferred import.

        Raises:
            ValueError: The declaration is not one explicit import binding.

        """
        if not alias:
            msg = "canonical import alias must be non-empty"
            raise ValueError(msg)
        statement = (
            f"from {module} import {alias}" if module is not None else f"import {alias}"
        )
        declaration = ast.parse(statement).body
        if (
            len(declaration) != 1
            or not isinstance(declaration[0], c.Infra.AST_IMPORT_TYPES)
            or len(declaration[0].names) != 1
            or declaration[0].names[0].name == "*"
        ):
            msg = "canonical import requires one explicit binding"
            raise ValueError(msg)
        imported = declaration[0].names[0]
        alias = imported.asname or imported.name.partition(".")[0]
        statement = ast.unparse(declaration[0])
        if not cls.alias_used(source, alias):
            return source
        if cls.has_alias_import(source, alias):
            deferred = (
                not runtime_required
                and "from __future__ import annotations" in source
                and cls._alias_is_annotation_only(source, alias)
            )
            if cls.has_runtime_alias_import(source, alias) or deferred:
                return source
            # A use outside annotations is a runtime requirement the source
            # itself proves; the deferred binding is promoted to runtime.
            source = cls._promote_deferred_alias_import(source, alias)
        if cls.alias_locally_bound(source, alias):
            return source
        if not runtime_required:
            typed = cls._alias_import_under_type_checking(source, statement, alias)
            if typed is not None:
                return typed
        info = cls._parse_header(source)
        offset = info.span.last_import_end or max(
            info.span.shebang_end,
            info.span.encoding_end,
            info.span.comments_end,
            info.span.docstring_end,
        )
        line = f"{statement}\n"
        if offset < len(source) and not source[offset:].startswith("\n"):
            line = f"{line}\n"
        return f"{source[:offset]}{line}{source[offset:]}"

    @staticmethod
    def _promote_deferred_alias_import(source: str, alias: str) -> str:
        """Drop the ``if TYPE_CHECKING:`` binding of an alias that now needs runtime.

        A generated holder that composes a sibling class by MRO needs the base at
        runtime, while an earlier annotation-only read placed the same import in
        the type-checking block. The runtime binding supersedes the deferred one,
        so the deferred binding is removed (and an emptied block with it) before
        the runtime import is injected; keeping both would bind the alias twice.

        Returns:
            The source without any deferred binding of ``alias``.

        """
        module = ast.parse(source)
        lines = source.splitlines(keepends=True)
        edits: MutableSequence[tuple[int, int, str]] = []
        for node in module.body:
            if not (
                isinstance(node, ast.If)
                and (
                    (
                        isinstance(node.test, ast.Name)
                        and node.test.id == "TYPE_CHECKING"
                    )
                    or (
                        isinstance(node.test, ast.Attribute)
                        and node.test.attr == "TYPE_CHECKING"
                    )
                )
            ):
                continue
            kept = 0
            block: MutableSequence[tuple[int, int, str]] = []
            for child in node.body:
                if not isinstance(child, c.Infra.AST_IMPORT_TYPES) or not any(
                    (name.asname or name.name.partition(".")[0]) == alias
                    for name in child.names
                ):
                    kept += 1
                    continue
                rest = [
                    name
                    for name in child.names
                    if (name.asname or name.name.partition(".")[0]) != alias
                ]
                end = child.end_lineno or child.lineno
                if rest:
                    kept += 1
                    child.names = rest
                    indent = lines[child.lineno - 1][
                        : len(lines[child.lineno - 1])
                        - len(lines[child.lineno - 1].lstrip())
                    ]
                    block.append((child.lineno, end, f"{indent}{ast.unparse(child)}\n"))
                else:
                    block.append((child.lineno, end, ""))
            if kept:
                edits.extend(block)
            elif block:
                edits.append((node.lineno, node.end_lineno or node.lineno, ""))
        for start, end, text in sorted(edits, reverse=True):
            lines[start - 1 : end] = [text] if text else []
        return "".join(lines)

    @staticmethod
    def has_runtime_alias_import(source: str, alias: str | None = None) -> bool:
        """Prove one or any canonical facade alias in the runtime import header.

        Returns:
            The resulting ``bool``.

        """
        module = ast.parse(source)
        header = (
            module.body[1:] if ast.get_docstring(module) is not None else module.body
        )
        expected = (
            frozenset({alias}) if alias is not None else c.FAMILY_CANONICAL_ALIASES
        )
        for node in header:
            if isinstance(node, ast.If) and (
                (isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING")
                or (
                    isinstance(node.test, ast.Attribute)
                    and node.test.attr == "TYPE_CHECKING"
                )
            ):
                continue
            if not isinstance(node, c.Infra.AST_IMPORT_TYPES):
                return False
            if any(
                (name.asname or name.name.partition(".")[0]) in expected
                for name in node.names
            ):
                return True
        return False

    @classmethod
    def _alias_import_under_type_checking(
        cls,
        source: str,
        statement: str,
        alias: str,
    ) -> str | None:
        """Place an annotation-only facade import inside ``if TYPE_CHECKING:``.

        A module that the package imports while initialising itself cannot
        import that same package at runtime: injecting the facade at module
        level made ``__version__.py`` raise ImportError on a partially
        initialised ``flext_infra``. With deferred annotations the alias is only
        ever read by a type checker, so the import belongs in the type-checking
        block, which is also what the facade law prescribes. Returns None when
        the module has no such block to extend.

        Returns:
            The resulting ``str | None``.

        """
        if "from __future__ import annotations" not in source:
            return None
        if not cls._alias_is_annotation_only(source, alias):
            return None
        lines = source.splitlines(keepends=True)
        for index, line in enumerate(lines):
            if line.rstrip() != "if TYPE_CHECKING:":
                continue
            following = lines[index + 1 :]
            indent = next(
                (
                    item[: len(item) - len(item.lstrip())]
                    for item in following
                    if item.strip()
                ),
                "    ",
            )
            lines.insert(index + 1, f"{indent}{statement}\n")
            return "".join(lines)
        return cls._create_type_checking_block(source, statement)

    @classmethod
    def _create_type_checking_block(cls, source: str, statement: str) -> str:
        """Create the type-checking block an annotation-only import needs.

        Without a block to extend, the injector fell through to a module-level
        import, which is exactly what breaks a module the package imports while
        initialising itself: ``__version__.py`` then raised
        ImportError on a partially initialised package. Deferred annotations
        make the alias a type-checker-only read, so the block is the correct
        destination and the facade law prescribes it.

        Returns:
            The resulting ``str``.

        """
        info = cls._parse_header(source)
        offset = info.span.last_import_end or max(
            info.span.shebang_end,
            info.span.encoding_end,
            info.span.comments_end,
            info.span.docstring_end,
        )
        prefix = source[:offset]
        if prefix and not prefix.endswith("\n"):
            prefix = f"{prefix}\n"
        if not prefix.endswith("\n\n"):
            prefix = f"{prefix}\n"
        guard = ""
        if not cls._imports_type_checking(source):
            guard = "from typing import TYPE_CHECKING\n\n"
        block = f"if TYPE_CHECKING:\n    {statement}\n"
        return f"{prefix}{guard}{block}{source[offset:]}"

    @staticmethod
    def _imports_type_checking(source: str) -> bool:
        """Return whether the module already imports ``TYPE_CHECKING``.

        Returns:
            Whether the module already imports ``TYPE_CHECKING``.

        """
        module = ast.parse(source)
        for node in ast.walk(module):
            if not isinstance(node, ast.ImportFrom) or node.module != "typing":
                continue
            if any(entry.name == "TYPE_CHECKING" for entry in node.names):
                return True
        return False

    @classmethod
    def bind_sibling_letters(cls, source: str) -> str:
        """Bind each used but unbound facade letter from its siblings' provider.

        A rewrite that introduces a family letter (``p.X`` beside an existing
        ``m.X``) reads it from the module-level provider that binds most of the
        module's other letters; a tie or no provider leaves the source to the
        lint delta gate.

        Returns:
            Source with every resolvable missing letter imported at runtime.

        """
        letters = {family.value for family in c.Infra.FacadeFamily}
        tree = ast.parse(source)
        counts: dict[str, int] = {}
        for node in tree.body:
            if (
                isinstance(node, ast.ImportFrom)
                and node.module is not None
                and node.level == 0
            ):
                bound = sum(
                    alias.name in letters and alias.asname is None
                    for alias in node.names
                )
                if bound:
                    counts[node.module] = counts.get(node.module, 0) + bound
        ranked = sorted(counts.items(), key=operator.itemgetter(1), reverse=True)
        provider = cls._mirror_provider(tree.body, ranked)
        if provider is None:
            return source
        for letter in sorted(letters):
            if (
                cls.alias_used(source, letter)
                and not cls.has_alias_import(source, letter)
                and not cls.alias_locally_bound(source, letter)
            ):
                source = cls.ensure_alias_import(
                    source, provider, letter, runtime_required=True
                )
        return source

    @staticmethod
    def _mirror_provider(
        body: list[ast.stmt],
        ranked: list[tuple[str, int]],
    ) -> str | None:
        """Select the provider an introduced mirror letter binds from.

        An introduced mirror follows the model provider when available.
        An ambiguous ranked-count tie does not select a provider.

        Returns:
            The resulting ``str | None``.

        """

        def provider_of(letter: str) -> str | None:
            """Return the module-level provider binding ``letter``, if any.

            Returns:
                The resulting ``str | None``.

            """
            return next(
                (
                    node.module
                    for node in body
                    if isinstance(node, ast.ImportFrom)
                    and node.module is not None
                    and node.level == 0
                    and any(
                        alias.name == letter and alias.asname is None
                        for alias in node.names
                    )
                ),
                None,
            )

        model_provider = provider_of(c.Infra.FacadeFamily.M.value)
        if model_provider is not None:
            return model_provider
        if not ranked:
            return None
        if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
            return None
        return ranked[0][0]

    @staticmethod
    def alias_used(source: str, alias: str) -> bool:
        """Return whether a loaded name or quoted dotted reference uses ``alias``.

        Returns:
            Whether a loaded name or quoted dotted reference uses ``alias``.

        """
        return any(
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and node.id == alias
            for node in ast.walk(ast.parse(source))
        ) or (
            c.Infra.compile(rf"\b{c.Infra.escape(alias)}\.(?![0-9])").search(source)
            is not None
        )

    @classmethod
    def has_alias_import(cls, source: str, alias: str) -> bool:
        """Return whether ``alias`` is already bound by a ``from`` import.

        Module-level bindings count, including ``if TYPE_CHECKING:``. The
        header scan stops at the first non-header statement, so an alias
        imported in that block read as absent and a duplicate was injected
        next to it. This proves a lexical declaration only; callers requiring
        runtime availability use ``has_runtime_alias_import``. Source that does
        not parse raises its ``SyntaxError``.

        Returns:
            Whether ``alias`` is already bound by a ``from`` import.

        """
        pending: list[ast.AST] = [ast.parse(source)]
        while pending:
            node = pending.pop()
            if isinstance(node, c.Infra.AST_DEFINITION_TYPES):
                continue
            if isinstance(node, c.Infra.AST_IMPORT_TYPES) and any(
                (name.asname or name.name.partition(".")[0]) == alias
                for name in node.names
            ):
                return True
            pending.extend(ast.iter_child_nodes(node))
        return False

    @staticmethod
    def _runtime_model_annotation_ids(module: ast.Module) -> frozenset[int]:
        """Return ids of class-body annotations a model resolves at runtime.

        A pydantic model evaluates its field annotations while the class is
        built, so an alias used there is a runtime dependency even though the
        syntax is an annotation. Deferring such an alias under
        ``if TYPE_CHECKING:`` made ``_SmellData.model_validate_json`` raise
        ``PydanticUserError`` during package import.

        Returns:
            Ids of class-body annotations a model resolves at runtime.

        """
        parents = FlextInfraUtilitiesRopeAnalysis.ast_parent_map(module)
        runtime_ids: set[int] = set()
        for node in ast.walk(module):
            if not isinstance(node, ast.AnnAssign):
                continue
            owner = parents.get(id(node))
            if not isinstance(owner, ast.ClassDef):
                continue
            if any(
                (isinstance(base, ast.Name) and base.id == "Protocol")
                or (isinstance(base, ast.Attribute) and base.attr == "Protocol")
                for base in owner.bases
            ):
                continue
            if not any(
                (isinstance(base, ast.Name) and base.id in c.Infra.RUNTIME_MODEL_BASES)
                or (
                    isinstance(base, ast.Attribute)
                    and base.attr in c.Infra.RUNTIME_MODEL_BASES
                )
                for base in owner.bases
            ):
                continue
            runtime_ids.add(id(node.annotation))
        return frozenset(runtime_ids)

    @classmethod
    def _alias_is_annotation_only(cls, source: str, alias: str) -> bool:
        """Report whether every use of ``alias`` is a deferred type reference.

        Class-body annotations on a runtime model are excluded from that set:
        the model resolves them at import time, so the alias must stay
        importable at runtime. Class bases and decorators are evaluated during
        class creation and remain runtime reads, including ``Protocol`` bases.

        Returns:
            The resulting ``bool``.

        """
        module = ast.parse(source)
        return annotation_reference_only(
            module, alias, cls._runtime_model_annotation_ids(module)
        )

    @staticmethod
    def alias_locally_bound(source: str, alias: str) -> bool:
        """Return whether a module-level definition or assignment owns an alias.

        Returns:
            Whether a module-level definition or assignment owns an alias.

        """
        escaped = c.Infra.escape(alias)
        pattern = c.Infra.compile(
            rf"^(?:{escaped}\s*(?::[^=\n]+)?=(?!=)|(?:class|def)\s+{escaped}\b)",
            multiline=True,
        )
        return pattern.search(source) is not None

    @staticmethod
    def _remove_future_annotations_lines(source: str) -> str:
        """Strip every ``from __future__ import annotations`` line.

        Returns:
            The resulting ``str``.

        """
        return "".join(
            line
            for line in source.splitlines(keepends=True)
            if line.strip() != c.Infra.FUTURE_ANNOTATIONS
        )


__all__: MutableSequence[str] = ["FlextInfraUtilitiesTransformerHeader"]
