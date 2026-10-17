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
        declared = FlextInfraUtilitiesGit.git_submodule_declarations(repository_root)
        if declared.failure:
            raise ValueError(declared.error or "invalid .gitmodules")
        configured_projects = tuple(item.path.as_posix() for item in declared.value)
        candidates = cls.discover_project_candidates(
            repository_root,
            scan_dirs=scan_dirs,
            declarations=declared.value,
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
    def discover_rope_project_roots(cls, repository_root: Path) -> t.SequenceOf[Path]:
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
        )
        if declarations.failure:
            raise ValueError(declarations.error or "invalid .gitmodules")
        declared = cls.discover_project_candidates(
            resolved_root,
            declarations=declarations.value,
        )
        nonparticipants = cls.repository_nonparticipant_paths(
            resolved_root,
            declarations=declarations.value,
        )
        direct = tuple(
            child.resolve()
            for child in sorted(resolved_root.iterdir(), key=attrgetter("name"))
            if child.is_dir()
            and not child.name.startswith(".")
            and (child / c.PYPROJECT_FILENAME).is_file()
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
    ) -> t.StrSequence:
        """Return only governed handwritten Python surfaces as scan targets.

        A workspace root is not itself a Python source surface. Passing ``.`` to
        ast-grep also traverses generated agent hooks and other managed
        projections, so a project-local ``make mod`` could rewrite files owned by
        another generator. The refactor config is the single scope owner for
        source trees; root Python modules cover public entry points such as
        ``conftest.py`` without opening hidden directories.

        Returns:
            Only governed handwritten Python surfaces as scan targets.

        Raises:
            ValueError: If a requested source is outside the governed inventory.

        """
        resolved_root = repository_root.resolve()
        if refactor_config is None:
            refactor_config = cls.load_refactor_config(resolved_root)
        scan_dirs = refactor_config.project_scan_dirs
        targets: set[str] = set()
        for project in cls.governed_project_roots(resolved_root):
            for suffix in c.Infra.PYTHON_SOURCE_SUFFIXES:
                # Python files directly in the project root (e.g., conftest.py)
                for target in project.glob(f"*{suffix}"):
                    if target.exists():
                        targets.add(target.relative_to(resolved_root).as_posix())
                # Recursively scan configured directories for Python sources:
                # modules and the stubs the catalog rules also govern.
                for directory in scan_dirs:
                    cls._collect_scan_dir_targets(
                        project / directory,
                        f"*{suffix}",
                        resolved_root,
                        targets,
                    )
        nonparticipants = cls.repository_nonparticipant_paths(resolved_root)
        eligible = {
            target
            for target in targets
            if not cls._is_nonparticipant(
                resolved_root / target, resolved_root, nonparticipants
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

    @staticmethod
    def _collect_scan_dir_targets(
        scan_dir: Path,
        pattern: str,
        resolved_root: Path,
        targets: set[str],
    ) -> None:
        """Add every Python file under one configured scan directory.

        Trees the codegen artifact SSOT ignores for source scans (generated
        sources included) are outside the inventory the semantic phases
        index, so they never become scan or rewrite targets either.
        """
        if not scan_dir.exists():
            return
        for target in scan_dir.rglob(pattern):
            if (
                target.is_file()
                and not FlextInfraUtilitiesIterationDirectory.source_scan_ignored_path(
                    scan_dir, target
                )
            ):
                targets.add(target.relative_to(resolved_root).as_posix())

    @classmethod
    def governed_project_roots(cls, repository_root: Path) -> t.SequenceOf[Path]:
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
                *cls.discover_project_roots(repository_root),
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
    def nearest_project_root(repository_root: Path, path: Path) -> Path | None:
        """Find the nearest manifest owner inside one governed repository.

        Returns:
            The resulting ``Path | None``.

        """
        boundary = repository_root.resolve()
        candidate = path.resolve()
        if not candidate.is_relative_to(boundary):
            return None
        for parent in (candidate, *candidate.parents):
            if (parent / c.PYPROJECT_FILENAME).is_file():
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
