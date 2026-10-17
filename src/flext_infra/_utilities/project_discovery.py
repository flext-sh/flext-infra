"""Project discovery helpers for flext-infra utilities.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from operator import attrgetter
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, config, m, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesGit,
    FlextInfraUtilitiesIterationDirectory,
    FlextInfraUtilitiesProjectDiscoveryCandidatesMixin,
    FlextInfraUtilitiesProjectManagedArtifacts,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from flext_infra import p


class FlextInfraUtilitiesProjectDiscovery(
    FlextInfraUtilitiesProjectDiscoveryCandidatesMixin,
):
    """Static helpers for discovering governed project roots in a workspace."""

    @staticmethod
    def repository_operation_targets(
        root: Path,
        scope: c.Infra.CodegenConformScope,
    ) -> p.Result[t.SequenceOf[m.Infra.WorkspaceOperationTarget]]:
        """Retain declared roots, including missing checkouts, in discovery order.

        Returns:
            The declared roots in discovery order.

        """
        resolved = root.expanduser().resolve()
        result_type = r[t.SequenceOf[m.Infra.WorkspaceOperationTarget]]
        if not resolved.is_dir():
            return result_type.fail(f"operation root does not exist: {resolved}")
        target = m.Infra.WorkspaceOperationTarget(root=resolved)
        if scope == c.Infra.CodegenConformScope.SELF:
            return result_type.ok((target,))
        if scope != c.Infra.CodegenConformScope.ALL:
            return result_type.fail(f"operation scope must be self or all: {scope}")
        declared = FlextInfraUtilitiesGit.git_submodule_declarations(resolved)
        if declared.failure:
            return result_type.from_failure(declared)
        return result_type.ok((
            target,
            *(
                m.Infra.WorkspaceOperationTarget(
                    root=resolved / declaration.path,
                    managed=declaration.managed,
                )
                for declaration in declared.value
            ),
        ))

    @staticmethod
    def repository_operation_applicability(
        target: m.Infra.WorkspaceOperationTarget,
        *,
        mutating: bool,
    ) -> p.Result[m.Infra.WorkspaceOperationApplicability]:
        """Read the target's own policy without reintroducing a workspace roster.

        Returns:
            The target's own applicability policy.

        """
        result_type = r[m.Infra.WorkspaceOperationApplicability]
        if target.managed is False:
            return result_type.ok(
                m.Infra.WorkspaceOperationApplicability(
                    applicable=False,
                    reason="Git declaration disables workspace management",
                ),
            )
        if not target.root.is_dir():
            return result_type.fail(
                f"required operation root is missing: {target.root}",
            )
        loaded = FlextInfraUtilitiesProjectManagedArtifacts.load_codegen_inputs(
            target.root,
        )
        if loaded.failure:
            return result_type.from_failure(loaded)
        repository = loaded.value.spec.repository
        if repository.codegen == c.Infra.CodegenKind.NONE:
            return result_type.ok(
                m.Infra.WorkspaceOperationApplicability(
                    applicable=False,
                    reason="Repository declaration disables code generation",
                ),
            )
        if mutating and repository.read_only:
            return result_type.ok(
                m.Infra.WorkspaceOperationApplicability(
                    applicable=False,
                    reason="Repository declaration is read-only",
                ),
            )
        return result_type.ok(m.Infra.WorkspaceOperationApplicability(applicable=True))

    @classmethod
    def load_refactor_config(cls, repository_root: Path) -> m.Infra.RefactorConfigSpec:
        """Load declared refactor configuration, propagating invalid manifests.

        Returns:
            The resulting ``m.Infra.RefactorConfigSpec``.

        """
        packaged = m.Infra.RefactorConfigSpec(
            project_scan_dirs=config.Infra.source_scan.roots,
        )
        loaded = FlextInfraUtilitiesProjectManagedArtifacts.load_codegen_inputs(
            repository_root,
        ).unwrap()
        repository = loaded.spec.repository
        if repository.refactor is None:
            return packaged
        return repository.refactor

    @classmethod
    def discover_project_roots(
        cls,
        repository_root: Path,
        *,
        scan_dirs: frozenset[str] | None = None,
        source_project: p.Infra.RopeProject | None = None,
    ) -> t.SequenceOf[Path]:
        """Discover all project directories under repository root.

        Algorithm:
          1. Check if repository_root itself looks like a project
          2. Enumerate only projects declared by the root's own ``.gitmodules``.
          3. Return the root and declared projects in deterministic order.

        Args:
            repository_root: Root directory to start search from.
            scan_dirs: Directory names indicating a project (e.g., "src", "tests").
                Must be a frozenset constant. Defaults to standard project dirs.

        Returns:
            Project roots sorted by their ``.gitmodules`` declaration order.

        Raises:
            ValueError: If ``declared.failure``.

        """
        declared = FlextInfraUtilitiesGit.git_submodule_declarations(
            repository_root,
            source_project=source_project,
        )
        if declared.failure:
            raise ValueError(declared.error or "invalid .gitmodules")
        configured_projects = tuple(item.path.as_posix() for item in declared.value)
        candidates = cls.discover_project_candidates(
            repository_root,
            scan_dirs=scan_dirs,
            declarations=declared.value,
            source_project=source_project,
        )
        resolved_repository_root = repository_root.resolve()
        if not configured_projects:
            return candidates
        configured_order = {name: idx for idx, name in enumerate(configured_projects)}

        def configured_key(candidate: Path) -> t.Pair[int, str]:
            relative = candidate.relative_to(resolved_repository_root).as_posix()
            return configured_order.get(
                relative,
                len(configured_projects),
            ), candidate.name

        return sorted(
            (c for c in candidates if c != resolved_repository_root),
            key=configured_key,
        )

    @classmethod
    def discover_rope_project_roots(
        cls,
        repository_root: Path,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> t.SequenceOf[Path]:
        """Return every Python project this repository's Rope workspace owns.

        A workspace census must index its declared first-party members so
        Rope resolves references across their public facades. The raw child
        scan below is a second enumerator, so it must honour the same manifest
        authority as ``discover_project_candidates``. Without that filter every
        direct child holding a ``pyproject.toml`` re-entered the scope the
        manifest had just excluded, and lazy-init planned files for a directory
        the transaction has no participant for -- which aborts staging after the
        phase root already exists on disk.

        Returns:
            Every Python project this repository's Rope workspace owns.

        Raises:
            ValueError: If the current Git declarations are invalid.

        """
        resolved_root = repository_root.resolve()
        declarations = FlextInfraUtilitiesGit.git_submodule_declarations(
            resolved_root,
            source_project=source_project,
        )
        if declarations.failure:
            raise ValueError(declarations.error or "invalid .gitmodules")
        declared = cls.discover_project_candidates(
            resolved_root,
            declarations=declarations.value,
            source_project=source_project,
        )
        nonparticipants = cls.repository_nonparticipant_paths(
            resolved_root,
            declarations=declarations.value,
        )
        direct = tuple(
            child.resolve()
            for child in (
                sorted(resolved_root.iterdir(), key=attrgetter("name"))
                if source_project is None
                else source_project.source_children(resolved_root)
            )
            if not child.name.startswith(".")
            and (
                child.is_dir()
                if source_project is None
                else source_project.source_query(child, "isdir")
            )
            and (
                (child / c.PYPROJECT_FILENAME).is_file()
                if source_project is None
                else source_project.source_query(child / c.PYPROJECT_FILENAME, "isfile")
            )
            and not cls._is_nonparticipant(child, resolved_root, nonparticipants)
        )
        return tuple(
            sorted(
                {*declared, *direct, resolved_root},
                key=Path.as_posix,
            ),
        )

    @classmethod
    def ast_grep_scan_targets(
        cls,
        repository_root: Path,
        *,
        source_files: t.SequenceOf[Path] | None = None,
        refactor_config: m.Infra.RefactorConfigSpec | None = None,
        source_project: p.Infra.RopeProject | None = None,
    ) -> t.StrSequence:
        """Return only governed handwritten Python surfaces as scan targets.

        Configured roots cannot hide active Python sources. Enumerating files
        instead of passing ``.`` keeps foreign repositories, hidden histories,
        and the artifact SSOT's ignored trees outside the rewrite inventory.

        Returns:
            Only governed handwritten Python surfaces as scan targets.

        Raises:
            ValueError: If a requested source is outside the governed inventory.

        """
        resolved_root = repository_root.resolve()
        del refactor_config
        nonparticipants = cls.repository_nonparticipant_paths(
            resolved_root, source_project=source_project
        )
        eligible = {
            path.relative_to(resolved_root).as_posix()
            for project in cls.governed_project_roots(
                resolved_root, source_project=source_project
            )
            for path in cls.discover_python_files(
                project,
                workspace_excluded_top_dirs=frozenset(),
                source_project=source_project,
            )
            if not cls._is_nonparticipant(path, resolved_root, nonparticipants)
            and not FlextInfraUtilitiesIterationDirectory.source_scan_ignored_path(
                resolved_root, path
            )
        }
        if source_files is not None:
            selected = {
                path.resolve().relative_to(resolved_root).as_posix()
                for path in source_files
            }
            if not selected or selected - eligible:
                msg = (
                    f"native source scope is outside governed inventory: "
                    f"{sorted(selected - eligible)}"
                )
                raise ValueError(msg)
            eligible.intersection_update(selected)
        return tuple(sorted(eligible))

    @classmethod
    def discover_python_dirs(
        cls,
        project_dir: Path,
        *,
        workspace_excluded_top_dirs: frozenset[str],
        skip_dirs: frozenset[str] | None = None,
        source_project: p.Infra.RopeProject | None = None,
    ) -> t.StrSequence:
        """Return owned top-level directories containing active Python sources.

        Returns:
            Directory names in deterministic order.

        """
        if not (
            project_dir.is_dir()
            if source_project is None
            else source_project.source_query(project_dir, "isdir")
        ):
            return []
        effective_skip = (
            frozenset(config.Infra.codegen.analysis_excluded_dirs)
            if skip_dirs is None
            else skip_dirs
        ) | frozenset(config.Infra.codegen.source_scan_ignored)
        nonparticipants = cls.repository_nonparticipant_paths(
            project_dir, source_project=source_project
        )
        return [
            subdir.name
            for subdir in (
                sorted(project_dir.iterdir())
                if source_project is None
                else source_project.source_children(project_dir, follow_aliases=False)
            )
            if (
                subdir.is_dir()
                if source_project is None
                else source_project.source_query(subdir, "isdir")
            )
            and (not subdir.is_symlink() if source_project is None else True)
            and not subdir.name.startswith(".")
            and subdir.name not in effective_skip
            and subdir.name not in workspace_excluded_top_dirs
            and not cls._is_nonparticipant(subdir, project_dir, nonparticipants)
            and not (
                (subdir / c.PYPROJECT_FILENAME).is_file()
                if source_project is None
                else source_project.source_query(
                    subdir / c.PYPROJECT_FILENAME, "isfile"
                )
            )
            and not (
                (subdir / c.Infra.GIT_DIR).exists()
                if source_project is None
                else source_project.source_query(subdir / c.Infra.GIT_DIR, "exists")
            )
            and any(
                cls._walk_python_files(
                    subdir, effective_skip, source_project=source_project
                )
            )
        ]

    @classmethod
    def discover_python_targets(
        cls,
        project_dir: Path,
        *,
        workspace_excluded_top_dirs: frozenset[str],
        source_project: p.Infra.RopeProject | None = None,
    ) -> t.StrSequence:
        """Return owned Python directories and standalone root modules.

        Returns:
            Every active source target owned by one project.

        """
        if not (
            project_dir.is_dir()
            if source_project is None
            else source_project.source_query(project_dir, "isdir")
        ):
            return []
        return [
            *cls.discover_python_dirs(
                project_dir,
                workspace_excluded_top_dirs=workspace_excluded_top_dirs,
                source_project=source_project,
            ),
            *(
                path.name
                for path in (
                    sorted(project_dir.iterdir())
                    if source_project is None
                    else source_project.source_children(
                        project_dir, follow_aliases=False
                    )
                )
                if (
                    path.is_file()
                    if source_project is None
                    else source_project.source_query(path, "isfile")
                )
                and (not path.is_symlink() if source_project is None else True)
                and not path.name.startswith(".")
                and path.suffix in c.Infra.PYTHON_SOURCE_SUFFIXES
                and cls._python_file_belongs_to_project(
                    project_dir, path, source_project=source_project
                )
                and not FlextInfraUtilitiesIterationDirectory.source_scan_ignored_path(
                    project_dir, path
                )
            ),
        ]

    @classmethod
    def discover_python_files(
        cls,
        project_dir: Path,
        *,
        workspace_excluded_top_dirs: frozenset[str],
        source_project: p.Infra.RopeProject | None = None,
    ) -> t.SequenceOf[Path]:
        """Expand canonical targets without crossing project or artifact boundaries.

        Returns:
            Sorted absolute Python source and stub paths.

        """
        project_dir = project_dir.resolve()
        skip_dirs = frozenset(config.Infra.codegen.analysis_excluded_dirs) | frozenset(
            config.Infra.codegen.source_scan_ignored
        )
        nonparticipants = cls.repository_nonparticipant_paths(
            project_dir, source_project=source_project
        )
        return tuple(
            sorted({
                path.resolve()
                for target in cls.discover_python_targets(
                    project_dir,
                    workspace_excluded_top_dirs=workspace_excluded_top_dirs,
                    source_project=source_project,
                )
                for candidate in (project_dir / target,)
                for path in (
                    cls._walk_python_files(
                        candidate, skip_dirs, source_project=source_project
                    )
                    if (
                        candidate.is_dir()
                        if source_project is None
                        else source_project.source_query(candidate, "isdir")
                    )
                    else (candidate,)
                )
                if cls._python_file_belongs_to_project(
                    project_dir, path, source_project=source_project
                )
                and not cls._is_nonparticipant(path, project_dir, nonparticipants)
                and not FlextInfraUtilitiesIterationDirectory.source_scan_ignored_path(
                    project_dir, path.resolve()
                )
            })
        )

    @staticmethod
    def _walk_python_files(
        directory: Path,
        skip_dirs: frozenset[str],
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> Iterator[Path]:
        """Yield sources while pruning hidden, ignored, and nested repository trees.

        Yields:
            Each eligible Python source path.

        """

        def on_error(error: OSError) -> None:
            """Propagate the walk's original filesystem failure."""
            raise error

        walk = (
            directory.walk(on_error=on_error)
            if source_project is None
            else source_project.source_walk(directory)
        )
        for parent, child_dirs, file_names in walk:
            child_dirs[:] = [
                name
                for name in child_dirs
                if name not in skip_dirs
                and not name.startswith(".")
                and (
                    not (parent / name).is_symlink() if source_project is None else True
                )
                and not (
                    (parent / name / c.PYPROJECT_FILENAME).is_file()
                    if source_project is None
                    else source_project.source_query(
                        parent / name / c.PYPROJECT_FILENAME, "isfile"
                    )
                )
                and not (
                    (parent / name / c.Infra.GIT_DIR).exists()
                    if source_project is None
                    else source_project.source_query(
                        parent / name / c.Infra.GIT_DIR, "exists"
                    )
                )
            ]
            for file_name in file_names:
                if (
                    not file_name.startswith(".")
                    and file_name not in skip_dirs
                    and Path(file_name).suffix in c.Infra.PYTHON_SOURCE_SUFFIXES
                    and (
                        not (parent / file_name).is_symlink()
                        if source_project is None
                        else source_project.source_query(parent / file_name, "isfile")
                    )
                ):
                    yield parent / file_name

    @staticmethod
    def _python_file_belongs_to_project(
        project_dir: Path,
        source: Path,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> bool:
        """Return whether a source resolves inside this project's own boundary.

        Returns:
            Whether the path belongs to the supplied project.

        """
        project_dir = project_dir.resolve()
        source = source.resolve()
        if not source.is_relative_to(project_dir):
            return False
        for parent in source.parents:
            if parent == project_dir:
                return True
            if (
                (parent / c.PYPROJECT_FILENAME).is_file()
                if source_project is None
                else source_project.source_query(
                    parent / c.PYPROJECT_FILENAME, "isfile"
                )
            ) or (
                (parent / c.Infra.GIT_DIR).exists()
                if source_project is None
                else source_project.source_query(parent / c.Infra.GIT_DIR, "exists")
            ):
                return False
        return False

    @classmethod
    def analyzer_python_roots(
        cls,
        project_dir: Path,
        declared: t.StrSequence,
        *,
        workspace_excluded_top_dirs: frozenset[str],
    ) -> t.StrSequence:
        """Keep declared directory order and append every discovered Python target.

        Returns:
            Declared directories and discovered Python directories and root modules.

        """
        discovered = cls.discover_python_targets(
            project_dir,
            workspace_excluded_top_dirs=workspace_excluded_top_dirs,
        )
        return (*declared, *(root for root in discovered if root not in declared))

    @classmethod
    def governed_project_roots(
        cls,
        repository_root: Path,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> t.SequenceOf[Path]:
        """Return the repositories a verb run at ``repository_root`` governs.

        The workspace owns its declared first-party members. A standalone
        repository has no member declarations and keeps its own root only.
        Manifest exclusions remain authoritative for both forms.

        Returns:
            The repositories a verb run at ``repository_root`` governs.

        """
        return tuple(
            dict.fromkeys((
                repository_root.resolve(),
                *cls.discover_project_roots(
                    repository_root, source_project=source_project
                ),
            )),
        )

    @staticmethod
    def mutable_flext_members(
        workspace: m.Infra.WorkspaceSpec,
    ) -> t.SequenceOf[m.Infra.RepositoryRef]:
        """Return the declared members a workspace may settle or rewrite.

        A member qualifies by its declaration alone: an internal FLEXT kind,
        a generated codegen surface, and a writable checkout. Declared order
        is kept, so every consumer reports members deterministically.

        Returns:
            The governed mutable members in declared order.

        """
        return tuple(
            member
            for member in workspace.subprojects
            if member.kind is c.Infra.ProjectKind.INTERNAL_FLEXT
            and member.codegen is not c.Infra.CodegenKind.NONE
            and not member.read_only
        )

    @staticmethod
    def nearest_project_root(
        repository_root: Path,
        path: Path,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> Path | None:
        """Find the nearest manifest owner inside one governed repository.

        Returns:
            The resulting ``Path | None``.

        """
        boundary = repository_root.resolve()
        candidate = path.resolve()
        if source_project is not None and source_project.source_query(
            candidate, "isfile"
        ):
            candidate = candidate.parent
        if not candidate.is_relative_to(boundary):
            return None
        for parent in (candidate, *candidate.parents):
            is_directory = (
                parent.is_dir()
                if source_project is None
                else source_project.source_query(parent, "isdir")
            )
            if is_directory and (
                (parent / c.PYPROJECT_FILENAME).is_file()
                if source_project is None
                else source_project.source_query(
                    parent / c.PYPROJECT_FILENAME, "isfile"
                )
            ):
                return parent
            if parent == boundary:
                return None
        return None

    @staticmethod
    def runtime_environment_dir(
        project_root: Path,
        *,
        runtime_root: Path | None = None,
    ) -> Path:
        """Resolve the checkout's Python environment.

        A declared ``runtime_root`` (the generated Makefile's ``RUNTIME_ROOT``)
        owns the environment. Undeclared, the owner derives it: a subproject
        checked out inside a workspace uses the workspace environment; a
        standalone checkout or a linked Git worktree owns its own physical
        environment inside the checkout, exactly as the generated Makefile and
        ``.envrc`` resolve it. No environment is shared between checkouts.

        Returns:
            The resulting ``Path``.

        """
        if runtime_root is None:
            runtime = FlextInfraUtilitiesGit.git_repository_root(
                m.Infra.GitRepoRequest(repo_root=project_root),
            ).unwrap()
            runtime_root = runtime.repository_root
        return runtime_root.resolve() / c.Infra.ENVIRONMENT_DIRECTORY

    @classmethod
    def runtime_python(
        cls,
        project_root: Path,
        *,
        runtime_root: Path | None = None,
    ) -> Path:
        """Resolve the fixed Python entrypoint inside the managed environment.

        ``runtime_root`` mirrors ``runtime_environment_dir``: a declared runtime
        root (the generated Makefile's ``RUNTIME_ROOT``) owns the environment.

        Returns:
            The resulting ``Path``.

        """
        return (
            cls.runtime_environment_dir(project_root, runtime_root=runtime_root)
            / ("Scripts" if sys.platform == "win32" else "bin")
            / ("python.exe" if sys.platform == "win32" else c.Infra.PYTHON)
        )


__all__: list[str] = ["FlextInfraUtilitiesProjectDiscovery"]
