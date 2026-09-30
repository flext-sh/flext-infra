"""Guarded filesystem effects for the Git capture owner."""

from __future__ import annotations

import os
import stat
from pathlib import Path

from flext_cli import u

from flext_infra import m, t

from .state_publication import FlextInfraUtilitiesGitStatePublicationMixin
from .worktree_io import FlextInfraUtilitiesGitWorktreeIO


class FlextInfraUtilitiesGitStateFilesMixin(
    FlextInfraUtilitiesGitStatePublicationMixin
):
    """Consume CLI physical-state primitives under the shared writer lease.

    File effects use the CLI's guarded atomic-file primitives. Symlink
    effects are implemented here — the Git capture owner's own guarded
    compare-and-swap semantics over ``os`` primitives — because the CLI
    surface has no guarded symlink-state verbs (flagged upstream owner gap).
    """

    @staticmethod
    def _state_require_directory_scope(
        root: Path, path: Path, owned: t.SequenceOf[Path]
    ) -> None:
        manifest = u.Cli.atomic_inventory_physical_tree(root / path).unwrap()
        for entry in manifest.entries:
            relative = entry.path.relative_to(root)
            if entry.kind != "directory" and relative not in owned:
                msg = f"directory transition would remove unowned content: {relative}"
                raise ValueError(msg)

    @classmethod
    def _state_require_payload(
        cls,
        root: Path,
        path: Path,
        before_content: bytes | None,
        before_mode: int,
        allowed: t.SequenceOf[m.Infra.GitWorktreeFileState | None],
    ) -> None:
        relative = path.relative_to(root)
        if before_content is None:
            mode = "100644"
        else:
            mode = "120000" if stat.S_ISLNK(before_mode) else (
                "100755" if before_mode & stat.S_IXUSR else "100644"
            )
        if before_content is None and None in allowed:
            return
        if before_content is not None:
            with FlextInfraUtilitiesGitWorktreeIO.git_stdin(
                before_content
            ) as stream:
                oid = cls._repo(root).git.hash_object("--stdin", istream=stream)
            observed = m.Infra.GitWorktreeFileState(
                path=relative, mode=mode, permissions=before_mode, oid=oid
            )
            if observed in allowed:
                return
        msg = f"owned file changed before guarded effect: {relative}"
        raise ValueError(msg)

    @staticmethod
    def _state_symlink_target(destination: Path) -> bytes | None:
        """Return the current symlink target bytes, or ``None`` when absent."""
        if not destination.is_symlink():
            return None
        return os.fsencode(destination.readlink())

    @classmethod
    def _state_effect_file(
        cls,
        root: Path,
        path: Path,
        desired: m.Infra.GitWorktreeFileState | None,
        allowed: t.SequenceOf[m.Infra.GitWorktreeFileState | None],
    ) -> None:
        destination = root / path
        before_target = cls._state_symlink_target(destination)
        if before_target is not None:
            cls._state_require_payload(
                root, path, before_target, stat.S_IFLNK, allowed
            )
            if desired is not None and desired.mode == "120000":
                payload = cls._repo(root).odb.stream(bytes.fromhex(desired.oid)).read()
                if payload != before_target:
                    destination.unlink()
                    destination.symlink_to(os.fsdecode(payload))
                return
            destination.unlink()
        else:
            before_file = u.Cli.atomic_read_binary_file_state(
                destination, required=False
            ).unwrap()
            cls._state_require_payload(
                root,
                path,
                before_file.content,
                before_file.mode if before_file.mode is not None else 0,
                allowed,
            )
            if desired is not None and desired.mode != "120000":
                payload = cls._repo(root).odb.stream(bytes.fromhex(desired.oid)).read()
                u.Cli.atomic_write_binary_file_guarded(
                    before_file, payload, permission_mode=desired.permissions
                ).unwrap()
                return
            if before_file.content is not None:
                u.Cli.atomic_delete_binary_file_guarded(before_file).unwrap()
        if desired is not None and desired.mode == "120000":
            # A kind transition has a recorded, recoverable absent intermediate.
            if cls._state_symlink_target(destination) is not None:
                msg = f"destination appeared during kind transition: {path}"
                raise ValueError(msg)
            payload = cls._repo(root).odb.stream(bytes.fromhex(desired.oid)).read()
            destination.symlink_to(os.fsdecode(payload))
        elif desired is not None:
            cls._state_effect_file(root, path, desired, (None,))

    @staticmethod
    def _state_remove_empty_tree(path: Path) -> None:
        manifest = u.Cli.atomic_inventory_physical_tree(path).unwrap()
        if any(entry.kind != "directory" for entry in manifest.entries):
            msg = f"directory gained content before file replacement: {path}"
            raise ValueError(msg)
        u.Cli.atomic_cleanup_physical_tree_guarded(manifest).unwrap()


__all__: list[str] = ["FlextInfraUtilitiesGitStateFilesMixin"]
