"""Source-level Rope rewrite helpers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import textwrap
from collections.abc import Mapping, MutableSequence, Sequence
from operator import itemgetter
from pathlib import Path

from flext_infra import c, p, t
from flext_infra._utilities import FlextInfraUtilitiesDiscovery
from flext_infra._utilities._rope.rope_runtime import FlextInfraUtilitiesRopeRuntime


class FlextInfraUtilitiesRopeSource:
    """Text-oriented helpers shared by Rope-backed refactors."""

    @staticmethod
    def source_declaration_region(
        module: p.Infra.RopeSourceModule,
        node: p.Infra.RopeAstNode,
    ) -> tuple[int, int]:
        """Read an opaque native node's exact region through its SDK index.

        Returns:
            The original inclusive/exclusive character offsets.

        Raises:
            ValueError: The native declaration has no valid source region.

        """
        start, end = module.get_source_binding_index().lines[node]
        if (
            start is None
            or end is None
            or not 0 <= start < end <= len(module.source_code)
        ):
            message = "Native declaration has no valid source region"
            raise ValueError(message)
        return start, end

    @classmethod
    def source_class_fields(
        cls, owner: p.Infra.RopeSourceClass
    ) -> Mapping[str, tuple[int, int]]:
        """Describe direct annotated fields through native class bindings.

        Inherited field precedence belongs to the native class-order owner.
        This query neither duplicates that order nor interprets syntax nodes.

        Returns:
            Declared field names mapped to their annotation source regions.

        Raises:
            TypeError: The declaring module is not a native source module.
            ValueError: A direct field has competing annotated declarations.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        module = owner.get_module()
        if not runtime.source_module(module):
            message = "Class field declarations require a native source module"
            raise TypeError(message)
        scope = owner.get_scope()
        fields: dict[str, tuple[int, int]] = {}
        index = module.get_source_binding_index()
        for name, binding in scope.get_defined_names().items():
            if not runtime.assigned_name(binding):
                continue
            regions: set[tuple[int, int]] = set()
            for assignment in binding.assignments:
                if assignment.type_hint is None:
                    continue
                region = cls.source_declaration_region(module, assignment.type_hint)
                if index.context_at(region[0]).structural_scope.pyobject is owner:
                    regions.add(region)
            if len(regions) > 1:
                message = (
                    f"Competing native field annotations: {owner.get_name()}.{name}"
                )
                raise ValueError(message)
            if regions:
                fields[name] = next(iter(regions))
        return fields

    @staticmethod
    def source_return_annotation(
        owner: p.Infra.RopeSourceFunction,
    ) -> tuple[int, int] | None:
        """Select the complete return annotation already classified by Rope.

        Returns:
            Its source region, or ``None`` for an unannotated function.

        Raises:
            TypeError: The declaring module is not a native source module.
            ValueError: Rope reports competing return-annotation roots.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        module = owner.get_module()
        if not runtime.source_module(module):
            message = "Return annotations require a native source module"
            raise TypeError(message)
        regions = frozenset(
            (fragment.start, fragment.end)
            for fragment in module.get_source_binding_index().fragments
            if fragment.context.role == "return-annotation"
            and fragment.context.structural_scope.pyobject is owner
        )
        roots = tuple(
            region
            for region in regions
            if not any(
                other != region and other[0] <= region[0] < region[1] <= other[1]
                for other in regions
            )
        )
        if len(roots) > 1:
            message = f"Competing native return annotations: {owner.get_name()}"
            raise ValueError(message)
        return roots[0] if roots else None

    @staticmethod
    def source_parameter_annotations(
        owner: p.Infra.RopeSourceFunction,
    ) -> Mapping[str, tuple[int, int]]:
        """Associate native parameter-annotation regions with native formal names.

        Returns:
            Annotated parameter names and their exact annotation regions.

        Raises:
            TypeError: The module or word finder lacks its native contract.
            ValueError: A parameter has competing native annotation roots.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        module = owner.get_module()
        if not runtime.source_module(module):
            message = "Parameter annotations require a native source module"
            raise TypeError(message)
        word = runtime.runtime_callable("rope.base.worder", "Worder")(
            module.source_code
        )
        if not isinstance(word, p.Infra.RopeWorder):
            message = "Parameter annotations require the native word finder"
            raise TypeError(message)
        fragments = module.get_source_binding_index().fragments
        annotations: dict[str, tuple[int, int]] = {}
        for _kind, name in owner.get_parameter_layout():
            formals = tuple(
                fragment
                for fragment in fragments
                if fragment.context.role == "formal-token"
                and fragment.context.structural_scope.pyobject is owner
                and word.get_word_at(fragment.start) == name
            )
            regions = frozenset(
                (fragment.start, fragment.end)
                for fragment in fragments
                if fragment.context.role == "parameter-annotation"
                and fragment.context.structural_scope.pyobject is owner
                and any(
                    formal.start <= fragment.start < fragment.end <= formal.end
                    for formal in formals
                )
            )
            roots = tuple(
                region
                for region in regions
                if not any(
                    other != region and other[0] <= region[0] < region[1] <= other[1]
                    for other in regions
                )
            )
            if len(roots) > 1:
                message = f"Competing native parameter annotations: {name}"
                raise ValueError(message)
            if roots:
                annotations[name] = roots[0]
        return annotations

    @staticmethod
    def source_type_parameters(
        owner: p.Infra.RopeSourceObject,
    ) -> tuple[tuple[int, int], ...]:
        """Retain native PEP 695 declarations, including their bounds/defaults.

        Returns:
            Type-parameter regions in the original declaration order.

        Raises:
            TypeError: The declaring module is not a native source module.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        module = owner.get_module()
        if not runtime.source_module(module):
            message = "Type parameters require a native source module"
            raise TypeError(message)
        return tuple(
            sorted({
                (fragment.start, fragment.end)
                for fragment in module.get_source_binding_index().fragments
                if fragment.context.role == "type-parameter-token"
                and fragment.context.structural_scope.pyobject is owner
            })
        )

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
                name
                for scope in cls._class_scopes(module)
                if wanted.intersection(scope.get_defined_names())
                and cls._settings_owner(scope.pyobject, roots)
                for name in cls._direct_settings_fields(module, scope, wanted)
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
