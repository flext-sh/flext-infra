"""Physical Git-HEAD lock contracts for complete generation."""

from __future__ import annotations

from pathlib import Path

from flext_infra import p, r, u
from flext_infra.codegen.codegen_transaction import FlextInfraCodegenTransaction
from flext_infra.codegen.mise_artifacts_workspace import FlextInfraMiseWorkspacePlanner
from flext_tests import tm
from tests.unit.codegen.mise_generation_lock_fixture import (
    lock_identity,
    lock_owner,
    lock_repository,
)


class TestsMiseGenerationLock:
    """Coordinate generation through one existing worktree-specific Git file."""

    @staticmethod
    def _submodule(tmp_path: Path) -> tuple[Path, Path]:
        source = lock_repository(tmp_path / "source")
        superproject = lock_repository(tmp_path / "superproject")
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

    def test_clean_check_locks_existing_head_without_creating_state(
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
        """Bind a governed member to the superproject worktree HEAD."""
        superproject, member = self._submodule(tmp_path)
        planner = FlextInfraMiseWorkspacePlanner(lock_owner(member))

        scope = planner.scope_identity()

        tm.ok(scope)
        tm.that(scope.value.repo_root, eq=superproject.resolve())
        tm.that(scope.value.git_dir, eq=(superproject / ".git").resolve())
        layout = planner.journal_layout(scope.value)
        tm.ok(layout)
        tm.that(layout.value.journal_path.parent, eq=scope.value.git_dir)

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
