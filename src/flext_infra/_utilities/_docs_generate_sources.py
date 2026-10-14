"""Authenticated source discovery and CAS verification for docs generation.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_cli import u as cli_u

from flext_infra import FlextInfraConfig, c, m, p, r, t
from flext_infra._utilities import FlextInfraUtilitiesDocsScope


class FlextInfraUtilitiesDocsGenerateSourcesMixin:
    """Freeze every physical source consumed by one documentation render."""

    @staticmethod
    def _source_directory_exists(path: Path) -> p.Result[bool]:
        """Return source-directory presence after physical path authentication.

        Returns:
            Source-directory presence after physical path authentication.

        """
        planned = cli_u.Cli.atomic_plan_directory_chain(path)
        if planned.failure:
            return r[bool].from_failure(planned)
        return r[bool].ok(not planned.value.directories)

    @staticmethod
    def _source_tree_files(
        root: Path,
        *,
        recursive: bool,
        suffixes: frozenset[str],
        excluded_names: frozenset[str] = frozenset(),
    ) -> p.Result[t.VariadicTuple[Path]]:
        """List regular source files through one authenticated tree inventory.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[Path]]``.

        from flext_cli import u as cli_u
        """
        planned = cli_u.Cli.atomic_plan_directory_chain(root)
        if planned.failure:
            return r[t.VariadicTuple[Path]].from_failure(planned)
        if planned.value.directories:
            return r[t.VariadicTuple[Path]].ok(())
        inventory = cli_u.Cli.atomic_inventory_physical_tree(root)
        if inventory.failure:
            return r[t.VariadicTuple[Path]].from_failure(inventory)
        return r[t.VariadicTuple[Path]].ok(
            tuple(
                entry.path
                for entry in inventory.value.entries
                if entry.kind == "file"
                and entry.path.suffix in suffixes
                and entry.path.name not in excluded_names
                and (recursive or entry.path.parent == root)
            ),
        )

    @staticmethod
    def docs_source_paths(
        repository_root: Path,
        extra_roots: t.SequenceOf[Path] = (),
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Discover every physical source consumed by one docs render.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[Path]]``.

        from flext_cli import u as cli_u
        """
        roots = FlextInfraUtilitiesDocsScope.docs_repository_roots(
            repository_root,
            extra_roots,
        )
        if roots.failure:
            return r[t.VariadicTuple[Path]].from_failure(roots)
        return FlextInfraUtilitiesDocsGenerateSourcesMixin.docs_source_paths_for_roots(
            roots.value,
        )

    @staticmethod
    def docs_scope_source_roots(
        repository_root: Path,
        scope: m.Infra.DocScope,
        aggregate_scopes: t.SequenceOf[m.Infra.DocScope],
    ) -> t.VariadicTuple[Path]:
        """Elect the current scope and its actual shared metadata owners."""
        return tuple(
            dict.fromkeys((
                repository_root,
                *(
                    (item.path for item in aggregate_scopes)
                    if scope.name == c.Infra.RK_ROOT
                    else (scope.path,)
                ),
            ))
        )

    @staticmethod
    def docs_scope_from_sources(
        scope: m.Infra.DocScope,
        source_states: t.SequenceOf[m.Cli.AtomicFileState],
    ) -> m.Infra.DocScope:
        """Derive scope metadata and package identity from the captured inventory."""
        if scope.name == c.Infra.RK_ROOT:
            return scope
        state = FlextInfraUtilitiesDocsScope.project_state(
            scope.path,
            source_states=source_states,
        )
        if not FlextInfraUtilitiesDocsScope.docs_scope_enabled(state.docs_meta):
            msg = f"docs scope is disabled in captured metadata: {scope.path}"
            raise ValueError(msg)
        return scope.model_copy(
            update={
                "name": state.project_name,
                "package_name": state.package_name,
                "project_class": FlextInfraUtilitiesDocsScope.classify_project_from_meta(
                    state.project_name,
                    state.docs_meta,
                ),
            }
        )

    @staticmethod
    def docs_source_directories(
        roots: t.SequenceOf[Path],
        *,
        source_scope: Path | None = None,
    ) -> p.Result[t.VariadicTuple[m.Cli.AtomicDirectoryChainPlan]]:
        """Capture presence and physical ancestry used by docs discovery."""
        states: list[m.Cli.AtomicDirectoryChainPlan] = []
        for root in roots:
            for (
                path,
                _recursive,
                _suffixes,
            ) in FlextInfraUtilitiesDocsGenerateSourcesMixin._source_trees(
                root,
                source_scope,
            ):
                state = cli_u.Cli.atomic_plan_directory_chain(path)
                if state.failure:
                    return r[
                        t.VariadicTuple[m.Cli.AtomicDirectoryChainPlan]
                    ].from_failure(
                        state,
                    )
                states.append(state.value)
        return r[t.VariadicTuple[m.Cli.AtomicDirectoryChainPlan]].ok(tuple(states))

    @staticmethod
    def docs_source_paths_for_roots(
        roots: t.SequenceOf[Path],
        *,
        source_scope: Path | None = None,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Discover only the elected roots and declared template dependencies."""
        paths: set[Path] = set()
        for root in roots:
            collected = (
                FlextInfraUtilitiesDocsGenerateSourcesMixin._collected_root_paths(
                    root,
                    source_scope=source_scope,
                )
            )
            if collected.failure:
                return r[t.VariadicTuple[Path]].from_failure(collected)
            paths.update(collected.value)
        templates_root = FlextInfraConfig.ssot_config_dir().parent / "templates"
        templates = cli_u.Cli.template_capture_sources((
            templates_root / c.Infra.TEMPLATE_MKDOCS_PROJECT,
            templates_root / c.Infra.TEMPLATE_MKDOCS_ROOT,
        ))
        if templates.failure:
            return r[t.VariadicTuple[Path]].from_failure(templates)
        paths.update(state.path for state in templates.value)
        return r[t.VariadicTuple[Path]].ok(tuple(sorted(paths)))

    @staticmethod
    def _source_trees(
        root: Path,
        source_scope: Path | None,
    ) -> t.VariadicTuple[t.Triple[Path, bool, frozenset[str]]]:
        """Declare the source grammar once for capture and published membership."""
        return (
            (root / "config", False, frozenset({".yaml", ".yml"})),
            *(
                ((root / c.Infra.DEFAULT_SRC_DIR, True, frozenset({".py"})),)
                if source_scope is None or source_scope == root
                else ()
            ),
            (root / c.Infra.DIR_DOCS / "guides", False, frozenset({".md"})),
        )

    @staticmethod
    def docs_source_path_is_input(
        path: Path,
        roots: t.SequenceOf[Path],
        *,
        source_scope: Path | None = None,
    ) -> bool:
        """Derive whether an owned publication becomes an input of the same owner."""
        for root in roots:
            if path in {
                root / c.Infra.GITMODULES,
                root / c.PYPROJECT_FILENAME,
                root / c.Infra.DIR_DOCS / c.Infra.DOCS_CONFIG_FILENAME,
            }:
                return True
            for (
                tree,
                recursive,
                suffixes,
            ) in FlextInfraUtilitiesDocsGenerateSourcesMixin._source_trees(
                root,
                source_scope,
            ):
                if (
                    path.suffix in suffixes
                    and path.is_relative_to(tree)
                    and (recursive or path.parent == tree)
                    and not (path.suffix == ".md" and path.name == "README.md")
                ):
                    return True
        return False

    @classmethod
    def _collected_root_paths(
        cls,
        root: Path,
        *,
        source_scope: Path | None = None,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Collect one repository root's documented physical source paths.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[Path]]``.

        """
        # The docs configuration lives one directory down, and a repository
        # that has never generated documentation has no `docs/` yet. Reading
        # a leaf under a directory that does not exist is not "absent", it
        # is a failure, so its presence is established first.
        docs_root_present = cls._source_directory_exists(root / c.Infra.DIR_DOCS)
        if docs_root_present.failure:
            return r[t.VariadicTuple[Path]].from_failure(docs_root_present)
        paths: set[Path] = set()
        fixed_paths = (
            root / c.Infra.GITMODULES,
            root / c.PYPROJECT_FILENAME,
            *(
                (root / c.Infra.DIR_DOCS / c.Infra.DOCS_CONFIG_FILENAME,)
                if docs_root_present.value
                else ()
            ),
        )
        collectors = (
            cls._collected_fixed_paths(paths, fixed_paths),
            *(
                cls._collected_tree_paths(
                    paths,
                    tree,
                    recursive=recursive,
                    suffixes=suffixes,
                    excluded_names=(
                        frozenset({"README.md"}) if ".md" in suffixes else frozenset()
                    ),
                )
                for tree, recursive, suffixes in cls._source_trees(root, source_scope)
            ),
        )
        for collected in collectors:
            if collected.failure:
                return r[t.VariadicTuple[Path]].from_failure(collected)
        return r[t.VariadicTuple[Path]].ok(tuple(sorted(paths)))

    @staticmethod
    def _collected_fixed_paths(
        paths: set[Path],
        fixed_paths: t.SequenceOf[Path],
    ) -> p.Result[bool]:
        """Add each existing fixed path to the collected set.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for fixed_path in fixed_paths:
            state = cli_u.Cli.atomic_read_binary_file_state(
                fixed_path,
                required=False,
            )
            if state.failure:
                return r[bool].from_failure(state)
            if state.value.content is not None:
                paths.add(fixed_path)
        return r[bool].ok(value=True)

    @classmethod
    def _collected_tree_paths(
        cls,
        paths: set[Path],
        tree_root: Path,
        *,
        recursive: bool,
        suffixes: frozenset[str],
        excluded_names: frozenset[str] = frozenset(),
    ) -> p.Result[bool]:
        """Add one inventoried source tree's files to the collected set.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        tree_paths = cls._source_tree_files(
            tree_root,
            recursive=recursive,
            suffixes=suffixes,
            excluded_names=excluded_names,
        )
        if tree_paths.failure:
            return r[bool].from_failure(tree_paths)
        paths.update(tree_paths.value)
        return r[bool].ok(value=True)

    @staticmethod
    def docs_verify_source_topology(
        repository_root: Path,
        source_states: t.SequenceOf[m.Cli.AtomicFileState],
        *,
        extra_roots: t.SequenceOf[Path] = (),
        source_roots: t.SequenceOf[Path] = (),
        source_directories: t.SequenceOf[m.Cli.AtomicDirectoryChainPlan] = (),
        created_directories: t.SequenceOf[m.Cli.AtomicDirectoryState] = (),
        source_scope: Path | None = None,
    ) -> p.Result[bool]:
        """Admit only the current batch's source membership and directory ancestry.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        created = {item.path: item for item in created_directories}
        for expected in source_directories:
            observed = cli_u.Cli.atomic_plan_directory_chain(expected.target)
            if observed.failure:
                return r[bool].from_failure(observed)
            if observed.value != expected:
                owned_chain = tuple(created.get(path) for path in expected.directories)
                if not (
                    expected.directories
                    and all(item is not None for item in owned_chain)
                    and not observed.value.directories
                    and observed.value.anchor_path == expected.target
                    and observed.value.anchor_ancestry
                    == (
                        *expected.anchor_ancestry,
                        *(
                            (item.device, item.inode)
                            for item in owned_chain
                            if item is not None
                        ),
                    )
                ):
                    return r[bool].fail(
                        f"{c.Infra.DOCS_SOURCE_TOPOLOGY_RACE_MARKER}: {expected.target}",
                    )
        discovered = (
            FlextInfraUtilitiesDocsGenerateSourcesMixin.docs_source_paths_for_roots(
                source_roots,
                source_scope=source_scope,
            )
            if source_roots
            else FlextInfraUtilitiesDocsGenerateSourcesMixin.docs_source_paths(
                repository_root,
                extra_roots,
            )
        )
        if discovered.failure:
            return r[bool].from_failure(discovered)
        expected_paths = tuple(
            state.path for state in source_states if state.content is not None
        )
        if discovered.value != expected_paths:
            added = sorted(set(discovered.value).difference(expected_paths))
            removed = sorted(set(expected_paths).difference(discovered.value))
            return r[bool].fail(
                f"{c.Infra.DOCS_SOURCE_TOPOLOGY_RACE_MARKER}: "
                f"added={[path.as_posix() for path in added]}, "
                f"removed={[path.as_posix() for path in removed]}",
            )
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraUtilitiesDocsGenerateSourcesMixin"]
