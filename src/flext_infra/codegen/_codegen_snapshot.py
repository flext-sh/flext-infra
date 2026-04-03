from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from flext_infra import (
    c,
    t,
    u,
)


class FlextInfraCodegenSnapshot:
    """Snapshot and change detection for code generation operations."""

    @staticmethod
    def find_package_dir(project_root: Path) -> Path | None:
        src_dir = project_root / c.Infra.Paths.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return None
        for child in sorted(src_dir.iterdir()):
            if child.is_dir() and (child / c.Infra.Files.INIT_PY).exists():
                return child
        return None

    @staticmethod
    def snapshot_init_files(*, project_path: Path) -> t.StrMapping:
        snapshot: t.MutableStrMapping = {}
        for root_name in c.Infra.MRO_SCAN_DIRECTORIES:
            root = project_path / root_name
            if not root.is_dir():
                continue
            for init_file in u.iter_directory_python_files(
                root,
                pattern=c.Infra.Files.INIT_PY,
            ):
                try:
                    snapshot[str(init_file)] = init_file.read_text(
                        encoding=c.Infra.Encoding.DEFAULT,
                    )
                except OSError:
                    continue
        return snapshot

    @staticmethod
    def snapshot_files(*, file_paths: Sequence[Path]) -> t.StrMapping:
        snapshot: t.MutableStrMapping = {}
        for file_path in file_paths:
            try:
                snapshot[str(file_path)] = file_path.read_text(
                    encoding=c.Infra.Encoding.DEFAULT,
                )
            except OSError:
                continue
        return snapshot

    @staticmethod
    def detect_changed_files(
        *,
        before_snapshot: t.StrMapping,
        file_paths: Sequence[Path],
    ) -> t.Infra.StrSet:
        changed: t.Infra.StrSet = set()
        for file_path in file_paths:
            path_key = str(file_path)
            previous = before_snapshot.get(path_key)
            try:
                current = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
            except OSError:
                continue
            if previous != current:
                changed.add(path_key)
        return changed


__all__ = ["FlextInfraCodegenSnapshot"]
