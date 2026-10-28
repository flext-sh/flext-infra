"""Public u.Infra Git facet — GitPython-backed behavior.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import os
from pathlib import Path

import pytest

from flext_infra import (
    FlextInfraCli,
    FlextInfraGitService,
    FlextInfraWorktreeService,
    m,
)
from tests import c, tm, u


class TestsFlextInfraGitFacet:
    """Exercise the public Git facade against a real repository worktree."""

    @staticmethod
    @pytest.mark.parametrize("index_mode", ["ordinary", "v4", "split"])
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
                m.Infra.GitIndexRetirementRequest(
                    repo_root=repository,
                    entry=entry,
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
        entry = tm.not_none(captured.entry)
        artifact.write_text('{"new": true}\n', encoding=c.DEFAULT_ENCODING)
        u.Tests.git_run(repository, "add", "--", artifact.name)
        before = self._lane_bytes(repository)
        rejected = u.Infra.git_retire_index_file(
            m.Infra.GitIndexRetirementRequest(
                repo_root=repository,
                entry=entry,
            ),
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

    def test_verify_lane_cli_has_no_preview_effects(self, tmp_path: Path) -> None:
        """A live-tip proof changes neither working bytes nor Git metadata."""
        repository, _, _ = self._lane_repository(tmp_path)
        before = self._lane_bytes(repository)
        tm.that(
            FlextInfraCli.infra_main([
                "workspace",
                "verify-lane",
                "--repo-root",
                str(repository),
            ]),
            eq=0,
        )
        tm.that(self._lane_bytes(repository), eq=before)

    @pytest.mark.parametrize(c.ContextScope.OPERATION, ["verify", "create", "retire"])
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
            FlextInfraCli.infra_main([
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
        tm.that(FlextInfraCli.infra_main(argv), eq=1)
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
            FlextInfraCli.infra_main([
                "workspace",
                "verify-lane",
                "--repo-root",
                str(repository),
            ]),
            eq=0,
        )
        _ = capsys.readouterr()
        before = self._lane_bytes(repository)
        tm.that(
            FlextInfraCli.infra_main([
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
            FlextInfraCli.infra_main([
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
            FlextInfraCli.infra_main([
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
            FlextInfraCli.infra_main([
                "workspace",
                "verify-lane",
                "--repo-root",
                str(repository),
            ]),
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
        (repository / c.GIT_DIR_NAME / "index").write_bytes(b"invalid index")

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
        branch_ref = repository / c.GIT_DIR_NAME / "refs" / "heads" / "initial"
        branch_ref.write_text("invalid object identifier\n", encoding="utf-8")

        corrupted = u.Infra.git_identity(request)

        tm.fail(corrupted)
        tm.fail(corrupted.error_code == c.Infra.GIT_UNBORN_HEAD_ERROR_CODE)
        tm.not_none(corrupted.exception)

    @staticmethod
    def test_identity_index_failure_is_not_unborn(tmp_path: Path) -> None:
        repository = u.Tests.git_repository(tmp_path)
        (repository / c.GIT_DIR_NAME / "index").write_bytes(b"invalid index")

        result = u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=repository))

        tm.fail(result)
        tm.fail(result.error_code == c.Infra.GIT_UNBORN_HEAD_ERROR_CODE)
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
