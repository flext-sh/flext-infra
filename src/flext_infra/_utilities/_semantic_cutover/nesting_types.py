"""Identity-preserving quoted type edits for class movement and nesting."""

from __future__ import annotations

import ast
from collections.abc import Callable
from pathlib import Path

from flext_infra import m, p, t

from ..rope_runtime_modules import FlextInfraUtilitiesRopeRuntimeModules
from ..rope_runtime_refactors import FlextInfraUtilitiesRopeRuntimeRefactors
from .family_type_references import FlextInfraUtilitiesSemanticFamilyTypeReferences


class FlextInfraUtilitiesSemanticNestingTypes(
    FlextInfraUtilitiesSemanticFamilyTypeReferences
):
    """Share the canonical type-position selector and original Rope scope."""

    @classmethod
    def _rewrite_quoted_types(
        cls,
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        source: str,
        replacement: Callable[[p.Infra.RopeScope, ast.expr], str | None],
        *,
        protected: t.Pair[int, int] | None = None,
    ) -> str:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        module = project.get_pymodule(resource)
        edits: list[m.Infra.SourceRewrite] = []
        for annotation, declaration_line in cls._annotation_roots(ast.parse(source)):
            if (
                protected is not None
                and protected[0] <= annotation.lineno <= protected[1]
            ):
                continue
            start, _ = cls._expression_range(source, annotation)
            scope = runtime.scope_at(module, start, declaration_line=declaration_line)
            for node in cls._type_nodes(annotation, project, scope):
                if not isinstance(node, ast.Constant) or not isinstance(
                    node.value, str
                ):
                    continue
                updated = cls._quoted_replacement(
                    project, resource, scope, node.value, replacement
                )
                if updated != node.value:
                    start, end = cls._expression_range(source, node)
                    edits.append(
                        m.Infra.SourceRewrite(start=start, end=end, text=repr(updated))
                    )
        return FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
            resource, source, edits
        ).new_contents

    @classmethod
    def _quoted_replacement(
        cls,
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        scope: p.Infra.RopeScope,
        source: str,
        replacement: Callable[[p.Infra.RopeScope, ast.expr], str | None],
    ) -> str:
        edits: list[m.Infra.SourceRewrite] = []
        for node in cls._type_nodes(
            ast.parse(source, mode="eval").body, project, scope
        ):
            start, end = cls._expression_range(source, node)
            if any(edit.start <= start and end <= edit.end for edit in edits):
                continue
            text = replacement(scope, node)
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                updated = cls._quoted_replacement(
                    project, resource, scope, node.value, replacement
                )
                if updated != node.value:
                    text = repr(updated)
            if text is not None and text != source[start:end]:
                edits.append(m.Infra.SourceRewrite(start=start, end=end, text=text))
        return FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
            resource, source, edits
        ).new_contents

    @classmethod
    def _nesting_quoted_sources(
        cls,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[Path, str],
        definitions: t.MappingKV[Path, t.StrMapping],
    ) -> t.MappingKV[Path, str]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        root = Path(project.root.real_path)
        bindings = tuple(
            (
                name,
                owner,
                project.get_pymodule(
                    project.get_resource(path.relative_to(root).as_posix())
                ).get_attribute(name),
            )
            for path, names in definitions.items()
            for name, owner in names.items()
        )

        def replacement(scope: p.Infra.RopeScope, node: ast.expr) -> str | None:
            actual = runtime.resolve_symbol(scope, node)
            for name, owner, expected in bindings:
                if not runtime.same_name(expected, actual):
                    continue
                if isinstance(node, ast.Attribute):
                    return f"{ast.unparse(node.value)}.{owner}.{name}"
                if isinstance(node, ast.Name):
                    if isinstance(actual, p.Infra.RopeImportedName):
                        parent = node.id if node.id != actual.imported_name else owner
                        return f"{parent}.{name}"
                    if node.id == name:
                        return f"{owner}.{name}"
            return None

        return {
            path: cls._rewrite_quoted_types(
                project,
                project.get_resource(path.relative_to(root).as_posix()),
                source,
                replacement,
            )
            for path, source in sources.items()
        }


__all__: list[str] = ["FlextInfraUtilitiesSemanticNestingTypes"]
