"""Identity-constrained model-field and schema-metadata contract normalization.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import re
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    pass


class FlextInfraUtilitiesSemanticModelFieldContracts(
    FlextInfraUtilitiesSemanticCutoverEdits
):
    """Normalize model-typed field annotations and deferred schema metadata."""

    @classmethod
    def plan_computed_model_field_contracts(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: Mapping[Path, str],
    ) -> p.Result[tuple[p.Infra.SemanticMigrationEdit, ...]]:
        """Rewrite model fields and eager schemas to deferred protocol contracts.

        Returns:
            The resulting semantic migration edits.

        """
        routes = cls._model_protocol_routes(workspace)
        edits: list[p.Infra.SemanticMigrationEdit] = []
        for path, source in cls._editable_sources(sources):
            if path.suffix != ".py":
                continue
            edit = cls._plan_single_file_contract(workspace, path, source, routes)
            if edit is not None:
                edits.append(edit)
        return r[tuple[p.Infra.SemanticMigrationEdit, ...]].ok(tuple(edits))

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
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None

        rewriter = _ModelFieldProtocolRewriter(routes)
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

    @classmethod
    def _model_protocol_routes(
        cls, workspace: p.Infra.RopeWorkspaceDsl
    ) -> Mapping[str, str]:
        """Obtain model to protocol route mappings from protocol model projection.

        Returns:
            Mapping from model class route to public protocol route.

        """
        from flext_infra._utilities.protocol_models import (
            FlextInfraUtilitiesModelsProtocol,
        )

        routes: dict[str, str] = {}
        try:
            projection = FlextInfraUtilitiesModelsProtocol._ModelProtocolProjection(
                workspace.repository_root,
                source_project=workspace.rope_project,
            )
            pkg = projection.source_package_name
            if projection.package is not None and pkg:
                projection._source_model_facade_owners(projection.package, pkg)
                routes.update(projection.source_model_protocol_routes)
        except (ValueError, KeyError, AttributeError):
            pass
        return routes

    @staticmethod
    def resolve_model_protocol(model_str: str, routes: Mapping[str, str]) -> str | None:
        """Resolve a model name or attribute to its public protocol route.

        Returns:
            The protocol route string, or None if not an admitted model.

        """
        stripped = model_str.strip()
        if stripped in routes:
            return routes[stripped]
        for candidate, target in routes.items():
            if candidate.endswith(f".{stripped}") or stripped.endswith(f".{candidate}"):
                return target
        if stripped.startswith("m."):
            return "p." + stripped[2:]
        return None

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
        try:
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
        except (ValueError, KeyError, AttributeError):
            return source

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

        """
        updated = source
        with FlextInfraUtilitiesRopeModulePatch.candidate_module(
            module, updated
        ) as candidate:
            if rewriter.needs_annotated:
                updated = FlextInfraUtilitiesRopeModulePatch.ensure_from_import(
                    candidate, module="typing", name="Annotated"
                )
            if rewriter.needs_p and pkg:
                updated = FlextInfraUtilitiesRopeModulePatch.ensure_from_import(
                    candidate, module=pkg, name="p"
                )
            if rewriter.needs_t and pkg:
                updated = FlextInfraUtilitiesRopeModulePatch.ensure_from_import(
                    candidate, module=pkg, name="t"
                )
        return updated


class _ModelFieldProtocolRewriter(ast.NodeTransformer):
    """AST rewriter for model fields and schema_for_model calls."""

    def __init__(self, routes: Mapping[str, str]) -> None:
        super().__init__()
        self.routes = routes
        self.in_model = False
        self.changed = False
        self.needs_annotated = False
        self.needs_p = False
        self.needs_t = False

    def visit_Call(self, node: ast.Call) -> ast.AST:
        node = self.generic_visit(node)
        func_name = ast.unparse(node.func)
        is_schema = func_name in {"t.schema_for_model", "schema_for_model"}
        if is_schema and node.args and not isinstance(node.args[0], ast.Lambda):
            node.args[0] = ast.Lambda(
                args=ast.arguments(
                    posonlyargs=[],
                    args=[],
                    kwonlyargs=[],
                    kw_defaults=[],
                    defaults=[],
                ),
                body=node.args[0],
            )
            self.changed = True
            self.needs_t = True
        return node

    def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
        node = self.generic_visit(node)
        if node.attr == "Model":
            val = ast.unparse(node.value)
            if val == "p" or re.match(r"^Flext\w*Protocols$", val):
                node.attr = "BaseModel"
                self.changed = True
        elif isinstance(node.value, ast.Name) and node.value.id == "FlextProtocolsBase":
            node.value.id = "FlextProtocolsPydantic"
            if node.attr == "Model":
                node.attr = "BaseModel"
            self.changed = True
        return node

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
        prev = self.in_model
        self.in_model = self.in_model or is_model
        node = self.generic_visit(node)
        self.in_model = prev
        return node

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AST:
        node = self.generic_visit(node)
        if not self.in_model:
            return node
        annotation = node.annotation
        if self._rewrite_annotated_subscript(annotation):
            self.changed = True
            return node
        unparsed = ast.unparse(annotation)
        protocol = (
            FlextInfraUtilitiesSemanticModelFieldContracts.resolve_model_protocol(
                unparsed, self.routes
            )
        )
        if protocol is not None:
            node.annotation = ast.parse(
                f"Annotated[{protocol}, t.schema_for_model(lambda: {unparsed})]",
                mode="eval",
            ).body
            self.needs_p = True
            self.needs_t = True
            self.needs_annotated = True
            self.changed = True
        return node

    def _rewrite_annotated_subscript(self, annotation: ast.expr) -> bool:
        if not (
            isinstance(annotation, ast.Subscript)
            and ast.unparse(annotation.value) in {"Annotated", "typing.Annotated"}
        ):
            return False
        slice_node = annotation.slice
        if not (isinstance(slice_node, ast.Tuple) and slice_node.elts):
            return False
        first_str = ast.unparse(slice_node.elts[0])
        protocol = (
            FlextInfraUtilitiesSemanticModelFieldContracts.resolve_model_protocol(
                first_str, self.routes
            )
        )
        if protocol is None:
            return False
        slice_node.elts[0] = ast.parse(protocol, mode="eval").body
        has_schema = any(
            "schema_for_model" in ast.unparse(elt) for elt in slice_node.elts[1:]
        )
        if not has_schema:
            schema_call = ast.parse(
                f"t.schema_for_model(lambda: {first_str})", mode="eval"
            ).body
            slice_node.elts.insert(1, schema_call)
            self.needs_t = True
        self.needs_p = True
        self.needs_annotated = True
        return True


__all__: list[str] = ["FlextInfraUtilitiesSemanticModelFieldContracts"]
