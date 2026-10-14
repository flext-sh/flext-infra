"""Public conformance preserves workspace and standalone dependency locks.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import infra
from flext_infra.codegen import FlextInfraCodegenConform
from flext_infra.workspace import (
    FlextInfraWorkspaceLockCompleteness,
)
from tests import c, t, tm, u

pytestmark = pytest.mark.slow


class TestsFlextInfraWorkspaceMemberLockOwnership:
    """Generation neither resolves existing locks nor creates missing locks."""

    @staticmethod
    def _repository(tmp_path: Path, *, attached: bool) -> t.Pair[Path, Path]:
        """Create an actual governed Git checkout in the requested topology.

        Returns:
            The workspace root.

        """
        root = u.Tests.WorktreeFixture.governed_workspace(tmp_path, "workspace")
        u.Tests.WorktreeFixture.initialize_governed_project(
            root / cls.MEMBER,
            cls.MEMBER,
            beads=u.Tests.BeadsIdentity(
                workspace="fixture-workspace",
                database="fixture_workspace",
                issue_prefix="fixture-workspace",
            ),
        )
        u.Tests.checkout_integration(root / cls.MEMBER)
        u.Tests.WorktreeFixture.write_gitmodules(root, (cls.MEMBER,))
        head = u.Tests.git_capture(root / cls.MEMBER, "rev-parse", c.Infra.GIT_HEAD)
        u.Tests.git_run(
            root,
            "update-index",
            "--add",
            "--cacheinfo",
            f"160000,{head.strip()},{cls.MEMBER}",
        )
        if uv_workspace:
            pyproject = root / c.PYPROJECT_FILENAME
            pyproject.write_text(
                pyproject.read_text(encoding="utf-8")
                + f'\n[tool.uv.workspace]\nmembers = ["{cls.MEMBER}"]\n',
                encoding="utf-8",
            )
        u.Tests.commit_git_changes(root, "declare members")
        return root

    def test_standalone_member_owns_its_lock(self, tmp_path: Path) -> None:
        """Without an enclosing uv workspace the member resolves alone."""
        member = self._workspace(tmp_path, uv_workspace=False) / self.MEMBER

        tm.that(tm.ok(FlextInfraCodegenConform.require_own_lock(member)), eq=member)

    @pytest.mark.parametrize("uv_workspace", [False, True])
    def test_verification_uses_native_lock_owner(
        self,
        tmp_path: Path,
        uv_workspace: bool,
    ) -> None:
        """Git attachment alone never elects the containing runtime's lock."""
        root = self._workspace(tmp_path, uv_workspace=uv_workspace)
        member = root / self.MEMBER
        owner = root if uv_workspace else member
        lock = owner / c.Infra.UV_LOCK_FILENAME
        lock.write_text("package = []", encoding="utf-8")

        tm.fail(FlextInfraWorkspaceLockCompleteness.validate(member), has=str(lock))
        tm.that(lock.read_text(encoding="utf-8"), eq="package = []")
        other = (member if uv_workspace else root) / c.Infra.UV_LOCK_FILENAME
        tm.that(other.exists(), eq=False)

    def test_attached_member_settle_stops_before_any_lock(
        self,
        tmp_path: Path,
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
        tm.that(bool(generated.written_files), eq=True)
        tm.that(tuple(path.read_bytes() for path in paths), eq=before)

    @pytest.mark.parametrize("attached", [False, True])
    def test_conform_does_not_create_missing_uv_lock(
        self,
        tmp_path: Path,
        attached: bool,
    ) -> None:
        """Projection generation succeeds without becoming a dependency resolver."""
        root, project = self._repository(tmp_path, attached=attached)
        locks = tuple(
            dict.fromkeys(
                checkout / c.Infra.UV_LOCK_FILENAME for checkout in (root, project)
            ),
        )
        tm.that(any(path.exists() for path in locks), eq=False)
        tm.ok(
            infra.codegen_conform(
                u.Tests.conform_request(
                    project,
                    mode=c.Infra.CodegenConformMode.APPLY,
                    scope=c.Infra.CodegenConformScope.SELF,
                ),
            ),
        )
        tm.that(any(path.exists() for path in locks), eq=False)
