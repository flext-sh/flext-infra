"""Synchronize pyright, mypy, and pyrefly paths from workspace dependencies.

Handlers are called by the canonical CLI via FlextInfraCliDeps.register_deps.

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

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path
from typing import Annotated, override

from flext_infra import FlextInfraProjectSelectionServiceBase, c, config, m, p, r, t, u
from flext_infra.workspace import FlextInfraWorkspaceDetector


class FlextInfraExtraPathsManager(
    FlextInfraProjectSelectionServiceBase[bool],
):
    """Manager for synchronizing type-checker search paths from dependencies."""

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

    @override
    def execute(self) -> p.Result[bool]:
        """Synchronize extra paths for the configured project slice.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        result = self.sync_extra_paths(
            dry_run=self.effective_dry_run,
            project_dirs=self.project_dirs,
        )
        if result.failure:
            return r[bool].from_failure(result)
        return r[bool].ok(value=True)

    def _search_path_set(
        self,
        rules: p.Infra.TypeCheckerPathRules,
        *,
        project_dir: Path,
        shared_search_paths: Sequence[str],
        include_generated_roots: bool,
    ) -> t.Infra.StrSet:
        """Return the unordered search roots a checker shares, minus ordered ones.

        ``include_generated_roots`` carries the only difference between the two
        callers: pyrefly also accepts a shared root the active codegen plan is
        about to materialize, mypy accepts only roots already on disk.

        Returns:
            The unordered search roots a checker shares, minus ordered ones.

        """
        shared_paths = [
            relative_path
            for relative_path in shared_search_paths
            if (project_dir / relative_path).is_dir()
            or (
                include_generated_roots and relative_path in self.generated_python_roots
            )
        ]
        paths: t.Infra.StrSet = set(shared_paths)
        paths.discard(rules.source_dir)
        paths.discard(rules.project_root)
        return paths

    @staticmethod
    def pyright_extra_paths() -> Sequence[str]:
        """Compute pyright extra paths for a project.

        Returns:
            The resulting ``Sequence[str]``.

        """
        rules = config.Infra.tooling.tools.pyright.path_rules
        source_root = rules.source_dir
        # Why: naive sorted({".", "src"}) puts "." first and diverges from the
        # declared scaffold roots and pyrefly search-path ordering, so conform
        # apply never reached a fixed point on pyproject.toml. Keep the source
        # import root first; sort everything else for stable comparisons.
        paths: t.Infra.StrSet = {rules.project_root, source_root}
        paths.discard(source_root)
        return (source_root, *sorted(paths))

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
        # `x` (the duplicate-class failure). mypy cannot
        # share this value — it enumerates every search-path root and reports
        # the same file under two module names as source-file-found-twice —
        # which is why the two tools now derive separately.
        root_path = rules.project_root
        has_project_root = (project_dir / root_path).is_dir()
        paths = self._search_path_set(
            rules,
            project_dir=project_dir,
            shared_search_paths=rules.project_shared_search_paths,
            include_generated_roots=True,
        )
        # Analysis inclusion does not create another import identity.
        # Additional search roots come only from the declared path rules.
        paths.discard(rules.source_dir)
        paths.discard(rules.project_root)
        has_source_root = (
            project_dir / source_root
        ).is_dir() or source_root in self.generated_python_roots
        ordered = sorted(paths)
        if has_project_root:
            ordered.append(root_path)
        if has_source_root:
            return (source_root, *ordered)
        return tuple(ordered)

    def mypy_search_paths(self, *, project_dir: Path) -> Sequence[str]:
        """Compute mypy search paths: like pyrefly but without the project root.

        mypy treats each search-path entry as a package root and enumerates the
        files under it. When a root re-spells a module that another root already
        provides -- the repo root resolving ``scripts/legado/lib/argocd.py`` as
        ``scripts.legado.lib.argocd`` while ``scripts/`` on the same path offers
        it as ``legado.lib.argocd`` -- mypy reports "Source file found twice
        under different module names" and aborts before checking anything.
        pyrefly does not have that failure mode: it resolves imports
        first-match-wins, so the project root is a safe resolution aid there
        and stays one (see :meth:`pyrefly_search_paths`).

        Returns:
            The resulting ``Sequence[str]``.

        """
        rules = config.Infra.tooling.tools.pyrefly.path_rules
        source_root = rules.source_dir
        paths = self._search_path_set(
            rules,
            project_dir=project_dir,
            shared_search_paths=rules.project_shared_search_paths,
            include_generated_roots=False,
        )
        if (project_dir / source_root).is_dir():
            return (source_root, *sorted(paths))
        return tuple(sorted(paths))

    def _included_pyrefly_env_dirs(self, *, project_dir: Path) -> Sequence[str]:
        """Return the declared env dirs whose Python sources pyrefly analyzes.

        The one declared set behind both pyrefly project-includes and the
        pyrefly search-path: a root included for analysis is also a root for
        import resolution. Never reread an on-disk Pyright table while its
        in-memory payload is being conformed; only real production roots
        (discovered on disk or materialized by the active codegen plan)
        participate.

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

    def sync_doc(
        self,
        doc: t.Cli.TomlDocument,
        *,
        project_dir: Path,
    ) -> Sequence[str]:
        """Apply computed extra paths to an in-memory TOMLDocument.

        Returns:
            The resulting ``Sequence[str]``.

        """
        # Path producers and toml_as_string_list both yield immutable
        # sequences, so equal content compares equal (no list/tuple churn).
        expected = self.pyright_extra_paths()
        tool_table = u.Cli.toml_table_child(doc, c.Infra.TOOL)
        if tool_table is None:
            return list[str]()
        pyright_table = u.Cli.toml_table_child(tool_table, c.Infra.PYRIGHT)
        if pyright_table is None:
            return list[str]()
        mypy_table = u.Cli.toml_table_child(tool_table, c.Infra.MYPY)
        changes: MutableSequence[str] = []
        pyright_extra_paths = u.Cli.toml_item_child(pyright_table, "extraPaths")
        current_pyright = u.Cli.toml_as_string_list(
            pyright_extra_paths if pyright_extra_paths is not None else [],
        )
        if current_pyright != expected:
            pyright_table["extraPaths"] = expected
            changes.append("synchronized pyright extraPaths")
        if mypy_table is not None:
            # NOT the pyrefly search path any more.
            # mypy enumerates every search-path root as a package root, so a
            # root that re-spells an already-rooted module makes it report the
            # same file twice ("Source file found twice under different module
            # names") and abort repo-wide. pyrefly resolves first-match and
            # tolerates what mypy cannot. mypy gets source + shared config
            # paths only; the project root stays a pyrefly-only resolution aid.
            expected_mypy = self.mypy_search_paths(
                project_dir=project_dir,
            )
            mypy_path_item = u.Cli.toml_item_child(mypy_table, "mypy_path")
            current_mypy = u.Cli.toml_as_string_list(
                mypy_path_item if mypy_path_item is not None else [],
            )
            if current_mypy != expected_mypy:
                mypy_table["mypy_path"] = expected_mypy
                tool_table[c.Infra.MYPY] = mypy_table
                changes.append("synchronized mypy mypy_path")
        if changes:
            tool_table[c.Infra.PYRIGHT] = pyright_table
            doc["tool"] = tool_table
        return changes

    def sync_payload(
        self,
        payload: t.MutableJsonMapping,
        *,
        project_dir: Path,
        mypy_search_paths: Sequence[str] | None = None,
    ) -> Sequence[str]:
        """Apply computed extra paths to one normalized TOML payload.

        Returns:
            The resulting ``Sequence[str]``.

        """
        expected = self.pyright_extra_paths()
        tool_table = u.Cli.toml_mapping_path(payload, (c.Infra.TOOL,))
        if tool_table is None:
            return list[str]()
        pyright_table = u.Cli.toml_mapping_path(tool_table, (c.Infra.PYRIGHT,))
        if pyright_table is None:
            return list[str]()
        mypy_table = u.Cli.toml_mapping_path(tool_table, (c.Infra.MYPY,))
        changes: MutableSequence[str] = []
        if u.Cli.toml_mapping_sync_string_list(
            u.Cli.toml_mapping_ensure_path(payload, (c.Infra.TOOL, c.Infra.PYRIGHT)),
            "extraPaths",
            expected,
        ):
            changes.append("synchronized pyright extraPaths")
        # Mypy resolves the same import graph as Pyrefly, so it needs the same
        # roots. pyright_extra_paths omits path dependencies, which left sibling
        # packages unresolvable and degraded every symbol they export to Any.
        # It does NOT take pyrefly_search_paths any more: mypy
        # enumerates each root as a package root and aborts repo-wide when two
        # roots re-spell one file (source-file-found-twice). First-match
        # resolution is pyrefly-only.
        if mypy_table is not None and u.Cli.toml_mapping_sync_string_list(
            u.Cli.toml_mapping_ensure_path(payload, (c.Infra.TOOL, c.Infra.MYPY)),
            "mypy_path",
            (
                self.mypy_search_paths(project_dir=project_dir)
                if mypy_search_paths is None
                else mypy_search_paths
            ),
        ):
            changes.append("synchronized mypy mypy_path")
        return changes

    def sync_one(
        self,
        pyproject_path: Path,
        *,
        dry_run: bool = False,
    ) -> p.Result[bool]:
        """Synchronize pyright and mypy paths for one pyproject.toml.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if not pyproject_path.exists():
            return r[bool].fail(f"pyproject not found: {pyproject_path}")
        doc_result = u.Cli.toml_read_document(pyproject_path)
        if doc_result.failure:
            return r[bool].from_failure(doc_result)
        changes = self.sync_doc(
            doc_result.value,
            project_dir=pyproject_path.parent,
        )
        if changes and (not dry_run):
            write_result = u.Cli.toml_write_document(pyproject_path, doc_result.value)
            if write_result.failure:
                return r[bool].from_failure(write_result)
        return r[bool].ok(bool(changes))

    def sync_extra_paths(
        self,
        *,
        dry_run: bool = False,
        project_dirs: Sequence[Path] | None = None,
    ) -> p.Result[int]:
        """Synchronize extraPaths and mypy_path across projects.

        Returns:
            The resulting ``p.Result[int]``.

        """
        if project_dirs:
            updated_selected = 0
            for project_dir in project_dirs:
                pyproject = project_dir / c.PYPROJECT_FILENAME
                # A governed worktree transaction materializes only the scoped
                # submodule's source tree, so a selected member legitimately has
                # no pyproject there. Failing closed made every scoped apply
                # report breakage and silently skip writing the derived paths.
                if not pyproject.exists():
                    continue
                synced = self._sync_target(
                    pyproject,
                    dry_run=dry_run,
                )
                if synced.failure:
                    return r[int].from_failure(synced)
                updated_selected += int(synced.value)
            return r[int].ok(updated_selected)
        # The selector-free operation owns the root AND
        # every managed member. Syncing only the root left each member's
        # mypy_path/extraPaths frozen at whatever was last written by hand, so
        # sibling path dependencies never reached the member analyzers and every
        # symbol imported from them degraded to Any.
        targets: MutableSequence[Path] = [self.root]
        targets.extend(
            self.root / member for member in u.Infra.workspace_project_paths(self.root)
        )
        updated = 0
        for target in targets:
            pyproject = target / c.PYPROJECT_FILENAME
            if not pyproject.exists():
                if target == self.root:
                    return r[int].fail(f"Missing {pyproject}")
                continue
            synced = self._sync_target(
                pyproject,
                dry_run=dry_run,
            )
            if synced.failure:
                return r[int].from_failure(synced)
            updated += int(synced.value)
        return r[int].ok(updated)

    def _sync_target(
        self,
        pyproject: Path,
        *,
        dry_run: bool,
    ) -> p.Result[bool]:
        """Sync one project's pyproject and report whether it changed.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        sync_result = self.sync_one(pyproject, dry_run=dry_run)
        if sync_result.failure:
            return r[bool].from_failure(sync_result)
        if sync_result.value and not dry_run:
            u.Cli.info(f"Updated {pyproject}")
        return r[bool].ok(value=sync_result.value)


__all__: list[str] = ["FlextInfraExtraPathsManager"]
