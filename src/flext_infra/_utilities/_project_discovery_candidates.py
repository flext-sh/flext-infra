"""Project candidate discovery for flext-infra utilities.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_cli import u
from flext_infra import c
from flext_infra._utilities._project_discovery_shape import (
    FlextInfraUtilitiesProjectDiscoveryShapeMixin,
)
from flext_infra._utilities.git_scope import FlextInfraUtilitiesGitScope
from flext_infra._utilities.pyproject import FlextInfraUtilitiesPyproject

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import t


class FlextInfraUtilitiesProjectDiscoveryCandidatesMixin(
    FlextInfraUtilitiesProjectDiscoveryShapeMixin
):
    """Private candidate enumeration for workspace project discovery."""

    @classmethod
    def discover_external_workspace_roots(
        cls, workspace_root: Path, *, scan_dirs: frozenset[str] | None = None
    ) -> t.SequenceOf[Path]:
        """Return explicitly configured workspace roots outside ``workspace_root``.

        Selection is bounded by the ``members`` paths or globs declared in the
        root's ``[tool.flext.workspace]`` or ``[tool.uv.workspace]`` table.
        Unrelated siblings are never probed. A configured but inaccessible
        member fails loud with its path.
        """
        resolved_workspace_root = workspace_root.resolve()
        effective_scan_dirs = scan_dirs or frozenset()
        configured_members = FlextInfraUtilitiesPyproject.workspace_member_names(
            workspace_root
        )
        configured_member_set = frozenset(configured_members)
        candidates: set[Path] = set()
        for member in configured_members:
            try:
                matched = (
                    tuple(resolved_workspace_root.glob(member))
                    if any(marker in member for marker in ("*", "?", "["))
                    else (resolved_workspace_root / member,)
                )
            except OSError as exc:
                msg = f"declared workspace member pattern is not accessible: {member}"
                raise OSError(msg) from exc
            candidates.update(matched)
        roots: list[Path] = []
        seen: set[Path] = set()
        for candidate in sorted(candidates, key=lambda item: item.as_posix()):
            try:
                resolved_candidate = candidate.resolve()
            except OSError as exc:
                msg = (
                    "declared external workspace member path cannot be resolved: "
                    f"{candidate}"
                )
                raise PermissionError(msg) from exc
            if resolved_candidate.is_relative_to(resolved_workspace_root):
                continue
            try:
                is_directory = resolved_candidate.is_dir()
            except OSError as exc:
                msg = (
                    "declared external workspace member is not accessible: "
                    f"{resolved_candidate}"
                )
                raise PermissionError(msg) from exc
            if not is_directory:
                msg = (
                    "declared external workspace member is not a directory: "
                    f"{resolved_candidate}"
                )
                raise NotADirectoryError(msg)
            pyproject = resolved_candidate / c.Infra.PYPROJECT_FILENAME
            try:
                has_pyproject = pyproject.is_file()
            except OSError as exc:
                msg = (
                    "declared external workspace member is not accessible: "
                    f"{resolved_candidate}"
                )
                raise PermissionError(msg) from exc
            if not has_pyproject:
                msg = (
                    "declared external workspace member has no pyproject.toml: "
                    f"{resolved_candidate}"
                )
                raise FileNotFoundError(msg)
            if resolved_candidate in seen:
                continue
            metadata_result = u.read_project_metadata(resolved_candidate)
            if metadata_result.failure:
                msg = (
                    "declared external workspace member metadata is invalid: "
                    f"{resolved_candidate}: {metadata_result.error}"
                )
                raise ValueError(msg)
            if not cls._looks_like_project(
                resolved_candidate,
                effective_scan_dirs=effective_scan_dirs,
                configured_member_set=configured_member_set,
            ):
                continue
            roots.append(resolved_candidate)
            seen.add(resolved_candidate)
        return tuple(roots)

    @classmethod
    def discover_project_candidates(
        cls,
        workspace_root: Path,
        *,
        scan_dirs: frozenset[str] | None = None,
        include_attached: bool = False,
    ) -> t.SequenceOf[Path]:
        """Return all canonical project candidates before consumer-specific filtering.

        Selection contract: declared workspace members isolate discovery to the
        configured set (git-tracked in live repositories); without a member
        declaration, discovery scans top-level directories structurally so
        standalone checkouts and untracked projects are still found.
        """
        roots: t.MutableSequenceOf[Path] = []
        effective_scan_dirs = scan_dirs or frozenset()
        configured_members = FlextInfraUtilitiesPyproject.workspace_member_names(
            workspace_root
        )
        configured_member_set = frozenset(configured_members)
        resolved_workspace_root = workspace_root.resolve()
        configured_entries: set[Path] = set()
        for member in configured_members:
            matched_entries = (
                tuple(resolved_workspace_root.glob(member))
                if any(marker in member for marker in ("*", "?", "["))
                else (resolved_workspace_root / member,)
            )
            configured_entries.update(
                entry.resolve()
                for entry in matched_entries
                if entry.is_dir()
                and entry.resolve().is_relative_to(resolved_workspace_root)
            )
        attached_child_dirs = (
            cls._attached_top_level_dir_names(resolved_workspace_root)
            if include_attached
            else frozenset()
        )
        external_workspace_roots = (
            cls.discover_external_workspace_roots(
                resolved_workspace_root, scan_dirs=scan_dirs
            )
            if include_attached
            else ()
        )

        if cls._looks_like_project(
            resolved_workspace_root,
            effective_scan_dirs=effective_scan_dirs,
            configured_member_set=configured_member_set,
        ) and FlextInfraUtilitiesGitScope.project_descriptor_is_tracked(
            resolved_workspace_root, resolved_workspace_root
        ):
            roots.append(resolved_workspace_root)
        if configured_members:
            candidate_entries: t.SequenceOf[Path] = sorted(
                {
                    *configured_entries,
                    *(
                        resolved_workspace_root / dir_name
                        for dir_name in attached_child_dirs
                    ),
                },
                key=lambda item: item.as_posix(),
            )
            roots.extend([
                entry.resolve()
                for entry in candidate_entries
                if entry.is_dir()
                and not entry.name.startswith(".")
                and (
                    entry.name in attached_child_dirs
                    or FlextInfraUtilitiesGitScope.project_descriptor_is_tracked(
                        resolved_workspace_root, entry.resolve()
                    )
                )
                and cls._looks_like_project(
                    entry.resolve(),
                    effective_scan_dirs=effective_scan_dirs,
                    configured_member_set=configured_member_set,
                )
            ])
        else:
            structural_entries: t.SequenceOf[Path] = sorted(
                {
                    *workspace_root.iterdir(),
                    *(
                        resolved_workspace_root / dir_name
                        for dir_name in attached_child_dirs
                    ),
                },
                key=lambda item: item.as_posix(),
            )
            roots.extend([
                entry.resolve()
                for entry in structural_entries
                if entry.is_dir()
                and not entry.name.startswith(".")
                and cls._looks_like_project(
                    entry.resolve(),
                    effective_scan_dirs=effective_scan_dirs,
                    configured_member_set=configured_member_set,
                )
            ])
        roots.extend(external_workspace_roots)
        if not roots and (resolved_workspace_root / c.Infra.DEFAULT_SRC_DIR).is_dir():
            return [resolved_workspace_root]
        return roots


__all__: list[str] = ["FlextInfraUtilitiesProjectDiscoveryCandidatesMixin"]
