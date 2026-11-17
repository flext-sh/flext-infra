"""Public u.Infra Git facet — GitPython-backed behavior.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from pathlib import Path

from tests import c, m, tm, u


class TestsFlextInfraGitFacet:
    """Exercise the public Git facade against a real repository worktree."""

    @staticmethod
    def test_inside_work_tree_uses_requested_directory(tmp_path: Path) -> None:
        """Control storage and its previews are outside the working tree."""
        repository = u.Tests.git_repository(tmp_path, "consumer")
        nested = repository / "nested"
        nested.mkdir()
        control = repository / ".git"
        preview = control / "source-preview"
        preview.mkdir()
        bare = tmp_path / "bare.git"
        u.Tests.git_run(repository, "init", "--bare", str(bare))
        outside = tmp_path / "outside"
        outside.mkdir()
        for path in (repository, nested, control, preview, bare):
            native = u.Tests.git_capture(
                path, "rev-parse", "--is-inside-work-tree"
            ).strip()
            report = tm.ok(
                u.Infra.git_is_inside_work_tree(m.Infra.GitRepoRequest(repo_root=path))
            )
            tm.that(report.value, eq=native == "true")
        for path in (control, preview, bare, outside, outside / "absent"):
            report = tm.ok(
                u.Infra.git_is_inside_work_tree(m.Infra.GitRepoRequest(repo_root=path))
            )
            tm.that(report.value, eq=False)
        undiscovered = tm.ok(
            u.Infra.git_is_inside_work_tree(
                m.Infra.GitRepoRequest(repo_root=nested),
                search_parent_directories=False,
            )
        )
        tm.that(undiscovered.value, eq=False)

    @staticmethod
    @c.Tests.MARK.parametrize("index_mode", ["ordinary", "v4", "split"])
    def test_retire_index_artifact_preserves_live_and_staged_siblings(
        tmp_path: Path,
        index_mode: str,
    ) -> None:
        """Native Git retains the other index entries and every working file."""
        repository = u.Tests.git_repository(tmp_path, "consumer")
        artifact = repository / "runtime.json"
        sibling = repository / "source.py"
        artifact.write_text('{"portable": true}\n', encoding=c.DEFAULT_ENCODING)
        sibling.write_text("value = 1\n", encoding=c.DEFAULT_ENCODING)
        u.Tests.git_run(repository, "add", "--", artifact.name, sibling.name)
        u.Tests.git_run(repository, "commit", "-m", "test: track fixture artifacts")
        sibling.write_text("value = 2\n", encoding=c.DEFAULT_ENCODING)
        u.Tests.git_run(repository, "add", "--", sibling.name)
        sibling.write_text("value = 3\n", encoding=c.DEFAULT_ENCODING)
        artifact.write_text('{"operator": true}\n', encoding=c.DEFAULT_ENCODING)
        if index_mode == "v4":
            u.Tests.git_run(repository, "update-index", "--index-version=4")
        elif index_mode == "split":
            u.Tests.git_run(repository, "update-index", "--split-index")
        original_artifact = artifact.read_bytes()
        original_sibling = sibling.read_bytes()
        captured_sibling = tm.ok(
            u.Infra.git_capture_index_file(
                m.Infra.GitRelativePathRequest(
                    repo_root=repository,
                    relative_path=sibling.name,
                ),
            ),
        )
        captured = tm.ok(
            u.Infra.git_capture_index_file(
                m.Infra.GitRelativePathRequest(
                    repo_root=repository,
                    relative_path=artifact.name,
                ),
            ),
        )
        entry = tm.not_none(captured.entry)
        tm.ok(
            u.Infra.git_retire_index_file(
                m.Infra.GitIndexRetirementRequest.model_validate({
                    "repo_root": (repository),
                    "entry": (entry),
                }),
            ),
        )
        observed_sibling = tm.ok(
            u.Infra.git_capture_index_file(
                m.Infra.GitRelativePathRequest(
                    repo_root=repository,
                    relative_path=sibling.name,
                ),
            ),
        )
        tm.that(observed_sibling, eq=captured_sibling)
        tm.that(artifact.read_bytes(), eq=original_artifact)
        tm.that(sibling.read_bytes(), eq=original_sibling)
        removed = tm.ok(
            u.Infra.git_is_tracked(
                m.Infra.GitRelativePathRequest(
                    repo_root=repository,
                    relative_path=artifact.name,
                ),
            ),
        )
        tm.fail(removed.value)
        native_tree = tm.ok(
            u.Cli.run((c.Infra.GIT, "write-tree"), cwd=repository),
        ).stdout.strip()
        native_artifact = tm.ok(
            u.Cli.run(
                (c.Infra.GIT, "ls-tree", native_tree, "--", artifact.name),
                cwd=repository,
            ),
        )
        tm.that(native_artifact.stdout, eq="")

    def test_retire_index_artifact_refuses_changed_preimage(
        self,
        tmp_path: Path,
    ) -> None:
        """An outside staging operation leaves new index bytes and live data intact."""
        repository = u.Tests.git_repository(tmp_path, "consumer")
        artifact = repository / "runtime.json"
        artifact.write_text('{"initial": true}\n', encoding=c.DEFAULT_ENCODING)
        u.Tests.git_run(repository, "add", "--", artifact.name)
        captured = tm.ok(
            u.Infra.git_capture_index_file(
                m.Infra.GitRelativePathRequest(
                    repo_root=repository,
                    relative_path=artifact.name,
                ),
            ),
        )
        entry = tm.not_none(captured.entry)
        artifact.write_text('{"new": true}\n', encoding=c.DEFAULT_ENCODING)
        u.Tests.git_run(repository, "add", "--", artifact.name)
        before = self._lane_bytes(repository)
        rejected = u.Infra.git_retire_index_file(
            m.Infra.GitIndexRetirementRequest.model_validate({
                "repo_root": (repository),
                "entry": (entry),
            }),
        )
        tm.fail(rejected)
        tm.that(rejected.exception, is_=ValueError)
        tm.that(self._lane_bytes(repository), eq=before)

    @staticmethod
    def _lane_repository(tmp_path: Path) -> tuple[Path, Path, str]:
        """Publish a real member whose superproject declares its integration line.

        The member keeps its own ``.git`` directory inside the superproject, so
        its index, refs and reflogs stay observable as member bytes.

        Returns:
            Member checkout, local bare remote, and the declared integration branch.

        """
        superproject = u.Tests.git_repository(tmp_path, "superproject")
        repository = u.Tests.git_repository(superproject, "member")
        branch = u.Tests.integration_branch(repository)
        remote = u.Tests.configure_local_origin(repository, tmp_path / "remote")
        u.Tests.git_run(
            superproject,
            "-c",
            "protocol.file.allow=always",
            "submodule",
            "add",
            "-b",
            branch,
            str(remote),
            repository.name,
        )
        u.Tests.git_run(superproject, "commit", "-m", "test: declare member line")
        return repository, remote, branch

    @staticmethod
    def _lane_bytes(repository: Path) -> tuple[tuple[str, bytes], ...]:
        """Observe fixture bytes, including the Git index, refs, and reflogs.

        Returns:
            Every regular fixture file's relative path and exact contents.

        """
        return tuple(
            (path.relative_to(repository).as_posix(), path.read_bytes())
            for path in sorted(repository.rglob("*"))
            if path.is_file()
        )

    @staticmethod
    def _tip(repository: Path, revision: str) -> str:
        """Resolve ``revision`` to its object id in a real fixture repository.

        Returns:
            The object id Git resolves for ``revision``.

        """
        return u.Tests.git_capture(repository, "rev-parse", revision).strip()

    @staticmethod
    def _sibling_commit(repository: Path) -> str:
        """Write one commit on top of HEAD that no ref of the checkout names.

        Returns:
            The new commit's object id.

        """
        return u.Tests.git_capture(
            repository,
            "commit-tree",
            "HEAD^{tree}",
            "-p",
            "HEAD",
            "-m",
            "test: sibling history",
        ).strip()

    def test_push_upstream_publishes_and_never_forces(self, tmp_path: Path) -> None:
        """A push publishes HEAD; a remote branch that moved rejects the next one.

        The incident ``refs/stash`` is seeded by ``update-ref`` and refuses
        nothing: the push is the native Git operation.
        """
        repository, remote, _ = self._lane_repository(tmp_path)
        u.Tests.git_run(repository, "update-ref", "refs/stash", "HEAD")
        reference = f"{c.Infra.GIT_REFS_HEADS}publication-candidate"
        request = m.Infra.GitPushRequest(
            repo_root=repository,
            branch="publication-candidate",
        )

        tm.ok(u.Infra.git_push_upstream(request))

        tm.that(self._tip(remote, reference), eq=self._tip(repository, "HEAD"))
        moved = self._sibling_commit(repository)
        u.Tests.git_run(
            repository,
            "push",
            c.Infra.GIT_DEFAULT_REMOTE,
            f"{moved}:{reference}",
        )

        tm.fail(u.Infra.git_push_upstream(request))

        tm.that(self._tip(remote, reference), eq=moved)

    def test_create_branch_creates_at_start_and_refuses_duplicates(
        self,
        tmp_path: Path,
    ) -> None:
        """A new name is created at its start point; an existing name is refused."""
        repository = u.Tests.git_repository(tmp_path)
        request = m.Infra.GitBranchCreateRequest(
            repo_root=repository,
            branch="candidate",
        )

        tm.ok(u.Infra.git_create_branch(request))

        head = self._tip(repository, "HEAD")
        tm.that(self._tip(repository, "refs/heads/candidate"), eq=head)
        moved = self._sibling_commit(repository)
        tm.fail(
            u.Infra.git_create_branch(
                m.Infra.GitBranchCreateRequest(
                    repo_root=repository,
                    branch="candidate",
                    start=moved,
                ),
            ),
        )
        tm.that(self._tip(repository, "refs/heads/candidate"), eq=head)

    @staticmethod
    def test_create_branch_switch_carries_changes_and_refuses_duplicates(
        tmp_path: Path,
    ) -> None:
        """Switching onto the new branch keeps uncommitted bytes; a repeat fails."""
        repository = u.Tests.git_repository(tmp_path)
        carried = repository / "carried.txt"
        carried.write_text("uncommitted\n", encoding="utf-8")
        request = m.Infra.GitBranchCreateRequest(
            repo_root=repository,
            branch="carrying",
            switch=True,
        )

        tm.ok(u.Infra.git_create_branch(request))

        tm.that(
            tm.ok(
                u.Infra.git_current_branch(
                    m.Infra.GitRepoRequest(repo_root=repository),
                ),
            ).text,
            eq="carrying",
        )
        tm.that(carried.read_text(encoding="utf-8"), eq="uncommitted\n")
        tm.fail(u.Infra.git_create_branch(request))

    def test_delete_ref_is_a_compare_and_swap_on_the_expected_oid(
        self,
        tmp_path: Path,
    ) -> None:
        """A ref is deleted only while it still names the expected object."""
        repository = u.Tests.git_repository(tmp_path)
        u.Tests.git_run(repository, "branch", "retired")
        reference = f"{c.Infra.GIT_REFS_HEADS}retired"
        head = self._tip(repository, reference)

        stale = u.Infra.git_delete_ref(
            m.Infra.GitDeleteRefRequest(
                repo_root=repository,
                reference=reference,
                expected_oid=self._sibling_commit(repository),
            ),
        )

        tm.fail(stale)
        tm.that(self._tip(repository, reference), eq=head)
        tm.ok(
            u.Infra.git_delete_ref(
                m.Infra.GitDeleteRefRequest(
                    repo_root=repository,
                    reference=reference,
                    expected_oid=head,
                ),
            ),
        )
        tm.that(u.Tests.git_ref_exists(repository, reference), eq=False)

    def test_delete_remote_branch_requires_and_honours_its_lease(
        self,
        tmp_path: Path,
    ) -> None:
        """No observed identity or a moved remote tip keeps the remote branch."""
        repository, _, _ = self._lane_repository(tmp_path)
        head = self._tip(repository, "HEAD")
        tm.ok(
            u.Infra.git_push_upstream(
                m.Infra.GitPushRequest(
                    repo_root=repository,
                    branch="publication-candidate",
                ),
            ),
        )
        unleased = m.Infra.GitRemoteBranchRequest(
            repo_root=repository,
            branch="publication-candidate",
        )

        tm.fail(
            u.Infra.git_delete_remote_branch(unleased),
            has="requires its observed object identity",
        )
        tm.fail(
            u.Infra.git_delete_remote_branch(
                m.Infra.GitRemoteBranchRequest(
                    repo_root=repository,
                    branch="publication-candidate",
                    expected_oid=self._sibling_commit(repository),
                ),
            ),
        )
        tm.that(tm.ok(u.Infra.git_remote_branch_oid(unleased)).text, eq=head)

        tm.ok(
            u.Infra.git_delete_remote_branch(
                m.Infra.GitRemoteBranchRequest(
                    repo_root=repository,
                    branch="publication-candidate",
                    expected_oid=head,
                ),
            ),
        )
        tm.that(tm.ok(u.Infra.git_remote_branch_oid(unleased)).text, eq="")

    @c.Tests.MARK.parametrize("origin", ["new", "local", "remote"])
    def test_add_lane_worktree_checks_out_the_lane_branch(
        self,
        tmp_path: Path,
        origin: str,
    ) -> None:
        """A lane is added for a new, an existing local, or a remote-tracked branch.

        A branch a worktree already checks out is refused by Git itself.
        """
        repository = u.Tests.git_repository(tmp_path)
        head = self._tip(repository, "HEAD")
        if origin == "local":
            u.Tests.git_run(repository, "branch", "candidate")
        elif origin == "remote":
            u.Tests.git_run(
                repository,
                "update-ref",
                f"refs/remotes/{c.Infra.GIT_DEFAULT_REMOTE}/candidate",
                "HEAD",
            )
        lane = tmp_path / "candidate-lane"
        request = m.Infra.GitWorktreeAddRequest(
            repo_root=repository,
            lane=lane,
            branch="candidate",
            base="HEAD",
            local_branch_exists=origin == "local",
            track_remote=origin == "remote",
        )

        tm.ok(u.Infra.git_add_lane_worktree(request))

        tm.that(
            tm.ok(
                u.Infra.git_current_branch(m.Infra.GitRepoRequest(repo_root=lane)),
            ).text,
            eq="candidate",
        )
        tm.that(self._tip(lane, "HEAD"), eq=head)
        second = tmp_path / "second-lane"
        tm.fail(
            u.Infra.git_add_lane_worktree(
                request.model_copy(update={"lane": second}),
            ),
        )
        tm.that(second.exists(), truth=False)

    @staticmethod
    def test_tracked_scope_preserves_literal_names_across_index_states(
        tmp_path: Path,
    ) -> None:
        repository = u.Tests.git_repository(tmp_path)
        scope = repository / "literal names"
        scope.mkdir()
        tracked = scope / ' tracked "name"\n.csv '
        raw_name = scope / os.fsdecode(b"tracked-\xff.csv")
        removed = scope / "removed.csv"
        renamed = scope / "rename -> source.csv"
        for path in (tracked, raw_name, removed, renamed):
            path.write_text("column\nvalue\n", encoding="utf-8")
        u.Tests.git_run(repository, "add", "--", scope.name)
        u.Tests.git_run(repository, "commit", "-m", "literal tracked paths")
        destination = scope / ' rename -> target\n".csv '
        u.Tests.git_run(repository, "mv", "--", str(renamed), str(destination))
        u.Tests.git_run(repository, "rm", "--cached", "--", str(removed))
        (repository / ".ignore").write_text("removed.csv\n", encoding="utf-8")
        untracked = scope / ' new\n" -> file.csv '
        untracked.write_text("column\nnew\n", encoding="utf-8")

        paths = tm.not_none(u.Infra.git_tracked_scope_paths(scope))

        # Tracked authority: index plus dirty tracked paths only. The staged
        # deletion stays (rm --cached), the ignored file stays (force-indexed),
        # and the untracked file never enters the inventory.
        tm.that(set(paths), eq={tracked, raw_name, removed, destination})
        tm.fail(untracked in paths)

    @staticmethod
    def test_tracked_scope_propagates_corrupt_index_failure(
        tmp_path: Path,
    ) -> None:
        repository = u.Tests.git_repository(tmp_path)
        (repository / c.GIT_DIR_NAME / "index").write_bytes(b"invalid index")

        with u.Tests.raises(Exception, match="index"):
            u.Infra.git_tracked_scope_paths(repository)

    @staticmethod
    def test_identity_marks_only_a_missing_symbolic_branch_as_unborn(
        tmp_path: Path,
    ) -> None:
        repository = tmp_path / "unborn"
        repository.mkdir()
        u.Tests.git_run(repository, "init", "--initial-branch=initial")
        request = m.Infra.GitRepoRequest(repo_root=repository)

        unborn = u.Infra.git_identity(request)

        tm.ok(unborn)
        branch_ref = repository / c.GIT_DIR_NAME / "refs" / "heads" / "initial"
        branch_ref.write_text("invalid object identifier\n", encoding="utf-8")

        corrupted = u.Infra.git_identity(request)

        tm.fail(corrupted)
        tm.not_none(corrupted.exception)

    @staticmethod
    def test_identity_index_failure_is_not_unborn(tmp_path: Path) -> None:
        repository = u.Tests.git_repository(tmp_path)
        (repository / c.GIT_DIR_NAME / "index").write_bytes(b"invalid index")

        result = u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=repository))

        tm.fail(result)
        tm.not_none(result.exception)

    @staticmethod
    def test_tracked_scope_refreshes_after_index_mutation(
        tmp_path: Path,
    ) -> None:
        """Only indexed files enter tracked scope, with no stale index inventory."""
        repository = u.Tests.git_repository(tmp_path)
        scope = repository / "src"
        scope.mkdir()

        tm.that(u.Infra.git_tracked_scope_paths(scope), eq=[])
        created = scope / "created.py"
        created.write_text("VALUE = 1\n", encoding="utf-8")

        tm.that(u.Infra.git_tracked_scope_paths(scope), eq=[])
        _ = u.Tests.git_run(repository, "add", "--", "src/created.py")
        tm.that(u.Infra.git_tracked_scope_paths(scope), eq=[created])
        created.unlink()
        tm.that(u.Infra.git_tracked_scope_paths(scope), eq=[])

    @staticmethod
    def test_source_scope_refreshes_after_filesystem_mutation(
        tmp_path: Path,
    ) -> None:
        """Source inventory includes unpublished files without staging them."""
        repository = u.Tests.git_repository(tmp_path)
        scope = repository / "src"
        scope.mkdir()
        tm.that(u.Infra.git_source_scope_paths(scope), eq=())

        created = scope / "created.py"
        created.write_text("VALUE = 1\n", encoding="utf-8")

        tm.that(u.Infra.git_source_scope_paths(scope), eq=(created,))
        tm.that(u.Infra.git_tracked_scope_paths(scope), eq=[])

        u.Tests.git_run(repository, "add", "--", "src/created.py")
        captured = tm.ok(u.Cli.atomic_read_binary_file_state(created, required=True))
        tm.that(u.Infra.git_tracked_scope_paths(scope), eq=[created])
        created.unlink()

        tm.fail(u.Cli.atomic_verify_binary_file_states((captured,)))
        tm.that(u.Infra.git_source_scope_paths(scope), eq=())
        tm.that(u.Infra.git_tracked_scope_paths(scope), eq=[])
        tm.that(
            u.Tests.git_capture(repository, "ls-files", "--", "src/created.py").strip(),
            eq="src/created.py",
        )

    @staticmethod
    def test_invalid_nested_git_marker_matches_native_tracked_scope(
        tmp_path: Path,
    ) -> None:
        """An empty Git marker never turns untracked files into tracked sources."""
        repository = u.Tests.git_repository(tmp_path)
        project = repository / "project"
        project.mkdir()
        (project / c.GIT_DIR_NAME).mkdir()
        source = project / "src" / "package"
        source.mkdir(parents=True)
        created = source / "module.py"
        created.write_text("VALUE = 1\n", encoding="utf-8")
        sibling = repository / "tracked.py"
        sibling.write_text("VALUE = 2\n", encoding="utf-8")
        _ = u.Tests.git_run(repository, "add", "--", sibling.name)
        native = u.Tests.git_capture(repository, "ls-files", "--", "project/src")

        tracked = u.Infra.git_tracked_scope_paths(project / "src")

        tm.that(native.strip(), eq="")
        tm.that(tracked, eq=[])

    @staticmethod
    def test_tracked_scope_does_not_borrow_an_ignoring_parent_repository(
        tmp_path: Path,
    ) -> None:
        """An explicitly selected ignored scope remains excluded by its repository."""
        repository = u.Tests.git_repository(tmp_path)
        (repository / ".ignore").write_text("scratch/\n", encoding="utf-8")
        ignored_scope = repository / "scratch" / "project"
        ignored_scope.mkdir(parents=True)
        (ignored_scope / "README.md").write_text("# Project\n", encoding="utf-8")

        tracked = u.Infra.git_tracked_scope_paths(ignored_scope)

        tm.that(tracked, eq=[])

    @staticmethod
    def test_merge_no_edit_requires_a_non_fast_forward_merge(
        tmp_path: Path,
    ) -> None:
        repository = u.Tests.git_repository(tmp_path)
        tm.ok(u.Cli.run_checked([c.Infra.GIT, "branch", "topic"], cwd=repository))
        tm.ok(u.Cli.run_checked([c.Infra.GIT, "switch", "topic"], cwd=repository))
        (repository / "topic.txt").write_text("topic\n", encoding="utf-8")
        tm.ok(u.Cli.run_checked([c.Infra.GIT, "add", "topic.txt"], cwd=repository))
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "commit", "-m", "topic"],
                cwd=repository,
            ),
        )
        topic = tm.ok(
            u.Infra.git_repository_head(m.Infra.GitRepoRequest(repo_root=repository)),
        ).oid
        tm.ok(u.Cli.run_checked([c.Infra.GIT, "switch", "main"], cwd=repository))
        tm.ok(
            u.Infra.git_merge_no_edit(
                m.Infra.GitCommitishRequest(repo_root=repository, commitish=topic),
            ),
        )
        parents = tm.ok(
            u.Cli.capture(
                [
                    c.Infra.GIT,
                    "rev-list",
                    "--parents",
                    "-n",
                    c.ParserBooleanToken.ONE,
                    "HEAD",
                ],
                cwd=repository,
            ),
        ).split()
        tm.that(parents, length=3)
