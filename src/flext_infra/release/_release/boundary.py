"""Release boundary: what may ship, how internal pins read, where receipts live.

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

from collections.abc import Sequence
from pathlib import Path, PurePosixPath

from flext_infra import FlextInfraProjectSelectionServiceBase, c, config, m, p, r, u


class FlextInfraReleaseReleaseBoundary(FlextInfraProjectSelectionServiceBase[bool]):
    """Shared release policy every phase applies to one repository."""

    @staticmethod
    def _release_dir(root: Path, tag: str = "") -> Path:
        """Return the release report directory, or one version's receipt directory.

        Returns:
            The release report directory, or one version's receipt directory.

        """
        return u.Cli.resolve_report_dir(root, c.Infra.PROJECT, c.Infra.RK_RELEASE) / tag

    @staticmethod
    def _write_release_text(path: Path, content: str) -> p.Result[bool]:
        """Write release text, creating its directory.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return r[bool].fail_op(
                f"create release output directory {path.parent}",
                exc,
            )
        return u.Cli.files_write_text(path, content)

    @staticmethod
    def _path_error(name: str, kind: str, *, root_index: int | None = None) -> str:
        """Return why ``name`` may not ship, or an empty string.

        Repository-operational trees are rejected only at an archive's content
        root (``root_index``): a package may ship a ``.github`` tree as data.
        A file codegen renders or manages is a projection, never a secret,
        whatever its name; other sensitive material is rejected at every depth.

        Returns:
            Why ``name`` may not ship, or an empty string.

        """
        path = PurePosixPath(name)
        if not name or "\\" in name or path.is_absolute() or ".." in path.parts:
            return f"unsafe {kind} path: {name}"
        if (
            root_index is not None
            and len(path.parts) > root_index
            and path.parts[root_index].casefold() in c.Infra.RELEASE_OPERATIONAL_ROOTS
        ):
            return f"operational {kind} path: {name}"
        codegen = config.Infra.codegen
        if name in {entry.destination for entry in codegen.templates.entries} or any(
            name == item.path.as_posix() for item in codegen.managed_file_specs
        ):
            return ""
        for part in (part.casefold() for part in path.parts):
            if (
                part in c.Infra.RELEASE_SENSITIVE_PARTS
                or part.startswith(c.Infra.RELEASE_SENSITIVE_PREFIXES)
                or part.endswith(c.Infra.RELEASE_SENSITIVE_SUFFIXES)
            ):
                return f"sensitive {kind} path: {name}"
        return ""

    @staticmethod
    def _sdist_member_allowed(
        parts: Sequence[str],
        allowed_roots: Sequence[str],
    ) -> bool:
        """Return whether one regular sdist member is inside the public boundary.

        Returns:
            Whether one regular sdist member is inside the public boundary.

        """
        relative = tuple(part.casefold() for part in parts[1:])
        permitted_roots = c.Infra.RELEASE_SDIST_ROOT_DIRS.union(
            root.casefold() for root in allowed_roots
        )
        if relative and relative[0] in permitted_roots:
            return True
        return len(relative) == 1 and (
            relative[0] in c.Infra.RELEASE_LICENSE_NAMES
            or relative[0] in c.Infra.RELEASE_SDIST_ROOT_FILES
            or relative[0].startswith("readme")
        )

    @staticmethod
    def _record(
        target: tuple[str, Path],
        log: Path,
        *,
        exit_code: int,
        artifacts: Sequence[m.Infra.BuildArtifact] = (),
        source: tuple[m.Infra.SourceSnapshot, str] | None = None,
    ) -> m.Infra.BuildRecord:
        """Model one strict build record with absolute paths.

        ``target`` is the release target (project name, project path);
        ``source`` is the staged source provenance -- its committed snapshot
        and LICENSE digest -- which a record carries completely or not at all.

        Returns:
            The resulting ``m.Infra.BuildRecord``.

        """
        name, path = target
        return m.Infra.BuildRecord(
            project=name,
            path=str(path.resolve()),
            exit_code=exit_code,
            log=str(log.resolve()),
            artifacts=tuple(artifacts),
            commit_oid=source[0].commit_oid if source is not None else None,
            source_date_epoch=source[0].source_date_epoch
            if source is not None
            else None,
            source_license_sha256=source[1] if source is not None else None,
        )


__all__: list[str] = ["FlextInfraReleaseReleaseBoundary"]
