"""Publication lane behavior: what a step produces reaches one pull request.

The lane is the canonical owner release and member propagation share: from a
clean integration checkout, ``u.Infra.git_publish_lane`` enters the lane,
runs the producing step, commits exactly the paths it produced, pushes the
lane and opens or refreshes its pull request.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r

from tests import c, m, p, t, tm, u

if TYPE_CHECKING:
    from collections.abc import Callable, Generator


class TestsFlextInfraReleasePublicationLane:
    """Behavior contract for the shared publication lane."""

    LANE = "lane/propagation"
    SUBJECT = "chore(deps): propagate the integrated infrastructure"

    @contextmanager
    def _lane(
        self,
        tmp_path: Path,
    ) -> Generator[t.Triple[Path, m.Infra.GitLaneRequest, Path]]:
        """Yield a clean integration checkout, its lane request and the ``gh`` log.

        Yields:
            Each ``t.Triple[Path, m.Infra.GitLaneRequest, Path]``.

        """
        repo = u.Tests.git_repository(tmp_path)
        base = u.Tests.checkout_integration(repo)
        u.Tests.configure_local_origin(repo, tmp_path / "remote")
        manifest = tm.ok(
            u.Infra.load_workspace_manifest(
                Path(__file__).resolve().parents[3],
            )
        )[0]
        declared = manifest.model_copy(
            update={
                "integration": m.Infra.WorkspaceIntegrationSpec(
                    provider=manifest.repository.provider,
                    branch=base,
                ),
            }
        )
        u.Infra.workspace_manifest_path(repo).parent.mkdir(exist_ok=True)
        tm.ok(
            u.Cli.yaml_dump(
                u.Infra.workspace_manifest_path(repo),
                declared.model_dump(mode="json"),
            )
        )
        u.Tests.commit_git_changes(repo, "declare integration owner")
        u.Tests.git_run(repo, "push", c.Infra.GIT_ORIGIN, base)
        snapshot = tm.ok(
            u.Infra.git_snapshot_worktree_state(
                m.Infra.GitWorktreeStateRequest(repo_root=repo, paths=(Path(),)),
            )
        )
        checkpoint = tm.ok(
            u.Infra.git_checkpoint_worktree_state(
                snapshot,
                "refs/checkpoints/prior-owned",
            )
        )
        publication = tm.ok(
            u.Infra.git_publish_worktree_checkpoint(checkpoint, c.Infra.GIT_ORIGIN)
        )
        u.Tests.git_run(
            repo,
            "merge",
            "--no-ff",
            "-m",
            "integrate owned state",
            checkpoint.worktree_commit,
        )
        u.Tests.git_run(repo, "push", c.Infra.GIT_ORIGIN, base)
        body = tmp_path / "body.md"
        body.write_text("# Propagation\n", encoding="utf-8")
        gh_log = u.Tests.cli_shim(tmp_path / "bin", c.Infra.GH)
        shim_path = f"{tmp_path / 'bin'}{os.pathsep}{os.environ['PATH']}"
        request = m.Infra.GitLaneRequest(
            repo_root=repo,
            branch=self.LANE,
            base=base,
            subject=self.SUBJECT,
            body_file=body,
            ownership=m.Infra.GitLaneOwnershipReceipt(
                checkpoint=checkpoint, publication=publication
            ),
        )
        with u.Tests.env_vars_context(env_vars={"PATH": shim_path}):
            yield repo, request, gh_log

    @staticmethod
    def _produce(
        repo: Path,
        content: str = "produced\n",
    ) -> Callable[[], p.Result[bool]]:
        """Return a producing step that writes one file.

        Returns:
            A producing step that writes one file.

        """
        return lambda: u.Cli.files_write_text(repo / "produced.txt", content)

    def _published(self, tmp_path: Path) -> str:
        """Return the lane branch the bare origin carries, or an empty string.

        Returns:
            The lane branch the bare origin carries, or an empty string.

        """
        return u.Tests.git_capture(
            tmp_path / "remote" / "origin.git",
            "branch",
            "--list",
            self.LANE,
        ).strip()

    def test_new_lane_is_refused_without_ownership_evidence(
        self,
        tmp_path: Path,
    ) -> None:
        """Lane creation fails closed until admission can prove ownership.

        The native admission contract (31959fed0; bead flext-itpd1.3.26 owns
        the Beads-ownership and prior-lane-integration proof) refuses every
        new lane, so publication creates nothing: no lane branch, no pushed
        branch, no commit of the produced path, no pull request.
        """
        with self._lane(tmp_path) as (repo, request, gh_log):
            head = u.Tests.git_capture(repo, "rev-parse", "HEAD").strip()

            result = u.Infra.git_publish_lane(request, self._produce(repo))

            tm.fail(result)
            tm.that(result.error or "", has="new lane refused")
            tm.fail(u.Tests.git_ref_exists(repo, f"refs/heads/{self.LANE}"))
            tm.that(self._published(tmp_path), eq="")
            tm.that(u.Tests.git_capture(repo, "rev-parse", "HEAD").strip(), eq=head)
            tm.fail(gh_log.exists())

    def test_dirty_checkout_is_refused(self, tmp_path: Path) -> None:
        """A lane never absorbs changes it did not produce."""
        with self._lane(tmp_path) as (repo, request, gh_log):
            (repo / "stray.txt").write_text("wip\n", encoding="utf-8")

            tm.fail(u.Infra.git_publish_lane(request, self._produce(repo)))
            tm.fail(u.Tests.git_ref_exists(repo, f"refs/heads/{self.LANE}"))
            tm.fail(gh_log.exists())

    def test_checkout_off_its_base_is_refused(self, tmp_path: Path) -> None:
        """A lane starts only from the branch its pull request targets."""
        with self._lane(tmp_path) as (repo, request, _):
            tm.ok(u.Tests.git_run(repo, "switch", "--create", "elsewhere"))

            result = u.Infra.git_publish_lane(request, self._produce(repo))

            tm.fail(result)
            tm.fail(u.Tests.git_ref_exists(repo, f"refs/heads/{self.LANE}"))

    def test_failed_production_publishes_nothing(self, tmp_path: Path) -> None:
        """The first failure of the producing step ends the lane unpushed."""
        with self._lane(tmp_path) as (_repo, request, gh_log):
            result = u.Infra.git_publish_lane(
                request,
                lambda: r[bool].fail("production failed"),
            )

            tm.fail(result)
            tm.that(self._published(tmp_path), eq="")
            tm.fail(gh_log.exists())

    def test_refused_lane_never_runs_the_producer(self, tmp_path: Path) -> None:
        """Admission refuses before production: no byte is written or staged."""
        with self._lane(tmp_path) as (repo, request, gh_log):
            original_head = u.Tests.git_capture(repo, "rev-parse", "HEAD").strip()
            produced = repo / "partial.txt"
            calls: list[str] = []

            def produce() -> p.Result[bool]:
                calls.append("produce")
                return u.Cli.files_write_text(produced, "partial production\n")

            result = u.Infra.git_publish_lane(request, produce)

            tm.fail(result)
            tm.that(result.error or "", has="new lane refused")
            tm.that(calls, eq=[])
            tm.fail(produced.exists())
            tm.that(
                u.Tests.git_capture(repo, "status", "--porcelain").strip(),
                eq="",
            )
            tm.that(
                u.Tests.git_capture(repo, "rev-parse", "HEAD").strip(),
                eq=original_head,
            )
            tm.fail(gh_log.exists())
