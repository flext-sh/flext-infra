"""Close native utility composition and its consumers in one source candidate.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Iterator, Mapping, Sequence, Set as AbstractSet
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, r
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesWorkspaceSnapshot,
)
from flext_infra._utilities._rope._analysis.asthelpers import (
    FlextInfraUtilitiesRopeAnalysisAstHelpers,
)
from flext_infra._utilities._rope.runtime_refactors import (
    FlextInfraUtilitiesRopeRuntimeRefactors,
)
from flext_infra._utilities._semantic_cutover.declaration_payload import (
    FlextInfraUtilitiesDeclarationPayload,
)
from flext_infra._utilities._semantic_cutover.edits import (
    FlextInfraUtilitiesSemanticCutoverEdits,
)
from flext_infra._utilities._semantic_cutover.own_mro import (
    FlextInfraUtilitiesSemanticCutoverOwnMro,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraUtilitiesSemanticComposition(
    FlextInfraUtilitiesRopeAnalysisAstHelpers,
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesDeclarationPayload,
    FlextInfraUtilitiesSemanticCutoverOwnMro,
    FlextInfraUtilitiesSemanticCutoverEdits,
):
    """Implement the composition law using native identities and existing edits."""

    @classmethod
    def plan_facade_composition(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: Mapping[Path, str],
    ) -> p.Result[tuple[m.Infra.SemanticMigrationEdit, ...]]:
        """Plan authored MRO dispatch, utility alias retirement and every consumer.

        Returns:
            Complete edits retaining each original source as their before witness.

        """
        authored = dict(cls._editable_sources(sources))
        working = dict(sources)
        with FlextInfraUtilitiesWorkspaceSnapshot.facade_source_project(
            workspace.repository_root,
            planned_sources=working,
            source_project=workspace.rope_project,
        ) as (project, _sources):
            for path, source in authored.items():
                working[path] = cls.rewrite_own_method_mro_calls(
                    source,
                    source_project=project,
                    file_path=path,
                )[0]
        with FlextInfraUtilitiesWorkspaceSnapshot.facade_source_project(
            workspace.repository_root,
            planned_sources=working,
            source_project=workspace.rope_project,
        ) as (project, _sources):
            aliases: list[
                tuple[p.Infra.RopeSourceClass, str, p.Infra.RopeSourceClass, str]
            ] = []
            bases: dict[Path, dict[int, list[str]]] = {}
            retired: dict[Path, set[tuple[int, int]]] = {}
            for path in authored:
                if (
                    cls.facade_family_of_source(
                        path.relative_to(workspace.repository_root)
                    )
                    != c.Infra.FacadeFamily.U
                ):
                    continue
                module = cls._composition_module(project, path)
                selected = cls._composition_aliases(project, module)
                for owner, name, target, expression, span in selected:
                    cls._require_composition_members(owner, target, aliases)
                    aliases.append((owner, name, target, expression))
                    retired.setdefault(path, set()).add(span)
                    if target not in owner.get_superclasses():
                        additions = bases.setdefault(path, {}).setdefault(
                            cls._composition_class_ast(owner).lineno, []
                        )
                        if expression not in additions:
                            additions.append(expression)
            for path in authored:
                module = cls._composition_module(project, path)
                consumers = cls._composition_consumers(module, working[path], aliases)
                working[path] = cls._apply_composition_edits(
                    project,
                    path,
                    working[path],
                    (
                        *cls._retired_statement_rewrites(
                            working[path],
                            frozenset(retired.get(path, set())),
                        ),
                        *cls._class_base_rewrites(
                            working[path],
                            bases.get(path, {}),
                        ),
                        *consumers.values(),
                    ),
                )
        return r[tuple[m.Infra.SemanticMigrationEdit, ...]].ok(
            tuple(
                m.Infra.SemanticMigrationEdit(
                    file_path=path,
                    original_source=source,
                    updated_source=working[path],
                    changes=("resolved native facade composition and consumers",),
                )
                for path, source in authored.items()
                if working[path] != source
            )
        )

    @classmethod
    def _composition_module(
        cls, project: p.Infra.RopeProject, path: Path
    ) -> p.Infra.RopeParsedModule:
        return cls.require_parsed_module(
            project.get_pymodule(cls.file_resource_at(project, path))
        )

    @classmethod
    def _composition_classes(
        cls, scope: p.Infra.RopeScope
    ) -> Iterator[p.Infra.RopeSourceClass]:
        for child in scope.get_scopes():
            if cls.py_class(owner := child.pyobject):
                yield owner
                yield from cls._composition_classes(child)

    @classmethod
    def _composition_aliases(
        cls, project: p.Infra.RopeProject, module: p.Infra.RopeParsedModule
    ) -> Iterator[
        tuple[
            p.Infra.RopeSourceClass,
            str,
            p.Infra.RopeSourceClass,
            str,
            tuple[int, int],
        ]
    ]:
        for owner in cls._composition_classes(module.get_scope()):
            if not cls.utility_namespace_declaration(project, owner):
                continue
            for statement in cls._composition_class_ast(owner).body:
                match statement:
                    case (
                        ast.Assign(
                            targets=[ast.Name(id=name)],
                            value=(ast.Name() | ast.Attribute()) as expression,
                        )
                        | ast.AnnAssign(
                            target=ast.Name(id=name),
                            value=(ast.Name() | ast.Attribute()) as expression,
                        )
                    ):
                        pass
                    case _:
                        continue
                binding = owner.get_scope().get_defined_names().get(name)
                if binding is None:
                    continue
                declared = cls.class_assignment_binding(binding, classes_only=True)
                if declared is None:
                    continue
                target = declared.get_object()
                if cls.py_class(target) and cls.utility_behavior_provider(
                    project, target
                ):
                    span = (statement.lineno, statement.end_lineno or statement.lineno)
                    yield owner, name, target, ast.unparse(expression), span

    @staticmethod
    def _composition_class_ast(owner: p.Infra.RopeSourceClass) -> ast.ClassDef:
        """Require the class syntax belonging to its native declaration.

        Returns:
            The original native class declaration.

        Raises:
            TypeError: The native source class has no class syntax tree.

        """
        declaration = owner.get_ast()
        if not isinstance(declaration, ast.ClassDef):
            message = (
                f"Composition owner has no native class syntax: {owner.get_name()}"
            )
            raise TypeError(message)
        return declaration

    @classmethod
    def _require_composition_members(
        cls,
        owner: p.Infra.RopeSourceClass,
        target: p.Infra.RopeSourceClass,
        aliases: Sequence[
            tuple[p.Infra.RopeSourceClass, str, p.Infra.RopeSourceClass, str]
        ],
    ) -> None:
        """Reject formerly independent namespaces with competing behavior.

        Raises:
            ValueError: Independent providers declare different members by one name.

        """
        members = target.get_attributes()
        for composer, _name, previous, _expression in aliases:
            if composer is not owner or previous is target:
                continue
            for name, binding in previous.get_attributes().items():
                if name.startswith("__") or name not in members:
                    continue
                if not cls.same_name(binding, members[name]):
                    message = (
                        "Ambiguous utility composition member: "
                        f"{owner.get_name()}.{name}; "
                        f"providers={previous.get_name()},{target.get_name()}"
                    )
                    raise ValueError(message)

    @classmethod
    def _composition_consumers(
        cls,
        module: p.Infra.RopeParsedModule,
        source: str,
        aliases: Sequence[
            tuple[p.Infra.RopeSourceClass, str, p.Infra.RopeSourceClass, str]
        ],
    ) -> dict[tuple[int, int], m.Infra.SourceRewrite]:
        """Rebind method receivers only after their complete native owner proof.

        Returns:
            Authenticated method rewrites keyed by original source coordinates.

        Raises:
            ValueError: A behavior alias escapes as a class identity.
            TypeError: If the composition consumer has no native module syntax.

        """
        rewritten: dict[tuple[int, int], m.Infra.SourceRewrite] = {}
        tree = module.get_ast()
        if not isinstance(tree, ast.AST):
            message = "Composition consumer has no native module syntax"
            raise TypeError(message)
        parents = cls.ast_parent_map(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Attribute):
                continue
            for owner, name, target, _expression in aliases:
                if node.attr != name:
                    continue
                scope = cls.scope_at(
                    module,
                    cls.source_offset(source, node),
                    declaration_line=node.lineno,
                )
                composer = cls.resolve_symbol(scope, node.value)
                binding = cls.resolve_symbol(scope, node)
                if (
                    composer is None
                    or all(
                        ancestor is not owner
                        for ancestor in cls.class_ancestry(composer.get_object())
                    )
                    or binding is None
                    or binding.get_object() is not target
                ):
                    continue
                parent = parents[id(node)]
                if (
                    not isinstance(parent, ast.Attribute)
                    or parent.value is not node
                    or parent.attr not in target.get_attributes()
                    or not cls.py_function(
                        target.get_attributes()[parent.attr].get_object()
                    )
                ):
                    message = (
                        "Utility composition alias escapes method dispatch: "
                        f"{module.get_name()}:{node.lineno}:{ast.unparse(node)}"
                    )
                    raise ValueError(message)
                replacement = f"{ast.unparse(node.value)}.{parent.attr}"
                span = cls.node_span_offsets(source, parent)
                if span is None:
                    message = "composition consumer has no complete source span"
                    raise ValueError(message)
                rewritten[parent.lineno, parent.col_offset] = m.Infra.SourceRewrite(
                    start=span[0],
                    end=span[1],
                    text=replacement,
                )
        return rewritten

    @staticmethod
    def _retired_statement_rewrites(
        source: str,
        retired: AbstractSet[tuple[int, int]],
    ) -> tuple[m.Infra.SourceRewrite, ...]:
        """Plan whole-line removal of every retired alias declaration.

        Returns:
            The deletion rewrites for the retired statement line ranges.

        """
        lines = source.splitlines(keepends=True)
        return tuple(
            m.Infra.SourceRewrite(
                start=sum(len(line) for line in lines[: node.lineno - 1]),
                end=sum(len(line) for line in lines[: node.end_lineno or node.lineno]),
                text="",
            )
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Assign | ast.AnnAssign)
            and (node.lineno, node.end_lineno or node.lineno) in retired
        )

    @staticmethod
    def _class_base_rewrites(
        source: str,
        bases: Mapping[int, Sequence[str]],
    ) -> tuple[m.Infra.SourceRewrite, ...]:
        """Plan appending composed bases to their authenticated declarations.

        Returns:
            The insertion rewrites for the composed class bases.

        """
        lines = source.splitlines(keepends=True)
        return tuple(
            FlextInfraUtilitiesSemanticComposition._class_base_addition(
                lines,
                node,
                additions,
            )
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.ClassDef)
            and (additions := bases.get(node.lineno, ()))
        )

    @classmethod
    def _apply_composition_edits(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        source: str,
        edits: tuple[m.Infra.SourceRewrite, ...],
    ) -> str:
        """Apply every authenticated composition edit in one change transaction.

        Returns:
            The rewritten source, unchanged when no edit was authenticated.

        """
        if not edits:
            return source
        return FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
            cls.file_resource_at(project, path),
            source,
            edits,
        ).new_contents

    @staticmethod
    def _class_base_addition(
        lines: Sequence[str],
        declaration: ast.ClassDef,
        additions: Sequence[str],
    ) -> m.Infra.SourceRewrite:
        """Plan appending composed bases to one class declaration header.

        Returns:
            The insertion rewrite after the last declared base, or the rewrite
            opening a base list on a previously bare declaration.

        Raises:
            ValueError: If the declaration or its last base has no complete span.

        """
        rendered = ", ".join(additions)
        if declaration.bases:
            last = declaration.bases[-1]
            if last.end_lineno is None or last.end_col_offset is None:
                msg = "composition base has no complete source span"
                raise ValueError(msg)
            prefix = lines[last.end_lineno - 1].encode(c.DEFAULT_ENCODING)
            end = sum(len(line) for line in lines[: last.end_lineno - 1]) + len(
                prefix[: last.end_col_offset].decode(c.DEFAULT_ENCODING)
            )
            return m.Infra.SourceRewrite(start=end, end=end, text=f", {rendered}")
        line = lines[declaration.lineno - 1]
        column = len(
            line.encode(c.DEFAULT_ENCODING)[: declaration.col_offset].decode(
                c.DEFAULT_ENCODING
            )
        )
        colon = line.index(":", column)
        start = sum(len(item) for item in lines[: declaration.lineno - 1]) + colon
        return m.Infra.SourceRewrite(start=start, end=start + 1, text=f"({rendered}):")


__all__: list[str] = ["FlextInfraUtilitiesSemanticComposition"]
