"""Project discovery helpers for flext-infra utilities.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from operator import attrgetter
from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import u

from flext_infra import c, config, m, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesGit,
    FlextInfraUtilitiesIterationDirectory,
    FlextInfraUtilitiesProjectDiscoveryCandidatesMixin,
    FlextInfraUtilitiesProjectManagedArtifacts,
)
from flext_infra._utilities.mise_binary import FlextInfraUtilitiesMiseBinary

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
        if not (target.root / c.PYPROJECT_FILENAME).is_file():
            return result_type.ok(
                m.Infra.WorkspaceOperationApplicability(
                    applicable=False,
                    reason="Repository declares no pyproject manifest",
                ),
            )
        loaded = FlextInfraUtilitiesProjectManagedArtifacts.load_codegen_inputs(
            target.root,
        )
        if loaded.failure:
            return result_type.from_failure(loaded)
        repository = loaded.value.spec.repository
        declared = FlextInfraUtilitiesProjectDiscovery._declared_applicability(
            repository,
            mutating=mutating,
        )
        if declared is not None:
            return result_type.ok(declared)
        return result_type.ok(m.Infra.WorkspaceOperationApplicability(applicable=True))

    @staticmethod
    def _declared_applicability(
        repository: m.Infra.RepositoryDeltaSpec,
        *,
        mutating: bool,
    ) -> m.Infra.WorkspaceOperationApplicability | None:
        """Read the repository's own declaration for an inapplicable target.

        Args:
            repository: The loaded repository declaration of the target.
            mutating: Whether the requested operation mutates sources.

        Returns:
            The declared inapplicability, or None when the target applies.

        """
        if repository.codegen == c.Infra.CodegenKind.NONE:
            return m.Infra.WorkspaceOperationApplicability(
                applicable=False,
                reason="Repository declaration disables code generation",
            )
        if mutating and repository.read_only:
            return m.Infra.WorkspaceOperationApplicability(
                applicable=False,
                reason="Repository declaration is read-only",
            )
        return None

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
            source_project: Optional Rope project used to read ``.gitmodules``

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
        """Return governed Python sources and owned stub-policy paths.

        Configured roots cannot hide active Python sources. Enumerating files
        instead of passing ``.`` keeps foreign repositories, hidden histories,
        and artifact outputs outside the rewrite inventory. Generated or retired
        owned typing paths remain detection inputs, never rewrite candidates.

        Returns:
            Governed source and path-policy targets.

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
                owned_path_admission=True,
            )
            if not cls._is_nonparticipant(path, resolved_root, nonparticipants)
        }
        if source_files is not None:
            selected = {
                (path.absolute() if path.suffix == ".pyi" else path.resolve())
                .relative_to(resolved_root)
                .as_posix()
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

    @staticmethod
    def excluded_parts() -> frozenset[str]:
        """Resolve analyzer exclusions from the generated artifact SSOT.

        Returns:
            The analysis-excluded and source-scan-ignored directory names.

        """
        return frozenset(config.Infra.codegen.analysis_excluded_dirs) | frozenset(
            config.Infra.codegen.source_scan_ignored
        )

    @classmethod
    def root_namespace(
        cls,
        project_root: Path,
        name: str,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> bool:
        """Return whether a direct child folder of a project root is a namespace.

        Namespaces are detected, never declared: ``src`` holds the public
        packages and every other importable child folder is an internal tier.
        A scan-ignored resource or a folder declaring its own project is no
        namespace of this one. Callers ask about a Python path beneath the
        folder, which proves that it holds code.

        Returns:
            Whether ``name`` is a namespace folder of ``project_root``.

        """
        folder = project_root / name
        return name == c.Infra.DEFAULT_SRC_DIR or (
            name.isidentifier()
            and name not in cls.excluded_parts()
            and (
                folder.is_dir()
                if source_project is None
                else source_project.source_query(folder, "isdir")
            )
            and not (
                (folder / c.PYPROJECT_FILENAME).is_file()
                if source_project is None
                else source_project.source_query(
                    folder / c.PYPROJECT_FILENAME, "isfile"
                )
            )
        )

    @classmethod
    def package_name_for_dir(
        cls,
        package_dir: Path,
        *,
        project_root: Path,
        source_project: p.Infra.RopeProject | None = None,
    ) -> str:
        """Return the import package a directory declares inside a project.

        ``src`` contributes its children with its own segment stripped; an
        internal namespace keeps its name. An empty string when the directory
        sits outside the project or under no detected namespace.
        A capture horizon may contain several declared projects; the nearest
        original project owns the namespace without changing source authority.

        Returns:
            The import package a directory declares inside a project.

        """
        if not package_dir.is_relative_to(project_root):
            return ""
        parts = package_dir.relative_to(project_root).parts
        if not parts or (
            parts[0] != c.Infra.DEFAULT_SRC_DIR and parts[0] in cls.excluded_parts()
        ):
            return ""
        if not cls.root_namespace(
            project_root, parts[0], source_project=source_project
        ):
            owner = cls.nearest_project_root(
                project_root, package_dir, source_project=source_project
            )
            if owner is not None:
                project_root = owner
                parts = package_dir.relative_to(project_root).parts
        if not parts or not cls.root_namespace(
            project_root, parts[0], source_project=source_project
        ):
            return ""
        return ".".join(parts[1:] if parts[0] == c.Infra.DEFAULT_SRC_DIR else parts)

    @classmethod
    def discover_python_files(
        cls,
        project_dir: Path,
        *,
        workspace_excluded_top_dirs: frozenset[str],
        source_project: p.Infra.RopeProject | None = None,
        owned_path_admission: bool = False,
    ) -> t.SequenceOf[Path]:
        """Enumerate sources once without crossing project or artifact boundaries.

        Returns:
            Sorted absolute Python source and stub paths.

        """
        project_dir = project_dir.resolve()
        if not (
            project_dir.is_dir()
            if source_project is None
            else source_project.source_query(project_dir, "isdir")
        ):
            return ()
        skip_dirs = cls.excluded_parts()
        owned_artifacts = (
            frozenset[str](
                artifact.name
                for artifact in config.Infra.codegen.artifacts
                if artifact.generated_source or artifact.retired_typing_root
            )
            if owned_path_admission
            else frozenset[str]()
        )
        nonparticipants = cls.repository_nonparticipant_paths(
            project_dir, source_project=source_project
        )
        excluded_paths = frozenset(
            project_dir / relative
            for relative in (*workspace_excluded_top_dirs, *nonparticipants)
        )
        return tuple(
            sorted({
                path.absolute()
                if owned_path_admission and path.suffix == ".pyi"
                else path.resolve()
                for path in cls._walk_python_files(
                    project_dir,
                    skip_dirs - owned_artifacts,
                    excluded_paths=excluded_paths,
                    source_project=source_project,
                    owned_path_admission=owned_path_admission,
                )
                if (owned_path_admission and path.suffix == ".pyi")
                or (
                    not any(
                        part.startswith(".") or part in skip_dirs
                        for part in path.relative_to(project_dir).parts
                    )
                    and not (
                        FlextInfraUtilitiesIterationDirectory.source_scan_ignored_path(
                            project_dir,
                            path,
                        )
                    )
                )
            })
        )

    @staticmethod
    def _walk_python_files(
        directory: Path,
        skip_dirs: frozenset[str],
        *,
        excluded_paths: frozenset[Path] = frozenset(),
        source_project: p.Infra.RopeProject | None = None,
        owned_path_admission: bool = False,
    ) -> Iterator[Path]:
        """Yield sources while pruning hidden, ignored, and nested repository trees.

        Yields:
            Each eligible Python source path.

        """

        def on_error(error: OSError) -> None:
            """Propagate the walk's original filesystem failure."""
            raise error

        retired_roots = (
            frozenset[Path](
                directory / artifact.name
                for artifact in config.Infra.codegen.artifacts
                if artifact.retired_typing_root
            )
            if owned_path_admission
            else frozenset[Path]()
        )
        owned_roots = (
            frozenset[Path](directory / root for root in config.Infra.source_scan.roots)
            | retired_roots
            if owned_path_admission
            else frozenset[Path]()
        )
        artifact_boundaries = frozenset(
            artifact.name
            for artifact in config.Infra.codegen.artifacts
            if artifact.source_scan_ignore
            and not (artifact.generated_source or artifact.retired_typing_root)
        ) | {c.Infra.GIT_DIR}
        walk = (
            directory.walk(on_error=on_error)
            if source_project is None
            else source_project.source_walk(directory)
        )
        for parent, child_dirs, file_names in walk:
            child_dirs[:] = [
                name
                for name in child_dirs
                if (
                    (name not in skip_dirs and not name.startswith("."))
                    or (
                        name not in artifact_boundaries
                        and any(
                            (parent / name).is_relative_to(root) for root in owned_roots
                        )
                    )
                )
                and parent / name not in excluded_paths
                and (
                    not (parent / name).is_symlink() if source_project is None else True
                )
                and (
                    any((parent / name).is_relative_to(root) for root in retired_roots)
                    or not (
                        (parent / name / c.PYPROJECT_FILENAME).is_file()
                        if source_project is None
                        else source_project.source_query(
                            parent / name / c.PYPROJECT_FILENAME, "isfile"
                        )
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
                stub_path = owned_path_admission and Path(file_name).suffix == ".pyi"
                if not stub_path and (
                    file_name.startswith(".") or file_name in skip_dirs
                ):
                    continue
                if (
                    parent / file_name not in excluded_paths
                    and Path(file_name).suffix in c.Infra.PYTHON_SOURCE_SUFFIXES
                    and FlextInfraUtilitiesProjectDiscovery._source_file_admitted(
                        parent / file_name,
                        source_project,
                        owned_stub=stub_path,
                    )
                ):
                    yield parent / file_name

    @staticmethod
    def _source_file_admitted(
        path: Path,
        source_project: p.Infra.RopeProject | None,
        *,
        owned_stub: bool,
    ) -> bool:
        """Preserve physical hazards for owned-stub rejection, not source execution.

        Returns:
            The original source membership or explicit retirement hazard witness.

        """
        if source_project is not None:
            return source_project.source_query(path, "isfile")
        return (path.is_file() and not path.is_symlink()) or (
            owned_stub and path.is_symlink()
        )

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

    @classmethod
    def runtime_environment_dir(
        cls,
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
            runtime_root = cls.runtime_owner_root(project_root).unwrap()
        return runtime_root.resolve() / c.Infra.ENVIRONMENT_DIRECTORY

    @classmethod
    def runtime_owner_root(cls, project_root: Path) -> p.Result[Path]:
        """Resolve the common native runtime owner without suppressing failures.

        Returns:
            The elected physical root or the original discovery failure.

        """
        identity = FlextInfraUtilitiesGit.git_show_toplevel(
            m.Infra.GitRepoRequest(repo_root=project_root),
        )
        if identity.failure:
            return r[Path].from_failure(identity)
        git_root = identity.value.repository_root.resolve()
        submitted = project_root.expanduser().resolve()
        project = cls.nearest_project_root(git_root, submitted) or git_root
        return cls._local_runtime_root(project, git_root)

    @classmethod
    def _local_runtime_root(cls, project_root: Path, git_root: Path) -> p.Result[Path]:
        """Elect the physical runtime from Git attachment and native UV scope.

        Returns:
            The declared runtime owner or the original discovery failure.

        """
        runtime = FlextInfraUtilitiesGit.git_repository_root(
            m.Infra.GitRepoRequest(repo_root=project_root)
        )
        if runtime.failure:
            return r[Path].from_failure(runtime)
        attached = runtime.value.repository_root.resolve()
        if attached != git_root and (attached / c.PYPROJECT_FILENAME).is_file():
            declarations = FlextInfraUtilitiesGit.git_submodule_declarations(attached)
            if declarations.failure:
                return r[Path].from_failure(declarations)
            if not any(
                (attached / member.path).resolve() == git_root
                for member in declarations.value
            ):
                return r[Path].fail(
                    f"attached runtime has no original member declaration: {git_root}"
                )
            return r[Path].ok(attached)
        scope = cls._native_resolution_scope(project_root, git_root)
        if scope.failure:
            return r[Path].from_failure(scope)
        return (
            cls._native_resolution_owner(project_root, scope.value)
            if scope.value != project_root
            else r[Path].ok(project_root)
        )

    @classmethod
    def _native_resolution_scope(
        cls, project_root: Path, git_root: Path
    ) -> p.Result[Path]:
        """Authenticate a Python ancestor before requiring its native reader.

        Returns:
            The native discovery scope or the original ownership failure.

        """
        enclosing = next(
            (
                parent
                for parent in project_root.parents
                if (project_root == git_root or parent.is_relative_to(git_root))
                and (parent / c.PYPROJECT_FILENAME).is_file()
            ),
            None,
        )
        if enclosing is None:
            return r[Path].ok(project_root)
        return cls._enclosing_git_scope(project_root, enclosing)

    @staticmethod
    def _enclosing_git_scope(project_root: Path, enclosing: Path) -> p.Result[Path]:
        """Reconcile an enclosing manifest with its authenticated Git ownership.

        Returns:
            The containing Git scope or the original ownership failure.

        """
        result_type = r[Path]
        ownership = FlextInfraUtilitiesGit.git_mutation_scope(
            m.Infra.GitRepoRequest(repo_root=enclosing),
        )
        if ownership.failure:
            return result_type.from_failure(ownership)
        if ownership.value.git_dir is None:
            return result_type.ok(project_root)
        identity = FlextInfraUtilitiesGit.git_show_toplevel(
            m.Infra.GitRepoRequest(repo_root=enclosing),
        )
        if identity.failure:
            return result_type.from_failure(identity)
        scope = identity.value.repository_root.resolve()
        if not project_root.is_relative_to(scope):
            return result_type.fail(
                "native association is outside its containing Git repository",
            )
        return result_type.ok(
            scope if (scope / c.PYPROJECT_FILENAME).is_file() else enclosing,
        )

    @staticmethod
    def _native_resolution_owner(
        project_root: Path, reader_root: Path
    ) -> p.Result[Path]:
        """Let managed UV resolve membership, including native exclusions.

        Returns:
            The authenticated native owner or the original discovery failure.

        """
        result_type = r[Path]
        identity = FlextInfraUtilitiesGit.git_show_toplevel(
            m.Infra.GitRepoRequest(repo_root=reader_root),
        )
        if identity.failure:
            return result_type.from_failure(identity)
        git_root = identity.value.repository_root.resolve()
        binary = FlextInfraUtilitiesMiseBinary.managed_mise_binary(
            c.Infra.UV, reader_root
        )
        if binary.failure:
            return result_type.from_failure(binary)
        discovered = u.Cli.run_raw(
            (str(binary.value), "workspace", "dir", "--project", str(project_root)),
            cwd=project_root,
            timeout=c.Infra.TIMEOUT_SHORT,
            options=m.Cli.ProcessOptions(
                env={"MISE_AUTO_INSTALL": "0"},
                remove_env_keys=config.Infra.codegen.make.native_environment_unset,
            ),
        )
        if discovered.failure:
            return result_type.from_failure(discovered)
        process = discovered.value
        if not u.Cli.process_succeeded(process.outcome) or process.stderr.strip():
            return result_type.fail(process.stderr or process.stdout)
        owner = Path(process.stdout.strip())
        if (
            not owner.is_absolute()
            or not owner.is_dir()
            or not owner.resolve().is_relative_to(git_root)
            or not project_root.is_relative_to(owner.resolve())
        ):
            return result_type.fail(
                f"native UV workspace owner leaves the project's Git boundary: {owner}",
            )
        return result_type.ok(owner.resolve())

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
