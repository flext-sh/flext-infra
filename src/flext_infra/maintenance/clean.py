"""Owner-scoped disposable cleanup for the generated ``clean`` verb.

The typed Make policy elects disposable resources. Git owns authored inputs and
repository boundaries; the shared physical-file owner authenticates removals.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from fnmatch import fnmatchcase
from pathlib import Path
from typing import TYPE_CHECKING, override

from flext_infra import c, r, s, u

if TYPE_CHECKING:
    from flext_infra import m, p, t


class FlextInfraCleanService(s[int]):
    """Remove declared disposables without crossing source or runtime ownership."""

    @override
    def execute(self) -> p.Result[int]:
        """Authenticate every target before removing unchanged owned resources.

        Returns:
            The resulting ``p.Result[int]``.

        """
        root = self.repository_root.expanduser().absolute()
        u.Infra.exact_worktree_root(root).unwrap()
        inputs = u.Infra.load_codegen_inputs(root).unwrap()
        codegen = inputs.spec
        with u.Cli.file_changes_lock(u.Infra.mutation_lock_path(root).unwrap()):
            directories, files = self._targets(root, codegen)
            for directory in directories:
                self._require_owned(root, directory.root.path, codegen)
                u.Cli.atomic_verify_binary_file_states(inputs.sources).unwrap()
                if self.apply_changes:
                    u.Cli.info(f"clean: remove {directory.root.path.relative_to(root)}")
                    u.Cli.atomic_cleanup_physical_tree_guarded(directory).unwrap()
                else:
                    u.Cli.info(f"clean: {directory.root.path.relative_to(root)}")
            for file in files:
                self._require_owned(root, file.path, codegen)
                u.Cli.atomic_verify_binary_file_states(inputs.sources).unwrap()
                if self.apply_changes:
                    u.Cli.info(f"clean: remove {file.path.relative_to(root)}")
                    u.Cli.atomic_delete_binary_file_guarded(file).unwrap()
                else:
                    u.Cli.info(f"clean: {file.path.relative_to(root)}")
        u.Cli.info(
            f"clean: {'removed' if self.apply_changes else 'selected'} "
            f"{len(directories) + len(files)} owned disposable resource(s)",
        )
        return r[int].ok(0)

    @classmethod
    def _targets(
        cls,
        root: Path,
        codegen: m.Infra.CodegenConfigSpec,
    ) -> t.Pair[
        tuple[m.Cli.AtomicPhysicalTreeManifest, ...],
        tuple[m.Cli.AtomicFileState, ...],
    ]:
        """Elect physical targets while retaining every foreign/runtime boundary.

        Returns:
            The disposable directory manifests and file states.

        """
        policy = codegen.make.clean
        cls._require_declarations(root, codegen)
        declarations = u.Infra.git_submodule_declarations(root).unwrap()
        members = tuple(root / member.path for member in declarations)
        protected = cls._protected_names(codegen)
        excluded = (*codegen.analysis_excluded_dirs, *codegen.source_scan_ignored)
        directories: list[m.Cli.AtomicPhysicalTreeManifest] = []
        files: list[m.Cli.AtomicFileState] = []
        pending = [root]
        while pending:
            parent = pending.pop()
            inventory = u.Cli.atomic_inventory_physical_directory(parent).unwrap()
            if parent != root and any(
                entry.name == c.Infra.GIT_DIR for entry in inventory.entries
            ):
                continue
            for entry in inventory.entries:
                path = parent / entry.name
                if (
                    entry.name in protected
                    or path in members
                    or (parent == root and entry.name == c.Infra.GIT_WORKTREES_DIRNAME)
                ):
                    continue
                directory_target = entry.name in policy.cache_dirs or (
                    parent == root and entry.name in policy.root_dirs
                )
                file_target = (
                    parent == root and entry.name in policy.root_files
                ) or any(
                    fnmatchcase(entry.name, pattern) for pattern in policy.trace_globs
                )
                if directory_target:
                    directories.append(
                        cls._directory_manifest(
                            root, path, entry.kind, members, codegen
                        )
                    )
                elif file_target:
                    files.append(cls._file_state(root, path, entry.kind, codegen))
                elif entry.kind == "directory" and not any(
                    fnmatchcase(entry.name, pattern) for pattern in excluded
                ):
                    pending.append(path)
        return tuple(directories), tuple(files)

    @classmethod
    def _require_declarations(
        cls,
        root: Path,
        codegen: m.Infra.CodegenConfigSpec,
    ) -> None:
        """Require single-name resources and filename globs in the clean policy.

        Raises:
            ValueError: When a declaration is not one relative name or filename glob.

        """
        policy = codegen.make.clean
        for name in (*policy.cache_dirs, *policy.root_dirs, *policy.root_files):
            if Path(name).name != name or name in {".", ".."}:
                msg = f"clean declarations require one relative resource name: {name}"
                raise ValueError(msg)
            cls._require_runtime_scope(root, root / name, codegen)
        for pattern in policy.trace_globs:
            if Path(pattern).name != pattern or pattern in {".", ".."}:
                msg = f"clean trace patterns require one filename glob: {pattern}"
                raise ValueError(msg)

    @classmethod
    def _directory_manifest(
        cls,
        root: Path,
        path: Path,
        kind: str,
        members: tuple[Path, ...],
        codegen: m.Infra.CodegenConfigSpec,
    ) -> m.Cli.AtomicPhysicalTreeManifest:
        """Authenticate one disposable directory and inventory its physical tree.

        Returns:
            The physical tree manifest of the owned directory.

        Raises:
            ValueError: When the target is not a physical directory or contains
                protected runtime state.

        """
        if kind != "directory":
            msg = f"clean requires a physical disposable directory: {path}"
            raise ValueError(msg)
        cls._require_owned(root, path, codegen)
        manifest = u.Cli.atomic_inventory_physical_tree(path).unwrap()
        for child in manifest.entries:
            cls._require_runtime_scope(root, child.path, codegen)
            if child.path in members:
                msg = f"clean target contains protected runtime state: {child.path}"
                raise ValueError(msg)
        return manifest

    @classmethod
    def _file_state(
        cls,
        root: Path,
        path: Path,
        kind: str,
        codegen: m.Infra.CodegenConfigSpec,
    ) -> m.Cli.AtomicFileState:
        """Authenticate one disposable regular file and capture its state.

        Returns:
            The captured state of the owned file.

        Raises:
            ValueError: When the target is not a regular file.

        """
        if kind != "file":
            msg = f"clean requires a regular disposable file: {path}"
            raise ValueError(msg)
        cls._require_owned(root, path, codegen)
        return u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()

    @staticmethod
    def _protected_names(codegen: m.Infra.CodegenConfigSpec) -> frozenset[str]:
        """Derive runtime identities that disposable declarations cannot retire.

        Returns:
            The protected runtime names.

        """
        return frozenset({
            c.Infra.GIT_DIR,
            c.Infra.ENVIRONMENT_DIRECTORY,
            c.Infra.WORKTREES_DIRNAME,
            c.Infra.TRANSACTION_STATE_DIRNAME,
            c.Infra.BEADS_DIRNAME,
            c.Infra.JOURNAL_NAME,
            c.Infra.MISE_LOCK_JOURNAL_FILENAME,
            c.Infra.CODEGEN_TRANSACTION_LOCK_FILENAME,
            codegen.make.testmon_cache.database_filename,
        })

    @classmethod
    def _require_owned(
        cls,
        root: Path,
        target: Path,
        codegen: m.Infra.CodegenConfigSpec,
    ) -> None:
        """Refuse source inputs, nested owners, locks and persistent test history.

        Raises:
            ValueError: When the target holds source, a declared member, or
                protected runtime state.

        """
        cls._require_runtime_scope(root, target, codegen)
        sources = u.Infra.git_source_scope_paths(root)
        if sources is None:
            msg = f"clean requires the target's native Git source inventory: {root}"
            raise ValueError(msg)
        if any(source == target or source.is_relative_to(target) for source in sources):
            msg = f"clean target contains authored or unpublished source: {target}"
            raise ValueError(msg)
        declarations = u.Infra.git_submodule_declarations(root).unwrap()
        if any((root / member.path).is_relative_to(target) for member in declarations):
            msg = f"clean target contains a declared member: {target}"
            raise ValueError(msg)

    @classmethod
    def _require_runtime_scope(
        cls,
        root: Path,
        target: Path,
        codegen: m.Infra.CodegenConfigSpec,
    ) -> None:
        """Keep every selected physical leaf inside its disposable owner.

        Raises:
            ValueError: When the target is protected ownership or runtime state.

        """
        lock_suffix = Path(c.Infra.CODEGEN_TRANSACTION_LOCK_FILENAME).suffix
        database = codegen.make.testmon_cache.database_filename
        if (
            not target.is_relative_to(root)
            or target == root
            or target.relative_to(root).parts[0] == c.Infra.GIT_WORKTREES_DIRNAME
            or any(
                part in cls._protected_names(codegen)
                or part.endswith(lock_suffix)
                or part.startswith(f"{database}-")
                for part in target.relative_to(root).parts
            )
        ):
            msg = f"clean cannot retire protected ownership or runtime state: {target}"
            raise ValueError(msg)


__all__: list[str] = ["FlextInfraCleanService"]
