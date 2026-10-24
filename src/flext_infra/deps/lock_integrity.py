"""Committed generated TOML lock integrity verification.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import re
import tomllib
from pathlib import Path
from typing import ClassVar, override

from flext_infra import FlextInfraServiceBase, c, config, m, p, r, t, u
from flext_infra.workspace import (
    FlextInfraWorkspaceDetector,
    FlextInfraWorkspaceLockCompleteness,
)


class FlextInfraLockIntegrityVerifier(FlextInfraServiceBase[bool]):
    """Verify the committed generated TOML locks of one repository root.

    Generated locks (``mise.lock``, ``uv.lock``) are projections that must
    never be merge-resolved: a textual merge concatenates tables and re-creates
    duplicate keys that surface far from the merge as cryptic resolver errors.
    The verifier parses each committed lock with the strict stdlib reader and
    fails naming the file, the parser cause, and every duplicated section.
    """

    _TABLE_HEADER: ClassVar[re.Pattern[str]] = re.compile(
        r"(?m)^[ \t]*(?:\[([^\][]+)\]|\[\[([^\][]+)\]\])[ \t]*(?:#.*)?$",
    )

    @classmethod
    def upgrade_lock(cls, request: p.Infra.WorkspaceRequest) -> p.Result[bool]:
        """Upgrade the elected native UV lock, then every member's own lock.

        A workspace member tracks its own ``uv.lock``, which its standalone CI
        installs frozen. Native uv elects the superproject for an attached
        member, so each member is relocked in dependency waves inside a
        short-lived worktree of its own repository outside the superproject,
        and the changed lock is committed, pushed and adopted before the next
        member resolves against it.

        Returns:
            Native upgrade and freshness verification, or the first failure.

        """
        selected = FlextInfraWorkspaceDetector.resolution_context(
            request.repository_root
        )
        if selected.failure:
            return r[bool].from_failure(selected)
        context = selected.value
        locked = cls._native_uv(
            context.runtime_root,
            context.runtime_root,
            ("lock", "--upgrade", "--refresh"),
        )
        if locked.failure:
            return r[bool].from_failure(locked)
        verified = FlextInfraWorkspaceLockCompleteness.verify_lock(context.runtime_root)
        if verified.failure:
            return r[bool].from_failure(verified)
        return cls._publish_member_locks(context.runtime_root)

    @staticmethod
    def _native_uv(
        runtime_root: Path,
        project: Path,
        arguments: t.StrSequence,
    ) -> p.Result[bool]:
        """Run one native uv project command with the runtime interpreter.

        Returns:
            Success of the native command, or its original failure.

        """
        binary = u.Infra.managed_mise_binary(c.Infra.UV, runtime_root)
        if binary.failure:
            return r[bool].from_failure(binary)
        return u.Cli.run_live(
            (
                str(binary.value),
                *arguments,
                "--project",
                str(project),
                "--python",
                str(u.Infra.runtime_python(runtime_root, runtime_root=runtime_root)),
                "--no-python-downloads",
            ),
            cwd=project,
            timeout=c.Infra.TIMEOUT_LONG,
            options=m.Cli.ProcessOptions(
                env={"MISE_AUTO_INSTALL": c.ParserBooleanToken.ZERO},
                remove_env_keys=config.Infra.codegen.make.native_environment_unset,
            ),
        ).map(lambda _output: True)

    @staticmethod
    def _git(checkout: Path, *arguments: str) -> p.Result[str]:
        """Run one native Git command in a checkout and capture its stdout.

        Returns:
            The stripped stdout, or the original command failure.

        """
        return u.Cli.capture(
            (c.Infra.GIT, "-C", str(checkout), *arguments),
            timeout=c.Infra.TIMEOUT_LONG,
        )

    @staticmethod
    def member_lock_worktree(checkout: Path) -> p.Result[Path]:
        """Derive the declared short-lived lock worktree of one member checkout.

        Returns:
            ``<pytest_scratch root><absolute checkout>/<member_lock.namespace>``,
            or the failure naming the missing user home.

        """
        scratch = config.Infra.codegen.make.pytest_scratch
        variable = str(scratch.user_home_environment_variable)
        home = os.environ.get(variable, "")
        if not home.strip() or not Path(home).is_absolute():
            return r[Path].fail(f"member lock worktree requires absolute ${variable}")
        absolute = checkout.expanduser().resolve()
        return r[Path].ok(
            Path(home)
            / scratch.home_relative_directory
            / scratch.state_directory_name
            / absolute.relative_to(absolute.anchor)
            / config.Infra.codegen.make.member_lock.namespace
        )

    @classmethod
    def _materialize_member_worktree(
        cls,
        checkout: Path,
        revision: str,
    ) -> p.Result[Path]:
        """Add the member's detached lock worktree at one revision.

        Returns:
            The created worktree, or the first preflight or Git failure.

        """
        selected = cls.member_lock_worktree(checkout)
        if selected.failure:
            return selected
        worktree = selected.value
        if worktree.exists():
            return r[Path].fail(
                f"member lock worktree already exists; retire it first: {worktree}"
            )
        parent = u.Cli.ensure_dir(worktree.parent)
        if parent.failure:
            return r[Path].from_failure(parent)
        added = cls._git(
            checkout,
            "worktree",
            "add",
            "--detach",
            str(worktree),
            revision,
        )
        if added.failure:
            return r[Path].from_failure(added)
        return r[Path].ok(worktree)

    @classmethod
    def _retire_member_worktree(
        cls,
        checkout: Path,
        worktree: Path,
        outcome: p.Result[str],
    ) -> p.Result[str]:
        """Remove the worktree; a failed outcome discards its own changes.

        Returns:
            The original outcome, or the retirement failure after success.

        """
        removal = ("worktree", "remove", str(worktree))
        retired = cls._git(
            checkout, *(removal if outcome.success else (*removal, "--force"))
        )
        if retired.failure:
            if outcome.failure:
                if outcome.exception is not None:
                    outcome.exception.add_note(
                        f"worktree retirement failed: {retired.error}"
                    )
                return outcome
            return r[str].from_failure(retired)
        return outcome

    @classmethod
    def _publish_member_locks(cls, root: Path) -> p.Result[bool]:
        """Relock every governed member's own lock in dependency waves.

        Returns:
            Success after every member published, or the first failure.

        """
        loaded = FlextInfraWorkspaceDetector.load_workspace_spec(root)
        if loaded.failure:
            return r[bool].from_failure(loaded)
        workspace = loaded.value
        if workspace.repository.role is not c.Infra.MakeProfile.WORKSPACE:
            return r[bool].ok(value=True)
        members = tuple(u.Infra.mutable_flext_members(workspace))
        by_distribution = {member.distribution: member for member in members}
        for wave in u.Infra.workspace_dependency_waves(root, members):
            for distribution in wave:
                published = cls._publish_member_lock(
                    root, root / by_distribution[distribution].path
                )
                if published.failure:
                    return r[bool].from_failure(published)
        return r[bool].ok(value=True)

    @classmethod
    def _publish_member_lock(cls, root: Path, checkout: Path) -> p.Result[str]:
        """Relock one member at its fetched branch tip, publish and adopt it.

        Returns:
            The published (or unchanged) member tip, or the first failure.

        """
        branch = u.Infra.git_current_branch(m.Infra.GitRepoRequest(repo_root=checkout))
        if branch.failure:
            return r[str].from_failure(branch)
        name = branch.value.text.strip()
        tip = cls._fetch_remote_tip(checkout, name)
        if tip.failure:
            return tip
        worktree = cls._materialize_member_worktree(checkout, tip.value)
        if worktree.failure:
            return r[str].from_failure(worktree)
        published = cls._retire_member_worktree(
            checkout,
            worktree.value,
            cls._relock_member_worktree(root, checkout, worktree.value, name),
        )
        if published.failure:
            return published
        u.Cli.info(f"[member lock] {checkout.name}: {tip.value} -> {published.value}")
        if published.value == tip.value:
            return published
        return cls._adopt_member_tip(checkout, name, tip.value, published.value)

    @classmethod
    def _fetch_remote_tip(cls, checkout: Path, branch: str) -> p.Result[str]:
        """Fetch one branch into its remote-tracking ref and read its tip.

        Returns:
            The freshly fetched remote tip, or the first Git failure.

        """
        remote_ref = f"refs/remotes/{c.Infra.GIT_ORIGIN}/{branch}"
        return cls._git(
            checkout,
            "fetch",
            c.Infra.GIT_ORIGIN,
            f"refs/heads/{branch}:{remote_ref}",
        ).flat_map(
            lambda _fetched: cls._git(
                checkout, "rev-parse", "--verify", f"{remote_ref}^{{commit}}"
            )
        )

    @classmethod
    def _adopt_member_tip(
        cls,
        checkout: Path,
        branch: str,
        previous: str,
        published: str,
    ) -> p.Result[str]:
        """Bring the primary checkout to the published member tip.

        Returns:
            The published tip after a fast-forward from the previous tip, or
            after a ``--no-ff`` integration of the remote branch otherwise.

        """
        remote_ref = f"refs/remotes/{c.Infra.GIT_ORIGIN}/{branch}"
        return (
            cls
            ._git(checkout, "rev-parse", "HEAD")
            .flat_map(
                lambda head: (
                    cls._git(checkout, "merge", "--ff-only", published)
                    if head == previous
                    else cls._git(checkout, "merge", "--no-ff", "--no-edit", remote_ref)
                )
            )
            .map(lambda _merged: published)
        )

    @classmethod
    def _relock_member_worktree(
        cls,
        root: Path,
        checkout: Path,
        worktree: Path,
        branch: str,
    ) -> p.Result[str]:
        """Relock the member lock in its own worktree and publish a change.

        Returns:
            The pushed member tip proven reachable from the fresh remote ref,
            the unchanged tip when the lock did not move, or the first failure.

        """
        relocked = cls._native_uv(root, worktree, ("lock", "--upgrade", "--refresh"))
        if relocked.failure:
            return r[str].from_failure(relocked)
        lock = c.Infra.UV_LOCK_FILENAME
        if not (worktree / lock).is_file():
            return r[str].fail(f"member relock produced no own lock: {worktree}")
        changed = cls._git(worktree, "status", "--porcelain", "--", lock)
        if changed.failure or not changed.value:
            return changed.flat_map(
                lambda _clean: cls._git(worktree, "rev-parse", "HEAD")
            )
        subject = config.Infra.codegen.make.member_lock.commit_subject
        for arguments in (
            ("add", "--", lock),
            ("commit", "-m", subject, "--", lock),
            ("push", c.Infra.GIT_ORIGIN, f"HEAD:refs/heads/{branch}"),
        ):
            step = cls._git(worktree, *arguments)
            if step.failure:
                return step
        return cls._git(worktree, "rev-parse", "HEAD").flat_map(
            lambda head: cls._fetch_remote_tip(checkout, branch).flat_map(
                lambda remote_tip: cls._git(
                    checkout, "merge-base", "--is-ancestor", head, remote_tip
                ).map(lambda _proven: head)
            )
        )

    @classmethod
    def verify_own_lock(cls, request: p.Infra.WorkspaceRequest) -> p.Result[bool]:
        """Check the selected checkout's own committed lock with native uv.

        A standalone checkout or workspace root checks its runtime lock in
        place. An attached member checks its committed lock (``HEAD``) inside
        its declared short-lived worktree, where native uv elects the member.

        Returns:
            Success when the checkout's own lock matches its manifest.

        """
        election = FlextInfraWorkspaceDetector.runtime_election(request.repository_root)
        if election.failure:
            return r[bool].from_failure(election)
        context = election.value
        if context.project_root == context.runtime_root:
            return FlextInfraWorkspaceLockCompleteness.verify_lock(
                context.runtime_root
            ).map(lambda _checked: True)
        worktree = cls._materialize_member_worktree(context.project_root, "HEAD")
        if worktree.failure:
            return r[bool].from_failure(worktree)
        checked = cls._retire_member_worktree(
            context.project_root,
            worktree.value,
            cls._native_uv(
                context.runtime_root, worktree.value, ("lock", "--check")
            ).map(lambda _checked: str(worktree.value)),
        )
        return checked.map(lambda _checked: True)

    @classmethod
    def _duplicated_sections(cls, text: str) -> t.StrSequence:
        """Enumerate table headers declared more than once in a corrupt lock.

        Returns:
            The resulting ``t.StrSequence``.

        """
        counts: t.MutableMappingKV[str, int] = {}
        for match in cls._TABLE_HEADER.finditer(text):
            key = (match.group(1) or match.group(2) or "").strip()
            counts[key] = counts.get(key, 0) + 1
        return tuple(sorted(key for key, count in counts.items() if count > 1))

    @classmethod
    def _verify_lock(cls, lock_path: Path) -> t.StrSequence:
        """Verify one committed lock, returning zero or more failure causes.

        Returns:
            The resulting ``t.StrSequence``.

        """
        if not lock_path.is_file():
            return (f"{lock_path.name}: missing committed generated lock",)
        text = lock_path.read_text(encoding="utf-8")
        try:
            tomllib.loads(text)
        except tomllib.TOMLDecodeError as error:
            duplicated = cls._duplicated_sections(text)
            sections = (
                f"; duplicated sections: {', '.join(duplicated)}" if duplicated else ""
            )
            return (f"{lock_path.name}: {error}{sections}",)
        return ()

    @override
    def execute(self) -> p.Result[bool]:
        """Verify every committed generated TOML lock at the repository root.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        selected = FlextInfraWorkspaceDetector.resolution_context(self.repository_root)
        if selected.failure:
            return r[bool].from_failure(selected)
        failures: t.StrSequence = tuple(
            failure
            for lock_path in (
                selected.value.runtime_root / c.Infra.MISE_LOCK_FILENAME,
                selected.value.lock_path,
            )
            for failure in self._verify_lock(lock_path)
        )
        if failures:
            return r[bool].fail("; ".join(failures))
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraLockIntegrityVerifier"]
