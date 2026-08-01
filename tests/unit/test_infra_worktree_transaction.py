"""Real Git behavior tests for isolated workspace transactions."""

from __future__ import annotations

import venv
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

    def test_import_probe_uses_requested_workspace_runtime_metadata(
        self, tmp_path: Path
    ) -> None:
        """Import staged sources with distribution metadata from their runtime."""
        workspace_root = _workspace(tmp_path)
        runtime_python = workspace_root / c.Infra.VENV_BIN_REL / c.Infra.PYTHON
        runtime_root = runtime_python.parent.parent
        venv.EnvBuilder(with_pip=False, symlinks=True).create(runtime_root)
        site_result = u.Cli.run_raw(
            (
                str(runtime_python),
                "-c",
                "import sysconfig; print(sysconfig.get_path('purelib'))",
            ),
            cwd=workspace_root,
        )
        site_output: p.Cli.CommandOutput = tm.ok(site_result)
        site_packages = Path(site_output.stdout.strip())
        dist_info = site_packages / "transaction_fixture-0.1.0.dist-info"
        dist_info.mkdir()
        (dist_info / "METADATA").write_text(
            "Metadata-Version: 2.1\nName: transaction-fixture\nVersion: 0.1.0\n",
            encoding="utf-8",
        )
        (workspace_root / "src" / "transaction_fixture" / "__init__.py").write_text(
            (
                "from importlib.metadata import version\n"
                "PACKAGE_VERSION = version('transaction-fixture')\n"
            ),
            encoding="utf-8",
        )
        transaction_environment = u.Infra._transaction_environment(  # ruff:ignore[private-member-access]
            workspace_root
        )
        import_probe = u.Infra._import_probe(  # ruff:ignore[private-member-access]
            workspace_root,
            workspace_root,
            transaction_environment,
            c.Infra.WORKTREE_TRANSACTION_TIMEOUT_SECONDS,
        )

        tm.that(import_probe.exit_code, eq=0)
        tm.that(import_probe.stdout, has="imported 1 packages")

    def test_request_normalizes_relative_workspace_root(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Canonicalize a direct caller's relative root at the typed boundary."""
        workspace_root = _workspace(tmp_path)
        monkeypatch.chdir(tmp_path)

        request = m.Infra.WorktreeTransactionRequest(
            workspace_root=workspace_root.relative_to(tmp_path),
            command=(c.Infra.CLI_GROUP_CODEGEN, c.Infra.CodegenKind.CONFORM),
            timeout_seconds=c.Infra.WORKTREE_TRANSACTION_TIMEOUT_SECONDS,
        )

        tm.that(request.workspace_root, eq=workspace_root.resolve())

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
        source_head = tm.ok(u.Infra.git_repository_head(nested_root))
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
            u.Infra.git_capture(
                workspace_root,
                (
                    "update-index",
                    "--add",
                    "--cacheinfo",
                    "160000",
                    source_head,
                    "nested-repository",
                ),
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
            u.Infra.git_capture(
                worktree_root,
                (
                    "update-index",
                    "--add",
                    "--cacheinfo",
                    "160000",
                    nested.checkpoint_sha,
                    nested.relative_path,
                ),
            )
        )

        deltas = tm.ok(u.Infra._repository_deltas(repositories))  # ruff:ignore[private-member-access]
        root_delta = next(delta for delta in deltas if delta.relative_path == ".")

        patch_text = root_delta.patch.decode()
        tm.that(patch_text, has=f"+Subproject commit {source_head}")
        tm.that(patch_text, lacks=f"+Subproject commit {nested.checkpoint_sha}")
        tm.ok(u.Infra.git_apply_patch(root_delta))
        staged = tm.ok(
            u.Infra.git_capture(
                workspace_root, ("ls-files", "--stage", "--", nested.relative_path)
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

    def test_empty_transaction_patch_reports_no_application(
        self, tmp_path: Path
    ) -> None:
        """Report a fixed-point transaction as a successful no-op."""
        _source_root, _worktree_root, delta = _operation_delta(tmp_path)
        empty_delta = delta.model_copy(update={"changed_files": (), "patch": b""})

        applied = tm.ok(u.Infra.git_apply_transaction_patches((empty_delta,)))

        tm.that(applied, eq=False)

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

    def test_public_dry_run_skips_static_tools_and_preserves_source(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Generate in isolation without invoking check-owned static tools."""
        workspace_root = _workspace(tmp_path)
        before_status = _git_status(workspace_root)
        pyproject_path = workspace_root / c.Infra.PYPROJECT_FILENAME
        before_pyproject = pyproject_path.read_bytes()
        sentinel_bin = tmp_path / "sentinel-bin"
        sentinel_bin.mkdir()
        for tool in (c.Infra.RUFF, c.Infra.PYREFLY):
            executable = sentinel_bin / tool
            executable.write_text(
                "#!/bin/sh\nprintf '%s\\n' called >> \"$0.called\"\nexit 91\n",
                encoding="utf-8",
            )
            executable.chmod(0o755)
        monkeypatch.setenv(
            c.Infra.ORCHESTRATOR_ENV_PATH,
            str(sentinel_bin),
            prepend=c.Infra.ORCHESTRATOR_ENV_PATH_SEPARATOR,
        )
        conform_request = m.Infra.CodegenConformRequest(
            root=workspace_root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        conform_arguments = tuple(
            argument
            for field_name, value in conform_request.model_dump(mode="json").items()
            for argument in (f"--{field_name.replace('_', '-')}", str(value))
        )

        transaction_result = u.Infra.execute_worktree_transaction(
            m.Infra.WorktreeTransactionRequest(
                workspace_root=workspace_root,
                command=(
                    c.Infra.CLI_GROUP_CODEGEN,
                    c.Infra.CodegenKind.CONFORM,
                    *conform_arguments,
                ),
                apply_patch=False,
                timeout_seconds=c.Infra.WORKTREE_TRANSACTION_TIMEOUT_SECONDS,
            )
        )
        report = tm.ok(transaction_result)
        output = u.Infra.render_worktree_transaction_report(report)

        tm.that(report.command_output.exit_code, eq=0, msg=output)
        tm.that(report.import_probe.exit_code, eq=0, msg=output)
        tm.that(report.breakage_detected, eq=False, msg=output)
        tm.that(output, has="diff -- repository .")
        tm.that(output, has="patch-check=ok")
        tm.that(output, has="applied=no")
        for tool in (c.Infra.RUFF, c.Infra.PYREFLY):
            tm.that((sentinel_bin / f"{tool}.called").exists(), eq=False)
        tm.that(pyproject_path.read_bytes(), eq=before_pyproject)
        tm.that(_git_status(workspace_root), eq=before_status)
        tm.that((workspace_root / c.Infra.MAKEFILE_FILENAME).exists(), eq=False)


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
