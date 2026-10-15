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

import ast
from pathlib import Path
from typing import ClassVar

from flext_cli import cli

from flext_infra import c, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodemodRules,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeTypes,
)
from flext_infra._utilities._rope_source_bases_aliases import (
    FlextInfraUtilitiesRopeSourceBasesAliases,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticCutoverBindings,
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
)


class FlextInfraFlextUtilitiesCodemodBindingChain:
    """Canonical namespace owner."""

    class FlextInfraUtilitiesCodemodBindingChain(FlextInfraUtilitiesCodemodRules):
        """Prove an occurrence's binding: one stable reaching declaration per link."""

        _RESOLVED_SYMBOL_OPERAND_COUNT: ClassVar[int] = 2

        @classmethod
        def codemod_source_import_demands(cls, content: bytes) -> frozenset[str]:
            """Elect an operation's source reads and directly imported bindings.

            The caller supplies the same authenticated bytes captured for its
            real Rope operation. No rule or admission is synthesized.
            """
            tree = ast.parse(content.decode("utf-8"))
            names = set(cls._expression_import_demands(tree))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import | ast.ImportFrom):
                    names.update(
                        alias.asname
                        or (
                            alias.name.partition(".")[0]
                            if isinstance(node, ast.Import)
                            else alias.name
                        )
                        for alias in node.names
                    )
            return cls._member_import_demands(tree, frozenset(names))

        @classmethod
        def _resolved_symbol_import_demands(
            cls,
            source: Path,
            content: bytes,
            admissions: tuple[m.Infra.CodemodAdmission, ...],
        ) -> frozenset[str] | None:
            """Elect consumer names from authenticated resolved-symbol captures.

            Identity predicates observe captured paths and their dependencies.
            Lexical predicates retain the source and the type/subscript receivers
            their existing proof owners read. Shadowing remains proved by Rope.
            """
            occurrence_predicates = {
                c.Infra.CodemodContextPredicate.RESOLVED_SYMBOL,
                c.Infra.CodemodContextPredicate.SAME_BINDING,
                c.Infra.CodemodContextPredicate.EXECUTABLE_OCCURRENCE,
                c.Infra.CodemodContextPredicate.UNREFERENCED_IMPORT,
            }
            conditions = tuple(
                (admission, condition)
                for admission in admissions
                for condition in admission.rule.context
                if condition.predicate in occurrence_predicates
            )
            if not conditions:
                return None
            demanded: set[str] = set()
            for admission, condition in conditions:
                capture = m.Infra.AstGrepCapture.model_validate(
                    admission.captures[condition.variable],
                )
                cls._validated_capture_span(source, capture, content)
                if (
                    condition.predicate
                    is c.Infra.CodemodContextPredicate.UNREFERENCED_IMPORT
                ):
                    # Its owner returns from local AST load analysis before
                    # requesting a Rope module or imported symbol.
                    continue
                expression = ast.parse(capture.text, mode="eval").body
                demanded.update(cls._expression_import_demands(expression))
                if condition.predicate is c.Infra.CodemodContextPredicate.SAME_BINDING:
                    if len(condition.arg) != 1:
                        msg = "same-binding requires one lexical expression"
                        raise ValueError(msg)
                    demanded.update(
                        cls._expression_import_demands(
                            ast.parse(condition.arg[0], mode="eval").body,
                        ),
                    )
            tree = ast.parse(content.decode("utf-8"), filename=str(source))
            if any(
                condition.predicate
                is not c.Infra.CodemodContextPredicate.UNREFERENCED_IMPORT
                for _, condition in conditions
            ):
                # Type-payload classification resolves each subscript receiver;
                # enclosing-subscript stability also reads its index bindings.
                demanded.update(
                    name
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Subscript)
                    for name in cls._expression_import_demands(node)
                )
            return cls._member_import_demands(tree, frozenset(demanded))

        @classmethod
        def _expression_import_demands(cls, expression: ast.AST) -> frozenset[str]:
            """Retain qualified reads without widening each attribute to its root."""
            if isinstance(expression, ast.Name):
                return (
                    frozenset({expression.id})
                    if isinstance(expression.ctx, ast.Load)
                    else frozenset()
                )
            if isinstance(expression, ast.Attribute):
                receivers = cls._expression_import_demands(expression.value)
                return frozenset(f"{receiver}.{expression.attr}" for receiver in receivers)
            return frozenset(
                name
                for child in ast.iter_child_nodes(expression)
                for name in cls._expression_import_demands(child)
            )

        @classmethod
        def _member_import_demands(
            cls,
            tree: ast.Module,
            names: frozenset[str],
        ) -> frozenset[str]:
            """Capture selected declarations, their aliases and inherited providers.

            This elects source dependencies only. The closed Rope graph remains
            responsible for lexical identity, shadowing and MRO verdicts.
            """
            declarations: dict[str, list[ast.AST]] = {}
            parents = {
                child: parent
                for parent in ast.walk(tree)
                for child in ast.iter_child_nodes(parent)
            }
            for node in ast.walk(tree):
                if isinstance(node, ast.Import | ast.ImportFrom):
                    continue
                for name in FlextInfraUtilitiesSemanticCutoverBindings.bound_identifiers(
                    node,
                ):
                    declarations.setdefault(name, []).append(node)
            demanded = set(names)
            pending = list(demanded)
            while pending:
                name = pending.pop()
                head, _, tail = name.partition(".")
                dependencies: set[str] = set()
                for node in declarations.get(head, ()):
                    selected: ast.AST = node
                    remainder = tail
                    while isinstance(selected, ast.ClassDef):
                        dependencies.update(
                            demand
                            for expression in (
                                *selected.decorator_list,
                                *(keyword.value for keyword in selected.keywords),
                            )
                            for demand in cls._expression_import_demands(expression)
                        )
                        for base in selected.bases:
                            expression = base.value if isinstance(base, ast.Subscript) else base
                            dependencies.update(
                                f"{provider}.{remainder}" if remainder else provider
                                for provider in cls._expression_import_demands(expression)
                            )
                        if not remainder:
                            break
                        child_name, _, remainder = remainder.partition(".")
                        children = [
                            child
                            for child in selected.body
                            if child_name
                            in FlextInfraUtilitiesSemanticCutoverBindings.bound_identifiers(
                                child,
                            )
                        ]
                        if len(children) != 1:
                            break
                        selected = children[0]
                    if isinstance(selected, ast.ClassDef):
                        continue
                    if isinstance(selected, ast.FunctionDef | ast.AsyncFunctionDef):
                        dependencies.update(
                            demand
                            for decorator in selected.decorator_list
                            for demand in cls._expression_import_demands(decorator)
                        )
                        if remainder:
                            dependencies.update(
                                f"{provider}.{remainder}"
                                for returned in ast.walk(selected)
                                if isinstance(returned, ast.Return)
                                and returned.value is not None
                                for provider in cls._expression_import_demands(returned.value)
                            )
                        continue
                    value, alias = (
                        FlextInfraUtilitiesSemanticCutoverBindings.bound_value(
                            selected, parents,
                        )
                    )
                    if value is not None:
                        dependencies.update(
                            f"{provider}.{remainder}" if alias and remainder else provider
                            for provider in cls._expression_import_demands(value)
                        )
                for dependency in dependencies:
                    if dependency not in demanded:
                        demanded.add(dependency)
                        pending.append(dependency)
            return frozenset(demanded)

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

            Returns:
                The resulting ``bool``.
            """
            root, source, project = frame
            capture = m.Infra.AstGrepCapture.model_validate(
                captures[condition.variable]
            )
            content = sources[source].encode("utf-8")
            text, start, end = cls._validated_capture_span(source, capture, content)
            tree = ast.parse(text, filename=str(source))
            if not any(
                isinstance(node, ast.expr | ast.Import | ast.ImportFrom)
                and FlextInfraUtilitiesRopeRuntimeModules.source_offset(text, node)
                == start
                and ast.get_source_segment(text, node) == capture.text
                for node in ast.walk(tree)
            ):
                return False
            if (
                condition.predicate
                is c.Infra.CodemodContextPredicate.UNREFERENCED_IMPORT
            ):
                return cls._unreferenced_import_holds(tree, capture.text)
            resource = project.get_resource(
                source.relative_to(root.resolve()).as_posix()
            )
            module = project.get_pymodule(resource)
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
            if (
                condition.predicate
                is c.Infra.CodemodContextPredicate.EXECUTABLE_OCCURRENCE
            ):
                return True
            return cls._resolved_expression_holds(
                (project, module, scope),
                condition,
                capture.text,
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
        def _unreferenced_import_holds(tree: ast.Module, capture_text: str) -> bool:
            """Report whether an import capture has no load references anywhere.

            Returns:
                Whether the single captured import stays unreferenced.

            """
            declarations = ast.parse(capture_text).body
            if len(declarations) != 1 or not isinstance(
                declarations[0], ast.Import | ast.ImportFrom
            ):
                return False
            names = FlextInfraUtilitiesSemanticCutoverBindings.bound_identifiers(
                declarations[0]
            )
            return not any(
                isinstance(node, ast.Name)
                and isinstance(node.ctx, ast.Load)
                and node.id in names
                for node in ast.walk(tree)
            )

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
            for node in ast.walk(ast.parse(text)):
                if not isinstance(node, ast.Subscript):
                    continue
                left, right = (
                    FlextInfraUtilitiesSemanticFamilyTypeReferences.expression_range(
                        text, node
                    )
                )
                if left <= start < end <= right and not cls._stable_binding_chain(
                    (
                        project,
                        module,
                        FlextInfraUtilitiesRopeRuntimeModules.scope_at(module, left),
                    ),
                    node.value,
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
            expression = ast.parse(capture_text, mode="eval").body
            if not isinstance(expression, ast.Name | ast.Attribute):
                return False
            actual = runtime.resolve_symbol(scope, expression)
            if condition.predicate is c.Infra.CodemodContextPredicate.RESOLVED_SYMBOL:
                matched = cls._resolved_symbol_matches(project, condition, actual)
                if not matched:
                    cli.display_text(
                        "mod: binding native chain "
                        + cls._binding_chain_identity(scope, expression),
                    )
                return matched
            if len(condition.arg) != 1:
                msg = "same-binding requires one lexical expression"
                raise ValueError(msg)
            target = condition.arg[0]
            target_expression = ast.parse(target, mode="eval").body
            if not cls._stable_binding_chain(frame, expression, start, sources):
                cli.display_text(
                    f"mod: binding rejection unstable capture={capture_text} "
                    + cls._binding_chain_identity(scope, expression),
                )
                return False
            if not cls._stable_binding_chain(frame, target_expression, start, sources):
                cli.display_text(
                    f"mod: binding rejection unstable target={target} "
                    + cls._binding_chain_identity(scope, target_expression),
                )
                return False
            primary = target_expression
            while isinstance(primary, ast.Attribute):
                primary = primary.value
            if not isinstance(primary, ast.Name):
                return False
            if (
                scope.get_kind() != c.Infra.RopeScopeKind.MODULE
                and primary.id in scope.get_defined_names()
            ):
                # A local assignment/import/parameter can capture the emitted
                # facade even when Rope infers its current value as a class.
                return False
            expected = runtime.resolve_symbol(scope, target_expression)
            holds = cls._binding_symbols_match(expected, actual)
            if not holds:
                cli.display_text(
                    "mod: binding rejection same-binding "
                    f"capture={capture_text} target={target} "
                    f"actual={cls._binding_identity(actual)} "
                    f"expected={cls._binding_identity(expected)}",
                )
            return holds

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
            if len(condition.arg) != cls._RESOLVED_SYMBOL_OPERAND_COUNT:
                msg = "resolved-symbol requires a module and an expression"
                raise ValueError(msg)
            target_module, target = condition.arg
            scope = project.get_module(target_module).get_scope()
            if scope is None:
                return False
            expected = FlextInfraUtilitiesRopeRuntimeModules.resolve_symbol(
                scope,
                ast.parse(target, mode="eval").body,
            )
            holds = cls._binding_symbols_match(expected, actual)
            if not holds:
                cli.display_text(
                    "mod: binding rejection resolved-symbol "
                    f"target={target_module}.{target} "
                    f"actual={cls._binding_identity(actual)} "
                    f"expected={cls._binding_identity(expected)}",
                )
            return holds

        @staticmethod
        def _binding_identity(binding: p.Infra.RopePyName | None) -> str:
            """Describe native identity without substituting an inferred value."""
            if binding is None:
                return "unresolved"
            holder, line = binding.get_definition_location()
            owner = holder.get_name() if holder is not None else "<no-owner>"
            return (
                f"{type(binding).__name__}@{owner}:{line} "
                f"object={type(binding.get_object()).__name__}"
            )

        @classmethod
        def _binding_chain_identity(
            cls,
            scope: p.Infra.RopeScope,
            expression: ast.expr,
        ) -> str:
            """Report each actual native receiver in a rejected attribute chain."""
            links = [expression]
            while isinstance(expression, ast.Attribute):
                expression = expression.value
                links.append(expression)
            return "; ".join(
                f"{ast.unparse(link)}={cls._binding_identity(
                    FlextInfraUtilitiesRopeRuntimeModules.resolve_symbol(scope, link)
                )}"
                for link in reversed(links)
            )

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
        def _stable_binding_chain(
            cls,
            frame: t.Triple[
                p.Infra.RopeProject, p.Infra.RopePyModule, p.Infra.RopeScope
            ],
            expression: ast.expr,
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
                module.get_name(), path, text
            )
            if not cls._single_reaching_binding(
                text, scope, expression, offset, routes
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
            expression: ast.expr,
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
            if isinstance(expression, ast.Attribute):
                if not cls._stable_binding_chain(
                    frame, expression.value, offset, sources, visited=visited
                ):
                    return None
            elif not isinstance(expression, ast.Name):
                return None
            return FlextInfraUtilitiesRopeRuntimeModules.resolve_symbol(
                scope, expression
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
            expression: ast.expr,
            routes: t.StrMapping,
        ) -> bool:
            """Hold the lazy alias route and the single-assignment contract.

            Returns:
                Whether the alias route agrees with the binding and the binding is
                assigned exactly once.

            """
            if isinstance(expression, ast.Name) and expression.id in routes:
                route = project.get_module(routes[expression.id])
                target = route.get_attribute(expression.id)
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
                rebound = any(
                    binding.imported_name
                    in FlextInfraUtilitiesSemanticCutoverBindings.bound_identifiers(
                        node
                    )
                    for node in ast.walk(ast.parse(imported_text))
                )
                value_resource = None if rebound else value.get_resource()
                return (
                    not rebound
                    and value_resource is not None
                    and Path(value_resource.real_path).resolve() in sources
                )
            return cls._stable_binding_chain(
                (project, imported, imported_scope),
                ast.Name(id=binding.imported_name, ctx=ast.Load()),
                len(imported_text),
                sources,
                visited=visited | {key},
            )

        @classmethod
        def _chain_declaration_stable(
            cls,
            project: p.Infra.RopeProject,
            binding: p.Infra.RopePyName,
            expression: ast.expr,
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
            name = (
                expression.attr
                if isinstance(expression, ast.Attribute)
                else expression.id
                if isinstance(expression, ast.Name)
                else ""
            )
            chased = cls._chain_holder_declaration(holder, holder_text, line, name)
            if chased is None:
                return False
            declaration, holder_offset, holder_scope = chased
            if not (
                isinstance(binding, p.Infra.RopeAssignedName)
                and isinstance(declaration, ast.Assign | ast.AnnAssign)
            ):
                return True
            value = declaration.value
            if not isinstance(value, ast.Name | ast.Attribute):
                return isinstance(value, ast.Constant)
            # The guard keys the link chased next (the assigned value), never the
            # link already proven: an import hop records (module, name) before this
            # declaration hop holds that same name, which is one chain, not a cycle.
            key = (holder.get_name(), ast.unparse(value))
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
        ) -> t.Triple[ast.stmt, int, p.Infra.RopeScope] | None:
            """Prove the holder's declaration is the single reaching definition.

            Returns:
                The declaration, its offset, and the holder lexical scope, or
                ``None`` when the declaration is absent or ambiguous.

            """
            runtime = FlextInfraUtilitiesRopeRuntimeModules
            declaration = next(
                (
                    node
                    for node in ast.walk(ast.parse(holder_text))
                    if isinstance(node, ast.stmt) and node.lineno == line
                ),
                None,
            )
            if declaration is None:
                return None
            holder_offset = runtime.source_offset(holder_text, declaration)
            holder_scope = runtime.scope_at(
                holder, holder_offset, declaration_line=line
            )
            if not cls._single_reaching_binding(
                holder_text,
                holder_scope,
                ast.Name(id=name, ctx=ast.Load()),
                len(holder_text),
            ):
                return None
            return declaration, holder_offset, holder_scope

        @classmethod
        def _single_reaching_binding(
            cls,
            source: str,
            scope: p.Infra.RopeScope,
            expression: ast.expr,
            offset: int,
            declared_routes: t.StrMapping | None = None,
        ) -> bool:
            """Prove one unconditional declaration instead of Rope's last assignment.

            Returns:
                The resulting ``bool``.
            """
            tree = ast.parse(source)
            parents = {
                child: parent
                for parent in ast.walk(tree)
                for child in ast.iter_child_nodes(parent)
            }
            declarations = cls._single_reaching_declarations(
                tree, parents, scope, expression
            )
            if isinstance(expression, ast.Attribute):
                return not declarations
            if len(declarations) != 1:
                return False
            declaration = declarations[0]
            if isinstance(declaration, ast.arg):
                return False
            start = FlextInfraUtilitiesRopeRuntimeModules.source_offset(
                source, declaration
            )
            if start >= offset:
                return False
            return cls._declaration_reaches_unconditionally(
                parents, declaration, expression, declared_routes
            )

        @staticmethod
        def _single_reaching_declarations(
            tree: ast.Module,
            parents: t.MappingKV[ast.AST, ast.AST],
            scope: p.Infra.RopeScope,
            expression: ast.expr,
        ) -> list[ast.AST]:
            """Collect the frame-local declarations competing with the expression.

            Returns:
                The declarations of the expression's spelling at the scope frame.

            """
            frames = (
                ast.Module,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
                ast.Lambda,
            )
            spelling = ast.unparse(expression)
            declarations: list[ast.AST] = []
            for node in ast.walk(tree):
                names = FlextInfraUtilitiesSemanticCutoverBindings.bound_identifiers(
                    node
                )
                attribute = isinstance(node, ast.Attribute) and isinstance(
                    node.ctx, ast.Store | ast.Del
                )
                if spelling not in names and not (
                    attribute and ast.unparse(node) == spelling
                ):
                    continue
                parent = parents.get(node)
                while parent is not None and not isinstance(parent, frames):
                    parent = parents.get(parent)
                if parent is not None and (
                    isinstance(parent, ast.Module) or parent.lineno == scope.get_start()
                ):
                    declarations.append(node)
            return declarations

        @staticmethod
        def _declaration_reaches_unconditionally(
            parents: t.MappingKV[ast.AST, ast.AST],
            declaration: ast.AST,
            expression: ast.expr,
            declared_routes: t.StrMapping | None,
        ) -> bool:
            """Report whether the declaration dominates the queried offset.

            Returns:
                Whether no conditional frame guards the declaration, allowing the
                declared lazy-module routes.

            """
            frames = (
                ast.Module,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
                ast.Lambda,
            )
            spelling = ast.unparse(expression)
            parent = parents.get(declaration)
            while parent is not None and not isinstance(parent, frames):
                conditional = isinstance(
                    parent, ast.If | ast.Try | ast.For | ast.While | ast.With
                )
                if conditional and not (
                    isinstance(parent, ast.If)
                    and declared_routes is not None
                    and spelling in declared_routes
                ):
                    return False
                parent = parents.get(parent)
            return True


__all__: list[str] = ["FlextInfraFlextUtilitiesCodemodBindingChain"]
