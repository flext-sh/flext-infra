"""Public real-file contracts for indivisible admission-cohort observations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, m, p, tm, u


class TestsFlextInfraCodegenAdmissionWitnesses:
    """Exercise native verification and publication with authenticated file reads."""

    @staticmethod
    @c.Tests.MARK.parametrize("reverse", [False, True])
    @c.Tests.MARK.parametrize("drift", [False, True])
    def test_noop_carrier_and_complete_reordering_keep_publication_guard(
        infra_git_repo: Path,
        codegen_admission_cohort: tuple[
            tuple[p.Infra.CodegenFilePlan, ...], p.Cli.AtomicFileState
        ],
        *,
        reverse: bool,
        drift: bool,
    ) -> None:
        """A no-op carrier guards all effects, including after complete reordering."""
        original, captured = codegen_admission_cohort
        files = tuple(reversed(original)) if reverse else original
        if drift:
            captured.path.write_text(
                "changed after admission\n", encoding=c.DEFAULT_ENCODING
            )
        published = u.Infra.publish_normalized_codegen_plans(
            infra_git_repo, files, files
        )
        if drift:
            tm.fail(published, has=f"atomic source changed: {captured.path}")
            for file in files:
                tm.that(file.path.read_bytes(), eq=file.before.content)
        else:
            tm.ok(published)
            for file in files:
                tm.that(file.path.read_bytes(), eq=file.desired_content)

    @staticmethod
    def test_later_conflicting_observation_rejects_all_effects(
        infra_git_repo: Path,
        codegen_admission_cohort: tuple[
            tuple[p.Infra.CodegenFilePlan, ...], p.Cli.AtomicFileState
        ],
    ) -> None:
        """A later conflicting read cannot replace the cohort's first witness."""
        files, captured = codegen_admission_cohort
        captured.path.write_text("second observation\n", encoding=c.DEFAULT_ENCODING)
        changed = tm.ok(
            u.Cli.atomic_read_binary_file_state(captured.path, required=True)
        )
        second = files[1]
        conflicting = m.Infra.CodegenFilePlan(
            project=second.project,
            path=second.path,
            before=second.before,
            desired_content=second.desired_content,
            desired_mode=second.desired_mode,
            inputs=(changed,),
        )
        cohort = (files[0], conflicting)
        tm.fail(
            u.Infra.publish_normalized_codegen_plans(infra_git_repo, cohort, cohort),
            has="atomic source has conflicting snapshots",
        )
        for file in files:
            tm.that(file.path.read_bytes(), eq=file.before.content)

    @staticmethod
    def test_read_only_verification_preserves_files_on_observation_drift(
        codegen_admission_cohort: tuple[
            tuple[p.Infra.CodegenFilePlan, ...], p.Cli.AtomicFileState
        ],
    ) -> None:
        """Native verification refuses a stale read without publishing any effect."""
        files, captured = codegen_admission_cohort
        captured.path.write_text("changed before check\n", encoding=c.DEFAULT_ENCODING)
        tm.fail(
            u.Cli.atomic_verify_binary_file_states(
                tuple(state for file in files for state in (file.before, *file.inputs))
            ),
            has=f"atomic source changed: {captured.path}",
        )
        for file in files:
            tm.that(file.path.read_bytes(), eq=file.before.content)

    @staticmethod
    @c.Tests.MARK.parametrize("drift", [False, True])
    def test_deleted_carrier_preserves_survivor_and_shared_input_guard(
        infra_git_repo: Path,
        codegen_admission_cohort: tuple[
            tuple[p.Infra.CodegenFilePlan, ...], p.Cli.AtomicFileState
        ],
        *,
        drift: bool,
    ) -> None:
        """Deleting the observation carrier cannot drop its transaction guard."""
        files, captured = codegen_admission_cohort
        first, survivor = files
        retired = m.Infra.CodegenFilePlan(
            project=first.project,
            path=first.path,
            before=first.before,
            desired_content=None,
            desired_mode=None,
            inputs=first.inputs,
        )
        cohort = (retired, survivor)
        if drift:
            captured.path.write_text(
                "changed before deletion\n", encoding=c.DEFAULT_ENCODING
            )
        published = u.Infra.publish_normalized_codegen_plans(
            infra_git_repo, cohort, cohort
        )
        if drift:
            tm.fail(published, has=f"atomic source changed: {captured.path}")
            for file in files:
                tm.that(file.path.read_bytes(), eq=file.before.content)
        else:
            tm.ok(published)
            tm.that(first.path.exists(), eq=False)
            tm.that(survivor.path.read_bytes(), eq=survivor.desired_content)

    @staticmethod
    def test_independent_cohorts_each_reject_their_shared_input_drift(
        infra_git_repo: Path,
        codegen_admission_cohort: tuple[
            tuple[p.Infra.CodegenFilePlan, ...], p.Cli.AtomicFileState
        ],
    ) -> None:
        """Each separately declared publication retains its original observation."""
        files, captured = codegen_admission_cohort
        captured.path.write_text(
            "changed before publication\n", encoding=c.DEFAULT_ENCODING
        )
        for file in files:
            cohort = (
                m.Infra.CodegenFilePlan(
                    project=file.project,
                    path=file.path,
                    before=file.before,
                    desired_content=file.desired_content,
                    desired_mode=file.desired_mode,
                    inputs=(captured,),
                ),
            )
            tm.fail(
                u.Infra.publish_normalized_codegen_plans(
                    infra_git_repo, cohort, cohort
                ),
                has=f"atomic source changed: {captured.path}",
            )
            tm.that(file.path.read_bytes(), eq=file.before.content)

    @staticmethod
    def test_absent_input_appearing_rejects_all_effects(
        infra_git_repo: Path,
        codegen_admission_cohort: tuple[
            tuple[p.Infra.CodegenFilePlan, ...], p.Cli.AtomicFileState
        ],
    ) -> None:
        """A negative source observation remains authoritative until publication."""
        files, _captured = codegen_admission_cohort
        source = infra_git_repo / "absent.txt"
        absent = tm.ok(u.Cli.atomic_read_binary_file_state(source))
        cohort = tuple(file.model_copy(update={"inputs": (absent,)}) for file in files)
        source.write_text("appeared after admission\n", encoding=c.DEFAULT_ENCODING)
        tm.fail(
            u.Infra.publish_normalized_codegen_plans(infra_git_repo, cohort, cohort),
            has=f"atomic source changed: {source}",
        )
        for file in files:
            tm.that(file.path.read_bytes(), eq=file.before.content)
