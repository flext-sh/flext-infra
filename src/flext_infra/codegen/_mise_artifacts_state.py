"""Persistent coordination-state lifecycle for Mise transactions."""

from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import m, u
from flext_infra.codegen import _mise_artifacts_files as files

if TYPE_CHECKING:
    from flext_infra import p


def prepare_state_roots(layout: m.Infra.MiseToolchainWorkspaceLayout) -> p.Result[bool]:
    """Create every configured persistent state root before transaction effects."""
    common = _prepare_state_root(layout.scope_root.parent, layout.state_root)
    if common.failure:
        return common
    for project in layout.projects:
        prepared = _prepare_state_root(
            layout.state_root, project.transaction_root.parent
        )
        if prepared.failure:
            return prepared
        try:
            staging_device = project.transaction_root.parent.stat().st_dev
            destination_parents = {
                artifact.parent
                for artifact in (
                    project.artifacts.config,
                    project.artifacts.unix_launcher,
                    project.artifacts.windows_launcher,
                    project.artifacts.lock,
                )
            }
            absent_parent = next(
                (parent for parent in destination_parents if not parent.is_dir()), None
            )
            if absent_parent is not None:
                return r[bool].fail(
                    f"Mise destination parent is absent: {absent_parent}"
                )
            destination_devices = {
                parent.stat().st_dev for parent in destination_parents
            }
            if destination_devices != {staging_device}:
                return r[bool].fail(
                    f"Mise state is not on destination filesystem: {project.selector}"
                )
        except OSError as exc:
            return r[bool].fail_op("inspect Mise state filesystem", exc)
    return r[bool].ok(True)


def prepare_common_state_root(scope_root: Path, state_root: Path) -> p.Result[bool]:
    """Create only the umbrella coordination root before acquiring its lock."""
    return _prepare_state_root(scope_root.parent, state_root)


def validate_lock_path(state_root: Path, *, require_existing: bool) -> p.Result[Path]:
    """Authenticate the persistent lock path before FileLock opens it."""
    lock_path = state_root / files.LOCK_NAME
    try:
        parent = lock_path.parent.lstat()
    except OSError as exc:
        return r[Path].fail_op("inspect Mise lock parent", exc)
    if not stat.S_ISDIR(parent.st_mode) or _is_reparse(parent):
        return r[Path].fail(f"Mise lock parent is not physical: {lock_path.parent}")
    if not lock_path.exists() and not lock_path.is_symlink():
        if require_existing:
            return r[Path].fail(f"Mise transaction lock is absent: {lock_path}")
        return r[Path].ok(lock_path)
    try:
        state = lock_path.lstat()
    except OSError as exc:
        return r[Path].fail_op("inspect Mise transaction lock", exc)
    if not stat.S_ISREG(state.st_mode) or state.st_nlink != 1 or _is_reparse(state):
        return r[Path].fail(f"Mise transaction lock is not physical: {lock_path}")
    return r[Path].ok(lock_path)


