"""Cached read-only query surface of the shared Rope workspace DSL.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import MutableMapping
from operator import attrgetter
from pathlib import Path
from typing import ClassVar

from flext_infra import c, m, p, t, u


class FlextInfraRopeQueryMixin:
    """Mixin holding the cached read-only query surface of one Rope session.

    The session's caches and the shared Rope project stay owned by the
    concrete workspace class; this mixin only reads them through ``self``.

    """

    _SURFACE_DIRS: ClassVar[t.StrSequence] = (
        c.Infra.DIR_TESTS,
        c.Infra.DIR_EXAMPLES,
        c.Infra.DIR_SCRIPTS,
    )
    _name_index: (
        MutableMapping[str, t.VariadicTuple[t.Triple[Path, str, t.VariadicTuple[int]]]]
        | None
    )
    _import_dependents_index: MutableMapping[str, t.VariadicTuple[Path]] | None

    def semantic(
        self: p.Infra.RopeWorkspaceQueryOwner, file_path: Path
    ) -> p.Infra.ModuleSemanticState:
        """Resolve a module's semantic state through the native Rope query owner.

        Returns:
            The semantic state of the bound module resource.

        """
        return u.Infra.resolve_module_semantic_state(
            self.rope_project,
            self._resource_for(file_path),
        )

    def resource(
        self: p.Infra.RopeWorkspaceQueryOwner, file_path: Path
    ) -> t.Infra.RopeFile | None:
        """Return one cached Rope resource for the requested file path.

        Returns:
            One cached Rope resource for the requested file path.

        """
        cache_key = str(file_path.resolve())
        cached = self._resource_cache.get(cache_key)
        if cache_key in self._resource_cache:
            return cached
        resource = u.Infra.resolve_resource_from_path(self.rope_project, file_path)
        self._resource_cache[cache_key] = resource
        return resource

    def module(
        self: p.Infra.RopeWorkspaceQueryOwner, file_path: Path
    ) -> m.Infra.RopeModuleIndexEntry | None:
        """Return one indexed module entry for the requested file path.

        Returns:
            One indexed module entry for the requested file path.

        """
        raw = self.workspace_index.modules_by_path.get(str(file_path.resolve()))
        if raw is None:
            return None
        validated: m.Infra.RopeModuleIndexEntry = (
            m.Infra.RopeModuleIndexEntry.model_validate(raw)
        )
        return validated

    def package(
        self: p.Infra.RopeWorkspaceQueryOwner, package_dir: Path
    ) -> m.Infra.RopePackageIndexEntry | None:
        """Return one indexed package entry for the requested directory.

        Returns:
            One indexed package entry for the requested directory.

        """
        raw = self.workspace_index.packages_by_dir.get(str(package_dir.resolve()))
        if raw is None:
            return None
        validated: m.Infra.RopePackageIndexEntry = (
            m.Infra.RopePackageIndexEntry.model_validate(raw)
        )
        return validated

    def modules(
        self: p.Infra.RopeWorkspaceQueryOwner,
        *,
        project_names: t.StrSequence | None = None,
    ) -> t.SequenceOf[m.Infra.RopeModuleIndexEntry]:
        """Return path-sorted module entries, optionally only the named projects'.

        Returns:
            Path-sorted module entries, optionally only the named projects'.

        """
        selected = frozenset(project_names or ())
        return tuple(
            sorted(
                (
                    entry
                    for entry in self.workspace_index.modules_by_path.values()
                    if not selected
                    or (
                        entry.project_root is not None
                        and entry.project_root.name in selected
                    )
                ),
                key=attrgetter("file_path"),
            ),
        )

    def source(self: p.Infra.RopeWorkspaceQueryOwner, file_path: Path) -> str:
        """Return one module source snapshot from the active Rope workspace.

        Returns:
            One module source snapshot from the active Rope workspace.

        """
        text: str = self._resource_for(file_path).read()
        return text

    def import_dependents(
        self: p.Infra.RopeWorkspaceQueryOwner, import_target: str
    ) -> t.VariadicTuple[Path]:
        """Return cached module paths that semantically import ``import_target``.

        Returns:
            Cached module paths that semantically import ``import_target``.

        """
        if not import_target:
            return ()
        index = self._import_dependents_index
        if index is None:
            dependents: MutableMapping[str, set[Path]] = defaultdict(set)
            for module in self.modules():
                file_path = module.file_path.resolve()
                for target in self.semantic(file_path).semantic_imports.values():
                    if not target:
                        continue
                    dependents[target].add(file_path)
            index = {
                target: tuple(sorted(paths)) for target, paths in dependents.items()
            }
            self._import_dependents_index = index
        return index.get(import_target, ())

    def name_index(
        self: p.Infra.RopeWorkspaceQueryOwner,
    ) -> t.MappingKV[str, t.VariadicTuple[t.Triple[Path, str, t.VariadicTuple[int]]]]:
        """Return a cached ``{name: ((path, surface, lines), ...)}`` workspace index.

        Built once per workspace session via a single regex scan of every
        indexed ``.py`` module. Short-circuits rope's ``find_occurrences``
        when a symbol's surface distribution alone answers the
        unused classification question.

        Returns:
            A cached ``{name: ((path, surface, lines), ...)}`` workspace index.

        """
        if self._name_index is not None:
            return self._name_index
        index: MutableMapping[str, list[t.Triple[Path, str, list[int]]]] = {}
        for entry in self.workspace_index.modules_by_path.values():
            py_file = entry.file_path
            source_text = self._resource_for(py_file).read()
            surface = self._reference_surface_for(py_file)
            lines_by_name: MutableMapping[str, list[int]] = {}
            for lineno, source_line in enumerate(source_text.splitlines(), start=1):
                for match in self._IDENTIFIER_PATTERN.finditer(source_line):
                    name = match.group(0)
                    lines_by_name.setdefault(name, []).append(lineno)
            for name, line_numbers in lines_by_name.items():
                index.setdefault(name, []).append((py_file, surface, line_numbers))
        self._name_index = {
            name: tuple((path, surface, tuple(lines)) for path, surface, lines in refs)
            for name, refs in index.items()
        }
        return self._name_index

    @classmethod
    def _reference_surface_for(cls, file_path: Path) -> str:
        """Return the reference surface for a file path.

        Returns:
            The reference surface for a file path.

        """
        for part in file_path.parts:
            if part in cls._SURFACE_DIRS:
                surface: str = part
                return surface
        default_src: str = c.Infra.DEFAULT_SRC_DIR
        return default_src

    def objects(
        self: p.Infra.RopeWorkspaceQueryOwner,
        file_path: Path,
        *,
        include_local_scopes: bool = True,
        include_references: bool = True,
    ) -> t.SequenceOf[m.Infra.Object]:
        """Return Rope-only discovered objects for one module path.

        Returns:
            Rope-only discovered objects for one module path.

        """
        resolved_file = file_path.resolve()
        cache_key = (str(resolved_file), include_local_scopes, include_references)
        with u.Infra.cached_source_query(
            self.rope_project,
            self._module_object_cache,
            cache_key,
            self._query_receipts,
            f"objects:{cache_key}",
        ) as cached:
            if cached:
                return self._module_object_cache[cache_key]
            objects = u.Infra.objects(
                self,
                resolved_file,
                include_local_scopes=include_local_scopes,
                include_references=include_references,
            )
            self._module_object_cache[cache_key] = objects
            return objects


__all__: list[str] = ["FlextInfraRopeQueryMixin"]
