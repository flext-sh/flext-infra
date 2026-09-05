"""Durable directory authority for generation transaction effects."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from flext_infra import m
from flext_infra.codegen.codegen_transaction import state
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
            version=7,
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

    def test_temporary_tree_is_journaled_before_creation_and_removed(
        self, tmp_path: Path
    ) -> None:
        """Remove arbitrary regular staging files and every newly created parent."""
        layout = self._layout(tmp_path / "repository")

        planned = state.plan_transaction_directories(layout)

        directories = tm.ok(planned)
        tm.that((layout.scope_root / ".state").exists(), eq=False)
        tm.ok(state.create_journaled_directories(layout, directories), eq=True)
        transaction_root = layout.projects[0].transaction_root
        assert transaction_root is not None
        (transaction_root / "partial-download").write_bytes(b"owned staging bytes")

        cleaned = state.cleanup_journaled_directories(
            layout, self._journal(layout, directories), include_generated=True
        )

        tm.ok(cleaned, eq=True)
        tm.that((layout.scope_root / ".state").exists(), eq=False)

    def test_nonempty_generated_directory_is_preserved_and_rejected(
        self, tmp_path: Path
    ) -> None:
        """Never infer ownership for an unexpected file in a live generated path."""
        layout = self._layout(tmp_path / "repository")
        target = layout.scope_root / "docs" / "generated"
        planned = state.plan_directories(
            layout, phase="docs", requested=(target,), disposition="generated"
        )
        directories = tm.ok(planned)
        tm.ok(state.create_journaled_directories(layout, directories), eq=True)
        foreign = target / "foreign.txt"
        foreign.write_text("not journaled", encoding="utf-8")

        cleaned = state.cleanup_journaled_directories(
            layout, self._journal(layout, directories), include_generated=True
        )

        tm.fail(cleaned, has="not safely empty")
        tm.that(foreign.read_text(encoding="utf-8"), eq="not journaled")

    @pytest.mark.skipif(os.name == "nt", reason="fixture symlink needs privilege")
    def test_transaction_symlink_is_preserved_and_rejected(
        self, tmp_path: Path
    ) -> None:
        """Reject a transaction tree whose topology contains an alias."""
        layout = self._layout(tmp_path / "repository")
        directories = tm.ok(state.plan_transaction_directories(layout))
        tm.ok(state.create_journaled_directories(layout, directories), eq=True)
        transaction_root = layout.projects[0].transaction_root
        assert transaction_root is not None
        (transaction_root / "alias").symlink_to(layout.scope_root)

        cleaned = state.cleanup_journaled_directories(
            layout, self._journal(layout, directories), include_generated=True
        )

        tm.fail(cleaned)
        tm.that((transaction_root / "alias").is_symlink(), eq=True)


__all__: tuple[str, ...] = ()
