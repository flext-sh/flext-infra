"""Binding-chain proofs the codemod project analysis reads.

ast-grep matches one file's syntax. Some laws are verdicts over the whole
project: whether a module takes part in an import cycle, whether a facade's
namespace composes every class its family package declares. The engine owns
building those project facts once per admission pass, from the tree as it is
then (a pass after a rewrite reads the rewritten project); rule
documents name the verdict they need through ``metadata.context`` predicates.
No rule lives here: the rule data decides where a fact is asked and what it
means.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from flext_infra import c, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodemodRules,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
    FlextInfraUtilitiesRopeStructure,
)
from flext_infra._utilities._rope_source_bases_aliases import (
    FlextInfraUtilitiesRopeSourceBasesAliases,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
)


class FlextInfraFlextUtilitiesCodemodBindingChain:
    """Canonical namespace owner."""

    class FlextInfraUtilitiesCodemodBindingChain(FlextInfraUtilitiesCodemodRules):
        """Prove an occurrence's binding: one stable reaching declaration per link."""

        RESOLVED_SYMBOL_OPERAND_COUNT: ClassVar[int] = 2

        @classmethod
        def _occurrence_binding_holds(
            cls,
            frame: t.Triple[Path, Path, p.Infra.RopeProject],
            condition: m.Infra.CodemodContextCondition,
            captures: t.JsonMapping,
            sources: t.MappingKV[Path, str],
        ) -> bool:
            """Resolve the exact captured expression, never another same-spelling use.

            A resolved-symbol operand names a module and its expression; same-binding
            names an expression in the occurrence's lexical scope. Annotation payloads
            are not executable migration candidates. Missing coordinates are a rule
            defect, not permission to resolve at module scope.


            Args:
                frame: A triple containing the root path, source path, and Rope project.
                condition: The codemod context condition to evaluate.
                captures: A mapping of captured variables.
                sources: A mapping of source file paths to their content.

            Returns:
                The resulting ``bool``.
            """
            root, source, project = frame
            capture = m.Infra.AstGrepCapture.model_validate(
                captures[condition.variable]
            )
            content = sources[source].encode("utf-8")
            text, start, end = cls._validated_capture_span(source, capture, content)
            resource = project.get_resource(
                source.relative_to(root.resolve()).as_posix()
            )
            module = project.get_pymodule(resource)
            if (
                condition.predicate
                is c.Infra.CodemodContextPredicate.UNREFERENCED_IMPORT
            ):
                return cls._unreferenced_import_holds(
                    project, module, capture.text, (start, end)
                )
            if (start, end) not in (
                FlextInfraUtilitiesRopeRuntimeRefactors.semantic_regions(
                    module,
                    "${binding_occurrence}",
                    arguments={},
                    start=start,
                    end=end,
                )
            ):
                return False
            scope = FlextInfraUtilitiesRopeRuntimeModules.scope_at(module, start)
            if cls._type_payload_occurrence(project, module, text, start, end):
                return False
            if condition.predicate in {
                c.Infra.CodemodContextPredicate.SAME_BINDING,
                c.Infra.CodemodContextPredicate.EXECUTABLE_OCCURRENCE,
            } and not cls._subscript_bindings_stable(
                project, module, text, (start, end), sources
            ):
                return False
            return cls._predicate_binding_verdict(
                (project, module, scope),
                condition,
                capture.text,
                start,
                sources,
            )

        @classmethod
        def _predicate_binding_verdict(
            cls,
            frame: t.Triple[
                p.Infra.RopeProject, p.Infra.RopePyModule, p.Infra.RopeScope
            ],
            condition: m.Infra.CodemodContextCondition,
            capture_text: str,
            start: int,
            sources: t.MappingKV[Path, str],
        ) -> bool:
            """Grade one admitted occurrence through its configured predicate.

            Args:
                frame: Rope project, module and lexical scope of the occurrence.
                condition: The codemod context condition to evaluate.
                capture_text: Exact captured expression text.
                start: Occurrence start offset inside its source.
                sources: Mapping of source file paths to their content.

            Returns:
                Whether the occurrence satisfies its binding predicate.
            """
            if (
                condition.predicate
                is c.Infra.CodemodContextPredicate.EXECUTABLE_OCCURRENCE
            ):
                return True
            if condition.predicate is c.Infra.CodemodContextPredicate.EMITTED_SYMBOL:
                return cls._emitted_symbol_holds(
                    frame,
                    condition,
                    start,
                    sources,
                )
            return cls._resolved_expression_holds(
                frame,
                condition,
                capture_text,
                start,
                sources,
            )

        @classmethod
        def _emitted_symbol_holds(
            cls,
            frame: t.Triple[
                p.Infra.RopeProject, p.Infra.RopePyModule, p.Infra.RopeScope
            ],
            condition: m.Infra.CodemodContextCondition,
            start: int,
            sources: t.MappingKV[Path, str],
        ) -> bool:
            """Resolve an emitted-symbol predicate through its module target.

            Returns:
                Whether the rewritten expression keeps a stable binding chain.

            Raises:
                ValueError: If emitted-symbol lacks a lexical expression, module
                    and target.

            """
            if len(condition.arg) != cls.RESOLVED_SYMBOL_OPERAND_COUNT + 1:
                message = (
                    "emitted-symbol requires a lexical expression, module and target"
                )
                raise ValueError(message)
            expression = condition.arg[0]
            if not cls._stable_binding_chain(
                frame,
                expression,
                start,
                sources,
            ):
                return False
            return cls._resolved_expression_holds(
                frame,
                condition.model_copy(
                    update={
                        "predicate": c.Infra.CodemodContextPredicate.RESOLVED_SYMBOL,
                        "arg": condition.arg[1:],
                    }
                ),
                condition.arg[0],
                start,
                sources,
            )

        @staticmethod
        def _validated_capture_span(
            source: Path,
            capture: m.Infra.AstGrepCapture,
            content: bytes,
        ) -> t.Triple[str, int, int]:
            """Validate the capture bytes against the snapshot content.

            Returns:
                The decoded source text and the capture start/end character
                offsets.

            Raises:
                ValueError: If binding capture differs from source.

            """
            if not (0 <= capture.start_byte < capture.end_byte <= len(content)) or (
                content[capture.start_byte : capture.end_byte]
                != capture.text.encode("utf-8")
            ):
                msg = f"binding capture differs from source: {source}"
                raise ValueError(msg)
            text = content.decode("utf-8")
            start = len(content[: capture.start_byte].decode("utf-8"))
            end = len(content[: capture.end_byte].decode("utf-8"))
            return text, start, end

        @staticmethod
        def _unreferenced_import_holds(
            project: p.Infra.RopeProject,
            module: p.Infra.RopePyModule,
            capture_text: str,
            span: t.Pair[int, int],
        ) -> bool:
            """Report whether an import capture has no load references anywhere.

            Returns:
                Whether the single captured import stays unreferenced.

            """
            start, end = span
            statements = tuple(
                row
                for row in FlextInfraUtilitiesRopeStructure.logical_statements(
                    module.source_code
                )
                if row.start_offset <= start < end <= row.end_offset
                and row.category
                in {
                    c.Infra.StatementCategory.IMPORT,
                    c.Infra.StatementCategory.FROM_IMPORT,
                }
                and row.text.strip() == capture_text.strip()
            )
            if len(statements) != 1:
                return False
            isolated = FlextInfraUtilitiesRopeRuntimeModules.build_string_module(
                project, capture_text
            )
            scope = isolated.get_scope()
            if scope is None:
                return False
            lexical = FlextInfraUtilitiesRopeRuntimeModules.scope_at(module, start)
            names = scope.get_defined_names()
            if not names:
                return False
            for name in names:
                binding = FlextInfraUtilitiesRopeRuntimeModules.expression_name(
                    lexical, name
                )
                if binding is None:
                    return False
                finder = (
                    FlextInfraUtilitiesRopeRuntimeRefactors.create_occurrence_finder(
                        project, name, binding, imports=True, in_hierarchy=False
                    )
                )
                if any(
                    not start <= occurrence.offset < end
                    for occurrence in finder.find_occurrences(pymodule=module)
                ):
                    return False
            return True

        @staticmethod
        def _type_payload_occurrence(
            project: p.Infra.RopeProject,
            module: p.Infra.RopePyModule,
            text: str,
            start: int,
            end: int,
        ) -> bool:
            """Report whether the occurrence lands inside a type payload range.

            Returns:
                Whether the capture start sits inside an annotation payload.

            """
            payload_ranges = (
                FlextInfraUtilitiesSemanticFamilyTypeReferences.type_payload_ranges
            )
            return any(
                left <= start < end <= right
                for left, right in payload_ranges(text, project, module)
            )

        @classmethod
        def _subscript_bindings_stable(
            cls,
            project: p.Infra.RopeProject,
            module: p.Infra.RopePyModule,
            text: str,
            span: t.Pair[int, int],
            sources: t.MappingKV[Path, str],
        ) -> bool:
            """Hold every enclosing subscript receiver on a stable binding chain.

            Returns:
                Whether no enclosing subscript hides a rebound or opaque wrapper.

            """
            start, end = span
            finder = FlextInfraUtilitiesRopeRuntimeRefactors.semantic_finder(module)
            for match in finder.get_matches(
                "${subscription_receiver}[${subscription_argument}]", {}
            ):
                left, right = match.get_region()
                receiver = (
                    FlextInfraUtilitiesRopeRuntimeRefactors.semantic_capture_region(
                        match, "subscription_receiver"
                    )
                )
                if receiver is None:
                    return False
                first, last = receiver
                if left <= start < end <= right and not cls._stable_binding_chain(
                    (
                        project,
                        module,
                        FlextInfraUtilitiesRopeRuntimeModules.scope_at(module, left),
                    ),
                    text[first:last],
                    left,
                    sources,
                ):
                    # A rebound/opaque wrapper can be a typing payload even
                    # when scope-wide inference currently calls it something
                    # else. Refuse the fixer rather than reinterpret its data.
                    return False
            return True

        @classmethod
        def _resolved_expression_holds(
            cls,
            frame: t.Triple[
                p.Infra.RopeProject, p.Infra.RopePyModule, p.Infra.RopeScope
            ],
            condition: m.Infra.CodemodContextCondition,
            capture_text: str,
            start: int,
            sources: t.MappingKV[Path, str],
        ) -> bool:
            """Resolve the captured expression against its predicate's target.

            Returns:
                Whether the resolved symbol matches the predicate's expectation.

            Raises:
                ValueError: If resolved-symbol requires a module and an expression; or
                    if same-binding requires one lexical expression.

            """
            runtime = FlextInfraUtilitiesRopeRuntimeModules
            project, scope = frame[0], frame[2]
            expression = cls._binding_expression(capture_text)
            if expression is None:
                return False
            actual = runtime.expression_name(scope, expression)
            if condition.predicate is c.Infra.CodemodContextPredicate.RESOLVED_SYMBOL:
                return cls._resolved_symbol_matches(
                    project, condition, actual
                ) and cls._stable_binding_chain(frame, expression, start, sources)
            if len(condition.arg) != 1:
                msg = "same-binding requires one lexical expression"
                raise ValueError(msg)
            target = condition.arg[0]
            target_expression = cls._binding_expression(target)
            if target_expression is None:
                return False
            if not (
                cls._stable_binding_chain(frame, expression, start, sources)
                and cls._stable_binding_chain(frame, target_expression, start, sources)
            ):
                return False
            primary = target_expression.partition(".")[0]
            if (
                scope.get_kind() != c.Infra.RopeScopeKind.MODULE
                and primary in scope.get_defined_names()
            ):
                # A local assignment/import/parameter can capture the emitted
                # facade even when Rope infers its current value as a class.
                return False
            expected = runtime.expression_name(scope, target_expression)
            return cls._binding_symbols_match(expected, actual)

        @classmethod
        def _resolved_symbol_matches(
            cls,
            project: p.Infra.RopeProject,
            condition: m.Infra.CodemodContextCondition,
            actual: p.Infra.RopePyName | None,
        ) -> bool:
            """Resolve the predicate's module-qualified target symbol.

            Returns:
                Whether the module target resolves to the actual occurrence symbol.

            Raises:
                ValueError: If resolved-symbol requires a module and an expression.

            """
            if len(condition.arg) != cls.RESOLVED_SYMBOL_OPERAND_COUNT:
                msg = "resolved-symbol requires a module and an expression"
                raise ValueError(msg)
            target_module, target = condition.arg
            scope = project.get_module(target_module).get_scope()
            if scope is None:
                return False
            expected = FlextInfraUtilitiesRopeRuntimeModules.expression_name(
                scope, target
            )
            return cls._binding_symbols_match(expected, actual)

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
                and len(expected.assignments) != 1
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
        def _stable_binding_chain(
            cls,
            frame: t.Triple[
                p.Infra.RopeProject, p.Infra.RopePyModule, p.Infra.RopeScope
            ],
            expression: str,
            offset: int,
            sources: t.MappingKV[Path, str],
            *,
            visited: frozenset[t.Pair[str, str]] = frozenset(),
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
            chain = cls._chain_module_text(project, module, sources)
            if chain is None:
                return False
            path, text = chain
            routes = FlextInfraUtilitiesRopeSourceBasesAliases.lazy_module_aliases(
                module.get_name(), path, text, project=project
            )
            if not cls._single_reaching_binding(
                module, scope, expression, offset, routes
            ):
                return False
            if not cls._chain_alias_and_assignment_proven(
                project, binding, expression, routes
            ):
                return False
            if isinstance(binding, p.Infra.RopeImportedName):
                return cls._chain_imported_binding(
                    project, binding, sources, visited=visited
                )
            return cls._chain_declaration_stable(
                project, binding, expression, sources, visited=visited
            )

        @classmethod
        def _chain_base_binding(
            cls,
            frame: t.Triple[
                p.Infra.RopeProject, p.Infra.RopePyModule, p.Infra.RopeScope
            ],
            expression: str,
            offset: int,
            sources: t.MappingKV[Path, str],
            *,
            visited: frozenset[t.Pair[str, str]],
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
            if separator and not cls._stable_binding_chain(
                frame, receiver, offset, sources, visited=visited
            ):
                return None
            return FlextInfraUtilitiesRopeRuntimeModules.expression_name(
                scope, normalized
            )

        @staticmethod
        def _chain_module_text(
            project: p.Infra.RopeProject,
            module: p.Infra.RopePyModule,
            sources: t.MappingKV[Path, str],
        ) -> t.Pair[Path, str] | None:
            """Locate the module source text inside the closed project.

            Returns:
                The module path and snapshot text, or ``None`` when unavailable.

            """
            resource = module.get_resource()
            if resource is None:
                return None
            path = Path(resource.real_path).resolve()
            if path.is_dir():
                path /= c.Infra.INIT_PY
            if not path.is_relative_to(Path(project.root.real_path).resolve()):
                # NoProject-backed foreign modules can read disk outside the closed
                # project's filesystem commands. Their receipts guard publication,
                # but cannot establish an immutable inference graph: refuse a fixer.
                return None
            text = sources.get(path)
            if text is None:
                return None
            return path, text

        @staticmethod
        def _chain_alias_and_assignment_proven(
            project: p.Infra.RopeProject,
            binding: p.Infra.RopePyName,
            expression: str,
            routes: t.StrMapping,
        ) -> bool:
            """Hold the lazy alias route and the single-assignment contract.

            Returns:
                Whether the alias route agrees with the binding and the binding is
                assigned exactly once.

            """
            if expression.isidentifier() and expression in routes:
                route = project.get_module(routes[expression])
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
            return not (
                isinstance(binding, p.Infra.RopeAssignedName)
                and len(binding.assignments) != 1
            )

        @classmethod
        def _chain_imported_binding(
            cls,
            project: p.Infra.RopeProject,
            binding: p.Infra.RopeImportedName,
            sources: t.MappingKV[Path, str],
            *,
            visited: frozenset[t.Pair[str, str]],
        ) -> bool:
            """Follow an imported name to its defining module and continue there.

            Returns:
                Whether the imported binding chain stays stable at its origin.

            """
            imported = binding.imported_module.get_object()
            if not FlextInfraUtilitiesRopeRuntimeTypes.pymodule(imported):
                return False
            key = (
                binding.imported_module.importing_module.get_name(),
                binding.imported_name,
            )
            if key in visited:
                return False
            imported_scope = imported.get_scope()
            imported_resource = imported.get_resource()
            if imported_scope is None or imported_resource is None:
                return False
            imported_path = Path(imported_resource.real_path).resolve()
            if imported_path.is_dir():
                imported_path /= c.Infra.INIT_PY
            imported_text = sources.get(imported_path)
            if imported_text is None:
                return False
            value = binding.get_object()
            if FlextInfraUtilitiesRopeRuntimeTypes.pymodule(value) and (
                value.get_name() == f"{imported.get_name()}.{binding.imported_name}"
            ):
                # A from-import may publish a submodule without a declaration in
                # its package initializer. Any package-level rebind makes that
                # implicit route unproven.
                rebound = binding.imported_name in imported_scope.get_defined_names()
                value_resource = None if rebound else value.get_resource()
                return (
                    not rebound
                    and value_resource is not None
                    and Path(value_resource.real_path).resolve() in sources
                )
            return cls._stable_binding_chain(
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
            sources: t.MappingKV[Path, str],
            *,
            visited: frozenset[t.Pair[str, str]],
        ) -> bool:
            """Hold the definition site of the resolved binding against rebinds.

            Returns:
                Whether the binding's single declaration stays stable at its owner.

            """
            holder_context = cls._chain_holder_context(binding, project, sources)
            if holder_context is None:
                return False
            if isinstance(binding, p.Infra.RopeImportedModule):
                return True
            holder, line, holder_text = holder_context
            name = expression.rpartition(".")[-1]
            chased = cls._chain_holder_declaration(holder, holder_text, line, name)
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
            matches = tuple(
                FlextInfraUtilitiesRopeRuntimeRefactors.semantic_finder(
                    holder
                ).get_matches("${binding_target} = ${binding_value}", {})
            )
            regions = tuple(
                FlextInfraUtilitiesRopeRuntimeRefactors.semantic_capture_region(
                    match, "binding_value"
                )
                for match in matches
                if declaration.start_offset <= match.get_region()[0]
                and match.get_region()[1] <= declaration.end_offset
            )
            if len(regions) != 1:
                return False
            first, last = regions[0]
            value = cls._binding_expression(holder_text[first:last])
            if value is None:
                return cls._literal_assignment_value(holder_text[first:last])
            # The guard keys the link chased next (the assigned value), never the
            # link already proven: an import hop records (module, name) before this
            # declaration hop holds that same name, which is one chain, not a cycle.
            key = (holder.get_name(), value)
            return key not in visited and cls._stable_binding_chain(
                (project, holder, holder_scope),
                value,
                holder_offset,
                sources,
                visited=visited | {key},
            )

        @staticmethod
        def _chain_holder_context(
            binding: p.Infra.RopePyName,
            project: p.Infra.RopeProject,
            sources: t.MappingKV[Path, str],
        ) -> t.Triple[p.Infra.RopePyModule, int | None, str] | None:
            """Locate the definition site text of one binding inside the project.

            Returns:
                The defining module, its line, and the snapshot text, or ``None``
                when the definition site is unavailable or foreign.

            """
            holder, line = binding.get_definition_location()
            holder_resource = None if holder is None else holder.get_resource()
            if holder_resource is None or holder is None:
                return None
            holder_path = Path(holder_resource.real_path).resolve()
            if holder_path.is_dir():
                holder_path /= c.Infra.INIT_PY
            if not holder_path.is_relative_to(Path(project.root.real_path).resolve()):
                return None
            holder_text = sources.get(holder_path)
            if holder_text is None:
                return None
            return holder, line, holder_text

        @classmethod
        def _chain_holder_declaration(
            cls,
            holder: p.Infra.RopePyModule,
            holder_text: str,
            line: int | None,
            name: str,
        ) -> t.Triple[m.Infra.LogicalStatement, int, p.Infra.RopeScope] | None:
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
            if not cls._single_reaching_binding(
                holder,
                holder_scope,
                name,
                len(holder_text),
            ):
                return None
            return declaration, holder_offset, holder_scope

        @classmethod
        def _single_reaching_binding(
            cls,
            module: p.Infra.RopePyModule,
            scope: p.Infra.RopeScope,
            expression: str,
            offset: int,
            declared_routes: t.StrMapping | None = None,
        ) -> bool:
            """Prove one unconditional declaration instead of Rope's last assignment.

            Returns:
                The resulting ``bool``.
            """
            declarations = cls._single_reaching_declarations(
                module, scope, expression
            )
            if "." in expression:
                return not declarations
            if len(declarations) != 1:
                return False
            declaration, start = declarations[0]
            if start >= offset:
                return False
            return cls._declaration_reaches_unconditionally(
                module, scope, declaration, expression, declared_routes
            )

        @classmethod
        def _single_reaching_declarations(
            cls,
            module: p.Infra.RopePyModule,
            scope: p.Infra.RopeScope,
            expression: str,
        ) -> t.SequenceOf[t.Pair[m.Infra.LogicalStatement, int]]:
            """Collect the frame-local declarations competing with the expression.

            Returns:
                The declarations of the expression's spelling at the scope frame.

            """
            if not isinstance(module, p.Infra.RopeSourceModule):
                return ()
            source = module.source_code
            runtime = FlextInfraUtilitiesRopeRuntimeModules
            rows = FlextInfraUtilitiesRopeStructure.logical_statements(source)
            name = expression.rpartition(".")[-1]
            finder = FlextInfraUtilitiesRopeRuntimeRefactors.lexical_occurrence_finder(
                module.pycore.project, name
            )
            declarations: list[t.Pair[m.Infra.LogicalStatement, int]] = []
            seen: set[t.Pair[int, int]] = set()
            for occurrence in finder.find_occurrences(pymodule=module):
                start, end = occurrence.get_primary_range()
                if cls._binding_expression(source[start:end]) != expression:
                    continue
                row = next(
                    (
                        statement
                        for statement in rows
                        if statement.start_offset <= occurrence.offset
                        < statement.end_offset
                    ),
                    None,
                )
                if row is None:
                    continue
                found_scope = runtime.scope_at(
                    module,
                    occurrence.offset,
                    declaration_line=(
                        row.line
                        if row.category
                        in {
                            c.Infra.StatementCategory.CLASS_DEF,
                            c.Infra.StatementCategory.FUNC_DEF,
                        }
                        else None
                    ),
                )
                if found_scope is not scope and (
                    found_scope.get_kind() != c.Infra.RopeScopeKind.MODULE
                ):
                    continue
                imported = False
                if row.category in {
                    c.Infra.StatementCategory.IMPORT,
                    c.Infra.StatementCategory.FROM_IMPORT,
                }:
                    imported_module = runtime.build_string_module(
                        module.pycore.project, row.text.strip()
                    )
                    imported_scope = imported_module.get_scope()
                    imported = (
                        imported_scope is not None
                        and expression in imported_scope.get_defined_names()
                    )
                assigned = occurrence.is_written() or occurrence.is_defined()
                if row.category == c.Infra.StatementCategory.ANN_ASSIGN:
                    assigned |= (
                        cls._binding_expression(row.text.partition(":")[0])
                        == expression
                    )
                if row.text.lstrip().startswith("del "):
                    assigned = True
                if not (assigned or imported):
                    continue
                key = row.start_offset, occurrence.offset
                if key not in seen:
                    seen.add(key)
                    declarations.append((row, occurrence.offset))
            return declarations

        @staticmethod
        def _declaration_reaches_unconditionally(
            module: p.Infra.RopePyModule,
            scope: p.Infra.RopeScope,
            declaration: m.Infra.LogicalStatement,
            expression: str,
            declared_routes: t.StrMapping | None,
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


__all__: list[str] = ["FlextInfraFlextUtilitiesCodemodBindingChain"]
