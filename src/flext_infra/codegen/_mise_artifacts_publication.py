"""Guarded live publication for one fully journaled generation phase.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, r, t, u
from flext_infra.codegen import FlextInfraMiseArtifactsFiles as files
from flext_infra.codegen import FlextInfraMiseArtifactsVerification

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
        dependencies = cls._source_prerequisites(plan.source_states, {})
        if dependencies.failure:
            return dependencies
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
        publication_before = (
            u.Infra.codegen_file_before_state(plan)
            if phase == c.Infra.CodegenStagedFilePhase.SEMANTIC
            else before
        )
        if publication_before.failure:
            return r[bool].from_failure(publication_before)
        staged_publication = cls._staged_publication(
            plan,
            phase=phase,
            before=publication_before.value,
        )
        if staged_publication.failure:
            return r[bool].from_failure(staged_publication)
        dependencies = cls._source_prerequisites(plan.source_states, {})
        if dependencies.failure:
            return dependencies
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
                    source_states=plan.source_states,
                    tracking=plan.tracking,
                    index_before=plan.index_before,
                    tracking_dependencies=plan.tracking_dependencies,
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
                source_states=plan.source_states,
                tracking=plan.tracking,
                index_before=plan.index_before,
                tracking_dependencies=plan.tracking_dependencies,
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
        published_states: t.MutableMappingKV[
            Path, t.Pair[m.Cli.AtomicFileState, m.Cli.AtomicFileState]
        ] = {}
        exception: BaseException | None = None
        total = len(publications)
        ordered = tuple(
            sorted(publications, key=lambda item: item.index_before is not None)
        )
        for index, publication in enumerate(ordered, start=1):
            u.Cli.emit_raw(f"  publish [{index}/{total}] {publication.before.path}\n")
            ready = FlextInfraMisePublication._tracking_prerequisites(
                publication,
                publications,
                written,
            )
            if ready.success:
                ready = FlextInfraMisePublication._source_prerequisites(
                    publication.source_states,
                    published_states,
                )
            if ready.failure:
                issues.append(
                    m.Infra.Issue(
                        file=str(publication.before.path),
                        line=0,
                        column=0,
                        code=c.Infra.ToolOutcome.ERROR.value,
                        message=ready.error or "tracking prerequisite failed",
                    ),
                )
                exception = exception or ready.exception
                continue
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
                    if (
                        publication.phase
                        in {
                            c.Infra.CodegenStagedFilePhase.SEMANTIC,
                            c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP,
                        }
                        or publication.tracking == "runtime-local"
                    )
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
            receipt = files.read_state(
                publication.before.path,
                required=publication.replacement is not None,
            )
            expected_content = (
                publication.replacement.content
                if publication.replacement is not None
                else None
            )
            expected_mode = (
                publication.replacement.mode
                if publication.replacement is not None
                else None
            )
            if receipt.failure or (
                receipt.value.content != expected_content
                or receipt.value.mode != expected_mode
            ):
                cause = (
                    receipt.exception or ValueError(receipt.error)
                    if receipt.failure
                    else ValueError(
                        f"generated destination changed after publication: "
                        f"{publication.before.path}",
                    )
                )
                issues.append(
                    m.Infra.Issue(
                        file=str(publication.before.path),
                        line=0,
                        column=0,
                        code=c.Infra.ToolOutcome.ERROR.value,
                        message=str(cause),
                    ),
                )
                exception = exception or cause
                continue
            published_states[publication.before.path] = (
                publication.before,
                receipt.value,
            )
            if publication.index_before is not None:
                retired = u.Infra.git_retire_index_file(
                    m.Infra.GitIndexRetirementRequest(
                        repo_root=publication.project,
                        entry=publication.index_before,
                    ),
                )
                if retired.failure:
                    issues.append(
                        m.Infra.Issue(
                            file=str(publication.before.path),
                            line=0,
                            column=0,
                            code=c.Infra.ToolOutcome.ERROR.value,
                            message=retired.error or "index retirement failed",
                        ),
                    )
                    exception = exception or retired.exception
        return r[m.Infra.CodegenPhaseOutcome].ok(
            m.Infra.CodegenPhaseOutcome(
                written_files=tuple(written),
                retained_files=tuple(retained),
                issues=tuple(issues),
                exception=exception,
            ),
        )

    @staticmethod
    def _source_prerequisites(
        sources: t.VariadicTuple[m.Cli.AtomicFileState],
        published: t.MappingKV[
            Path, t.Pair[m.Cli.AtomicFileState, m.Cli.AtomicFileState]
        ],
    ) -> p.Result[bool]:
        """Verify this target's inputs, rebinding only this phase's own writes.

        Returns:
            Exact dependency verification or its first native cause.
        """
        expected: list[m.Cli.AtomicFileState] = []
        for source in sources:
            receipt = published.get(source.path)
            if receipt is None:
                expected.append(source)
                continue
            before, after = receipt
            if source != before:
                cause = ValueError(
                    f"generated dependency preimage differs: {source.path}",
                )
                return r[bool].fail(str(cause), exception=cause)
            expected.append(after)
        verified = FlextInfraMiseArtifactsVerification.states_current(tuple(expected))
        if verified.failure and verified.exception is None:
            cause = ValueError(verified.error)
            return r[bool].fail(str(cause), exception=cause)
        return verified

    @staticmethod
    def _tracking_prerequisites(
        publication: m.Infra.CodegenStagedFile,
        publications: t.VariadicTuple[m.Infra.CodegenStagedFile],
        written: t.SequenceOf[Path],
    ) -> p.Result[bool]:
        """Require portable declarations from this phase before retiring their binding.

        Returns:
            Verified publication evidence for every required declaration.
        """
        for dependency in publication.tracking_dependencies:
            planned = next(
                (item for item in publications if item.before.path == dependency),
                None,
            )
            if (
                planned is None
                or dependency not in written
                or planned.replacement is None
            ):
                error = ValueError(
                    f"portable declaration was not published: {dependency}",
                )
                return r[bool].fail(str(error), exception=error)
            observed = files.read_state(dependency, required=True)
            if observed.failure:
                return r[bool].from_failure(observed)
            if (
                observed.value.content != planned.replacement.content
                or observed.value.mode != planned.replacement.mode
            ):
                error = ValueError(
                    f"portable declaration changed after publication: {dependency}",
                )
                return r[bool].fail(str(error), exception=error)
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraMisePublication"]
