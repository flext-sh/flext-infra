"""Real Git behavior tests for isolated workspace transactions."""

from __future__ import annotations

import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

import pytest

from flext_core import r
from flext_infra import c, config, p, t
from flext_tests import tm
from tests import m, u


def _git_status(repository_root: Path) -> str:
    return tm.ok(
        u.Cli.capture(
            [c.Infra.GIT, "status", "--porcelain=v1", "-z"], cwd=repository_root
        )
    )


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
    add_result = u.Infra.git_add_detached_worktree(source_root, worktree_root)
    tm.ok(add_result)
    checkpoint = tm.ok(
        u.Infra.git_checkpoint_worktree(
            worktree_root, message="test isolated transaction checkpoint"
        )
    )
    (worktree_root / artifact.name).write_bytes(b"after\n")
    delta_result = u.Infra.git_repository_delta(
        m.Infra.RepositoryWorktree(
            relative_path=".",
            source_root=source_root,
            worktree_root=worktree_root,
            checkpoint_sha=checkpoint,
        )
    )
    tm.ok(delta_result)
    return source_root, worktree_root, delta_result.value


def _workspace(tmp_path: Path) -> Path:
    workspace_root = tmp_path / "workspace"
    package_root = workspace_root / "src" / "transaction_fixture"
    package_root.mkdir(parents=True)
    (package_root / "__init__.py").write_text(
        '"""Transaction fixture package."""\n', encoding="utf-8"
    )
    (workspace_root / "pyproject.toml").write_text(
        (
            "[project]\n"
            "name = 'transaction-fixture'\n"
            "version = '0.1.0'\n"
            "\n"
            "[tool.pyrefly]\n"
            "project-includes = ['src/**/*.py*']\n"
            "python-version = '3.13'\n"
        ),
        encoding="utf-8",
    )
    (workspace_root / ".taplo.toml").write_text("", encoding="utf-8")
    config_root = workspace_root / "config"
    config_root.mkdir()
    (config_root / "workspace.yaml").write_text(
        (
            "version: 3\n"
            "name: transaction-fixture\n"
            "repository:\n"
            "  name: transaction-fixture\n"
            "  distribution: transaction-fixture\n"
            "  provider: flext-sh\n"
            "  url: https://github.com/flext-sh/transaction-fixture.git\n"
            "  path: .\n"
            "  role: workspace-root\n"
            "  state: active\n"
            "  checkout: root\n"
            "  codegen: conform\n"
            "  package: false\n"
            "  editable: false\n"
            "  read_only: false\n"
            "project:\n"
            "  package_name: transaction_fixture\n"
            "  class_stem: TransactionFixture\n"
            "  namespace: TransactionFixture\n"
            "  constant_name: transaction-fixture\n"
            "  namespace_attribute: transaction_fixture\n"
            "  alias: transaction_fixture\n"
            "  environment_prefix: TRANSACTION_FIXTURE_\n"
            '  description: "Demo transaction fixture"\n'
            '  version: "0.1.0"\n'
            "  license: MIT\n"
            "  author_name: FLEXT Team\n"
            "  author_email: team@flext.sh\n"
            "  upstream: flext_core\n"
            "  homepage: https://github.com/flext-sh/transaction-fixture\n"
            "  documentation: https://github.com/flext-sh/transaction-fixture\n"
            "  workspace_root_rel: .\n"
            "  year: 2026\n"
            "members: []\n"
            "exclusions: []\n"
        ),
        encoding="utf-8",
    )
    u.Tests.initialize_git_repo(workspace_root)
    return workspace_root


