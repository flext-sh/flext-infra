"""Real cold-workspace upgrades materialize gitlinks before Python resolution.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_core import r
from tests import c, m, t, tm, u

pytestmark = [pytest.mark.slow, pytest.mark.remote]


class TestsFlextInfraCodegenUpgWorkspace:
    """Upgrade a real workspace with an indexed, uninitialized member."""

    @staticmethod
    def _declared_member_checkout(
        root: Path,
        tmp_path: Path,
    ) -> tuple[str, Path, m.Infra.RepositoryRef]:
        """Attach a governed origin member and capture its indexed gitlink.

        Args:
            root: Workspace root receiving the submodule.
            tmp_path: Test-scoped scratch root hosting the member origin.

        Returns:
            The recorded gitlink of the member, its checkout path, and the
            member repository reference.

        """
        member = u.Tests.repository_ref("fixture-member", path=Path("fixture-member"))
        source = tmp_path / "member-origin"
        beads = u.Tests.beads_project(member.name)
        u.Tests.WorktreeFixture.initialize_governed_project(
            source,
            member.distribution,
            beads=u.Tests.BeadsIdentity(
                workspace=beads.workspace,
                database=beads.database,
                issue_prefix=beads.issue_prefix,
            ),
        )
        branch = u.Tests.checkout_integration(source)
        u.Tests.git_bootstrap(
            root,
            (
                "-c",
                "protocol.file.allow=always",
                "submodule",
                "add",
                "-b",
                branch,
                str(source),
                member.path.as_posix(),
            ),
        )
        u.Tests.git_bootstrap(
            root,
            (
                "config",
                "-f",
                c.Infra.GITMODULES,
                f"submodule.{member.path.as_posix()}.flext-managed",
                "true",
            ),
        )
        u.Tests.git_bootstrap(root, ("add", c.Infra.GITMODULES, member.path.as_posix()))
        u.Tests.git_bootstrap(root, ("commit", "-m", "Declare real workspace member"))
        gitlink = tm.ok(
            u.Cli.capture(
                [c.Infra.GIT, "rev-parse", f"HEAD:{member.path.as_posix()}"],
                cwd=root,
            ),
        ).strip()
        return gitlink, root / member.path, member

    @staticmethod
    def _added_member_checkout(root: Path, tmp_path: Path) -> Path:
        """Attach an additional governed member the Makefile does not declare.

        Args:
            root: Workspace root receiving the submodule.
            tmp_path: Test-scoped scratch root hosting the member origin.

        Returns:
            The checkout path of the additionally attached member.

        """
        added = u.Tests.repository_ref("added-member", path=Path("added-member"))
        added_source = tmp_path / "added-origin"
        added_beads = u.Tests.beads_project(added.name)
        u.Tests.WorktreeFixture.initialize_governed_project(
            added_source,
            added.distribution,
            beads=u.Tests.BeadsIdentity(
                workspace=added_beads.workspace,
                database=added_beads.database,
                issue_prefix=added_beads.issue_prefix,
            ),
        )
        added_branch = u.Tests.checkout_integration(added_source)
        u.Tests.git_bootstrap(
            root,
            (
                "-c",
                "protocol.file.allow=always",
                "submodule",
                "add",
                "-b",
                added_branch,
                str(added_source),
                added.path.as_posix(),
            ),
        )
        u.Tests.git_bootstrap(
            root,
            (
                "config",
                "-f",
                c.Infra.GITMODULES,
                f"submodule.{added.path.as_posix()}.flext-managed",
                "true",
            ),
        )
        u.Tests.commit_git_changes(root, "Declare additional governed member")
        return root / added.path

    def test_upg_materializes_member_before_resolving_workspace_lock(
        self,
        tmp_path: Path,
    ) -> None:
        """Test upg materializes member before resolving workspace lock."""
        root, _ = u.Tests.render_make_environment(
            tmp_path,
            c.Infra.MakeProfile.WORKSPACE,
            bootstrap=True,
        )
        gitlink, checkout, member = self._declared_member_checkout(root, tmp_path)
        repository = u.Tests.repository_ref(
            root.name,
            role=c.Infra.MakeProfile.WORKSPACE,
        )
        workspace = u.Tests.workspace_spec(
            repository,
            project=u.Tests.project_spec(repository.name),
            subprojects=(member,),
        )
        plan = u.Tests.conform_plan(root, workspace)
        artifacts = tuple(
            artifact
            for artifact in plan.files
            if artifact.path
            in {root / c.Infra.MAKEFILE_FILENAME, root / c.PYPROJECT_FILENAME}
        )
        tm.that(len(artifacts), eq=2)
        tm.ok(
            u.Tests.materialize_codegen_plans(
                r[tuple[m.Infra.CodegenFilePlan, ...]].ok(artifacts),
            ),
        )
        u.Tests.git_bootstrap(root, ("submodule", "deinit", "--force", "--all"))
        checkout = root / member.path
        tm.that((checkout / c.PYPROJECT_FILENAME).exists(), eq=False)
        tm.that((root / c.Infra.UV_LOCK_FILENAME).exists(), eq=False)
        custom = root / c.Infra.MAKEFILE_CUSTOM_INCLUDE
        custom.write_text(
            custom.read_text(encoding="utf-8") + "post-upg:\n"
            '\t@$(UV) lock --check --project "$(RUNTIME_ROOT)"\n'
            '\t@printf "hook-native-lock-satisfied %s\\n" "$(RUNTIME_ROOT)"\n',
            encoding="utf-8",
        )

        process = tm.ok(
            u.Tests.run_isolated_make(
                ["--no-print-directory", "upg"],
                cwd=root,
                env={"GIT_ALLOW_PROTOCOL": "file:https:ssh"},
            ),
        )

        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=True,
            msg=process.stdout + process.stderr,
        )
        tm.that((checkout / c.PYPROJECT_FILENAME).is_file(), eq=True)
        tm.that(
            tm.ok(
                u.Cli.capture([c.Infra.GIT, "rev-parse", "HEAD"], cwd=checkout),
            ).strip(),
            eq=gitlink,
        )
        locked = u.Tests.toml_payload((root / c.Infra.UV_LOCK_FILENAME).read_text())
        packages = t.Cli.JSON_LIST_ADAPTER.validate_python(locked["package"])
        tm.that(
            tuple(
                t.Cli.JSON_MAPPING_ADAPTER.validate_python(item)["name"]
                for item in packages
            ),
            has=member.distribution,
        )
        tm.that(
            (u.Infra.runtime_environment_dir(root) / "pyvenv.cfg").is_file(),
            eq=True,
        )
        tm.that((checkout / ".venv").exists(), eq=False)
        tm.that((checkout / c.Infra.UV_LOCK_FILENAME).exists(), eq=False)
        tm.that(process.stdout, has=f"hook-native-lock-satisfied {root}")

        # The running Makefile does not yet declare this new Git member. Its
        # generated successor must include it in the containing root's lock.
        added_checkout = self._added_member_checkout(root, tmp_path)
        tm.that((added_checkout / c.Infra.UV_LOCK_FILENAME).exists(), eq=False)
        expanded = tm.ok(
            u.Tests.run_isolated_make(
                ["--no-print-directory", "upg"],
                cwd=root,
                env={"GIT_ALLOW_PROTOCOL": "file:https:ssh"},
            ),
        )
        tm.that(
            u.Cli.process_succeeded(expanded.outcome),
            eq=True,
            msg=expanded.stdout + expanded.stderr,
        )
        tm.that((root / c.Infra.UV_LOCK_FILENAME).is_file(), eq=True)
        tm.that(expanded.stdout, has=f"hook-native-lock-satisfied {root}")
        for project in (checkout, added_checkout):
            tm.that((project / c.Infra.UV_LOCK_FILENAME).exists(), eq=False)
        tm.that((added_checkout / ".venv").exists(), eq=False)
