"""Native module bindings and import changes over the caller's source candidate.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from flext_infra import c, m, p, r
from flext_infra._utilities import FlextInfraUtilitiesWorkspaceSnapshot
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
)
from flext_infra._utilities._rope._analysis import (
    FlextInfraUtilitiesRopeAnalysisExports,
)


class FlextInfraUtilitiesRopeModulePatch:
    """Compose native metadata, refactorings and import planning without effects."""

    @staticmethod
    def runtime_alias_bindings(
        module: p.Infra.RopeSourceModule, *, alias: str
    ) -> tuple[p.Infra.RopeSourceAssignmentLayout, ...]:
        """Return direct assignments without inferring unrelated values."""
        return tuple(
            binding
            for binding in module.get_source_binding_index().assignment_layouts(
                name=alias
            )
            if binding.kind in {"Assign", "AnnAssign"}
        )

    @classmethod
    def facade_letter_names_at(
        cls, project: p.Infra.RopeProject, path: Path
    ) -> frozenset[str]:
        """Read published class aliases through their native bindings.

        Returns:
            The resulting ``frozenset[str]``.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        module = runtime.require_source_object(
            project.get_pymodule(
                runtime.file_resource_at(project, path), force_errors=True
            )
        )
        letters: set[str] = set()
        for name in FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
            module
        ):
            if not name.islower() or name.startswith("_"):
                continue
            if len(cls.runtime_alias_bindings(module, alias=name)) != 1:
                continue
            binding = module.get_source_binding_index().assignment_layouts(
                name=name, resolve_values=True
            )[0]
            root, value = binding.root_binding, binding.value_binding
            if (
                root is not None
                and runtime.abstract_class(root.get_object())
                and value is not None
                and runtime.abstract_class(value.get_object())
            ):
                letters.add(name)
        return frozenset(letters)

    @classmethod
    def remove_runtime_alias_export(
        cls, module: p.Infra.RopeSourceModule, *, alias: str
    ) -> str:
        """Remove one explicit alias through native export metadata.

        Returns:
            The resulting ``str``.

        """
        exports = FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
            module
        )
        return (
            cls.rewrite_all_declaration(
                module, names=[name for name in exports if name != alias]
            )
            if alias in exports
            else module.source_code
        )

    @staticmethod
    def rewrite_all_declaration(
        module: p.Infra.RopeSourceModule, *, names: list[str]
    ) -> str:
        """Replace a unique literal export declaration by native source region.

        Returns:
            The resulting ``str``.

        Raises:
            ValueError: If ambiguous __all__ declarations during facade repair; or if
                facade repair requires an explicit literal __all__ declaration; or if
                export declaration has no source resource.

        """
        declarations = module.get_source_binding_index().assignment_layouts(
            name="__all__"
        )
        if len(declarations) > 1:
            msg = "ambiguous __all__ declarations during facade repair"
            raise ValueError(msg)
        source = module.source_code
        rendered = f"__all__: list[str] = {names!r}"
        if not declarations:
            return source.rstrip() + "\n\n" + rendered + "\n"
        declaration = declarations[0]
        if (
            declaration.kind not in {"Assign", "AnnAssign"}
            or len(declaration.targets) != 1
            or declaration.string_sequence is None
        ):
            msg = "facade repair requires an explicit literal __all__ declaration"
            raise ValueError(msg)
        resource = module.get_resource()
        if resource is None:
            msg = "export declaration has no source resource"
            raise ValueError(msg)
        start, end = declaration.region
        return FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
            resource,
            source,
            (m.Infra.SourceRewrite(start=start, end=end, text=rendered),),
        ).new_contents

    @staticmethod
    def ensure_from_import(
        source_module: p.Infra.RopeSourceModule, *, module: str, name: str
    ) -> str:
        """Delegate insertion and binding reuse to the native import manager.

        Returns:
            The resulting ``str``.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        imports = runtime.module_imports_for_pymodule(
            source_module.pycore.project, source_module
        )
        imports.add_import(runtime.from_import(module, 0, ((name, None),)))
        return imports.get_changed_source()

    @staticmethod
    @contextmanager
    def candidate_module(
        module: p.Infra.RopeSourceModule, source: str
    ) -> Generator[p.Infra.RopeSourceModule]:
        """Retain the complete candidate while binding one changed module.

        Yields:
            Each ``p.Infra.RopeSourceModule``.

        Raises:
            ValueError: If candidate module has no source resource.

        """
        project = module.pycore.project
        resource = module.get_resource()
        if resource is None:
            msg = "candidate module has no source resource"
            raise ValueError(msg)
        path = Path(resource.real_path)
        declarations = FlextInfraUtilitiesWorkspaceSnapshot.workspace_declared_sources(
            Path(project.root.real_path), (), {path: source}, source_project=project
        )
        with project.source_view(
            declared_files=declarations, additional_source_folders=None
        ) as candidate:
            yield FlextInfraUtilitiesRopeRuntime.require_source_object(
                candidate.get_pymodule(candidate.get_resource(resource.path))
            )

    @staticmethod
    def _changed_source(
        module: p.Infra.RopeSourceModule,
        changes: p.Infra.RopeChangeSet | None,
    ) -> str:
        """Read the current resource's native content change.

        Returns:
            The resulting ``str``.

        Raises:
            ValueError: If native module rewrite changed another resource.

        """
        resource = module.get_resource()
        if changes is None or not changes.changes:
            return module.source_code
        selected = tuple(
            change.new_contents
            for change in changes.changes
            if isinstance(change, p.Infra.RopeChangeContents)
            and resource is not None
            and change.resource.real_path == resource.real_path
        )
        if len(selected) != 1 or len(changes.changes) != 1:
            msg = "native module rewrite changed another resource"
            raise ValueError(msg)
        return selected[0]

    @classmethod
    def strip_type_checking_scaffold(
        cls, module: p.Infra.RopeSourceModule
    ) -> p.Result[str]:
        """Retire empty typing guards through native semantic restructuring.

        Returns:
            The native candidate text on the existing typed result boundary.

        Raises:
            ValueError: If typing scaffold has no source resource.

        """
        project = module.pycore.project
        resource = module.get_resource()
        if resource is None:
            msg = "typing scaffold has no source resource"
            raise ValueError(msg)
        source = module.source_code
        for statement in ("pass", "..."):
            with cls.candidate_module(module, source) as candidate:
                changes = FlextInfraUtilitiesRopeRuntimeRefactors.restructure_changes(
                    project,
                    m.Infra.RopeRestructureRequest(
                        pattern=f"if ${{guard}}:\n    {statement}",
                        goal="",
                        arguments={"guard": "name=typing.TYPE_CHECKING"},
                        resources=(resource,),
                    ),
                )
                source = cls._changed_source(candidate, changes)
        with cls.candidate_module(module, source) as candidate:
            runtime = FlextInfraUtilitiesRopeRuntime
            imports = FlextInfraUtilitiesRopeRuntimeModules.module_imports_for_pymodule(
                project, candidate
            )
            original = tuple((item, item.import_info) for item in imports.imports)
            imports.remove_unused_imports()
            for item, before in original:
                retained = frozenset(item.import_info.names_and_aliases)
                if runtime.from_import_info(before) and before.module_name == "typing":
                    item.import_info = runtime.from_import(
                        before.module_name,
                        before.level,
                        tuple(
                            pair
                            for pair in before.names_and_aliases
                            if pair[0] != "TYPE_CHECKING" or pair in retained
                        ),
                    )
                elif runtime.normal_import_info(before):
                    item.import_info = runtime.normal_import(
                        tuple(
                            pair
                            for pair in before.names_and_aliases
                            if pair[0] != "typing" or pair in retained
                        )
                    )
                else:
                    item.import_info = before
            return r[str].ok(imports.get_changed_source())

    @staticmethod
    def _apply_alias_rename(
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        candidate: p.Infra.RopeSourceModule,
        words: p.Infra.RopeWorder,
        fragment: p.Infra.RopeFragment,
        source: str,
        *,
        alias: str,
        original: str,
    ) -> p.Result[str]:
        """Rename one aliased own-package import to its original binding.

        Returns:
            The renamed candidate text, or the typed occupation or no-change
            refusal.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        if resource.exists() and resource.read() != source:
            # The rename offsets belong to the held text epoch; rope computes
            # changes against the resource's own bytes. A divergent epoch
            # would splice foreign content into the candidate — refuse it as
            # typed evidence instead.
            return r[str].fail(
                f"import alias rename raced its source epoch: {resource.real_path}"
            )
        context = candidate.get_source_binding_index().context_at(fragment.start)
        existing = context.environment.lookup(original)
        imported = context.environment.lookup(alias)
        if existing is not None and not runtime.same_name(existing, imported):
            return r[str].fail(f"import alias destination is occupied: {original}")
        offset = words.get_word_range(fragment.end - 1)[0]
        changes = refactors.rename_changes(
            project,
            resource,
            offset,
            original,
            options=m.Infra.RopeRenameOptions(resources=(resource,), docs=False),
        )
        rewritten = FlextInfraUtilitiesRopeModulePatch._changed_source(
            candidate, changes
        )
        if rewritten == source:
            return r[str].fail(f"native import alias rename made no change: {alias}")
        return r[str].ok(value=rewritten)

    @classmethod
    def unalias_own_package_imports(
        cls, module: p.Infra.RopeSourceModule, *, package: str
    ) -> p.Result[str]:
        """Plan imported bindings with expected refusals on the result boundary.

        Returns:
            Native candidate text, or a typed binding-collision/no-change refusal.

        Raises:
            TypeError: If native import aliases require Worder.
            ValueError: If the supplied native module has no source resource.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        project = module.pycore.project
        resource = module.get_resource()
        if resource is None:
            msg = "import alias has no source resource"
            raise ValueError(msg)
        source = module.source_code
        while True:
            with cls.candidate_module(module, source) as candidate:
                words = runtime.runtime_callable("rope.base.worder", "Worder")(source)
                if not isinstance(words, p.Infra.RopeWorder):
                    msg = "native import aliases require Worder"
                    raise TypeError(msg)
                selected = next(
                    (
                        (fragment, alias, original)
                        for fragment in candidate.get_source_binding_index().fragments
                        if words.is_from_aliased(fragment.start)
                        if (provider := words.get_from_module(fragment.start))
                        is not None
                        and (provider == package or provider.startswith(f"{package}."))
                        if (alias := words.get_from_aliased(fragment.start)) is not None
                        and alias not in c.Infra.ALIAS_NAMES
                        if (original := words.get_word_at(fragment.start))
                    ),
                    None,
                )
                if selected is None:
                    return r[str].ok(source)
                fragment, alias, original = selected
                if alias == original:
                    source = refactors.content_change(
                        resource,
                        source,
                        (
                            m.Infra.SourceRewrite(
                                start=fragment.start, end=fragment.end, text=original
                            ),
                        ),
                    ).new_contents
                    continue
                renamed = cls._apply_alias_rename(
                    project,
                    resource,
                    candidate,
                    words,
                    fragment,
                    source,
                    alias=alias,
                    original=original,
                )
                if renamed.failure:
                    return renamed
                source = renamed.value


__all__: list[str] = ["FlextInfraUtilitiesRopeModulePatch"]
