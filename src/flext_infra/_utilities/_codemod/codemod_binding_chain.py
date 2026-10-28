"""Binding-chain proofs the codemod project analysis reads.

A rewrite that replaces one spelling with another is safe only when both
resolve to the same binding at the occurrence. These proofs answer that from
native Rope identities: stable binding chains and the single reaching
binding, read by the semantic cutover contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
from pathlib import Path

from flext_infra import c, m, p
from flext_infra._utilities._codemod import FlextInfraUtilitiesCodemodRules
from flext_infra._utilities._rope.rope_runtime import FlextInfraUtilitiesRopeRuntime
from flext_infra._utilities._rope.rope_runtime_modules import (
    FlextInfraUtilitiesRopeRuntimeModules,
)
from flext_infra._utilities._rope.rope_runtime_refactors import (
    FlextInfraUtilitiesRopeRuntimeRefactors,
)
from flext_infra._utilities._rope.rope_runtime_types import (
    FlextInfraUtilitiesTypesRopeRuntime,
)
from flext_infra._utilities._rope.rope_structure import FlextInfraUtilitiesRopeStructure
from flext_infra._utilities._rope.source_bases_aliases import (
    FlextInfraUtilitiesRopeSourceBasesAliases,
)


class FlextInfraUtilitiesCodemodBindingChain:
    """Canonical namespace owner."""

    class FlextInfraUtilitiesCodemodBindingChain(FlextInfraUtilitiesCodemodRules):
        """Prove an occurrence's binding: one stable reaching declaration per link."""

        @staticmethod
        def _binding_symbols_match(
            expected: p.Infra.RopePyName | None,
            actual: p.Infra.RopePyName | None,
        ) -> bool:
            """Compare the resolved expectation against the actual occurrence.

            Returns:
                Whether both sides resolve to the same symbol or facade alias.

            """
            if expected is None or actual is None:
                return False
            if (
                isinstance(expected, p.Infra.RopeAssignedName)
                and len(expected.assignments) > 1
            ):
                return False
            if FlextInfraUtilitiesRopeRuntimeModules.same_name(expected, actual):
                return True
            # A facade alias is an assignment of the identical class, not a
            # duplicate declaration. Scalar/unknown object inference is never proof.
            owner = expected.get_object()
            return (
                FlextInfraUtilitiesRopeRuntime.abstract_class(owner)
                and owner is actual.get_object()
            )

        @classmethod
        def _binding_expression(cls, text: str) -> str | None:
            """Admit the dotted-name grammar before native lexical evaluation.

            Returns:
                The normalized native binding expression, or ``None``.

            """
            parts = tuple(part.strip() for part in text.split("."))
            return (
                ".".join(parts) if all(part.isidentifier() for part in parts) else None
            )

        @classmethod
        def stable_binding_chain(
            cls,
            frame: tuple[p.Infra.RopeProject, p.Infra.RopePyModule, p.Infra.RopeScope],
            expression: str,
            offset: int,
            sources: Mapping[Path, str],
            *,
            visited: frozenset[tuple[str, str]] = frozenset(),
        ) -> bool:
            """Reject rebound receivers, intermediate owners, and imported alias chains.

            ``frame`` carries the Rope project, the module owning the expression,
            and the lexical scope the expression resolves in.

            Returns:
                The resulting ``bool``.

            """
            project, module, scope = frame
            binding = cls._chain_base_binding(
                frame, expression, offset, sources, visited=visited
            )
            if binding is None:
                return False
            chain = cls._chain_module_text(module, sources)
            if chain is None:
                return False
            path, text = chain
            routes = FlextInfraUtilitiesRopeSourceBasesAliases.lazy_module_aliases(
                module.get_name(), path, text, project=project, pymodule=module
            )
            if not cls.single_reaching_binding(
                module, scope, expression, offset, routes
            ):
                return False
            if not cls._chain_alias_and_assignment_proven(
                project, binding, expression, routes, sources
            ):
                return False
            if isinstance(binding, p.Infra.RopeImportedName):
                return cls.chain_imported_binding(
                    project, binding, sources, visited=visited
                )
            return cls._chain_declaration_stable(
                project, binding, expression, sources, visited=visited
            )

        @classmethod
        def _chain_base_binding(
            cls,
            frame: tuple[p.Infra.RopeProject, p.Infra.RopePyModule, p.Infra.RopeScope],
            expression: str,
            offset: int,
            sources: Mapping[Path, str],
            *,
            visited: frozenset[tuple[str, str]],
        ) -> p.Infra.RopePyName | None:
            """Resolve the chain's base binding for one attribute or name expression.

            Returns:
                The resolved base binding, or ``None`` when the receiver chain is
                rebound, opaque, or the expression is neither attribute nor name.

            """
            scope = frame[2]
            normalized = cls._binding_expression(expression)
            if normalized is None:
                return None
            receiver, separator, _attribute = normalized.rpartition(".")
            if separator and not cls.stable_binding_chain(
                frame, receiver, offset, sources, visited=visited
            ):
                return None
            return FlextInfraUtilitiesRopeRuntimeModules.expression_name(
                scope, normalized
            )

        @staticmethod
        def _chain_module_text(
            module: p.Infra.RopeParsedModule,
            sources: Mapping[Path, str],
        ) -> tuple[Path, str] | None:
            """Locate the module source text inside the authenticated closure.

            Untouched consumers resolve through the project's authenticated
            snapshot instead of the planned working map. A folder resource
            without its initializer text in the closure is unavailable, never
            read directly.

            Returns:
                The module path and snapshot text, or ``None`` when unavailable.

            """
            resource = module.get_resource()
            if resource is None:
                return None
            path = Path(resource.real_path).resolve()
            if path.is_dir():
                path /= c.Infra.INIT_PY
            text = sources.get(path)
            if text is not None:
                return path, text
            if not FlextInfraUtilitiesTypesRopeRuntime.file_resource(resource):
                return None
            return path, resource.read()

        @classmethod
        def _chain_alias_and_assignment_proven(
            cls,
            project: p.Infra.RopeProject,
            binding: p.Infra.RopePyName,
            expression: str,
            routes: Mapping[str, str],
            sources: Mapping[Path, str],
        ) -> bool:
            """Hold the lazy alias route and the single-assignment contract.

            Returns:
                Whether the alias route agrees with the binding and the binding is
                assigned exactly once or declares a lazy type alias.

            """
            if expression.isidentifier() and expression in routes:
                route = FlextInfraUtilitiesRopeRuntime.require_semantic_module(
                    project.get_module(routes[expression])
                )
                target = route.get_attribute(expression)
                if not FlextInfraUtilitiesRopeRuntimeModules.same_name(
                    target, binding
                ) and (
                    not FlextInfraUtilitiesRopeRuntime.abstract_class(
                        target.get_object()
                    )
                    or target.get_object() is not binding.get_object()
                ):
                    return False
            if (
                isinstance(binding, p.Infra.RopeAssignedName)
                and len(binding.assignments) != 1
            ):
                context = cls._chain_holder_context(binding, sources)
                if binding.assignments or context is None:
                    return False
                _holder, line, text = context
                # Rope records no assigned value for lazy PEP 695 aliases.
                return any(
                    isinstance(node, ast.TypeAlias) and node.lineno == line
                    for node in ast.walk(ast.parse(text))
                )
            return True

        @classmethod
        def chain_imported_binding(
            cls,
            project: p.Infra.RopeProject,
            binding: p.Infra.RopeImportedName,
            sources: Mapping[Path, str],
            *,
            visited: frozenset[tuple[str, str]],
        ) -> bool:
            """Follow an imported name to its defining module and continue there.

            Returns:
                Whether the imported binding chain stays stable at its origin.

            """
            imported = binding.imported_module.get_object()
            imported = imported.get_module()
            if not FlextInfraUtilitiesTypesRopeRuntime.source_module(imported):
                return False
            key = (
                binding.imported_module.importing_module.get_name(),
                binding.imported_name,
            )
            if key in visited:
                return False
            imported_scope = imported.get_scope()
            chain = cls._chain_module_text(imported, sources)
            if chain is None:
                return False
            imported_text = chain[1]
            value = binding.get_object()
            if FlextInfraUtilitiesTypesRopeRuntime.pymodule(value) and (
                value.get_name() == f"{imported.get_name()}.{binding.imported_name}"
            ):
                # A from-import may publish a submodule without a declaration in
                # its package initializer. Rope lists submodules among package
                # structural attributes, so an implicit route is only unproven
                # when the initializer source itself declares the same name.
                rebound = cls._initializer_declares(
                    imported_text,
                    binding.imported_name,
                )
                return (
                    not rebound and cls._chain_module_text(value, sources) is not None
                )
            return cls.stable_binding_chain(
                (project, imported, imported_scope),
                binding.imported_name,
                len(imported_text),
                sources,
                visited=visited | {key},
            )

        @classmethod
        def _chain_declaration_stable(
            cls,
            project: p.Infra.RopeProject,
            binding: p.Infra.RopePyName,
            expression: str,
            sources: Mapping[Path, str],
            *,
            visited: frozenset[tuple[str, str]],
        ) -> bool:
            """Hold the definition site of the resolved binding against rebinds.

            Returns:
                Whether the binding's single declaration stays stable at its owner.

            """
            holder_context = cls._chain_holder_context(binding, sources)
            if (
                holder_context is None
                or isinstance(binding, p.Infra.RopeImportedModule)
                or FlextInfraUtilitiesTypesRopeRuntime.parameter_name(binding)
            ):
                return holder_context is not None
            holder, line, holder_text = holder_context
            chased = cls._chain_holder_declaration(
                holder, holder_text, line, expression.rpartition(".")[-1]
            )
            if chased is None:
                return False
            declaration, holder_offset, holder_scope = chased
            if not (
                isinstance(binding, p.Infra.RopeAssignedName)
                and declaration.category
                in {
                    c.Infra.StatementCategory.ASSIGN,
                    c.Infra.StatementCategory.ANN_ASSIGN,
                }
            ):
                return True
            pattern = (
                "${binding_target}: ${binding_annotation} = ${binding_value}"
                if declaration.category == c.Infra.StatementCategory.ANN_ASSIGN
                else "${binding_target} = ${binding_value}"
            )
            regions = tuple(
                FlextInfraUtilitiesRopeRuntimeRefactors.semantic_capture_region(
                    match, "binding_value"
                )
                for match in tuple(
                    FlextInfraUtilitiesRopeRuntimeRefactors.semantic_finder(
                        holder, arguments={}
                    ).get_matches(pattern, {})
                )
                if declaration.start_offset <= match.get_region()[0]
                and match.get_region()[1] <= declaration.end_offset
            )
            if len(regions) != 1:
                return False
            first, last = regions[0]
            value = cls._binding_expression(holder_text[first:last])
            if value is None:
                # A sole unconditional declaration whose value is not a dotted
                # name has no alias hop to chase: the binding is already proven
                # stable at its owner by the single-reaching-declaration proof.
                return True
            # The guard keys the link chased next (the assigned value), never the
            # link already proven: an import hop records (module, name) before this
            # declaration hop holds that same name, which is one chain, not a cycle.
            key = (holder.get_name(), value)
            return key not in visited and cls.stable_binding_chain(
                (project, holder, holder_scope),
                value,
                holder_offset,
                sources,
                visited=visited | {key},
            )

        @classmethod
        def _chain_holder_context(
            cls,
            binding: p.Infra.RopePyName,
            sources: Mapping[Path, str],
        ) -> tuple[p.Infra.RopePyModule, int | None, str] | None:
            """Locate one binding's definition inside the authenticated closure.

            Untouched definition sites resolve through the project's
            authenticated snapshot instead of the planned working map.

            Returns:
                The defining module, its line, and the snapshot text, or ``None``
                when the definition site is unavailable or uncaptured.

            """
            holder, line = binding.get_definition_location()
            if holder is None:
                return None
            holder = holder.get_module()
            if not FlextInfraUtilitiesTypesRopeRuntime.source_module(holder):
                return None
            chain = cls._chain_module_text(holder, sources)
            if chain is None:
                return None
            if line is None:
                runtime = FlextInfraUtilitiesRopeRuntimeModules
                aliases = tuple(
                    node.lineno
                    for node in ast.walk(ast.parse(chain[1]))
                    if isinstance(node, ast.TypeAlias)
                    and runtime.same_name(
                        binding,
                        runtime.expression_name(
                            runtime.scope_at(
                                holder, holder.lines.get_line_start(node.lineno)
                            ),
                            node.name.id,
                        ),
                    )
                )
                if len(aliases) == 1:
                    (line,) = aliases
            return holder, line, chain[1]

        @classmethod
        def _initializer_declares(cls, text: str, name: str) -> bool:
            """Report whether an initializer source binds ``name`` at module level.

            Rope lists package submodules among structural attributes, so the
            implicit from-import route of a submodule is only unproven when the
            initializer's own declared statements bind the same name.

            Returns:
                Whether a module-level initializer statement binds ``name``.

            """
            return any(
                name in cls._statement_bound_names(row.text)
                for row in FlextInfraUtilitiesRopeStructure.logical_statements(text)
                if row.enclosing_kind == c.Infra.RopeScopeKind.MODULE
                and row.category
                in {
                    c.Infra.StatementCategory.ASSIGN,
                    c.Infra.StatementCategory.ANN_ASSIGN,
                    c.Infra.StatementCategory.IMPORT,
                    c.Infra.StatementCategory.FROM_IMPORT,
                }
            )

        @staticmethod
        def _statement_bound_names(text: str) -> frozenset[str]:
            """Return the names one module-level statement binds.

            Returns:
                The declared binding names of the statement, parsed once
                through Rope's native module boundary.

            """
            isolated = FlextInfraUtilitiesRopeRuntimeModules.build_string_module(
                None,
                text.strip(),
            )
            return frozenset(isolated.get_scope().get_defined_names())

        @classmethod
        def _chain_holder_declaration(
            cls,
            holder: p.Infra.RopePyModule,
            holder_text: str,
            line: int | None,
            name: str,
        ) -> tuple[m.Infra.LogicalStatement, int, p.Infra.RopeScope] | None:
            """Prove the holder's declaration is the single reaching definition.

            Returns:
                The declaration, its offset, and the holder lexical scope, or
                ``None`` when the declaration is absent or ambiguous.

            """
            runtime = FlextInfraUtilitiesRopeRuntimeModules
            declaration = next(
                (
                    row
                    for row in FlextInfraUtilitiesRopeStructure.logical_statements(
                        holder_text
                    )
                    if row.line <= (line or 0) <= row.end_line
                ),
                None,
            )
            if declaration is None:
                return None
            holder_offset = declaration.start_offset
            holder_scope = runtime.scope_at(
                holder, holder_offset, declaration_line=line
            )
            if not cls.single_reaching_binding(
                holder,
                holder_scope,
                name,
                len(holder_text),
            ):
                return None
            return declaration, holder_offset, holder_scope

        @classmethod
        def single_reaching_binding(
            cls,
            module: p.Infra.RopePyModule,
            scope: p.Infra.RopeScope,
            expression: str,
            offset: int,
            declared_routes: Mapping[str, str] | None = None,
        ) -> bool:
            """Prove one unconditional declaration instead of Rope's last assignment.

            Returns:
                The resulting ``bool``.

            """
            declarations = cls.single_reaching_declarations(module, scope, expression)
            if "." in expression:
                return not declarations
            if len(declarations) != 1:
                return False
            declaration, start = declarations[0]
            if start >= offset and not (
                scope.get_kind() != c.Infra.RopeScopeKind.MODULE
                and declaration.enclosing_kind == c.Infra.RopeScopeKind.MODULE
            ):
                return False
            return cls._declaration_reaches_unconditionally(
                module, scope, declaration, expression, declared_routes
            )

        @classmethod
        def _occurrence_is_imported(
            cls,
            module: p.Infra.RopePyModule,
            row: m.Infra.LogicalStatement,
            expression: str,
        ) -> bool:
            """Report whether the statement imports the expression into scope.

            Returns:
                Whether the import statement's module scope defines the
                expression.

            Raises:
                TypeError: If the parsed module lacks its native source graph.

            """
            if row.category not in {
                c.Infra.StatementCategory.IMPORT,
                c.Infra.StatementCategory.FROM_IMPORT,
            }:
                return False
            if not FlextInfraUtilitiesTypesRopeRuntime.source_module(module):
                msg = "native import occurrence has no source-module graph"
                raise TypeError(msg)
            runtime = FlextInfraUtilitiesRopeRuntimeModules
            imported_module = runtime.build_string_module(
                module.pycore.project, row.text.strip()
            )
            imported_scope = imported_module.get_scope()
            return expression in imported_scope.get_defined_names()

        @classmethod
        def single_reaching_declarations(
            cls,
            module: p.Infra.RopePyModule,
            scope: p.Infra.RopeScope,
            expression: str,
        ) -> Sequence[tuple[m.Infra.LogicalStatement, int]]:
            """Collect the frame-local declarations competing with the expression.

            Returns:
                The declarations of the expression's spelling at the scope frame.

            """
            if not FlextInfraUtilitiesTypesRopeRuntime.source_module(module):
                return ()
            source = module.source_code
            runtime = FlextInfraUtilitiesRopeRuntimeModules
            rows = FlextInfraUtilitiesRopeStructure.logical_statements(source)
            name = expression.rpartition(".")[-1]
            binding = runtime.expression_name(scope, expression)
            assignment_lines: frozenset[int | None] = (
                frozenset(assignment.get_lineno() for assignment in binding.assignments)
                if isinstance(binding, p.Infra.RopeAssignedName)
                else frozenset()
            )
            finder = FlextInfraUtilitiesRopeRuntimeRefactors.lexical_occurrence_finder(
                module.pycore.project, name
            )
            declarations: list[tuple[m.Infra.LogicalStatement, int]] = []
            seen: set[tuple[int, int]] = set()
            for occurrence in finder.find_occurrences(pymodule=module):
                start, end = occurrence.get_primary_range()
                if cls._binding_expression(source[start:end]) != expression:
                    continue
                row = next(
                    (
                        statement
                        for statement in rows
                        if statement.start_offset
                        <= occurrence.offset
                        < statement.end_offset
                    ),
                    None,
                )
                if row is None:
                    continue
                if not cls._occurrence_redefines(
                    (module, scope),
                    occurrence,
                    row,
                    expression,
                    assignment_lines,
                ):
                    continue
                key = row.start_offset, occurrence.offset
                if key not in seen:
                    seen.add(key)
                    declarations.append((row, occurrence.offset))
            return declarations

        @classmethod
        def _occurrence_redefines(
            cls,
            frame: tuple[p.Infra.RopePyModule, p.Infra.RopeScope],
            occurrence: p.Infra.RopeOccurrence,
            row: m.Infra.LogicalStatement,
            expression: str,
            assignment_lines: frozenset[int | None],
        ) -> bool:
            """Classify one occurrence as a competing frame-local declaration.

            Args:
                frame: The queried Rope module and lexical scope frame.
                occurrence: The lexical occurrence of the expression.
                row: The logical statement containing the occurrence.
                expression: The full dotted binding expression.
                assignment_lines: Line numbers of the binding's assignments.

            Returns:
                Whether the occurrence writes, defines, imports, or deletes the
                expression inside the queried frame.

            """
            module, scope = frame
            binding = FlextInfraUtilitiesRopeRuntimeModules.expression_name(
                scope, expression
            )
            parameter = (
                binding is not None
                and FlextInfraUtilitiesTypesRopeRuntime.parameter_name(binding)
            )
            found_scope = FlextInfraUtilitiesRopeRuntimeModules.scope_at(
                module,
                occurrence.offset,
                declaration_line=(
                    row.line
                    if row.category
                    in {
                        c.Infra.StatementCategory.CLASS_DEF,
                        c.Infra.StatementCategory.FUNC_DEF,
                    }
                    and not parameter
                    else None
                ),
            )
            if found_scope is not scope and (
                found_scope.get_kind() != c.Infra.RopeScopeKind.MODULE
            ):
                return False
            imported = cls._occurrence_is_imported(module, row, expression)
            assigned = (
                occurrence.is_defined()
                or (expression.isidentifier() and occurrence.lineno in assignment_lines)
                or cls._occurrence_writes_header_name(row, occurrence)
            )
            if row.category == c.Infra.StatementCategory.ANN_ASSIGN:
                assigned |= (
                    cls._binding_expression(row.text.partition(":")[0]) == expression
                )
            if row.text.lstrip().startswith("del "):
                assigned = True
            return assigned or imported

        @staticmethod
        def _occurrence_writes_header_name(
            row: m.Infra.LogicalStatement,
            occurrence: p.Infra.RopeOccurrence,
        ) -> bool:
            """Report whether one header occurrence writes its expression.

            Rope's textual ``is_written`` misreads parameter annotations such as
            ``def write(marker: _Marker = _SENTINEL)``, where the annotated name
            textually precedes ``=`` without being an assignment target. The
            native statement tree owns the store-or-load verdict.

            Returns:
                Whether the occurrence carries a native ``Store`` context.

            """
            if row.category not in {
                c.Infra.StatementCategory.FUNC_DEF,
                c.Infra.StatementCategory.CLASS_DEF,
                c.Infra.StatementCategory.TYPE_ALIAS,
            }:
                return occurrence.is_written()
            prefix = len(row.text) - len(row.text.lstrip())
            source = row.text[prefix:]
            if source.rstrip().endswith(":"):
                source = f"{source.rstrip()}\n{' ' * (prefix + 4)}pass"
            try:
                tree = ast.parse(source)
            except SyntaxError:
                return occurrence.is_written()
            relative = occurrence.get_word_range()[0] - row.start_offset - prefix
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Name)
                    and node.col_offset == relative
                    and isinstance(node.ctx, ast.Store)
                ):
                    return True
            return False

        @staticmethod
        def _declaration_reaches_unconditionally(
            module: p.Infra.RopePyModule,
            scope: p.Infra.RopeScope,
            declaration: m.Infra.LogicalStatement,
            expression: str,
            declared_routes: Mapping[str, str] | None,
        ) -> bool:
            """Report whether the declaration dominates the queried offset.

            Returns:
                Whether no conditional frame guards the declaration, allowing the
                declared lazy-module routes.

            """
            rows = tuple(
                row
                for row in FlextInfraUtilitiesRopeStructure.logical_statements(
                    module.source_code
                )
                if (
                    scope.get_kind() == c.Infra.RopeScopeKind.MODULE
                    and row.enclosing_kind == c.Infra.RopeScopeKind.MODULE
                )
                or (
                    scope.get_start() < row.line <= scope.get_end()
                    and row.enclosing_kind == scope.get_kind()
                    and row.enclosing_name == scope.pyobject.get_name()
                )
            )
            direct_indent = (
                0
                if scope.get_kind() == c.Infra.RopeScopeKind.MODULE
                else min((row.indent for row in rows), default=declaration.indent)
            )
            if declaration.indent <= direct_indent:
                return True
            if declared_routes is None or expression not in declared_routes:
                return False
            guards: list[m.Infra.LogicalStatement] = []
            for row in rows:
                if row.start_offset >= declaration.start_offset:
                    break
                while guards and row.indent <= guards[-1].indent:
                    guards.pop()
                if row.text.rstrip().endswith(":"):
                    guards.append(row)
            return bool(guards) and all(
                row.category == c.Infra.StatementCategory.IF_GUARD
                or row.text.lstrip().startswith(("else:", "elif "))
                for row in guards
            )


__all__: list[str] = ["FlextInfraUtilitiesCodemodBindingChain"]
