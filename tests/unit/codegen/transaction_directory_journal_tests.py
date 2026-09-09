"""Durable directory authority for generation transaction effects."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import m, p, u
from flext_infra.codegen import codegen_transaction as transaction
from flext_infra.codegen.mise_artifacts import FlextInfraCodegenMiseArtifacts
from flext_infra.codegen.mise_artifacts_workspace import FlextInfraMiseWorkspacePlanner
from tests import u as test_u


class TestsTransactionDirectoryJournal:
    """Exercise creation and cleanup against real physical filesystem state."""

    _TRANSACTION_ID = "a" * 32

    @pytest.mark.parametrize("foreign_change", [False, True])
    @pytest.mark.parametrize("missing_launcher_parent", [False, True])
    def test_duplicate_phase_recovers_only_its_new_generated_files(
        self, tmp_path: Path, *, foreign_change: bool, missing_launcher_parent: bool
    ) -> None:
        """Undo exact new publications, never a foreign replacement at their path."""
        root = test_u.Tests.git_repository(tmp_path)
        test_u.Tests.copy_tracked_mise_seeds(root)
        owner = transaction.FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root)
        )
        layout = tm.ok(
            FlextInfraMiseWorkspacePlanner(
                FlextInfraCodegenMiseArtifacts(repository_root=root)
            ).layout_from_selectors(root.resolve(), (".",))
        )
        artifacts = layout.projects[0].artifacts
        if missing_launcher_parent:
            artifacts.unix_launcher.unlink()
            artifacts.windows_launcher.unlink()
            artifacts.unix_launcher.parent.rmdir()
        target = root / "docs/generated/readme.md"

        def conflict(scope_root: Path) -> p.Result[m.Infra.CodegenTransactionSession]:
            config_path = root / ".mise.toml"
            before = tm.ok(
                u.Cli.atomic_read_binary_file_state(config_path, required=True)
            )
            config_plan = tm.ok(
                u.Infra.planned_file(
                    root,
                    config_path,
                    required=True,
                    desired_content=before.content,
                    desired_mode=before.mode,
                    owner="mise",
                )
            )
            session = tm.ok(
                owner.begin_locked(scope_root, (config_plan,), (config_plan,))
            )
            tm.that(artifacts.unix_launcher.is_file(), eq=True)
            tm.that(artifacts.windows_launcher.is_file(), eq=True)
            session = tm.ok(
                owner.append_directories_locked(session, "docs", (target.parent,))
            )
            first = tm.ok(
                u.Infra.planned_file(
                    root,
                    target,
                    required=False,
                    desired_content=b"first phase\n",
                    desired_mode=before.mode,
                    owner="conform",
                )
            )
            session = tm.ok(owner.append_phase_locked(session, "conform", (first,)))
            if foreign_change:
                target.write_bytes(b"foreign content\n")
            duplicate = tm.ok(
                u.Infra.planned_file(
                    root,
                    target,
                    required=True,
                    desired_content=b"docs phase\n",
                    desired_mode=before.mode,
                    owner="docs",
                )
            )
            return owner.append_phase_locked(session, "docs", (duplicate,))

        failed = owner.run_locked(prepare=True, operation=conflict)

        tm.fail(failed, has="multiple generation phases own one destination")
        identity = tm.ok(u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=root)))
        journal = FlextInfraMiseWorkspacePlanner.journal_path(identity)
        tm.that(journal.exists(), eq=foreign_change)
        if foreign_change:
            tm.that(failed.error, has="new generated file changed before recovery")
            tm.that(target.read_bytes(), eq=b"foreign content\n")
        else:
            tm.that(failed.error, lacks="recovery failed")
            tm.that((root / "docs").exists(), eq=False)
            tm.that((root / ".state").exists(), eq=False)
            tm.that(
                artifacts.unix_launcher.parent.exists(), eq=not missing_launcher_parent
            )

    def test_appended_phase_rejects_replaced_created_parent(
        self, tmp_path: Path
    ) -> None:
        """Never adopt a foreign parent while staging a previously absent file."""
        root = test_u.Tests.git_repository(tmp_path)
        test_u.Tests.copy_tracked_mise_seeds(root)
        owner = transaction.FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root)
        )
        target = root / "docs/generated/readme.md"
        preserved = root / "original-generated"

        def replace_parent(
            scope_root: Path,
        ) -> p.Result[m.Infra.CodegenTransactionSession]:
            config_path = root / ".mise.toml"
            before = tm.ok(
                u.Cli.atomic_read_binary_file_state(config_path, required=True)
            )
            config_plan = tm.ok(
                u.Infra.planned_file(
                    root,
                    config_path,
                    required=True,
                    desired_content=before.content,
                    desired_mode=before.mode,
                    owner="mise",
                )
            )
            session = tm.ok(
                owner.begin_locked(scope_root, (config_plan,), (config_plan,))
            )
            planned = tm.ok(
                u.Infra.planned_file(
                    root,
                    target,
                    required=False,
                    desired_content=b"owned content\n",
                    desired_mode=before.mode,
                    owner="docs",
                )
            )
            session = tm.ok(
                owner.append_directories_locked(session, "docs", (target.parent,))
            )
            target.parent.rename(preserved)
            target.parent.mkdir()
            return owner.append_phase_locked(session, "docs", (planned,))

        failed = owner.run_locked(prepare=True, operation=replace_parent)

        tm.fail(failed, has="generation destination parent differs from journal")
        tm.that(target.exists(), eq=False)
        tm.that(target.parent.is_dir(), eq=True)
        tm.that(preserved.is_dir(), eq=True)

    @staticmethod
    def _layout(root: Path) -> m.Infra.MiseToolchainWorkspaceLayout:
        root.mkdir()
        test_u.Tests.initialize_git_repo(root)
        (root / "bin").mkdir()
        owner = FlextInfraCodegenMiseArtifacts(
            repository_root=root, apply_changes=True, check_only=False
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
        recorded: m.Infra.CodegenTransactionJournal = tm.ok(
            transaction.journal_io.record_directories(journal, registered)
        )
        return recorded

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
