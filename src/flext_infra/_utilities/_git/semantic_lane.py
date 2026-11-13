"""Canonical publication lane for ``u.Infra``: produced paths to one pull request.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import u

from flext_infra import c, m, r
from flext_infra._utilities._git import (
    FlextInfraUtilitiesGitSemanticPaths,
    FlextInfraUtilitiesGitSemanticPublish,
    FlextInfraUtilitiesGitSemanticRefs,
    FlextInfraUtilitiesGitWorktreeStatus,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from flext_infra import p


class FlextInfraUtilitiesGitSemanticLane:
    """Own the lane every repository publication shares (release, propagation)."""

    @classmethod
    def _verified_lane_base(cls, request: p.Infra.GitLaneRequest) -> p.Result[Path]:
        """Require a clean checkout on the lane base and return the repo root.

        Returns:
            The resulting ``p.Result[Path]``.

        """
        root = request.repo_root
        status = FlextInfraUtilitiesGitWorktreeStatus.git_status(
            m.Infra.GitStatusRequest(repo_root=root)
        )
        if status.failure:
            return r[Path].from_failure(status)
        if status.value.dirty:
            return r[Path].fail(
                f"lane {request.branch} requires a clean checkout: {root}\n"
                f"{status.value.porcelain}",
            )
        current = FlextInfraUtilitiesGitSemanticRefs.git_current_branch(
            m.Infra.GitRepoRequest(repo_root=root)
        )
        if current.failure:
            return r[Path].from_failure(current)
        if current.value.text != request.base:
            return r[Path].fail(
                f"lane {request.branch} starts from {request.base}, "
                f"not {current.value.text}",
            )
        return r[Path].ok(root)

    @classmethod
    def _git_produce_lane(
        cls,
        request: p.Infra.GitLaneRequest,
        produce: Callable[[], p.Result[bool]],
    ) -> p.Result[bool]:
        """Enter the lane, produce, and commit; restore base when a step fails.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for step in (
            lambda: cls._git_enter_lane(request),
            produce,
            lambda: cls._git_commit_produced(request),
        ):
            outcome = step()
            if outcome.failure:
                # Preserve partial output and the original failure for recovery.
                return outcome
        return r[bool].ok(value=True)

    @classmethod
    def git_publish_lane(
        cls,
        request: p.Infra.GitLaneRequest,
        produce: Callable[[], p.Result[bool]],
    ) -> p.Result[bool]:
        """Carry what ``produce`` writes from ``base`` to a pull request on ``branch``.

        The lane is the protocol's own deterministic ``branch``: admission is
        the read-only ``verify`` preflight (no stash, live integration tip,
        base ancestry) plus a clean checkout on ``base``. It never requests
        agent-lane ``create`` admission, whose Beads-ownership proof a clean
        CI checkout cannot carry.

        The checkout must be clean on ``base``, so every path the status lists
        after ``produce`` was produced by it; exactly those paths are committed
        under ``subject``, the lane is pushed, and its pull request is opened or
        updated. A rerun continues the open lane (local or remote), merges
        ``base`` in, reproduces identical bytes and commits nothing. A lane
        that carries nothing beyond ``base`` publishes nothing: the checkout
        returns to ``base``, the empty lane branch is removed, and the result
        is ``False``.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        root = request.repo_root
        admitted = FlextInfraUtilitiesGitSemanticRefs.git_verify_lane(
            m.Infra.GitLaneVerificationRequest.model_validate({
                "repo_root": (root),
                "operation": ("verify"),
                "candidate": (request.base),
            }),
        )
        if admitted.failure:
            return r[bool].from_failure(admitted)
        base = cls._verified_lane_base(request)
        if base.failure:
            return r[bool].from_failure(base)
        produced = cls._git_produce_lane(request, produce)
        if produced.failure:
            return produced
        ahead = u.Cli.capture(
            [c.Infra.GIT, "rev-list", "--count", f"{request.base}..{request.branch}"],
            cwd=root,
        )
        if ahead.failure:
            return r[bool].from_failure(ahead)
        return (
            cls._git_discard_empty_lane(request)
            if ahead.value.strip() == c.ParserBooleanToken.ZERO
            else cls._git_open_pull_request(request)
        )

    @classmethod
    def _git_discard_empty_lane(cls, request: p.Infra.GitLaneRequest) -> p.Result[bool]:
        """Return to ``base`` and remove the lane branch that carries nothing.

        Returns:
            To ``base`` and remove the lane branch that carries nothing.

        """
        root = request.repo_root
        for command in (
            [c.Infra.GIT, "switch", request.base],
            [c.Infra.GIT, "branch", "--delete", request.branch],
        ):
            outcome = u.Cli.run_checked(command, cwd=root)
            if outcome.failure:
                return outcome
        return r[bool].ok(value=False)

    @classmethod
    def _git_enter_lane(cls, request: p.Infra.GitLaneRequest) -> p.Result[bool]:
        """Continue the lane where it exists (local then remote), else start at HEAD.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        root, branch = request.repo_root, request.branch
        local = u.Cli.capture(
            [c.Infra.GIT, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"],
            cwd=root,
        )
        fetched = u.Cli.run_checked(
            [c.Infra.GIT, "fetch", c.Infra.GIT_ORIGIN, branch],
            cwd=root,
        )
        if local.success:
            switched = u.Cli.run_checked([c.Infra.GIT, "switch", branch], cwd=root)
        elif fetched.success:
            switched = u.Cli.run_checked(
                [
                    c.Infra.GIT,
                    "switch",
                    "--create",
                    branch,
                    f"refs/remotes/{c.Infra.GIT_ORIGIN}/{branch}",
                ],
                cwd=root,
            )
        else:
            return u.Cli.run_checked(
                [c.Infra.GIT, "switch", "--create", branch],
                cwd=root,
            )
        if switched.failure:
            return switched
        merged = FlextInfraUtilitiesGitSemanticPublish.git_merge_no_edit(
            m.Infra.GitCommitishRequest(repo_root=root, commitish=request.base),
        )
        if merged.success:
            return r[bool].ok(value=True)
        return cls._git_take_base_projections(request, merged.error or "")

    @classmethod
    def _git_take_base_projections(
        cls,
        request: p.Infra.GitLaneRequest,
        merge_error: str,
    ) -> p.Result[bool]:
        """Conclude a merge whose only conflicts are full generated projections.

        ``.gitattributes`` marks a full projection ``-merge linguist-generated``:
        Git never combines it textually, so the lane's earlier rendering and
        the base's always conflict. The merge takes the base's rendering and
        the producing step regenerates it from the merged sources. Any other
        conflict keeps the merge state and fails with the original error.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        root = request.repo_root
        listed = u.Cli.capture(
            [c.Infra.GIT, "diff", "--name-only", "--diff-filter=U", "-z"],
            cwd=root,
        )
        if listed.failure:
            return r[bool].from_failure(listed)
        conflicted = tuple(path for path in listed.value.split("\0") if path)
        if not conflicted:
            return r[bool].fail(merge_error)
        attributes = u.Cli.capture(
            [
                c.Infra.GIT,
                "check-attr",
                "-z",
                *c.Infra.GIT_PROJECTION_ATTRIBUTES,
                "--",
                *conflicted,
            ],
            cwd=root,
        )
        if attributes.failure:
            return r[bool].from_failure(attributes)
        fields = attributes.value.split("\0")
        declared = set(zip(fields[::3], fields[1::3], fields[2::3], strict=False))
        regenerated = {
            path
            for path in conflicted
            if all(
                (path, name, value) in declared
                for name, value in c.Infra.GIT_PROJECTION_ATTRIBUTES.items()
            )
        }
        foreign = sorted(set(conflicted) - regenerated)
        if foreign:
            return r[bool].fail(
                f"{merge_error}\nconflicts outside generated projections: "
                + ", ".join(foreign),
            )
        for command in (
            [c.Infra.GIT, "checkout", "--theirs", "--", *conflicted],
            [c.Infra.GIT, "add", "--", *conflicted],
            [c.Infra.GIT, "commit", "--no-edit"],
        ):
            outcome = u.Cli.run_checked(command, cwd=root)
            if outcome.failure:
                return outcome
        return r[bool].ok(value=True)

    @classmethod
    def _git_commit_produced(cls, request: p.Infra.GitLaneRequest) -> p.Result[bool]:
        """Commit exactly the paths the status lists; nothing produced commits nothing.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        root = request.repo_root
        status = FlextInfraUtilitiesGitWorktreeStatus.git_status(
            m.Infra.GitStatusRequest(repo_root=root)
        )
        if status.failure:
            return r[bool].from_failure(status)
        # The status code and the path are whitespace-separated; the first
        # line arrives without its leading status padding.
        produced = tuple(
            line.split(maxsplit=1)[1]
            for line in status.value.porcelain.splitlines()
            if line.strip()
        )
        if not produced:
            return r[bool].ok(value=True)
        staged = FlextInfraUtilitiesGitSemanticPaths.git_add_paths(
            m.Infra.GitPathsRequest(repo_root=root, paths=produced),
        )
        if staged.failure:
            return r[bool].from_failure(staged)
        return FlextInfraUtilitiesGitSemanticPaths.git_commit(
            m.Infra.GitCommitRequest(repo_root=root, message=request.subject),
        ).map(lambda _report: True)

    @classmethod
    def _git_open_pull_request(cls, request: p.Infra.GitLaneRequest) -> p.Result[bool]:
        """Push the lane, then refresh its open pull request or open a new one.

        The pull request is resolved by head, base and ``open`` state: once the
        previous one merged, the lane opens a new one. Several open pull
        requests on one lane, or a body beyond GitHub's ceiling, fail loud.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        root, branch = request.repo_root, request.branch
        body = u.Cli.files_read_text(request.body_file)
        if body.failure:
            return r[bool].from_failure(body)
        if len(body.value) > c.Infra.GH_PULL_REQUEST_BODY_MAX_CHARS:
            return r[bool].fail(
                f"pull request body {request.body_file} has {len(body.value)} "
                f"characters; GitHub accepts {c.Infra.GH_PULL_REQUEST_BODY_MAX_CHARS}",
            )
        pushed = FlextInfraUtilitiesGitSemanticPublish.git_push_upstream(
            m.Infra.GitPushRequest(repo_root=root, branch=branch),
        )
        if pushed.failure:
            return r[bool].from_failure(pushed)
        # Only an open pull request is the lane's: a merged or closed one on
        # the same head (the previous release) is history and never edited.
        listed = u.Cli.capture(
            [
                c.Infra.GH,
                "pr",
                "list",
                "--head",
                branch,
                "--base",
                request.base,
                "--state",
                "open",
                "--json",
                "number",
                "--jq",
                ".[].number",
            ],
            cwd=root,
        )
        if listed.failure:
            return r[bool].from_failure(listed)
        numbers = listed.value.split()
        if len(numbers) > 1:
            return r[bool].fail(
                f"lane {branch} has several open pull requests: {', '.join(numbers)}",
            )
        command = (
            [c.Infra.GH, "pr", "edit", numbers[0]]
            if numbers
            else [c.Infra.GH, "pr", "create", "--base", request.base, "--head", branch]
        )
        return u.Cli.run_checked(
            [
                *command,
                "--title",
                request.subject,
                "--body-file",
                str(request.body_file),
            ],
            cwd=root,
        )


__all__: list[str] = ["FlextInfraUtilitiesGitSemanticLane"]
