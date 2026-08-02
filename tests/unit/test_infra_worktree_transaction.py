"""Real Git behavior tests for isolated workspace transactions."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

import pytest

from flext_core import r
from flext_infra import c, config, p, t
from flext_tests import tm
from tests import m, u


def _git_status(repository_root: Path) -> bytes:
    result = u.Infra.git_capture_bytes(
        repository_root, ("status", "--porcelain=v1", "-z")
    )
    status: bytes = tm.ok(result)
    return status


def _operation_delta(tmp_path: Path) -> tuple[Path, Path, m.Infra.RepositoryDelta]:
    source_root = tmp_path / "source"
    source_root.mkdir(parents=True)
    transaction_lock = config.Infra.codegen.make.serialization.lock_path
    (source_root / ".gitignore").write_text(
        f"{transaction_lock.parts[0]}/\n", encoding="utf-8"
    )
    artifact = source_root / "artifact.txt"
    artifact.write_bytes(b"before\n")
    u.Tests.initialize_git_repo(source_root)
    worktree_root = tmp_path / "isolated"
    tm.ok(u.Infra.git_add_detached_worktree(source_root, worktree_root))
    checkpoint: str = tm.ok(
        u.Infra.git_checkpoint_worktree(
            worktree_root, message="test isolated transaction checkpoint"
        )
    )
    (worktree_root / artifact.name).write_bytes(b"after\n")
    delta: m.Infra.RepositoryDelta = tm.ok(
        u.Infra.git_repository_delta(
            m.Infra.RepositoryWorktree(
                relative_path=".",
                source_root=source_root,
                worktree_root=worktree_root,
                checkpoint_sha=checkpoint,
            )
        )
    )
    return source_root, worktree_root, delta


def _workspace(tmp_path: Path) -> Path:
    workspace_root = tmp_path / "workspace"
    package_root = workspace_root / "src" / "transaction_fixture"
    package_root.mkdir(parents=True)
    (package_root / "__init__.py").write_text(
        '"""Transaction fixture package."""\n', encoding="utf-8"
    )
    (workspace_root / "pyproject.toml").write_text(
        "[project]\nname = 'transaction-fixture'\nversion = '0.1.0'\n", encoding="utf-8"
    )
    repository = u.Tests.repository_ref("transaction-fixture")
    workspace = m.Infra.WorkspaceSpec(
        version=c.Infra.WORKSPACE_MANIFEST_VERSION,
        name=repository.name,
        repository=repository,
        members=(),
    )
    tm.ok(
        u.Cli.yaml_dump(
            workspace_root / "config" / "workspace.yaml",
            workspace.model_dump(mode="json", exclude_none=True),
        )
    )
    u.Tests.initialize_git_repo(workspace_root)
    return workspace_root


class TestsFlextInfraWorktreeTransaction:
    """Exercise transaction invariants through real Git state."""

    def test_transaction_apply_removes_source_and_sandbox_lock_state(
        self, tmp_path: Path
    ) -> None:
        source_root, worktree_root, delta = _operation_delta(tmp_path)
        lock_path = config.Infra.codegen.make.serialization.lock_path

        tm.ok(u.Infra.git_apply_transaction_patches((delta,)))

        tm.that((source_root / lock_path).exists(), eq=False)
        tm.that((worktree_root / lock_path).exists(), eq=False)
        tm.that((source_root / lock_path.parts[0]).exists(), eq=False)
        tm.that((worktree_root / lock_path.parts[0]).exists(), eq=False)

    def test_detached_transaction_worktree_does_not_run_repository_hooks(
        self, tmp_path: Path
    ) -> None:
        """Keep synthetic validation worktrees independent of operator hooks."""
        source_root = tmp_path / "source"
        source_root.mkdir()
        u.Tests.initialize_git_repo(source_root)
        hooks_root = source_root / ".git" / "hooks"
        hooks_root.mkdir(exist_ok=True)
        post_checkout = hooks_root / "post-checkout"
        post_checkout.write_text("#!/bin/sh\nexit 70\n", encoding="utf-8")
        post_checkout.chmod(0o755)
        worktree_root = tmp_path / "isolated"

        head: str = tm.ok(u.Infra.git_add_detached_worktree(source_root, worktree_root))

        tm.that(tm.ok(u.Infra.git_repository_head(worktree_root)), eq=head)

    def test_isolated_worktree_does_not_run_host_checkout_hooks(
        self, tmp_path: Path
    ) -> None:
        """Transaction setup remains independent of host hook toolchains."""
        source_root = tmp_path / "source"
        source_root.mkdir()
        (source_root / "README.md").write_text("fixture\n", encoding="utf-8")
        u.Tests.initialize_git_repo(source_root)
        marker = tmp_path / "host-hook-ran"
        hooks_root = tmp_path / "hooks"
        hooks_root.mkdir()
        hook = hooks_root / "post-checkout"
        hook.write_text(f"#!/bin/sh\ntouch {marker}\nexit 77\n", encoding="utf-8")
        hook.chmod(0o755)
        tm.ok(
            u.Infra.git_capture(
                source_root, ("config", "core.hooksPath", str(hooks_root))
            )
        )

        isolated_root = tmp_path / "isolated"

        tm.ok(u.Infra.git_add_detached_worktree(source_root, isolated_root))
        tm.that(marker.exists(), eq=False)
        tm.that(isolated_root.is_dir(), eq=True)

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

        tm.ok(u.Infra.git_apply_transaction_patches((delta,)))

        tm.that(artifact.read_bytes(), eq=b"after\n")
        tm.that(_git_status(source_root), eq=converged_status)

    def test_apply_is_repeatable(self, tmp_path: Path) -> None:
        """Apply the same real patch twice without a second mutation or failure."""
        source_root, _worktree_root, delta = _operation_delta(tmp_path)
        artifact = source_root / "artifact.txt"
        tm.ok(u.Infra.git_apply_transaction_patches((delta,)))
        applied_status = _git_status(source_root)

        tm.ok(u.Infra.git_apply_transaction_patches((delta,)))

        tm.that(artifact.read_bytes(), eq=b"after\n")
        tm.that(_git_status(source_root), eq=applied_status)

    def test_transaction_apply_preflights_all_heads_before_any_patch(
        self, tmp_path: Path
    ) -> None:
        """Reject one advanced source before applying any repository delta."""
        first_source, first_worktree, first_delta = _operation_delta(tmp_path / "first")
        second_source, second_worktree, second_delta = _operation_delta(
            tmp_path / "second"
        )
        first_artifact = first_source / "artifact.txt"
        second_artifact = second_source / "artifact.txt"
        concurrent = second_source / "concurrent.txt"
        concurrent.write_text("new head\n", encoding="utf-8")
        tm.ok(u.Infra.git_capture(second_source, ("add", concurrent.name)))
        tm.ok(
            u.Infra.git_capture(
                second_source, ("commit", "-m", "advance source during transaction")
            )
        )
        first_status = _git_status(first_source)
        second_status = _git_status(second_source)
        first_bytes = first_artifact.read_bytes()
        second_bytes = second_artifact.read_bytes()

        result = u.Infra.git_apply_transaction_patches((first_delta, second_delta))

        tm.fail(result, has="source HEAD changed during isolated transaction")
        tm.that(first_artifact.read_bytes(), eq=first_bytes)
        tm.that(second_artifact.read_bytes(), eq=second_bytes)
        tm.that(_git_status(first_source), eq=first_status)
        tm.that(_git_status(second_source), eq=second_status)
        serialization = config.Infra.codegen.make.serialization

        def available() -> p.Result[bool]:
            return r[bool].ok(True)

        def timeout_failure(lock_path: Path, timeout_seconds: int) -> p.Result[bool]:
            return r[bool].fail(f"{lock_path} remained locked for {timeout_seconds}s")

        def acquisition_failure(error: str) -> p.Result[bool]:
            return r[bool].fail(error)

        for repository_root in (
            first_source,
            first_worktree,
            second_source,
            second_worktree,
        ):
            tm.ok(
                u.Infra.serialization_lock_execute(
                    (repository_root / serialization.lock_path,),
                    0,
                    available,
                    timeout_failure=timeout_failure,
                    acquisition_failure=acquisition_failure,
                )
            )

    def test_transaction_lock_blocks_head_movement_after_preflight(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Apply every delta before a contending writer can advance source HEAD."""
        first_source, _first_worktree, first_delta = _operation_delta(
            tmp_path / "first"
        )
        second_source, _second_worktree, second_delta = _operation_delta(
            tmp_path / "second"
        )
        first_artifact = first_source / "artifact.txt"
        second_artifact = second_source / "artifact.txt"
        lock_path = (
            second_source / config.Infra.codegen.make.serialization.lock_path
        ).resolve()
        preflight_complete = Event()
        contention_observed = Event()
        original_run_raw = u.Cli.run_raw

        def observed_run_raw(
            cmd: t.StrSequence,
            cwd: t.Cli.TextPath | None = None,
            timeout: int | None = None,
            env: t.StrMapping | None = None,
            remove_env_keys: t.StrSequence = (),
            input_data: str | bytes | None = None,
            *,
            capture: bool = True,
        ) -> p.Result[p.Cli.CommandOutput]:
            result = original_run_raw(
                cmd,
                cwd=cwd,
                timeout=timeout,
                env=env,
                remove_env_keys=remove_env_keys,
                input_data=input_data,
                capture=capture,
            )
            if (
                tuple(cmd) == (c.Infra.GIT, "rev-parse", "HEAD")
                and cwd is not None
                and Path(cwd).resolve() == second_source.resolve()
            ):
                preflight_complete.set()
                tm.that(contention_observed.wait(timeout=10), where=bool)
            return result

        monkeypatch.setattr(u.Cli, "run_raw", observed_run_raw)

        def advance_source_head() -> p.Result[bool]:
            concurrent = second_source / "concurrent.txt"
            concurrent.write_text("new head\n", encoding="utf-8")
            add_result = u.Infra.git_capture(second_source, ("add", concurrent.name))
            if add_result.failure:
                return r[bool].fail(add_result.error or "failed to stage writer change")
            commit_result = u.Infra.git_capture(
                second_source,
                ("commit", "-m", "advance source after transaction apply"),
            )
            if commit_result.failure:
                return r[bool].fail(
                    commit_result.error or "failed to commit writer change"
                )
            return r[bool].ok(True)

        def timeout_failure(_lock_path: Path, _timeout_seconds: int) -> p.Result[bool]:
            return r[bool].fail("canonical transaction lock contended")

        def acquisition_failure(error: str) -> p.Result[bool]:
            return r[bool].fail(error)

        def attempt_head_advance() -> bool:
            tm.that(preflight_complete.wait(timeout=10), where=bool)
            immediate: p.Result[bool] = u.Infra.serialization_lock_execute(
                (lock_path,),
                0,
                advance_source_head,
                timeout_failure=timeout_failure,
                acquisition_failure=acquisition_failure,
            )
            lock_contended = immediate.failure
            contention_observed.set()
            if lock_contended:
                tm.ok(
                    u.Infra.serialization_lock_execute(
                        (lock_path,),
                        10,
                        advance_source_head,
                        timeout_failure=timeout_failure,
                        acquisition_failure=acquisition_failure,
                    )
                )
            return lock_contended

        with ThreadPoolExecutor(max_workers=1) as executor:
            advance_future = executor.submit(attempt_head_advance)
            tm.ok(u.Infra.git_apply_transaction_patches((first_delta, second_delta)))
            lock_contended = advance_future.result(timeout=15)

        tm.that(lock_contended, where=bool)
        tm.that(first_artifact.read_bytes(), eq=b"after\n")
        tm.that(second_artifact.read_bytes(), eq=b"after\n")
        tm.that((second_source / "concurrent.txt").read_bytes(), eq=b"new head\n")

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
        checkpoint: str = tm.ok(
            u.Infra.git_add_detached_worktree(source_root, worktree_root)
        )
        generated = worktree_root / ".vscode" / "settings.json"
        generated.parent.mkdir()
        generated.write_text('{"strict": true}\n', encoding="utf-8")
        delta: m.Infra.RepositoryDelta = tm.ok(
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

    def test_public_transaction_executes_current_cli_without_source_mutation(
        self, tmp_path: Path
    ) -> None:
        """Exercise the isolated runtime and preserve the source checkout."""
        workspace_root = _workspace(tmp_path)
        before_status = _git_status(workspace_root)
        before_pyproject = (workspace_root / "pyproject.toml").read_bytes()

        transaction_result = u.Infra.execute_worktree_transaction(
            m.Infra.WorktreeTransactionRequest(
                workspace_root=workspace_root,
                command=("--help",),
                apply_patch=False,
                timeout_seconds=c.Infra.WORKTREE_TRANSACTION_TIMEOUT_SECONDS,
            )
        )
        report: m.Infra.WorktreeTransactionReport = tm.ok(transaction_result)
        output = u.Infra.render_worktree_transaction_report(report)

        tm.that(report.breakage_detected, eq=False, msg=output)
        tm.that(report.command_output.exit_code, eq=0, msg=output)
        tm.that(report.import_probe.exit_code, eq=0, msg=output)
        tm.that(report.applied, eq=False)
        tm.that(output, has="applied=no")
        tm.that((workspace_root / "pyproject.toml").read_bytes(), eq=before_pyproject)
        tm.that(_git_status(workspace_root), eq=before_status)
        tm.that(report.worktree_root.exists(), eq=False)


__all__: tuple[str, ...] = ()
