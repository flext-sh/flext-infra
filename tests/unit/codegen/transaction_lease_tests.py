"""Public transaction ownership across real processes and attached repositories."""

from __future__ import annotations

import multiprocessing
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from filelock import Timeout
from flext_tests import tm

from flext_core import r
from flext_infra import config, m, p, u
from flext_infra.codegen.codegen_transaction import FlextInfraCodegenTransaction
from flext_infra.codegen.mise_artifacts import FlextInfraCodegenMiseArtifacts
from flext_infra.codegen.mise_artifacts_workspace import FlextInfraMiseWorkspacePlanner
from tests import u as test_u

if TYPE_CHECKING:
    from multiprocessing.synchronize import Event


def _ok_path(scope: Path) -> p.Result[Path]:
    """Trivial identity operation typed concretely for ``run_locked``.

    Why: passing the generic ``r[Path].ok`` classmethod directly loses its
    ``Path`` specialization at the call site (a second, independent type
    variable on ``ok`` itself), so a concretely annotated wrapper is the
    typed fix rather than widening ``run_locked``'s signature.
    """
    return r[Path].ok(scope)


class TestsTransactionLease:
    """Keep live journal recovery behind the shared physical scope lease."""

    @staticmethod
    def _hold_transaction(root: Path, ready: Event, release: Event) -> None:
        """Publish a real prepared phase and commit after the contender finishes."""
        owner = FlextInfraCodegenMiseArtifacts(repository_root=root)
        transaction = FlextInfraCodegenTransaction(owner)

        def publish(scope_root: Path) -> p.Result[bool]:
            config_path = root / ".mise.toml"
            before = tm.ok(
                u.Cli.atomic_read_binary_file_state(config_path, required=True)
            )
            plan = tm.ok(
                u.Infra.planned_file(
                    root,
                    config_path,
                    required=True,
                    desired_content=before.content,
                    desired_mode=before.mode,
                    owner="mise",
                )
            )
            session = tm.ok(transaction.begin_locked(scope_root, (plan,), (plan,)))
            ready.set()
            tm.that(
                release.wait(config.Infra.tooling.tools.pytest.slow_timeout_seconds),
                eq=True,
            )
            tm.ok(
                transaction.commit_locked(
                    session, lambda: owner.validate_artifacts(root)
                )
            )
            return r[bool].ok(True)

        tm.ok(transaction.run_locked(prepare=True, operation=publish))

    @pytest.mark.slow
    def test_contenders_cannot_reconcile_live_journal_across_member_scope(
        self, tmp_path: Path
    ) -> None:
        """Reject root/member contenders while a separate scope stays independent."""
        root = test_u.Tests.git_repository(tmp_path, "workspace")
        seed = test_u.Tests.git_repository(tmp_path, "member-source")
        test_u.Tests.copy_tracked_mise_seeds(seed)
        test_u.Tests.commit_git_changes(seed, "Seed declared Mise artifacts")
        test_u.Tests.git_bootstrap(
            root,
            (
                "-c",
                "protocol.file.allow=always",
                "submodule",
                "add",
                str(seed),
                "member",
            ),
        )
        member = root / "member"
        independent = test_u.Tests.git_repository(tmp_path, "independent")
        test_u.Tests.copy_tracked_mise_seeds(independent)
        identity = tm.ok(u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=root)))
        journal_path = FlextInfraMiseWorkspacePlanner.journal_path(identity)
        lock_path = journal_path.with_name(f"{journal_path.name}.lock")
        context = multiprocessing.get_context("spawn")
        ready, release = context.Event(), context.Event()
        holder = context.Process(
            target=self._hold_transaction, args=(member, ready, release)
        )
        holder.start()
        try:
            tm.that(
                ready.wait(config.Infra.tooling.tools.pytest.slow_timeout_seconds),
                eq=True,
            )
            journal_before = journal_path.read_bytes()
            lock_before = lock_path.stat()
            for contender_root in (root, member):
                contender = FlextInfraCodegenTransaction(
                    FlextInfraCodegenMiseArtifacts(repository_root=contender_root)
                )
                with pytest.raises(Timeout) as failure:
                    contender.run_locked(prepare=True, operation=_ok_path)
                tm.that(failure.value.lock_file, eq=str(lock_path))
                tm.that(journal_path.read_bytes(), eq=journal_before)

            independent_owner = FlextInfraCodegenMiseArtifacts(
                repository_root=independent
            )
            tm.ok(
                FlextInfraCodegenTransaction(independent_owner).run_locked(
                    prepare=True, operation=independent_owner.validate_artifacts
                )
            )
            tm.that(journal_path.read_bytes(), eq=journal_before)
        finally:
            release.set()
            holder.join(timeout=config.Infra.tooling.tools.pytest.slow_timeout_seconds)
            tm.that(holder.exitcode, eq=0)
            holder.close()

        tm.that(journal_path.exists(), eq=False)
        lock_after = lock_path.stat()
        tm.that(
            (lock_after.st_dev, lock_after.st_ino),
            eq=(lock_before.st_dev, lock_before.st_ino),
        )
        owner = FlextInfraCodegenMiseArtifacts(repository_root=member)
        tm.ok(
            FlextInfraCodegenTransaction(owner).run_locked(
                prepare=True, operation=lambda _scope: owner.validate_artifacts(member)
            )
        )
        tm.that(lock_path.stat().st_ino, eq=lock_after.st_ino)

    def test_operation_error_escapes_unchanged_and_releases_lease(
        self, tmp_path: Path
    ) -> None:
        """Keep the original error object and allow ownership after an exception."""
        root = test_u.Tests.git_repository(tmp_path)
        transaction = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root)
        )
        original = OSError("operation failed under its lease")

        def fail(_scope: Path) -> p.Result[bool]:
            raise original

        with pytest.raises(
            OSError, match="operation failed under its lease"
        ) as failure:
            transaction.run_locked(prepare=False, operation=fail)
        tm.that(failure.value is original, eq=True)
        tm.ok(transaction.run_locked(prepare=False, operation=_ok_path))
