"""Durable directory authority for generation transaction effects.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import errno
import os
import stat
from pathlib import Path
from uuid import uuid4

import pytest

from flext_infra import config
from flext_infra.codegen import (
    FlextInfraCodegenTransaction,
    FlextInfraMiseArtifactsCandidates,
    FlextInfraMiseArtifactsJournal,
    FlextInfraMiseArtifactsState,
    FlextInfraMiseArtifactsVerification,
)
from flext_infra.codegen.mise_artifacts import FlextInfraCodegenMiseArtifacts
from flext_infra.codegen.mise_artifacts_workspace import FlextInfraMiseWorkspacePlanner
from tests import c, m, p, r, t, tm, u
from tests.unit.codegen.conform_support import TestsFlextInfraConformSupport


class TestsFlextInfraTransactionDirectoryJournal:
    """Exercise creation and cleanup against real physical filesystem state."""

    _TRANSACTION_ID = "a" * 32

    @staticmethod
    def _archived(
        root: Path,
        transaction_id: str,
    ) -> tuple[m.Infra.CodegenPhaseOutcome, ...]:
        """Read every receipt the transaction archived under its identity.

        Returns:
            The archived publication receipts of the transaction.

        """
        archive = (
            tm.ok(u.Infra.refactor_report_evidence_root(root))
            / c.Infra.CODEGEN_PUBLICATION_ARCHIVE_RELATIVE_PATH
            / transaction_id
        )
        return tuple(
            m.Infra.CodegenPhaseOutcome.model_validate_json(
                path.read_text(encoding=c.DEFAULT_ENCODING),
            )
            for path in sorted(archive.iterdir())
        )

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize(
        ("project_name", "package_name", "version"),
        [
            ("flext-source-alpha", "flext_source_alpha", "0.12.7"),
            ("flext-source-beta", "flext_source_beta", "7.4.9"),
        ],
    )
    def test_initial_invalid_source_dependencies_leave_no_staging_effects(
        tmp_path: Path,
        project_name: str,
        package_name: str,
        version: str,
    ) -> None:
        """Initial staging recovery preserves the original files and first failure."""
        root, _package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name=project_name,
            package_name=package_name,
        )
        tm.ok(u.Infra.replace_project_version(root, version))
        u.Tests.copy_tracked_mise_seeds(root)
        target = root / "generated.md"
        target.write_bytes(b"original document\n")
        config_path = root / c.Infra.MISE_TOML_FILENAME
        config_before = tm.ok(
            u.Cli.atomic_read_binary_file_state(config_path, required=True),
        )
        target_before = tm.ok(
            u.Cli.atomic_read_binary_file_state(target, required=True),
        )
        config_plan = m.Infra.CodegenFilePlan(
            project=root,
            path=config_path,
            before=config_before,
            desired_content=config_before.content,
            desired_mode=config_before.mode,
            owner="mise",
        )
        invalid = m.Infra.CodegenFilePlan(
            project=root,
            path=target,
            before=target_before,
            desired_content=b"generated document\n",
            desired_mode=target_before.mode,
            source_states=(config_before, config_before),
            owner="conform",
        )
        owner = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = owner.capability_roots("conform", (root,))
        before = TestsFlextInfraConformSupport.project_tree(root)
        for _attempt in range(2):
            failed = owner.run_files_locked(
                roots,
                lambda scope_root: owner.publish_file_phase_locked(
                    scope_root,
                    roots,
                    m.Infra.CodegenPhaseAnalysis(
                        phase=c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP,
                        files=(config_plan, invalid),
                        inputs=(config_before,),
                    ),
                    m.Infra.CodegenPhasePublicationPolicy(directories=()),
                ),
            )
            tm.fail(failed, has="journal entry source dependencies must be unique")
            tm.that(
                TestsFlextInfraConformSupport.project_tree(root),
                eq=before,
            )
        tm.that(
            tuple((root / c.Infra.TRANSACTION_STATE_DIRNAME).iterdir()),
            eq=(
                root
                / c.Infra.TRANSACTION_STATE_DIRNAME
                / f"{c.Infra.JOURNAL_NAME}.lock",
            ),
        )
        identity = tm.ok(u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=root)))
        tm.that(
            FlextInfraMiseWorkspacePlanner.journal_path(identity).exists(),
            eq=False,
        )
        tm.ok(owner.run_locked(prepare=True, operation=r[Path].ok))

    @staticmethod
    def test_mise_snapshot_separates_render_inputs_from_local_config_sources(
        tmp_path: Path,
    ) -> None:
        """Mixed render provenance authenticates without widening local config sets."""
        root = u.Tests.git_repository(tmp_path)
        u.Tests.copy_tracked_mise_seeds(root)
        config_dir = root / c.CONFIG_DIR_NAME
        config_dir.mkdir()
        local = config_dir / "scenario.yaml"
        local.write_text("scenario: initial\n", encoding="utf-8")
        template = tmp_path / "template.j2"
        template.write_text("{{ scenario }}\n", encoding="utf-8")
        template_state = tm.ok(
            u.Cli.atomic_read_binary_file_state(template, required=True),
        )
        tm.that(template_state.content, none=False)
        config_sources = tm.ok(u.Infra.snapshot_config_sources(root))
        local_state = next(source for source in config_sources if source.path == local)
        tm.that(local_state.content, none=False)
        owner = FlextInfraCodegenMiseArtifacts(repository_root=root)
        planner = FlextInfraMiseWorkspacePlanner(owner)
        layout = tm.ok(planner.layout_from_selectors(root, (".",)))
        before = tm.ok(
            u.Cli.atomic_read_binary_file_state(
                layout.projects[0].config, required=True
            ),
        )
        config_plan = m.Infra.CodegenFilePlan(
            project=root,
            path=before.path,
            before=before,
            desired_content=before.content,
            desired_mode=before.mode,
            source_states=(template_state, *config_sources),
        )

        observed = tm.ok(planner.snapshot(layout, (config_plan,)))

        tm.that(observed.projects[0].config.sources, eq=config_sources)
        tm.ok(FlextInfraMiseArtifactsVerification.sources(observed))
        template.write_text("{{ changed }}\n", encoding="utf-8")
        tm.fail(planner.snapshot(layout, (config_plan,)), has=str(template))
        template.write_bytes(tm.not_none(template_state.content))
        local.write_text("scenario: changed\n", encoding="utf-8")
        tm.fail(planner.snapshot(layout, (config_plan,)), has=str(local))
        local.write_bytes(tm.not_none(local_state.content))
        (config_dir / "added.yaml").write_text("added: true\n", encoding="utf-8")
        tm.fail(
            FlextInfraMiseArtifactsVerification.sources(observed),
            has="Mise sources changed",
        )

    @staticmethod
    @pytest.mark.parametrize("mutation", ["missing", "wrong-phase", "duplicate"])
    @pytest.mark.parametrize("delivery", ["result", "raise"])
    def test_persisted_journal_rejects_unowned_source_dependencies(
        tmp_path: Path,
        mutation: str,
        delivery: str,
    ) -> None:
        """A persisted publication requires unique same-phase source authority."""
        root = u.Tests.git_repository(tmp_path)
        source_path = root / "source.txt"
        target = root / "generated.md"
        source_path.write_bytes(b"owned source\n")
        target.write_bytes(b"original target\n")
        source = tm.ok(
            u.Cli.atomic_read_binary_file_state(source_path, required=True),
        )
        before = tm.ok(
            u.Cli.atomic_read_binary_file_state(target, required=True),
        )
        owner = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = {"@source-authority-0": root}
        original_errors: list[ValueError] = []

        def reject_journal(
            session: m.Infra.CodegenTransactionSession,
            _publications: t.VariadicTuple[m.Infra.CodegenStagedFile],
        ) -> p.Result[m.Infra.CodegenTransactionSession]:
            journal, snapshot = tm.ok(
                FlextInfraMiseArtifactsJournal.read(session.plan.layout),
            )
            entry = journal.entries[0]
            tm.that(entry.source_paths, eq=(source.path,))
            if mutation == "duplicate":
                corrupted = journal.model_copy(
                    update={
                        "entries": (
                            entry.model_copy(
                                update={
                                    "source_paths": (*entry.source_paths, source.path)
                                },
                            ),
                        ),
                    },
                )
            else:
                corrupted = journal.model_copy(
                    update={
                        "sources": (
                            ()
                            if mutation == "missing"
                            else tuple(
                                item.model_copy(update={"phase": "semantic"})
                                for item in journal.sources
                            )
                        ),
                    },
                )
            tm.ok(snapshot.mode is not None)
            if snapshot.mode is None:
                pytest.fail("the observed journal snapshot has no physical mode")
            tm.ok(
                u.Cli.atomic_write_binary_file_guarded(
                    snapshot,
                    corrupted.model_dump_json().encode(c.DEFAULT_ENCODING),
                    permission_mode=snapshot.mode,
                ),
            )
            with pytest.raises(ValueError, match="source dependenc") as rejected:
                FlextInfraMiseArtifactsJournal.read(session.plan.layout)
            original_errors.append(rejected.value)
            if delivery == "raise":
                raise rejected.value
            return r[m.Infra.CodegenTransactionSession].fail(
                str(rejected.value),
                exception=rejected.value,
            )

        def publish(scope_root: Path) -> p.Result[m.Infra.CodegenTransactionSession]:
            session = tm.ok(owner.begin_files_locked(scope_root, roots, ()))
            planned = m.Infra.CodegenFilePlan(
                project=root,
                path=target,
                before=before,
                desired_content=b"generated target\n",
                desired_mode=before.mode,
                source_states=(source,),
                owner="docs",
            )
            return owner.publish_prepared_locked(
                session,
                lambda current: owner.append_phase_locked(
                    current,
                    "docs",
                    (planned,),
                    publication_policy=m.Infra.CodegenPhasePublicationPolicy(
                        directories=(), staged_validator=reject_journal
                    ),
                ),
            )

        if delivery == "raise":
            with pytest.raises(ValueError, match="source dependenc") as propagated:
                owner.run_files_locked(roots, publish)
            tm.ok(propagated.value is original_errors[0])
        else:
            rejected = owner.run_files_locked(roots, publish)
            tm.fail(rejected, has="source dependenc")
            tm.ok(rejected.exception is original_errors[0])
            tm.ok(bool(tm.not_none(rejected.error_data)["cleanup_error"]))
        tm.that(target.read_bytes(), eq=before.content)
        tm.that(source_path.read_bytes(), eq=source.content)

    @staticmethod
    def test_live_artifact_verification_preserves_native_read_failure(
        tmp_path: Path,
    ) -> None:
        """A configuration replaced by a directory retains its reader failure."""
        root = u.Tests.git_repository(tmp_path)
        u.Tests.copy_tracked_mise_seeds(root)
        owner = FlextInfraCodegenMiseArtifacts(repository_root=root)
        planner = FlextInfraMiseWorkspacePlanner(owner)
        layout = tm.ok(planner.layout_from_selectors(root, (".",)))
        plan = tm.ok(planner.snapshot(layout))
        config_path = layout.projects[0].config
        preserved = tmp_path / "preserved-mise-config"
        config_path.rename(preserved)
        config_path.mkdir()
        baseline = u.Cli.atomic_read_binary_file_state(
            config_path,
            required=False,
        )

        observed = FlextInfraMiseArtifactsVerification.live(owner, plan)

        tm.that(tm.fail(observed), eq=tm.fail(baseline))
        tm.ok(config_path.is_dir())
        tm.that(preserved.read_bytes(), eq=plan.projects[0].config.before.content)

    @staticmethod
    @pytest.mark.parametrize("pending", [False, True])
    def test_read_only_file_readiness_never_recovers_a_pending_journal(
        tmp_path: Path,
        *,
        pending: bool,
    ) -> None:
        """Readiness proves current state without promoting or removing history."""
        root = u.Tests.git_repository(tmp_path)
        owner = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = {"@readiness-0": root}
        if pending:
            session = tm.ok(
                owner.run_files_locked(
                    roots,
                    lambda scope: owner.begin_files_locked(scope, roots, ()),
                ),
            )
            before = tm.ok(
                u.Cli.atomic_read_binary_file_state(
                    session.plan.layout.journal_path,
                    required=True,
                ),
            )
            tm.fail(
                owner.run_files_locked(
                    roots,
                    lambda _scope: r[bool].ok(value=True),
                    prepare=False,
                ),
                has="pending",
            )
            tm.that(
                tm.ok(
                    u.Cli.atomic_read_binary_file_state(
                        session.plan.layout.journal_path,
                        required=True,
                    ),
                ),
                eq=before,
            )
        else:
            tm.ok(
                owner.run_files_locked(
                    roots,
                    lambda _scope: r[bool].ok(value=True),
                    prepare=False,
                ),
            )

    def test_generation_source_accepts_authenticated_hardlink(
        self,
        tmp_path: Path,
    ) -> None:
        """Journal an immutable dependency source materialized from a cache."""
        root = u.Tests.git_repository(tmp_path)
        u.Tests.copy_tracked_mise_seeds(root)
        mise_owner = FlextInfraCodegenMiseArtifacts(repository_root=root)
        planner = FlextInfraMiseWorkspacePlanner(mise_owner)
        layout = tm.ok(planner.layout_from_selectors(root, (".",)))
        plan = tm.ok(planner.snapshot(layout))
        cache_source = tmp_path / "cache-source.j2"
        installed_source = tmp_path / "installed-source.j2"
        cache_source.write_bytes(b"immutable template bytes")
        os.link(cache_source, installed_source)
        source = tm.ok(
            u.Cli.atomic_read_binary_file_state(installed_source, required=True),
        )

        journal = FlextInfraMiseArtifactsJournal.begin(
            plan,
            transaction_id=self._TRANSACTION_ID,
            sources=(("lazy-init", source),),
        )

        recorded = tm.ok(journal)
        tm.that(recorded.sources[0].link_count, eq=2)

    @staticmethod
    def test_staged_mode_mismatch_preserves_original_configuration(
        tmp_path: Path,
    ) -> None:
        """Reject a real staged mode mismatch without touching the rollback target."""
        root = u.Tests.git_repository(tmp_path)
        u.Tests.copy_tracked_mise_seeds(root)
        owner = FlextInfraCodegenMiseArtifacts(repository_root=root)
        planner = FlextInfraMiseWorkspacePlanner(owner)
        layout = tm.ok(planner.layout_from_selectors(root, (".",)))
        plan = tm.ok(planner.snapshot(layout))
        config_path = layout.projects[0].config
        before = tm.ok(u.Cli.atomic_read_binary_file_state(config_path, required=True))
        desired_mode = next(
            item.mode
            for item in config.Infra.codegen.managed_files
            if item.path == Path(config_path.name)
        )
        stage = tmp_path / "stage"
        stage.mkdir()
        staged_config = stage / config_path.name
        staged_config.write_bytes(tm.not_none(before.content))
        staged_config.chmod(desired_mode ^ stat.S_IWGRP)

        tm.fail(
            FlextInfraMiseArtifactsCandidates.publication_plan(plan.projects, (stage,)),
            has="staged Mise artifact mode differs",
        )
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(config_path, required=True)),
            eq=before,
        )

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("change_config", [False, True])
    @pytest.mark.parametrize("alternate_mode", [False, True])
    def test_mise_commit_preserves_unchanged_publications(
        tmp_path: Path,
        *,
        change_config: bool,
        alternate_mode: bool,
    ) -> None:
        """Journal all staged files without rewriting unchanged live artifacts."""
        root = u.Tests.git_repository(tmp_path)
        u.Tests.copy_tracked_mise_seeds(root)
        mise_owner = FlextInfraCodegenMiseArtifacts(repository_root=root)
        owner = FlextInfraCodegenTransaction(mise_owner)
        roots = owner.capability_roots("mise", (root,))
        layout = tm.ok(
            FlextInfraMiseWorkspacePlanner(mise_owner).layout_from_selectors(
                root,
                (".",),
            ),
        )
        config_path = layout.projects[0].config
        declared_mode = next(
            item.mode
            for item in config.Infra.codegen.managed_files
            if item.path == Path(config_path.name)
        )
        desired_mode = declared_mode ^ stat.S_IWGRP if alternate_mode else declared_mode

        def publish(
            scope_root: Path,
            *,
            change: bool = False,
        ) -> p.Result[t.VariadicTuple[Path]]:
            before = tm.ok(
                u.Cli.atomic_read_binary_file_state(config_path, required=True),
            )
            content = tm.not_none(before.content)
            if change:
                content += b"\n# transaction fixture update\n"
            plan = m.Infra.CodegenFilePlan(
                project=root,
                path=config_path,
                before=before,
                desired_content=content,
                desired_mode=desired_mode,
                owner="mise",
            )
            return owner.publish_file_phase_locked(
                scope_root,
                roots,
                m.Infra.CodegenPhaseAnalysis(
                    phase=c.Infra.CodegenStagedFilePhase.MISE,
                    files=(plan,),
                    inputs=(),
                ),
                m.Infra.CodegenPhasePublicationPolicy(directories=()),
            )

        tm.ok(owner.run_files_locked(roots, publish))
        tm.that(stat.S_IMODE(config_path.stat().st_mode), eq=desired_mode)
        before_state = tm.ok(
            u.Cli.atomic_read_binary_file_state(config_path, required=True),
        )

        written = tm.ok(
            owner.run_files_locked(
                roots,
                lambda scope: publish(scope, change=change_config),
            ),
        )

        tm.that(written, eq=(config_path,) if change_config else ())
        if change_config:
            tm.that(
                config_path.read_bytes(),
                eq=(
                    tm.not_none(before_state.content)
                    + b"\n# transaction fixture update\n"
                ),
            )
        else:
            tm.that(
                tm.ok(u.Cli.atomic_read_binary_file_state(config_path, required=True)),
                eq=before_state,
            )
        tm.fail(layout.journal_path.exists())
        tm.fail(layout.state_root.exists())
        tm.that(stat.S_IMODE(config_path.stat().st_mode), eq=desired_mode)

    @staticmethod
    def test_later_phase_records_identity_without_destination_preimages(
        tmp_path: Path,
    ) -> None:
        """Phases retain fingerprints and gains without original-byte copies."""
        root = u.Tests.git_repository(tmp_path)
        owner = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = {"@docs-0": root}
        targets = {"conform": root / "first.md", "lazy-init": root / "second.md"}
        for phase, target in targets.items():
            target.write_bytes(f"{phase} original\n".encode())
        transactions: list[str] = []

        def two_phases(scope: Path) -> p.Result[t.VariadicTuple[Path]]:
            session = tm.ok(owner.begin_files_locked(scope, roots, ()))
            for phase, target in targets.items():
                plan = m.Infra.CodegenFilePlan(
                    project=root,
                    path=target,
                    before=tm.ok(
                        u.Cli.atomic_read_binary_file_state(target, required=True),
                    ),
                    desired_content=f"{phase} generated\n".encode(),
                    desired_mode=session.journal_state.mode,
                    owner=phase,
                )
                session = tm.ok(owner.append_phase_locked(session, phase, (plan,)))
                transactions.append(session.journal.transaction_id)
                checkpoints = {
                    (item.completed, item.root, item.phase, item.written_files)
                    for item in TestsFlextInfraTransactionDirectoryJournal._archived(
                        root, session.journal.transaction_id
                    )
                }
                tm.that(
                    (False, root, phase, session.written_files) in checkpoints,
                    eq=True,
                )
            tm.that(
                tuple(entry.original_sha256 for entry in session.journal.entries),
                eq=tuple(
                    u.Cli.sha256_bytes(f"{phase} original\n".encode())
                    for phase in targets
                ),
            )
            return owner.commit_locked(session)

        tm.ok(owner.run_files_locked(roots, two_phases))
        completed = {
            (item.completed, item.written_files)
            for item in TestsFlextInfraTransactionDirectoryJournal._archived(
                root, transactions[-1]
            )
        }
        tm.ok((True, tuple(targets.values())) in completed)
        tm.that(
            (root / c.Infra.CODEGEN_PUBLICATION_REPORT_RELATIVE_PATH).exists(),
            eq=False,
        )
        for phase, target in targets.items():
            tm.that(target.read_bytes(), eq=f"{phase} generated\n".encode())

    @staticmethod
    @pytest.mark.parametrize("foreign_change", [False, True])
    def test_duplicate_phase_preserves_previously_generated_files(
        tmp_path: Path,
        *,
        foreign_change: bool,
    ) -> None:
        """Reject duplicate ownership without undoing accepted publications."""
        root = u.Tests.git_repository(tmp_path)
        u.Tests.copy_tracked_mise_seeds(root)
        owner = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = owner.capability_roots("conform", (root,))
        target = root / "docs/generated/readme.md"

        def conflict(scope_root: Path) -> p.Result[m.Infra.CodegenTransactionSession]:
            config_path = root / ".mise.toml"
            before = tm.ok(
                u.Cli.atomic_read_binary_file_state(config_path, required=True),
            )
            config_plan = m.Infra.CodegenFilePlan(
                project=root,
                path=config_path,
                before=before,
                desired_content=before.content,
                desired_mode=before.mode,
                owner="mise",
            )
            session = tm.ok(
                owner.begin_files_locked(scope_root, roots, ()),
            )
            session = tm.ok(
                owner.append_phase_locked(
                    session, c.Infra.CodegenStagedFilePhase.MISE, (config_plan,)
                ),
            )
            session = tm.ok(
                owner.append_directories_locked(session, "docs", (target.parent,)),
            )
            first = m.Infra.CodegenFilePlan(
                project=root,
                path=target,
                before=tm.ok(
                    u.Cli.atomic_read_binary_file_state(target, required=False),
                ),
                desired_content=b"first phase\n",
                desired_mode=before.mode,
                owner="conform",
            )
            session = tm.ok(owner.append_phase_locked(session, "conform", (first,)))
            if foreign_change:
                target.write_bytes(b"foreign content\n")
            duplicate = m.Infra.CodegenFilePlan(
                project=root,
                path=target,
                before=tm.ok(
                    u.Cli.atomic_read_binary_file_state(target, required=True),
                ),
                desired_content=b"docs phase\n",
                desired_mode=before.mode,
                owner="docs",
            )
            return owner.append_phase_locked(session, "docs", (duplicate,))

        failed = owner.run_files_locked(roots, conflict)

        tm.fail(failed, has="multiple generation phases own one destination")
        identity = tm.ok(u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=root)))
        journal = FlextInfraMiseWorkspacePlanner.journal_path(identity)
        # Staging cleanup retires its cursor without removing generated outputs.
        tm.fail(journal.exists())
        if foreign_change:
            tm.that(target.read_bytes(), eq=b"foreign content\n")
            tm.ok((root / "docs").exists())
            tm.ok((root / "docs/generated").exists())
        else:
            tm.that(target.read_bytes(), eq=b"first phase\n")
        tm.that(
            tuple((root / c.Infra.TRANSACTION_STATE_DIRNAME).iterdir()),
            eq=(
                root
                / c.Infra.TRANSACTION_STATE_DIRNAME
                / f"{c.Infra.JOURNAL_NAME}.lock",
            ),
        )
        tm.ok(journal.with_name(f"{journal.name}.lock").is_file())

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("raises", [False, True])
    def test_failed_phase_after_begin_leaves_no_prepared_journal(
        tmp_path: Path,
        *,
        raises: bool,
    ) -> None:
        """A failed phase retires staging while preserving previous publications."""
        root = u.Tests.git_repository(tmp_path)
        u.Tests.copy_tracked_mise_seeds(root)
        owner = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = owner.capability_roots("conform", (root,))
        target = root / "generated.md"
        cause = OSError("docs preparation raised after begin")
        config_path = root / ".mise.toml"
        original = tm.ok(
            u.Cli.atomic_read_binary_file_state(config_path, required=True),
        )
        declared_mode = next(
            item.mode
            for item in config.Infra.codegen.managed_files
            if item.path == Path(config_path.name)
        )
        desired_mode = declared_mode ^ stat.S_IWGRP

        def failing_phase(
            _session: m.Infra.CodegenTransactionSession,
        ) -> p.Result[bool]:
            tm.that(target.read_bytes(), eq=b"prepared phase\n")
            tm.that(stat.S_IMODE(config_path.stat().st_mode), eq=desired_mode)
            if raises:
                raise cause
            return r[bool].fail("docs preparation failed after begin")

        def publish(scope_root: Path) -> p.Result[bool]:
            before = tm.ok(
                u.Cli.atomic_read_binary_file_state(config_path, required=True),
            )
            config_plan = m.Infra.CodegenFilePlan(
                project=root,
                path=config_path,
                before=before,
                desired_content=before.content,
                desired_mode=desired_mode,
                owner="mise",
            )
            generated = m.Infra.CodegenFilePlan(
                project=root,
                path=target,
                before=tm.ok(
                    u.Cli.atomic_read_binary_file_state(target, required=False),
                ),
                desired_content=b"prepared phase\n",
                desired_mode=before.mode,
                owner="conform",
            )
            session = tm.ok(
                owner.begin_files_locked(scope_root, roots, ()),
            )
            session = tm.ok(
                owner.append_phase_locked(
                    session,
                    c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP,
                    (config_plan, generated),
                ),
            )
            return owner.publish_prepared_locked(session, failing_phase)

        if raises:
            with pytest.raises(OSError, match="raised after begin") as failure:
                owner.run_files_locked(roots, publish)
            tm.ok(failure.value is cause)
        else:
            tm.fail(
                owner.run_files_locked(roots, publish),
                has="docs preparation failed after begin",
            )
        identity = tm.ok(u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=root)))
        tm.that(
            FlextInfraMiseWorkspacePlanner.journal_path(identity).exists(),
            eq=False,
        )
        tm.that(target.read_bytes(), eq=b"prepared phase\n")
        restored = tm.ok(
            u.Cli.atomic_read_binary_file_state(config_path, required=True),
        )
        tm.that((restored.content, restored.mode), eq=(original.content, desired_mode))
        tm.ok(owner.run_locked(prepare=True, operation=r[Path].ok))

    @staticmethod
    def test_appended_phase_rejects_replaced_created_parent(
        tmp_path: Path,
    ) -> None:
        """Never adopt a foreign parent while staging a previously absent file."""
        root = u.Tests.git_repository(tmp_path)
        u.Tests.copy_tracked_mise_seeds(root)
        owner = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = owner.capability_roots("docs", (root,))
        target = root / "docs/generated/readme.md"
        preserved = root / "original-generated"

        def replace_parent(
            scope_root: Path,
        ) -> p.Result[m.Infra.CodegenTransactionSession]:
            config_path = root / ".mise.toml"
            before = tm.ok(
                u.Cli.atomic_read_binary_file_state(config_path, required=True),
            )
            config_plan = m.Infra.CodegenFilePlan(
                project=root,
                path=config_path,
                before=before,
                desired_content=before.content,
                desired_mode=before.mode,
                owner="mise",
            )
            session = tm.ok(
                owner.begin_files_locked(scope_root, roots, ()),
            )
            session = tm.ok(
                owner.append_phase_locked(
                    session, c.Infra.CodegenStagedFilePhase.MISE, (config_plan,)
                ),
            )
            planned = m.Infra.CodegenFilePlan(
                project=root,
                path=target,
                before=tm.ok(u.Infra.codegen_target_snapshot(target)),
                desired_content=b"owned content\n",
                desired_mode=before.mode,
                owner="docs",
            )
            session = tm.ok(owner.bind_publication_proof(session, (planned,)))
            session = tm.ok(
                owner.append_directories_locked(session, "docs", (target.parent,)),
            )
            target.parent.rename(preserved)
            target.parent.mkdir()
            return owner.append_phase_locked(session, "docs", (planned,))

        failed = owner.run_files_locked(roots, replace_parent)

        tm.fail(failed, has="generation source parent identity changed")
        tm.fail(target.exists())
        tm.ok(target.parent.is_dir())
        tm.ok(preserved.is_dir())

    def test_file_begin_preserves_residue_created_after_reconciliation(
        self,
        tmp_path: Path,
    ) -> None:
        """A held lease never grants ownership of newly appearing staging."""
        root = u.Tests.git_repository(tmp_path)
        u.Tests.copy_tracked_mise_seeds(root)
        mise_owner = FlextInfraCodegenMiseArtifacts(repository_root=root)
        owner = FlextInfraCodegenTransaction(mise_owner)
        roots = owner.capability_roots("conform", (root,))
        layout = tm.ok(
            FlextInfraMiseWorkspacePlanner(mise_owner).file_layout(
                root.resolve(),
                roots,
                transaction_id=self._TRANSACTION_ID,
            ),
        )
        residue = layout.file_participants[0].transaction_root

        def begin_after_reconciliation(
            scope_root: Path,
        ) -> p.Result[m.Infra.CodegenTransactionSession]:
            residue.mkdir(parents=True)
            (residue / "orphan").write_bytes(b"journal-less staging")
            return owner.begin_files_locked(scope_root, roots, ())

        tm.fail(
            owner.run_files_locked(roots, begin_after_reconciliation),
            has="file transaction has unowned staging residue",
        )
        tm.that((residue / "orphan").read_bytes(), eq=b"journal-less staging")

    @pytest.mark.parametrize("unregistered_child", [False, True])
    def test_reconciliation_never_adopts_unjournaled_trees(
        self,
        tmp_path: Path,
        *,
        unregistered_child: bool,
    ) -> None:
        """Unregistered children are outside scope; in-scope residue fails closed."""
        root = u.Tests.git_repository(tmp_path)
        owner = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        participant = root / "unregistered" if unregistered_child else root
        participant.mkdir(exist_ok=True)
        layout = tm.ok(
            FlextInfraMiseWorkspacePlanner(
                FlextInfraCodegenMiseArtifacts(repository_root=root),
            ).file_layout(
                root,
                {"@docs-0": participant},
                transaction_id=self._TRANSACTION_ID,
            ),
        )
        residue = layout.file_participants[0].transaction_root
        residue.mkdir(parents=True)
        marker = residue / "foreign.bin"
        marker.write_bytes(b"not transaction-owned")
        before = tm.ok(u.Cli.atomic_read_binary_file_state(marker, required=True))

        result = owner.run_locked(prepare=True, operation=r[Path].ok)

        if unregistered_child:
            tm.ok(result)
        else:
            tm.fail(result, has="no journal authority")
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(marker, required=True)),
            eq=before,
        )

    @staticmethod
    @pytest.mark.parametrize("with_foreign_file", [False, True])
    def test_phase_failure_preserves_preexisting_staging_root(
        tmp_path: Path,
        *,
        with_foreign_file: bool,
    ) -> None:
        """Failure to create a phase root cannot authorize deleting that root."""
        root = u.Tests.git_repository(tmp_path)
        owner = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = {"@docs-0": root}
        target = root / "generated.md"

        def stage(scope_root: Path) -> p.Result[m.Infra.CodegenTransactionSession]:
            session = tm.ok(owner.begin_files_locked(scope_root, roots, ()))
            phase_root = (
                session.plan.layout.file_participants[0].transaction_root / "phase-docs"
            )
            phase_root.mkdir()
            if with_foreign_file:
                (phase_root / "foreign.bin").write_bytes(b"preserve")
            identity = phase_root.stat()
            planned = m.Infra.CodegenFilePlan(
                project=root,
                path=target,
                before=tm.ok(
                    u.Cli.atomic_read_binary_file_state(target, required=False),
                ),
                desired_content=b"generated\n",
                desired_mode=session.journal_state.mode,
                owner="docs",
            )
            failed = owner.append_phase_locked(session, "docs", (planned,))
            tm.fail(failed)
            tm.that(phase_root.stat().st_ino, eq=identity.st_ino)
            if with_foreign_file:
                tm.that((phase_root / "foreign.bin").read_bytes(), eq=b"preserve")
            tm.ok(session.journal_state.path.exists())
            return failed

        tm.fail(owner.run_files_locked(roots, stage))
        tm.fail(target.exists())

    @staticmethod
    @pytest.mark.parametrize(
        c.ContextScope.OPERATION, [c.MergeStrategy.APPEND, "commit"]
    )
    def test_same_content_journal_replacement_is_not_adopted(
        tmp_path: Path,
        operation: str,
    ) -> None:
        """Full-state CAS rejects a new inode even when journal bytes/mode match."""
        root = u.Tests.git_repository(tmp_path)
        owner = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = {"@docs-0": root}
        target = root / "generated.md"

        def replace_journal(scope_root: Path) -> p.Result[bool]:
            session = tm.ok(owner.begin_files_locked(scope_root, roots, ()))
            journal = session.journal_state.path
            original = journal.with_suffix(".preserved")
            journal.rename(original)
            journal.write_bytes(original.read_bytes())
            journal.chmod(original.stat().st_mode)
            replacement = tm.ok(
                u.Cli.atomic_read_binary_file_state(journal, required=True),
            )
            if operation == c.MergeStrategy.APPEND:
                planned = m.Infra.CodegenFilePlan(
                    project=root,
                    path=target,
                    before=tm.ok(
                        u.Cli.atomic_read_binary_file_state(target, required=False),
                    ),
                    desired_content=b"generated\n",
                    desired_mode=session.journal_state.mode,
                    owner="docs",
                )
                failed = owner.publish_prepared_locked(
                    session,
                    lambda current: owner.append_phase_locked(
                        current, "docs", (planned,)
                    ),
                )
                tm.fail(failed, has="atomic file physical state changed")
                tm.that(
                    failed.exception,
                    is_=OSError,
                    attr_eq={"errno": errno.ESTALE},
                )
            else:
                tm.fail(
                    owner.publish_prepared_locked(
                        session,
                        owner.commit_locked,
                    ),
                    has="journal changed",
                )
            tm.that(
                tm.ok(u.Cli.atomic_read_binary_file_state(journal, required=True)),
                eq=replacement,
            )
            tm.that(original.read_bytes(), eq=replacement.content)
            return r[bool].ok(value=True)

        tm.ok(owner.run_files_locked(roots, replace_journal))
        tm.fail(target.exists())


class TestsFlextInfraTransactionDirectoryCleanup:
    """Exercise physical cleanup without conflating it with journal publication."""

    @staticmethod
    def _layout(root: Path) -> m.Infra.MiseToolchainWorkspaceLayout:
        root.mkdir()
        u.Tests.initialize_git_repo(root)
        (root / "bin").mkdir()
        owner = FlextInfraCodegenMiseArtifacts(
            repository_root=root,
            apply_changes=True,
            check_only=False,
        )
        planned = FlextInfraMiseWorkspacePlanner(owner).layout_from_selectors(
            root.resolve(),
            (".",),
            transaction_id=uuid4().hex,
        )
        return tm.ok(planned)

    @staticmethod
    def _journal(
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        directories: t.VariadicTuple[m.Infra.CodegenJournalDirectory],
    ) -> m.Infra.CodegenTransactionJournal:
        physical = layout.scope_root.lstat()
        return m.Infra.CodegenTransactionJournal(
            version=9,
            transaction_id=tm.not_none(layout.transaction_id),
            scope_device=physical.st_dev,
            scope_inode=physical.st_ino,
            state="prepared",
            projects=(
                m.Infra.CodegenJournalProject(
                    selector=".",
                    device=physical.st_dev,
                    inode=physical.st_ino,
                ),
            ),
            sources=(),
            directories=directories,
            entries=(),
        )

    @staticmethod
    def _materialize(
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        directories: t.VariadicTuple[m.Infra.CodegenJournalDirectory],
    ) -> t.VariadicTuple[m.Infra.CodegenJournalDirectory]:
        current = directories
        for intent in directories:
            created = tm.ok(
                FlextInfraMiseArtifactsState.create_journaled_directory(
                    layout,
                    current,
                    intent,
                ),
            )
            current = tuple(
                created if entry.path == intent.path else entry for entry in current
            )
        return current

    @classmethod
    def _register_manifest(
        cls,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        directories: t.VariadicTuple[m.Infra.CodegenJournalDirectory],
    ) -> m.Infra.CodegenTransactionJournal:
        journal = cls._journal(layout, directories)
        registered = tm.ok(
            FlextInfraMiseArtifactsVerification.register_transaction_manifests(
                layout,
                journal,
            ),
        )
        recorded: m.Infra.CodegenTransactionJournal = tm.ok(
            FlextInfraMiseArtifactsJournal.record_directories(journal, registered),
        )
        return recorded

    def test_temporary_tree_is_journaled_before_creation_and_removed(
        self,
        tmp_path: Path,
    ) -> None:
        """Remove arbitrary regular staging files and every newly created parent."""
        layout = self._layout(tmp_path / "repository")

        planned = FlextInfraMiseArtifactsState.plan_transaction_directories(layout)

        directories = tm.ok(planned)
        tm.fail((layout.scope_root / ".state").exists())
        directories = self._materialize(layout, directories)
        transaction_root = tm.not_none(layout.projects[0].transaction_root)
        (transaction_root / "partial-download").write_bytes(b"owned staging bytes")
        journal = self._register_manifest(layout, directories)

        cleaned = FlextInfraMiseArtifactsState.cleanup_journaled_directories(
            layout,
            journal,
            include_generated=True,
        )

        tm.ok(cleaned, eq=True)
        tm.fail(transaction_root.exists())
        tm.fail(layout.state_root.exists())

    def test_nonempty_generated_directory_is_preserved_and_rejected(
        self,
        tmp_path: Path,
    ) -> None:
        """Never infer ownership for an unexpected file in a live generated path."""
        layout = self._layout(tmp_path / "repository")
        target = layout.scope_root / "docs" / "generated"
        planned = FlextInfraMiseArtifactsState.plan_directories(
            layout,
            phase="docs",
            requested=(target,),
            disposition="generated",
        )
        directories = tm.ok(planned)
        directories = self._materialize(layout, directories)
        foreign = target / "foreign.txt"
        foreign.write_text("not journaled", encoding="utf-8")

        cleaned = FlextInfraMiseArtifactsState.cleanup_journaled_directories(
            layout,
            self._journal(layout, directories),
            include_generated=True,
        )

        tm.fail(cleaned)
        tm.that(foreign.read_text(encoding="utf-8"), eq="not journaled")

    @pytest.mark.skipif(os.name == "nt", reason="fixture symlink needs privilege")
    def test_transaction_symlink_is_preserved_and_rejected(
        self,
        tmp_path: Path,
    ) -> None:
        """Reject a transaction tree whose topology contains an alias."""
        layout = self._layout(tmp_path / "repository")
        directories = tm.ok(
            FlextInfraMiseArtifactsState.plan_transaction_directories(layout),
        )
        directories = self._materialize(layout, directories)
        transaction_root = tm.not_none(layout.projects[0].transaction_root)
        journal = self._register_manifest(layout, directories)
        (transaction_root / "alias").symlink_to(layout.scope_root)

        cleaned = FlextInfraMiseArtifactsState.cleanup_journaled_directories(
            layout,
            journal,
            include_generated=True,
        )

        tm.fail(cleaned)
        tm.ok((transaction_root / "alias").is_symlink())

    def test_replaced_generated_directory_identity_is_preserved_and_rejected(
        self,
        tmp_path: Path,
    ) -> None:
        """Never delete a new empty inode placed at a journaled pathname."""
        layout = self._layout(tmp_path / "repository")
        target = layout.scope_root / "docs" / "generated"
        directories = tm.ok(
            FlextInfraMiseArtifactsState.plan_directories(
                layout,
                phase="docs",
                requested=(target,),
                disposition="generated",
            ),
        )
        directories = self._materialize(layout, directories)
        original = layout.scope_root / "original-generated"
        target.rename(original)
        target.mkdir()

        cleaned = FlextInfraMiseArtifactsState.cleanup_journaled_directories(
            layout,
            self._journal(layout, directories),
            include_generated=True,
        )

        tm.fail(cleaned)
        tm.ok(target.is_dir())
        tm.ok(original.is_dir())

    def test_foreign_file_after_manifest_is_preserved_and_rejected(
        self,
        tmp_path: Path,
    ) -> None:
        """Reject an unregistered descendant before applying any delete."""
        layout = self._layout(tmp_path / "repository")
        directories = self._materialize(
            layout,
            tm.ok(FlextInfraMiseArtifactsState.plan_transaction_directories(layout)),
        )
        journal = self._register_manifest(layout, directories)
        transaction_root = tm.not_none(layout.projects[0].transaction_root)
        foreign = transaction_root / "foreign.bin"
        foreign.write_bytes(b"foreign")

        cleaned = FlextInfraMiseArtifactsState.cleanup_journaled_directories(
            layout,
            journal,
            include_generated=True,
        )

        tm.fail(cleaned, has="unregistered")
        tm.that(foreign.read_bytes(), eq=b"foreign")

    def test_missing_registered_temporary_file_preserves_tree_and_fails(
        self,
        tmp_path: Path,
    ) -> None:
        """Do not normalize disappearance of a non-consumable journaled file."""
        layout = self._layout(tmp_path / "repository")
        directories = self._materialize(
            layout,
            tm.ok(FlextInfraMiseArtifactsState.plan_transaction_directories(layout)),
        )
        transaction_root = tm.not_none(layout.projects[0].transaction_root)
        payload = transaction_root / "registered.bin"
        payload.write_bytes(b"registered")
        journal = self._register_manifest(layout, directories)
        payload.unlink()

        cleaned = FlextInfraMiseArtifactsState.cleanup_journaled_directories(
            layout,
            journal,
            include_generated=True,
        )

        tm.fail(cleaned, has="missing")
        tm.ok(transaction_root.is_dir())

    def test_crash_before_identity_persistence_preserves_unbound_tree(
        self,
        tmp_path: Path,
    ) -> None:
        """Never infer ownership from a pathname after the creation crash window."""
        layout = self._layout(tmp_path / "repository")
        directories = tm.ok(
            FlextInfraMiseArtifactsState.plan_transaction_directories(layout),
        )
        transaction_root = tm.not_none(layout.projects[0].transaction_root)
        transaction_root.mkdir(parents=True)
        marker = transaction_root / "unknown-owner.bin"
        marker.write_bytes(b"preserve")

        cleaned = FlextInfraMiseArtifactsState.cleanup_journaled_directories(
            layout,
            self._journal(layout, directories),
            include_generated=True,
        )

        tm.fail(cleaned, has="not journaled")
        tm.that(marker.read_bytes(), eq=b"preserve")
