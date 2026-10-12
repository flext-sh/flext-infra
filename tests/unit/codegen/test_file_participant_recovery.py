"""Public recovery behavior for file-only transaction participants.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra import c, m, p, r, t
from flext_infra.codegen import FlextInfraMisePublication
from flext_infra.codegen.codegen_transaction import FlextInfraCodegenTransaction
from flext_infra.codegen.mise_artifacts import FlextInfraCodegenMiseArtifacts
from flext_infra.validate import FlextInfraValidateFreshImport
from tests import tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraFileParticipantRecovery:
    """Recover prepared file-only journals through their physical owners."""

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
    def test_publication_adopts_current_destination_before_one_write(
        tmp_path: Path,
    ) -> None:
        """An external edit before publication is input, not a fleet failure."""
        target = tmp_path / "generated.md"
        target.write_bytes(b"original\n")
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
        target.write_bytes(b"external edit\n")

        outcome = tm.ok(FlextInfraMisePublication.publish((staged,)))

        tm.that(outcome.written_files, eq=(target,))
        tm.that(outcome.issues, eq=())
        tm.that(target.read_bytes(), eq=b"generated\n")

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
            else "destination",
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
    def test_fresh_import_failure_preserves_published_initializer(
        tmp_path: Path,
    ) -> None:
        """Preserve completed publication while reporting its invalid runtime."""
        root = u.Tests.git_repository(tmp_path)
        package = root / c.Infra.DEFAULT_SRC_DIR / "flext_import_probe"
        package.mkdir(parents=True)
        initializer = package / c.Infra.INIT_PY
        initializer.write_text("__all__ = ()\n", encoding=c.DEFAULT_ENCODING)
        before = tm.ok(u.Cli.atomic_read_binary_file_state(initializer, required=True))
        owner = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = {"@lazy-init": root}
        publication = m.Infra.CodegenFilePlan(
            project=root,
            path=initializer,
            before=before,
            desired_content=b"__all__ = ('missing_export',)\n",
            desired_mode=before.mode,
            owner="lazy-init",
        )
        validator = FlextInfraValidateFreshImport(
            repository_root=root,
            packages=(package.name,),
        )

        def publish(scope: Path) -> p.Result[t.VariadicTuple[Path]]:
            session = tm.ok(owner.begin_files_locked(scope, roots, (before,)))
            published = tm.ok(
                owner.append_phase_locked(session, "lazy-init", (publication,)),
            )
            return owner.commit_locked(published, validator.execute)

        failed = owner.run_files_locked(roots, publish)

        tm.fail(failed, has="missing_export")
        tm.that(failed.error, has="Traceback")
        restored = tm.ok(
            u.Cli.atomic_read_binary_file_state(initializer, required=True),
        )
        tm.that(restored.content, eq=publication.desired_content)
        tm.that(restored.mode, eq=before.mode)
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
    @pytest.mark.parametrize("journal_change", ["unchanged", "replaced", "missing"])
    @pytest.mark.parametrize("failure_kind", ["validator", "exception", "abort"])
    def test_session_failure_never_recovers_changed_journal(
        tmp_path: Path,
        failure_kind: str,
        journal_change: str,
    ) -> None:
        """Retain the causal failure and publications when journal authority changes."""
        root = u.Tests.git_repository(tmp_path)
        owner = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = {"@docs-0": root}
        target = root / "generated.md"
        cause = OSError("validator failed after journal replacement")

        def fail_validator() -> p.Result[bool]:
            if failure_kind == "exception":
                raise cause
            return r[bool].fail(str(cause))

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
            saved = journal.with_suffix(".preserved")
            if journal_change != "unchanged":
                journal.rename(saved)
            if journal_change == "replaced":
                journal.write_bytes(saved.read_bytes())
                journal.chmod(saved.stat().st_mode)
            foreign = tm.ok(
                u.Cli.atomic_read_binary_file_state(journal, required=False),
            )
            if failure_kind == "exception":
                with pytest.raises(OSError, match=str(cause)) as raised:
                    owner.publish_prepared_locked(
                        initial,
                        lambda _initial: owner.commit_locked(session, fail_validator),
                    )
                tm.that(raised.value is cause, eq=True)
            else:
                failed = (
                    owner.abort_locked(session, str(cause))
                    if failure_kind == "abort"
                    else owner.publish_prepared_locked(
                        initial,
                        lambda _initial: owner.commit_locked(session, fail_validator),
                    )
                )
                tm.fail(failed, has=str(cause))
                tm.that(
                    (failed.error_data or {}).get("cleanup_error") is not None,
                    eq=journal_change != "unchanged",
                )
            if journal_change == "unchanged":
                tm.that(journal.exists(), eq=False)
                tm.that(target.read_bytes(), eq=b"prepared publication\n")
            else:
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
