"""Native state and cached read-only queries of the Rope workspace DSL.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import MutableMapping
from operator import attrgetter
from pathlib import Path
from time import perf_counter
from typing import ClassVar

from flext_infra import c, m, p, s, t, u


class FlextInfraRopeQueryMixin(s[m.Infra.RopeWorkspaceSession]):
    """Own the native Rope project, structural index, and read-only query caches."""

    _IDENTIFIER_PATTERN: ClassVar[t.RegexPattern] = c.Infra.IDENTIFIER_PATTERN
    _rope_repository_root: Path = m.PrivateAttr()
    _rope_project: t.Infra.RopeProject | None = m.PrivateAttr(
        default_factory=lambda: None,
    )
    _owns_rope_project: bool = m.PrivateAttr(default=True)
    _index_receipt: m.Infra.CodegenPhaseAnalysis | None = m.PrivateAttr(default=None)
    _reused_index: bool = m.PrivateAttr(default=False)
    _workspace_index: m.Infra.RopeWorkspaceIndex | None = m.PrivateAttr(
        default_factory=lambda: None,
    )
    _resource_cache: MutableMapping[str, t.Infra.RopeFile | None] = m.PrivateAttr(
        default_factory=dict[str, t.Infra.RopeFile | None],
    )
    _name_index: (
        MutableMapping[str, t.VariadicTuple[t.Triple[Path, str, t.VariadicTuple[int]]]]
        | None
    ) = m.PrivateAttr(default_factory=lambda: None)
    _import_dependents_index: MutableMapping[str, t.VariadicTuple[Path]] | None = (
        m.PrivateAttr(default_factory=lambda: None)
    )

    _SURFACE_DIRS: ClassVar[t.StrSequence] = (
        c.Infra.DIR_TESTS,
        c.Infra.DIR_EXAMPLES,
        c.Infra.DIR_SCRIPTS,
    )

    @property
    def rope_repository_root(self) -> Path:
        """Canonical root used for the shared Rope project."""
        return self._rope_repository_root

    @property
    def rope_project(self) -> t.Infra.RopeProject:
        """Shared Rope project, opening it lazily once."""
        rope_project = self._rope_project
        if rope_project is None:
            started_at = perf_counter()
            u.Cli.info(f"rope: opening workspace at {self._rope_repository_root}")
            # The session indexes this repository, not its declared submodules.
            rope_project = u.Infra.init_rope_workspace(self._rope_repository_root)
            self._rope_project = rope_project
            u.Cli.info(f"rope: workspace ready in {perf_counter() - started_at:.2f}s")
        return rope_project

    @property
    def workspace_index(self) -> m.Infra.RopeWorkspaceIndex:
        """Cached workspace index for the shared Rope project."""
        workspace_index = self._workspace_index
        if workspace_index is None:
            started_at = perf_counter()
            u.Cli.info(
                f"rope: indexing python workspace at {self._rope_repository_root}",
            )
            with (
                self.rope_project.source_consumption() as consumption,
                self.rope_project.source_selection(),
            ):
                workspace_index = u.Infra.index_rope_workspace(
                    self.rope_project,
                    self.repository_root,
                )
            self._index_receipt = consumption.receipt()
            self._workspace_index = workspace_index
            u.Cli.info(
                "rope: indexed "
                f"{len(workspace_index.package_dirs)} package dirs and "
                f"{len(workspace_index.modules_by_path)} modules in "
                f"{perf_counter() - started_at:.2f}s",
            )
        if self._reused_index:
            self.rope_project.replay_source_consumption(self.source_index_receipt)
            self._reused_index = False
        return workspace_index

    @property
    def source_index_receipt(self) -> m.Infra.CodegenPhaseAnalysis:
        """Require the original authenticated structural-selection receipt.

        Raises:
            ValueError: If the structural index has no original source evidence.

        """
        if self._index_receipt is None:
            msg = "Rope structural index has no original source evidence"
            raise ValueError(msg)
        return self._index_receipt

    def resource(self, file_path: Path) -> t.Infra.RopeFile | None:
        """Resolve one cached live resource or bound planning resource.

        Returns:
            The resource, or ``None`` when absent or outside the workspace.

        """
        if self._owns_rope_project:
            cache_key = str(file_path.resolve())
            cached = self._resource_cache.get(cache_key)
            if cache_key in self._resource_cache:
                return cached
            resource = u.Infra.resolve_resource_from_path(self.rope_project, file_path)
            self._resource_cache[cache_key] = resource
            return resource
        path = file_path.absolute()
        root = self._rope_repository_root.resolve()
        if not path.is_relative_to(root):
            return None
        if not self.rope_project.source_query(path, "isfile"):
            return None
        return u.Infra.require_file_resource(
            self.rope_project.get_resource(path.relative_to(root).as_posix()),
            path,
        )

    def semantic(self, file_path: Path) -> p.Infra.ModuleSemanticState:
        """Resolve a module's semantic state through the native Rope query owner.

        Returns:
            The semantic state of the bound module resource.

        """
        return u.Infra.resolve_module_semantic_state(
            self.rope_project,
            self._resource_for(file_path),
        )

    def module(self, file_path: Path) -> m.Infra.RopeModuleIndexEntry | None:
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

    def package(self, package_dir: Path) -> m.Infra.RopePackageIndexEntry | None:
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
        self,
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

    def source(self, file_path: Path) -> str:
        """Return one module source snapshot from the active Rope workspace.

        Returns:
            One module source snapshot from the active Rope workspace.

        """
        text: str = self._resource_for(file_path).read()
        return text

    def import_dependents(self, import_target: str) -> t.VariadicTuple[Path]:
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
        self,
    ) -> t.MappingKV[str, t.VariadicTuple[t.Triple[Path, str, t.VariadicTuple[int]]]]:
        """Return a cached ``{name: ((path, surface, lines), ...)}`` workspace index.

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

    def _resource_for(self, file_path: Path) -> t.Infra.RopeFile:
        """Require a resource inside the active Rope workspace.

        Returns:
            The bound Rope file resource.

        Raises:
            FileNotFoundError: If a workspace file is absent.
            ValueError: If the path is outside the active workspace.

        """
        resource = self.resource(file_path)
        if resource is not None:
            return resource
        resolved_path = file_path.resolve()
        if (
            resolved_path.is_relative_to(self._rope_repository_root.resolve())
            and not resolved_path.exists()
        ):
            raise FileNotFoundError(resolved_path)
        msg = f"path is outside the active rope workspace: {file_path}"
        raise ValueError(msg)

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


__all__: list[str] = ["FlextInfraRopeQueryMixin"]
