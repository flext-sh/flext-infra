"""Per-worktree administrative lock contracts for complete generation."""

from __future__ import annotations

from pathlib import Path

<<<<<<< HEAD
import pytest

from flext_infra import c, m, p, r, u
from flext_infra.codegen.codegen_transaction import FlextInfraCodegenTransaction
from flext_infra.codegen.mise_artifacts import FlextInfraCodegenMiseArtifacts
from flext_infra.codegen.mise_artifacts_lock import FlextInfraMiseLock
=======
from flext_infra import p, r, u
from flext_infra.codegen.codegen_transaction import FlextInfraCodegenTransaction
>>>>>>> origin/0.12.0-dev
from flext_infra.codegen.mise_artifacts_workspace import FlextInfraMiseWorkspacePlanner
from flext_tests import tm
from tests.unit.codegen.mise_generation_lock_fixture import (
    lock_identity,
    lock_owner,
    lock_repository,
)


class TestsMiseGenerationLock:
    """Coordinate generation through one worktree-specific Git lock file."""

    @staticmethod
<<<<<<< HEAD
    def _repository(root: Path) -> Path:
        root.mkdir(parents=True)
        test_u.Tests.initialize_git_repo(root)
        return root

    @staticmethod
    def _owner(root: Path) -> FlextInfraCodegenMiseArtifacts:
        return FlextInfraCodegenMiseArtifacts(
            repository_root=root, apply_changes=False, check_only=True
        )

    @staticmethod
    def _identity(root: Path) -> m.Infra.GitIdentityReport:
        identity = u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=root))
        validated: m.Infra.GitIdentityReport = tm.ok(identity)
        return validated

    @staticmethod
    def _replace_head(head: Path, replacement: Path) -> None:
        replacement.write_bytes(head.read_bytes())
        replacement.replace(head)

    @staticmethod
    def _replace_lock(lock: Path, replacement: Path) -> None:
        replacement.write_bytes(lock.read_bytes())
        replacement.chmod(c.Infra.CODEGEN_TRANSACTION_LOCK_MODE)
        replacement.replace(lock)

    @classmethod
    def _submodule(cls, tmp_path: Path) -> tuple[Path, Path]:
        source = cls._repository(tmp_path / "source")
        superproject = cls._repository(tmp_path / "superproject")
=======
    def _submodule(tmp_path: Path) -> tuple[Path, Path]:
        source = lock_repository(tmp_path / "source")
        superproject = lock_repository(tmp_path / "superproject")
>>>>>>> origin/0.12.0-dev
        tm.ok(
            u.Cli.run_checked([
                "git",
                "-C",
                str(superproject),
                "-c",
                "protocol.file.allow=always",
                "submodule",
                "add",
                "--quiet",
                str(source),
                "member",
            ])
        )
        tm.ok(
            u.Cli.run_checked([
                "git",
                "-C",
                str(superproject),
                "commit",
                "--quiet",
                "-m",
                "add member",
            ])
        )
        return superproject, superproject / "member"

    def test_clean_check_uses_git_administration_without_creating_state(
        self, tmp_path: Path
    ) -> None:
        """Reach the locked check operation while a clean checkout stays untouched."""
        root = lock_repository(tmp_path / "standalone")
        transaction = FlextInfraCodegenTransaction(lock_owner(root))
        observed: list[Path] = []

        def observe(scope: Path) -> p.Result[bool]:
            observed.append(scope)
            return r[bool].ok(True)

        result = transaction.run_locked(prepare=False, operation=observe)

        tm.ok(result, eq=True)
        tm.that(observed, eq=[root.resolve()])
        tm.that((root / ".state").exists(), eq=False)
        tm.that(
            (
                self._identity(root).git_dir / c.Infra.CODEGEN_TRANSACTION_LOCK_FILENAME
            ).is_file(),
            eq=True,
        )

<<<<<<< HEAD
    def test_second_process_contends_on_same_scope_lock(self, tmp_path: Path) -> None:
        """Make a distinct process lose one nonblocking attempt on the same inode."""
        root = self._repository(tmp_path / "contended")
        identity = self._identity(root)
        child = """
from pathlib import Path
import sys
from flext_infra import m, u
from flext_infra.codegen.mise_artifacts_lock import FlextInfraMiseLock

identity = u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=Path(sys.argv[1])))
if identity.failure:
    raise SystemExit(3)
try:
    with FlextInfraMiseLock.lease(identity.value):
        raise SystemExit(4)
except BlockingIOError:
    raise SystemExit(0)
"""

        with FlextInfraMiseLock.lease(identity):
            contended = u.Cli.run_raw(
                (sys.executable, "-c", child, str(root)), timeout=30
            )

        tm.ok(contended)
        tm.that(
            contended.value.outcome.raw_return_code, eq=0, msg=contended.value.stderr
        )