def lock_holder(lock_path: Path) -> p.Result[str]:
    """Resolve the exact Linux process holding one authenticated file lock."""
    if os.name != "posix" or not Path("/proc/locks").is_file():
        return r[str].fail("lock-holder diagnostics require Linux /proc/locks")
    try:
        lock_state = lock_path.stat()
        identity = (
            f"{os.major(lock_state.st_dev):02x}:"
            f"{os.minor(lock_state.st_dev):02x}:{lock_state.st_ino}"
        )
        records = Path("/proc/locks").read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return r[str].fail_op("inspect Mise lock holder", exc)
    inode = str(lock_state.st_ino)
    inode_records: list[str] = []
    for record in records:
        fields = record.split()
        if len(fields) < 6 or fields[5].rsplit(":", 1)[-1] != inode:
            continue
        inode_records.append(record)
        pid = fields[4]
        descriptor_matches: list[Path] = []
        try:
            for descriptor in Path(f"/proc/{pid}/fd").iterdir():
                try:
                    descriptor_state = descriptor.stat()
                    descriptor_target = descriptor.readlink()
                except FileNotFoundError:
                    continue
                if (
                    descriptor_state.st_ino == lock_state.st_ino
                    and descriptor_target == lock_path
                ):
                    descriptor_matches.append(descriptor)
        except OSError as exc:
            return r[str].fail_op(
                f"inspect Mise lock-holder descriptors for process {pid}", exc
            )
        if fields[5] != identity and not descriptor_matches:
            continue
        try:
            command = (
                Path(f"/proc/{pid}/cmdline")
                .read_bytes()
                .replace(b"\0", b" ")
                .decode("utf-8")
                .strip()
            )
            cwd = Path(f"/proc/{pid}/cwd").readlink()
            stat_fields = (
                Path(f"/proc/{pid}/stat")
                .read_text(encoding="utf-8")
                .split(") ", maxsplit=1)[1]
                .split()
            )
            start_seconds = int(stat_fields[19]) / int(os.sysconf("SC_CLK_TCK"))
            uptime_seconds = float(
                Path("/proc/uptime").read_text(encoding="utf-8").split(maxsplit=1)[0]
            )
            elapsed_seconds = uptime_seconds - start_seconds
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            return r[str].fail_op(f"inspect Mise lock-holder process {pid}", exc)
        if not command:
            return r[str].fail(f"Mise lock-holder process has no command: pid={pid}")
        return r[str].ok(
            f"pid={pid} elapsed={elapsed_seconds:.2f}s cwd={cwd} command={command} "
            f"descriptors={descriptor_matches} "
            f"observed_lock_identity={fields[5]} expected_lock_identity={identity}"
        )
    if inode_records:
        return r[str].fail(
            f"Mise lock has only foreign-device inode matches: path={lock_path} "
            f"identity={identity} records={inode_records}"
        )
    return r[str].fail(
        f"Mise lock has no observable holder: path={lock_path} identity={identity}"
    )


def journal_state(
    layout: m.Infra.MiseToolchainWorkspaceLayout,
) -> p.Result[m.Cli.AtomicFileState]:
    """Read the common journal without creating its parent in check mode."""
    return journal_state_at(layout.state_root)


def journal_state_at(state_root: Path) -> p.Result[m.Cli.AtomicFileState]:
    """Read the common journal before mutable workspace topology is loaded."""
    journal = state_root / files.JOURNAL_NAME
    return u.Cli.atomic_read_binary_file_state(journal, required=False)


def transaction_residue(
    layout: m.Infra.MiseToolchainWorkspaceLayout,
) -> tuple[Path, ...]:
    """Return every existing or aliased per-project transaction root."""
    return tuple(
        project.transaction_root
        for project in layout.projects
        if project.transaction_root.exists() or project.transaction_root.is_symlink()
    )


def create_transaction_roots(
    layout: m.Infra.MiseToolchainWorkspaceLayout,
) -> p.Result[bool]:
    """Create one fresh private transaction root on each destination filesystem."""
    residue = transaction_residue(layout)
    if residue:
        return r[bool].fail(f"Mise transaction staging already exists: {residue[0]}")
    created: list[tuple[Path, tuple[int, int]]] = []
    try:
        for project in layout.projects:
            project.transaction_root.mkdir(mode=0o700, exist_ok=False)
            state = project.transaction_root.lstat()
            created.append((project.transaction_root, (state.st_dev, state.st_ino)))
    except OSError as exc:
        cleanup = _remove_exact(tuple(created))
        if cleanup.failure:
            return r[bool].fail(f"create Mise transaction roots failed ({exc}); "
            f"cleanup failed ({cleanup.error})", exception=exc)
        return r[bool].fail_op("create Mise transaction roots", exc)
    return r[bool].ok(True)


