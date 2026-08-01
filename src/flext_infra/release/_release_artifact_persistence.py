"""Atomic persistence for complete validated release artifact sets."""

from __future__ import annotations

import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import t, u
from flext_infra.release._release_artifact_source import (
    FlextInfraReleaseArtifactSourceMixin,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraReleaseArtifactPersistenceMixin(FlextInfraReleaseArtifactSourceMixin):
    """Validate and atomically persist complete project artifact sets."""

    @staticmethod
    def _build_artifact_paths(output_dir: Path) -> p.Result[t.SequenceOf[Path]]:
        """Resolve exactly one wheel and one sdist from uv build output."""
        try:
            entries = tuple(sorted(output_dir.iterdir()))
        except OSError as exc:
            return r[t.SequenceOf[Path]].fail_op(
                f"list uv build output {output_dir}", exc
            )
        wheels = tuple(path for path in entries if path.suffix == ".whl")
        sdists = tuple(path for path in entries if path.name.endswith(".tar.gz"))
        artifacts = (*wheels, *sdists)
        unexpected = tuple(path for path in entries if path not in artifacts)
        if unexpected:
            names = ", ".join(path.name for path in unexpected)
            return r[t.SequenceOf[Path]].fail(
                f"uv build emitted unexpected output: {names}"
            )
        if len(wheels) != 1 or len(sdists) != 1:
            return r[t.SequenceOf[Path]].fail(
                f"expected one wheel and one sdist, found "
                f"{len(wheels)} wheel(s) and {len(sdists)} sdist(s)"
            )
        return r[t.SequenceOf[Path]].ok(artifacts)

    @staticmethod
    def _validate_existing_file_set(
        files: t.SequenceOf[t.Pair[Path, t.Infra.ReleaseArtifactSha256]],
        destinations: t.SequenceOf[Path],
        destination_dir: Path,
    ) -> p.Result[t.SequenceOf[Path]]:
        """Validate an already persisted immutable file set."""
        try:
            existing = tuple(sorted(destination_dir.iterdir()))
        except OSError as exc:
            return r[t.SequenceOf[Path]].fail_op("list persisted artifact set", exc)
        if existing != tuple(sorted(destinations)):
            return r[t.SequenceOf[Path]].fail(
                f"immutable artifact set collision at {destination_dir}"
            )
        for (source, digest), destination in zip(files, destinations, strict=True):
            if u.Cli.sha256_file(source) != digest:
                return r[t.SequenceOf[Path]].fail(
                    f"source file digest changed before persistence: {source}"
                )
            if u.Cli.sha256_file(destination) != digest:
                return r[t.SequenceOf[Path]].fail(
                    f"immutable artifact collision at {destination}"
                )
        return r[t.SequenceOf[Path]].ok(destinations)

    @staticmethod
    def _stage_file_set(
        files: t.SequenceOf[t.Pair[Path, t.Infra.ReleaseArtifactSha256]],
        staging_dir: Path,
    ) -> p.Result[bool]:
        """Copy one file set into staging and verify every digest."""
        for source, digest in files:
            staged = staging_dir / source.name
            shutil.copy2(source, staged)
            if u.Cli.sha256_file(staged) != digest:
                return r[bool].fail(f"staged artifact digest mismatch: {source}")
        return r[bool].ok(True)

    @classmethod
    def _commit_file_set(
        cls,
        files: t.SequenceOf[t.Pair[Path, t.Infra.ReleaseArtifactSha256]],
        destinations: t.SequenceOf[Path],
        destination_dir: Path,
    ) -> p.Result[t.SequenceOf[Path]]:
        """Copy and atomically rename one complete validated file set."""
        try:
            with TemporaryDirectory(
                prefix=f".{destination_dir.name}-", dir=destination_dir.parent
            ) as temporary:
                staging_dir = Path(temporary)
                staged = cls._stage_file_set(files, staging_dir)
                if staged.failure:
                    return r[t.SequenceOf[Path]].fail(
                        staged.error or "artifact staging validation failed"
                    )
                staging_dir.replace(destination_dir)
        except OSError as exc:
            return r[t.SequenceOf[Path]].fail_op("persist release artifact set", exc)
        return r[t.SequenceOf[Path]].ok(destinations)

    @classmethod
    def _persist_file_set(
        cls,
        files: t.SequenceOf[t.Pair[Path, t.Infra.ReleaseArtifactSha256]],
        destination_dir: Path,
    ) -> p.Result[t.SequenceOf[Path]]:
        """Persist a complete validated file set atomically."""
        if not files:
            return r[t.SequenceOf[Path]].fail("immutable file set is empty")
        names = tuple(source.name for source, _ in files)
        if len(names) != len(set(names)):
            return r[t.SequenceOf[Path]].fail("immutable file set has duplicate names")
        for source, digest in files:
            if not source.is_file() or source.is_symlink():
                return r[t.SequenceOf[Path]].fail(
                    f"immutable file source is not a regular file: {source}"
                )
            if u.Cli.sha256_file(source) != digest:
                return r[t.SequenceOf[Path]].fail(
                    f"immutable file source digest mismatch: {source}"
                )
        destinations = tuple(destination_dir / name for name in names)
        try:
            destination_dir.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return r[t.SequenceOf[Path]].fail_op("create artifact output parent", exc)
        if destination_dir.exists():
            return cls._validate_existing_file_set(files, destinations, destination_dir)
        return cls._commit_file_set(files, destinations, destination_dir)

    @classmethod
    def _persist_artifact_set(
        cls,
        artifacts: t.SequenceOf[
            t.Triple[Path, t.Infra.ReleaseArtifactKind, t.Infra.ReleaseArtifactSha256]
        ],
        destination_dir: Path,
    ) -> p.Result[t.SequenceOf[Path]]:
        """Persist one validated Python release artifact set atomically."""
        files = tuple((source, digest) for source, _, digest in artifacts)
        return cls._persist_file_set(files, destination_dir)


__all__: list[str] = ["FlextInfraReleaseArtifactPersistenceMixin"]
