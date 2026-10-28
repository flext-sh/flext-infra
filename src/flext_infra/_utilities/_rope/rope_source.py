"""Source-level Rope rewrite helpers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import textwrap
from collections.abc import MutableSequence, Sequence
from operator import itemgetter
from pathlib import Path

from flext_infra import c, p, t
from flext_infra._utilities import FlextInfraUtilitiesDiscovery
from flext_infra._utilities._rope.rope_runtime import FlextInfraUtilitiesRopeRuntime


class FlextInfraUtilitiesRopeSource:
    """Text-oriented helpers shared by Rope-backed refactors."""

    @classmethod
    def settings_branch_fields(
        cls,
        source_project: p.Infra.RopeProject,
        source_files: Sequence[Path],
        wanted: frozenset[str],
    ) -> frozenset[str]:
        """Authenticate immediate annotated settings fields through native identity.

        The invocation supplies its elected files and original project. Rope's
        class graph elects the settings owners; its semantic matcher and binding
        index distinguish direct declarations from conditional suite bindings.

        Returns:
            Requested names declared directly on genuine settings/config classes.

        Raises:
            TypeError: A canonical owner or indexed source violates its contract.

        """
        if not wanted:
            return frozenset()
        runtime = FlextInfraUtilitiesRopeRuntime
        roots = cls._settings_owner_roots(source_project)
        proven: set[str] = set()
        for path in source_files:
            module = source_project.get_pymodule(
                runtime.file_resource_at(source_project, path), force_errors=True
            )
            if not runtime.source_module(module):
                msg = f"Settings field inventory is not a native source module: {path}"
                raise TypeError(msg)
            proven.update(
                cls._direct_settings_fields(module, scope, wanted)
                for scope in cls._class_scopes(module)
                if wanted.intersection(scope.get_defined_names())
                and cls._settings_owner(scope.pyobject, roots)
            )
        return frozenset(proven)

    @classmethod
    def _settings_owner_roots(
        cls,
        source_project: p.Infra.RopeProject,
    ) -> list[p.Infra.RopeSourceClass]:
        """Authenticate the canonical settings owner classes in flext-core.

        Returns:
            The native settings and config owner classes.

        Raises:
            TypeError: A canonical owner violates its native class contract.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        roots: list[p.Infra.RopeSourceClass] = []
        for module_name, name in (
            ("flext_core._settings", "FlextSettings"),
            ("flext_core._config", "FlextConfig"),
        ):
            module = source_project.get_module(module_name)
            if not runtime.source_module(module):
                msg = f"Native settings module is not a source module: {module_name}"
                raise TypeError(msg)
            owner = module.get_attribute(name).get_object()
            if not runtime.py_class(owner):
                msg = (
                    f"Native settings owner is not a source class: {module_name}.{name}"
                )
                raise TypeError(msg)
            roots.append(owner)
        return roots

    @staticmethod
    def _class_scopes(module: p.Infra.RopePyModule) -> list[p.Infra.RopeScope]:
        """Collect every class scope of one module.

        Returns:
            The module's class scopes.

        """
        scopes: list[p.Infra.RopeScope] = []
        pending: list[p.Infra.RopeScope] = [module.get_scope()]
        while pending:
            scope = pending.pop()
            pending.extend(scope.get_scopes())
            if scope.get_kind() == "Class":
                scopes.append(scope)
        return scopes

    @staticmethod
    def _settings_owner(
        candidate: p.Infra.RopePyObject,
        roots: Sequence[p.Infra.RopeSourceClass],
    ) -> bool:
        """Follow Rope's original superclass identities without spelling rules.

        Returns:
            The resulting ``bool``.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        pending = [candidate]
        visited: set[int] = set()
        while pending:
            owner = pending.pop()
            if any(owner is root for root in roots):
                return True
            if id(owner) in visited:
                continue
            visited.add(id(owner))
            if runtime.abstract_class(owner):
                pending.extend(owner.get_superclasses())
        return False

    @staticmethod
    def _direct_settings_fields(
        module: p.Infra.RopeSourceModule,
        scope: p.Infra.RopeScope,
        wanted: frozenset[str],
    ) -> frozenset[str]:
        """Query whole native annotated declarations at class-body depth.

        Returns:
            The resulting ``frozenset[str]``.

        Raises:
            TypeError: If Settings field query requires the native word finder contract.
            ValueError: If Native settings class has no unique indexed declaration.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        index = module.get_source_binding_index()
        finder = runtime.runtime_callable("rope.base.worder", "Worder")(
            module.source_code
        )
        if not isinstance(finder, p.Infra.RopeWorder):
            msg = "Settings field query requires the native word finder contract"
            raise TypeError(msg)
        owners = tuple(
            fragment
            for fragment in index.fragments
            if module.lines.get_line_number(fragment.start) == scope.get_start()
            and finder.get_word_at(fragment.start) == "class"
        )
        if len(owners) != 1:
            msg = "Native settings class has no unique indexed declaration"
            raise ValueError(msg)
        owner = owners[0]
        direct = frozenset(
            (fragment.start, fragment.end)
            for fragment in index.fragments
            if fragment.depth == owner.depth + 1
            and owner.start < fragment.start < fragment.end <= owner.end
            and index.context_at(fragment.start).structural_scope.pyobject
            is scope.pyobject
        )
        proven: set[str] = set()
        for name in wanted:
            binding = scope.get_defined_names().get(name)
            if (
                binding is None
                or not runtime.assigned_name(binding)
                or not any(
                    assignment.type_hint is not None
                    for assignment in binding.assignments
                )
            ):
                continue
            for pattern in (
                f"{name}: ${{annotation}}",
                f"{name}: ${{annotation}} = ${{value}}",
            ):
                regions = runtime.semantic_regions(
                    module,
                    pattern,
                    arguments={},
                    start=owner.start,
                    end=owner.end,
                )
                if direct.intersection(regions):
                    proven.add(name)
        return frozenset(proven)

    @staticmethod
    def discover_first_party_namespaces(
        project_dir: Path,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> Sequence[str]:
        """Discover live regular, namespace, and stub packages under ``src/``.

        Returns:
            The resulting ``Sequence[str]``.

        """
        src_dir = project_dir / c.Infra.DEFAULT_SRC_DIR
        return [
            name
            for name in FlextInfraUtilitiesDiscovery.discover_python_dirs(
                src_dir,
                workspace_excluded_top_dirs=frozenset(),
                source_project=source_project,
            )
            if name.isidentifier()
        ]

    @staticmethod
    def find_import_insert_position(
        lines: Sequence[str],
        *,
        past_existing: bool = True,
    ) -> int:
        """Return the module-level line index where an import may be inserted.

        The position is derived from parsed statements rather than scanned
        lines. A line scan cannot see that a match belongs to a continuation or
        to an indented suite, so it returned positions inside a parenthesized
        import list and inside ``if TYPE_CHECKING:``; inserting a column-zero
        statement at either point produced a file that no longer parses.

        Only top-level imports move the position. ``past_existing`` places it
        after the last of them; otherwise it lands after the module docstring
        and the ``__future__`` imports, before the first regular import.

        A module whose first statement is neither a docstring nor an import
        pins the position just above that statement: returning 0 would insert
        above comment-only header lines (shebang, encoding) and corrupt them.

        ``lines`` may or may not carry trailing newlines (callers feed both
        ``splitlines()`` and ``splitlines(keepends=True)``), so separators are
        normalized here: a ``"".join`` collapse would hand ``ast.parse`` one
        broken line.

        Returns:
            The module-level line index where an import may be inserted.

        """
        source = "\n".join(line.removesuffix("\n") for line in lines)
        module = ast.parse(source)
        position = 0
        for statement in module.body:
            if isinstance(statement, ast.Expr) and isinstance(
                statement.value,
                ast.Constant,
            ):
                if isinstance(statement.value.value, str) and position == 0:
                    position = statement.end_lineno or position
                    continue
                break
            if (
                isinstance(statement, ast.ImportFrom)
                and statement.module == "__future__"
            ):
                position = statement.end_lineno or position
                continue
            if past_existing and isinstance(statement, c.Infra.AST_IMPORT_TYPES):
                position = statement.end_lineno or position
                continue
            if position == 0 and statement.lineno:
                position = statement.lineno - 1
            break
        return position

    @staticmethod
    def parse_import_names(names_str: str) -> t.StrPairSequence:
        """Parse ``A, B as C`` into ``[(name, bound), ...]``.

        Returns:
            The resulting ``t.StrPairSequence``.

        """
        result: MutableSequence[tuple[str, str]] = []
        for part in names_str.split(","):
            candidate = part.strip().rstrip("\\").strip()
            if not candidate or candidate.startswith(("(", ")")):
                continue
            if " as " in candidate:
                name, alias = candidate.split(" as ", 1)
                result.append((name.strip(), alias.strip()))
                continue
            result.append((candidate, candidate))
        return result

    @classmethod
    def hoist_inline_imports(
        cls,
        file_path: Path,
        statement_lines: Sequence[t.IntPair],
    ) -> bool:
        """Move function-local import statements to the module import block.

        ``statement_lines`` holds the 1-based inclusive line span of each
        import statement a rule found. The statements are removed from their
        function bodies and their dedented text is added once after the
        module's last top-level import. A body left empty, or a result that no
        longer parses, raises: the move is never half-applied.

        Returns:
            The resulting ``bool``.

        """
        if not statement_lines:
            return False
        source = file_path.read_text(encoding=c.DEFAULT_ENCODING)
        updated = cls.plan_hoist_inline_imports(file_path, source, statement_lines)
        if updated == source:
            return False
        file_path.write_text(updated, encoding=c.DEFAULT_ENCODING)
        return True

    @classmethod
    def plan_hoist_inline_imports(
        cls,
        file_path: Path,
        source: str,
        statement_lines: Sequence[t.IntPair],
    ) -> str:
        """Plan the same statement hoist without changing its physical source.

        Returns:
            The source with the selected statements hoisted to the import block.

        """
        if not statement_lines:
            return source
        lines = source.splitlines(keepends=True)
        hoisted: list[str] = []
        drop: set[int] = set()
        for start, end in statement_lines:
            text = textwrap.dedent("".join(lines[start - 1 : end])).strip()
            if text not in hoisted:
                hoisted.append(text)
            drop.update(range(start, end + 1))
        kept = [line for index, line in enumerate(lines, start=1) if index not in drop]
        position = cls.find_import_insert_position(kept)
        present = {line.strip() for line in kept[:position]}
        block = [f"{text}\n" for text in hoisted if text not in present]
        updated = "".join([*kept[:position], *block, *kept[position:]])
        ast.parse(updated, filename=str(file_path))
        return updated

    @staticmethod
    def statements_at_module_end(
        source: str,
        statement_lines: Sequence[t.IntPair],
        *,
        filename: str,
    ) -> str:
        """Return ``source`` with top-level statements moved after its last one.

        ``statement_lines`` holds the 1-based inclusive line span of each
        top-level statement to move. The statements keep their text and
        relative order and close the module, separated from what precedes them
        by the blank lines PEP 8 asks for: two after a class or function, one
        otherwise. A result that no longer parses raises.

        Returns:
            The rewritten source; ``source`` itself when nothing moves.

        """
        if not statement_lines:
            return source
        lines = source.splitlines(keepends=True)
        drop = {
            index for start, end in statement_lines for index in range(start, end + 1)
        }
        moved = "".join(
            "".join(lines[start - 1 : end]).rstrip() + "\n"
            for start, end in sorted(statement_lines)
        )
        kept = "".join(
            line for index, line in enumerate(lines, start=1) if index not in drop
        ).rstrip()
        body = ast.parse(kept, filename=filename).body
        closes_definition = bool(body) and isinstance(
            body[-1], c.Infra.AST_DEFINITION_TYPES
        )
        separator = "\n\n\n" if closes_definition else "\n\n"
        updated = f"{kept}{separator}{moved}" if kept else moved
        ast.parse(updated, filename=filename)
        return updated

    @staticmethod
    def rewrite_source_at_offsets(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeFile,
        changes: Sequence[tuple[int, int, str]],
        *,
        apply: bool = True,
    ) -> str:
        """Apply offset-based edits (start, end, replacement) to source.

        Returns:
            The resulting ``str``.

        Raises:
            TypeError: If the resource is not a Rope file resource.

        """
        del rope_project
        if not FlextInfraUtilitiesRopeRuntime.file_resource(resource):
            msg = f"expected a Rope file resource: {resource.path}"
            raise TypeError(msg)
        source: str = resource.read()
        for start, end, replacement in sorted(changes, key=itemgetter(0), reverse=True):
            source = source[:start] + replacement + source[end:]
        if apply and source != resource.read():
            resource.write(source)
        return source


__all__: list[str] = ["FlextInfraUtilitiesRopeSource"]
