"""Declarative intra-file duplicate statement extraction for ``make mod``.

The truthful jscpd report is the candidate detector; this phase is the semantic
authority. For a Python clone whose two sides are the SAME contiguous statement
sequence of the SAME module it hoists one helper that executes that sequence and
rewires every occurrence to a call, preserving evaluation order, assertions and
side effects exactly.

Safety precedes coverage. A candidate whose free variables cannot be
parameterized without changing behavior is skipped, never forced: ``yield``,
``nonlocal``/``global``, ``return``/``break``/``continue`` crossing the block
boundary, walrus, starred assignment targets, ``await``, zero-argument ``super``,
nested definitions, imports, and names bound inside the block but read outside it
all disqualify the candidate. A block whose local free variables have no
module-resolvable annotation cannot produce a typed helper and is skipped too.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import builtins
import hashlib
import operator
import textwrap
from collections.abc import Mapping, MutableMapping, Sequence
from pathlib import Path
from typing import ClassVar

from flext_infra import c, m, p, r, t, u
from flext_infra._utilities._rope import FlextInfraUtilitiesRopeAnalysis


class FlextInfraCodemodExtractDuplicate:
    """Hoist and rewire one safe intra-file duplicate statement block per file.

    The phase reads each governed project's truthful jscpd report, re-validates
    every reported range against the live source (so a stale report is a no-op),
    and publishes at most one extraction per file per loop iteration. The mod
    loop re-invokes the phase until the joint fixed point is reached, which makes
    the phase idempotent: once a block is extracted its report range no longer
    aligns to a statement boundary and the candidate disappears.
    """

    name: str = "extract-duplicates"

    _HELPER_PREFIX: ClassVar[str] = "_flext_extract_"
    _SUMMARY: ClassVar[str] = (
        "Execute the repeated statement block extracted by the mod loop."
    )
    _MEMBER_INDENT: ClassVar[str] = "    "
    _BODY_INDENT: ClassVar[str] = "        "
    _MIN_BLOCK_STATEMENTS: ClassVar[int] = 2
    _BUILTIN_NAMES: ClassVar[frozenset[str]] = frozenset(dir(builtins))

    @staticmethod
    def apply(
        root: Path,
        preflight: m.Infra.ModScanReport,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
    ) -> p.Result[bool]:
        """Extract one safe duplicate statement block per governed project file.

        Returns:
            The resulting ``p.Result[bool]`` — ``True`` marks changed sources.

        """
        del preflight, rope_workspace
        changed = False
        for project_root in u.Infra.governed_project_roots(root):
            planned = FlextInfraCodemodExtractDuplicate.plan_project(project_root)
            if planned.failure:
                return r[bool].from_failure(planned)
            for edit in planned.value:
                ok, report = u.Infra.protected_source_write(
                    edit.file_path,
                    request=m.Infra.ProtectedSourceWriteRequest(
                        workspace=project_root,
                        updated_source=edit.updated_source,
                        gates=(),
                    ),
                )
                if not ok:
                    return r[bool].fail(
                        "; ".join(report[:3]) or "protected write failed",
                    )
                changed = True
        return r[bool].ok(value=changed)

    @classmethod
    def plan_project(
        cls,
        project_root: Path,
    ) -> p.Result[tuple[m.Infra.SemanticMigrationEdit, ...]]:
        """Plan the first safe extraction per file from one project's report.

        Returns:
            One edit per changed file, or a failure when the report is malformed.

        """
        report_path = (
            project_root / c.Infra.JSCPD_REPORT_DIRNAME / c.Infra.JSCPD_REPORT_FILENAME
        )
        if not report_path.is_file():
            return r[tuple[m.Infra.SemanticMigrationEdit, ...]].ok(())
        loaded = u.Cli.json_parse(report_path.read_text(encoding=c.DEFAULT_ENCODING))
        if loaded.failure:
            return r[tuple[m.Infra.SemanticMigrationEdit, ...]].from_failure(
                loaded,
            )
        grouped = cls._intra_file_ranges(
            u.Cli.json_as_mapping(loaded.value),
            project_root,
        )
        edits: list[m.Infra.SemanticMigrationEdit] = []
        for path in sorted(grouped):
            edit = cls._plan_file(path, grouped[path])
            if edit is not None:
                edits.append(edit)
        return r[tuple[m.Infra.SemanticMigrationEdit, ...]].ok(tuple(edits))

    @classmethod
    def _intra_file_ranges(
        cls,
        data: t.JsonMapping,
        project_root: Path,
    ) -> MutableMapping[Path, list[tuple[int, int, int, int]]]:
        """Group Python intra-file clone ranges by their owned module path.

        Returns:
            The resulting mapping of module path to ``(first_start, first_end,
            second_start, second_end)`` line ranges.

        """
        grouped: MutableMapping[Path, list[tuple[int, int, int, int]]] = {}
        for duplicate in u.Cli.json_deep_mapping_list(data, "duplicates"):
            if u.Cli.json_pick_str(duplicate, "format") != "python":
                continue
            first = u.Cli.json_deep_mapping(duplicate, "firstFile")
            second = u.Cli.json_deep_mapping(duplicate, "secondFile")
            name = u.Cli.json_pick_str(first, "name")
            if name != u.Cli.json_pick_str(second, "name"):
                continue
            path = Path(name)
            if path.suffix != c.Infra.EXT_PYTHON or not path.is_relative_to(
                project_root,
            ):
                continue
            span = (
                u.Cli.json_nested_int(first, "startLoc", "line", default=0),
                u.Cli.json_nested_int(first, "endLoc", "line", default=0),
                u.Cli.json_nested_int(second, "startLoc", "line", default=0),
                u.Cli.json_nested_int(second, "endLoc", "line", default=0),
            )
            if not cls._valid_span(span):
                continue
            spans = grouped.setdefault(path, [])
            if span not in spans:
                spans.append(span)
        return grouped

    @staticmethod
    def _valid_span(span: tuple[int, int, int, int]) -> bool:
        """Return whether one reported clone span is a usable, disjoint range.

        Returns:
            Whether one reported clone span is a usable, disjoint range.

        """
        first_start, first_end, second_start, second_end = span
        if min(span) < 1:
            return False
        if first_end <= first_start or second_end <= second_start:
            return False
        return first_end < second_start or second_end < first_start

    @classmethod
    def _plan_file(
        cls,
        path: Path,
        spans: Sequence[tuple[int, int, int, int]],
    ) -> m.Infra.SemanticMigrationEdit | None:
        """Plan one extraction for a file, or ``None`` when it is not safe.

        Returns:
            The resulting ``m.Infra.SemanticMigrationEdit | None``.

        """
        if not path.is_file():
            return None
        source = path.read_text(encoding=c.DEFAULT_ENCODING)
        if source.startswith(c.Infra.AUTOGEN_HEADER):
            return None
        updated = cls.plan_source(source, spans)
        if updated is None or updated == source:
            return None
        return m.Infra.SemanticMigrationEdit(
            file_path=path.resolve(),
            original_source=source,
            updated_source=updated,
            changes=("extracted intra-file duplicate statement block",),
        )

    @classmethod
    def plan_source(
        cls,
        source: str,
        spans: Sequence[tuple[int, int, int, int]],
    ) -> str | None:
        """Return the source with the first safe extraction applied, if any.

        A reported span that no longer aligns to a full statement boundary on
        both sides is ignored, so a stale report never rewrites a live source.

        Returns:
            The rewritten source, or ``None`` when no reported span is safe.

        """
        tree = FlextInfraUtilitiesRopeAnalysis.Tree.parse_module_source(source)
        parents = u.Infra.ast_parent_map(tree)
        for span in spans:
            rewritten = cls._plan_span(source, tree, parents, span)
            if rewritten is not None:
                return rewritten
        return None

    @classmethod
    def _plan_span(
        cls,
        source: str,
        tree: t.Infra.AstModule,
        parents: Mapping[int, t.Infra.RopeAstNode],
        span: tuple[int, int, int, int],
    ) -> str | None:
        """Plan one extraction for a single reported clone span.

        Returns:
            The rewritten source, or ``None`` when the span is not safe.

        """
        first_start, first_end, second_start, second_end = span
        first_block = cls._statement_slice(tree, first_start, first_end)
        second_block = cls._statement_slice(tree, second_start, second_end)
        if first_block is None or second_block is None:
            return None
        if not cls._pair_matches(first_block, second_block):
            return None
        owner = cls._enclosing_class(parents, first_block[0])
        if (
            owner is None
            or owner is not cls._enclosing_class(parents, second_block[0])
            or not cls._class_is_module_level(parents, owner)
        ):
            return None
        bound = cls._block_bindings(first_block)
        if cls._bindings_escape(tree, first_block, bound):
            return None
        parameters = cls._free_parameters(tree, parents, first_block)
        if parameters is None:
            return None
        helper_name = cls._helper_name(tree, first_block)
        return cls._render(source, span, (owner, helper_name, parameters), first_block)

    @classmethod
    def _pair_matches(
        cls,
        first_block: Sequence[t.Infra.AstStatement],
        second_block: Sequence[t.Infra.AstStatement],
    ) -> bool:
        """Return whether two statement slices are one safe, repeatable block.

        Returns:
            Whether two statement slices are one safe, repeatable block.

        """
        if len(first_block) < cls._MIN_BLOCK_STATEMENTS:
            return False
        if cls._dump(first_block) != cls._dump(second_block):
            return False
        return cls._block_is_safe(first_block)

    # ------------------------------------------------------------------ scopes

    @staticmethod
    def _statement_slice(
        tree: t.Infra.AstModule,
        start: int,
        end: int,
    ) -> tuple[t.Infra.AstStatement, ...] | None:
        """Return the exact contiguous statement slice covering ``[start, end]``.

        Returns:
            The tightest matching statement tuple, or ``None``.

        """
        best: tuple[t.Infra.AstStatement, ...] | None = None
        for node in FlextInfraUtilitiesRopeAnalysis.walk_ast_nodes(tree):
            raw: Sequence[t.Infra.RopeAstNode] | None = getattr(node, "body", None)
            if not isinstance(raw, list) or not raw:
                continue
            statements = [
                child
                for child in raw
                if isinstance(child, FlextInfraUtilitiesRopeAnalysis.Tree.Statement)
            ]
            if len(statements) != len(raw):
                continue
            for index, first in enumerate(statements):
                if first.lineno != start:
                    continue
                for last_index in range(index, len(statements)):
                    if statements[last_index].end_lineno == end:
                        candidate = tuple(statements[index : last_index + 1])
                        if best is None or len(candidate) <= len(best):
                            best = candidate
                        break
        return best

    @classmethod
    def _dump(cls, block: Sequence[t.Infra.AstStatement]) -> str:
        """Return the statement list's canonical structural digest.

        Returns:
            The statement list's canonical structural digest.

        """
        return FlextInfraUtilitiesRopeAnalysis.Tree.dump(
            FlextInfraUtilitiesRopeAnalysis.Tree.Module(
                body=list(block), type_ignores=[]
            )
        )

    @classmethod
    def _block_is_safe(cls, block: Sequence[t.Infra.AstStatement]) -> bool:
        """Return whether the block survives extraction without behavior change.

        Returns:
            Whether the block survives extraction without behavior change.

        """
        unsafe = (
            FlextInfraUtilitiesRopeAnalysis.Tree.Return,
            FlextInfraUtilitiesRopeAnalysis.Tree.Yield,
            FlextInfraUtilitiesRopeAnalysis.Tree.YieldFrom,
            FlextInfraUtilitiesRopeAnalysis.Tree.Break,
            FlextInfraUtilitiesRopeAnalysis.Tree.Continue,
            FlextInfraUtilitiesRopeAnalysis.Tree.Nonlocal,
            FlextInfraUtilitiesRopeAnalysis.Tree.Global,
            FlextInfraUtilitiesRopeAnalysis.Tree.Await,
            FlextInfraUtilitiesRopeAnalysis.Tree.NamedExpr,
            FlextInfraUtilitiesRopeAnalysis.Tree.Import,
            FlextInfraUtilitiesRopeAnalysis.Tree.ImportFrom,
            FlextInfraUtilitiesRopeAnalysis.Tree.FunctionDef,
            FlextInfraUtilitiesRopeAnalysis.Tree.AsyncFunctionDef,
            FlextInfraUtilitiesRopeAnalysis.Tree.ClassDef,
            FlextInfraUtilitiesRopeAnalysis.Tree.Lambda,
        )
        for statement in block:
            for node in FlextInfraUtilitiesRopeAnalysis.walk_ast_nodes(statement):
                if isinstance(node, unsafe):
                    return False
                if isinstance(
                    node, FlextInfraUtilitiesRopeAnalysis.Tree.Starred
                ) and isinstance(node.ctx, FlextInfraUtilitiesRopeAnalysis.Tree.Store):
                    return False
                if (
                    isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Name)
                    and node.id == "__class__"
                ):
                    return False
                if (
                    isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Call)
                    and isinstance(node.func, FlextInfraUtilitiesRopeAnalysis.Tree.Name)
                    and node.func.id == "super"
                    and not node.args
                    and not node.keywords
                ):
                    return False
        return True

    @classmethod
    def _block_bindings(cls, block: Sequence[t.Infra.AstStatement]) -> frozenset[str]:
        """Return every name the block binds.

        Returns:
            Every name the block binds.

        """
        bound: set[str] = set()
        for statement in block:
            for node in FlextInfraUtilitiesRopeAnalysis.walk_ast_nodes(statement):
                if isinstance(
                    node, FlextInfraUtilitiesRopeAnalysis.Tree.Name
                ) and isinstance(node.ctx, FlextInfraUtilitiesRopeAnalysis.Tree.Store):
                    bound.add(node.id)
                elif isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Argument):
                    bound.add(node.arg)
                elif (
                    isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.ExceptHandler)
                    and node.name
                ):
                    bound.add(node.name)
                elif isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Alias):
                    bound.add((node.asname or node.name).split(".")[0])
        return frozenset(bound)

    @classmethod
    def _bindings_escape(
        cls,
        tree: t.Infra.AstModule,
        block: Sequence[t.Infra.AstStatement],
        bound: frozenset[str],
    ) -> bool:
        """Return whether any name the block binds is read outside the block.

        Returns:
            Whether any name the block binds is read outside the block.

        """
        if not bound:
            return False
        inside = {
            id(node)
            for statement in block
            for node in FlextInfraUtilitiesRopeAnalysis.walk_ast_nodes(statement)
        }
        return any(
            isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Name)
            and isinstance(node.ctx, FlextInfraUtilitiesRopeAnalysis.Tree.Load)
            and node.id in bound
            and id(node) not in inside
            for node in FlextInfraUtilitiesRopeAnalysis.walk_ast_nodes(tree)
        )

    @staticmethod
    def _enclosing_class(
        parents: Mapping[int, t.Infra.RopeAstNode],
        node: t.Infra.AstStatement,
    ) -> t.Infra.AstClassDefinition | None:
        """Return the innermost class enclosing ``node``, if any.

        Returns:
            The innermost class enclosing ``node``, if any.

        """
        current = parents.get(id(node))
        while current is not None:
            if isinstance(current, FlextInfraUtilitiesRopeAnalysis.Tree.ClassDef):
                return current
            current = parents.get(id(current))
        return None

    @classmethod
    def _class_is_module_level(
        cls,
        parents: Mapping[int, t.Infra.RopeAstNode],
        owner: t.Infra.AstClassDefinition,
    ) -> bool:
        """Return whether the class name resolves as a module global.

        A class nested inside a function or another class cannot be addressed by
        a bare name from a later call, so it is never a safe helper owner.

        Returns:
            Whether the class name resolves as a module global.

        """
        current = parents.get(id(owner))
        while current is not None:
            if isinstance(current, c.Infra.AST_DEFINITION_TYPES):
                return False
            current = parents.get(id(current))
        return True

    @classmethod
    def _enclosing_functions(
        cls,
        parents: Mapping[int, t.Infra.RopeAstNode],
        node: t.Infra.AstStatement,
    ) -> tuple[t.Infra.AstFunctionDefinition, ...]:
        """Return the enclosing functions of ``node``, innermost first.

        Returns:
            The enclosing functions of ``node``, innermost first.

        """
        chain: list[t.Infra.AstFunctionDefinition] = []
        current = parents.get(id(node))
        while current is not None:
            if isinstance(current, c.Infra.AST_FUNCTION_TYPES):
                chain.append(current)
            current = parents.get(id(current))
        return tuple(chain)

    @classmethod
    def _free_parameters(
        cls,
        tree: t.Infra.AstModule,
        parents: Mapping[int, t.Infra.RopeAstNode],
        block: Sequence[t.Infra.AstStatement],
    ) -> tuple[tuple[str, str], ...] | None:
        """Return the typed parameters the helper needs, or ``None`` if untypable.

        Only free variables local to an enclosing function become parameters: a
        module global stays resolvable from a module-level declaration and needs
        no argument.

        Returns:
            ``(name, annotation source)`` pairs, or ``None`` when a local free
            variable has no module-resolvable annotation.

        """
        loaded: set[str] = set()
        for statement in block:
            loaded.update(
                node.id
                for node in FlextInfraUtilitiesRopeAnalysis.walk_ast_nodes(statement)
                if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Name)
                and isinstance(node.ctx, FlextInfraUtilitiesRopeAnalysis.Tree.Load)
            )
        free = sorted(loaded - cls._block_bindings(block) - cls._BUILTIN_NAMES)
        chain = cls._enclosing_functions(parents, block[0])
        module_bound = cls._module_bindings(tree)
        parameters: list[tuple[str, str]] = []
        for name in free:
            locals_of = tuple(
                func for func in chain if name in cls._scope_bindings(func)
            )
            if not locals_of:
                continue
            annotation = cls._annotation_for(locals_of, name)
            if annotation is None or not cls._annotation_is_resolvable(
                annotation,
                module_bound,
            ):
                return None
            parameters.append((name, annotation))
        return tuple(parameters)

    # ------------------------------------------------------------------ naming

    @classmethod
    def _helper_name(
        cls,
        tree: t.Infra.AstModule,
        block: Sequence[t.Infra.AstStatement],
    ) -> str:
        """Return a deterministic helper name that is not already bound.

        Returns:
            A deterministic helper name that is not already bound.

        """
        digest = hashlib.sha256(cls._dump(block).encode()).hexdigest()
        used = {
            node.id
            for node in FlextInfraUtilitiesRopeAnalysis.walk_ast_nodes(tree)
            if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Name)
        }
        used.update(
            node.name
            for node in FlextInfraUtilitiesRopeAnalysis.walk_ast_nodes(tree)
            if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.FunctionDef)
        )
        for width in (10, 16, 32):
            candidate = f"{cls._HELPER_PREFIX}{digest[:width]}"
            if candidate not in used:
                return candidate
        return f"{cls._HELPER_PREFIX}{digest}"

    # ------------------------------------------------------------------ render

    @classmethod
    def _render(
        cls,
        source: str,
        span: tuple[int, int, int, int],
        plan: tuple[
            t.Infra.AstClassDefinition,
            str,
            tuple[tuple[str, str], ...],
        ],
        block: Sequence[t.Infra.AstStatement],
    ) -> str | None:
        """Render the helper and rewire both occurrences to a single call.

        Returns:
            The rewritten source, or ``None`` when the block needs re-indenting
            that would corrupt a multi-line literal.

        """
        owner, helper_name, parameters = plan
        first_start, first_end, second_start, second_end = span
        lines = source.splitlines(keepends=True)
        first_raw = lines[first_start - 1]
        indent = first_raw[: len(first_raw) - len(first_raw.lstrip())]
        if indent != cls._BODY_INDENT and cls._has_multiline_string(block):
            return None
        arguments = ", ".join(name for name, _annotation in parameters)
        helper_lines = cls._helper_lines(
            helper_name,
            parameters,
            "".join(lines[first_start - 1 : first_end]),
            indent,
        )
        edits: list[tuple[int, int, list[str]]] = [
            (
                first_start - 1,
                first_end,
                cls._call_lines(lines, first_start, owner, helper_name, arguments),
            ),
            (
                second_start - 1,
                second_end,
                cls._call_lines(lines, second_start, owner, helper_name, arguments),
            ),
            (
                cls._insertion_index(owner),
                cls._insertion_index(owner),
                helper_lines,
            ),
        ]
        for start, end, replacement in sorted(
            edits,
            key=operator.itemgetter(0),
            reverse=True,
        ):
            lines[start:end] = replacement
        rendered = "".join(lines)
        FlextInfraUtilitiesRopeAnalysis.Tree.parse_module_source(rendered)
        return rendered

    @staticmethod
    def _has_multiline_string(block: Sequence[t.Infra.AstStatement]) -> bool:
        """Return whether the block holds a multi-line string literal.

        Re-indenting a block whose indentation already matches the helper body
        is verbatim; any other block is dedented, which would corrupt a
        multi-line literal, so such a block is skipped instead.

        Returns:
            Whether the block holds a multi-line string literal.

        """
        return any(
            isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Constant)
            and isinstance(node.value, str)
            and "\n" in node.value
            for statement in block
            for node in FlextInfraUtilitiesRopeAnalysis.walk_ast_nodes(statement)
        )

    @staticmethod
    def _call_lines(
        lines: Sequence[str],
        start: int,
        owner: t.Infra.AstClassDefinition,
        helper_name: str,
        arguments: str,
    ) -> list[str]:
        """Return the single call line replacing one occurrence.

        Returns:
            The single call line replacing one occurrence.

        """
        raw = lines[start - 1]
        indent = raw[: len(raw) - len(raw.lstrip())]
        return [f"{indent}{owner.name}.{helper_name}({arguments})\n"]

    @classmethod
    def _helper_lines(
        cls,
        helper_name: str,
        parameters: tuple[tuple[str, str], ...],
        block_text: str,
        indent: str,
    ) -> list[str]:
        """Return the staticmethod declaration lines at class indentation.

        The block body keeps its original formatting when its indentation
        already equals the helper body's; otherwise it is dedented and re-indented
        (a multi-line literal already disqualified that case).

        Returns:
            The staticmethod declaration lines at class indentation.

        """
        base = cls._MEMBER_INDENT
        body = cls._BODY_INDENT
        lines: list[str] = [f"{base}@staticmethod\n"]
        if parameters:
            lines.append(f"{base}def {helper_name}(\n")
            lines.extend(
                f"{body}{name}: {annotation},\n" for name, annotation in parameters
            )
            lines.append(f"{base}) -> None:\n")
        else:
            lines.append(f"{base}def {helper_name}() -> None:\n")
        lines.append(f'{body}"""{cls._SUMMARY}"""\n')
        lines.extend(cls._body_lines(block_text, indent))
        lines.append("\n")
        return lines

    @classmethod
    def _body_lines(cls, block_text: str, indent: str) -> list[str]:
        """Return the helper body lines preserving the block's formatting.

        Returns:
            The helper body lines preserving the block's formatting.

        """
        if indent == cls._BODY_INDENT:
            return block_text.splitlines(keepends=True)
        dedented = textwrap.dedent(block_text)
        return [
            f"{cls._BODY_INDENT}{line}" if line.strip() else "\n"
            for line in dedented.splitlines(keepends=True)
        ]

    @classmethod
    def _insertion_index(cls, owner: t.Infra.AstClassDefinition) -> int:
        """Return the 0-based line index before the class body's first member.

        The helper is declared after the class docstring and before the first
        member, so it never separates a decorator from its definition.

        Returns:
            The 0-based insertion index.

        """
        members: list[t.Infra.AstStatement] = list(owner.body)
        if (
            members
            and isinstance(members[0], FlextInfraUtilitiesRopeAnalysis.Tree.Expr)
            and isinstance(
                members[0].value, FlextInfraUtilitiesRopeAnalysis.Tree.Constant
            )
            and isinstance(members[0].value.value, str)
        ):
            members = members[1:]
        if not members:
            return owner.end_lineno or owner.lineno
        first = members[0]
        decorators = (
            first.decorator_list
            if isinstance(first, c.Infra.AST_DEFINITION_TYPES)
            else ()
        )
        return min([first.lineno, *(item.lineno for item in decorators)]) - 1

    # ------------------------------------------------------------- scope facts

    @classmethod
    def _scope_bindings(
        cls,
        func: t.Infra.AstFunctionDefinition,
    ) -> frozenset[str]:
        """Return an over-approximation of one function's local bindings.

        Over-approximation is safe: a global misclassified as local becomes an
        extra parameter (still correct at the call site), never a missing one.

        Returns:
            The names bound anywhere inside the function.

        """
        bound: set[str] = {arg.arg for arg in cls._function_arguments(func)}
        for node in FlextInfraUtilitiesRopeAnalysis.walk_ast_nodes(func):
            if isinstance(
                node, FlextInfraUtilitiesRopeAnalysis.Tree.Name
            ) and isinstance(node.ctx, FlextInfraUtilitiesRopeAnalysis.Tree.Store):
                bound.add(node.id)
            elif isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Alias):
                bound.add((node.asname or node.name).split(".")[0])
            elif (
                isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.ExceptHandler)
                and node.name
            ):
                bound.add(node.name)
        return frozenset(bound)

    @staticmethod
    def _function_arguments(
        func: t.Infra.AstFunctionDefinition,
    ) -> tuple[t.Infra.AstFunctionArgument, ...]:
        """Return every parameter argument of a function.

        Returns:
            Every parameter argument of a function.

        """
        arguments = func.args
        return (
            *arguments.posonlyargs,
            *arguments.args,
            *arguments.kwonlyargs,
            *((arguments.vararg,) if arguments.vararg else ()),
            *((arguments.kwarg,) if arguments.kwarg else ()),
        )

    @classmethod
    def _annotation_for(
        cls,
        locals_of: Sequence[t.Infra.AstFunctionDefinition],
        name: str,
    ) -> str | None:
        """Return the source annotation binding ``name`` in the enclosing chain.

        Returns:
            The source annotation binding ``name``, or ``None``.

        """
        for func in locals_of:
            for arg in cls._function_arguments(func):
                if arg.arg == name and arg.annotation is not None:
                    return FlextInfraUtilitiesRopeAnalysis.Tree.unparse(arg.annotation)
            for node in FlextInfraUtilitiesRopeAnalysis.walk_ast_nodes(func):
                if (
                    isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.AnnAssign)
                    and isinstance(
                        node.target, FlextInfraUtilitiesRopeAnalysis.Tree.Name
                    )
                    and node.target.id == name
                ):
                    return FlextInfraUtilitiesRopeAnalysis.Tree.unparse(node.annotation)
        return None

    @classmethod
    def _annotation_is_resolvable(
        cls,
        annotation: str,
        module_bound: frozenset[str],
    ) -> bool:
        """Return whether every name in an annotation resolves at module scope.

        Returns:
            Whether every name in an annotation resolves at module scope.

        """
        parsed = FlextInfraUtilitiesRopeAnalysis.Tree.parse_expression_source(
            annotation
        )
        return all(
            node.id in module_bound or node.id in cls._BUILTIN_NAMES
            for node in FlextInfraUtilitiesRopeAnalysis.walk_ast_nodes(parsed)
            if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Name)
        )

    @classmethod
    def _module_bindings(cls, tree: t.Infra.AstModule) -> frozenset[str]:
        """Return the names bound at the module's top-level scope.

        Returns:
            The names bound at the module's top-level scope.

        """
        bound: set[str] = set()
        cls._collect_module_bindings(tree.body, bound)
        return frozenset(bound)

    @classmethod
    def _collect_module_bindings(
        cls,
        statements: Sequence[t.Infra.AstStatement],
        bound: set[str],
    ) -> None:
        """Accumulate top-level bindings without descending into definitions."""
        for statement in statements:
            if isinstance(statement, c.Infra.AST_DEFINITION_TYPES):
                bound.add(statement.name)
                continue
            if isinstance(statement, c.Infra.AST_IMPORT_TYPES):
                bound.update(
                    (alias.asname or alias.name).split(".")[0]
                    for alias in statement.names
                )
                continue
            bound.update(cls._statement_targets(statement))
            for body in cls._nested_bodies(statement):
                cls._collect_module_bindings(body, bound)

    @staticmethod
    def _nested_bodies(
        statement: t.Infra.AstStatement,
    ) -> Sequence[tuple[t.Infra.AstStatement, ...]]:
        """Return the nested statement bodies owned by one compound statement.

        Returns:
            The nested statement bodies owned by one compound statement.

        """
        bodies: list[tuple[t.Infra.AstStatement, ...]] = []
        for child in FlextInfraUtilitiesRopeAnalysis.Tree.child_nodes(statement):
            raw: Sequence[t.Infra.RopeAstNode] | None = getattr(child, "body", None)
            if not isinstance(raw, list) or not raw:
                continue
            candidate = tuple(
                item
                for item in raw
                if isinstance(item, FlextInfraUtilitiesRopeAnalysis.Tree.Statement)
            )
            if len(candidate) != len(raw):
                continue
            bodies.append(candidate)
        return tuple(bodies)

    @staticmethod
    def _statement_targets(statement: t.Infra.AstStatement) -> Sequence[str]:
        """Return names bound by one statement's own (non-nested) targets.

        Returns:
            Names bound by one statement's own targets.

        """
        targets: list[t.Infra.RopeAstNode] = []
        if isinstance(statement, FlextInfraUtilitiesRopeAnalysis.Tree.Assign):
            targets = list(statement.targets)
        elif isinstance(
            statement,
            (
                FlextInfraUtilitiesRopeAnalysis.Tree.AnnAssign,
                FlextInfraUtilitiesRopeAnalysis.Tree.AugAssign,
                FlextInfraUtilitiesRopeAnalysis.Tree.For,
                FlextInfraUtilitiesRopeAnalysis.Tree.AsyncFor,
            ),
        ):
            targets = [statement.target]
        elif isinstance(statement, c.Infra.AST_WITH_TYPES):
            targets = [
                item.optional_vars
                for item in statement.items
                if item.optional_vars is not None
            ]
        names: list[str] = []
        for target in targets:
            names.extend(
                node.id
                for node in FlextInfraUtilitiesRopeAnalysis.walk_ast_nodes(target)
                if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Name)
            )
        return tuple(names)


__all__: list[str] = ["FlextInfraCodemodExtractDuplicate"]
