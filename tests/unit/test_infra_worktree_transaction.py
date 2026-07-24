"""Real Git behavior tests for isolated workspace transactions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra.services.cli_transaction import CliTransactionService
from tests import m, u

if TYPE_CHECKING:
    from pathlib import Path


def _git_status(repository_root: Path) -> bytes:
    result = u.Infra.git_capture_bytes(
        repository_root, ("status", "--porcelain=v1", "-z")
    )
    tm.ok(result)
    return result.value


def _operation_delta(tmp_path: Path) -> tuple[Path, Path, m.Infra.RepositoryDelta]:
    source_root = tmp_path / "source"
    source_root.mkdir()
    artifact = source_root / "artifact.txt"
    artifact.write_bytes(b"before\n")
    u.Tests.initialize_git_repo(source_root)
    worktree_root = tmp_path / "isolated"
    add_result = u.Infra.git_add_detached_worktree(source_root, worktree_root)
    tm.ok(add_result)
    (worktree_root / artifact.name).write_bytes(b"after\n")
    delta_result = u.Infra.git_repository_delta(
        m.Infra.RepositoryWorktree(
            relative_path=".",
            source_root=source_root,
            worktree_root=worktree_root,
            checkpoint_sha=add_result.value,
        )
    )
    tm.ok(delta_result)
    return source_root, worktree_root, delta_result.value


def _workspace(tmp_path: Path) -> Path:
    workspace_root = tmp_path / "workspace"
    package_root = workspace_root / "src" / "transaction_fixture"
    package_root.mkdir(parents=True)
    (package_root / "__init__.py").write_text("", encoding="utf-8")
    (workspace_root / "pyproject.toml").write_text(
        ("[project]\nname = 'transaction-fixture'\nversion = '0.1.0'\n"),
        encoding="utf-8",
    )
    (workspace_root / ".taplo.toml").write_text("", encoding="utf-8")
    config_root = workspace_root / "config"
    config_root.mkdir()
    (config_root / "workspace.yaml").write_text(
        (
            "version: 2\n"
            "name: transaction-fixture\n"
            "repository:\n"
            "  name: transaction-fixture\n"
            "  distribution: transaction-fixture\n"
            "  provider: flext-sh\n"
            "  url: https://github.com/flext-sh/transaction-fixture.git\n"
            "  branch: main\n"
            "  path: .\n"
            "  role: workspace-root\n"
            "  state: active\n"
            "  profile: workspace-root\n"
            "  checkout: root\n"
            "  codegen: conform\n"
            "  package: false\n"
            "  editable: false\n"
            "  read_only: false\n"
            "members: []\n"
            "content_only: []\n"
            "exclusions: []\n"
        ),
        encoding="utf-8",
    )
    u.Tests.initialize_git_repo(workspace_root)
    return workspace_root


class TestsFlextInfraWorktreeTransaction:
    """Exercise transaction invariants through real Git state."""

    def test_preview_validates_isolated_target_without_touching_source(
        self, tmp_path: Path
    ) -> None:
        """Reverse-check the isolated final state and preserve source bytes/status."""
        source_root, _worktree_root, delta = _operation_delta(tmp_path)
        artifact = source_root / "artifact.txt"
        before_bytes = artifact.read_bytes()
        before_status = _git_status(source_root)

        tm.ok(u.Infra.git_check_isolated_patch(delta))

        tm.that(artifact.read_bytes(), eq=before_bytes)
        tm.that(_git_status(source_root), eq=before_status)

    def test_apply_accepts_concurrent_same_target_convergence(
        self, tmp_path: Path
    ) -> None:
        """Treat an identical cooperative source update as successful convergence."""
        source_root, _worktree_root, delta = _operation_delta(tmp_path)
        artifact = source_root / "artifact.txt"
        artifact.write_bytes(b"after\n")
        converged_status = _git_status(source_root)

        tm.ok(u.Infra.git_apply_patch(delta))

        tm.that(artifact.read_bytes(), eq=b"after\n")
        tm.that(_git_status(source_root), eq=converged_status)

    def test_apply_is_repeatable(self, tmp_path: Path) -> None:
        """Apply the same real patch twice without a second mutation or failure."""
        source_root, _worktree_root, delta = _operation_delta(tmp_path)
        artifact = source_root / "artifact.txt"
        tm.ok(u.Infra.git_apply_patch(delta))
        applied_status = _git_status(source_root)

        tm.ok(u.Infra.git_apply_patch(delta))

        tm.that(artifact.read_bytes(), eq=b"after\n")
        tm.that(_git_status(source_root), eq=applied_status)

    def test_apply_replaces_existing_ignored_canonical_addition(
        self, tmp_path: Path
    ) -> None:
        """Converge an ignored projection that the patch canonically adds."""
        source_root = tmp_path / "source"
        source_root.mkdir()
        (source_root / ".gitignore").write_text(".vscode/\n", encoding="utf-8")
        u.Tests.initialize_git_repo(source_root)
        ignored = source_root / ".vscode" / "settings.json"
        ignored.parent.mkdir()
        ignored.write_text('{"strict": false}\n', encoding="utf-8")
        worktree_root = tmp_path / "isolated"
        checkpoint = tm.ok(
            u.Infra.git_add_detached_worktree(source_root, worktree_root)
        )
        generated = worktree_root / ".vscode" / "settings.json"
        generated.parent.mkdir()
        generated.write_text('{"strict": true}\n', encoding="utf-8")
        delta = tm.ok(
            u.Infra.git_repository_delta(
                m.Infra.RepositoryWorktree(
                    relative_path=".",
                    source_root=source_root,
                    worktree_root=worktree_root,
                    checkpoint_sha=checkpoint,
                )
            )
        )

        tm.ok(u.Infra.git_apply_patch(delta))

        tm.that(ignored.read_text(encoding="utf-8"), eq='{"strict": true}\n')

    def test_failed_collision_apply_restores_ignored_projection(
        self, tmp_path: Path
    ) -> None:
        """Preserve ignored source bytes when another patch hunk conflicts."""
        source_root = tmp_path / "source"
        source_root.mkdir()
        tracked = source_root / "tracked.txt"
        tracked.write_text("before\n", encoding="utf-8")
        (source_root / ".gitignore").write_text(".vscode/\n", encoding="utf-8")
        u.Tests.initialize_git_repo(source_root)
        ignored = source_root / ".vscode" / "settings.json"
        ignored.parent.mkdir()
        ignored.write_text('{"strict": false}\n', encoding="utf-8")
        worktree_root = tmp_path / "isolated"
        checkpoint = tm.ok(
            u.Infra.git_add_detached_worktree(source_root, worktree_root)
        )
        (worktree_root / "tracked.txt").write_text("after\n", encoding="utf-8")
        generated = worktree_root / ".vscode" / "settings.json"
        generated.parent.mkdir()
        generated.write_text('{"strict": true}\n', encoding="utf-8")
        delta = tm.ok(
            u.Infra.git_repository_delta(
                m.Infra.RepositoryWorktree(
                    relative_path=".",
                    source_root=source_root,
                    worktree_root=worktree_root,
                    checkpoint_sha=checkpoint,
                )
            )
        )
        tracked.write_text("concurrent\n", encoding="utf-8")

        tm.fail(u.Infra.git_apply_patch(delta), has="patch failed")

        tm.that(ignored.read_text(encoding="utf-8"), eq='{"strict": false}\n')
        tm.that(tracked.read_text(encoding="utf-8"), eq="concurrent\n")

    def test_public_dry_run_materializes_inner_patch_without_source_mutation(
        self, tmp_path: Path
    ) -> None:
        """Keep request.apply_patch false while the isolated command runs apply."""
        workspace_root = _workspace(tmp_path)
        before_status = _git_status(workspace_root)
        before_pyproject = (workspace_root / "pyproject.toml").read_bytes()

        transaction_result = u.Infra.execute_worktree_transaction(
            m.Infra.WorktreeTransactionRequest(
                workspace_root=workspace_root,
                command=(
                    "workspace",
                    "sync",
                    "--workspace",
                    str(workspace_root),
                    "--apply",
                ),
                apply_patch=False,
                allow_lint_regression=True,
                timeout_seconds=120,
            )
        )
        report = tm.ok(transaction_result)
        output = u.Infra.render_worktree_transaction_report(report)
        lint_output = "\n".join(item.output for item in report.lint_after)

        tm.that(report.breakage_detected, eq=False, msg=lint_output)
        tm.that(output, has="diff -- repository .")
        tm.that(output, has="applied=no")
        tm.that((workspace_root / "pyproject.toml").read_bytes(), eq=before_pyproject)
        tm.that(_git_status(workspace_root), eq=before_status)
        tm.that((workspace_root / "Makefile").exists(), eq=False)


class TestsFlextInfraWorktreeTransactionLintRegression:
    """Contract for the explicit lint-regression allowance."""

    def test_lint_regressed_detects_diagnostic_increase(self) -> None:
        """Flag diagnostic growth as regression; stable diagnostics are safe."""
        before = (m.Infra.LintSnapshot(tool="ruff", exit_code=0, errors=10),)
        after = (m.Infra.LintSnapshot(tool="ruff", exit_code=0, errors=11),)

        regressed = u.Infra._lint_regressed(  # ruff:ignore[private-member-access]
            before, after
        )
        stable = u.Infra._lint_regressed(  # ruff:ignore[private-member-access]
            before, before
        )

        tm.that(regressed, eq=True)
        tm.that(stable, eq=False)

    def test_request_defaults_to_rejecting_lint_regression(
        self, tmp_path: Path
    ) -> None:
        """Default transactions keep rejecting lint regressions."""
        request = m.Infra.WorktreeTransactionRequest(
            workspace_root=tmp_path, command=("deps", "modernize"), timeout_seconds=60
        )

        tm.that(request.allow_lint_regression, eq=False)

    def test_inner_args_strip_allow_lint_regression_flag(self) -> None:
        """Strip the outer allowance flag before the isolated invocation."""
        args = (
            "modernize",
            "--apply",
            "--allow-lint-regression",
            "--projects",
            "flext-infra",
        )

        normalized = CliTransactionService.transaction_inner_args(
            "deps:modernize", args
        )

        tm.that("--allow-lint-regression" in normalized, eq=False)
        tm.that("--apply" in normalized, eq=True)
        tm.that("--projects" in normalized, eq=True)
