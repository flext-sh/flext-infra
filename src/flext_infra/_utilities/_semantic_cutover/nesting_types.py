"""Identity-preserving native type edits for class movement and nesting.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Callable
from pathlib import Path

from flext_infra import c, m, p, t
from flext_infra._utilities._codemod import FlextInfraUtilitiesCodemodBindingChain
from flext_infra._utilities._rope.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra._utilities._rope.rope_runtime_modules import (
    FlextInfraUtilitiesRopeRuntimeModules,
)
from flext_infra._utilities._rope.rope_runtime_refactors import (
    FlextInfraUtilitiesRopeRuntimeRefactors,
)
from flext_infra._utilities._rope.rope_runtime_types import (
    FlextInfraUtilitiesTypesRopeRuntime,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
)


class FlextInfraUtilitiesTypesSemanticNesting(
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
):
    """Share native annotation regions and original lexical binding identity."""

    @classmethod
    def quoted_type_edits(
        cls,
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        source: str,
        replacement: Callable[[p.Infra.RopeScope, str], str | None],
        *,
        protected: t.Pair[int, int] | None = None,
    ) -> tuple[m.Infra.SourceRewrite, ...]:
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            project,
            FlextInfraUtilitiesTypesRopeRuntime.require_file_resource(
                resource, resource.path
            ),
        )
        edits: list[m.Infra.SourceRewrite] = []
        tree = ast.parse(source)
        generic_scopes = tuple(
            node
            for node in ast.walk(tree)
            if isinstance(
                node,
                ast.TypeAlias | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
            )
            and node.type_params
        )
        constants = cls._quoted_constants(source, tree)
        regions: t.MutableMappingKV[
            t.Pair[int, int], t.Pair[str, p.Infra.RopeScope]
        ] = {}
        for begin, end, _literal, scope in cls.quoted_type_regions(
            source, project, module
        ):
            containing = [
                item for item in constants if item[0] <= begin < end <= item[1]
            ]
            if len(containing) != 1:
                msg = (
                    f"native quoted type has no unique original constant: {begin}:{end}"
                )
                raise ValueError(msg)
            first, last, literal = containing[0]
            regions[first, last] = literal, scope
        for (begin, end), (literal, scope) in regions.items():
            line = module.lines.get_line_number(begin)
            if protected is not None and protected[0] <= line <= protected[1]:
                continue
            parameters = frozenset(
                parameter.name
                for node in generic_scopes
                if node.end_lineno is not None
                and node.lineno <= line <= node.end_lineno
                for parameter in node.type_params
                if isinstance(parameter, c.Infra.AST_TYPE_PARAM_TYPES)
            )

            def scoped_replacement(
                current: p.Infra.RopeScope,
                expression: str,
                shadowed: frozenset[str] = parameters,
            ) -> str | None:
                if expression.partition(".")[0] in shadowed:
                    return None
                return replacement(current, expression)

            changed = cls.rewrite_type_source(
                literal, project, scope, scoped_replacement
            )
            if changed != literal:
                edits.append(
                    m.Infra.SourceRewrite(start=begin, end=end, text=repr(changed))
                )
        return tuple(edits)

    @staticmethod
    def _quoted_constants(
        source: str, tree: ast.Module
    ) -> list[t.Triple[int, int, str]]:
        lines = source.splitlines(keepends=True)
        constants: list[t.Triple[int, int, str]] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            if node.end_lineno is None or node.end_col_offset is None:
                msg = "quoted type constant has no complete original source range"
                raise ValueError(msg)
            end_prefix = (
                lines[node.end_lineno - 1].encode()[: node.end_col_offset].decode()
            )
            constants.append((
                FlextInfraUtilitiesRopeRuntimeModules.source_offset(source, node),
                sum(map(len, lines[: node.end_lineno - 1])) + len(end_prefix),
                node.value,
            ))
        return constants

    @classmethod
    def rewrite_quoted_types(
        cls,
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        source: str,
        replacement: Callable[[p.Infra.RopeScope, str], str | None],
        *,
        protected: t.Pair[int, int] | None = None,
    ) -> str:
        edits = cls.quoted_type_edits(
            project,
            resource,
            source,
            replacement,
            protected=protected,
        )
        return FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
            resource,
            source,
            edits,
        ).new_contents

    @staticmethod
    def require_nesting_binding(
        native: t.Triple[p.Infra.RopeProject, p.Infra.RopePyModule, p.Infra.RopeScope],
        expression: str,
        offset: int,
        sources: t.MappingKV[Path, ...],
    ) -> None:
        """Reuse native reaching-definition proof, including star provenance.

        Raises:
            ValueError: If the nesting binding is ambiguous or dynamic.

        """
        project, module, scope = native
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        chain = FlextInfraUtilitiesCodemodBindingChain
        proof = chain.FlextInfraUtilitiesCodemodBindingChain
        actual = runtime.expression_name(scope, expression)
        if isinstance(actual, p.Infra.RopeImportedName) and not (
            proof.single_reaching_declarations(module, scope, expression)
        ):
            importing = runtime.module_imports_for_pymodule(project, module)
            stars = [
                statement
                for statement in importing.imports
                if isinstance(statement.import_info, p.Infra.RopeFromImport)
                and ("*", None) in statement.import_info.names_and_aliases
                and statement.import_info.module_name
                == actual.imported_module.module_name
                and statement.import_info.level == actual.imported_module.level
            ]
            if len(stars) == 1 and proof.chain_imported_binding(
                project,
                actual,
                sources,
                visited=frozenset(),
            ):
                return
        if not proof.stable_binding_chain(
            (project, module, scope),
            expression,
            offset,
            sources,
        ):
            msg = (
                "ambiguous or dynamic native nesting binding: "
                f"{module.get_name()}.{expression}"
            )
            raise ValueError(msg)

    @staticmethod
    def checked_type_reference(scope: p.Infra.RopeScope, expression: str) -> str:
        if not all(part.isidentifier() for part in expression.split(".")):
            msg = f"quoted type destination is not an identifier chain: {expression}"
            raise TypeError(msg)
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        root = expression.partition(".")[0]
        module = scope.pyobject.get_module()
        if not FlextInfraUtilitiesTypesRopeRuntime.source_module(module):
            msg = "quoted type scope has no declaring module"
            raise ValueError(msg)
        local = runtime.expression_name(scope, root)
        global_binding = runtime.expression_name(module.get_scope(), root)
        if local is not None and (
            global_binding is None or not runtime.same_name(global_binding, local)
        ):
            msg = f"shadowed quoted type destination: {expression}"
            raise ValueError(msg)
        return expression


__all__: list[str] = ["FlextInfraUtilitiesTypesSemanticNesting"]