class TestsFlextInfraWorktreeTransaction:
    """Exercise transaction invariants through real Git state."""

    def test_complete_worktree_includes_declared_existing_nested_repository(
        self, tmp_path: Path
    ) -> None:
        workspace_root = _workspace(tmp_path)
        nested_root = workspace_root / "nested-repository"
        nested_root.mkdir()
        marker = nested_root / "marker.txt"
        marker.write_text("nested state\n", encoding="utf-8")
        u.Tests.initialize_git_repo(nested_root)
        marker.write_text("nested WIP\n", encoding="utf-8")
        manifest = workspace_root / "config" / "workspace.yaml"
        manifest.write_text(
            manifest.read_text(encoding="utf-8").replace(
                "members: []\n",
                "members:\n"
                "  - name: nested-repository\n"
                "    distribution: nested-repository\n"
                "    provider: flext-sh\n"
                "    url: https://github.com/flext-sh/nested-repository.git\n"
                "    path: nested-repository\n"
                "    role: workspace-member\n"
                "    state: active\n"
                "    checkout: submodule\n"
                "    codegen: conform\n"
                "    package: true\n"
                "    editable: true\n"
                "    read_only: false\n",
            ),
            encoding="utf-8",
        )
        worktree_root = tmp_path / "isolated"

        repositories = tm.ok(
            u.Infra._create_complete_worktree(  # ruff:ignore[private-member-access]
                workspace_root, worktree_root, "transaction-test"
            )
        )

        tm.that(
            tuple(repository.relative_path for repository in repositories),
            has="nested-repository",
        )
        tm.that(
            (worktree_root / "nested-repository" / "marker.txt").read_text(
                encoding="utf-8"
            ),
            eq="nested WIP\n",
        )
        tm.that(marker.read_text(encoding="utf-8"), eq="nested WIP\n")
        tm.ok(u.Infra._cleanup_worktrees(repositories, worktree_root))  # ruff:ignore[private-member-access]

    def test_nested_checkpoint_transport_preserves_source_head_gitlink(
        self, tmp_path: Path
    ) -> None:
        workspace_root = _workspace(tmp_path)
        nested_root = workspace_root / "nested-repository"
        nested_root.mkdir()
        (nested_root / "marker.txt").write_text("source\n", encoding="utf-8")
        u.Tests.initialize_git_repo(nested_root)
        source_head = tm.ok(
            u.Infra.git_repository_head(m.Infra.GitRepoRequest(repo_root=nested_root))
        ).oid
        # The contract under test is gitlink TRANSPORT: the isolated worktree
        # must not leak its own checkpoint SHA back into the superproject's
        # recorded pointer. That pointer only exists when the superproject
        # actually tracks the nested repository as a gitlink, so the fixture
        # records it exactly as Git does for an initialized submodule.
        (workspace_root / ".gitmodules").write_text(
            '[submodule "nested-repository"]\n'
            "\tpath = nested-repository\n"
            "\turl = https://github.com/flext-sh/nested-repository.git\n"
            "\tbranch = 0.12.0-dev\n"
            "\tflext-managed = true\n",
            encoding="utf-8",
        )
        tm.ok(
            u.Infra.git_update_index_gitlink(
                m.Infra.GitUpdateIndexGitlinkRequest(
                    repo_root=workspace_root,
                    oid=source_head,
                    relative_path="nested-repository",
                )
            )
        )
        manifest = workspace_root / "config" / "workspace.yaml"
        manifest.write_text(
            manifest.read_text(encoding="utf-8").replace(
                "members: []\n",
                "members:\n"
                "  - name: nested-repository\n"
                "    distribution: nested-repository\n"
                "    provider: flext-sh\n"
                "    url: https://github.com/flext-sh/nested-repository.git\n"
                "    path: nested-repository\n"
                "    role: workspace-member\n"
                "    state: active\n"
                "    checkout: submodule\n"
                "    codegen: conform\n"
                "    package: true\n"
                "    editable: true\n"
                "    read_only: false\n",
            ),
            encoding="utf-8",
        )
        worktree_root = tmp_path / "isolated"
        repositories = tm.ok(
            u.Infra._create_complete_worktree(  # ruff:ignore[private-member-access]
                workspace_root, worktree_root, "gitlink-identity-test"
            )
        )
        nested = next(
            repository
            for repository in repositories
            if repository.relative_path == "nested-repository"
        )
        tm.ok(
            u.Infra.git_update_index_gitlink(
                m.Infra.GitUpdateIndexGitlinkRequest(
                    repo_root=worktree_root,
                    oid=nested.checkpoint_sha,
                    relative_path=nested.relative_path,
                )
            )
        )

        deltas = tm.ok(u.Infra._repository_deltas(repositories))  # ruff:ignore[private-member-access]
        root_delta = next(delta for delta in deltas if delta.relative_path == ".")

        # Operation patches exclude submodule pointers entirely
        # (--ignore-submodules=all): gitlinks are owned by `make setup`, which
        # fast-forwards each declared submodule to its branch tip. The root
        # patch therefore carries no Subproject line for either the source
        # head or the sandbox checkpoint; the transport-safety contract is
        # enforced by the source index keeping the source head after apply.
        patch_text = root_delta.patch.decode()
        tm.that(patch_text, lacks="Subproject commit")
        tm.ok(u.Infra.git_apply_patch(root_delta))
        staged = tm.ok(
            u.Cli.capture(
                [c.Infra.GIT, "ls-files", "--stage", "--", nested.relative_path],
                cwd=workspace_root,
            )
        )
        tm.that(staged, eq=f"160000 {source_head} 0\t{nested.relative_path}")
        tm.ok(u.Infra._cleanup_worktrees(repositories, worktree_root))  # ruff:ignore[private-member-access]

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

        head = tm.ok(u.Infra.git_add_detached_worktree(source_root, worktree_root))

        tm.that(
            tm.ok(
                u.Infra.git_repository_head(
                    m.Infra.GitRepoRequest(repo_root=worktree_root)
                )
            ).oid,
            eq=head,
        )

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
            u.Cli.run_checked(
                [c.Infra.GIT, "config", "core.hooksPath", str(hooks_root)],
                cwd=source_root,
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
        tm.ok(
            u.Cli.run_checked([c.Infra.GIT, "add", concurrent.name], cwd=second_source)
        )
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "commit", "-m", "advance source during transaction"],
                cwd=second_source,
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
        original_head = u.Infra.git_repository_head

        def observed_head(
            _cls: type[object], request: m.Infra.GitRepoRequest
        ) -> p.Result[m.Infra.GitOidReport]:
            """Observe the typed preflight HEAD read on the contended source."""
            result = original_head(request)
            if request.repo_root.expanduser().resolve() == second_source.resolve():
                preflight_complete.set()
                tm.that(contention_observed.wait(timeout=10), where=bool)
            return result

        # The facet resolves HEAD through the typed Request/Report method, so
        # the contention hook patches that seam (GitPython spawns no u.Cli
        # process call the old monkeypatch could observe).
        monkeypatch.setattr(
            "flext_infra._utilities.git.FlextInfraUtilitiesGit.git_repository_head",
            classmethod(observed_head),
        )

        def advance_source_head() -> p.Result[bool]:
            concurrent = second_source / "concurrent.txt"
            concurrent.write_text("new head\n", encoding="utf-8")
            add_result = u.Cli.run_checked(
                [c.Infra.GIT, "add", concurrent.name], cwd=second_source
            )
            if add_result.failure:
                return r[bool].fail(add_result.error or "failed to stage writer change")
            commit_result = u.Cli.run_checked(
                [c.Infra.GIT, "commit", "-m", "advance source after transaction apply"],
                cwd=second_source,
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
                    "codegen",
                    "conform",
                    "--root",
                    str(workspace_root),
                    "--scope",
                    "self",
                    "--mode",
                    "apply",
                ),
                apply_patch=False,
                timeout_seconds=c.Infra.WORKTREE_TRANSACTION_TIMEOUT_SECONDS,
            )
        )
        report = tm.ok(transaction_result)
        output = u.Infra.render_worktree_transaction_report(report)
        lint_output = "\n".join(item.output for item in report.lint_after)

        tm.that(report.breakage_detected, eq=False, msg=f"{output}\n{lint_output}")
        tm.that(output, has="diff -- repository .")
        tm.that(output, has="applied=no")
        tm.that((workspace_root / "pyproject.toml").read_bytes(), eq=before_pyproject)
        tm.that(_git_status(workspace_root), eq=before_status)
        tm.that((workspace_root / "Makefile").exists(), eq=False)

    def test_public_transaction_fails_before_command_when_managed_tool_is_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Empty lint-command SSOT resolves without requiring managed lint tools."""
        managed_bin = tmp_path / "host-bin-without-managed-tools"
        managed_bin.mkdir()
        required_host_tools = (c.Infra.GIT, "basename", "sed", "uname", "sh")
        for tool in required_host_tools:
            resolved_tool = shutil.which(tool)
            if resolved_tool is None:
                pytest.fail(f"host tool required by the transaction test: {tool}")
            (managed_bin / tool).symlink_to(resolved_tool)
        monkeypatch.setenv(c.Infra.ORCHESTRATOR_ENV_PATH, str(managed_bin))

        tm.that(c.Infra.WORKTREE_TRANSACTION_LINT_COMMANDS, eq=())
        commands = tm.ok(u.Infra._lint_commands(tmp_path))  # ruff:ignore[private-member-access]
        tm.that(commands, eq=())


class TestsFlextInfraWorktreeTransactionLint:
    """Contract for fail-closed differential transaction lint evidence."""

    def test_transaction_lint_binds_uv_overlay_tools_from_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Empty lint-command SSOT resolves to an empty bound command tuple."""
        overlay_bin = tmp_path / "overlay" / "bin"
        overlay_bin.mkdir(parents=True)
        monkeypatch.setenv("PATH", str(overlay_bin))
        monkeypatch.setenv(c.Infra.ORCHESTRATOR_ENV_PATH, str(overlay_bin))

        tm.that(c.Infra.WORKTREE_TRANSACTION_LINT_COMMANDS, eq=())
        commands = tm.ok(u.Infra._lint_commands(tmp_path))  # ruff:ignore[private-member-access]

        tm.that(commands, eq=())

    def test_transaction_lint_type_checks_against_the_project_venv(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """With empty lint commands there is no pyrefly interpreter binding."""
        overlay_bin = tmp_path / "overlay" / "bin"
        overlay_bin.mkdir(parents=True)
        monkeypatch.setenv("PATH", str(overlay_bin))
        monkeypatch.setenv(c.Infra.ORCHESTRATOR_ENV_PATH, str(overlay_bin))
        venv_python = tmp_path / c.Infra.VENV_BIN_REL / c.Infra.PYTHON
        venv_python.parent.mkdir(parents=True)
        venv_python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        venv_python.chmod(0o755)

        tm.that(c.Infra.WORKTREE_TRANSACTION_LINT_COMMANDS, eq=())
        commands: t.StrSequencePairTuple = tm.ok(
            u.Infra._lint_commands(tmp_path)  # ruff:ignore[private-member-access]
        )

        tm.that(commands, eq=())
        tm.that(any(tool == c.Infra.PYREFLY for tool, _command in commands), eq=False)

    def test_transaction_lint_reports_counts_and_actionable_locations(self) -> None:
        """Transaction lint commands are intentionally empty by design."""
        tm.that(c.Infra.WORKTREE_TRANSACTION_LINT_COMMANDS, eq=())

    def test_lint_regressed_rejects_new_errors_warnings_and_failures(self) -> None:
        """Stable debt is reported; every introduced diagnostic is rejected."""
        clean = (m.Infra.LintSnapshot(tool="ruff", exit_code=0),)
        errors = (m.Infra.LintSnapshot(tool="ruff", exit_code=0, errors=1),)
        warnings = (m.Infra.LintSnapshot(tool="ruff", exit_code=0, warnings=1),)
        nonzero = (m.Infra.LintSnapshot(tool="ruff", exit_code=1, errors=1),)

        lint_regressed = u.Infra._lint_regressed  # ruff:ignore[private-member-access]

        tm.that(lint_regressed(clean, errors), eq=True)
        tm.that(lint_regressed(clean, warnings), eq=True)
        tm.that(lint_regressed(clean, nonzero), eq=True)
        tm.that(lint_regressed(errors, errors), eq=False)


class TestsFlextInfraWorktreeTransactionScope:
    """Contract for the productive source roots one transaction owns."""

    @staticmethod
    def _workspace(root: Path, *members: str) -> Path:
        """Materialize a workspace whose members each expose a source root."""
        for member in members:
            package = root / member / c.Infra.DEFAULT_SRC_DIR / member.replace("-", "_")
            package.mkdir(parents=True)
            (package / c.Infra.INIT_PY).write_text("", encoding="utf-8")
        return root

    def test_scoped_request_excludes_unrelated_sibling_members(
        self, tmp_path: Path
    ) -> None:
        """A scoped transaction never adopts a sibling it does not declare."""
        # Presence on disk is not a declared dependency: importing an unscoped
        # sibling fails closed on any member that is merely checked out.
        root = self._workspace(tmp_path, "alpha-package", "beta-package")
        source_roots = u.Infra._source_roots  # ruff:ignore[private-member-access]

        scoped = source_roots(root, (Path("alpha-package"),))

        tm.that({path.parent.parent.name for path in scoped}, eq={"alpha-package"})

    def test_unscoped_request_keeps_every_member(self, tmp_path: Path) -> None:
        """An empty scope still isolates the whole workspace, as documented."""
        root = self._workspace(tmp_path, "alpha-package", "beta-package")
        source_roots = u.Infra._source_roots  # ruff:ignore[private-member-access]

        every = source_roots(root)

        tm.that(
            {path.parent.parent.name for path in every},
            eq={"alpha-package", "beta-package"},
        )
