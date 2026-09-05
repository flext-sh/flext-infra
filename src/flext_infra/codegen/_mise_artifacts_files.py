"""Exact filesystem-state primitives for Mise artifact transactions."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Final

from flext_core import r
from flext_infra import c, m

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
JOURNAL_NAME: Final[str] = "journal.json"
JOURNAL_MODE: Final[int] = 0o600
LOCK_NAME: Final[str] = "publication.lock"
PROJECTS_DIR_NAME: Final[str] = "projects"
ROOT_PROJECT_DIR_NAME: Final[str] = "root"
TRANSACTION_DIR_NAME: Final[str] = "transaction"


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


def source_selector(root: Path, path: Path) -> p.Result[str]:
    """Encode an authenticated source inside the scope or by canonical absolute path."""
    absolute_root = root.absolute()
    candidate = path.absolute()
    if candidate.is_relative_to(absolute_root):
        return workspace_relative(absolute_root, candidate)
    if (
        not path.is_absolute()
        or not path.name
        or ".." in path.parts
        or Path(os.path.normpath(path)) != path
    ):
        return r[str].fail(f"invalid external codegen source path: {path}")
    return r[str].ok(path.as_posix())


def resolve_source(root: Path, selector: str) -> p.Result[Path]:
    """Resolve one canonical journal source without widening write ownership."""
    candidate = Path(selector)
    if not candidate.is_absolute():
        return resolve_relative(root, selector, purpose="Mise journal source")
    if (
        not candidate.name
        or ".." in candidate.parts
        or Path(os.path.normpath(candidate)) != candidate
        or candidate.is_relative_to(root.absolute())
    ):
        return r[Path].fail(f"unsafe external Mise journal source path: {selector}")
    return r[Path].ok(candidate)


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


def project_for_path(
    layout: m.Infra.MiseToolchainWorkspaceLayout, path: Path
) -> p.Result[m.Infra.MiseToolchainProjectLayout]:
    """Resolve one destination to its most-specific selected project owner."""
    candidate = path.absolute()
    if candidate.is_relative_to(layout.state_root.absolute()):
        return r[m.Infra.MiseToolchainProjectLayout].fail(
            f"managed path enters codegen transaction state: {path}"
        )
    owners = tuple(
        project
        for project in layout.projects
        if candidate.is_relative_to(project.root.absolute())
    )
    if not owners:
        return r[m.Infra.MiseToolchainProjectLayout].fail(
            f"managed path is outside selected project topology: {path}"
        )
    deepest = max(len(project.root.parts) for project in owners)
    selected = tuple(
        project for project in owners if len(project.root.parts) == deepest
    )
    if len(selected) != 1:
        return r[m.Infra.MiseToolchainProjectLayout].fail(
            f"managed path has ambiguous project ownership: {path}"
        )
    return r[m.Infra.MiseToolchainProjectLayout].ok(selected[0])


def missing_parent_directories(
    layout: m.Infra.MiseToolchainWorkspaceLayout, targets: tuple[Path, ...]
) -> p.Result[tuple[Path, ...]]:
    """Return the exact destination directories absent at preflight."""
    result_type = r[tuple[Path, ...]]
    missing: set[Path] = set()
    for target in targets:
        owner = project_for_path(layout, target)
        if owner.failure:
            return result_type.from_failure(owner)
        root = owner.value.root.absolute()
        if not root.is_dir() or root.is_symlink():
            return result_type.fail(f"invalid codegen project root: {root}")
        current = root
        relative_parent = target.absolute().parent.relative_to(root)
        ancestor_absent = False
        for part in relative_parent.parts:
            current /= part
            if current.is_symlink():
                return result_type.fail(
                    f"codegen destination directory is a symlink: {current}"
                )
            if current.exists():
                if ancestor_absent or not current.is_dir():
                    return result_type.fail(
                        f"invalid codegen destination directory: {current}"
                    )
                continue
            ancestor_absent = True
            missing.add(current)
    return result_type.ok(
        tuple(sorted(missing, key=lambda path: (len(path.parts), str(path))))
    )


def create_directories(
    layout: m.Infra.MiseToolchainWorkspaceLayout, selectors: tuple[str, ...]
) -> p.Result[bool]:
    """Create only journal-authorized absent directories, parents first."""
    for selector in selectors:
        resolved = resolve_relative(
            layout.scope_root, selector, purpose="codegen destination directory"
        )
        if resolved.failure:
            return r[bool].from_failure(resolved)
        target = resolved.value
        if target.exists() or target.is_symlink():
            return r[bool].fail(
                f"codegen destination directory appeared after preflight: {target}"
            )
        if not target.parent.is_dir() or target.parent.is_symlink():
            return r[bool].fail(
                f"codegen destination directory parent is invalid: {target.parent}"
            )
        try:
            target.mkdir(mode=0o755, exist_ok=False)
        except OSError as exc:
            return r[bool].fail_op(
                f"create codegen destination directory {target}", exc
            )
    return r[bool].ok(True)


def remove_created_directories(
    layout: m.Infra.MiseToolchainWorkspaceLayout, selectors: tuple[str, ...]
) -> p.Result[bool]:
    """Remove only journal-authorized directories, children first."""
    for selector in reversed(selectors):
        resolved = resolve_relative(
            layout.scope_root, selector, purpose="codegen destination directory"
        )
        if resolved.failure:
            return r[bool].from_failure(resolved)
        target = resolved.value
        if not target.exists() and not target.is_symlink():
            continue
        if target.is_symlink() or not target.is_dir():
            return r[bool].fail(
                f"created codegen directory has foreign state: {target}"
            )
        try:
            target.rmdir()
        except OSError as exc:
            return r[bool].fail_op(
                f"remove created codegen destination directory {target}", exc
            )
    return r[bool].ok(True)


def transaction_sources(
    plan: m.Infra.MiseToolchainWorkspacePlan,
    managed_plans: tuple[m.Infra.CodegenFilePlan, ...],
) -> p.Result[tuple[m.Cli.AtomicFileState, ...]]:
    """Return one deterministic immutable state for every transaction source."""
    result_type = r[tuple[m.Cli.AtomicFileState, ...]]
    by_path: dict[Path, m.Cli.AtomicFileState] = {}
    candidates = (
        *(source for project in plan.projects for source in project.config.sources),
        *(source for item in managed_plans for source in item.source_states),
    )
    for source in candidates:
        existing = by_path.get(source.path)
        if existing is not None and existing != source:
            return result_type.fail(
                f"codegen source has conflicting snapshots: {source.path}"
            )
        by_path[source.path] = source
    ordered: list[tuple[str, m.Cli.AtomicFileState]] = []
    for source in by_path.values():
        selector = source_selector(plan.layout.scope_root, source.path)
        if selector.failure:
            return result_type.from_failure(selector)
        ordered.append((selector.value, source))
    return result_type.ok(tuple(source for _, source in sorted(ordered)))


__all__: list[str] = [
    "ARTIFACT_NAMES",
    "ARTIFACT_SPECS",
    "CONFIG_SPEC",
    "JOURNAL_MODE",
    "JOURNAL_NAME",
    "LOCK_NAME",
    "PROJECTS_DIR_NAME",
    "PUBLICATION_SPECS",
    "ROOT_PROJECT_DIR_NAME",
    "TRANSACTION_DIR_NAME",
    "create_directories",
    "missing_parent_directories",
    "project_for_path",
    "remove_created_directories",
    "resolve_relative",
    "resolve_source",
    "source_selector",
    "transaction_sources",
    "workspace_relative",
]
