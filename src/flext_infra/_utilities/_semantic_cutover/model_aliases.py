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
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
)
from flext_infra._utilities._semantic_cutover.declaration_payload import (
    FlextInfraUtilitiesDeclarationPayload,
)
from flext_infra._utilities._semantic_cutover.nesting_types import (
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
                family := FlextInfraUtilitiesCodegenNamespace.facade_family_of_directory(
                    path.parent.name,
                )
            ) is not None
            and family == c.Infra.FacadeFamily.U
            for node in ast.parse(source).body
            if isinstance(node, ast.ClassDef) and cls._alias_body(node) is not None
        )
        for path, name in candidates:
            project = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
                workspace.rope_project, working,
            )
            try:
                cls._retire(project, path, name, working)
            finally:
                project.close()
        return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].ok(tuple(
            m.Infra.SemanticMigrationEdit(
                file_path=path, original_source=source, updated_source=working[path],
                changes=("native pure utility model-alias retirement",),
            )
            for path, source in sources.items() if working[path] != source
        ))

    @staticmethod
    def _alias_body(node: ast.ClassDef) -> tuple[ast.Assign, ...] | None:
        if node.bases or node.keywords or node.decorator_list or node.type_params:
            return None
        body = node.body
        if body and isinstance(body[0], ast.Expr) and isinstance(
            body[0].value, ast.Constant,
        ) and isinstance(body[0].value.value, str):
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
        node = next(item for item in ast.parse(working[path]).body
                    if isinstance(item, ast.ClassDef) and item.name == name)
        assignments = cls._alias_body(node)
        if assignments is None:
            return
        wrapper = module.get_attribute(name)
        scope = wrapper.get_object().get_scope()
        if scope is None:
            raise ValueError(f"model alias namespace has no native scope: {path}:{name}")
        aliases: dict[str, p.Infra.RopePyName] = {}
        targets: dict[str, tuple[str, str]] = {}
        for assignment in assignments:
            alias = ast.unparse(assignment.targets[0])
            target = runtime.expression_name(scope, ast.unparse(assignment.value))
            if target is None:
                raise ValueError(f"unresolved model alias target: {path}:{name}.{alias}")
            value = target.get_object()
            if value == refactors.runtime_callable("rope.base.pyobjects", "get_unknown")():
                raise ValueError(f"unresolved model alias target identity: {path}:{alias}")
            if not FlextInfraUtilitiesRopeRuntimeTypes.py_class(value):
                return
            provider = value.get_module()
            provider_resource = None if provider is None else provider.get_resource()
            if provider_resource is None:
                raise ValueError(f"model alias target has no source declaration: {path}:{alias}")
            origin = Path(provider_resource.real_path)
            family = FlextInfraUtilitiesCodegenNamespace.facade_family_of_directory(
                origin.parent.name,
            )
            if family != c.Infra.FacadeFamily.M:
                return
            declarations = FlextInfraUtilitiesDeclarationPayload.declaration_names(
                project, origin, value.get_name(),
            )
            canonical = tuple(
                qualified
                for qualified in declarations
                for binding in (FlextInfraUtilitiesDeclarationPayload.payload_declaration(
                    project, origin, qualified,
                ),)
                if binding is not None and binding.get_object() == value
                and runtime.same_name(binding, target)
            )
            if len(canonical) != 1 or provider is None:
                raise ValueError(f"alias target is not a canonical model declaration: {path}:{alias}")
            aliases[alias] = wrapper.get_object().get_attribute(alias)
            targets[alias] = (provider.get_name(), canonical[0])
        consumers = cls._prove_uses(project, wrapper, aliases, targets, working)
        # Keep declarations during SDK planning: a last assignment without a
        # docstring must never leave an unparsable empty class in the overlay.
        for alias in aliases:
            snapshot = runtime.snapshot_project(project, working)
            try:
                current = cls._resource(snapshot, path)
                owner = next(item for item in ast.parse(working[path]).body
                             if isinstance(item, ast.ClassDef) and item.name == name)
                assignment = next(item for item in owner.body
                                  if isinstance(item, ast.Assign)
                                  and ast.unparse(item.targets[0]) == alias)
                offset = runtime.source_offset(working[path], assignment.targets[0])
                changes = refactors.inline_variable_changes(
                    snapshot, current, offset,
                    resources=tuple(cls._resource(snapshot, item) for item, source in working.items()
                                    if not source.startswith(c.Infra.AUTOGEN_HEADERS)),
                    remove=False,
                )
                for change in refactors.change_set_members(
                    changes.changes, "model-alias inlining returned a non-content change",
                ).unwrap():
                    changed = Path(change.resource.real_path).resolve()
                    if changed not in working:
                        raise ValueError(f"model alias consumer is outside captured inventory: {changed}")
                    working[changed] = change.new_contents
            finally:
                snapshot.close()
        # The wrapper's own declaration and export are the only authored
        # structural removal; consumer edits above belong entirely to Rope.
        source = working[path]
        tree = ast.parse(source)
        owner = next(item for item in tree.body
                     if isinstance(item, ast.ClassDef) and item.name == name)
        lines = source.splitlines(keepends=True)
        begin = sum(map(len, lines[:owner.lineno - 1]))
        end = sum(map(len, lines[:owner.end_lineno]))
        edits = [m.Infra.SourceRewrite(start=begin, end=end, text="")]
        for item in tree.body:
            if isinstance(item, ast.Assign | ast.AnnAssign):
                targets = item.targets if isinstance(item, ast.Assign) else [item.target]
                if any(isinstance(target, ast.Name) and target.id == "__all__" for target in targets):
                    if not isinstance(item.value, ast.List | ast.Tuple) or any(
                        not isinstance(element, ast.Constant) or element.value != name
                        for element in item.value.elts
                    ):
                        raise ValueError(f"model alias namespace has nonexclusive exports: {path}:{name}")
                    edits.append(m.Infra.SourceRewrite(
                        start=sum(map(len, lines[:item.lineno - 1])),
                        end=sum(map(len, lines[:item.end_lineno])), text="",
                    ))
        working[path] = refactors.content_change(resource, source, edits).new_contents
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
                        native.changes, "model-alias import organization returned a non-content change",
                    ).unwrap():
                        working[Path(change.resource.real_path).resolve()] = change.new_contents
        finally:
            snapshot.close()

    @classmethod
    def _prove_uses(
        cls,
        project: p.Infra.RopeProject,
        wrapper: p.Infra.RopePyName,
        aliases: t.MappingKV[str, p.Infra.RopePyName],
        targets: t.MappingKV[str, t.Pair[str, str]],
        sources: t.MutableMappingKV[Path, str],
    ) -> frozenset[Path]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        name = wrapper.get_object().get_name()
        observed = dict(sources)
        for resource in project.get_python_files():
            path = Path(resource.real_path).resolve()
            if path not in observed:
                source = resource.read()
                if not source.startswith(c.Infra.AUTOGEN_HEADERS):
                    raise ValueError(f"model alias proof requires complete workspace source inventory: {path}")
                observed[path] = source
        consumers: set[Path] = set()
        for path, source in observed.items():
            resource = cls._resource(project, path)
            tree = ast.parse(source)
            imports = tuple(item for item in ast.walk(tree)
                            if isinstance(item, ast.Import | ast.ImportFrom))
            module = FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
            spellings = {name}
            for item in imports:
                if not isinstance(item, ast.ImportFrom) or not any(
                    imported.name == name for imported in item.names
                ):
                    continue
                provider = (
                    project.get_relative_module(item.module or "", resource.parent, item.level)
                    if item.level else project.get_module(item.module or "")
                )
                if not runtime.same_name(wrapper, provider.get_attributes().get(name)):
                    continue
                for imported in item.names:
                    if imported.name != name:
                        continue
                    local = imported.asname or imported.name
                    spellings.add(local)
                    scope = runtime.scope_at(module, runtime.source_offset(source, item))
                    if not runtime.same_name(wrapper, runtime.expression_name(scope, local)):
                        raise ValueError(f"model alias namespace import is rebound or ambiguous: {path}:{local}")
            occurrences = (
                occurrence
                for spelling in spellings
                for occurrence in refactors.create_occurrence_finder(
                    project, spelling, wrapper, imports=True, in_hierarchy=False,
                ).find_occurrences(resource=resource)
            )
            for occurrence in occurrences:
                if path in sources and not source.startswith(c.Infra.AUTOGEN_HEADERS):
                    consumers.add(path)
                if occurrence.is_defined() or any(
                    item.lineno <= occurrence.lineno <= (item.end_lineno or item.lineno)
                    for item in imports
                ):
                    continue
                if source.startswith(c.Infra.AUTOGEN_HEADERS):
                    raise ValueError(f"model alias has generated behavior, not just exports: {path}:{occurrence.lineno}")
                _start, end = occurrence.get_word_range()
                suffix = source[end:].lstrip()
                # Worder owns the full primary; don't infer attribute identity
                # from its spelling or accept the wrapper as a first-class value.
                if not suffix.startswith("."):
                    raise ValueError(f"model alias namespace escapes as a class value: {path}:{occurrence.lineno}")
                # The next member token is obtained from Rope's native lexer.
                words = FlextInfraUtilitiesRopeRuntimeRefactors.runtime_callable(
                    "rope.base.worder", "Worder",
                )(source)
                if not isinstance(words, p.Infra.RopeWorder):
                    raise TypeError("model alias proof requires native Rope Worder")
                member_start = end + len(source[end:]) - len(source[end:].lstrip()) + 1
                member_start += len(source[member_start:]) - len(source[member_start:].lstrip())
                first, last = words.get_word_range(member_start)
                member = source[first:last]
                if member not in aliases or occurrence.is_written():
                    raise ValueError(f"unknown or mutated model alias namespace member: {path}:{occurrence.lineno}:{member}")
                module = FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
                scope = runtime.scope_at(module, occurrence.offset)
                primary, _finish = occurrence.get_primary_range()
                selected = runtime.expression_name(scope, source[primary:last])
                if not runtime.same_name(aliases[member], selected):
                    raise ValueError(f"unproven model alias occurrence: {path}:{occurrence.lineno}:{member}")
                members = FlextInfraUtilitiesRopeRuntimeRefactors.create_occurrence_finder(
                    project, member, aliases[member], imports=True, in_hierarchy=False,
                )
                if any(item.is_written() and not item.is_defined()
                       for item in members.find_occurrences(resource=resource)):
                    raise ValueError(f"mutated model alias member: {path}:{member}")
            required: set[tuple[str, str]] = set()

            def quoted(scope: p.Infra.RopeScope, expression: str) -> str | None:
                parts = expression.split(".")
                for count in range(1, len(parts) + 1):
                    binding = runtime.expression_name(scope, ".".join(parts[:count]))
                    if not runtime.same_name(wrapper, binding):
                        continue
                    if count == len(parts) or parts[count] not in aliases:
                        raise ValueError(f"quoted model alias namespace escapes or selects an unknown member: {path}:{expression}")
                    alias = parts[count]
                    selected = runtime.expression_name(scope, ".".join(parts[:count + 1]))
                    if not runtime.same_name(aliases[alias], selected):
                        raise ValueError(f"unproven quoted model alias: {path}:{expression}")
                    provider, qualified = targets[alias]
                    root = qualified.partition(".")[0]
                    existing = runtime.expression_name(scope, root)
                    original = runtime.qualified_name(project, root, module_name=provider)
                    if existing is not None and not runtime.same_name(original, existing):
                        raise ValueError(f"canonical model import is shadowed: {path}:{root}")
                    required.add((provider, root))
                    return ".".join((qualified, *parts[count + 1:]))
                return None

            rewritten = FlextInfraUtilitiesSemanticNestingTypes._rewrite_quoted_types(
                project, resource, source, quoted,
            )
            if rewritten != source:
                if path not in sources or source.startswith(c.Infra.AUTOGEN_HEADERS):
                    raise ValueError(f"model alias annotation is outside editable source inventory: {path}")
                module = runtime.build_string_module(project, rewritten, resource=resource)
                imports = runtime.module_imports_for_pymodule(project, module)
                for provider, root in sorted(required):
                    imports.add_import(runtime.from_import(provider, 0, ((root, None),)))
                sources[path] = imports.get_changed_source()
                consumers.add(path)
        return frozenset(consumers)


__all__: list[str] = ["FlextInfraUtilitiesSemanticModelAliases"]
