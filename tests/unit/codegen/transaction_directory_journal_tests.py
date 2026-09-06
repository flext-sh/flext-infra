"""Durable directory authority for generation transaction effects."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from flext_infra import m
from flext_infra.codegen import codegen_transaction as transaction
from flext_infra.codegen.mise_artifacts import FlextInfraCodegenMiseArtifacts
from flext_infra.codegen.mise_artifacts_workspace import FlextInfraMiseWorkspacePlanner
from flext_tests import tm
from tests import u as test_u


class TestsTransactionDirectoryJournal:
    """Exercise creation and cleanup against real physical filesystem state."""

    _TRANSACTION_ID = "a" * 32

    @staticmethod
    def _layout(root: Path) -> m.Infra.MiseToolchainWorkspaceLayout:
        root.mkdir()
        test_u.Tests.initialize_git_repo(root)
        (root / "bin").mkdir()
        owner = FlextInfraCodegenMiseArtifacts(
            workspace_root=root, apply_changes=True, check_only=False
        )
        planned = FlextInfraMiseWorkspacePlanner(owner).layout_from_selectors(
            root.resolve(),
            (".",),
            transaction_id=TestsTransactionDirectoryJournal._TRANSACTION_ID,
        )
        return tm.ok(planned)

    @staticmethod
    def _journal(
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        directories: tuple[m.Infra.CodegenJournalDirectory, ...],
    ) -> m.Infra.CodegenTransactionJournal:
        physical = layout.scope_root.lstat()
        return m.Infra.CodegenTransactionJournal(
            version=8,
            transaction_id=TestsTransactionDirectoryJournal._TRANSACTION_ID,
            scope_device=physical.st_dev,
            scope_inode=physical.st_ino,
            state="prepared",
            projects=(
                m.Infra.CodegenJournalProject(
                    selector=".", device=physical.st_dev, inode=physical.st_ino
                ),
            ),
            sources=(),
            directories=directories,
            entries=(),
        )

    @staticmethod
    def _materialize(
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        directories: tuple[m.Infra.CodegenJournalDirectory, ...],
    ) -> tuple[m.Infra.CodegenJournalDirectory, ...]:
        current = directories
        for intent in directories:
            created = tm.ok(
                transaction.state.create_journaled_directory(layout, current, intent)
            )
            current = tuple(
                created if entry.path == intent.path else entry for entry in current
            )
        return current

    @classmethod
    def _register_manifest(
        cls,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        directories: tuple[m.Infra.CodegenJournalDirectory, ...],
    ) -> m.Infra.CodegenTransactionJournal:
        journal = cls._journal(layout, directories)
        registered = tm.ok(
            transaction.verify.register_transaction_manifests(layout, journal)
        )
        return tm.ok(transaction.journal_io.record_directories(journal, registered))

    def test_temporary_tree_is_journaled_before_creation_and_removed(
        self, tmp_path: Path
    ) -> None:
        """Remove arbitrary regular staging files and every newly created parent."""
        layout = self._layout(tmp_path / "repository")

        planned = transaction.state.plan_transaction_directories(layout)

        directories = tm.ok(planned)
        tm.that((layout.scope_root / ".state").exists(), eq=False)
        directories = self._materialize(layout, directories)
        transaction_root = layout.projects[0].transaction_root
        assert transaction_root is not None
        (transaction_root / "partial-download").write_bytes(b"owned staging bytes")
        journal = self._register_manifest(layout, directories)

        cleaned = transaction.state.cleanup_journaled_directories(
            layout, journal, include_generated=True
        )

        tm.ok(cleaned, eq=True)
        tm.that((layout.scope_root / ".state").exists(), eq=False)

    def test_nonempty_generated_directory_is_preserved_and_rejected(
        self, tmp_path: Path
    ) -> None:
        """Never infer ownership for an unexpected file in a live generated path."""
        layout = self._layout(tmp_path / "repository")
        target = layout.scope_root / "docs" / "generated"
        planned = transaction.state.plan_directories(
            layout, phase="docs", requested=(target,), disposition="generated"
        )
        directories = tm.ok(planned)
        directories = self._materialize(layout, directories)
        foreign = target / "foreign.txt"
        foreign.write_text("not journaled", encoding="utf-8")

        cleaned = transaction.state.cleanup_journaled_directories(
            layout, self._journal(layout, directories), include_generated=True
        )

        tm.fail(cleaned)
        tm.that(foreign.read_text(encoding="utf-8"), eq="not journaled")

    @pytest.mark.skipif(os.name == "nt", reason="fixture symlink needs privilege")
    def test_transaction_symlink_is_preserved_and_rejected(
        self, tmp_path: Path
    ) -> None:
        """Reject a transaction tree whose topology contains an alias."""
        layout = self._layout(tmp_path / "repository")
        directories = tm.ok(transaction.state.plan_transaction_directories(layout))
        directories = self._materialize(layout, directories)
        transaction_root = layout.projects[0].transaction_root
        assert transaction_root is not None
        journal = self._register_manifest(layout, directories)
        (transaction_root / "alias").symlink_to(layout.scope_root)

        cleaned = transaction.state.cleanup_journaled_directories(
            layout, journal, include_generated=True
        )

        tm.fail(cleaned)
        tm.that((transaction_root / "alias").is_symlink(), eq=True)

    def test_replaced_generated_directory_identity_is_preserved_and_rejected(
        self, tmp_path: Path
    ) -> None:
        """Never delete a new empty inode placed at a journaled pathname."""
        layout = self._layout(tmp_path / "repository")
        target = layout.scope_root / "docs" / "generated"
        directories = tm.ok(
            transaction.state.plan_directories(
                layout, phase="docs", requested=(target,), disposition="generated"
            )
        )
        directories = self._materialize(layout, directories)
        original = layout.scope_root / "original-generated"
        target.rename(original)
        target.mkdir()

        cleaned = transaction.state.cleanup_journaled_directories(
            layout, self._journal(layout, directories), include_generated=True
        )

        tm.fail(cleaned)
        tm.that(target.is_dir(), eq=True)
        tm.that(original.is_dir(), eq=True)

    def test_foreign_file_after_manifest_is_preserved_and_rejected(
        self, tmp_path: Path
    ) -> None:
        """Reject an unregistered descendant before applying any delete."""
        layout = self._layout(tmp_path / "repository")
        directories = self._materialize(
            layout, tm.ok(transaction.state.plan_transaction_directories(layout))
        )
        journal = self._register_manifest(layout, directories)
        transaction_root = layout.projects[0].transaction_root
        assert transaction_root is not None
        foreign = transaction_root / "foreign.bin"
        foreign.write_bytes(b"foreign")

        cleaned = transaction.state.cleanup_journaled_directories(
            layout, journal, include_generated=True
        )

        tm.fail(cleaned, has="unregistered")
        tm.that(foreign.read_bytes(), eq=b"foreign")

    def test_missing_registered_temporary_file_preserves_tree_and_fails(
        self, tmp_path: Path
    ) -> None:
        """Do not normalize disappearance of a non-consumable journaled file."""
        layout = self._layout(tmp_path / "repository")
        directories = self._materialize(
            layout, tm.ok(transaction.state.plan_transaction_directories(layout))
        )
        transaction_root = layout.projects[0].transaction_root
        assert transaction_root is not None
        payload = transaction_root / "registered.bin"
        payload.write_bytes(b"registered")
        journal = self._register_manifest(layout, directories)
        payload.unlink()

        cleaned = transaction.state.cleanup_journaled_directories(
            layout, journal, include_generated=True
        )

        tm.fail(cleaned, has="missing")
        tm.that(transaction_root.is_dir(), eq=True)

    def test_crash_before_identity_persistence_preserves_unbound_tree(
        self, tmp_path: Path
    ) -> None:
        """Never infer ownership from a pathname after the creation crash window."""
        layout = self._layout(tmp_path / "repository")
        directories = tm.ok(transaction.state.plan_transaction_directories(layout))
        transaction_root = layout.projects[0].transaction_root
        assert transaction_root is not None
        transaction_root.mkdir(parents=True)
        marker = transaction_root / "unknown-owner.bin"
        marker.write_bytes(b"preserve")

        cleaned = transaction.state.cleanup_journaled_directories(
            layout, self._journal(layout, directories), include_generated=True
        )

        tm.fail(cleaned, has="not journaled")
        tm.that(marker.read_bytes(), eq=b"preserve")


__all__: tuple[str, ...] = ()
