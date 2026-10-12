"""Guarded live publication for one fully journaled generation phase.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, r, t, u
from flext_infra.codegen import FlextInfraMiseArtifactsFiles as files

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraMisePublication:
    """Publish staged generated files through full-state guarded primitives."""

    @staticmethod
    def _invalidate_project_document(path: Path) -> None:
        """Drop the process-wide parsed pyproject after this writer replaces it.

        Why: flext-core caches the parsed pyproject per process keyed by root; a
        plan built right after publication must read the published document.
        """
        if path.name == c.PYPROJECT_FILENAME:
            u.read_project_document_cached.cache_clear()

    @classmethod
    def publish_file_plan(
        cls,
        plan: m.Infra.CodegenFilePlan,
        *,
        phase: str,
    ) -> p.Result[bool]:
        """Publish one FilePlan through write_publication without a journal.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if not u.Infra.codegen_file_requires_effect(plan):
            return r[bool].ok(value=True)
        before = files.read_state(plan.path, required=False)
        if before.failure:
            return r[bool].from_failure(before)
        if (
            phase != c.Infra.CodegenStagedFilePhase.SEMANTIC
            and plan.path.name == c.Infra.INIT_PY
            and u.Infra.codegen_initializer_is_authored(before.value.content)
        ):
            u.Cli.info(
                f"ownership=authored disposition=retained target={plan.path}",
            )
            return r[bool].ok(value=False)
        staged_publication = cls._staged_publication(
            plan,
            phase=phase,
            before=(
                plan.before
                if phase == c.Infra.CodegenStagedFilePhase.SEMANTIC
                else before.value
            ),
        )
        if staged_publication.failure:
            return r[bool].from_failure(staged_publication)
        published = files.write_publication(staged_publication.value)
        FlextInfraMisePublication._invalidate_project_document(plan.path)
        return published

    @classmethod
    def _staged_publication(
        cls,
        plan: m.Infra.CodegenFilePlan,
        *,
        phase: str,
        before: m.Cli.AtomicFileState,
    ) -> p.Result[m.Infra.CodegenStagedFile]:
        """Stage one plan's desired content beside its destination.

        A deletion-only plan stages the journal entry whose replacement is
        None; the model owns that contract.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenStagedFile]``.

        """
        result_type = r[m.Infra.CodegenStagedFile]
        if plan.desired_content is None:
            return result_type.ok(
                m.Infra.CodegenStagedFile(
                    phase=c.Infra.CodegenStagedFilePhase(phase),
                    project=plan.project,
                    before=before,
                    replacement=None,
                ),
            )
        mode = plan.desired_mode
        if mode is None:
            return result_type.fail(f"codegen desired mode is absent: {plan.path}")
        staging_path = plan.path.with_name(f".{plan.path.name}.codegen-staging")
        staged_before = u.Cli.atomic_read_binary_file_state(
            staging_path,
            required=False,
        )
        if staged_before.failure:
            return result_type.from_failure(staged_before)
        written = u.Cli.atomic_write_binary_file_guarded(
            staged_before.value,
            plan.desired_content,
            permission_mode=mode,
        )
        if written.failure:
            return result_type.from_failure(written)
        staged = files.read_state(staging_path, required=True)
        if staged.failure:
            return result_type.from_failure(staged)
        return result_type.ok(
            m.Infra.CodegenStagedFile(
                phase=c.Infra.CodegenStagedFilePhase(phase),
                project=plan.project,
                before=before,
                replacement=staged.value,
            ),
        )

    @staticmethod
    def publish(
        publications: t.VariadicTuple[m.Infra.CodegenStagedFile],
    ) -> p.Result[m.Infra.CodegenPhaseOutcome]:
        """Publish every target independently and retain all native failures.

        Returns:
            The complete written paths and target issues.

        """
        written: list[Path] = []
        retained: list[Path] = []
        issues: list[m.Infra.Issue] = []
        exception: BaseException | None = None
        total = len(publications)
        for index, publication in enumerate(publications, start=1):
            u.Cli.emit_raw(f"  publish [{index}/{total}] {publication.before.path}\n")
            observed = files.read_state(publication.before.path, required=False)
            if (
                observed.success
                and publication.phase != c.Infra.CodegenStagedFilePhase.SEMANTIC
                and publication.before.path.name == c.Infra.INIT_PY
                and u.Infra.codegen_initializer_is_authored(observed.value.content)
            ):
                retained.append(publication.before.path)
                u.Cli.info(
                    "ownership=authored disposition=retained "
                    f"target={publication.before.path}",
                )
                continue
            changed = (
                files.write_publication(
                    publication
                    if publication.phase == c.Infra.CodegenStagedFilePhase.SEMANTIC
                    else publication.model_copy(update={"before": observed.value}),
                )
                if observed.success
                else r[bool].from_failure(observed)
            )
            if changed.failure:
                issues.append(
                    m.Infra.Issue(
                        file=str(publication.before.path),
                        line=0,
                        column=0,
                        code=c.Infra.ToolOutcome.ERROR.value,
                        message=changed.error or "publication failed",
                    ),
                )
                if exception is None:
                    exception = changed.exception
                continue
            FlextInfraMisePublication._invalidate_project_document(
                publication.before.path,
            )
            written.append(publication.before.path)
        return r[m.Infra.CodegenPhaseOutcome].ok(
            m.Infra.CodegenPhaseOutcome(
                written_files=tuple(written),
                retained_files=tuple(retained),
                issues=tuple(issues),
                exception=exception,
            ),
        )


__all__: list[str] = ["FlextInfraMisePublication"]
