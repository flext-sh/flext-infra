"""Git HEAD-anchor lease validation contracts for complete generation."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from flext_infra import u
from flext_infra.codegen.mise_artifacts_lock import FlextInfraMiseLock
from flext_tests import tm
from tests.unit.codegen.mise_generation_lock_fixture import (
    lock_identity,
    lock_repository,
)


class TestsMiseGenerationLockAnchor:
    """Reject every Git HEAD shape that cannot anchor a unique lease."""

    @staticmethod
    def _replace_head(head: Path, replacement: Path) -> None:
        replacement.write_bytes(head.read_bytes())
        replacement.replace(head)

    def test_second_process_contends_on_same_scope_head(self, tmp_path: Path) -> None:
        """Make a distinct process lose one nonblocking attempt on the same inode."""
        root = lock_repository(tmp_path / "contended")
        identity = lock_identity(root)
        child = """
from pathlib import Path
import sys
from flext_infra import m, u
from flext_infra.codegen.mise_artifacts_lock import FlextInfraMiseLock

identity = u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=Path(sys.argv[1])))
if identity.failure:
    raise SystemExit(3)
try:
    with FlextInfraMiseLock.lease(identity.value):
        raise SystemExit(4)
except BlockingIOError:
    raise SystemExit(0)
"""

        with FlextInfraMiseLock.lease(identity):
            contended = u.Cli.run_raw(
                (sys.executable, "-c", child, str(root)), timeout=30
            )

        tm.ok(contended)
        tm.that(
            u.Cli.process_succeeded(contended.value.outcome),
            eq=True,
            msg=contended.value.stderr,
        )

    def test_head_replacement_is_rejected_while_lease_is_held(
        self, tmp_path: Path
    ) -> None:
        """Reject a Git operation that atomically replaces the locked HEAD inode."""
        root = lock_repository(tmp_path / "swapped")
        identity = lock_identity(root)
        head = identity.git_dir / "HEAD"
        replacement = identity.git_dir / "replacement-head"

        with (
            pytest.raises(OSError, match="changed while held"),
            FlextInfraMiseLock.lease(identity),
        ):
            self._replace_head(head, replacement)

    def test_head_hardlink_is_rejected(self, tmp_path: Path) -> None:
        """Reject an anchor inode that is no longer uniquely named."""
        root = lock_repository(tmp_path / "hardlinked")
        identity = lock_identity(root)
        (identity.git_dir / "HEAD-alias").hardlink_to(identity.git_dir / "HEAD")

        with (
            pytest.raises(OSError, match="hard links"),
            FlextInfraMiseLock.lease(identity),
        ):
            pass

    @pytest.mark.skipif(
        os.name == "nt", reason="fixture symlinks need Windows privilege"
    )
    def test_head_symlink_is_rejected(self, tmp_path: Path) -> None:
        """Reject legacy Git HEAD symlinks as reparse/alias lock anchors."""
        root = lock_repository(tmp_path / "symlinked")
        identity = lock_identity(root)
        head = identity.git_dir / "HEAD"
        backup = identity.git_dir / "HEAD-backup"
        head.replace(backup)
        head.symlink_to(backup.name)

        with (
            pytest.raises(OSError, match="regular file"),
            FlextInfraMiseLock.lease(identity),
        ):
            pass


__all__: tuple[str, ...] = ()
