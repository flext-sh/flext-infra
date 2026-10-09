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
import sys
from collections.abc import Mapping, MutableMapping
from functools import cache, lru_cache
from importlib.metadata import packages_distributions
from importlib.util import find_spec
from pathlib import Path
from types import MappingProxyType

from flext_cli import u
from packaging.utils import canonicalize_name

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesBase,
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesCodemodRules,
    FlextInfraUtilitiesDeclarationPayload,
    FlextInfraUtilitiesPyproject,
    FlextInfraUtilitiesRopeAnalysisAstHelpers,
    FlextInfraUtilitiesRopeAnalysisExports,
    FlextInfraUtilitiesRopeAnalysisImportState,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeImports,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeSourceBases,
    FlextInfraUtilitiesSemanticCutoverBindings,
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
)

_RESOLVED_SYMBOL_OPERAND_COUNT = 2


class FlextInfraUtilitiesCodemodBindingChain(FlextInfraUtilitiesCodemodRules):
    """Prove one binding chain stable: one reaching declaration per link."""

    @classmethod
    def _stable_binding_chain(
        cls,
        frame: t.Triple[p.Infra.RopeProject, p.Infra.RopePyModule, p.Infra.RopeScope],
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
        routes = FlextInfraUtilitiesRopeSourceBases.lazy_module_aliases(
            module.get_name(), path, text
        )
        if not cls._single_reaching_binding(text, scope, expression, offset, routes):
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
        frame: t.Triple[p.Infra.RopeProject, p.Infra.RopePyModule, p.Infra.RopeScope],
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
        return FlextInfraUtilitiesRopeRuntimeModules.resolve_symbol(scope, expression)

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
                not FlextInfraUtilitiesRopeRuntime.abstract_class(target.get_object())
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
        if not isinstance(imported, p.Infra.RopePyModule):
            return False
        key = (imported.get_name(), binding.imported_name)
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
        if isinstance(value, p.Infra.RopePyModule) and (
            value.get_name() == f"{imported.get_name()}.{binding.imported_name}"
        ):
            # A from-import may publish a submodule without a declaration in
            # its package initializer. Any package-level rebind makes that
            # implicit route unproven.
            rebound = any(
                binding.imported_name
                in FlextInfraUtilitiesSemanticCutoverBindings.bound_identifiers(node)
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
        key = (holder.get_name(), name)
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
        holder_scope = runtime.scope_at(holder, holder_offset, declaration_line=line)
        if not cls._single_reaching_binding(
            holder_text,
            holder_scope,
            ast.Name(id=name, ctx=ast.Load()),
            len(holder_text),
        ):
            return None
        return declaration, holder_offset, holder_scope

    @staticmethod
    def _single_reaching_binding(
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
        declarations = cls._single_reaching_declarations(
            source, scope, expression
        )
        if isinstance(expression, ast.Attribute):
            return not declarations
        if len(declarations) != 1:
            return False
        declaration = declarations[0]
        if isinstance(declaration, ast.arg):
            return False
        start = FlextInfraUtilitiesRopeRuntimeModules.source_offset(source, declaration)
        if start >= offset:
            return False
        return cls._declaration_reaches_unconditionally(
            source, declaration, expression, declared_routes
        )

    @staticmethod
    def _single_reaching_declarations(
        source: str,
        scope: p.Infra.RopeScope,
        expression: ast.expr,
    ) -> list[ast.AST]:
        """Collect the frame-local declarations competing with the expression.

        Returns:
            The declarations of the expression's spelling at the scope frame.

        """
        tree = ast.parse(source)
        parents = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
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
            names = FlextInfraUtilitiesSemanticCutoverBindings.bound_identifiers(node)
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
        source: str,
        declaration: ast.AST,
        expression: ast.expr,
        declared_routes: t.StrMapping | None,
    ) -> bool:
        """Report whether the declaration dominates the queried offset.

        Returns:
            Whether no conditional frame guards the declaration, allowing the
            declared lazy-module routes.

        """
        parents = {
            child: parent
            for parent in ast.walk(ast.parse(source))
            for child in ast.iter_child_nodes(parent)
        }
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


__all__: list[str] = ["FlextInfraUtilitiesCodemodBindingChain"]
