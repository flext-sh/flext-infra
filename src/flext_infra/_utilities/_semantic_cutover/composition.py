"""Close native utility composition and its consumers in one source candidate.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Iterator, Mapping, Sequence, Set as AbstractSet
from pathlib import Path

from flext_infra import c, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesWorkspaceSnapshot,
)
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeCorePyModule,
    FlextInfraUtilitiesRopeRuntimeModuleQueries,
    FlextInfraUtilitiesRopeRuntimeRefactors,
)
from flext_infra._utilities._rope._analysis import (
    FlextInfraUtilitiesRopeAnalysisAstHelpers,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesDeclarationPayload,
    FlextInfraUtilitiesSemanticCutoverEdits,
    FlextInfraUtilitiesSemanticCutoverOwnMro,
)


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
    ) -> p.Result[tuple[p.Infra.SemanticMigrationEdit, ...]]:
        """Plan authored MRO dispatch, utility alias retirement and every consumer.

        Returns:
            Complete edits retaining each original source as their before witness.

        """
        authored = dict(cls._editable_sources(sources))
        working = dict(sources)
        with FlextInfraUtilitiesWorkspaceSnapshot.facade_source_project(
            Path(workspace.rope_project.root.real_path),
            planned_sources=working,
            source_project=workspace.rope_project,
        ) as (project, _sources):
            working.update(cls._adopt_pure_facades(workspace, project, working))
            for path in authored:
                working[path] = cls.rewrite_own_method_mro_calls(
                    working[path],
                    source_project=project,
                    file_path=path,
                )[0]
        with FlextInfraUtilitiesWorkspaceSnapshot.facade_source_project(
            Path(workspace.rope_project.root.real_path),
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
        return r[tuple[p.Infra.SemanticMigrationEdit, ...]].ok(
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
    def normalize_test_facades(cls, root: Path) -> tuple[Path, ...]:
        """Normalize the five test facades through the rope workspace.

        Returns:
            The facade paths whose source changed.

        """
        with FlextInfraUtilitiesRopeCore.open_project(root) as project:
            sources = {
                path: path.read_text(encoding=c.DEFAULT_ENCODING)
                for path in (root / c.Infra.DIR_TESTS).glob("*.py")
            }
            changed = cls._compose_test_facades(project, root, sources)
        for path, source in changed.items():
            path.write_text(source, encoding=c.DEFAULT_ENCODING)
        return tuple(changed)

    @classmethod
    def _compose_test_facades(
        cls,
        project: p.Infra.RopeProject,
        root: Path,
        sources: Mapping[Path, str],
    ) -> Mapping[Path, str]:
        """Rewrite test facade MRO through the canonical composition owner.

        Returns:
            The changed test facade sources.

        """
        families = {
            "constants.py": ("c", "Constants"),
            "typings.py": ("t", "Types"),
            "protocols.py": ("p", "Protocols"),
            "models.py": ("m", "Models"),
            "utilities.py": ("u", "Utilities"),
        }
        package = cls._test_facade_package(root)
        changed: dict[Path, str] = {}
        for path, source in sources.items():
            family = families.get(path.name)
            if family is None:
                continue
            letter, suffix = family
            resource = project.get_file(f"{c.Infra.DIR_TESTS}/{path.name}")
            module = FlextInfraUtilitiesRopeCorePyModule.resolve_pymodule(
                project,
                resource,
            )
            rewritten = cls._rewrite_test_facade_source(
                module,
                source,
                package,
                letter,
                suffix,
            )
            if rewritten != source:
                changed[path] = rewritten
        return changed

    @staticmethod
    def _test_facade_package(root: Path) -> str:
        """Resolve the project package that owns the test facades.

        Returns:
            The project package name.

        """
        source_root = root / c.Infra.DEFAULT_SRC_DIR
        for candidate in sorted(source_root.glob("*/__init__.py")):
            package = candidate.parent.name
            if package and not package.startswith("_"):
                return package
        return root.name.replace("-", "_")

    @classmethod
    def _rewrite_test_facade_source(
        cls,
        module: t.Infra.RopeSourceModule,
        source: str,
        package: str,
        letter: str,
        suffix: str,
    ) -> str:
        """Rewrite one test facade header to the canonical MRO.

        Returns:
            The rewritten source.

        """
        package_alias = f"{package}_{letter}"
        tests_alias = f"flext_tests_{letter}"
        outer = next(
            (
                scope
                for scope in module.get_scope().get_scopes()
                if scope.get_kind() == c.Infra.RopeScopeKind.CLASS
                and scope.pyobject.get_name().startswith("Tests")
            ),
            None,
        )
        if outer is None:
            return source
        nested = next(
            (
                scope
                for scope in outer.get_scopes()
                if scope.get_kind() == c.Infra.RopeScopeKind.CLASS
                and scope.pyobject.get_name() == "Tests"
            ),
            None,
        )
        if nested is None:
            return source
        outer_offset = FlextInfraUtilitiesRopeRuntimeModuleQueries.source_offset(
            source,
            outer.pyobject.get_ast(),
        )
        nested_offset = FlextInfraUtilitiesRopeRuntimeModuleQueries.source_offset(
            source,
            nested.pyobject.get_ast(),
        )
        outer_line = source.count("\n", 0, outer_offset) + 1
        nested_line = source.count("\n", 0, nested_offset) + 1
        edits: list[tuple[int, int, str]] = []
        outer_span = cls._class_base_span(source, outer_line)
        if outer_span is not None:
            edits.append((*outer_span, package_alias))
        nested_span = cls._class_base_span(source, nested_line)
        if nested_span is not None:
            bases = cls._split_bases(source[nested_span[0] : nested_span[1]])
            kept = tuple(
                base
                for base in bases
                if not cls._is_old_test_facade_base(base.strip(), suffix)
            )
            replacement = ", ".join((f"{tests_alias}.Tests", *kept))
            edits.append((*nested_span, replacement))
        edits.extend(cls._override_removals(source, nested_line))
        edits.extend(
            cls._test_facade_import_edits(
                source,
                package,
                letter,
                package_alias,
                tests_alias,
            )
        )
        for start, end, replacement in sorted(edits, reverse=True):
            source = source[:start] + replacement + source[end:]
        return source

    @staticmethod
    def _class_base_span(source: str, lineno: int) -> tuple[int, int] | None:
        """Return the character span between a class header's parentheses.

        Returns:
            The base-list span, or ``None`` for a class without bases.

        """
        lines = source.splitlines(keepends=True)
        offset = sum(len(line) for line in lines[: lineno - 1])
        opening = source.find("(", offset)
        if opening < 0:
            return None
        depth = 0
        for index in range(opening, len(source)):
            if source[index] == "(":
                depth += 1
            elif source[index] == ")":
                depth -= 1
                if depth == 0:
                    return opening + 1, index
        return None

    @staticmethod
    def _split_bases(text: str) -> tuple[str, ...]:
        """Split a base list on top-level commas.

        Returns:
            The stripped base expressions.

        """
        bases: list[str] = []
        depth = 0
        start = 0
        for index, character in enumerate(text):
            if character in "([{":
                depth += 1
            elif character in ")]}":
                depth -= 1
            elif character == "," and depth == 0:
                bases.append(text[start:index].strip())
                start = index + 1
        tail = text[start:].strip()
        if tail:
            bases.append(tail)
        return tuple(base for base in bases if base)

    @staticmethod
    def _is_old_test_facade_base(base: str, suffix: str) -> bool:
        """Return whether a base is an old test facade owner.

        Returns:
            ``True`` for the old project or flext-tests facade base.

        """
        if base in {"c", "t", "p", "m", "u"}:
            return True
        if base.startswith(("FlextTests", "flext_tests_")):
            return True
        return base.startswith("Flext") and base.endswith(suffix)

    @classmethod
    def _override_removals(
        cls,
        source: str,
        class_line: int,
    ) -> tuple[tuple[int, int, str], ...]:
        """Return edits removing an ``@override`` decorator above a class.

        Returns:
            The removal edits.

        """
        lines = source.splitlines(keepends=True)
        offset = 0
        edits: list[tuple[int, int, str]] = []
        for index, line in enumerate(lines, start=1):
            if index >= class_line:
                break
            if line.strip() == "@override":
                edits.append((offset, offset + len(line), ""))
            offset += len(line)
        return tuple(edits)

    @classmethod
    def _test_facade_import_edits(
        cls,
        source: str,
        package: str,
        letter: str,
        package_alias: str,
        tests_alias: str,
    ) -> tuple[tuple[int, int, str], ...]:
        """Return edits adding the canonical test facade imports.

        Returns:
            The import insertion edits.

        """
        lines = source.splitlines(keepends=True)
        tests_line = f"from flext_tests import {letter} as {tests_alias}\n"
        package_line = f"from {package} import {letter} as {package_alias}\n"
        has_tests = any(
            line.startswith("from flext_tests import")
            and f"{letter} as {tests_alias}" in line
            for line in lines
        )
        has_package = any(
            line.startswith(f"from {package} import")
            and f"{letter} as {package_alias}" in line
            for line in lines
        )
        missing = "".join(
            line
            for line, present in (
                (tests_line, has_tests),
                (package_line, has_package),
            )
            if not present
        )
        if not missing:
            return ()
        position = 0
        for index, line in enumerate(lines, start=1):
            if line.startswith(("import ", "from ")):
                position = sum(len(item) for item in lines[:index])
        return ((position, position, missing),)

    @classmethod
    def _adopt_pure_facades(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        project: p.Infra.RopeProject,
        sources: Mapping[Path, str],
    ) -> Mapping[Path, str]:
        """Adopt declared pure facades through the existing native projection owner.

        Returns:
            Source plans retaining the original native frames and identities.

        Raises:
            ValueError: The introducing class or facade publication is ambiguous.

        """
        layout = cls.layout(workspace.repository_root, rope_project=project)
        if layout is None:
            message = (
                f"facade adoption has no declared layout: {workspace.repository_root}"
            )
            raise ValueError(message)
        adopted: dict[Path, str] = {}
        for family in cls.facade_families().values():
            path = layout.package_dir / f"{family.module}.py"
            source = sources.get(path)
            if source is None or source.startswith(c.Infra.AUTOGEN_HEADER):
                continue
            name = f"{layout.class_stem}{family.suffix}"
            module = cls._composition_module(project, path)
            if cls._pure_facade_owner(project, module, path, family, name) is None:
                continue
            declared = FlextInfraUtilitiesWorkspaceSnapshot.workspace_declared_sources(
                Path(project.root.real_path),
                (),
                {**sources, **adopted},
                source_project=project,
            )
            projected = workspace.facade_projection(
                declared_files=declared,
                selection=(path, c.Infra.FacadeFamily(family.letter)),
            )
            for plan in projected.files:
                if plan.desired_content is None:
                    message = (
                        f"facade adoption requires a source retirement: {plan.path}"
                    )
                    raise ValueError(message)
                adopted[plan.path] = plan.desired_content.decode(c.DEFAULT_ENCODING)
        return adopted

    @classmethod
    def _pure_facade_owner(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopeParsedModule,
        path: Path,
        family: p.Infra.FacadeFamily,
        name: str,
    ) -> p.Infra.RopeSourceClass | None:
        """Elect the published owner of one pure facade declaration.

        Returns:
            The published owner class, or ``None`` when the module is not a
            pure facade declaration.

        Raises:
            ValueError: The introducing class or publication identity is ambiguous.

        """
        binding = module.get_scope().get_defined_names().get(name)
        if binding is None:
            return None
        owner = binding.get_object()
        if not cls.py_class(owner):
            return None
        if owner.get_module() is not module:
            message = f"facade adoption has a foreign introducing class: {path}:{name}"
            raise ValueError(message)
        exported = cls._declared_exports(path, rope_project=project)
        published = module.get_scope().get_defined_names().get(family.letter)
        if set(exported) != {name, family.letter} or published is None:
            return None
        if published.get_object() is not owner:
            message = f"facade adoption has a different publication identity: {path}"
            raise ValueError(message)
        if (
            not cls._pure_facade_declaration(cls._composition_class_ast(owner))
            or not cls._pure_facade_module(module.get_ast(), name, family.letter)
            or cls._facade_declares_protocols(project, module)
        ):
            return None
        return owner

    @classmethod
    def _facade_declares_protocols(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopeParsedModule,
    ) -> bool:
        """Keep nominal protocol declarations outside managed facade adoption.

        Returns:
            Whether a native class directly declares a standard Protocol base.

        """
        protocols = tuple(
            cls.qualified_name(project, "Protocol", module_name=provider).get_object()
            for provider in ("typing", "typing_extensions")
        )
        return any(
            base in protocols
            for owner in cls._composition_classes(module.get_scope())
            for base in cls.direct_bases(owner)
        )

    @classmethod
    def _pure_facade_declaration(cls, declaration: ast.ClassDef) -> bool:
        """Require a namespace tree with documentation and composition only.

        Returns:
            Whether each nested suite is a pure namespace composition.

        """
        return (
            not declaration.decorator_list
            and not declaration.keywords
            and all(
                isinstance(node, ast.Pass)
                or (
                    isinstance(node, ast.Expr)
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)
                )
                or (
                    isinstance(node, ast.ClassDef)
                    and cls._pure_facade_declaration(node)
                )
                for node in declaration.body
            )
        )

    @classmethod
    def _pure_facade_module(cls, tree: ast.Module, owner: str, alias: str) -> bool:
        """Reject executable module bodies before managed facade adoption.

        Returns:
            Whether the module holds imports, its facade and literal publications.

        """
        return all(
            isinstance(node, (ast.Import, ast.ImportFrom))
            or (isinstance(node, ast.ClassDef) and node.name == owner)
            or (
                isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            )
            or cls._facade_publication(node, owner, alias)
            for node in tree.body
        )

    @staticmethod
    def _facade_publication(node: ast.stmt, owner: str, alias: str) -> bool:
        """Validate standard facade publications without evaluating source.

        Returns:
            Whether a statement binds its facade or literal public exports.

        """
        match node:
            case (
                ast.Assign(targets=[ast.Name(id=name)], value=value)
                | ast.AnnAssign(target=ast.Name(id=name), value=value)
            ):
                pass
            case _:
                return False
        if name == alias:
            return isinstance(value, ast.Name) and value.id == owner
        return (
            name == "__all__"
            and isinstance(value, (ast.Tuple, ast.List))
            and all(
                isinstance(item, ast.Constant) and item.value in {alias, owner}
                for item in value.elts
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
    ) -> dict[tuple[int, int], p.Infra.SourceRewrite]:
        """Rebind method receivers only after their complete native owner proof.

        Returns:
            Authenticated method rewrites keyed by original source coordinates.

        Raises:
            ValueError: A behavior alias escapes as a class identity.

        """
        rewritten: dict[tuple[int, int], p.Infra.SourceRewrite] = {}
        tree = module.get_ast()
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
    ) -> tuple[p.Infra.SourceRewrite, ...]:
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
    ) -> tuple[p.Infra.SourceRewrite, ...]:
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
        edits: tuple[p.Infra.SourceRewrite, ...],
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
    ) -> p.Infra.SourceRewrite:
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
