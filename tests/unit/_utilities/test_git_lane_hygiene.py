"""Native lane facts and the one public evaluator against real local Git.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from flext_infra import FlextInfraCli, FlextInfraGitService, config, m, workspace
from tests import c, tm, u


class TestsFlextInfraGitLaneHygiene:
    """Preserve incoming census intents under the canonical fresh-base contract."""

    @staticmethod
    def _declared_base(tmp_path: Path) -> m.Infra.GitLaneVerificationRequest:
        """Create a real remote whose integration is available and demonstrably live.

        Returns:
            The typed request with a fixture-owned integration declaration.

        """
        repository = u.Tests.git_repository(tmp_path)
        integration = u.Tests.integration_branch(repository)
        u.Tests.git_run(repository, "branch", "-m", integration)
        remote = tmp_path / "integration.git"
        u.Tests.git_bootstrap(tmp_path, ("init", "--bare", str(remote)))
        policy = config.Infra.codegen.branch_policy
        action = "set-url" if policy.lane_remote == c.Infra.GIT_ORIGIN else "add"
        u.Tests.git_run(repository, "remote", action, policy.lane_remote, str(remote))
        u.Tests.git_run(repository, "push", "-u", policy.lane_remote, integration)
        return m.Infra.GitLaneVerificationRequest(
            repo_root=repository,
            declared=integration,
        )

    @classmethod
    def test_clean_repository_passes(
        cls,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Only the declared integration remains; dormant sources are not probed."""
        request = cls._declared_base(tmp_path)
        facts = tm.ok(u.Infra.git_lane_facts(request))
        tm.that(facts.stash_oids, eq=())
        tm.that(facts.read_errors, eq=())
        report = tm.ok(FlextInfraGitService.verify_lanes(request))
        tm.that(report.violations, eq=())
        tm.that(report.findings, eq=())
        tm.that(report.integration_branch, eq=request.declared)
        tm.that(
            FlextInfraCli.infra_main([
                "workspace",
                "verify-lanes",
                "--repo-root",
                str(request.repo_root),
                "--declared",
                str(request.declared),
            ]),
            eq=0,
        )
        _ = capsys.readouterr()

    @classmethod
    def test_missing_integration_base_fails_loud(cls, tmp_path: Path) -> None:
        """An explicit missing authority cannot silently choose a healthy branch."""
        request = cls._declared_base(tmp_path)
        missing = request.model_copy(update={"declared": "fixture/missing-authority"})
        result = FlextInfraGitService.verify_lanes(missing)
        tm.fail(result)
        tm.that(str(result.error), has="integration branch is absent remotely")

    @classmethod
    def test_every_violation_class_is_listed(
        cls,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Stashes, all merged refs, orphans and clean linked lanes surface."""
        request = cls._declared_base(tmp_path / "primary")
        repository = request.repo_root
        (repository / "README.md").write_text("# Lane\n", encoding="utf-8")
        u.Tests.commit_git_changes(repository, "seed tracked file")
        policy = config.Infra.codegen.branch_policy
        u.Tests.git_run(repository, "push", policy.lane_remote)
        head = u.Tests.git_capture(repository, "rev-parse", "HEAD")
        u.Tests.git_run(
            repository,
            "update-ref",
            "--create-reflog",
            "-m",
            "recovery fixture",
            "refs/stash",
            head,
        )
        u.Tests.git_run(repository, "branch", "merged-lane")
        merged = u.Tests.git_linked_lane(
            tmp_path / "lanes", repository, "merged-worktree"
        )
        gone = u.Tests.git_linked_lane(tmp_path / "lanes", repository, "gone-worktree")
        gone.rename(tmp_path / "preserved-worktree")
        facts = tm.ok(u.Infra.git_lane_facts(request))
        tm.that(facts.stash_oids, eq=(head,))
        result = FlextInfraGitService.verify_lanes(request)
        tm.fail(result)
        report = m.Infra.GitLaneReport.model_validate_json(tm.not_none(result.error))
        kind = c.Infra.LaneViolationKind
        expected = {
            (kind.STASH, head),
            (kind.MERGED_BRANCH, "refs/heads/merged-lane"),
            (kind.MERGED_BRANCH, "refs/heads/merged-worktree"),
            (kind.MERGED_BRANCH, "refs/heads/gone-worktree"),
            (kind.MERGED_WORKTREE, str(merged)),
            (kind.MISSING_WORKTREE, str(gone)),
        }
        if any(merged.is_relative_to(root) for root in policy.lane_temporary_roots):
            expected.add((kind.TEMP_WORKTREE, str(merged)))
        tm.that({(entry.kind, entry.ref) for entry in report.violations}, eq=expected)
        tm.that(
            FlextInfraCli.infra_main([
                "workspace",
                "verify-lanes",
                "--repo-root",
                str(repository),
                "--declared",
                str(request.declared),
            ]),
            eq=1,
        )
        output = capsys.readouterr()
        for ref in (head, "refs/heads/merged-lane", str(merged), str(gone)):
            tm.that(output.out + output.err, has=ref)

    @classmethod
    def _retained_ownership(
        cls,
        tmp_path: Path,
        *,
        paths: tuple[Path, ...] = (Path(),),
        publish: bool = True,
        integrate: bool = True,
        large: bool = False,
    ) -> m.Infra.GitLaneOwnershipRequest:
        """Retain actual native layers through the existing checkpoint owners.

        Returns:
            The reference selected by the public read-only receipt producer.

        """
        base = cls._declared_base(tmp_path)
        root = base.repo_root
        remote = config.Infra.codegen.branch_policy.lane_remote
        if large:
            names = tuple(f"retained-{index}-{'x' * 160}" for index in range(512))
            for name in names:
                (root / name).write_text("retained source\n", encoding="utf-8")
            u.Tests.git_run(root, "add", "--", *names)
            u.Tests.git_run(root, "commit", "-m", "chore: retain source inputs")
            u.Tests.git_run(root, "push", remote, str(base.declared))
        u.Tests.git_run(
            tmp_path / "integration.git",
            "symbolic-ref",
            "HEAD",
            f"refs/heads/{base.declared}",
        )
        checkpoint = tm.ok(
            u.Infra.git_checkpoint_worktree_state(
                tm.ok(
                    u.Infra.git_snapshot_worktree_state(
                        m.Infra.GitWorktreeStateRequest(repo_root=root, paths=paths),
                    )
                ),
                "refs/checkpoints/owned-state",
            )
        )
        if publish:
            tm.ok(u.Infra.git_publish_worktree_checkpoint(checkpoint, remote))
        if integrate:
            u.Tests.git_run(
                root,
                "merge",
                "--no-ff",
                "-m",
                "integrate retained ownership",
                checkpoint.worktree_commit,
            )
            u.Tests.git_run(root, "push", remote, str(base.declared))
        return m.Infra.GitLaneOwnershipRequest(
            repo_root=root,
            remote=remote,
            checkpoint_ref=checkpoint.checkpoint_ref,
            expected_tip=u.Tests.git_capture(root, "rev-parse", "HEAD").strip(),
        )

    @classmethod
    def test_receipt_producer_preserves_shared_layers(
        cls,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Authenticated historical ownership does not require clean current work."""
        request = cls._retained_ownership(tmp_path)
        root = request.repo_root
        u.Tests.git_run(root, "switch", "-c", "active-candidate")
        (root / "README.md").write_text("staged ownership\n", encoding="utf-8")
        u.Tests.git_run(root, "add", "README.md")
        (root / "README.md").write_text("unstaged ownership\n", encoding="utf-8")
        (root / "untracked.txt").write_text("independent work\n", encoding="utf-8")
        index = (root / c.GIT_DIR_NAME / "index").read_bytes()
        before = tm.ok(
            u.Infra.git_snapshot_worktree_state(
                m.Infra.GitWorktreeStateRequest(repo_root=root, paths=(Path(),)),
            )
        )
        receipt = tm.ok(FlextInfraGitService.lane_ownership(request))
        tm.that(receipt.checkpoint.checkpoint_ref, eq=request.checkpoint_ref)
        tm.that(receipt.publication.remote_name, eq=request.remote)
        _ = capsys.readouterr()
        tm.that(
            FlextInfraCli.infra_main([
                "workspace",
                "lane-ownership",
                "--repo-root",
                str(root),
                "--remote",
                request.remote,
                "--checkpoint-ref",
                request.checkpoint_ref,
                "--expected-tip",
                str(request.expected_tip),
            ]),
            eq=0,
        )
        encoded = capsys.readouterr().out
        tm.that(
            m.Infra.GitLaneOwnershipReceipt.model_validate_json(encoded), eq=receipt
        )
        tm.that((root / c.GIT_DIR_NAME / "index").read_bytes(), eq=index)
        tm.that(
            tm.ok(
                u.Infra.git_snapshot_worktree_state(
                    m.Infra.GitWorktreeStateRequest(repo_root=root, paths=(Path(),)),
                )
            ),
            eq=before,
        )

    @classmethod
    @pytest.mark.parametrize("missing", ["publication", "integration", "scope"])
    def test_receipt_requires_actual_prior_proof(
        cls, tmp_path: Path, missing: str
    ) -> None:
        """Local retention, remote publication, and whole-repository scope differ."""
        request = cls._retained_ownership(
            tmp_path,
            paths=(Path("README.md"),) if missing == "scope" else (Path(),),
            publish=missing != "publication",
            integrate=missing != "integration",
        )
        tm.fail(FlextInfraGitService.lane_ownership(request))

    @classmethod
    @pytest.mark.parametrize("forged", ["tip", "reference", "metadata"])
    def test_receipt_rejects_forged_native_identity(
        cls, tmp_path: Path, forged: str
    ) -> None:
        """Wrong live tips, branch aliases, and altered checkpoint objects fail."""
        request = cls._retained_ownership(tmp_path)
        if forged == "metadata":
            u.Tests.git_run(
                request.repo_root,
                "update-ref",
                request.checkpoint_ref,
                "HEAD",
            )
        result = FlextInfraGitService.lane_ownership(
            m.Infra.GitLaneOwnershipRequest(
                repo_root=request.repo_root,
                remote=request.remote,
                checkpoint_ref=(
                    f"refs/heads/{u.Tests.integration_branch(request.repo_root)}"
                    if forged == "reference"
                    else request.checkpoint_ref
                ),
                expected_tip=(
                    u.Tests.git_capture(request.repo_root, "rev-parse", "HEAD^").strip()
                    if forged == "tip"
                    else request.expected_tip
                ),
            )
        )
        tm.fail(result)

    @classmethod
    @pytest.mark.parametrize("selection", ["native", "missing", "shell-data"])
    def test_version_recipe_consumes_only_native_receipt(
        cls, tmp_path: Path, selection: str
    ) -> None:
        """The generated recipe transports real proof and treats selectors as data."""
        request = cls._retained_ownership(tmp_path, large=selection == "native")
        root = request.repo_root
        if selection == "native":
            receipt = tm.ok(FlextInfraGitService.lane_ownership(request))
            tm.that(len(receipt.model_dump_json().encode()) > 128 * 1024, eq=True)
        pyproject = u.Tests.WorktreeFixture.write_python_project(root, root.name)
        u.Tests.git_run(root, "add", "--", str(pyproject.relative_to(root)))
        u.Tests.git_run(root, "commit", "-m", "chore: establish release baseline")
        version = tm.ok(u.Infra.current_workspace_version(root))
        u.Tests.git_run(root, "tag", f"v{version}")
        u.Tests.git_run(root, "push", request.remote, "HEAD")
        rendered_root = u.Tests.git_repository(tmp_path / "rendered")
        u.Tests.WorktreeFixture.write_python_project(rendered_root, rendered_root.name)
        u.Tests.write_standalone_workspace_manifest(rendered_root, rendered_root.name)
        u.Tests.git_run(
            rendered_root,
            "remote",
            "add",
            request.remote,
            u.Tests.WorktreeFixture.governed_repository_url(rendered_root.name),
        )
        rendered = u.Tests.conform_makefile_text(
            rendered_root,
            tm.ok(
                workspace.FlextInfraWorkspaceDetector.load_workspace_spec(rendered_root)
            ),
        )
        body = rendered.split("_builtin_release_version:", 1)[1].split("\n\n", 1)[0]
        recipe = "\n".join(
            line.removeprefix("\t").removeprefix("@") for line in body.splitlines()[1:]
        )
        command = (
            recipe
            .replace("$$", "$")
            .replace("$(PROJECT_FLEXT_INFRA)", f'"{sys.executable}" -m flext_infra')
            .replace("$(PROJECT_ROOT)", str(root))
        )
        reference = (
            request.checkpoint_ref
            if selection == "native"
            else ""
            if selection == "missing"
            else "refs/checkpoints/owned-state; touch injected"
        )
        before = u.Tests.git_capture(root, "rev-parse", "HEAD").strip()
        with u.Tests.env_vars_context({"FLEXT_LANE_CHECKPOINT_REF": reference}):
            output = tm.ok(u.Cli.run_raw(["bash", "-eu", "-c", command], cwd=root))
        tm.that(
            u.Cli.process_succeeded(output.outcome),
            eq=selection != "shell-data",
            msg=output.stdout + output.stderr,
        )
        tm.that(u.Tests.git_capture(root, "rev-parse", "HEAD").strip(), eq=before)
        tm.that((root / "injected").exists(), eq=False)
