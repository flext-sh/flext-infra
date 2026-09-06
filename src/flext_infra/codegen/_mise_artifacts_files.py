"""Exact filesystem-state primitives for Mise artifact transactions."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import stat
from typing import TYPE_CHECKING, Final

from flext_core import r
from flext_infra import c, m, u

if TYPE_CHECKING:
    from flext_infra import p

ARTIFACT_SPECS: Final[tuple[tuple[str, int], ...]] = (
    ("bin/mise", 0o755),
    ("bin/mise.cmd", 0o644),
    ("mise.lock", 0o644),
)
CONFIG_SPEC: Final[tuple[str, int]] = (c.Infra.MISE_TOML_FILENAME, 0o644)
PUBLICATION_SPECS: Final[tuple[tuple[str, int], ...]] = (CONFIG_SPEC, *ARTIFACT_SPECS)
ARTIFACT_NAMES: Final[tuple[str, ...]] = tuple(name for name, _mode in ARTIFACT_SPECS)
JOURNAL_NAME: Final[str] = "flext-infra-codegen-transaction-journal.json"
JOURNAL_MODE: Final[int] = 0o600
STATE_DIRECTORY: Final[Path] = Path(".state") / "mise-artifacts"
TRANSACTION_DIR_PREFIX: Final[str] = "transaction-"
TRANSACTION_ID_LENGTH: Final[int] = 32


def digest(content: bytes) -> str:
    """Return the exact lowercase SHA-256 identity for raw bytes."""
    return sha256(content).hexdigest()


def read_state(path: Path, *, required: bool) -> p.Result[m.Cli.AtomicFileState]:
    """Read exact state through the canonical descriptor-authenticated owner."""
    return u.Cli.atomic_read_binary_file_state(path, required=required)


def physical_directory_identity(path: Path) -> p.Result[tuple[int, int]]:
    """Return the device/inode identity of one physical directory."""
    try:
        observed = path.lstat()
    except OSError as exc:
        return r[tuple[int, int]].fail_op("inspect generation directory", exc)
    reparse = getattr(observed, "st_file_attributes", 0) & getattr(
        stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0
    )
    if not stat.S_ISDIR(observed.st_mode) or reparse:
        return r[tuple[int, int]].fail(f"generation directory is not physical: {path}")
    return r[tuple[int, int]].ok((observed.st_dev, observed.st_ino))


def write_publication(publication: m.Infra.CodegenStagedFile) -> p.Result[bool]:
    """Consume one staged create/replace/mode/delete through the CLI owner."""
    before = publication.before
    replacement = publication.replacement
    if replacement is None:
        return delete_state(before)
    if replacement.content is None or replacement.mode is None:
        return r[bool].fail(f"codegen staged replacement is absent: {replacement.path}")
    published = u.Cli.atomic_publish_staged_binary_file_guarded(before, replacement)
    if published.failure:
        return r[bool].from_failure(published)
    observed = published.value
    observed_identity = (
        observed.path,
        observed.parent_device,
        observed.parent_inode,
        observed.content,
        observed.mode,
        observed.device,
        observed.inode,
        observed.link_count,
        observed.file_attributes,
        observed.reparse_tag,
    )
    replacement_identity = (
        before.path,
        before.parent_device,
        before.parent_inode,
        replacement.content,
        replacement.mode,
        replacement.device,
        replacement.inode,
        replacement.link_count,
        replacement.file_attributes,
        replacement.reparse_tag,
    )
    if observed_identity != replacement_identity:
        return r[bool].fail(
            f"published codegen file differs from staged identity: {before.path}"
        )
    return r[bool].ok(True)


def delete_state(state: m.Cli.AtomicFileState) -> p.Result[bool]:
    """Delete one exact existing state through the CLI owner."""
    if (
        state.content is None
        or state.mode is None
        or state.device is None
        or state.inode is None
    ):
        return r[bool].fail(f"cannot delete absent codegen file state: {state.path}")
    return u.Cli.atomic_delete_binary_file_guarded(state)


def workspace_relative(root: Path, path: Path) -> p.Result[str]:
    """Return a canonical lexical workspace-relative path selector."""
    absolute_root = root.absolute()
    try:
        relative = path.absolute().relative_to(absolute_root)
    except ValueError as exc:
        return r[str].fail_op(f"resolve workspace artifact {path}", exc)
    selector = relative.as_posix()
    if not selector or selector == "." or ".." in relative.parts:
        return r[str].fail(f"invalid workspace artifact path: {path}")
    return r[str].ok(selector)


def resolve_relative(root: Path, selector: str, *, purpose: str) -> p.Result[Path]:
    """Resolve a lexical relative selector without dereferencing its leaf."""
    relative = Path(selector)
    if (
        relative.is_absolute()
        or relative.as_posix() != selector
        or not relative.parts
        or ".." in relative.parts
    ):
        return r[Path].fail(f"unsafe {purpose} path: {selector}")
    absolute_root = root.absolute()
    candidate = (absolute_root / relative).absolute()
    if not candidate.is_relative_to(absolute_root):
        return r[Path].fail(f"{purpose} path escapes its root: {selector}")
    return r[Path].ok(candidate)


__all__: list[str] = [
    "ARTIFACT_NAMES",
    "ARTIFACT_SPECS",
    "BOOTSTRAP_DIR_NAME",
    "CONFIG_SPEC",
    "JOURNAL_MODE",
    "JOURNAL_NAME",
    "PUBLICATION_SPECS",
    "STATE_DIRECTORY",
    "TRANSACTION_DIR_PREFIX",
    "delete_state",
    "digest",
    "physical_directory_identity",
    "read_state",
    "resolve_relative",
    "workspace_relative",
    "write_publication",
]
