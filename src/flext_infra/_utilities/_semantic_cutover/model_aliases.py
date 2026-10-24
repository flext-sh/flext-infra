"""Retire pure utility namespaces whose attributes alias canonical model types.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path

from flext_infra import c, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesDeclarationPayload,
    FlextInfraUtilitiesSemanticNestingTypes,
)


class FlextInfraUtilitiesSemanticModelAliases:
    """Require declaration identity and complete occurrence proof before inlining."""

    @classmethod
    def plan_model_aliases(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Plan native consumer/import changes; generated exports remain owner-written.

        Returns:
            A complete edit batch, or an actionable unsafe-use failure.

        """
        working = dict(sources)
        candidates = tuple(
            (path, node.name)
            for path, source in sources.items()
            if path.is_relative_to(workspace.repository_root)
            and not source.startswith(c.Infra.AUTOGEN_HEADERS)
            and (
                family
                := FlextInfraUtilitiesCodegenNamespace.facade_family_of_directory(
                    path.parent.name,
                )
            )
            is not None
            and family == c.Infra.FacadeFamily.U
            for node in ast.parse(source).body
            if isinstance(node, ast.ClassDef) and cls._alias_body(node) is not None
        )
        for path, name in candidates:
            project = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
                workspace.rope_project,
                working,
            )
            try:
                cls._retire(project, path, name, working)
            finally:
                project.close()
        return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].ok(
            tuple(
                m.Infra.SemanticMigrationEdit(
                    file_path=path,
                    original_source=source,
                    updated_source=working[path],
                    changes=("native pure utility model-alias retirement",),
                )
                for path, source in sources.items()
                if working[path] != source
            )
        )

    @staticmethod
    def _alias_body(node: ast.ClassDef) -> tuple[ast.Assign, ...] | None:
        if node.bases or node.keywords or node.decorator_list or node.type_params:
            return None
        body = node.body
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(
                body[0].value,
                ast.Constant,
            )
            and isinstance(body[0].value.value, str)
        ):
            body = body[1:]
        if not body or not all(
            isinstance(item, ast.Assign)
            and len(item.targets) == 1
            and isinstance(item.targets[0], ast.Name)
            and isinstance(item.value, ast.Attribute)
            and all(part.isidentifier() for part in ast.unparse(item.value).split("."))
            for item in body
        ):
            return None
        return tuple(item for item in body if isinstance(item, ast.Assign))

    @staticmethod
    def _resource(project: p.Infra.RopeProject, path: Path) -> p.Infra.RopeResource:
        return project.get_resource(
            path.relative_to(Path(project.root.real_path)).as_posix(),
        )

    @classmethod
    def _retire(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        name: str,
        working: t.MutableMappingKV[Path, str],
    ) -> None:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        resource = cls._resource(project, path)
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
        node = next(
            item
            for item in ast.parse(working[path]).body
            if isinstance(item, ast.ClassDef) and item.name == name
        )
        assignments = cls._alias_body(node)
        if assignments is None:
            return
        wrapper = module.get_attribute(name)
        resolved = cls._resolve_alias_targets(project, path, wrapper, assignments)
        if resolved is None:
            return
        aliases, targets = resolved
        consumers = cls._prove_uses(project, wrapper, aliases, targets, working)
        cls._inline_aliases(project, path, name, aliases, working)
        cls._remove_alias_namespace(resource, path, name, working)
        snapshot = runtime.snapshot_project(project, working)
        try:
            organizer = runtime.import_organizer(snapshot)
            for changed in consumers | {path}:
                source = working[changed]
                if source.startswith(c.Infra.AUTOGEN_HEADERS):
                    continue
                native = organizer.organize_imports(cls._resource(snapshot, changed))
                if native is not None:
                    for change in refactors.change_set_members(
                        native.changes,
                        "model-alias import organization returned a non-content change",
                    ).unwrap():
                        working[Path(change.resource.real_path).resolve()] = (
                            change.new_contents
                        )
        finally:
            snapshot.close()

    @classmethod
    def _resolve_alias_targets(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        wrapper: p.Infra.RopePyName,
        assignments: tuple[ast.Assign, ...],
    ) -> tuple[dict[str, p.Infra.RopePyName], dict[str, tuple[str, str]]] | None:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        namespace = FlextInfraUtilitiesRopeRuntimeTypes.require_source_object(
            wrapper.get_object(), str(path)
        )
        scope = namespace.get_scope()
        aliases: dict[str, p.Infra.RopePyName] = {}
        targets: dict[str, tuple[str, str]] = {}
        for assignment in assignments:
            alias = ast.unparse(assignment.targets[0])
            target = runtime.expression_name(scope, ast.unparse(assignment.value))
            if target is None:
                msg = (
                    f"unresolved model alias target: "
                    f"{path}:{namespace.get_name()}.{alias}"
                )
                raise ValueError(msg)
            value = target.get_object()
            if (
                value
                == FlextInfraUtilitiesRopeRuntimeRefactors.runtime_callable(
                    "rope.base.pyobjects", "get_unknown"
                )()
            ):
                msg = f"unresolved model alias target identity: {path}:{alias}"
                raise ValueError(msg)
            if not FlextInfraUtilitiesRopeRuntimeTypes.py_class(value):
                return None
            provider = value.get_module()
            provider_resource = provider.get_resource()
            if provider_resource is None:
                msg = f"model alias target has no source declaration: {path}:{alias}"
                raise ValueError(msg)
            origin = Path(provider_resource.real_path)
            family = FlextInfraUtilitiesCodegenNamespace.facade_family_of_directory(
                origin.parent.name,
            )
            if family != c.Infra.FacadeFamily.M:
                return None
            declarations = FlextInfraUtilitiesDeclarationPayload.declaration_names(
                project,
                origin,
                value.get_name(),
            )
            canonical = tuple(
                qualified
                for qualified in declarations
                for binding in (
                    FlextInfraUtilitiesDeclarationPayload.payload_declaration(
                        project,
                        origin,
                        qualified,
                    ),
                )
                if binding is not None
                and binding.get_object() == value
                and runtime.same_name(binding, target)
            )
            if len(canonical) != 1:
                msg = (
                    f"alias target is not a canonical model declaration: {path}:{alias}"
                )
                raise ValueError(msg)
            aliases[alias] = wrapper.get_object().get_attribute(alias)
            targets[alias] = (provider.get_name(), canonical[0])
        return aliases, targets

    @classmethod
    def _inline_aliases(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        name: str,
        aliases: t.MappingKV[str, p.Infra.RopePyName],
        working: t.MutableMappingKV[Path, str],
    ) -> None:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        # Keep declarations during SDK planning: a last assignment without a
        # docstring must never leave an unparsable empty class in the overlay.
        for alias in aliases:
            snapshot = runtime.snapshot_project(project, working)
            try:
                current = cls._resource(snapshot, path)
                owner = next(
                    item
                    for item in ast.parse(working[path]).body
                    if isinstance(item, ast.ClassDef) and item.name == name
                )
                assignment = next(
                    item
                    for item in owner.body
                    if isinstance(item, ast.Assign)
                    and ast.unparse(item.targets[0]) == alias
                )
                offset = runtime.source_offset(working[path], assignment.targets[0])
                changes = refactors.inline_variable_changes(
                    snapshot,
                    current,
                    offset,
                    resources=tuple(
                        cls._resource(snapshot, item)
                        for item, source in working.items()
                        if not source.startswith(c.Infra.AUTOGEN_HEADERS)
                    ),
                    remove=False,
                )
                for change in refactors.change_set_members(
                    changes.changes,
                    "model-alias inlining returned a non-content change",
                ).unwrap():
                    changed = Path(change.resource.real_path).resolve()
                    if changed not in working:
                        msg = (
                            "model alias consumer is outside captured "
                            f"inventory: {changed}"
                        )
                        raise ValueError(msg)
                    working[changed] = cls._retain_inline_imports(
                        snapshot, current, change, working[changed]
                    )
            finally:
                snapshot.close()

    @staticmethod
    def _retain_inline_imports(
        project: p.Infra.RopeProject,
        origin: p.Infra.RopeResource,
        change: p.Infra.RopeChangeContents,
        source: str,
    ) -> str:
        """Retain authored and still-used imports after a native inline change.

        Returns:
            The native change with only its proven obsolete imports removed.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        before = runtime.build_string_module(project, source, resource=change.resource)
        original_imports = {
            (information.module_name, information.level, binding)
            for statement in runtime.module_imports_for_pymodule(
                project, before
            ).imports
            if isinstance(information := statement.import_info, p.Infra.RopeFromImport)
            for binding in information.names_and_aliases
        }
        after = runtime.build_string_module(
            project, change.new_contents, resource=change.resource
        )
        imports = runtime.module_imports_for_pymodule(project, after)
        used_imports = {
            (information.module_name, information.level, binding)
            for information in imports.get_used_imports(after)
            if isinstance(information, p.Infra.RopeFromImport)
            for binding in information.names_and_aliases
        }
        for statement in imports.imports:
            information = statement.import_info
            if (
                not isinstance(information, p.Infra.RopeFromImport)
                or (
                    project.get_relative_module(
                        information.module_name,
                        change.resource.parent,
                        information.level,
                    )
                    if information.level
                    else project.get_module(information.module_name)
                ).get_resource()
                != origin
            ):
                continue
            retained = tuple(
                binding
                for binding in information.names_and_aliases
                if (key := (information.module_name, information.level, binding))
                in original_imports
                or key in used_imports
            )
            if retained != tuple(information.names_and_aliases):
                statement.import_info = runtime.from_import(
                    information.module_name, information.level, retained
                )
        return imports.get_changed_source()

    @staticmethod
    def _remove_alias_namespace(
        resource: p.Infra.RopeResource,
        path: Path,
        name: str,
        working: t.MutableMappingKV[Path, str],
    ) -> None:
        # The wrapper's own declaration and export are the only authored
        # structural removal; consumer edits above belong entirely to Rope.
        source = working[path]
        tree = ast.parse(source)
        owner = next(
            item
            for item in tree.body
            if isinstance(item, ast.ClassDef) and item.name == name
        )
        lines = source.splitlines(keepends=True)
        begin = sum(map(len, lines[: owner.lineno - 1]))
        end = sum(map(len, lines[: owner.end_lineno]))
        edits = [m.Infra.SourceRewrite(start=begin, end=end, text="")]
        for item in tree.body:
            if isinstance(item, ast.Assign | ast.AnnAssign):
                assign_targets = (
                    item.targets if isinstance(item, ast.Assign) else [item.target]
                )
                if any(
                    isinstance(target, ast.Name) and target.id == "__all__"
                    for target in assign_targets
                ):
                    if not isinstance(item.value, ast.List | ast.Tuple) or any(
                        not isinstance(element, ast.Constant) or element.value != name
                        for element in item.value.elts
                    ):
                        msg = (
                            "model alias namespace has nonexclusive "
                            f"exports: {path}:{name}"
                        )
                        raise ValueError(msg)
                    edits.append(
                        m.Infra.SourceRewrite(
                            start=sum(map(len, lines[: item.lineno - 1])),
                            end=sum(map(len, lines[: item.end_lineno])),
                            text="",
                        )
                    )
        working[path] = FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
            resource, source, edits
        ).new_contents

    @classmethod
    def _prove_uses(
        cls,
        project: p.Infra.RopeProject,
        wrapper: p.Infra.RopePyName,
        aliases: t.MappingKV[str, p.Infra.RopePyName],
        targets: t.MappingKV[str, t.Pair[str, str]],
        sources: t.MutableMappingKV[Path, str],
    ) -> frozenset[Path]:
        name = FlextInfraUtilitiesRopeRuntimeTypes.require_named_object(
            wrapper.get_object(), "model alias namespace"
        ).get_name()
        observed = dict(sources)
        for resource in project.get_python_files():
            path = Path(resource.real_path).resolve()
            if path not in observed:
                source = resource.read()
                if not source.startswith(c.Infra.AUTOGEN_HEADERS):
                    msg = (
                        "model alias proof requires complete workspace "
                        f"source inventory: {path}"
                    )
                    raise ValueError(msg)
                observed[path] = source
        consumers: set[Path] = set()
        for path, source in observed.items():
            resource = cls._resource(project, path)
            tree = ast.parse(source)
            module = FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
            imports, spellings = cls._alias_import_spellings(
                project, resource, module, (source, tree), (name, wrapper, path)
            )
            if cls._prove_alias_occurrences(
                project,
                resource,
                (path, source),
                (wrapper, aliases, spellings, imports),
                editable=path in sources,
            ):
                consumers.add(path)
            if cls._rewrite_alias_annotations(
                project, resource, sources, (path, source), (wrapper, aliases, targets)
            ):
                consumers.add(path)
        return frozenset(consumers)

    @staticmethod
    def _alias_import_spellings(
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        module: p.Infra.RopeParsedModule,
        syntax: tuple[str, ast.Module],
        context: tuple[str, p.Infra.RopePyName, Path],
    ) -> tuple[tuple[ast.Import | ast.ImportFrom, ...], set[str]]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        source, tree = syntax
        name, wrapper, path = context
        imports = tuple(
            item
            for item in ast.walk(tree)
            if isinstance(item, ast.Import | ast.ImportFrom)
        )
        spellings = {name}
        for item in imports:
            if not isinstance(item, ast.ImportFrom) or not any(
                imported.name == name for imported in item.names
            ):
                continue
            provider = FlextInfraUtilitiesRopeRuntime.require_semantic_module(
                project.get_relative_module(
                    item.module or "", resource.parent, item.level
                )
                if item.level
                else project.get_module(item.module or "")
            )
            if not runtime.same_name(wrapper, provider.get_attributes().get(name)):
                continue
            for imported in item.names:
                if imported.name != name:
                    continue
                local = imported.asname or imported.name
                spellings.add(local)
                scope = runtime.scope_at(module, runtime.source_offset(source, item))
                if not runtime.same_name(
                    wrapper, runtime.expression_name(scope, local)
                ):
                    msg = (
                        "model alias namespace import is rebound "
                        f"or ambiguous: {path}:{local}"
                    )
                    raise ValueError(msg)
        return imports, spellings

    @classmethod
    def _prove_alias_occurrences(
        cls,
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        entry: tuple[Path, str],
        context: tuple[
            p.Infra.RopePyName,
            t.MappingKV[str, p.Infra.RopePyName],
            set[str],
            tuple[ast.Import | ast.ImportFrom, ...],
        ],
        *,
        editable: bool,
    ) -> bool:
        path, source = entry
        wrapper, aliases, spellings, imports = context
        consumer = False
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        for spelling in spellings:
            occurrences = (
                occurrence
                for occurrence in refactors.create_occurrence_finder(
                    project,
                    spelling,
                    wrapper,
                    imports=True,
                    in_hierarchy=False,
                ).find_occurrences(resource=resource)
            )
            for occurrence in occurrences:
                if editable and not source.startswith(c.Infra.AUTOGEN_HEADERS):
                    consumer = True
                if occurrence.is_defined() or any(
                    item.lineno <= occurrence.lineno <= (item.end_lineno or item.lineno)
                    for item in imports
                ):
                    continue
                if source.startswith(c.Infra.AUTOGEN_HEADERS):
                    msg = (
                        "model alias has generated behavior, "
                        f"not just exports: {path}:{occurrence.lineno}"
                    )
                    raise ValueError(msg)
                cls._prove_alias_member(project, resource, occurrence, entry, aliases)
        return consumer

    @staticmethod
    def _prove_alias_member(
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        occurrence: p.Infra.RopeOccurrence,
        entry: tuple[Path, str],
        aliases: t.MappingKV[str, p.Infra.RopePyName],
    ) -> None:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        path, source = entry
        end = occurrence.get_word_range()[1]
        # Worder owns the full primary; don't infer attribute identity
        # from its spelling or accept the wrapper as a first-class value.
        if not source[end:].lstrip().startswith("."):
            msg = (
                "model alias namespace escapes as a class "
                f"value: {path}:{occurrence.lineno}"
            )
            raise ValueError(msg)
        # The next member token is obtained from Rope's native lexer.
        words = FlextInfraUtilitiesRopeRuntimeRefactors.runtime_callable(
            "rope.base.worder",
            "Worder",
        )(source)
        if not isinstance(words, p.Infra.RopeWorder):
            msg = "model alias proof requires native Rope Worder"
            raise TypeError(msg)
        member_start = end + len(source[end:]) - len(source[end:].lstrip()) + 1
        member_start += len(source[member_start:]) - len(source[member_start:].lstrip())
        first, last = words.get_word_range(member_start)
        member = source[first:last]
        if member not in aliases or occurrence.is_written():
            msg = (
                "unknown or mutated model alias namespace "
                f"member: {path}:{occurrence.lineno}:{member}"
            )
            raise ValueError(msg)
        scope = runtime.scope_at(
            FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource),
            occurrence.offset,
        )
        primary = occurrence.get_primary_range()[0]
        if not runtime.same_name(
            aliases[member], runtime.expression_name(scope, source[primary:last])
        ):
            msg = (
                f"unproven model alias occurrence: {path}:{occurrence.lineno}:{member}"
            )
            raise ValueError(msg)
        members = FlextInfraUtilitiesRopeRuntimeRefactors.create_occurrence_finder(
            project,
            member,
            aliases[member],
            imports=True,
            in_hierarchy=False,
        )
        if any(
            item.is_written() and not item.is_defined()
            for item in members.find_occurrences(resource=resource)
        ):
            msg = f"mutated model alias member: {path}:{member}"
            raise ValueError(msg)

    @classmethod
    def _rewrite_alias_annotations(
        cls,
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        sources: t.MutableMappingKV[Path, str],
        entry: tuple[Path, str],
        context: tuple[
            p.Infra.RopePyName,
            t.MappingKV[str, p.Infra.RopePyName],
            t.MappingKV[str, t.Pair[str, str]],
        ],
    ) -> bool:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        path, source = entry
        required: set[tuple[str, str]] = set()

        def quoted(
            scope: p.Infra.RopeScope,
            expression: str,
            path: Path = path,
            required: set[tuple[str, str]] = required,
        ) -> str | None:
            return cls._quoted_alias_reference(
                project, scope, expression, (path, required), context
            )

        rewritten = FlextInfraUtilitiesSemanticNestingTypes.rewrite_quoted_types(
            project, resource, source, quoted
        )
        if rewritten == source:
            return False
        if path not in sources or source.startswith(c.Infra.AUTOGEN_HEADERS):
            msg = f"model alias annotation is outside editable source inventory: {path}"
            raise ValueError(msg)
        module = runtime.build_string_module(project, rewritten, resource=resource)
        imports = runtime.module_imports_for_pymodule(project, module)
        for provider, root in sorted(required):
            imports.add_import(runtime.from_import(provider, 0, ((root, None),)))
        sources[path] = imports.get_changed_source()
        return True

    @staticmethod
    def _quoted_alias_reference(
        project: p.Infra.RopeProject,
        scope: p.Infra.RopeScope,
        expression: str,
        entry: tuple[Path, set[tuple[str, str]]],
        context: tuple[
            p.Infra.RopePyName,
            t.MappingKV[str, p.Infra.RopePyName],
            t.MappingKV[str, t.Pair[str, str]],
        ],
    ) -> str | None:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        path, required = entry
        wrapper, aliases, targets = context
        parts = expression.split(".")
        for count in range(1, len(parts) + 1):
            binding = runtime.expression_name(scope, ".".join(parts[:count]))
            if not runtime.same_name(wrapper, binding):
                continue
            if count == len(parts) or parts[count] not in aliases:
                msg = (
                    "quoted model alias namespace escapes or "
                    "selects an unknown member: "
                    f"{path}:{expression}"
                )
                raise ValueError(msg)
            selected = runtime.expression_name(scope, ".".join(parts[: count + 1]))
            if not runtime.same_name(aliases[parts[count]], selected):
                msg = f"unproven quoted model alias: {path}:{expression}"
                raise ValueError(msg)
            provider, qualified = targets[parts[count]]
            root = qualified.partition(".")[0]
            existing = runtime.expression_name(scope, root)
            original = runtime.qualified_name(project, root, module_name=provider)
            if existing is not None and not runtime.same_name(original, existing):
                msg = f"canonical model import is shadowed: {path}:{root}"
                raise ValueError(msg)
            required.add((provider, root))
            return ".".join((qualified, *parts[count + 1 :]))
        return None


__all__: list[str] = ["FlextInfraUtilitiesSemanticModelAliases"]