=======
>>>>>>> origin/0.12.0-dev
    def test_nested_independent_repo_ignores_ancestor_journal(
        self, tmp_path: Path
    ) -> None:
        """Resolve the requested repository before considering its own recovery state."""
        parent = lock_repository(tmp_path / "parent")
        journal = (
            lock_identity(parent).git_dir
            / "flext-infra-codegen-transaction-journal.json"
        )
        journal.write_bytes(b"foreign ancestor journal")
        nested = lock_repository(parent / "nested")

        scope = FlextInfraMiseWorkspacePlanner(lock_owner(nested)).scope_identity()

        tm.ok(scope)
        tm.that(scope.value.repo_root, eq=nested.resolve())
        tm.that(scope.value.git_dir, eq=(nested / ".git").resolve())

    def test_layout_binds_journal_directly_to_exact_git_directory(
        self, tmp_path: Path
    ) -> None:
        """Carry one distinctive journal path from the authenticated Git identity."""
        root = lock_repository(tmp_path / "journal-layout")
        identity = lock_identity(root)

        layout = FlextInfraMiseWorkspacePlanner(lock_owner(root)).journal_layout(
            identity
        )

        tm.ok(layout)
        tm.that(
            layout.value.journal_path,
            eq=identity.git_dir / "flext-infra-codegen-transaction-journal.json",
        )
        tm.that(layout.value.journal_path.parent, eq=identity.git_dir)
        tm.that(layout.value.journal_path.is_relative_to(root / ".state"), eq=False)

    def test_submodule_uses_its_declared_superproject_scope(
        self, tmp_path: Path
    ) -> None:
        """Bind a governed member to the superproject worktree Git directory."""
        superproject, member = self._submodule(tmp_path)
        planner = FlextInfraMiseWorkspacePlanner(lock_owner(member))

        scope = planner.scope_identity()

        tm.ok(scope)
        tm.that(scope.value.repo_root, eq=superproject.resolve())
        tm.that(scope.value.git_dir, eq=(superproject / ".git").resolve())
        layout = planner.journal_layout(scope.value)
        tm.ok(layout)
        tm.that(layout.value.journal_path.parent, eq=scope.value.git_dir)

<<<<<<< HEAD
    def test_head_replacement_is_rejected_while_lease_is_held(
        self, tmp_path: Path
    ) -> None:
        """Reject a Git operation that atomically replaces the locked HEAD inode."""
        root = self._repository(tmp_path / "swapped")
        identity = self._identity(root)
        head = identity.git_dir / "HEAD"
        replacement = identity.git_dir / "replacement-head"

        with (
            pytest.raises(OSError, match="changed while held"),
            FlextInfraMiseLock.lease(identity),
        ):
            self._replace_head(head, replacement)

    def test_lock_replacement_is_rejected_while_lease_is_held(
        self, tmp_path: Path
    ) -> None:
        """Reject pathname replacement that could create two lock owners."""
        root = self._repository(tmp_path / "lock-swapped")
        identity = self._identity(root)
        lock = identity.git_dir / c.Infra.CODEGEN_TRANSACTION_LOCK_FILENAME
        replacement = identity.git_dir / "replacement-codegen-lock"

        with (
            pytest.raises(OSError, match="pathname changed while held"),
            FlextInfraMiseLock.lease(identity),
        ):
            self._replace_lock(lock, replacement)

    def test_head_hardlink_is_rejected(self, tmp_path: Path) -> None:
        """Reject an anchor inode that is no longer uniquely named."""
        root = self._repository(tmp_path / "hardlinked")
        identity = self._identity(root)
        (identity.git_dir / "HEAD-alias").hardlink_to(identity.git_dir / "HEAD")

        with (
            pytest.raises(OSError, match="hard links"),
            FlextInfraMiseLock.lease(identity),
        ):
            pass

    @pytest.mark.skipif(
        os.name == "nt", reason="fixture symlinks need Windows privilege"
    )
    def test_head_symlink_is_rejected(self, tmp_path: Path) -> None:
        """Reject legacy Git HEAD symlinks as reparse/alias lock anchors."""
        root = self._repository(tmp_path / "symlinked")
        identity = self._identity(root)
        head = identity.git_dir / "HEAD"
        backup = identity.git_dir / "HEAD-backup"
        head.replace(backup)
        head.symlink_to(backup.name)

        with (
            pytest.raises(OSError, match="regular file"),
            FlextInfraMiseLock.lease(identity),
        ):
            pass

=======
>>>>>>> origin/0.12.0-dev
    def test_head_validation_and_reconcile_create_no_state(
        self, tmp_path: Path
    ) -> None:
        """Keep Git validation and journal discovery read-only before the operation."""
        root = lock_repository(tmp_path / "apply")
        identity = lock_identity(root)
        head = identity.git_dir / "HEAD"
        journal = identity.git_dir / "flext-infra-codegen-transaction-journal.json"
        head.chmod(0o666)
        transaction = FlextInfraCodegenTransaction(lock_owner(root))

        rejected = transaction.run_locked(
            prepare=True, operation=lambda _scope: r[bool].ok(True)
        )

        tm.fail(rejected, has="unsafe mode")
        tm.that((root / ".state").exists(), eq=False)
        head.chmod(0o644)

        accepted = transaction.run_locked(
            prepare=True,
            operation=lambda _scope: r[bool].ok(
                not (root / ".state").exists() and not journal.exists()
            ),
        )

        tm.ok(accepted, eq=True)
        tm.that((root / ".state").exists(), eq=False)
        tm.that(journal.exists(), eq=False)


__all__: tuple[str, ...] = ()
