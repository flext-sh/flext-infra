"""Identity-constrained model-field and schema-metadata contract normalization.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import re
from collections.abc import Mapping
from pathlib import Path
from typing import ClassVar, override

from flext_infra import m, p, r
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeModulePatch,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeTypes,
)
from flext_infra._utilities._semantic_cutover.edits import (
    FlextInfraUtilitiesSemanticCutoverEdits,
)


class FlextInfraUtilitiesSemanticModelFieldContracts(
    FlextInfraUtilitiesSemanticCutoverEdits
):
    """Normalize model-typed field annotations and deferred schema metadata."""

    @classmethod
    def plan_computed_model_field_contracts(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: Mapping[Path, str],
        routes: Mapping[str, str],
    ) -> p.Result[tuple[p.Infra.SemanticMigrationEdit, ...]]:
        """Rewrite model fields and eager schemas to deferred protocol contracts.

        Returns:
            The resulting semantic migration edits.

        """
        edits: list[p.Infra.SemanticMigrationEdit] = []
        for path, source in cls._editable_sources(sources):
            if path.suffix != ".py" or cls._is_projection(path):
                continue
            edit = cls._plan_single_file_contract(workspace, path, source, routes)
            if edit is not None:
                edits.append(edit)
        return r[tuple[p.Infra.SemanticMigrationEdit, ...]].ok(tuple(edits))

    @staticmethod
    def _is_projection(path: Path) -> bool:
        """Return whether the path is a generated protocol projection.

        A projection is regenerated from its owner; editing it here would add
        protocol members the runtime-checkable contract cannot carry.

        Returns:
            True for the protocol projection surface of a package.

        """
        return "_protocols" in path.parts or path.name == "protocols.py"

    @classmethod
    def _plan_single_file_contract(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        path: Path,
        source: str,
        routes: Mapping[str, str],
    ) -> p.Infra.SemanticMigrationEdit | None:
        """Plan semantic contract changes for one source file.

        Returns:
            The resulting edit, or None when source remains unchanged.

        """
        tree = ast.parse(source, filename=str(path))
        rewriter = _ModelFieldProtocolRewriter(path, routes, tree)
        transformed = rewriter.visit(tree)
        if not rewriter.changed:
            return None

        updated = cls._patch_file_imports(
            workspace, path, ast.unparse(transformed), rewriter
        )
        if updated == source:
            return None

        return m.Infra.SemanticMigrationEdit(
            file_path=path,
            original_source=source,
            updated_source=updated,
            changes=(
                (
                    "normalized model fields and schema metadata to deferred protocol "
                    "contracts"
                ),
            ),
        )

    @staticmethod
    def resolve_model_protocol(model_str: str, routes: Mapping[str, str]) -> str | None:
        """Resolve a model identity route to its public protocol route.

        A reference resolves by its exact public (``m.X``) or source route, or,
        when dotted, by the one source route it qualifies. No prefix is
        rewritten blindly: a reference outside the route table is not a model.

        Returns:
            The protocol route string, or None if not an admitted model.

        Raises:
            ValueError: The reference qualifies competing protocol routes.

        """
        stripped = model_str.strip()
        if stripped in routes:
            return routes[stripped]
        if "." not in stripped:
            return None
        targets = {
            target
            for candidate, target in routes.items()
            if candidate.endswith(f".{stripped}")
        }
        if len(targets) > 1:
            msg = (
                f"model reference {stripped} qualifies competing protocol routes: "
                f"{sorted(targets)}"
            )
            raise ValueError(msg)
        return next(iter(targets), None)

    @classmethod
    def _patch_file_imports(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        path: Path,
        source: str,
        rewriter: _ModelFieldProtocolRewriter,
    ) -> str:
        """Ensure necessary typing, p, and t imports are present.

        Returns:
            The updated source with missing imports added.

        """
        resource = FlextInfraUtilitiesRopeRuntimeModules.file_resource_at(
            workspace.rope_project, path
        )
        module = FlextInfraUtilitiesRopeRuntimeTypes.require_source_module(
            workspace.rope_project.get_pymodule(resource)
        )
        pkg = FlextInfraUtilitiesRopeAnalysis.package_name_for_module(
            module.get_name(), resource
        )
        return cls._apply_patch_imports(module, source, pkg, rewriter)

    @staticmethod
    def _apply_patch_imports(
        module: p.Infra.RopePyModule,
        source: str,
        pkg: str | None,
        rewriter: _ModelFieldProtocolRewriter,
    ) -> str:
        """Apply from-import additions to one module candidate.

        Returns:
            The resulting source text.

        Raises:
            ValueError: A projected contract needs a facade import outside a package.

        """
        facades = tuple(
            name
            for name, needed in (("p", rewriter.needs_p), ("t", rewriter.needs_t))
            if needed
        )
        if facades and pkg is None:
            msg = f"projected protocol contract has no owning package: {rewriter.path}"
            raise ValueError(msg)
        updated = source
        with FlextInfraUtilitiesRopeModulePatch.candidate_module(
            module, updated
        ) as candidate:
            if rewriter.needs_annotated:
                updated = FlextInfraUtilitiesRopeModulePatch.ensure_from_import(
                    candidate, module="typing", name="Annotated"
                )
            for owner, name in (
                tuple((pkg, name) for name in facades) if pkg is not None else ()
            ):
                updated = FlextInfraUtilitiesRopeModulePatch.ensure_from_import(
                    candidate, module=owner, name=name
                )
        return updated


class _ModelFieldProtocolRewriter(ast.NodeTransformer):
    """Project every model type operand of one module to its protocol route.

    Model fields (direct model-class annotations and computed-field returns)
    keep the model owner directly (``m.X``) at each model operand, nested
    generic arguments included. Every other type position (signatures, local
    and module annotations, type aliases, ``cast`` targets and parameterized
    factories) receives the plain protocol route. Construction, validation
    and schema metadata keep the actual model owner.
    """

    _ANNOTATED: ClassVar[frozenset[str]] = frozenset({"Annotated", "typing.Annotated"})
    _CLASS_VAR: ClassVar[frozenset[str]] = frozenset({"ClassVar", "typing.ClassVar"})
    _LITERAL: ClassVar[frozenset[str]] = frozenset({"Literal", "typing.Literal"})
    _CAST: ClassVar[frozenset[str]] = frozenset({"cast", "typing.cast"})
    _NON_MODEL_M: ClassVar[frozenset[str]] = frozenset({
        "InstanceOf",
        "SettingsConfigDict",
    })

    def __init__(self, path: Path, routes: Mapping[str, str], tree: ast.Module) -> None:
        super().__init__()
        self.path = path
        self.routes = routes
        self.model_roots = frozenset(
            alias.asname or alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
            if alias.name == "m"
        )
        self.model_aliases: dict[str, str] = {
            alias.asname or alias.name: node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
            if alias.name == "m"
        }
        self.fields: set[int] = set()
        self.changed = False
        self.needs_annotated = False
        self.needs_p = False
        self.needs_t = False

    @override
    def visit_Call(self, node: ast.Call) -> ast.AST:
        visited = self.generic_visit(node)
        if not isinstance(visited, ast.Call):
            return visited
        func_name = ast.unparse(visited.func)
        if func_name in self._CAST and visited.args:
            visited.args[0] = self._project(visited.args[0], field=False)
        visited.func = self._project_factory(visited.func)
        for keyword in visited.keywords:
            if keyword.arg == "default_factory":
                keyword.value = self._project_factory(keyword.value)
        return visited

    @override
    def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
        visited = self.generic_visit(node)
        if not isinstance(visited, ast.Attribute):
            return visited
        if visited.attr == "Model":
            val = ast.unparse(visited.value)
            if val == "p" or re.match(r"^Flext\w*Protocols$", val):
                visited.attr = "BaseModel"
                self.changed = True
        elif (
            isinstance(visited.value, ast.Name)
            and visited.value.id == "FlextProtocolsBase"
        ):
            visited.value.id = "FlextProtocolsPydantic"
            if visited.attr == "Model":
                visited.attr = "BaseModel"
            self.changed = True
        return visited

    @override
    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        for tp in getattr(node, "type_params", []):
            default = getattr(tp, "default_value", None)
            if default is not None:
                tp.default_value = self.visit(default)
        is_model = any(
            re.search(
                r"(\bm\.|BaseModel|Models|Model\b|Settings\b)",
                ast.unparse(base),
            )
            for base in node.bases
        )
        if is_model:
            for statement in node.body:
                if isinstance(statement, ast.AnnAssign) or (
                    isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and any(
                        "computed_field" in ast.unparse(decorator)
                        for decorator in statement.decorator_list
                    )
                ):
                    self.fields.add(id(statement))
        return self.generic_visit(node)

    @override
    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AST:
        visited = self.generic_visit(node)
        if not isinstance(visited, ast.AnnAssign):
            return visited
        visited.annotation = self._project(
            visited.annotation, field=id(node) in self.fields
        )
        return visited

    @override
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        return self._visit_signature(node)

    @override
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        return self._visit_signature(node)

    @override
    def visit_TypeAlias(self, node: ast.TypeAlias) -> ast.AST:
        visited = self.generic_visit(node)
        if not isinstance(visited, ast.TypeAlias):
            return visited
        visited.value = self._project(visited.value, field=False)
        return visited

    def _visit_signature(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> ast.AST:
        visited = self.generic_visit(node)
        if not isinstance(visited, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return visited
        arguments = visited.args
        for argument in (
            *arguments.posonlyargs,
            *arguments.args,
            *arguments.kwonlyargs,
            *((arguments.vararg,) if arguments.vararg else ()),
            *((arguments.kwarg,) if arguments.kwarg else ()),
        ):
            if argument.annotation is not None:
                argument.annotation = self._project(argument.annotation, field=False)
        if visited.returns is not None:
            visited.returns = self._project(
                visited.returns, field=id(node) in self.fields
            )
        return visited

    def _project_factory(self, node: ast.expr) -> ast.expr:
        """Project the type operands of a parameterized non-model factory.

        Returns:
            The factory with protocol operands; a model specialization stays.

        """
        if not isinstance(node, ast.Subscript) or self._model_spec(node) is not None:
            return node
        return self._project(node, field=False)

    def _project(self, node: ast.expr, *, field: bool) -> ast.expr:
        """Return ``node`` with each model operand received as its protocol.

        Returns:
            The projected expression, or ``node`` itself when unchanged.

        """
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            parsed = ast.parse(node.value, mode="eval").body
            projected = self._project(parsed, field=field)
            return node if projected is parsed else ast.Constant(ast.unparse(projected))
        spec = self._model_spec(node)
        if spec is not None:
            if field:
                # Simplified: fields use the model directly, not protocol+schema.
                self.changed = True
                return node
            self.changed = True
            self.needs_p = True
            return spec
        if isinstance(node, ast.Subscript):
            return self._project_subscript(node, field=field)
        return self._project_composite(node, field=field)

    def _project_composite(self, node: ast.expr, *, field: bool) -> ast.expr:
        """Project the members of a union, tuple or callable-argument list.

        Returns:
            The projected expression, or ``node`` itself when unchanged.

        """
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            left = self._project(node.left, field=field)
            right = self._project(node.right, field=field)
            if left is node.left and right is node.right:
                return node
            return ast.BinOp(left=left, op=ast.BitOr(), right=right)
        if not isinstance(node, (ast.Tuple, ast.List)):
            return node
        elements = [self._project(elt, field=field) for elt in node.elts]
        if all(new is old for new, old in zip(elements, node.elts, strict=True)):
            return node
        return type(node)(elts=elements, ctx=ast.Load())

    def _project_subscript(self, node: ast.Subscript, *, field: bool) -> ast.expr:
        """Project the type arguments of a non-model generic operand.

        Returns:
            The projected expression, or ``node`` itself when unchanged.

        """
        base = ast.unparse(node.value)
        if base in self._LITERAL:
            return node
        if base in self._ANNOTATED:
            return self._project_annotated(node, field=field)
        projected_slice = self._project(
            node.slice, field=field and base not in self._CLASS_VAR
        )
        if projected_slice is node.slice:
            return node
        return ast.Subscript(value=node.value, slice=projected_slice, ctx=ast.Load())

    def _project_annotated(self, node: ast.Subscript, *, field: bool) -> ast.expr:
        """Project an ``Annotated`` operand while its metadata stays executable.

        Returns:
            The projected ``Annotated`` expression, or ``node`` when unchanged.

        """
        if not (isinstance(node.slice, ast.Tuple) and node.slice.elts):
            return node
        first, *metadata = node.slice.elts
        spec = self._model_spec(first)
        if spec is None:
            projected = self._project(first, field=field)
            if projected is first and not metadata:
                return node
            elements = [projected, *metadata]
            self.changed = True
            if metadata:
                self.needs_annotated = True
            return ast.Subscript(
                value=node.value,
                slice=ast.Tuple(elts=elements, ctx=ast.Load()),
                ctx=ast.Load(),
            )
        if field:
            # Simplified: keep the model operand, drop protocol+schema.
            self.changed = True
            if metadata:
                self.needs_annotated = True
                return ast.Subscript(
                    value=node.value,
                    slice=ast.Tuple(elts=[first, *metadata], ctx=ast.Load()),
                    ctx=ast.Load(),
                )
            return first
        self.needs_p = True
        self.needs_annotated = True
        elements = [spec, *metadata]
        self.changed = True
        return ast.Subscript(
            value=node.value,
            slice=ast.Tuple(elts=elements, ctx=ast.Load()),
            ctx=ast.Load(),
        )

    def _model_spec(self, node: ast.expr) -> ast.expr | None:
        """Return the plain protocol expression of a direct model operand.

        Returns:
            The protocol route (specialized for a generic model), or None.

        Raises:
            ValueError: A model-facade reference has no projected protocol route.

        """
        if isinstance(node, ast.Subscript):
            if isinstance(node.value, (ast.Name, ast.Attribute)):
                base = self._model_spec(node.value)
                if base is not None:
                    return ast.Subscript(
                        value=base,
                        slice=self._project(node.slice, field=False),
                        ctx=ast.Load(),
                    )
            return None
        if not isinstance(node, (ast.Name, ast.Attribute)) or (
            isinstance(node, ast.Attribute) and node.attr in self._NON_MODEL_M
        ):
            return None
        reference = ast.unparse(node)
        protocol = (
            FlextInfraUtilitiesSemanticModelFieldContracts.resolve_model_protocol(
                reference, self.routes
            )
        )
        if protocol is not None:
            return ast.parse(protocol, mode="eval").body
        root = node
        while isinstance(root, ast.Attribute):
            root = root.value
        if isinstance(root, ast.Name) and root.id in self.model_aliases:
            alias_protocol = self._aliased_model_protocol(reference, root.id)
            if alias_protocol is not None:
                return alias_protocol
        if isinstance(node, ast.Attribute) and (
            isinstance(root, ast.Name) and root.id in self.model_roots
        ):
            msg = (
                f"{self.path}:{node.lineno}: model type reference {reference} "
                "has no projected protocol route"
            )
            raise ValueError(msg)
        return None

    def _aliased_model_protocol(self, reference: str, local: str) -> ast.expr | None:
        """Resolve through an `m` facade alias to the owning package route.

        Returns:
            The protocol route, or None when the alias names no model.

        """
        rest = reference[len(local) :]
        candidates: list[str] = []
        module = self.model_aliases.get(local, "")
        if module:
            candidates.append(f"{module}.m{rest}")
        if local != "m":
            candidates.append(f"m{rest}")
        for candidate in candidates:
            protocol = (
                FlextInfraUtilitiesSemanticModelFieldContracts.resolve_model_protocol(
                    candidate, self.routes
                )
            )
            if protocol is not None:
                return ast.parse(protocol, mode="eval").body
        return None


__all__: list[str] = ["FlextInfraUtilitiesSemanticModelFieldContracts"]
