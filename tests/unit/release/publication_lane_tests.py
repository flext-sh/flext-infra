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

import pytest

from tests import c, m, p, r, tm, u

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
    ) -> Generator[tuple[Path, p.Infra.GitLaneRequest, Path]]:
        """Yield a clean integration checkout, its lane request and the ``gh`` log.

        Yields:
            Each ``tuple[Path, m.Infra.GitLaneRequest, Path]``.

        """
        repo = u.Tests.git_repository(tmp_path)
        base = u.Tests.checkout_integration(repo)
        u.Tests.configure_local_origin(repo, tmp_path / "remote")
        # The fixture owner declares the standalone repository; the lane test
        # only binds its integration line to the checkout's base.
        u.Tests.write_standalone_workspace_manifest(repo, repo.name)
        manifest = tm.ok(u.Infra.load_workspace_manifest(repo))[0]
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
        )
        with u.Tests.env_vars_context(env_vars={"PATH": shim_path}):
            yield repo, request, gh_log

    @staticmethod
    def _produce(
        target: Path,
        content: str = "produced\n",
    ) -> Callable[[], p.Result[bool]]:
        """Return a producing step that writes ``target``.

        Returns:
            A producing step that writes ``target``.

        """
        return lambda: u.Cli.files_write_text(target, content)

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

    def test_lane_publishes_from_a_clean_base_without_a_receipt(
        self,
        tmp_path: Path,
    ) -> None:
        """A clean integration checkout carries its production to one lane.

        The protocol lane needs no agent-lane ownership receipt: a clean CI
        checkout on the declared base enters the lane, commits exactly the
        produced path, pushes the lane and opens its pull request.
        """
        with self._lane(tmp_path) as (repo, request, gh_log):
            result = u.Infra.git_publish_lane(
                request, self._produce(repo / "produced.txt")
            )

            tm.ok(result, eq=True)
            tm.that(u.Tests.git_ref_exists(repo, f"refs/heads/{self.LANE}"), eq=True)
            tm.that(self._published(tmp_path), has=self.LANE)
            tm.that(
                u.Tests.git_capture(
                    repo, "show", "--name-only", "--format=%s", self.LANE
                ),
                has=[self.SUBJECT, "produced.txt"],
            )
            tm.that(gh_log.exists(), eq=True)

    def test_body_beyond_github_ceiling_fails_before_publication(
        self,
        tmp_path: Path,
    ) -> None:
        """A body GitHub would reject fails loud: nothing pushed, no ``gh`` call."""
        with self._lane(tmp_path) as (repo, request, gh_log):
            request.body_file.write_text(
                "x" * (c.Infra.GH_PULL_REQUEST_BODY_MAX_CHARS + 1),
                encoding="utf-8",
            )

            result = u.Infra.git_publish_lane(
                request, self._produce(repo / "produced.txt")
            )

            tm.fail(result)
            tm.that(result.error or "", has=str(request.body_file))
            tm.that(self._published(tmp_path), eq="")
            tm.fail(gh_log.exists())

    def test_dirty_checkout_is_refused(self, tmp_path: Path) -> None:
        """A lane never absorbs changes it did not produce."""
        with self._lane(tmp_path) as (repo, request, gh_log):
            (repo / "stray.txt").write_text("wip\n", encoding="utf-8")

            tm.fail(
                u.Infra.git_publish_lane(request, self._produce(repo / "produced.txt"))
            )
            tm.fail(u.Tests.git_ref_exists(repo, f"refs/heads/{self.LANE}"))
            tm.fail(gh_log.exists())

    def test_checkout_off_its_base_is_refused(self, tmp_path: Path) -> None:
        """A lane starts only from the branch its pull request targets."""
        with self._lane(tmp_path) as (repo, request, _):
            tm.ok(u.Tests.git_run(repo, "switch", "--create", "elsewhere"))

            result = u.Infra.git_publish_lane(
                request, self._produce(repo / "produced.txt")
            )

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
            (repo / "stashed.txt").write_text("stashed\n", encoding="utf-8")
            u.Tests.git_run(repo, "stash", "push", "--include-untracked")
            original_head = u.Tests.git_capture(repo, "rev-parse", "HEAD").strip()
            produced = repo / "partial.txt"
            calls: list[str] = []

            def produce() -> p.Result[bool]:
                calls.append("produce")
                return u.Cli.files_write_text(produced, "partial production\n")

            result = u.Infra.git_publish_lane(request, produce)

            tm.fail(result)
            tm.that(result.error or "", has="refuses existing stash state")
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

    def _diverge(self, repo: Path, request: p.Infra.GitLaneRequest, name: str) -> None:
        """Publish ``name`` on the lane, then advance ``name`` on the base."""
        tm.ok(
            u.Infra.git_publish_lane(request, self._produce(repo / name, "lane\n")),
            eq=True,
        )
        u.Tests.git_run(repo, "switch", request.base)
        (repo / name).write_text("base\n", encoding="utf-8")
        u.Tests.commit_git_changes(repo, "advance the base")

    @pytest.mark.parametrize(
        ("attributes", "published"),
        [("-merge linguist-generated", True), ("", False)],
    )
    def test_rerun_regenerates_only_conflicting_projections(
        self,
        tmp_path: Path,
        attributes: str,
        *,
        published: bool,
    ) -> None:
        """A projection conflict takes the base and is regenerated; others fail.

        ``.gitattributes`` declares a full projection ``-merge
        linguist-generated``: the rerun concludes the merge with the base's
        rendering and commits what the producer regenerates from it. A
        conflict on any other path keeps the merge state and fails loud.
        """
        name = "projection.md"
        with self._lane(tmp_path) as (repo, request, _):
            (repo / ".gitattributes").write_text(
                f"/{name} {attributes}\n", encoding="utf-8"
            )
            (repo / name).write_text("seed\n", encoding="utf-8")
            u.Tests.commit_git_changes(repo, "declare the projection")
            self._diverge(repo, request, name)

            result = u.Infra.git_publish_lane(
                request, self._produce(repo / name, "regenerated\n")
            )

            if published:
                tm.ok(result, eq=True)
                tm.that(
                    u.Tests.git_capture(repo, "show", f"{self.LANE}:{name}"),
                    eq="regenerated",
                )
            else:
                tm.fail(result)
                tm.that(result.error or "", has=name)
