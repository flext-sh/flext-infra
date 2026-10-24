"""Behavior tests for the repository .gitmodules contract.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra.workspace import FlextInfraWorkspaceDetector
from tests import c, tm, u


class TestsFlextInfraRepositoryGitmodulesContract:
    """Prove the declared .gitmodules contract and its provider identity."""

    @staticmethod
    def test_invalid_repository_path_fails_closed(tmp_path: Path) -> None:
        """Return a typed failure for a path that is not a repository directory."""
        result = FlextInfraWorkspaceDetector().detect(tmp_path / "absent")

        tm.fail(result, has="not a directory")

    @staticmethod
    def test_repository_without_origin_fails_closed(tmp_path: Path) -> None:
        """Require an explicit origin before classifying provider ownership."""
        root = tmp_path / "without-origin"
        u.Tests.WorktreeFixture.initialize_governed_project(
            root,
            "without-origin",
            beads=u.Tests.BeadsIdentity(
                workspace="without-origin",
                database="without_origin",
                issue_prefix="without-origin",
            ),
        )
        tm.ok(u.Cli.run_checked(["git", "remote", "remove", "origin"], cwd=root))

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has="No item found with id origin")

    @staticmethod
    @pytest.mark.parametrize(
        ("missing_key", "expected_error"),
        [
            ("url", "Git submodule URL is missing"),
            ("branch", "Git submodule branch is missing"),
        ],
    )
    def test_gitmodule_requires_complete_contract(
        tmp_path: Path,
        missing_key: str,
        expected_error: str,
    ) -> None:
        """Reject a declared_repository entry without its exact URL or branch."""
        root = tmp_path / missing_key
        u.Tests.WorktreeFixture.initialize_governed_project(
            root,
            "fixture-workspace",
            beads=u.Tests.BeadsIdentity(
                workspace="fixture-workspace",
                database="fixture_workspace",
                issue_prefix="fixture-workspace",
            ),
        )
        provider = u.Tests.provider()
        fields = {
            "url": f"\turl = {provider.base_url}/fixture-child.git\n",
            "branch": f"\tbranch = {u.Tests.provider_branch()}\n",
        }
        fields.pop(missing_key)
        (root / c.Infra.GITMODULES).write_text(
            '[submodule "fixture-child"]\n'
            "\tpath = fixture-child\n"
            f"{''.join(fields.values())}",
            encoding="utf-8",
        )

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has=expected_error)

    @staticmethod
    def test_gitmodule_rejects_duplicate_paths(tmp_path: Path) -> None:
        """Reject two declarations that claim the same checkout path."""
        root = u.Tests.WorktreeFixture.governed_workspace(tmp_path, "duplicate")
        provider = u.Tests.provider()
        (root / c.Infra.GITMODULES).write_text(
            '[submodule "first"]\n'
            "\tpath = fixture-child\n"
            f"\turl = {provider.base_url}/fixture-child.git\n"
            f"\tbranch = {u.Tests.provider_branch()}\n"
            '[submodule "second"]\n'
            "\tpath = fixture-child\n"
            f"\turl = {provider.base_url}/fixture-child.git\n"
            f"\tbranch = {u.Tests.provider_branch()}\n",
            encoding="utf-8",
        )

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has="duplicate Git submodule path")

    @staticmethod
    def test_gitmodule_rejects_malformed_configuration(tmp_path: Path) -> None:
        """Reject syntax that cannot define an exact submodule contract."""
        root = u.Tests.WorktreeFixture.governed_workspace(
            tmp_path,
            "malformed-gitmodules",
        )
        (root / c.Infra.GITMODULES).write_text(
            '[submodule "unterminated"\npath = fixture-child\n',
            encoding="utf-8",
        )

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has="failed to read Git submodule declarations")

    @staticmethod
    @pytest.mark.parametrize("declared_path", ["../escape", "/absolute/escape"])
    def test_gitmodule_rejects_escaping_path(
        tmp_path: Path,
        declared_path: str,
    ) -> None:
        """Reject relative traversal and absolute checkout destinations."""
        root = u.Tests.WorktreeFixture.governed_workspace(tmp_path, "escaping-path")
        provider = u.Tests.provider()
        (root / c.Infra.GITMODULES).write_text(
            '[submodule "fixture-child"]\n'
            f"\tpath = {declared_path}\n"
            f"\turl = {provider.base_url}/fixture-child.git\n"
            f"\tbranch = {u.Tests.provider_branch()}\n",
            encoding="utf-8",
        )

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has="invalid Git submodule path")

    @staticmethod
    def test_gitmodule_rejects_missing_checkout(tmp_path: Path) -> None:
        """Reject a governed declaration whose checkout is absent."""
        root = u.Tests.WorktreeFixture.governed_workspace(tmp_path, "missing-checkout")
        u.Tests.WorktreeFixture.write_gitmodules(root, ("fixture-child",))

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has="governed subproject checkout is missing")

    @staticmethod
    def test_uninitialized_gitlink_does_not_borrow_parent_origin(
        tmp_path: Path,
    ) -> None:
        """Fail closed on an indexed, uninitialized checkout.

        The empty directory sits inside the parent repository, so a Git probe
        from it would resolve the parent's identity. The governed declaration
        (no ``flext-managed=false``) must therefore report the missing checkout
        instead of borrowing the parent origin.
        """
        root = u.Tests.WorktreeFixture.governed_workspace(
            tmp_path,
            "uninitialized-gitlink",
        )
        child_path = Path("fixture-child")
        u.Tests.WorktreeFixture.write_gitmodules(root, (child_path.as_posix(),))
        recorded = tm.ok(
            u.Cli.capture([c.Infra.GIT, "rev-parse", c.Infra.GIT_HEAD], cwd=root),
        ).strip()
        tm.ok(
            u.Cli.run_checked(
                [
                    c.Infra.GIT,
                    "update-index",
                    "--add",
                    "--cacheinfo",
                    f"160000,{recorded},{child_path.as_posix()}",
                ],
                cwd=root,
            ),
        )
        (root / child_path).mkdir()

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has=f"governed subproject checkout is missing: {child_path}")

    @staticmethod
    def test_gitmodule_rejects_provider_branch_divergence(tmp_path: Path) -> None:
        """Reject a governed checkout declared on another integration line."""
        root = u.Tests.WorktreeFixture.governed_workspace(tmp_path, "branch-divergence")
        u.Tests.WorktreeFixture.write_gitmodules(root, ("fixture-child",))
        gitmodules = root / c.Infra.GITMODULES
        gitmodules.write_text(
            gitmodules.read_text(encoding="utf-8").replace(
                u.Tests.provider_branch(),
                "unexpected-integration",
            ),
            encoding="utf-8",
        )

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has="branch differs from the workspace integration line")

    @staticmethod
    def test_declared_unmanaged_gitlink_classifies_as_external_dependency(
        tmp_path: Path,
    ) -> None:
        """Honor the .gitmodules overlay: flext-managed=false is never governed."""
        root = u.Tests.WorktreeFixture.governed_workspace(tmp_path, "overlay-external")
        (root / "external-fork").mkdir()
        (root / c.Infra.GITMODULES).write_text(
            '[submodule "external-fork"]\n'
            "\tpath = external-fork\n"
            "\turl = https://github.com/foreign-owner/external-fork.git\n"
            "\tbranch = master\n"
            "\tflext-classification = external-fork\n"
            "\tflext-managed = false\n",
            encoding="utf-8",
        )
        # A root declaring submodules is a workspace; its manifest must agree.
        _ = u.Tests.write_workspace_manifest(
            root,
            "fixture-workspace",
            role=c.Infra.MakeProfile.WORKSPACE,
        )

        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))

        tm.that(workspace.subprojects, empty=True)
        tm.that(workspace.external_dependency_paths, eq=(Path("external-fork"),))

    @staticmethod
    def test_gitmodule_accepts_the_published_integration_branch(
        tmp_path: Path,
    ) -> None:
        """Accept a governed checkout declared on the published integration line."""
        root = u.Tests.WorktreeFixture.governed_workspace(tmp_path, "integration-line")
        baseline = tm.ok(u.Cli.capture([c.Infra.GIT, "rev-parse", "HEAD"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "update-ref", "refs/remotes/origin/develop", baseline],
                cwd=root,
            ),
        )
        tm.ok(
            u.Cli.run_checked(
                [
                    c.Infra.GIT,
                    "update-ref",
                    "-d",
                    f"refs/remotes/origin/{u.Tests.provider_branch()}",
                ],
                cwd=root,
            ),
        )
        _ = u.Tests.WorktreeFixture.attach_member_child(root)
        child_url = u.Tests.WorktreeFixture.governed_repository_url("fixture-child")
        (root / c.Infra.GITMODULES).write_text(
            '[submodule "fixture-child"]\n'
            "\tpath = fixture-child\n"
            f"\turl = {child_url}\n"
            "\tbranch = develop\n",
            encoding="utf-8",
        )
        # A root declaring submodules is a workspace; its manifest must agree.
        _ = u.Tests.write_workspace_manifest(
            root,
            "fixture-workspace",
            role=c.Infra.MakeProfile.WORKSPACE,
        )

        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))

        tm.that(
            [item.path.as_posix() for item in workspace.subprojects],
            eq=["fixture-child"],
        )

    @staticmethod
    def test_gitmodule_rejects_origin_url_divergence(tmp_path: Path) -> None:
        """Reject a checkout whose origin identity differs from its declaration."""
        root = u.Tests.WorktreeFixture.governed_workspace(tmp_path, "url-divergence")
        _ = u.Tests.WorktreeFixture.attach_member_child(root)
        provider = u.Tests.provider()
        (root / c.Infra.GITMODULES).write_text(
            '[submodule "fixture-child"]\n'
            "\tpath = fixture-child\n"
            f"\turl = {provider.base_url}/different-child.git\n"
            f"\tbranch = {u.Tests.provider_branch()}\n",
            encoding="utf-8",
        )

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has="subproject origin differs from its .gitmodules URL")

    @staticmethod
    def test_gitmodule_rejects_unknown_provider_without_raw_url(
        tmp_path: Path,
    ) -> None:
        """Reject an unknown declared owner without leaking its raw URL."""
        root = u.Tests.WorktreeFixture.governed_workspace(tmp_path, "unknown-provider")
        # The detector requires the governed checkout before comparing origins.
        _ = u.Tests.WorktreeFixture.attach_member_child(root)
        raw_host_marker = "private-submodule-host"
        (root / c.Infra.GITMODULES).write_text(
            '[submodule "fixture-child"]\n'
            "\tpath = fixture-child\n"
            f"\turl = git@{raw_host_marker}:unknown-owner/fixture-child.git\n"
            f"\tbranch = {u.Tests.provider_branch()}\n",
            encoding="utf-8",
        )

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has="subproject origin differs from its .gitmodules URL")
        tm.that(result.error or "", lacks=raw_host_marker)

    @staticmethod
    def test_detected_provider_identity_normalizes_the_git_suffix() -> None:
        """Accept equivalent provider URLs with or without the clone suffix."""
        suffixed = u.Tests.repository_ref("fixture-project")
        bare = suffixed.model_copy(
            update={"url": suffixed.url.removesuffix(c.GIT_DIR_NAME)}
        )

        first = tm.ok(u.Infra.repository_provider(suffixed))
        second = tm.ok(u.Infra.repository_provider(bare))

        tm.that(first, eq=second)
        tm.that(first.name, eq=u.Tests.provider().name)
        tm.that(first.organization, eq=u.Tests.provider().organization)
