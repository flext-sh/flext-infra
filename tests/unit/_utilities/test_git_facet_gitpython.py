"""Public u.Infra Git facet — GitPython-backed behavior.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from flext_infra import FlextInfraGitService, FlextInfraWorktreeService, c, m, main, t
from tests import tm, u


class TestsFlextInfraGitFacet:
    """Exercise the public Git facade against a real repository worktree."""

    @pytest.mark.parametrize("index_mode", ["ordinary", "v4", "split"])
    def test_retire_index_artifact_preserves_live_and_staged_siblings(
        self,
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
        tm.that(captured.entry, none=False)
        tm.ok(
            u.Infra.git_retire_index_file(
                m.Infra.GitIndexRetirementRequest(
                    repo_root=repository,
                    entry=captured.entry,
                ),
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
        tm.that(captured.entry, none=False)
        artifact.write_text('{"new": true}\n', encoding=c.DEFAULT_ENCODING)
        u.Tests.git_run(repository, "add", "--", artifact.name)
        before = self._lane_bytes(repository)
        rejected = u.Infra.git_retire_index_file(
            m.Infra.GitIndexRetirementRequest(
                repo_root=repository,
                entry=captured.entry,
            ),
        )
        tm.fail(rejected)
        tm.that(rejected.exception, is_=ValueError)
        tm.that(self._lane_bytes(repository), eq=before)

    @staticmethod
    def _lane_repository(tmp_path: Path) -> t.Triple[Path, Path, str]:
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
    def _lane_bytes(repository: Path) -> t.VariadicTuple[t.Pair[str, bytes]]:
        """Observe fixture bytes, including the Git index, refs, and reflogs.

        Returns:
            Every regular fixture file's relative path and exact contents.

        """
        return tuple(
            (path.relative_to(repository).as_posix(), path.read_bytes())
            for path in sorted(repository.rglob("*"))
            if path.is_file()
        )

    def test_verify_lane_cli_has_no_preview_effects(self, tmp_path: Path) -> None:
        """A live-tip proof changes neither working bytes nor Git metadata."""
        repository, _, _ = self._lane_repository(tmp_path)
        before = self._lane_bytes(repository)
        tm.that(
            main(["workspace", "verify-lane", "--repo-root", str(repository)]),
            eq=0,
        )
        tm.that(self._lane_bytes(repository), eq=before)

    @pytest.mark.parametrize("operation", ["verify", "create", "retire"])
    def test_verify_lane_refuses_legacy_stash_ref_without_effects(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        operation: str,
    ) -> None:
        """Seed an incident ref, never call any stash creation or apply command."""
        repository, _, _ = self._lane_repository(tmp_path)
        u.Tests.git_run(repository, "update-ref", "refs/stash", "HEAD")
        before = self._lane_bytes(repository)
        tm.that(
            main([
                "workspace",
                "verify-lane",
                "--repo-root",
                str(repository),
                "--operation",
                operation,
            ]),
            eq=1,
        )
        output = capsys.readouterr()
        tm.that(output.out + output.err, has="existing stash state")
        tm.that(self._lane_bytes(repository), eq=before)

    @pytest.mark.parametrize("boundary", ["stale", "unabsorbed", "moved"])
    def test_verify_lane_refuses_remote_drift_without_effects(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        boundary: str,
    ) -> None:
        """A changed live remote is not made current by a cached ancestry proof."""
        repository, remote, branch = self._lane_repository(tmp_path)
        tip = tm.ok(
            FlextInfraGitService.verify_lane(
                m.Infra.GitLaneVerificationRequest(repo_root=repository),
            ),
        ).oid
        advanced = u.Tests.git_capture(
            repository,
            "commit-tree",
            "HEAD^{tree}",
            "-p",
            "HEAD",
            "-m",
            "test: advance remote",
        ).strip()
        u.Tests.git_run(remote, "fetch", str(repository), advanced)
        u.Tests.git_run(remote, "update-ref", f"refs/heads/{branch}", advanced)
        if boundary != "stale":
            u.Tests.git_run(repository, "fetch", c.Infra.GIT_DEFAULT_REMOTE)
        before = self._lane_bytes(repository)
        remote_before = self._lane_bytes(remote)
        argv = ["workspace", "verify-lane", "--repo-root", str(repository)]
        if boundary == "moved":
            argv.extend(("--expected-tip", tip))
        tm.that(main(argv), eq=1)
        output = capsys.readouterr()
        diagnostic = {
            "stale": "stale integration cache",
            "unabsorbed": "has not absorbed",
            "moved": "tip changed before effect",
        }[boundary]
        tm.that(output.out + output.err, has=diagnostic)
        tm.fail(
            u.Infra.git_push_upstream(
                m.Infra.GitPushRequest(
                    repo_root=repository,
                    branch="publication-candidate",
                ),
            ),
            has=(
                "stale integration cache" if boundary == "stale" else "has not absorbed"
            ),
        )
        tm.that(self._lane_bytes(repository), eq=before)
        tm.that(self._lane_bytes(remote), eq=remote_before)

    def test_new_lane_requires_authoritative_ownership_without_touching_foreign_refs(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Foreign refs do not block verification or authorize a second own lane."""
        repository, _, _ = self._lane_repository(tmp_path)
        u.Tests.git_run(repository, "branch", "foreign-candidate")
        tm.that(
            main(["workspace", "verify-lane", "--repo-root", str(repository)]),
            eq=0,
        )
        _ = capsys.readouterr()
        before = self._lane_bytes(repository)
        tm.that(
            main([
                "workspace",
                "verify-lane",
                "--repo-root",
                str(repository),
                "--operation",
                "create",
            ]),
            eq=1,
        )
        output = capsys.readouterr()
        tm.that(output.out + output.err, has="authoritative Beads ownership")
        tm.fail(
            u.Infra.git_create_branch(
                m.Infra.GitBranchCreateRequest(
                    repo_root=repository,
                    branch="second-candidate",
                ),
            ),
            has="authoritative Beads ownership",
        )
        lane = tmp_path / "never-created"
        tm.fail(
            u.Infra.git_add_lane_worktree(
                m.Infra.GitWorktreeAddRequest(
                    repo_root=repository,
                    lane=lane,
                    branch="second-candidate",
                    base="HEAD",
                ),
            ),
            has="authoritative Beads ownership",
        )
        tm.fail(
            FlextInfraWorktreeService(
                repository_root=repository,
                operation=c.Infra.WorktreeOperation.ADD,
                branch="second-candidate",
                base="HEAD",
                apply_changes=True,
            ).execute(),
            has="authoritative Beads ownership",
        )
        tm.fail(lane.exists())
        tm.that(self._lane_bytes(repository), eq=before)

    @pytest.mark.parametrize("integrated", [False, True])
    def test_retirement_refuses_clean_unmerged_or_unpreserved_candidate(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        *,
        integrated: bool,
    ) -> None:
        """A clean tree and even contained HEAD do not authorize retirement."""
        repository, _, _ = self._lane_repository(tmp_path)
        lane = u.Tests.git_linked_lane(tmp_path, repository, "retirement-candidate")
        if not integrated:
            u.Tests.git_run(
                lane,
                "commit",
                "--allow-empty",
                "-m",
                "test: pending integration",
            )
        before = self._lane_bytes(repository)
        lane_before = self._lane_bytes(lane)
        tm.that(
            main([
                "workspace",
                "verify-lane",
                "--repo-root",
                str(lane),
                "--operation",
                "retire",
            ]),
            eq=1,
        )
        output = capsys.readouterr()
        diagnostic = (
            "published preservation" if integrated else "unintegrated candidate"
        )
        tm.that(output.out + output.err, has=diagnostic)
        tm.fail(u.Infra.git_remove_clean_worktree(repository, lane), has=diagnostic)
        candidate = tm.ok(
            u.Infra.git_repository_head(
                m.Infra.GitRepoRequest(repo_root=lane),
            ),
        ).oid
        tm.fail(
            u.Infra.git_delete_ref(
                m.Infra.GitDeleteRefRequest(
                    repo_root=lane,
                    reference=f"{c.Infra.GIT_REFS_HEADS}retirement-candidate",
                    expected_oid=candidate,
                ),
            ),
            has=diagnostic,
        )
        tm.fail(
            u.Infra.git_delete_remote_branch(
                m.Infra.GitRemoteBranchRequest(
                    repo_root=lane,
                    branch="retirement-candidate",
                    expected_oid=candidate,
                ),
            ),
            has=diagnostic,
        )
        tm.that(self._lane_bytes(repository), eq=before)
        tm.that(self._lane_bytes(lane), eq=lane_before)

    @pytest.mark.parametrize("change", ["tracked", "staged", "untracked"])
    def test_retirement_cli_preserves_every_dirty_layer(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        change: str,
    ) -> None:
        """Dirty refusal cannot refresh or overwrite the index or working bytes."""
        repository, _, _ = self._lane_repository(tmp_path)
        changed = repository / (
            "untracked.txt" if change == "untracked" else "README.md"
        )
        changed.write_text("retained WIP\n", encoding="utf-8")
        if change == "staged":
            u.Tests.git_run(repository, "add", "--", changed.name)
        before = self._lane_bytes(repository)
        tm.that(
            main([
                "workspace",
                "verify-lane",
                "--repo-root",
                str(repository),
                "--operation",
                "retire",
            ]),
            eq=1,
        )
        output = capsys.readouterr()
        tm.that(output.out + output.err, has="dirty worktree")
        tm.that(self._lane_bytes(repository), eq=before)

    def test_verify_lane_missing_declaration_is_not_a_guessed_branch(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A standalone remote that declares no default branch is refused.

        A standalone checkout declares its integration line through its forge
        default branch (the remote ``HEAD``); an empty remote declares none,
        and admission refuses visibly without guessing a branch or effects.
        """
        repository = u.Tests.git_repository(tmp_path)
        empty_remote = tmp_path / "empty-remote.git"
        u.Tests.git_run(tmp_path, "init", "--bare", str(empty_remote))
        u.Tests.git_run(repository, "remote", "set-url", "origin", str(empty_remote))
        before = self._lane_bytes(repository)
        tm.that(
            main(["workspace", "verify-lane", "--repo-root", str(repository)]),
            eq=1,
        )
        output = capsys.readouterr()
        tm.that(output.out + output.err, has="declares no default branch")
        tm.that(self._lane_bytes(repository), eq=before)

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
        (repository / ".gitignore").write_text("removed.csv\n", encoding="utf-8")
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
        (repository / ".git" / "index").write_bytes(b"invalid index")

        with pytest.raises(Exception, match="index"):
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

        tm.fail(unborn)
        tm.that(unborn.error_code, eq=c.Infra.GIT_UNBORN_HEAD_ERROR_CODE)
        branch_ref = repository / ".git" / "refs" / "heads" / "initial"
        branch_ref.write_text("invalid object identifier\n", encoding="utf-8")

        corrupted = u.Infra.git_identity(request)

        tm.fail(corrupted)
        tm.fail(corrupted.error_code == c.Infra.GIT_UNBORN_HEAD_ERROR_CODE)
        tm.not_none(corrupted.exception)

    @staticmethod
    def test_identity_index_failure_is_not_unborn(tmp_path: Path) -> None:
        repository = u.Tests.git_repository(tmp_path)
        (repository / ".git" / "index").write_bytes(b"invalid index")

        result = u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=repository))

        tm.fail(result)
        tm.fail(result.error_code == c.Infra.GIT_UNBORN_HEAD_ERROR_CODE)
        tm.not_none(result.exception)

    @staticmethod
    def _add_submodule(repository: Path, source: Path, name: str) -> None:
        """Add and commit ``source`` as a file-protocol submodule named ``name``."""
        _ = u.Tests.git_run(
            repository,
            "-c",
            "protocol.file.allow=always",
            "submodule",
            "add",
            str(source),
            name,
        )
        _ = u.Tests.git_run(repository, "commit", "-am", name)

    @staticmethod
    def _update_submodules(lane: Path) -> None:
        """Initialize every declared submodule inside the lane checkout."""
        _ = u.Tests.git_run(
            lane,
            "-c",
            "protocol.file.allow=always",
            "submodule",
            "update",
            "--init",
            "--recursive",
        )

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
        (project / ".git").mkdir()
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
        (repository / ".gitignore").write_text("scratch/\n", encoding="utf-8")
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
                [c.Infra.GIT, "rev-list", "--parents", "-n", "1", "HEAD"],
                cwd=repository,
            ),
        ).split()
        tm.that(parents, length=3)

    @staticmethod
    def test_repository_head_and_status_and_service(real_git_repo: Path) -> None:
        """Head, porcelain status, and FlextInfraGitService share one typed path."""
        head = u.Infra.git_repository_head(
            m.Infra.GitRepoRequest(repo_root=real_git_repo),
        )
        tm.that(head.success, truth=True)
        tm.that(head.value.oid, length=c.Infra.GIT_OID_HEX_LENGTH_SHA1)
        status = u.Infra.git_status(m.Infra.GitStatusRequest(repo_root=real_git_repo))
        tm.that(status.success, truth=True)
        tm.that(isinstance(status.value.porcelain, str), truth=True)
        assert status.value.dirty is False
        primary = u.Infra.git_primary_worktree_root(
            m.Infra.GitRepoRequest(repo_root=real_git_repo),
        )
        tm.that(primary.success, truth=True)
        tm.that(primary.value.primary_root == real_git_repo.resolve(), truth=True)
        report = FlextInfraGitService(repository_root=real_git_repo).execute()
        tm.that(report.success, truth=True)
        tm.that(isinstance(report.value, m.Infra.GitStatusReport), truth=True)
        tm.that(report.value.repo_root == real_git_repo.resolve(), truth=True)
        assert report.value.dirty is False

    @staticmethod
    def test_git_init_bare_on_non_repo_cwd(tmp_path: Path) -> None:
        """cwd-bound execute must allow git init --bare outside a worktree."""
        bare_root = tmp_path / "bare"
        bare_root.mkdir()
        init_result = u.Cli.run_checked([c.Infra.GIT, "init", "--bare"], cwd=bare_root)
        tm.that(init_result.success, truth=True)
        tm.that((bare_root / "HEAD").is_file(), truth=True)
        captured = u.Cli.capture([c.Infra.GIT, "rev-parse", "--git-dir"], cwd=bare_root)
        tm.that(captured.success, truth=True)
        tm.that(captured.value.strip() in {".", str(bare_root.resolve())}, truth=True)

    @staticmethod
    def test_service_status_reports_dirty_tree(real_git_repo: Path) -> None:
        """The status-only service flips dirty when the worktree changes."""
        clean = tm.ok(FlextInfraGitService(repository_root=real_git_repo).execute())
        tm.that(clean.dirty, eq=False)
        (real_git_repo / "dirty.txt").write_text("x", encoding="utf-8")
        dirty = tm.ok(FlextInfraGitService(repository_root=real_git_repo).execute())
        tm.that(dirty.dirty, eq=True)
        tm.that(dirty.porcelain, has="dirty.txt")

    @staticmethod
    @pytest.mark.parametrize("change", ["tracked", "staged", "untracked"])
    def test_verify_clean_cli_accepts_real_worktree_changes(
        real_git_repo: Path,
        capsys: pytest.CaptureFixture[str],
        change: str,
    ) -> None:
        """The public CLI passes a clean checkout and exposes a dirty Git report."""
        argv = ["workspace", "verify-clean", "--repo-root", str(real_git_repo)]
        tm.that(main(argv), eq=0)
        _ = capsys.readouterr()

        if change == "untracked":
            changed_path = real_git_repo / "dirty.txt"
            changed_path.write_text("dirty\n", encoding="utf-8")
        else:
            changed_path = real_git_repo / "README.md"
            changed_path.write_text("# Changed Repository\n", encoding="utf-8")
            if change == "staged":
                tm.ok(
                    u.Cli.run_checked(
                        [c.Infra.GIT, "add", changed_path.name],
                        cwd=real_git_repo,
                    ),
                )

        request = m.Infra.GitStatusRequest(repo_root=real_git_repo)
        before = tm.ok(u.Infra.git_status(request))
        report = tm.ok(FlextInfraGitService.verify_clean(request))
        tm.that(report.dirty, eq=True)
        tm.that(report.porcelain, eq=before.porcelain)
        tm.that(main(argv), eq=0)
        output = capsys.readouterr()
        tm.that(output.out + output.err, has="existing work preserved")
        tm.that(tm.ok(u.Infra.git_status(request)).porcelain, eq=before.porcelain)

    @staticmethod
    @pytest.mark.parametrize("entries", [1, 2])
    @pytest.mark.parametrize("linked", [False, True])
    def test_verify_clean_preserves_recovery_stash_objects_without_mutation(
        real_git_repo: Path,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        entries: int,
        *,
        linked: bool,
    ) -> None:
        """Real recovery refs remain intact after accepted service and CLI calls."""
        repository = (
            u.Tests.git_linked_lane(tmp_path, real_git_repo, "owned-lane")
            if linked
            else real_git_repo
        )
        request = m.Infra.GitStatusRequest(repo_root=repository)
        tm.ok(FlextInfraGitService.verify_clean(request))
        head = u.Tests.git_capture(real_git_repo, "rev-parse", c.Infra.GIT_HEAD)
        tree = u.Tests.git_capture(real_git_repo, "rev-parse", f"{head}^{{tree}}")
        index_parent = u.Tests.git_capture(
            real_git_repo,
            "commit-tree",
            tree,
            "-p",
            head,
            "-m",
            "recovery index",
        )
        oids: list[str] = []
        for entry in range(entries):
            oid = u.Tests.git_capture(
                real_git_repo,
                "commit-tree",
                tree,
                "-p",
                head,
                "-p",
                index_parent,
                "-m",
                f"recovery worktree {entry}",
            )
            u.Tests.git_run(
                real_git_repo,
                "update-ref",
                "--create-reflog",
                "refs/stash",
                oid,
            )
            oids.append(oid)
        tm.that(
            tm.ok(FlextInfraGitService(repository_root=repository).execute()).dirty,
            eq=False,
        )

        result = FlextInfraGitService.verify_clean(request)

        tm.that(tm.ok(result).dirty, eq=False)
        tm.that(
            main(["workspace", "verify-clean", "--repo-root", str(repository)]),
            eq=0,
        )
        output = capsys.readouterr()
        tm.that(output.out + output.err, has="existing work preserved")
        remaining = tm.ok(
            u.Infra.git_stash_oids(m.Infra.GitRepoRequest(repo_root=repository)),
        ).oids
        tm.that(tuple(remaining), eq=tuple(reversed(oids)))
        tm.that(
            u.Tests.git_capture(real_git_repo, "rev-parse", c.Infra.GIT_HEAD),
            eq=head,
        )
        tm.fail(tm.ok(u.Infra.git_status(request)).dirty)

    @staticmethod
    def test_verify_clean_propagates_status_probe_failure(
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """An unusable Git root retains the original technical status failure."""
        request = m.Infra.GitStatusRequest(repo_root=tmp_path)
        probe = u.Infra.git_status(request)
        tm.fail(probe)

        result = FlextInfraGitService.verify_clean(request)

        tm.fail(result)
        tm.that(result.error, eq=probe.error)
        tm.that(result.error_code, eq=probe.error_code)
        tm.that(result.error_data, eq=probe.error_data)
        tm.not_none(result.exception)
        tm.that(type(result.exception), eq=type(probe.exception))
        tm.that(
            main(["workspace", "verify-clean", "--repo-root", str(tmp_path)]),
            eq=1,
        )
        output = capsys.readouterr()
        tm.that(output.out + output.err, has=tm.not_none(probe.error))

    @staticmethod
    def test_git_changed_paths_reports_tracked_and_untracked_files(
        real_git_repo: Path,
    ) -> None:
        """The public Git facade returns the complete existing worktree delta."""
        readme = real_git_repo / "README.md"
        readme.write_text("changed\n", encoding="utf-8")
        created = real_git_repo / "created.py"
        created.write_text("VALUE = 1\n", encoding="utf-8")

        changed = tm.ok(
            u.Infra.git_changed_paths(m.Infra.GitRepoRequest(repo_root=real_git_repo)),
        )

        tm.that(set(changed), eq={readme.resolve(), created.resolve()})

    @staticmethod
    def test_status_classifies_registered_nested_worktrees_as_administrative(
        tmp_path: Path,
    ) -> None:
        repository = u.Tests.git_repository(tmp_path)
        container = repository / ".worktrees"
        first = container / "first"
        second = container / "second"
        container.mkdir()
        tm.ok(u.Cli.run_checked([c.Infra.GIT, "branch", "first"], cwd=repository))
        tm.ok(u.Cli.run_checked([c.Infra.GIT, "branch", "second"], cwd=repository))
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "worktree", "add", str(first), "first"],
                cwd=repository,
            ),
        )
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "worktree", "add", str(second), "second"],
                cwd=repository,
            ),
        )
        clean = tm.ok(
            u.Infra.git_status(m.Infra.GitStatusRequest(repo_root=repository)),
        )
        assert clean.dirty is False
        (repository / "rogue.txt").write_text("rogue", encoding="utf-8")
        rogue = tm.ok(
            u.Infra.git_status(m.Infra.GitStatusRequest(repo_root=repository)),
        )
        assert rogue.dirty is True
        (repository / "rogue.txt").unlink()
        (container / "rogue.txt").write_text("rogue", encoding="utf-8")
        nested_rogue = tm.ok(
            u.Infra.git_status(m.Infra.GitStatusRequest(repo_root=repository)),
        )
        assert nested_rogue.dirty is True
        (container / "rogue.txt").unlink()
        (repository / "README.md").write_text("changed", encoding="utf-8")
        tracked = tm.ok(
            u.Infra.git_status(m.Infra.GitStatusRequest(repo_root=repository)),
        )
        assert tracked.dirty is True
        (repository / "README.md").write_text("# Test Repository\n", encoding="utf-8")
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "worktree", "remove", str(second)],
                cwd=repository,
            ),
        )
        second.mkdir(parents=True)
        (second / "stale.txt").write_text("stale", encoding="utf-8")
        stale = tm.ok(
            u.Infra.git_status(m.Infra.GitStatusRequest(repo_root=repository)),
        )
        assert stale.dirty is True

    @staticmethod
    def test_missing_git_binary_fails_closed(tmp_path: Path) -> None:
        """Missing git on PATH must Result.fail without raising."""
        empty_path = tmp_path / "empty-path"
        empty_path.mkdir()
        with tm.scope(env={"PATH": str(empty_path)}):
            result = u.Infra.git_status(m.Infra.GitStatusRequest(repo_root=tmp_path))
        tm.that(result.failure, truth=True)
        tm.that(result.error, none=False)
        tm.that("git executable not found" in result.error, truth=True)

    @staticmethod
    def test_refresh_binary_reports_the_resolved_executable() -> None:
        """The public facet refreshes the Git binary it will then use."""
        refreshed = u.Infra.refresh_binary()
        tm.ok(refreshed)
        tm.ok(refreshed.value)

    def test_remove_clean_worktree_refuses_missing_lifecycle_proof(
        self,
        tmp_path: Path,
    ) -> None:
        repository = u.Tests.git_repository(tmp_path)
        source = u.Tests.git_repository(tmp_path, "member-source")
        self._add_submodule(repository, source, "member")
        lane = u.Tests.git_linked_lane(tmp_path, repository, "fixture-lane")
        self._update_submodules(lane)
        gitmodules = (repository / ".gitmodules").read_text(encoding="utf-8")
        gitlink = tm.ok(
            u.Cli.capture(
                (c.Infra.GIT, "ls-files", "--stage", "member"),
                cwd=repository,
            ),
        )
        configured = tm.ok(
            u.Cli.capture(
                (c.Infra.GIT, "config", "--get", "submodule.member.url"),
                cwd=repository,
            ),
        )

        u.Tests.git_run(repository, "fetch", "--quiet", "origin")

        tm.fail(
            u.Infra.git_remove_clean_worktree(repository, lane),
            has="retirement refused",
        )

        tm.that(lane.is_dir(), truth=True)
        tm.that((repository / "member").is_dir(), truth=True)
        tm.that(
            (repository / ".gitmodules").read_text(encoding="utf-8") == gitmodules,
            truth=True,
        )
        tm.that(
            tm.ok(
                u.Cli.capture(
                    (c.Infra.GIT, "ls-files", "--stage", "member"), cwd=repository
                )
            ),
            eq=gitlink,
        )
        tm.that(
            tm.ok(
                u.Cli.capture(
                    (c.Infra.GIT, "config", "--get", "submodule.member.url"),
                    cwd=repository,
                )
            ),
            eq=configured,
        )

    def test_remove_clean_worktree_refuses_dirty_nested_submodule(
        self,
        tmp_path: Path,
    ) -> None:
        repository = u.Tests.git_repository(tmp_path)
        nested_source = u.Tests.git_repository(tmp_path, "nested-source")
        member_source = u.Tests.git_repository(tmp_path, "member-source")
        self._add_submodule(member_source, nested_source, "nested")
        self._add_submodule(repository, member_source, "member")
        lane = u.Tests.git_linked_lane(tmp_path, repository, "dirty-lane")
        self._update_submodules(lane)
        (lane / "member" / "nested" / "dirty.txt").write_text(
            "dirty\n",
            encoding="utf-8",
        )

        result = u.Infra.git_remove_clean_worktree(repository, lane)

        tm.fail(result, has="dirty nested submodule")
        tm.that(lane.is_dir(), truth=True)

    @staticmethod
    def test_remove_clean_worktree_refuses_locked_worktree(
        tmp_path: Path,
    ) -> None:
        repository = u.Tests.git_repository(tmp_path)
        lane = u.Tests.git_linked_lane(tmp_path, repository, "locked-lane")
        _ = u.Tests.git_run(repository, "worktree", "lock", str(lane))

        result = u.Infra.git_remove_clean_worktree(repository, lane)

        tm.fail(result, has="locked worktree")
        tm.that(lane.is_dir(), truth=True)

    @staticmethod
    def test_is_ancestor_proves_any_pair_and_defaults_to_head(
        tmp_path: Path,
    ) -> None:
        """One owner proves ancestry for a pair and for the HEAD-bound case."""
        repository = u.Tests.git_repository(tmp_path)
        base = tm.ok(
            u.Infra.git_repository_head(m.Infra.GitRepoRequest(repo_root=repository)),
        ).oid
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "switch", "-c", "topic"],
                cwd=repository,
            ),
        )
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

        ancestor = tm.ok(
            u.Infra.git_is_ancestor(
                m.Infra.GitAncestryRequest(
                    repo_root=repository,
                    ancestor=base,
                    descendant=topic,
                ),
            ),
        )
        reverse = tm.ok(
            u.Infra.git_is_ancestor(
                m.Infra.GitAncestryRequest(
                    repo_root=repository,
                    ancestor=topic,
                    descendant=base,
                ),
            ),
        )
        defaulted = tm.ok(
            u.Infra.git_is_ancestor(
                m.Infra.GitAncestryRequest(repo_root=repository, ancestor=base),
            ),
        )

        tm.ok(ancestor.value)
        tm.fail(reverse.value)
        tm.ok(defaulted.value)

    @staticmethod
    def test_is_ancestor_fails_on_unknown_commitish(tmp_path: Path) -> None:
        """An unresolvable side is a failure, never a silent negative."""
        repository = u.Tests.git_repository(tmp_path)

        result = u.Infra.git_is_ancestor(
            m.Infra.GitAncestryRequest(
                repo_root=repository,
                ancestor="deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
            ),
        )

        tm.that(result.failure, truth=True)
        tm.that(result.error, none=False)

    @staticmethod
    def test_has_staged_changes_tracks_the_index(tmp_path: Path) -> None:
        """The staged probe distinguishes a staged delta from a clean index."""
        repository = u.Tests.git_repository(tmp_path)
        request = m.Infra.GitRepoRequest(repo_root=repository)

        tm.fail(tm.ok(u.Infra.git_has_staged_changes(request)).value)

        (repository / "staged.txt").write_text("staged\n", encoding="utf-8")
        tm.fail(tm.ok(u.Infra.git_has_staged_changes(request)).value)

        tm.ok(
            u.Cli.run_checked([c.Infra.GIT, "add", "staged.txt"], cwd=repository),
        )
        tm.ok(tm.ok(u.Infra.git_has_staged_changes(request)).value)

        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "commit", "-m", "staged"],
                cwd=repository,
            ),
        )
        tm.fail(tm.ok(u.Infra.git_has_staged_changes(request)).value)
