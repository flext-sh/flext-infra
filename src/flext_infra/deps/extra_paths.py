"""Derive Pyrefly search paths and analysis roots from the workspace topology.

Every emitted entry is relative to the project that owns the file it is written
into. A dependency that lives in another checkout resolves through its installed
distribution in the environment the project runs against, never through a
filesystem hop out of the project root: a generated surface that encodes
``../<sibling>/src`` describes one host layout, so it is wrong in any checkout
whose siblings sit elsewhere and it makes one generator emit different content
per clone.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Annotated, override

from flext_infra import FlextInfraProjectSelectionServiceBase, c, config, m, p, t, u
from flext_infra.workspace import FlextInfraWorkspaceDetector


class FlextInfraExtraPathsManager(
    FlextInfraProjectSelectionServiceBase[bool],
):
    """Derive the Pyrefly search paths and analysis roots of workspace projects."""

    # Why (fixed point): codegen materializes managed roots (tests/) while it
    # applies. Discovery that only sees the pre-apply tree would omit them and
    # the post-apply verification plan would want the pyproject changed again.
    generated_python_roots: Annotated[
        Sequence[str],
        m.Field(
            default=(),
            description="Analyzer roots the active codegen plan materializes",
        ),
    ] = ()
    analysis_exclusions: Annotated[
        Sequence[str],
        m.Field(
            default=(),
            description="Workspace-relative paths excluded from analyzer discovery",
        ),
    ] = ()

    _workspace_project_names: t.Infra.StrSet = m.PrivateAttr(default_factory=set)

    @override
    def model_post_init(self, __context: Mapping[str, p.AttributeProbe], /) -> None:
        """Initialize workspace metadata after validation."""
        del __context
        self._workspace_project_names = set(
            u.Infra.workspace_project_paths(self.repository_root),
        )

    @property
    def workspace_project_names(self) -> Sequence[str]:
        """Managed workspace project names backing dependency resolution."""
        return tuple(sorted(self._workspace_project_names))

    @property
    def analysis_excluded_top_dirs(self) -> frozenset[str]:
        """First path segments from the caller's validated topology."""
        return frozenset(
            Path(path).parts[0] for path in self.analysis_exclusions if Path(path).parts
        )

    def _search_path_set(self, *, project_dir: Path) -> t.Infra.StrSet:
        """Return the unordered shared search roots, minus the ordered ones.

        A shared root counts when it exists on disk or when the active codegen
        plan is about to materialize it.

        Returns:
            The unordered shared search roots, minus the ordered ones.

        """
        rules = config.Infra.tooling.tools.pyrefly.path_rules
        paths: t.Infra.StrSet = {
            relative_path
            for relative_path in rules.project_shared_search_paths
            if (project_dir / relative_path).is_dir()
            or relative_path in self.generated_python_roots
        }
        paths.discard(rules.source_dir)
        paths.discard(rules.project_root)
        return paths

    def pyrefly_search_paths(
        self,
        *,
        project_dir: Path,
    ) -> Sequence[str]:
        """Compute pyrefly search paths for a project.

        Only roots inside ``project_dir`` are emitted. Path dependencies and uv
        workspace projects are importable through their installed distributions,
        so they need no search-path entry and must never be described by a path
        that leaves the project.

        Returns:
            The resulting ``Sequence[str]``.

        """
        rules = config.Infra.tooling.tools.pyrefly.path_rules
        source_root = rules.source_dir
        # Why: the project root closes the chain for
        # cross-tree imports. `scripts/` is a checked env dir and owns
        # `scripts/__init__.py`, so `tests/` and `scripts/` import its modules
        # as `scripts.*`; resolving them needs the repo root on the search
        # path. It must come LAST: pyrefly resolves the FIRST matching entry,
        # so `source_dir` ahead of "." keeps `src.x` from also resolving as
        # `x` (the duplicate-class failure).
        root_path = rules.project_root
        has_project_root = (project_dir / root_path).is_dir()
        # Analysis inclusion does not create another import identity.
        # Additional search roots come only from the declared path rules.
        paths = self._search_path_set(project_dir=project_dir)
        has_source_root = (
            project_dir / source_root
        ).is_dir() or source_root in self.generated_python_roots
        ordered = sorted(paths)
        if has_project_root:
            ordered.append(root_path)
        if has_source_root:
            ordered.insert(0, source_root)
        return tuple(ordered)

    def _included_pyrefly_env_dirs(self, *, project_dir: Path) -> Sequence[str]:
        """Return the declared env dirs whose Python sources pyrefly analyzes.

        The one declared set behind both pyrefly project-includes and the
        pyrefly search-path: a root included for analysis is also a root for
        import resolution. Only real production roots (discovered on disk or
        materialized by the active codegen plan) participate.

        Returns:
            The resulting ``Sequence[str]``.

        """
        rules = config.Infra.tooling.tools.pyrefly.path_rules
        discovered_python_roots = set(
            u.Infra.discover_python_dirs(
                project_dir,
                workspace_excluded_top_dirs=self.analysis_excluded_top_dirs,
            ),
        )
        return tuple(
            directory
            for directory in rules.env_dirs
            if directory in discovered_python_roots
            or directory in self.generated_python_roots
        )

    def pyrefly_project_includes(
        self,
        *,
        project_dir: Path,
        is_root: bool,
    ) -> Sequence[str]:
        """Build Pyrefly includes from configured productive directories.

        Returns:
            The resulting ``Sequence[str]``.

        """
        includes: t.Infra.StrSet = set(
            self.pyrefly_include_globs(
                self._included_pyrefly_env_dirs(project_dir=project_dir),
            ),
        )
        if not is_root or (
            not config.Infra.tooling.tools.pyrefly.path_rules.workspace_include_children
        ):
            return sorted(includes)
        for child in sorted(project_dir.iterdir()):
            if not child.is_dir() or not (child / c.PYPROJECT_FILENAME).exists():
                continue
            child_dirs = u.Infra.discover_python_dirs(
                child,
                workspace_excluded_top_dirs=(
                    FlextInfraWorkspaceDetector.analysis_excluded_top_dirs(
                        child,
                    ).unwrap()
                ),
            )
            includes.update(
                f"{child.name}/{directory}/**/*.py*" for directory in child_dirs
            )
        return sorted(includes)

    @staticmethod
    def pyrefly_include_globs(env_dirs: Sequence[str]) -> Sequence[str]:
        """Render Pyrefly include globs for already validated Python roots.

        Returns:
            The resulting ``Sequence[str]``.

        """
        return tuple(f"{directory}/**/*.py*" for directory in env_dirs)


__all__: list[str] = ["FlextInfraExtraPathsManager"]
