"""Recovery classification never deadlocks on a vanished staging tree."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra.codegen._mise_artifacts_files import (
    FlextInfraMiseArtifactsFiles as files,
)
from flext_infra.codegen._mise_artifacts_recovery import FlextInfraMiseRecovery
from flext_infra.codegen.mise_artifacts import FlextInfraCodegenMiseArtifacts
from flext_infra.codegen.mise_artifacts_workspace import FlextInfraMiseWorkspacePlanner
from tests import m, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraMiseRecoveryVanishedStaging:
    """A recovery journal whose staged tree is gone must classify to noop."""

    def test_restore_entry_with_vanished_staging_tree_never_deadlocks(
        self, tmp_path: Path
    ) -> None:
        """A crashed run that removed the staged tree cannot restore it.

        Why: recovery used to hard-fail on the required read of the staged
        rollback candidate under a directory that no longer exists, so the
        pending journal blocked every later generation run (circular
        impasse). The downgrade keeps the generation as the file owner and
        skips staging a restore candidate.
        """
        root = u.Tests.git_repository(tmp_path)
        u.Tests.copy_tracked_mise_seeds(root)
        mise_owner = FlextInfraCodegenMiseArtifacts(repository_root=root)
        planner = FlextInfraMiseWorkspacePlanner(mise_owner)
        layout = tm.ok(planner.layout_from_selectors(root, (".",)))
        destination = root / "config" / "generated-demo.md"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("original\n", encoding="utf-8")
        original = tm.ok(u.Cli.atomic_read_binary_file_state(destination, required=True))
        destination.write_text("desired\n", encoding="utf-8")
        desired = tm.ok(u.Cli.atomic_read_binary_file_state(destination, required=True))
        entry = m.Infra.CodegenJournalEntry.model_construct(
            phase="lazy-init",
            project=".",
            path="config/generated-demo.md",
            original_exists=True,
            original_backup="phase-lazy-init/backups/generated-demo.md",
            original_parent_device=original.parent_device,
            original_parent_inode=original.parent_inode,
            original_sha256=files.digest(original.content),
            original_mode=original.mode,
            original_device=original.device,
            original_inode=original.inode,
            original_link_count=original.link_count,
            original_file_attributes=original.file_attributes,
            original_reparse_tag=original.reparse_tag,
            desired_exists=True,
            desired_staging="phase-lazy-init/staging/generated-demo.md",
            desired_parent_device=desired.parent_device,
            desired_parent_inode=desired.parent_inode,
            desired_sha256=files.digest(desired.content),
            desired_mode=desired.mode,
            desired_device=desired.device,
            desired_inode=desired.inode,
            desired_link_count=desired.link_count,
            desired_file_attributes=desired.file_attributes,
            desired_reparse_tag=desired.reparse_tag,
            rollback_exists=False,
            rollback_parent_device=desired.parent_device,
            rollback_parent_inode=desired.parent_inode,
            rollback_sha256=None,
            rollback_mode=None,
            rollback_file_attributes=None,
            rollback_reparse_tag=None,
        )
        journal = m.Infra.CodegenTransactionJournal.model_construct(
            state="recovering",
            entries=(entry,),
        )
        recovery = FlextInfraMiseRecovery()

        actions = tm.ok(recovery._classify(layout, journal))
        candidates = tm.ok(recovery._prepare_restore_candidates(layout, actions))

        tm.that(actions[0].operation, eq="noop")
        tm.that(candidates, eq=(None,))


__all__: list[str] = ["TestsFlextInfraMiseRecoveryVanishedStaging"]
