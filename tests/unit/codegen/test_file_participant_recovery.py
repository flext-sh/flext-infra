"""Public recovery behavior for file-only transaction participants.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from flext_infra.codegen import (
    FlextInfraMiseArtifactsFiles,
    FlextInfraMiseArtifactsJournal,
    FlextInfraMisePublication,
)
from flext_infra.codegen.codegen_transaction import FlextInfraCodegenTransaction
from flext_infra.codegen.mise_artifacts import FlextInfraCodegenMiseArtifacts
from flext_infra.validate import FlextInfraValidateFreshImport
from tests import c, m, p, r, t, tm, u


class TestsFlextInfraFileParticipantRecovery:
    """Recover prepared file-only journals through their physical owners."""

    @staticmethod
    def _injected_validator_verdict(
        failure_kind: str,
        cause: RuntimeError,
        current: m.Infra.CodegenTransactionSession,
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Inject the parametrized validator failure into the staged phase.

        Args:
            failure_kind: The parametrized failure injection kind.
            cause: The explicit rejection cause.
            current: The staged session admitted when no failure applies.

        Returns:
            The validator verdict for the staged session.

        """
        if failure_kind == "exception":
            raise cause
        if failure_kind == "validator":
            return r[m.Infra.CodegenTransactionSession].fail(
                str(cause), exception=cause
            )
        return r[m.Infra.CodegenTransactionSession].ok(current)

    @staticmethod
    def _replaced_report_directory(root: Path) -> None:
        """Replace the publication receipt archive with a same-named file.

        Args:
            root: Repository root owning the publication receipt archive.

        """
        archive = root / c.Infra.CODEGEN_PUBLICATION_ARCHIVE_RELATIVE_PATH
        shutil.rmtree(archive)
        archive.write_bytes(b"")

    @staticmethod
    def _corrupted_journal_state(
        journal: Path,
        journal_change: str,
    ) -> m.Cli.AtomicFileState | None:
        """Corrupt the journaled authority per the parametrized change kind.

        Args:
            journal: The transaction journal file path.
            journal_change: The parametrized journal corruption kind.

        Returns:
            The observed journal state after the corruption, or ``None`` when
            the journal path became a directory.

        """
        saved = journal.with_suffix(".preserved")
        if journal_change != "unchanged":
            journal.rename(saved)
        if journal_change == "replaced":
            journal.write_bytes(saved.read_bytes())
            journal.chmod(saved.stat().st_mode)
        if journal_change == "directory":
            journal.mkdir()
            return None
        return tm.ok(u.Cli.atomic_read_binary_file_state(journal, required=False))

    @staticmethod
    def _validate_failed_publication(
        session: m.Infra.CodegenTransactionSession,
        failure_kind: str,
        cause: RuntimeError,
    ) -> p.Result[bool]:
        """Exercise native rejection, journal replacement, or unowned cleanup bytes.

        Returns:
            The consumer verdict, leaving real settlement faults for the transaction.

        """
        if failure_kind == "cleanup":
            participant = session.plan.layout.file_participants[0]
            (participant.transaction_root / "foreign.bin").write_bytes(b"foreign\n")
        if failure_kind == "settlement":
            journal = session.journal_state.path
            saved = journal.with_suffix(".preserved")
            journal.rename(saved)
            journal.write_bytes(saved.read_bytes())
            journal.chmod(saved.stat().st_mode)
        if failure_kind == "exception":
            raise cause
        if failure_kind == "validator":
            return r[bool].fail(str(cause), exception=cause)
        return r[bool].ok(value=True)

    @staticmethod
    @pytest.mark.parametrize(
        "failure_kind",
        ["target", "validator", "exception", "settlement", "cleanup", "evidence"],
    )
    @pytest.mark.parametrize("deleted", [False, True])
    def test_failed_commit_exports_only_authenticated_retained_effects(
        tmp_path: Path,
        failure_kind: str,
        *,
        deleted: bool,
    ) -> None:
        """Failure preserves admitted correspondence without claiming acceptance."""
        root = u.Tests.git_repository(tmp_path)
        owner = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = {"@semantic": root}
        targets = (root / "first.py", root / "second.py")
        for target in targets:
            target.write_bytes(b"before\n")
        originals = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
            for target in targets
        )
        receipts: list[m.Infra.CodegenStagedFile] = []
        cause = RuntimeError("explicit consumer rejection")

        def publish(scope: Path) -> p.Result[t.VariadicTuple[Path]]:
            session = tm.ok(owner.begin_files_locked(scope, roots, ()))
            plans = tuple(
                m.Infra.CodegenFilePlan(
                    project=root,
                    path=before.path,
                    before=before,
                    desired_content=None if deleted else b"after\n",
                    desired_mode=None if deleted else before.mode,
                    owner="semantic",
                )
                for before in originals
            )

            def staged(
                current: m.Infra.CodegenTransactionSession,
                _files: t.VariadicTuple[m.Infra.CodegenStagedFile],
            ) -> p.Result[m.Infra.CodegenTransactionSession]:
                return (
                    TestsFlextInfraFileParticipantRecovery._injected_validator_verdict(
                        failure_kind, cause, current
                    )
                )

            appended = owner.append_phase_locked(
                session,
                "semantic",
                plans,
                publication_policy=m.Infra.CodegenPhasePublicationPolicy(
                    directories=(), staged_validator=staged
                ),
            )
            if appended.failure:
                return r[t.VariadicTuple[Path]].from_failure(appended)
            session = appended.value
            if failure_kind == "target":
                targets[1].write_bytes(b"concurrent\n")
            if failure_kind == "evidence":
                TestsFlextInfraFileParticipantRecovery._replaced_report_directory(
                    root,
                )

            tm.ok(
                TestsFlextInfraFileParticipantRecovery._validate_failed_publication(
                    session, failure_kind, cause
                )
            )
            return owner.commit_locked(session, published_files=receipts)

        if failure_kind == "exception":
            with pytest.raises(RuntimeError) as raised:
                owner.run_files_locked(roots, publish)
            tm.that(raised.value is cause, eq=True)
        else:
            failed = owner.run_files_locked(roots, publish)
            tm.fail(failed)
            if failure_kind == "validator":
                tm.that(failed.exception is cause, eq=True)
        TestsFlextInfraFileParticipantRecovery._verified_retained_receipts(
            receipts, originals, targets, failure_kind, deleted=deleted
        )

    @staticmethod
    def test_failed_append_preserves_independent_effect_and_concurrent_target(
        tmp_path: Path,
    ) -> None:
        """A rejected append preserves its gain and the exact foreign input."""
        root = u.Tests.git_repository(tmp_path)
        owner = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = {"@semantic": root}
        targets = (root / "first.py", root / "second.py")
        for target in targets:
            target.write_bytes(b"before\n")
        originals = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
            for target in targets
        )
        observed: list[m.Cli.AtomicFileState] = []
        foreign: list[m.Cli.AtomicFileState] = []

        def publish(scope: Path) -> p.Result[t.VariadicTuple[Path]]:
            session = tm.ok(owner.begin_files_locked(scope, roots, ()))
            plans = tuple(
                m.Infra.CodegenFilePlan(
                    project=root,
                    path=before.path,
                    before=before,
                    desired_content=b"after\n",
                    desired_mode=before.mode,
                    owner="semantic",
                )
                for before in originals
            )

            def staged(
                current: m.Infra.CodegenTransactionSession,
                _files: t.VariadicTuple[m.Infra.CodegenStagedFile],
            ) -> p.Result[m.Infra.CodegenTransactionSession]:
                targets[1].write_bytes(b"concurrent\n")
                foreign.append(
                    tm.ok(
                        u.Cli.atomic_read_binary_file_state(targets[1], required=True)
                    )
                )
                return r[m.Infra.CodegenTransactionSession].ok(current)

            appended = owner.append_phase_locked(
                session,
                "semantic",
                plans,
                publication_policy=m.Infra.CodegenPhasePublicationPolicy(
                    directories=(), staged_validator=staged
                ),
            )
            tm.fail(appended)
            observed.extend(
                tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
                for target in targets
            )
            return r[t.VariadicTuple[Path]].from_failure(appended)

        tm.fail(owner.run_files_locked(roots, publish))
        tm.that(observed[0].content, eq=b"after\n")
        tm.that(observed[0].mode, eq=originals[0].mode)
        tm.that(observed[0].parent_device, eq=originals[0].parent_device)
        tm.that(observed[0].parent_inode, eq=originals[0].parent_inode)
        tm.that(observed[1], eq=foreign[0])
        for target, expected in zip(targets, observed, strict=True):
            tm.that(
                tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True)),
                eq=expected,
            )
        tm.that(tm.ok(owner.inspect_journal()).journal_state, eq="prepared")

    @staticmethod
    def _verified_retained_receipts(
        receipts: list[m.Infra.CodegenStagedFile],
        originals: tuple[m.Cli.AtomicFileState, ...],
        targets: tuple[Path, ...],
        failure_kind: str,
        *,
        deleted: bool,
    ) -> None:
        """Assert the retained receipts match their authenticated originals.

        Args:
            receipts: The retained publication receipts of the failed commit.
            originals: The authenticated pre-publication states of the targets.
            targets: The governed publication target paths.
            failure_kind: The parametrized failure injection kind.
            deleted: Whether the publication planned deletions.

        """
        expected = (
            ()
            if failure_kind in {"validator", "exception"}
            else targets[:1]
            if failure_kind == "target"
            else targets
        )
        tm.that(tuple(receipt.before.path for receipt in receipts), eq=expected)
        for receipt in receipts:
            tm.that(receipt.before, eq=originals[targets.index(receipt.before.path)])
            current = tm.ok(
                u.Cli.atomic_read_binary_file_state(
                    receipt.before.path,
                    required=not deleted,
                )
            )
            if deleted:
                tm.that(current.content, eq=None)
                tm.that(receipt.replacement, eq=None)
            else:
                tm.that(receipt.replacement, eq=current)

    @staticmethod
    @pytest.mark.parametrize("drift", ["none", "restored", "same-bytes"])
    def test_rejected_commit_exports_only_live_endpoint_receipts(
        tmp_path: Path,
        drift: str,
    ) -> None:
        """Restored bytes or a replaced inode cannot authenticate a retained effect."""
        root = u.Tests.git_repository(tmp_path)
        target = root / "source.py"
        target.write_bytes(b"original\n")
        original = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
        owner = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = {"@semantic": root}
        receipts: list[m.Infra.CodegenStagedFile] = []
        current_states: list[m.Cli.AtomicFileState] = []

        def publish(scope: Path) -> p.Result[t.VariadicTuple[Path]]:
            session = tm.ok(owner.begin_files_locked(scope, roots, ()))
            plan = m.Infra.CodegenFilePlan(
                project=root,
                path=target,
                before=original,
                desired_content=b"final\n",
                desired_mode=original.mode,
                owner="semantic",
            )
            session = tm.ok(owner.append_phase_locked(session, "semantic", (plan,)))

            def reject() -> p.Result[bool]:
                if drift != "none":
                    target.rename(target.with_suffix(".preserved"))
                    target.write_bytes(
                        tm.not_none(original.content)
                        if drift == "restored"
                        else b"final\n"
                    )
                    target.chmod(tm.not_none(original.mode))
                return r[bool].fail("consumer rejected")

            rejected = reject()
            current_states.append(
                tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
            )
            settled = owner.commit_locked(session, published_files=receipts)
            if drift != "none":
                tm.fail(
                    settled,
                    has="live generation destination differs from staged identity",
                )
                return settled
            tm.ok(settled)
            return r[t.VariadicTuple[Path]].from_failure(rejected)

        tm.fail(
            owner.run_files_locked(roots, publish),
            has="consumer rejected"
            if drift == "none"
            else "live generation destination differs from staged identity",
        )
        tm.that(len(receipts), eq=1 if drift == "none" else 0)
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True)),
            eq=current_states[0],
        )
        if drift == "none":
            tm.that(receipts[0].before, eq=original)
            tm.that(
                receipts[0].replacement,
                eq=tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True)),
            )

    @staticmethod
    def test_late_authored_initializer_is_retained_instead_of_overwritten(
        tmp_path: Path,
    ) -> None:
        """Reelect ownership from the current target before its single write."""
        target = tmp_path / c.Infra.INIT_PY
        target.write_text(f"{c.Infra.AUTOGEN_HEADER}\n", encoding=c.DEFAULT_ENCODING)
        before = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
        replacement = tmp_path / "replacement.py"
        replacement.write_text(
            f"{c.Infra.AUTOGEN_HEADER}\n__all__ = []\n",
            encoding=c.DEFAULT_ENCODING,
        )
        publication = m.Infra.CodegenStagedFile(
            phase=c.Infra.CodegenStagedFilePhase.LAZY_INIT,
            project=tmp_path,
            before=before,
            replacement=tm.ok(
                u.Cli.atomic_read_binary_file_state(replacement, required=True),
            ),
        )
        authored = b"VALUE = 'authored behavior'\n"
        target.write_bytes(authored)

        outcome = tm.ok(FlextInfraMisePublication.publish((publication,)))

        tm.that(outcome.written_files, eq=())
        tm.that(outcome.retained_files, eq=(target,))
        tm.that(outcome.issues, eq=())
        tm.that(target.read_bytes(), eq=authored)

    @staticmethod
    @pytest.mark.parametrize("edit_before_capture", [False, True])
    def test_publication_adopts_current_destination_before_one_write(
        tmp_path: Path,
        *,
        edit_before_capture: bool,
    ) -> None:
        """Publish an elected current input and reject changes after its capture."""
        target = tmp_path / "generated.md"
        target.write_bytes(b"original\n")
        if edit_before_capture:
            target.write_bytes(b"external edit\n")
        before = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
        replacement = tmp_path / "replacement.md"
        replacement.write_bytes(b"generated\n")
        staged = m.Infra.CodegenStagedFile(
            phase=c.Infra.CodegenStagedFilePhase.DOCS,
            project=tmp_path,
            before=before,
            replacement=tm.ok(
                u.Cli.atomic_read_binary_file_state(replacement, required=True),
            ),
        )
        if not edit_before_capture:
            target.write_bytes(b"external edit\n")
        current = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))

        outcome = tm.ok(FlextInfraMisePublication.publish((staged,)))

        if edit_before_capture:
            tm.that(outcome.written_files, eq=(target,))
            tm.that(outcome.issues, eq=())
            tm.that(outcome.published_files, len=1)
            tm.that(outcome.published_files[0].before, eq=before)
            tm.that(
                outcome.published_files[0].replacement,
                eq=tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True)),
            )
            tm.that(target.read_bytes(), eq=b"generated\n")
        else:
            tm.that(outcome.written_files, eq=())
            tm.that(outcome.published_files, eq=())
            tm.that(outcome.issues, len=1)
            tm.that(outcome.issues[0].file, eq=str(target))
            tm.that(outcome.issues[0].code, eq=c.Infra.ToolOutcome.ERROR.value)
            tm.that(
                tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True)),
                eq=current,
            )

    @staticmethod
    def test_publication_reports_failed_target_and_preserves_other_gains(
        tmp_path: Path,
    ) -> None:
        """A rejected physical target does not stop independent publications."""
        publications: list[m.Infra.CodegenStagedFile] = []
        for index in range(3):
            target = tmp_path / f"generated-{index}.md"
            target.write_bytes(b"original\n")
            replacement = tmp_path / f"replacement-{index}.md"
            replacement.write_bytes(b"generated\n")
            publications.append(
                m.Infra.CodegenStagedFile(
                    phase=c.Infra.CodegenStagedFilePhase.DOCS,
                    project=tmp_path,
                    before=tm.ok(
                        u.Cli.atomic_read_binary_file_state(target, required=True),
                    ),
                    replacement=tm.ok(
                        u.Cli.atomic_read_binary_file_state(replacement, required=True),
                    ),
                ),
            )
        rejected = publications[1].before.path
        foreign = tmp_path / "foreign.md"
        foreign.write_bytes(b"preserved\n")
        rejected.unlink()
        rejected.symlink_to(foreign)

        outcome = tm.ok(FlextInfraMisePublication.publish(tuple(publications)))

        tm.that(
            outcome.written_files,
            eq=(publications[0].before.path, publications[2].before.path),
        )
        tm.that(outcome.issues, len=1)
        tm.that(outcome.issues[0].file, eq=str(rejected))
        tm.that(outcome.issues[0].code, eq=c.Infra.ToolOutcome.ERROR.value)
        tm.that(rejected.is_symlink(), eq=True)
        tm.that(foreign.read_bytes(), eq=b"preserved\n")
        for path in outcome.written_files:
            tm.that(path.read_bytes(), eq=b"generated\n")

    @staticmethod
    @pytest.mark.parametrize("invalid_later_plan", ["participant", "destination"])
    def test_later_invalid_plan_leaves_no_partial_staging(
        tmp_path: Path,
        invalid_later_plan: str,
    ) -> None:
        """A rejected phase cannot strand earlier replacements outside its journal."""
        root = u.Tests.git_repository(tmp_path)
        nested = root / "unregistered"
        nested.mkdir()
        first = root / "first.md"
        second = nested / "second.md"
        roots = {"@docs-0": root}
        owner = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )

        def publish(scope: Path) -> p.Result[m.Infra.CodegenTransactionSession]:
            session = tm.ok(owner.begin_files_locked(scope, roots, ()))
            plans = tuple(
                m.Infra.CodegenFilePlan(
                    project=project,
                    path=destination,
                    before=tm.ok(
                        u.Cli.atomic_read_binary_file_state(
                            destination,
                            required=False,
                        ),
                    ),
                    desired_content=b"generated replacement\n",
                    desired_mode=session.journal_state.mode,
                    owner="docs",
                )
                for project, destination in (
                    (root, first),
                    (nested if invalid_later_plan == "participant" else root, second),
                )
            )
            if invalid_later_plan == "destination":
                second.write_bytes(b"concurrent content\n")
            return owner.append_phase_locked(session, "docs", plans)

        failed = owner.run_files_locked(roots, publish)

        tm.fail(
            failed,
            has="no transaction participant"
            if invalid_later_plan == "participant"
            else f"generation output differs from its authenticated preimage: {second}",
        )
        tm.that(first.exists(), eq=False)
        if invalid_later_plan == "destination":
            tm.that(second.read_bytes(), eq=b"concurrent content\n")
        else:
            tm.that(second.exists(), eq=False)
        # A fresh public transaction entry authenticates and reconciles the tree;
        # the previous implementation refuses its unregistered phase directory.
        tm.ok(owner.run_files_locked(roots, lambda _scope: r[bool].ok(value=True)))

    @staticmethod
    def test_fresh_import_failure_rejects_candidate_before_publication(
        tmp_path: Path,
    ) -> None:
        """Reject the complete candidate without publishing an invalid initializer."""
        root = u.Tests.git_repository(tmp_path)
        distribution = "flext-import-probe"
        u.Tests.WorktreeFixture.write_python_project(root, distribution)
        package = root / c.Infra.DEFAULT_SRC_DIR / distribution.replace("-", "_")
        initializer = package / c.Infra.INIT_PY
        header = c.Infra.AUTOGEN_HEADERS[0]
        initializer.write_text(
            f"{header}\n__all__ = ()\n",
            encoding=c.DEFAULT_ENCODING,
        )
        before = tm.ok(u.Cli.atomic_read_binary_file_state(initializer, required=True))
        owner = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = {"@lazy-init": root}
        publication = m.Infra.CodegenFilePlan(
            project=root,
            path=initializer,
            before=before,
            desired_content=(
                f"{header}\n__all__ = ('missing_export',)\n".encode(c.DEFAULT_ENCODING)
            ),
            desired_mode=before.mode,
            owner="lazy-init",
        )
        candidate = owner.preview_sources(
            root,
            {
                initializer: tm.not_none(publication.desired_content).decode(
                    c.DEFAULT_ENCODING
                )
            },
            lambda view_root, _candidate: FlextInfraValidateFreshImport(
                repository_root=view_root,
                packages=(package.name,),
            ).execute(),
            inputs=(before,),
        )
        tm.ok(candidate)
        failed = candidate.value

        tm.fail(failed, has="missing_export")
        tm.that(failed.error, has="Traceback")
        restored = tm.ok(
            u.Cli.atomic_read_binary_file_state(initializer, required=True),
        )
        tm.that(restored, eq=before)
        tm.ok(owner.run_files_locked(roots, lambda _scope: r[bool].ok(value=True)))

    @staticmethod
    def test_recovers_external_only_prepared_journal(tmp_path: Path) -> None:
        """Test recovers external only prepared journal."""
        workspace = u.Tests.create_docs_workspace(tmp_path, project_names=())
        docs_root = tmp_path / "published-docs"
        docs_root.mkdir()
        roots = {"@docs-0": docs_root}
        source = tm.ok(
            u.Cli.atomic_read_binary_file_state(workspace / "README.md", required=True),
        )
        transaction = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=workspace),
        )

        prepared = transaction.run_files_locked(
            roots,
            lambda scope_root: transaction.begin_files_locked(
                scope_root,
                roots,
                (source,),
            ),
        )
        tm.ok(prepared)

        recovered = transaction.run_files_locked(
            roots,
            lambda _scope_root: r[bool].ok(value=True),
        )

        tm.ok(recovered)
        tm.that(recovered.value, eq=True)

    @staticmethod
    @pytest.mark.parametrize("foreign_change", ["none", "extra", "replaced"])
    def test_prepared_publication_recovery_requires_original_tree(
        tmp_path: Path,
        foreign_change: str,
    ) -> None:
        """Recover owned publications, but retain foreign trees and their evidence."""
        root = u.Tests.git_repository(tmp_path)
        owner = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = {"@docs-0": root}
        target = root / "generated.md"

        def prepare(scope_root: Path) -> p.Result[m.Infra.CodegenTransactionSession]:
            session = tm.ok(owner.begin_files_locked(scope_root, roots, ()))
            plan = m.Infra.CodegenFilePlan(
                project=root,
                path=target,
                before=tm.ok(
                    u.Cli.atomic_read_binary_file_state(target, required=False),
                ),
                desired_content=b"owned publication\n",
                desired_mode=session.journal_state.mode,
                owner="docs",
            )
            return owner.append_phase_locked(session, "docs", (plan,))

        session = tm.ok(owner.run_files_locked(roots, prepare))
        staging = session.plan.layout.file_participants[0].transaction_root
        tm.that(target.read_bytes(), eq=b"owned publication\n")
        if foreign_change == "replaced":
            staging.rename(root / "preserved-staging")
            staging.mkdir()
        if foreign_change != "none":
            (staging / "foreign.bin").write_bytes(b"preserve")

        recovered = owner.run_files_locked(roots, lambda _scope: r[bool].ok(value=True))

        if foreign_change == "none":
            tm.ok(recovered)
            tm.that(target.read_bytes(), eq=b"owned publication\n")
            tm.that(staging.exists(), eq=False)
            tm.that(session.journal_state.path.exists(), eq=False)
        else:
            tm.fail(recovered)
            tm.that((staging / "foreign.bin").read_bytes(), eq=b"preserve")
            tm.that(target.read_bytes(), eq=b"owned publication\n")
            tm.that(session.journal_state.path.exists(), eq=True)

    @staticmethod
    @pytest.mark.parametrize("operation", ["replace", "create", "delete"])
    @pytest.mark.parametrize("drift", ["none", "published-inode", "pending-inode"])
    def test_interrupted_group_retirement_preserves_exact_current_destinations(
        tmp_path: Path,
        operation: str,
        drift: str,
    ) -> None:
        """Adopt current inputs without replaying or approving an interrupted group."""
        root = u.Tests.git_repository(tmp_path)
        owner = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = {"@semantic": root}
        targets = (root / "first.py", root / "second.py")
        producer = root / "producer.py"
        producer.write_bytes(b"original producer\n")
        for target in targets:
            if operation != "create" or target != targets[0]:
                target.write_bytes(b"before\n")
        before = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(target, required=False))
            for target in targets
        )
        interrupted: list[m.Infra.CodegenTransactionSession] = []

        def stop_after_first(
            current: m.Infra.CodegenTransactionSession,
            staged: t.VariadicTuple[m.Infra.CodegenStagedFile],
        ) -> p.Result[m.Infra.CodegenTransactionSession]:
            interrupted.append(current)
            published = tm.ok(
                FlextInfraMisePublication.publish(staged[:1], journal=current.journal)
            )
            tm.that(published.written_files, eq=targets[:1])
            message = "interrupted after one guarded publication"
            raise InterruptedError(message)

        def publish(scope: Path) -> p.Result[m.Infra.CodegenTransactionSession]:
            source = tm.ok(u.Cli.atomic_read_binary_file_state(producer, required=True))
            session = tm.ok(owner.begin_files_locked(scope, roots, (source,)))
            plans = tuple(
                m.Infra.CodegenFilePlan(
                    project=root,
                    path=original.path,
                    before=original,
                    desired_content=None if operation == "delete" else b"after\n",
                    desired_mode=(
                        None
                        if operation == "delete"
                        else original.mode
                        if original.mode is not None
                        else session.journal_state.mode
                    ),
                    owner="semantic",
                    dependency_group="interrupted-group",
                )
                for original in before
            )
            return owner.append_phase_locked(
                session,
                "semantic",
                plans,
                publication_policy=m.Infra.CodegenPhasePublicationPolicy(
                    directories=(),
                    staged_validator=stop_after_first,
                ),
            )

        with pytest.raises(InterruptedError, match="one guarded publication"):
            owner.run_files_locked(roots, publish)
        session = interrupted[0]
        producer.write_bytes(b"current producer\n")
        observed = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(target, required=False))
            for target in targets
        )
        tm.that(observed[0].content, eq=None if operation == "delete" else b"after\n")
        tm.that(observed[1], eq=before[1])
        if drift != "none":
            target = targets[0 if drift == "published-inode" else 1]
            original = observed[targets.index(target)]
            if original.content is not None:
                target.rename(target.with_suffix(".preserved"))
            target.write_bytes(
                original.content if original.content is not None else b"foreign\n"
            )
            target.chmod(
                tm.not_none(
                    original.mode
                    if original.mode is not None
                    else session.journal_state.mode
                )
            )
        retained = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(target, required=False))
            for target in targets
        )
        recovered = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        ).run_files_locked(roots, lambda _scope: r[bool].ok(value=True))
        tm.ok(recovered)
        tm.that(session.journal_state.path.exists(), eq=False)
        tm.that(
            session.plan.layout.file_participants[0].transaction_root.exists(),
            eq=False,
        )
        for target, expected in zip(targets, retained, strict=True):
            tm.that(
                tm.ok(u.Cli.atomic_read_binary_file_state(target, required=False)),
                eq=expected,
            )
        tm.that(producer.read_bytes(), eq=b"current producer\n")

    @staticmethod
    def test_proposal_cleanup_rejects_replaced_current_input_before_any_cleanup(
        tmp_path: Path,
    ) -> None:
        """A captured input's replacement preserves staging and journal authority."""
        root = u.Tests.git_repository(tmp_path)
        target = root / "generated.py"
        owner = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = {"@semantic": root}

        def reject_cleanup(scope: Path) -> p.Result[bool]:
            session = tm.ok(owner.begin_files_locked(scope, roots, ()))
            plan = m.Infra.CodegenFilePlan(
                project=root,
                path=target,
                before=tm.ok(
                    u.Cli.atomic_read_binary_file_state(target, required=False)
                ),
                desired_content=b"published\n",
                desired_mode=session.journal_state.mode,
                owner="semantic",
            )
            session = tm.ok(owner.append_phase_locked(session, "semantic", (plan,)))
            captured = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
            target.rename(target.with_suffix(".preserved"))
            target.write_bytes(tm.not_none(captured.content))
            target.chmod(tm.not_none(captured.mode))
            current = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
            tm.fail(
                FlextInfraMiseArtifactsJournal.cleanup(
                    session.plan.layout,
                    session.journal,
                    session.journal_state,
                    preserved_states=(captured,),
                ),
                has="generation authenticated state changed",
            )
            tm.that(session.journal_state.path.exists(), eq=True)
            tm.that(
                session.plan.layout.file_participants[0].transaction_root.exists(),
                eq=True,
            )
            tm.that(
                tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True)),
                eq=current,
            )
            return r[bool].ok(value=True)

        tm.ok(owner.run_files_locked(roots, reject_cleanup))

    @staticmethod
    def test_explicit_group_failure_preserves_first_cause_and_foreign_destination(
        tmp_path: Path,
    ) -> None:
        """Compensate the rejected group without consuming another writer's bytes."""
        root = u.Tests.git_repository(tmp_path)
        targets = (root / "first.py", root / "second.py")
        for target in targets:
            target.write_bytes(b"before\n")
        originals = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
            for target in targets
        )
        owner = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = {"@semantic": root}
        foreign: list[m.Cli.AtomicFileState] = []
        compensated: list[m.Cli.AtomicFileState] = []
        failures: list[p.FailureLike] = []

        def change_second(
            current: m.Infra.CodegenTransactionSession,
            _staged: t.VariadicTuple[m.Infra.CodegenStagedFile],
        ) -> p.Result[m.Infra.CodegenTransactionSession]:
            targets[1].write_bytes(b"foreign writer\n")
            foreign.append(
                tm.ok(u.Cli.atomic_read_binary_file_state(targets[1], required=True))
            )
            return r[m.Infra.CodegenTransactionSession].ok(current)

        def publish(scope: Path) -> p.Result[t.VariadicTuple[Path]]:
            session = tm.ok(owner.begin_files_locked(scope, roots, ()))
            plans = tuple(
                m.Infra.CodegenFilePlan(
                    project=root,
                    path=original.path,
                    before=original,
                    desired_content=b"after\n",
                    desired_mode=original.mode,
                    owner="semantic",
                    dependency_group="explicit-failure-group",
                )
                for original in originals
            )
            appended = owner.append_phase_locked(
                session,
                "semantic",
                plans,
                publication_policy=m.Infra.CodegenPhasePublicationPolicy(
                    directories=(),
                    staged_validator=change_second,
                ),
            )
            tm.fail(appended, has=str(targets[1]))
            failures.append(appended)
            tm.that(targets[0].read_bytes(), eq=originals[0].content)
            current = tm.ok(
                u.Cli.atomic_read_binary_file_state(targets[0], required=True)
            )
            journal, _snapshot = tm.ok(
                FlextInfraMiseArtifactsJournal.read(session.plan.layout)
            )
            entry = next(
                item
                for item in journal.entries
                if tm.ok(
                    FlextInfraMiseArtifactsFiles.resolve_transaction(
                        session.plan.layout,
                        item.path,
                        purpose="compensated group destination",
                    )
                )
                == targets[0]
            )
            backup = tm.ok(
                FlextInfraMiseArtifactsFiles.resolve_transaction(
                    session.plan.layout,
                    tm.not_none(entry.original_staging),
                    purpose="compensated group preimage",
                )
            )
            intent = next(
                intent
                for intent in journal.staging_intents
                if intent.before.path == backup
            )
            receipt = tm.not_none(intent.created)
            tm.that(
                (
                    current.device,
                    current.inode,
                    current.mode,
                    current.link_count,
                    current.file_attributes,
                    current.reparse_tag,
                ),
                eq=(
                    receipt.device,
                    receipt.inode,
                    receipt.mode,
                    receipt.link_count,
                    receipt.file_attributes,
                    receipt.reparse_tag,
                ),
            )
            compensated.append(current)
            tm.that(
                tm.ok(u.Cli.atomic_read_binary_file_state(targets[1], required=True)),
                eq=foreign[0],
            )
            tm.that(entry.recover_group, eq=True)
            tm.that(session.journal_state.path.exists(), eq=True)
            tm.that(
                session.plan.layout.file_participants[0].transaction_root.exists(),
                eq=True,
            )
            return r[t.VariadicTuple[Path]].from_failure(appended)

        failed = owner.run_files_locked(roots, publish)
        tm.fail(failed)
        tm.that(failed.exception is failures[0].exception, eq=True)
        tm.that(failed.error, eq=failures[0].error)
        tm.that(tm.ok(owner.inspect_journal()).journal_state, eq="prepared")
        recovered = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        tm.ok(recovered.run_files_locked(roots, lambda _scope: r[bool].ok(value=True)))
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(targets[0], required=True)),
            eq=compensated[0],
        )
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(targets[1], required=True)),
            eq=foreign[0],
        )
        tm.that(tm.ok(recovered.inspect_journal()).journal_state, eq="absent")

    @staticmethod
    def test_owned_cleanup_rejects_a_different_transaction_layout(
        tmp_path: Path,
    ) -> None:
        """A foreign cleanup capability cannot retire the owned staging receipt."""
        root = u.Tests.git_repository(tmp_path)
        owner = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = {"@docs-0": root}
        live = root / "source.txt"
        live.write_text("preserve", encoding=c.DEFAULT_ENCODING)
        modified_ns = live.stat().st_mtime_ns

        def exercise(scope_root: Path) -> p.Result[bool]:
            session = tm.ok(owner.begin_files_locked(scope_root, roots, ()))
            layout = session.plan.layout
            identifier = tm.not_none(layout.transaction_id)
            other_identifier = ("0" if identifier[0] != "0" else "1") + identifier[1:]
            foreign = session.model_copy(
                update={
                    "plan": session.plan.model_copy(
                        update={
                            "layout": layout.model_copy(
                                update={"transaction_id": other_identifier},
                            ),
                        },
                    ),
                },
            )
            failure = r[bool].fail("consumer failed")
            rejected = owner.abort_locked(foreign, failure)
            tm.fail(rejected)
            tm.that(session.journal_state.path.is_file(), eq=True)
            tm.that(live.read_text(encoding=c.DEFAULT_ENCODING), eq="preserve")
            tm.that(live.stat().st_mtime_ns, eq=modified_ns)
            retired = owner.abort_locked(session, failure)
            tm.fail(retired)
            tm.that(session.journal_state.path.exists(), eq=False)
            return r[bool].ok(value=True)

        tm.ok(owner.run_files_locked(roots, exercise))
        tm.ok(
            owner.run_files_locked(
                roots,
                lambda _scope: r[bool].ok(value=True),
                prepare=False,
            ),
        )
        tm.that(live.read_text(encoding=c.DEFAULT_ENCODING), eq="preserve")
        tm.that(live.stat().st_mtime_ns, eq=modified_ns)

    @staticmethod
    @pytest.mark.parametrize("with_foreign_file", [False, True])
    @pytest.mark.parametrize("journal_state", ["staging", "prepared"])
    def test_unmanifested_created_directory_owns_no_descendants(
        tmp_path: Path,
        journal_state: str,
        *,
        with_foreign_file: bool,
    ) -> None:
        """A pre-manifest crash receipt permits only exact empty-directory cleanup."""
        root = u.Tests.git_repository(tmp_path)
        owner = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = {"@docs-0": root}
        session = tm.ok(
            owner.run_files_locked(
                roots,
                lambda scope: owner.begin_files_locked(scope, roots, ()),
            ),
        )
        staging = session.plan.layout.file_participants[0].transaction_root
        crash_journal = m.Infra.CodegenTransactionJournal.model_validate({
            **session.journal.model_dump(),
            "state": journal_state,
            "directories": tuple(
                {**entry.model_dump(), "manifest": None}
                for entry in session.journal.directories
            ),
        })
        tm.ok(
            u.Cli.atomic_write_binary_file_guarded(
                session.journal_state,
                crash_journal.model_dump_json(indent=2).encode(c.DEFAULT_ENCODING),
                permission_mode=tm.not_none(session.journal_state.mode),
            ),
        )
        if with_foreign_file:
            (staging / "foreign.bin").write_bytes(b"not journaled")

        recovered = owner.run_files_locked(roots, lambda _scope: r[bool].ok(value=True))

        if with_foreign_file:
            tm.fail(recovered)
            tm.that((staging / "foreign.bin").read_bytes(), eq=b"not journaled")
            tm.that(session.journal_state.path.exists(), eq=True)
        else:
            tm.ok(recovered)
            tm.that(staging.exists(), eq=False)
            tm.that(session.journal_state.path.exists(), eq=False)

    @staticmethod
    @pytest.mark.parametrize(
        "journal_change", ["unchanged", "replaced", "missing", "directory"]
    )
    @pytest.mark.parametrize(
        "failure_kind", ["validator", "exception", "abort", "false"]
    )
    @pytest.mark.parametrize("error", [None, "", "consumer rejected publication"])
    def test_session_failure_never_recovers_changed_journal(
        tmp_path: Path,
        failure_kind: str,
        journal_change: str,
        error: str | None,
    ) -> None:
        """Retain the causal failure and publications when journal authority changes."""
        root = u.Tests.git_repository(tmp_path)
        owner = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = {"@docs-0": root}
        target = root / "generated.md"
        cause = OSError("validator failed after journal replacement")
        original = r[bool].fail(
            error,
            exception=cause,
            error_code="PUBLICATION_REJECTED",
            error_data={"consumer": "native-validator", "context": "primary context"},
        )

        def fail_validator() -> p.Result[bool]:
            if failure_kind == "exception":
                raise cause
            return (
                r[bool].fail("consumer rejected")
                if failure_kind == "false"
                else original
            )

        def fail_session(scope: Path) -> p.Result[bool]:
            session = tm.ok(owner.begin_files_locked(scope, roots, ()))
            plan = m.Infra.CodegenFilePlan(
                project=root,
                path=target,
                before=tm.ok(
                    u.Cli.atomic_read_binary_file_state(target, required=False),
                ),
                desired_content=b"prepared publication\n",
                desired_mode=session.journal_state.mode,
                owner="docs",
            )
            initial = session
            session = tm.ok(owner.append_phase_locked(session, "docs", (plan,)))
            before = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
            journal = session.journal_state.path
            foreign = TestsFlextInfraFileParticipantRecovery._corrupted_journal_state(
                journal, journal_change
            )
            if failure_kind == "exception":
                with pytest.raises(OSError, match=str(cause)) as raised:
                    owner.publish_prepared_locked(
                        initial,
                        lambda _initial: fail_validator(),
                    )
                tm.that(raised.value is cause, eq=True)
            else:
                failed = (
                    owner.abort_locked(session, original)
                    if failure_kind == "abort"
                    else owner.publish_prepared_locked(
                        initial,
                        lambda _initial: fail_validator(),
                    )
                )
                tm.fail(failed)
                if failure_kind == "false":
                    tm.that(failed.error, eq="consumer rejected")
                else:
                    tm.that(failed.error, eq=original.error)
                    tm.that(failed.exception is cause, eq=True)
                    tm.that(failed.error_code, eq=original.error_code)
                    tm.that(
                        tm.not_none(failed.error_data)["consumer"],
                        eq="native-validator",
                    )
                    tm.that(
                        tm.not_none(failed.error_data)["context"], eq="primary context"
                    )
                tm.that(
                    (failed.error_data or {}).get("cleanup_error") is not None,
                    eq=journal_change != "unchanged",
                )
            if journal_change == "unchanged":
                tm.that(journal.exists(), eq=False)
                tm.that(target.read_bytes(), eq=b"prepared publication\n")
            elif journal_change == "directory":
                tm.that(journal.is_dir(), eq=True)
                tm.that(target.read_bytes(), eq=before.content)
            else:
                foreign = tm.not_none(foreign)
                tm.that(
                    tm.ok(u.Cli.atomic_read_binary_file_state(journal, required=False)),
                    eq=foreign,
                )
                tm.that(
                    tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True)),
                    eq=before,
                )
            return r[bool].ok(value=True)

        tm.ok(owner.run_files_locked(roots, fail_session))

    @staticmethod
    def test_abort_rejects_success_before_any_recovery(tmp_path: Path) -> None:
        """Reject success without consuming the owned journal or its staging tree."""
        root = u.Tests.git_repository(tmp_path)
        owner = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = {"@docs-0": root}

        def exercise(scope: Path) -> p.Result[bool]:
            session = tm.ok(owner.begin_files_locked(scope, roots, ()))
            staging = session.plan.layout.file_participants[0].transaction_root
            before = tm.ok(u.Cli.atomic_inventory_physical_tree(staging))
            with pytest.raises(
                ValueError,
                match=c.ERR_RESULT_FAILURE_REQUIRED,
            ) as rejected:
                owner.abort_locked(session, r[bool].ok(value=True))
            tm.that(str(rejected.value), eq=c.ERR_RESULT_FAILURE_REQUIRED)
            tm.that(
                tm.ok(u.Cli.atomic_read_binary_file_state(session.journal_state.path)),
                eq=session.journal_state,
            )
            tm.that(tm.ok(u.Cli.atomic_inventory_physical_tree(staging)), eq=before)
            tm.fail(owner.abort_locked(session, r[bool].fail(None)))
            tm.that(session.journal_state.path.exists(), eq=False)
            return r[bool].ok(value=True)

        tm.ok(owner.run_files_locked(roots, exercise))
