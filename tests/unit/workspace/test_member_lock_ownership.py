"""Public conformance preserves workspace and standalone dependency locks.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import infra
from flext_infra.workspace import (
    FlextInfraWorkspaceDetector,
    FlextInfraWorkspaceLockCompleteness,
)
from tests import c, tm, u

pytestmark = pytest.mark.slow


class TestsFlextInfraWorkspaceMemberLockOwnership:
    """Generation neither resolves existing locks nor creates missing locks."""

    @staticmethod
    def _repository(tmp_path: Path, *, attached: bool) -> tuple[Path, Path]:
        """Create an actual governed Git checkout in the requested topology.

        Returns:
            The containing root and the project selected for conformance.

        """
        root = tmp_path / "workspace"
        if attached:
            member = u.Tests.WorktreeFixture.governed_workspace_with_member(root)
            return root, member
        project = u.Tests.WorktreeFixture.governed_workspace(tmp_path, "standalone")
        return project, project

    @pytest.mark.parametrize("attached", [False, True])
    def test_verification_uses_selected_owner_without_repair(
        self,
        tmp_path: Path,
        *,
        attached: bool,
    ) -> None:
        """Attached and standalone validation name their own selected missing lock."""
        root, project = self._repository(tmp_path, attached=attached)
        context = tm.ok(FlextInfraWorkspaceDetector.resolution_context(project))
        tm.that(context.runtime_root, eq=root)
        legacy = project / c.Infra.UV_LOCK_FILENAME
        legacy.write_text("package = []\n", encoding="utf-8")

        tm.fail(
            FlextInfraWorkspaceLockCompleteness.verify_lock(project),
            has=str(context.lock_path),
        )

        tm.fail(context.lock_path.exists())
        tm.that(legacy.read_text(encoding="utf-8"), eq="package = []\n")

    @pytest.mark.parametrize("attached", [False, True])
    def test_conform_preserves_existing_locks(
        self,
        tmp_path: Path,
        *,
        attached: bool,
    ) -> None:
        """Conform a real project while retaining each owner's exact lock bytes."""
        root, project = self._repository(tmp_path, attached=attached)
        paths = tuple(
            dict.fromkeys(
                checkout / filename
                for checkout in (root, project)
                for filename in (c.Infra.UV_LOCK_FILENAME, c.Infra.MISE_LOCK_FILENAME)
            ),
        )
        for path in paths:
            if not path.exists():
                path.write_text("version = 1\n", encoding="utf-8")
        before = tuple(path.read_bytes() for path in paths)
        generated = tm.ok(
            infra.codegen_conform(
                u.Tests.conform_request(
                    project,
                    mode=c.Infra.CodegenConformMode.APPLY,
                    scope=c.Infra.CodegenConformScope.SELF,
                ),
            ),
        )
        tm.ok(bool(generated.written_files))
        tm.that(tuple(path.read_bytes() for path in paths), eq=before)

    @pytest.mark.parametrize("attached", [False, True])
    def test_conform_does_not_create_missing_uv_lock(
        self,
        tmp_path: Path,
        *,
        attached: bool,
    ) -> None:
        """Projection generation succeeds without becoming a dependency resolver."""
        root, project = self._repository(tmp_path, attached=attached)
        locks = tuple(
            dict.fromkeys(
                checkout / c.Infra.UV_LOCK_FILENAME for checkout in (root, project)
            ),
        )
        tm.fail(any(path.exists() for path in locks))
        tm.ok(
            infra.codegen_conform(
                u.Tests.conform_request(
                    project,
                    mode=c.Infra.CodegenConformMode.APPLY,
                    scope=c.Infra.CodegenConformScope.SELF,
                ),
            ),
        )
        tm.fail(any(path.exists() for path in locks))