def remove_transaction_roots(
    layout: m.Infra.MiseToolchainWorkspaceLayout,
) -> p.Result[bool]:
    """Remove only preflighted literal transaction roots owned by this plan."""
    targets: list[tuple[Path, tuple[int, int]]] = []
    for project in layout.projects:
        valid = _validate_transaction_root(project.transaction_root)
        if valid.failure:
            return r[bool].from_failure(valid)
        if valid.value:
            targets.append((project.transaction_root, valid.value[0]))
    return _remove_exact(tuple(targets))


def validate_transaction_roots(
    layout: m.Infra.MiseToolchainWorkspaceLayout,
) -> p.Result[bool]:
    """Authenticate every existing staging and recovery root."""
    for project in layout.projects:
        transaction = _validate_transaction_root(project.transaction_root)
        if transaction.failure:
            return r[bool].from_failure(transaction)
        if not transaction.value:
            continue
        recovery_root = project.transaction_root / "recovery"
        if not recovery_root.exists() and not recovery_root.is_symlink():
            continue
        try:
            recovery_state = recovery_root.lstat()
        except OSError as exc:
            return r[bool].fail_op("inspect Mise recovery root", exc)
        if not stat.S_ISDIR(recovery_state.st_mode) or _is_reparse(recovery_state):
            return r[bool].fail(f"Mise recovery root is not physical: {recovery_root}")
    return r[bool].ok(True)


def _prepare_state_root(anchor: Path, target: Path) -> p.Result[bool]:
    cursor = anchor.absolute()
    try:
        relative = target.absolute().relative_to(cursor)
        for part in relative.parts:
            cursor /= part
            if not cursor.exists() and not cursor.is_symlink():
                cursor.mkdir(mode=0o700, exist_ok=False)
            state = cursor.lstat()
            if not stat.S_ISDIR(state.st_mode) or _is_reparse(state):
                return r[bool].fail(f"Mise state path is not physical: {cursor}")
    except OSError as exc:
        return r[bool].fail_op("prepare persistent Mise state", exc)
    return r[bool].ok(True)


def _validate_transaction_root(target: Path) -> p.Result[tuple[tuple[int, int], ...]]:
    if not target.exists() and not target.is_symlink():
        return r[tuple[tuple[int, int], ...]].ok(())
    if target.name != files.TRANSACTION_DIR_NAME or target.is_symlink():
        return r[tuple[tuple[int, int], ...]].fail(
            f"refusing invalid Mise transaction target: {target}"
        )
    try:
        state = target.lstat()
    except OSError as exc:
        return r[tuple[tuple[int, int], ...]].fail_op(
            "inspect Mise transaction target", exc
        )
    if not stat.S_ISDIR(state.st_mode) or _is_reparse(state):
        return r[tuple[tuple[int, int], ...]].fail(
            f"Mise transaction target is not physical: {target}"
        )
    return r[tuple[tuple[int, int], ...]].ok(((state.st_dev, state.st_ino),))


def _remove_exact(targets: tuple[tuple[Path, tuple[int, int]], ...]) -> p.Result[bool]:
    try:
        for target, expected_identity in targets:
            state = target.lstat()
            if (
                (state.st_dev, state.st_ino) != expected_identity
                or not stat.S_ISDIR(state.st_mode)
                or _is_reparse(state)
            ):
                return r[bool].fail(
                    f"Mise transaction target changed before cleanup: {target}"
                )
            shutil.rmtree(target)
    except OSError as exc:
        return r[bool].fail_op("remove exact Mise transaction staging", exc)
    return r[bool].ok(True)


def _is_reparse(state: os.stat_result) -> bool:
    attributes = getattr(state, "st_file_attributes", 0)
    marker = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(attributes & marker)


__all__: list[str] = [
    "create_transaction_roots",
    "journal_state",
    "journal_state_at",
    "prepare_common_state_root",
    "prepare_state_roots",
    "remove_transaction_roots",
    "transaction_residue",
    "validate_lock_path",
    "validate_transaction_roots",
]
