"""Release protocol behavior: plan, guard, version, and tag against real Git.

Every case drives the public CLI over a real repository whose merge commits
carry pull-request titles, exactly as GitHub leaves them when the merge commit
subject is the pull-request title.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from flext_infra import config
from tests import c, m, t, tm, u

if TYPE_CHECKING:
    from collections.abc import Generator


# These scenarios drive real release phases over Git repositories; their
# integration harness shares the declared slow policy.
@pytest.mark.slow
class TestsFlextInfraReleaseProtocol:
    """Behavior contract for the release protocol."""

    class TestsMaintenanceFinalization:
        """Explicit maintenance decisions do not reinterpret historical subjects."""

        @pytest.mark.parametrize(
            ("scenario", "outcome"),
            [
                (("7.4.6", "v7.4.6", "feat: existing capability"), ("7.4.7", True)),
                (("7.4.6", "v7.4.6", "perf: existing optimization"), ("7.4.7", True)),
                (
                    ("7.4.6", "v7.4.6", "chore: existing administration"),
                    ("7.4.7", True),
                ),
                (
                    ("7.4.6", "v7.4.6", "Merge pull request #8 from x/y"),
                    ("7.4.7", True),
                ),
                (("7.4.6", "v7.4.6", "feat!: historical marker"), ("7.4.7", True)),
                (("7.4.6", "v7.4.6", ""), ("7.4.7", True)),
                (("7.4.6", "", "feat: before first release"), ("7.4.6", True)),
                (("7.4.6rc2", "", "feat!: before first release"), ("7.4.6", True)),
                (("7.4.7", "v7.4.6", "chore(release): v7.4.7"), ("7.4.7", False)),
                (("7.4.7", "v7.4.6", "feat: declared ahead"), ("7.4.7", True)),
                (("7.4.7rc2", "v7.4.6", "legacy merge subject"), ("7.4.7", True)),
            ],
        )
        @staticmethod
        def test_explicit_patch_finalization_preserves_opaque_history(
            tmp_path: Path,
            scenario: tuple[str, str, str],
            outcome: tuple[str, bool],
        ) -> None:
            """A selected closure releases its line without compatibility inference."""
            current, tag, subject = scenario
            workspace = u.Tests.create_release_workspace(tmp_path, version=current)
            tm.ok(
                u.Cli.yaml_dump(
                    workspace / "config" / "infra.yaml",
                    {
                        "Infra": {
                            "release": {
                                "maintenance_line": [7, 4],
                                "finalize_maintenance": True,
                            }
                        }
                    },
                )
            )
            u.Tests.checkout_integration(workspace)
            if tag:
                TestsFlextInfraReleaseProtocol._tag(workspace, tag)
            if subject:
                u.Tests.merge_pull_request(workspace, subject)
            before = u.Tests.git_capture(workspace, "log", "--format=%H:%s")
            tm.that(u.Tests.run_release_main(workspace, "--phase", "plan"), eq=0)
            plan = TestsFlextInfraReleaseProtocol._plan(workspace)
            tm.that(plan.next, eq=outcome[0])
            tm.that(
                str(plan.bump),
                eq="patch" if tag == f"v{current}" else "none",
            )
            tm.that(plan.releasable, eq=outcome[1])
            tm.that(u.Tests.git_capture(workspace, "log", "--format=%H:%s"), eq=before)
            tm.ok(u.Infra.current_workspace_version(workspace), eq=current)

        @pytest.mark.parametrize("tag", ["", "v7.4.6", "v7.4.5"])
        @staticmethod
        def test_finalization_without_line_is_rejected_in_every_branch(
            tmp_path: Path,
            capsys: pytest.CaptureFixture[str],
            tag: str,
        ) -> None:
            """Require a line for first, tagged and awaiting releases."""
            workspace = u.Tests.create_release_workspace(tmp_path, version="7.4.6")
            tm.ok(
                u.Cli.yaml_dump(
                    workspace / "config" / "infra.yaml",
                    {"Infra": {"release": {"finalize_maintenance": True}}},
                )
            )
            u.Tests.checkout_integration(workspace)
            if tag:
                TestsFlextInfraReleaseProtocol._tag(workspace, tag)
                u.Tests.merge_pull_request(workspace, "chore(release): v7.4.6")
            tm.that(u.Tests.run_release_main(workspace, "--phase", "plan"), ne=0)
            output = capsys.readouterr()
            tm.that(output.out + output.err, has="requires a declared maintenance line")
            tm.fail(
                (
                    workspace / ".reports/release" / c.Infra.RELEASE_PLAN_FILENAME
                ).exists()
            )

        @staticmethod
        def test_generic_mode_uses_selected_consumer_bump_map(tmp_path: Path) -> None:
            """The generic planner uses its selected consumer's map."""
            workspace = u.Tests.create_release_workspace(tmp_path, version="7.4.6")
            tm.ok(
                u.Cli.yaml_dump(
                    workspace / "config" / "infra.yaml",
                    {"Infra": {"release": {"bump_types": {"feat": "patch"}}}},
                )
            )
            u.Tests.checkout_integration(workspace)
            TestsFlextInfraReleaseProtocol._tag(workspace, "v7.4.6")
            u.Tests.merge_pull_request(workspace, "feat: selected map scenario")
            tm.that(u.Tests.run_release_main(workspace, "--phase", "plan"), eq=0)
            tm.that(TestsFlextInfraReleaseProtocol._plan(workspace).next, eq="7.4.7")

    @staticmethod
    def _plan(workspace: Path) -> m.Infra.ReleasePlan:
        """Read the plan receipt the last ``plan`` phase wrote.

        Returns:
            The resulting ``m.Infra.ReleasePlan``.

        """
        payload = workspace / ".reports" / "release" / c.Infra.RELEASE_PLAN_FILENAME
        return m.Infra.ReleasePlan.model_validate_json(
            payload.read_text(encoding="utf-8"),
        )

    @staticmethod
    def _tag(repo: Path, tag: str) -> None:
        """Mark HEAD as an already-released version."""
        tm.ok(u.Cli.run_checked([c.Infra.GIT, "tag", "-a", tag, "-m", tag], cwd=repo))

    @classmethod
    def _released_workspace(cls, tmp_path: Path) -> Path:
        """Return a workspace on its integration branch with ``v0.1.0`` released.

        Returns:
            A workspace on its integration branch with ``v0.1.0`` released.

        """
        workspace = u.Tests.create_release_workspace(tmp_path)
        u.Tests.checkout_integration(workspace)
        cls._tag(workspace, "v0.1.0")
        return workspace

    @staticmethod
    def _release_lane_workspace(
        tmp_path: Path,
        runtime_environment: t.StrMapping | None = None,
    ) -> Path:
        """Return a pre-release workspace that can push to a local bare origin.

        Returns:
            A pre-release workspace that can push to a local bare origin.

        """
        if runtime_environment is None:
            workspace = u.Tests.create_release_workspace(
                tmp_path,
                version=c.Tests.RELEASE_VERSION_PRERELEASE,
            )
        else:
            workspace, _ = u.Tests.render_make_environment(
                tmp_path,
                c.Infra.MakeProfile.STANDALONE,
                bootstrap=True,
                shape=u.Tests.MakeEnvironmentShape(
                    project_name="workspace",
                    version=c.Tests.RELEASE_VERSION_PRERELEASE,
                ),
            )
            (workspace / ".gitignore").write_text(
                tm.ok(
                    u.Infra.render_project_gitignore(
                        config.Infra.codegen,
                        profile=c.Infra.MakeProfile.STANDALONE,
                        project_name=workspace.name,
                    )
                ),
                encoding="utf-8",
            )
            for verb in ("upg", "setup"):
                outcome = tm.ok(
                    u.Tests.run_isolated_make(
                        [verb],
                        cwd=workspace,
                        env={
                            **runtime_environment,
                            "UV_OFFLINE": c.ParserBooleanToken.ZERO,
                        },
                        private_env={
                            "GITHUB_TOKEN": t.SecretStr(os.environ["GITHUB_TOKEN"]),
                        },
                    )
                )
                tm.that(
                    u.Cli.process_succeeded(outcome.outcome),
                    truth=True,
                    msg=outcome.stderr + outcome.stdout,
                )
        u.Tests.commit_git_changes(workspace, "chore: seed release resolution inputs")
        local_origin = tmp_path / "remote"
        bare_origin = u.Tests.configure_local_origin(workspace, local_origin)
        provider = u.Tests.provider()
        tm.ok(
            u.Cli.run_checked(
                [
                    c.Infra.GIT,
                    "remote",
                    "set-url",
                    "origin",
                    f"{provider.base_url}/release-fixture.git",
                ],
                cwd=workspace,
            ),
        )
        u.Tests.git_bootstrap(
            workspace,
            (
                "config",
                "--local",
                f"url.{bare_origin}.insteadOf",
                f"{provider.base_url}/release-fixture.git",
            ),
        )
        tm.ok(
            u.Cli.run_checked(
                [
                    c.Infra.GIT,
                    "remote",
                    "set-url",
                    "--add",
                    "--push",
                    "origin",
                    # Why: the push URL must name the bare repository itself; the
                    # parent directory is not a git repository (git push exit 128).
                    # The bare path is the canonical return of configure_local_origin.
                    bare_origin.as_posix(),
                ],
                cwd=workspace,
            ),
        )
        u.Tests.checkout_integration(workspace)
        return workspace

    @staticmethod
    def _commit_merge_subject(workspace: Path, subject: str) -> None:
        """Record one empty commit whose subject a merge left on the lane."""
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "commit", "--allow-empty", "-m", subject],
                cwd=workspace,
            ),
        )

    def _planned_release(self, workspace: Path) -> m.Infra.ReleasePlan:
        """Run the plan phase once and return its receipt.

        Returns:
            The resulting ``m.Infra.ReleasePlan``.

        """
        tm.that(u.Tests.run_release_main(workspace, "--phase", "plan"), eq=0)
        return self._plan(workspace)

    @classmethod
    @contextmanager
    def _lane_with_shim(
        cls,
        tmp_path: Path,
        runtime_environment: t.StrMapping | None = None,
    ) -> Generator[tuple[Path, Path, m.Infra.GitLaneOwnershipReceipt]]:
        """Yield the release-lane fixture with the recording ``gh`` shim on PATH.

        Why: PATH is restored by the public ``env_vars_context`` facade rather
        than ``monkeypatch``, so the fixture stays inside the test utilities
        contract.

        Yields:
            The checkout, GitHub command log, and authenticated ownership receipt.

        """
        workspace = cls._release_lane_workspace(tmp_path, runtime_environment)
        snapshot = tm.ok(
            u.Infra.git_snapshot_worktree_state(
                m.Infra.GitWorktreeStateRequest(repo_root=workspace, paths=(Path(),)),
            ),
        )
        checkpoint = tm.ok(
            u.Infra.git_checkpoint_worktree_state(
                snapshot,
                "refs/checkpoints/release-owned",
            ),
        )
        publication = tm.ok(
            u.Infra.git_publish_worktree_checkpoint(checkpoint, c.Infra.GIT_ORIGIN),
        )
        u.Tests.git_run(
            workspace,
            "merge",
            "--no-ff",
            "-m",
            "chore: integrate prior owned state",
            checkpoint.worktree_commit,
        )
        u.Tests.git_run(
            workspace,
            "push",
            c.Infra.GIT_ORIGIN,
            u.Tests.integration_branch(workspace),
        )
        ownership = m.Infra.GitLaneOwnershipReceipt(
            checkpoint=checkpoint,
            publication=publication,
        )
        gh_log = u.Tests.cli_shim(tmp_path / "bin", c.Infra.GH)
        shim_path = f"{tmp_path / 'bin'}{os.pathsep}{os.environ['PATH']}"
        with u.Tests.env_vars_context(
            env_vars={
                **(runtime_environment or {}),
                "PATH": shim_path,
            }
        ):
            yield workspace, gh_log, ownership

    @staticmethod
    def _apply_release_version(
        workspace: Path,
        integration: str,
        ownership: m.Infra.GitLaneOwnershipReceipt,
    ) -> None:
        """Stamp the release version once and return to the integration branch."""
        tm.that(
            u.Tests.run_release_main(
                workspace,
                "--phase",
                "version",
                "--apply",
                ownership=ownership,
            ),
            eq=0,
        )
        tm.ok(u.Cli.run_checked([c.Infra.GIT, "switch", integration], cwd=workspace))

    def test_first_release_finalizes_the_declared_prerelease(
        self,
        tmp_path: Path,
    ) -> None:
        """Without any tag the declared pre-release ships as its base version."""
        workspace = u.Tests.create_release_workspace(
            tmp_path,
            version=c.Tests.RELEASE_VERSION_PRERELEASE,
        )

        result = u.Tests.run_release_main(workspace, "--phase", "plan")

        plan = self._plan(workspace)
        tm.that(result, eq=0)
        tm.that(plan.next, eq=c.Tests.RELEASE_VERSION_BASE)
        tm.that(plan.previous_tag, eq=None)
        tm.ok(plan.releasable)

    @pytest.mark.parametrize(
        ("current", "tag", "subject", "outcome"),
        [
            ("3.7.2", "", "", ("3.7.2", True)),
            ("3.7.2rc3", "", "", ("3.7.2", True)),
            ("3.7.2", "v3.7.2", "fix: repair runtime", ("3.7.3", True)),
            ("3.7.8", "v3.7.8", "fix: independent repair", ("3.7.9", True)),
            ("3.7.2", "v3.7.2", "docs: explain runtime", ("3.7.2", False)),
        ],
    )
    def test_maintenance_release_candidates(
        self,
        tmp_path: Path,
        current: str,
        tag: str,
        subject: str,
        outcome: tuple[str, bool],
    ) -> None:
        """Explicit scenario policy permits patches and declared releases."""
        workspace = u.Tests.create_release_workspace(tmp_path, version=current)
        tm.ok(
            u.Cli.yaml_dump(
                workspace / "config" / "infra.yaml",
                {"Infra": {"release": {"maintenance_line": [3, 7]}}},
            ),
        )
        u.Tests.checkout_integration(workspace)
        if tag:
            self._tag(workspace, tag)
        if subject:
            u.Tests.merge_pull_request(workspace, subject)
        plan = self._planned_release(workspace)
        tm.that(plan.next, eq=outcome[0])
        tm.that(plan.releasable, eq=outcome[1])

    @pytest.mark.parametrize(
        ("scenario", "diagnostic_fragment"),
        [
            (("3.7.2", "v3.7.2", "feat: introduce capability"), "bump=minor"),
            (("3.7.2", "v3.7.2", "fix!: remove public capability"), "bump=major"),
            (("3.8.1", "", ""), "allowed=3.7.x"),
            (("4.0.0rc1", "", ""), "allowed=3.7.x"),
            (("3.7.2", "v3.7.3", "fix: repair stale declaration"), "older than latest"),
            (("3.7.2rc1", "v3.7.2", ""), "older than latest"),
            (("3.8.1", "v3.7.2", "chore(release): v3.8.1"), "allowed=3.7.x"),
        ],
    )
    def test_maintenance_rejects_incompatible_candidates_without_receipt(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        scenario: tuple[str, str, str],
        diagnostic_fragment: str,
    ) -> None:
        """No semantic bump or newer declaration is silently clamped or downgraded."""
        current, tag, subject = scenario
        workspace = u.Tests.create_release_workspace(tmp_path, version=current)
        tm.ok(
            u.Cli.yaml_dump(
                workspace / "config" / "infra.yaml",
                {"Infra": {"release": {"maintenance_line": [3, 7]}}},
            ),
        )
        u.Tests.checkout_integration(workspace)
        if tag:
            self._tag(workspace, tag)
        if subject:
            u.Tests.merge_pull_request(workspace, subject)
        tm.that(u.Tests.run_release_main(workspace, "--phase", "plan"), ne=0)
        output = capsys.readouterr()
        diagnostic = output.out + output.err
        tm.that(diagnostic, has=current)
        tm.that(diagnostic, has=diagnostic_fragment)
        if diagnostic_fragment.startswith("bump="):
            tm.that(diagnostic, has=subject)
            tm.that(diagnostic, has="allowed=3.7.x")
        tm.fail(
            (
                workspace / ".reports" / "release" / c.Infra.RELEASE_PLAN_FILENAME
            ).exists(),
        )
        tm.that(tm.ok(u.Infra.current_workspace_version(workspace)), eq=current)

    def test_final_tag_outorders_rc_for_patch_planning(self, tmp_path: Path) -> None:
        """Merged stable and RC tags use semantic ordering, not Git refname order."""
        workspace = self._released_workspace(tmp_path)
        self._tag(workspace, "v0.1.0rc9")
        u.Tests.merge_pull_request(workspace, "fix: repair after final release")
        plan = self._planned_release(workspace)
        tm.that(plan.previous_tag, eq="v0.1.0")
        tm.that(plan.next, eq="0.1.1")

    @pytest.mark.parametrize("subject", ["fix: member repair", "feat: member feature"])
    @pytest.mark.parametrize("finalize", [False, True])
    def test_attached_member_inherits_workspace_maintenance_policy(
        self,
        tmp_path: Path,
        subject: str,
        *,
        finalize: bool,
    ) -> None:
        """Git attachment elects the enclosing policy without per-member copies."""
        workspace = u.Tests.create_release_workspace(tmp_path, version="3.7.1")
        tm.ok(
            u.Cli.yaml_dump(
                workspace / "config" / "infra.yaml",
                {
                    "Infra": {
                        "release": {
                            "maintenance_line": [3, 7],
                            "finalize_maintenance": finalize,
                        }
                    }
                },
            ),
        )
        member_seed = u.Tests.WorktreeFixture.self_named_project(
            tmp_path / "member-seed" / "member-project",
            "member-project",
        )
        tm.ok(u.Infra.replace_project_version(member_seed, "3.7.8"))
        u.Tests.commit_git_changes(
            member_seed,
            c.Infra.RELEASE_COMMIT_SUBJECT.format(version="3.7.8"),
        )
        (workspace / "member").mkdir()
        member = member_seed.rename(workspace / "member" / member_seed.name)
        u.Tests.WorktreeFixture.attach_submodule(
            workspace,
            member,
            distribution=member.name,
            relative_path=member.relative_to(workspace).as_posix(),
        )
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "submodule", "absorbgitdirs"],
                cwd=workspace,
            ),
        )
        u.Tests.checkout_integration(member)
        self._tag(member, "v3.7.8")
        u.Tests.merge_pull_request(member, subject)
        result = u.Tests.run_release_main(member, "--phase", "plan")
        if finalize or subject.startswith("fix:"):
            tm.that(result, eq=0)
            tm.that(self._plan(member).next, eq="3.7.9")
        else:
            tm.that(result, ne=0)

    def test_first_release_ships_a_final_version_unchanged(
        self,
        tmp_path: Path,
    ) -> None:
        """A final version without a tag is released as declared, never bumped."""
        workspace = u.Tests.create_release_workspace(tmp_path)
        u.Tests.merge_pull_request(workspace, "feat: history before the first tag")

        result = u.Tests.run_release_main(workspace, "--phase", "plan")

        plan = self._plan(workspace)
        tm.that(result, eq=0)
        tm.that(plan.next, eq=c.Tests.RELEASE_VERSION_BASE)
        tm.ok(plan.releasable)

    def test_declared_prerelease_finalizes_without_consulting_titles(
        self,
        tmp_path: Path,
    ) -> None:
        """A pre-release was decided when it was cut; later history is not parsed."""
        workspace = u.Tests.create_release_workspace(
            tmp_path,
            version=c.Tests.RELEASE_VERSION_PRERELEASE,
        )
        u.Tests.checkout_integration(workspace)
        self._tag(workspace, "v0.1.0rc0")
        u.Tests.merge_pull_request(workspace, "Merge pull request #1 from x/y")

        result = u.Tests.run_release_main(workspace, "--phase", "plan")

        plan = self._plan(workspace)
        tm.that(result, eq=0)
        tm.that(plan.next, eq=c.Tests.RELEASE_VERSION_BASE)
        tm.that(plan.previous_tag, eq="v0.1.0rc0")
        tm.ok(plan.releasable)

    def test_plan_ignores_higher_tag_outside_integration_history(
        self,
        tmp_path: Path,
    ) -> None:
        """A release on an unrelated branch cannot select this lane's baseline."""
        workspace = self._released_workspace(tmp_path)
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "switch", "-c", "unrelated-release"],
                cwd=workspace,
            ),
        )
        self._commit_merge_subject(workspace, "chore(release): v9.0.0")
        self._tag(workspace, "v9.0.0")
        u.Tests.checkout_integration(workspace)
        u.Tests.merge_pull_request(workspace, "fix: repair the integrated runtime")

        plan = self._planned_release(workspace)

        tm.that(plan.previous_tag, eq="v0.1.0")
        tm.that(plan.next, eq="0.1.1")
        tm.ok(plan.releasable)

    def test_final_version_is_ahead_of_its_own_prerelease_tag(
        self,
        tmp_path: Path,
    ) -> None:
        """A final version whose last tag is one of its pre-releases ships as declared.

        The release triple is shared, so only a comparison that keeps the
        pre-release segment sees that ``0.1.0`` follows ``v0.1.0rc2``.
        """
        workspace = u.Tests.create_release_workspace(tmp_path)
        u.Tests.checkout_integration(workspace)
        self._tag(workspace, "v0.1.0rc2")
        self._commit_merge_subject(workspace, "Merge pull request #4 from legacy/lane")
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "fetch", c.Infra.GIT_ORIGIN],
                cwd=workspace,
            ),
        )

        plan = self._planned_release(workspace)
        tm.that(plan.next, eq=c.Tests.RELEASE_VERSION_BASE)
        tm.that(plan.previous_tag, eq="v0.1.0rc2")
        tm.ok(plan.releasable)

    def test_declared_version_ahead_of_the_last_tag_is_the_next_release(
        self,
        tmp_path: Path,
    ) -> None:
        """A version declared beyond the last tag was decided before the protocol.

        It ships as declared; the titles merged since the tag (including
        GitHub's default merge subjects) are not consulted.
        """
        workspace = self._released_workspace(tmp_path)
        self._commit_merge_subject(workspace, "Merge pull request #3 from legacy/lane")
        tm.ok(u.Infra.replace_project_version(workspace, "0.2.0"))
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "commit", "-am", "chore: baseline 0.2.0"],
                cwd=workspace,
            ),
        )
        # The fixture's origin is the repository itself: refresh the remote
        # ref so the integration base carries the declared version.
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "fetch", c.Infra.GIT_ORIGIN],
                cwd=workspace,
            ),
        )

        plan = self._planned_release(workspace)
        tm.that(plan.next, eq="0.2.0")
        tm.that(plan.bump, eq=c.Infra.VersionBump.NONE)
        tm.ok(plan.releasable)

    def test_pull_request_titles_decide_the_bump(self, tmp_path: Path) -> None:
        """The most significant Conventional title since the last tag wins."""
        workspace = self._released_workspace(tmp_path)
        u.Tests.merge_pull_request(workspace, "fix(core): patch level")
        u.Tests.merge_pull_request(workspace, "feat(cli): minor level")
        u.Tests.merge_pull_request(workspace, "[WIP] merge origin/integration")

        result = u.Tests.run_release_main(workspace, "--phase", "plan")

        plan = self._plan(workspace)
        tm.that(result, eq=0)
        tm.that(plan.next, eq="0.2.0")
        tm.that(plan.bump, eq=c.Infra.VersionBump.MINOR)
        tm.that(plan.previous_tag, eq="v0.1.0")
        tm.that(len(plan.merges), eq=3)

    def test_breaking_marker_earns_a_major_bump(self, tmp_path: Path) -> None:
        """``!`` in a pull-request title is a breaking change."""
        workspace = self._released_workspace(tmp_path)
        u.Tests.merge_pull_request(workspace, "feat!: remove the legacy surface")

        tm.that(self._planned_release(workspace).next, eq="1.0.0")

    def test_non_releasing_titles_release_nothing(self, tmp_path: Path) -> None:
        """Docs and chores keep the version; the plan is not releasable."""
        workspace = self._released_workspace(tmp_path)
        u.Tests.merge_pull_request(workspace, "docs: explain the protocol")

        plan = self._planned_release(workspace)
        tm.that(plan.next, eq=plan.current)
        tm.fail(plan.releasable)

    def test_default_github_merge_subject_fails_loud(self, tmp_path: Path) -> None:
        """A merged pull request without its title carries no release truth."""
        workspace = self._released_workspace(tmp_path)
        u.Tests.merge_pull_request(workspace, "Merge pull request #7 from x/y")

        tm.that(u.Tests.run_release_main(workspace, "--phase", "plan"), ne=0)

    def test_manual_version_edit_is_rejected(self, tmp_path: Path) -> None:
        """A hand-edited pyproject version fails the plan, naming the commit."""
        workspace = self._released_workspace(tmp_path)
        tm.ok(u.Infra.replace_project_version(workspace, "0.1.1"))
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "commit", "-am", "chore: bump"],
                cwd=workspace,
            ),
        )

        tm.that(u.Tests.run_release_main(workspace, "--phase", "plan"), ne=0)

    def test_protocol_release_commit_is_accepted(self, tmp_path: Path) -> None:
        """Only the release commit may carry the version it names."""
        workspace = self._released_workspace(tmp_path)
        tm.ok(u.Infra.replace_project_version(workspace, "0.1.1"))
        subject = c.Infra.RELEASE_COMMIT_SUBJECT.format(version="0.1.1")
        tm.ok(u.Cli.run_checked([c.Infra.GIT, "commit", "-am", subject], cwd=workspace))

        plan = self._planned_release(workspace)
        tm.that(plan.next, eq="0.1.1")
        tm.fail(plan.releasable)

    def test_repository_declared_integration_branch_governs_the_plan(
        self,
        tmp_path: Path,
    ) -> None:
        """A consumer integrating on its own declared line plans against it.

        The workspace policy line is not published here: only the repository's
        ``repository.integration`` declaration names the base the version guard
        compares against, exactly as a consumer that integrates on ``dev``.
        """
        workspace = self._released_workspace(tmp_path)
        declared = "integration/declared-line"
        codegen = workspace / "config" / c.Infra.CODEGEN_CONFIG_FILENAME
        codegen.parent.mkdir(parents=True, exist_ok=True)
        tm.ok(
            u.Cli.yaml_dump(
                codegen,
                {
                    "Infra": {
                        "codegen": {
                            "repository": {
                                "integration": {
                                    "provider": u.Tests.provider().name,
                                    "branch": declared,
                                },
                            },
                        },
                    },
                },
            ),
        )
        tm.ok(u.Cli.run_checked([c.Infra.GIT, "add", "config"], cwd=workspace))
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "commit", "-m", "chore: declare integration"],
                cwd=workspace,
            ),
        )
        published = u.Tests.git_capture(
            workspace,
            "for-each-ref",
            "--format=%(refname)",
            "refs/remotes/origin",
        )
        for reference in published.split():
            tm.ok(
                u.Cli.run_checked(
                    [c.Infra.GIT, "update-ref", "-d", reference],
                    cwd=workspace,
                ),
            )
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "update-ref", f"refs/remotes/origin/{declared}", "HEAD"],
                cwd=workspace,
            ),
        )
        tm.ok(u.Infra.replace_project_version(workspace, "0.1.1"))
        subject = c.Infra.RELEASE_COMMIT_SUBJECT.format(version="0.1.1")
        tm.ok(u.Cli.run_checked([c.Infra.GIT, "commit", "-am", subject], cwd=workspace))

        plan = self._planned_release(workspace)

        tm.that(plan.next, eq="0.1.1")

    def test_merged_release_commit_awaits_its_tag_from_any_head(
        self,
        tmp_path: Path,
    ) -> None:
        """GitHub's merged form of the release commit, below HEAD, ends the plan.

        The merge appends the pull-request number to the subject, and CI plans
        on a synthetic merge commit above it; neither may reopen the release
        nor consult the titles merged before it.
        """
        workspace = self._released_workspace(tmp_path)
        self._commit_merge_subject(workspace, "Merge pull request #7 from legacy/lane")
        tm.ok(u.Infra.replace_project_version(workspace, "0.1.1"))
        merged_subject = (
            f"{c.Infra.RELEASE_COMMIT_SUBJECT.format(version='0.1.1')} (#8)"
        )
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "commit", "-am", merged_subject],
                cwd=workspace,
            ),
        )
        self._commit_merge_subject(workspace, "Merge abc123 into def456")

        plan = self._planned_release(workspace)
        tm.that(plan.next, eq="0.1.1")
        tm.that(plan.bump, eq=c.Infra.VersionBump.NONE)
        tm.fail(plan.releasable)

    def test_apply_opens_the_release_pull_request(
        self,
        tmp_path: Path,
        hermetic_git_environment: t.StrMapping,
    ) -> None:
        """Stamp, commit on the release lane, push it, and open the pull request."""
        with self._lane_with_shim(tmp_path, hermetic_git_environment) as (
            workspace,
            gh_log,
            ownership,
        ):
            integration = u.Tests.integration_branch(workspace)
            # flext-core caches the parsed pyproject per process; a warm cache
            # holding the pre-stamp document must not leak into the projections.
            tm.ok(u.Infra.read_project_metadata_result(workspace))
            locks = tuple(
                (workspace / name, (workspace / name).read_text(encoding="utf-8"))
                for name in u.Tests.git_capture(
                    workspace,
                    "ls-files",
                    "--",
                    f"*{c.Infra.UV_LOCK_FILENAME}",
                ).splitlines()
            )
            tm.that(locks, truth=True)

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                "version",
                "--apply",
                ownership=ownership,
            )

            tm.that(result, eq=0)
            tm.ok(
                u.Infra.current_workspace_version(workspace),
                eq=c.Tests.RELEASE_VERSION_BASE,
            )
            tm.ok((workspace / "docs" / "CHANGELOG.md").is_file())
            head = tm.ok(
                u.Cli.capture([c.Infra.GIT, "log", "-1", "--format=%s"], cwd=workspace),
            ).strip()
            tm.that(head, eq=c.Infra.RELEASE_COMMIT_SUBJECT.format(version="0.1.0"))
            # The docs projections render the version; the release commit
            # carries them regenerated, so the lane is a `gen check` fixed point.
            # Resolution stays owned by make upg, not the version operation.
            committed = tm.ok(
                u.Cli.capture(
                    [c.Infra.GIT, "show", "--name-only", "--format=", c.Infra.GIT_HEAD],
                    cwd=workspace,
                ),
            )
            tm.that(committed, has=[c.PYPROJECT_FILENAME, "docs/index.md"])
            for lock, before in locks:
                tm.that(lock.read_text(encoding="utf-8"), eq=before)
                tm.that(committed, lacks=lock.relative_to(workspace).as_posix())
            tm.that(
                (workspace / "docs" / "index.md").read_text(encoding="utf-8"),
                has=f"- Version: `{c.Tests.RELEASE_VERSION_BASE}`",
                lacks=c.Tests.RELEASE_VERSION_PRERELEASE,
            )
            tm.that(
                u.Infra.git_status(
                    m.Infra.GitStatusRequest(repo_root=workspace),
                ).value.dirty,
                eq=False,
            )
            tm.that(
                tm.ok(
                    u.Cli.capture(
                        [c.Infra.GIT, "branch", "--show-current"],
                        cwd=workspace,
                    ),
                ).strip(),
                eq=c.Infra.RELEASE_BRANCH,
            )
            remote_ref = tm.ok(
                u.Cli.capture(
                    [c.Infra.GIT, "rev-parse", f"refs/heads/{c.Infra.RELEASE_BRANCH}"],
                    cwd=tmp_path / "remote" / "origin.git",
                ),
            ).strip()
            tm.that(len(remote_ref), eq=40)
            recorded = gh_log.read_text(encoding="utf-8")
            tm.that(
                recorded,
                has=(f"pr create --base {integration} --head {c.Infra.RELEASE_BRANCH}"),
            )
            tm.that(recorded, has="--title chore(release): v0.1.0")

    def test_rerun_continues_the_lane_without_a_second_commit(
        self,
        tmp_path: Path,
        hermetic_git_environment: t.StrMapping,
    ) -> None:
        """A retry from the integration branch is idempotent on the open lane."""
        with self._lane_with_shim(tmp_path, hermetic_git_environment) as (
            workspace,
            _,
            ownership,
        ):
            integration = u.Tests.integration_branch(workspace)
            self._apply_release_version(workspace, integration, ownership)

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                "version",
                "--apply",
                ownership=ownership,
            )

            tm.that(result, eq=0)
            lane_commits = tm.ok(
                u.Cli.capture(
                    [
                        c.Infra.GIT,
                        "rev-list",
                        "--count",
                        f"{integration}..{c.Infra.RELEASE_BRANCH}",
                    ],
                    cwd=workspace,
                ),
            ).strip()
            tm.that(lane_commits, eq=c.ParserBooleanToken.ONE)
            head = tm.ok(
                u.Cli.capture([c.Infra.GIT, "log", "-1", "--format=%s"], cwd=workspace),
            ).strip()
            tm.that(head, eq=c.Infra.RELEASE_COMMIT_SUBJECT.format(version="0.1.0"))

    class TestsAdmission:
        """Version and tag admission against real Git state."""

        @pytest.mark.parametrize("foreign_owner", [False, True])
        @staticmethod
        def test_release_version_refuses_missing_or_foreign_ownership(
            tmp_path: Path,
            capsys: pytest.CaptureFixture[str],
            *,
            foreign_owner: bool,
        ) -> None:
            """The public request cannot admit an absent or another checkout's proof."""
            with TestsFlextInfraReleaseProtocol._lane_with_shim(tmp_path) as (
                workspace,
                _,
                _,
            ):
                with TestsFlextInfraReleaseProtocol._lane_with_shim(
                    tmp_path / "foreign",
                ) as (_, _, foreign):
                    result = u.Tests.run_release_main(
                        workspace,
                        "--phase",
                        "version",
                        "--apply",
                        ownership=foreign if foreign_owner else None,
                    )
                tm.that(result, ne=0)
                output = capsys.readouterr()
                tm.that(
                    output.out + output.err,
                    has=(
                        "lane ownership receipt does not cover this entire repository"
                        if foreign_owner
                        else "authoritative Beads ownership"
                    ),
                )
                tm.that(
                    u.Tests.git_capture(workspace, "branch", "--show-current"),
                    eq=u.Tests.integration_branch(workspace),
                )
                tm.ok(
                    u.Infra.current_workspace_version(workspace),
                    eq=c.Tests.RELEASE_VERSION_PRERELEASE,
                )

        @staticmethod
        def test_pull_request_title_is_validated_when_given(tmp_path: Path) -> None:
            """A CI check passes a title; only a Conventional title is accepted."""
            workspace = u.Tests.create_release_workspace(tmp_path)
            accepted = u.Tests.run_release_main(
                workspace,
                "--phase",
                "plan",
                "--pr-title",
                "feat(core): accepted",
            )
            rejected = u.Tests.run_release_main(
                workspace,
                "--phase",
                "plan",
                "--pr-title",
                "Accepted without a type",
            )
            tm.that(accepted, eq=0)
            tm.that(rejected, ne=0)

        @staticmethod
        def test_dry_run_changes_nothing(tmp_path: Path) -> None:
            """Without apply the plan is reported and the checkout is untouched."""
            workspace = TestsFlextInfraReleaseProtocol._release_lane_workspace(tmp_path)
            tm.that(u.Tests.run_release_main(workspace, "--phase", "version"), eq=0)
            tm.ok(
                u.Infra.current_workspace_version(workspace),
                eq=c.Tests.RELEASE_VERSION_PRERELEASE,
            )
            tm.fail((workspace / "docs").exists())

        @staticmethod
        def test_dirty_checkout_is_refused(tmp_path: Path) -> None:
            """A release commit never absorbs unrelated working-tree changes."""
            workspace = TestsFlextInfraReleaseProtocol._release_lane_workspace(tmp_path)
            (workspace / "stray.txt").write_text("wip\n", encoding="utf-8")
            tm.that(
                u.Tests.run_release_main(workspace, "--phase", "version", "--apply"),
                ne=0,
            )

        @staticmethod
        def test_non_integration_branch_is_refused(tmp_path: Path) -> None:
            """The release pull request is cut from the integration branch only."""
            workspace = u.Tests.create_release_workspace(
                tmp_path,
                version=c.Tests.RELEASE_VERSION_PRERELEASE,
            )
            tm.that(
                u.Tests.run_release_main(workspace, "--phase", "version", "--apply"),
                ne=0,
            )

        @staticmethod
        def test_nothing_to_release_is_a_clean_no_op(tmp_path: Path) -> None:
            """A tagged repository with no releasing titles opens no pull request."""
            workspace = TestsFlextInfraReleaseProtocol._released_workspace(tmp_path)
            u.Tests.merge_pull_request(workspace, "docs: nothing to ship")
            tm.that(
                u.Tests.run_release_main(workspace, "--phase", "version", "--apply"),
                eq=0,
            )
            tm.that(
                tm.ok(
                    u.Cli.capture(
                        [c.Infra.GIT, "branch", "--list", c.Infra.RELEASE_BRANCH],
                        cwd=workspace,
                    ),
                ).strip(),
                eq="",
            )

        @staticmethod
        def test_merged_release_commit_is_tagged_and_pushed(
            tmp_path: Path,
            hermetic_git_environment: t.StrMapping,
        ) -> None:
            """After the release pull request merges, HEAD earns its tag once."""
            with TestsFlextInfraReleaseProtocol._lane_with_shim(
                tmp_path,
                hermetic_git_environment,
            ) as (
                workspace,
                _,
                ownership,
            ):
                integration = u.Tests.integration_branch(workspace)
                TestsFlextInfraReleaseProtocol._apply_release_version(
                    workspace,
                    integration,
                    ownership,
                )
                subject = (
                    f"{c.Infra.RELEASE_COMMIT_SUBJECT.format(version='0.1.0')} (#1)"
                )
                tm.ok(
                    u.Cli.run_checked(
                        [c.Infra.GIT, "switch", integration],
                        cwd=workspace,
                    ),
                )
                tm.ok(
                    u.Cli.run_checked(
                        [
                            c.Infra.GIT,
                            "merge",
                            "--no-ff",
                            "-m",
                            subject,
                            c.Infra.RELEASE_BRANCH,
                        ],
                        cwd=workspace,
                    ),
                )
                first = u.Tests.run_release_main(workspace, "--phase", "tag", "--apply")
                second = u.Tests.run_release_main(
                    workspace,
                    "--phase",
                    "tag",
                    "--apply",
                )
                tm.that(first, eq=0)
                tm.that(second, eq=0)
                for repository in (workspace, tmp_path / "remote" / "origin.git"):
                    tm.that(
                        tm.ok(
                            u.Cli.capture(
                                [c.Infra.GIT, "tag", "-l", "v0.1.0"],
                                cwd=repository,
                            ),
                        ).strip(),
                        eq="v0.1.0",
                    )

        @staticmethod
        def test_head_without_release_commit_is_refused(tmp_path: Path) -> None:
            """Only the protocol's release commit may be tagged."""
            workspace = TestsFlextInfraReleaseProtocol._released_workspace(tmp_path)
            u.Tests.merge_pull_request(workspace, "feat: not a release commit")
            tm.that(
                u.Tests.run_release_main(workspace, "--phase", "tag", "--apply"),
                ne=0,
            )
