"""Plan declared projections and publish them through the shared publisher.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Self, override

from flext_infra import c, m, p, r, settings, t, u, workspace as workspace_services
from flext_infra.codegen import FlextInfraCodegenPreconditions
from flext_infra.codegen._conform.plan import FlextInfraCodegenConformPlan


class FlextInfraCodegenConformExecute(FlextInfraCodegenConformPlan):
    """Generate one request: plan every declared projection, publish once."""

    @classmethod
    def from_request(
        cls: type[Self],
        request: m.Infra.CodegenGenerateRequest,
        *,
        execution_context: p.Infra.CodegenExecutionContext | None,
        repository_root: t.Infra.Path | None = None,
    ) -> p.Result[FlextInfraCodegenConformExecute]:
        """Bind one validated request to the projection executor.

        Returns:
            The bound executor or the original admission failure.

        """
        root = request.root.expanduser().resolve()
        identity = u.Infra.exact_worktree_root(root)
        if identity.failure:
            return r[FlextInfraCodegenConformExecute].from_failure(identity)
        generation_root = (
            root if repository_root is None else repository_root.expanduser().resolve()
        )
        state = m.Infra.CodegenConformState(
            repository_root=generation_root,
            request=request,
            ports=(
                None
                if execution_context is None
                else execution_context.codegen_conform_collaborators()
            ),
        )
        if (
            request.what is c.Infra.CodegenConformSurface.ALL
            and not (root / c.PYPROJECT_FILENAME).exists()
        ):
            inputs = u.Infra.load_codegen_inputs(root)
            if inputs.failure:
                return r[FlextInfraCodegenConformExecute].from_failure(inputs)
            observed = (
                workspace_services.FlextInfraWorkspaceDetector.load_workspace_spec(
                    root, inputs=inputs.value
                )
            )
            if observed.failure:
                return r[FlextInfraCodegenConformExecute].from_failure(observed)
            state.initial_workspace = observed.value
        return r[FlextInfraCodegenConformExecute].ok(
            cls(
                repository_root=generation_root,
                state=state,
                runtime_settings=(
                    None if execution_context is None else execution_context.settings
                ),
                initial_context=(
                    None if execution_context is None else execution_context.context
                ),
            ),
        )

    @classmethod
    def execute_request(
        cls: type[Self],
        request: p.Infra.CodegenGenerateRequest,
        *,
        execution_context: p.Infra.CodegenExecutionContext | None,
        repository_root: t.Infra.Path | None = None,
    ) -> p.Result[p.Infra.CodegenResult]:
        """Admit the public request once, then generate it.

        Returns:
            The projection result or its original failure.

        """
        admitted = m.Infra.CodegenGenerateRequest.model_validate(
            request, from_attributes=True
        )
        bound = cls.from_request(
            admitted,
            execution_context=execution_context,
            repository_root=repository_root,
        )
        if bound.failure:
            return r[p.Infra.CodegenResult].from_failure(bound)
        return bound.value.execute()

    @override
    def execute(self) -> p.Result[p.Infra.CodegenResult]:
        """Generate the bound request.

        Returns:
            The projection outcome.

        Raises:
            ValueError: The executor has no bound request.

        """
        request = self.state.request
        if request is None:
            msg = "projection execution requires a bound generation request"
            raise ValueError(msg)
        return self.execute_managed(request)

    def execute_managed(
        self,
        request: p.Infra.CodegenGenerateRequest,
        *,
        after_publication: tuple[
            Callable[[tuple[Path, ...]], p.Result[bool]], ...
        ] = (),
    ) -> p.Result[p.Infra.CodegenResult]:
        """Plan the request's projections and publish them once.

        ``after_publication`` runs with the written paths after a successful
        publication; its first failure fails the request.

        Returns:
            The plan and written paths, or the first failure.

        """
        u.Cli.info(
            f"operation=generate root={request.root} scope={request.scope} "
            # Bind diagnostics to the selected process settings, never an old report.
            f"surface={request.what} pid={os.getpid()} "
            f"profile={settings.Infra.profile} "
            f"profile_output={settings.Infra.profile_output}"
        )
        root = request.root.expanduser().resolve()
        return (
            FlextInfraCodegenPreconditions
            .rendering_engine(root)
            .flat_map(lambda _: self._planned(request))
            .flat_map(
                lambda plan: self._published(request, root, plan, after_publication)
            )
        )

    def check_managed(
        self,
        request: p.Infra.CodegenGenerateRequest,
    ) -> p.Result[p.Infra.CodegenResult]:
        """Fail when the request's projections differ from the tree.

        Uses the same plan and normalized view as publication, without effects.

        Returns:
            The plan when every projection is current, or the stale paths.

        """
        root = request.root.expanduser().resolve()
        return (
            FlextInfraCodegenPreconditions
            .rendering_engine(root)
            .flat_map(lambda _: self._planned(request))
            .flat_map(lambda plan: self._checked(request, plan))
        )

    def _checked(
        self,
        request: p.Infra.CodegenGenerateRequest,
        plan: m.Infra.CodegenPlan,
    ) -> p.Result[p.Infra.CodegenResult]:
        """Compare the injected publisher's normalized plan with the tree.

        Check and apply consume the same publication capability; neither resolves
        a utility implementation inside the executor.

        Returns:
            The plan when nothing is pending, or the stale destinations.

        """
        result_type = r[p.Infra.CodegenResult]
        if (
            plan.issues
            or plan.exception is not None
            or any(outcome.failed for outcome in plan.outcomes)
        ):
            return result_type.from_failure(self._admitted_plans(request, plan))
        ports = self.state.ports
        if ports is None:
            return result_type.fail(
                "conformance requires facade-wired file publication"
            )
        changes = self._admitted_plans(request, plan).flat_map(
            lambda files: u.Cli.atomic_verify_binary_file_states(
                tuple(state for file in files for state in (file.before, *file.inputs))
            ).flat_map(lambda _: ports.file_publisher.normalized_codegen_changes(files))
        )
        if changes.failure:
            return result_type.from_failure(changes)
        pending = u.Cli.pending_file_changes(changes.value)
        if pending:
            return result_type.fail(
                "generated projections are stale: "
                + ", ".join(sorted(str(change.path) for change in pending))
            )
        payload: p.Infra.CodegenResult = m.Infra.CodegenResult(plan=plan)
        return result_type.ok(payload)

    def _planned(
        self,
        request: p.Infra.CodegenGenerateRequest,
    ) -> p.Result[m.Infra.CodegenPlan]:
        """Plan the request, failing when planning produced only failures.

        Returns:
            The plan, or its planning failure.

        """
        started = time.monotonic()
        u.Cli.info(f"stage=planning state=start root={request.root}")
        planned = (
            self._plan_single_surface(request)
            if request.what in c.Infra.FILE_ONLY_SURFACES
            else self.plan(request)
        )
        failed = planned.failure or (
            planned.success
            and (
                bool(planned.value.issues)
                or planned.value.exception is not None
                or any(outcome.failed for outcome in planned.value.outcomes)
            )
        )
        u.Cli.info(
            f"stage=planning state=end root={request.root} "
            f"elapsed={time.monotonic() - started:.3f}s "
            f"files={len(planned.value.files) if planned.success else 0} "
            f"failed={failed}"
        )
        if (
            planned.success
            and not planned.value.files
            and (
                planned.value.issues
                or planned.value.exception is not None
                or any(outcome.failed for outcome in planned.value.outcomes)
            )
        ):
            native = self.state.planning_failure
            if native is None:
                native = next(
                    (
                        outcome.native_failure
                        for outcome in planned.value.outcomes
                        if outcome.native_failure is not None
                    ),
                    None,
                )
            if native is not None:
                return r[m.Infra.CodegenPlan].from_failure(native)
            return r[m.Infra.CodegenPlan].fail(
                "\n".join(issue.formatted for issue in planned.value.issues)
                or "generation planning failed",
                exception=planned.value.exception,
            )
        return planned

    def _published(
        self,
        request: p.Infra.CodegenGenerateRequest,
        root: Path,
        plan: m.Infra.CodegenPlan,
        after_publication: tuple[Callable[[tuple[Path, ...]], p.Result[bool]], ...],
    ) -> p.Result[p.Infra.CodegenResult]:
        """Publish independent authenticated cohorts, retaining every failure.

        Changed providers, consumers and exports share candidate admission.
        Publication failures retain the writer's completed-path receipt;
        unrelated admitted effects remain valid and are included in the final
        failure metadata. Follow-ups require the complete request to succeed.

        Returns:
            The full result, or the first cause with all actual written paths.

        """
        if not plan.outcomes:
            return self._published_cohort(request, root, plan, after_publication)
        result_type = r[p.Infra.CodegenResult]
        ready = {
            repository.name: repository
            for repository in plan.repositories
            if any(
                outcome.repository == repository.name and not outcome.failed
                for outcome in plan.outcomes
            )
        }
        ready_roots = {
            (root / repository.path).resolve() for repository in ready.values()
        }
        documents = self._docs_plans(
            request,
            m.Infra.CodegenPlan(
                request=plan.request,
                workspace=plan.workspace,
                repositories=tuple(ready.values()),
                files=tuple(file for file in plan.files if file.project in ready_roots),
                uv_environments=plan.uv_environments,
            ),
        )
        if documents.failure:
            owner = next(
                (
                    repository
                    for repository in ready.values()
                    if repository.path == Path()
                ),
                None,
            )
            if owner is None:
                return result_type.from_failure(documents)
            issue = m.Infra.Issue(
                file=str(root),
                line=0,
                column=0,
                code=c.Infra.ToolOutcome.ERROR.value,
                message=documents.error or "documentation planning failed",
            )
            original = next(
                outcome for outcome in plan.outcomes if outcome.repository == owner.name
            )
            native = original.native_failure
            if native is None and original.exception is not None:
                native = r.fail(original.error, exception=original.exception)
            if native is None:
                native = documents
            original.error = native.error or ""
            original.exception = native.exception
            original.native_failure = native
            original.issues = (*original.issues, issue)
            plan.issues = (*plan.issues, issue)
            first_native = self.state.planning_failure
            plan.exception = (
                first_native.exception
                if first_native is not None
                else plan.exception
                if plan.exception is not None
                else native.exception
            )
        else:
            plan.files = documents.value
        cohorts = self._publication_cohorts(root, plan)
        if cohorts.failure:
            return result_type.from_failure(cohorts)
        written: list[Path] = []
        failures: list[p.FailureLike] = []
        first_native = self.state.planning_failure
        ordered = sorted(
            cohorts.value,
            key=lambda cohort: (
                not any(
                    outcome.native_failure is first_native
                    for outcome in cohort.outcomes
                )
                if first_native is not None
                else False
            ),
        )
        for cohort in ordered:
            published = self._published_cohort(
                request, root, cohort, (), prepared_files=cohort.files
            )
            if published.failure:
                failures.append(published)
                written.extend(
                    Path(path)
                    for path in u.type_adapter(t.TypeForm(list[str])).validate_python(
                        (published.error_data or {}).get("written_files", []),
                        strict=True,
                    )
                )
                u.Cli.error(published.error or "generation cohort failed")
            else:
                written.extend(published.value.written_files)
        if not failures:
            for operation in after_publication:
                completed = operation(tuple(written))
                if completed.failure:
                    failures.append(completed)
                    written.extend(
                        Path(path)
                        for path in u.type_adapter(
                            t.TypeForm(list[str])
                        ).validate_python(
                            (completed.error_data or {}).get("written_files", []),
                            strict=True,
                        )
                    )
                    break
        if failures:
            first = failures[0]
            return result_type.fail(
                "\n".join(failure.error or "generation failed" for failure in failures),
                error_code=first.error_code,
                error_data={
                    **(first.error_data or {}),
                    "written_files": [str(path) for path in written],
                    "errors": [
                        failure.error or "generation failed" for failure in failures
                    ],
                },
                exception=first.exception,
            )
        payload: p.Infra.CodegenResult = m.Infra.CodegenResult(
            plan=plan, written_files=tuple(written)
        )
        return result_type.ok(payload)

    @staticmethod
    def _publication_cohorts(
        root: Path,
        plan: m.Infra.CodegenPlan,
    ) -> p.Result[tuple[m.Infra.CodegenPlan, ...]]:
        """Close candidate effects over authenticated changed-file dependencies.

        Returns:
            Existing plan objects grouped by the native graph component owner.

        """
        result_type = r[tuple[m.Infra.CodegenPlan, ...]]
        outcomes = {outcome.repository: outcome for outcome in plan.outcomes}
        repositories = {repository.name: repository for repository in plan.repositories}
        roots = {
            name: (root / repository.path).resolve()
            for name, repository in repositories.items()
        }
        accounted = tuple(
            issue for outcome in outcomes.values() for issue in outcome.issues
        )
        if any(
            issue not in accounted
            and not any(
                outcome.failed and issue.file == str(roots[outcome.repository])
                for outcome in outcomes.values()
            )
            for issue in plan.issues
        ) or (
            plan.exception is not None
            and not any(
                outcome.exception is plan.exception for outcome in outcomes.values()
            )
        ):
            return result_type.ok((plan,))
        owners: dict[Path, set[str]] = {}
        projects: dict[Path, set[str]] = {roots[name]: {name} for name in outcomes}
        edges: dict[str, set[str]] = {name: set() for name in outcomes}
        for outcome in outcomes.values():
            for file in outcome.files:
                projects.setdefault(file.project, set()).add(outcome.repository)
        files = (
            *(file for outcome in outcomes.values() for file in outcome.files),
            *plan.files,
        )
        pending = frozenset(change.path for change in u.Cli.pending_file_changes(files))
        unowned = tuple(
            file.path for file in plan.files if file.project not in projects
        )
        if unowned:
            message = f"publication effects have no repository owner: {unowned}"
            return result_type.fail(message)
        for file in files:
            if file.path in pending:
                owners.setdefault(file.path, set()).update(projects[file.project])
        for file in files:
            for path in (
                file.path,
                *file.tracking_dependencies,
                *(state.path for state in file.inputs),
            ):
                for repository in projects[file.project]:
                    for owner in owners.get(path, ()):
                        edges[repository].add(owner)
                        edges[owner].add(repository)
        cohorts: list[m.Infra.CodegenPlan] = []
        for component in u.Cli.dag_strongly_connected(edges):
            selected = tuple(
                outcome for outcome in plan.outcomes if outcome.repository in component
            )
            issues = tuple(issue for outcome in selected for issue in outcome.issues)
            failed = tuple(outcome for outcome in selected if outcome.failed)
            issues += tuple(
                m.Infra.Issue(
                    file=str(roots[outcome.repository]),
                    line=0,
                    column=0,
                    code=c.Infra.ToolOutcome.ERROR.value,
                    message=(
                        outcome.error_traceback
                        or outcome.error
                        or outcome.error_type
                        or str(outcome.exception)
                    ),
                )
                for outcome in failed
                if outcome.error
                or outcome.error_type
                or outcome.error_traceback
                or outcome.exception is not None
            )
            cohorts.append(
                m.Infra.CodegenPlan(
                    request=plan.request,
                    workspace=plan.workspace,
                    uv_environments=plan.uv_environments,
                    repositories=tuple(
                        repositories[name] for name in sorted(component)
                    ),
                    files=tuple(
                        file
                        for file in plan.files
                        if projects[file.project].intersection(component)
                    ),
                    issues=issues,
                    exception=next(
                        (
                            outcome.exception
                            for outcome in failed
                            if outcome.exception is plan.exception
                        ),
                        next(
                            (
                                outcome.exception
                                for outcome in failed
                                if outcome.exception is not None
                            ),
                            None,
                        ),
                    ),
                    outcomes=selected,
                )
            )
        if plan.exception is not None:
            cohorts.sort(key=lambda cohort: cohort.exception is not plan.exception)
        return result_type.ok(tuple(cohorts))

    def _published_cohort(
        self,
        request: p.Infra.CodegenGenerateRequest,
        root: Path,
        plan: m.Infra.CodegenPlan,
        after_publication: tuple[Callable[[tuple[Path, ...]], p.Result[bool]], ...],
        *,
        prepared_files: tuple[m.Infra.CodegenFilePlan, ...] | None = None,
    ) -> p.Result[p.Infra.CodegenResult]:
        """Admit and publish one complete cohort through the existing owners.

        Every planning diagnostic and cold-import failure rejects the cohort
        before the first destination effect. Check and apply share candidate
        admission and the existing guarded publication owner.

        Returns:
            The plan and written paths, or the first failure.

        """
        result_type = r[p.Infra.CodegenResult]
        ports = self.state.ports
        if ports is None:
            return result_type.fail(
                "conformance requires facade-wired file publication"
            )
        started = time.monotonic()
        u.Cli.info(f"stage=admission state=start root={root} files={len(plan.files)}")
        admitted = self._admitted_plans(request, plan, prepared_files=prepared_files)
        u.Cli.info(
            f"stage=admission state=end root={root} "
            f"elapsed={time.monotonic() - started:.3f}s failed={admitted.failure}"
        )
        if admitted.failure:
            return result_type.from_failure(admitted)
        started = time.monotonic()
        u.Cli.info(
            f"stage=publication state=start root={root} files={len(admitted.value)}"
        )
        published = ports.file_publisher.publish_codegen_plans(root, admitted.value)
        completed_paths = (
            published.value
            if published.success
            else tuple(
                Path(path)
                for path in u.type_adapter(t.TypeForm(list[str])).validate_python(
                    (published.error_data or {}).get("written_files", []), strict=True
                )
            )
        )
        u.Cli.info(
            f"stage=publication state=end root={root} "
            f"elapsed={time.monotonic() - started:.3f}s "
            f"written={len(completed_paths)} "
            f"failed={published.failure}"
        )
        if published.failure:
            return result_type.from_failure(published)
        snapshot = self.state.snapshot
        if snapshot is not None and snapshot.workspace_root == root:
            u.Infra.workspace_snapshot_rebase(snapshot, published.value)
        for operation in after_publication:
            completed = operation(published.value)
            if completed.failure:
                return result_type.fail(
                    completed.error or "publication follow-up failed",
                    error_code=completed.error_code,
                    error_data={
                        **(completed.error_data or {}),
                        "written_files": [
                            *(str(path) for path in published.value),
                            *u.type_adapter(t.TypeForm(list[str])).validate_python(
                                (completed.error_data or {}).get("written_files", []),
                                strict=True,
                            ),
                        ],
                    },
                    exception=completed.exception,
                )
        payload: p.Infra.CodegenResult = m.Infra.CodegenResult(
            plan=plan,
            written_files=published.value,
        )
        return result_type.ok(payload)

    def _admitted_plans(
        self,
        request: p.Infra.CodegenGenerateRequest,
        plan: m.Infra.CodegenPlan,
        *,
        prepared_files: tuple[m.Infra.CodegenFilePlan, ...] | None = None,
    ) -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]]:
        """Validate the normalized dependency cohort before accepting any effects.

        The native preview materializes original file declarations, including
        retirements. Its existing cold-import owner must accept that exact source
        view before the shared publisher may verify and write its destinations.

        Returns:
            The normalized plans, or the original planning or admission failure.

        """
        result_type = r[tuple[m.Infra.CodegenFilePlan, ...]]
        if (
            plan.issues
            or plan.exception is not None
            or any(outcome.failed for outcome in plan.outcomes)
        ):
            native = next(
                (
                    outcome.native_failure
                    for outcome in plan.outcomes
                    if outcome.native_failure is not None
                    and (
                        plan.exception is None
                        or outcome.native_failure.exception is plan.exception
                    )
                ),
                None,
            )
            first_native = self.state.planning_failure
            if first_native is not None and any(
                outcome.native_failure is first_native for outcome in plan.outcomes
            ):
                native = first_native
            if native is not None:
                return result_type.from_failure(native)
            return result_type.fail(
                "\n".join(issue.formatted for issue in plan.issues)
                or "generation planning failed",
                exception=plan.exception,
            )
        ports = self.state.ports
        if ports is None:
            return result_type.fail(
                "conformance requires facade-wired candidate admission"
            )
        docs = (
            result_type.ok(prepared_files)
            if prepared_files is not None
            else self._docs_plans(request, plan)
        )
        if docs.failure:
            return result_type.from_failure(docs)
        composed = result_type.create_from_callable(
            lambda: u.Infra.codegen_compose_file_plans(docs.value)
        )
        if composed.failure:
            return result_type.from_failure(composed)
        files = composed.value
        changes = ports.file_publisher.normalized_codegen_changes(files)
        if changes.failure:
            return result_type.from_failure(changes)
        normalized = {change.path: change for change in changes.value}
        files = tuple(
            m.Infra.CodegenFilePlan(
                project=file.project,
                path=file.path,
                before=file.before,
                desired_content=normalized[file.path].desired_content,
                desired_mode=normalized[file.path].desired_mode,
                owner=file.owner,
                policy=file.policy,
                tracking=file.tracking,
                index_before=file.index_before,
                tracking_dependencies=file.tracking_dependencies,
                inputs=file.inputs,
            )
            for file in files
        )
        return self._validated_source_plans(request, files, ports)

    @staticmethod
    def _validated_source_plans(
        request: p.Infra.CodegenGenerateRequest,
        files: tuple[m.Infra.CodegenFilePlan, ...],
        ports: p.Infra.CodegenConformPorts,
    ) -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]]:
        """Admit the normalized candidate through its injected runtime validator.

        Returns:
            The unchanged normalized plans, or the original validation failure.

        """
        result_type = r[tuple[m.Infra.CodegenFilePlan, ...]]
        if not any(file.path.suffix == c.Infra.EXT_PYTHON for file in files):
            return result_type.ok(files)
        root = request.root.expanduser().resolve()
        preview = ports.source_preview.preview_sources(
            root,
            {
                file.path: file.desired_content.decode(c.DEFAULT_ENCODING)
                if file.desired_content is not None
                else None
                for file in files
            },
            lambda candidate, _paths: ports.candidate_validator(
                root,
                candidate,
                tuple(
                    sorted({
                        file.project
                        for file in files
                        if file.path.suffix == c.Infra.EXT_PYTHON
                    })
                ),
            ),
            options=m.Infra.CodegenSourcePreviewOptions(
                declared_files=files,
                inputs=tuple(
                    state for file in files for state in (file.before, *file.inputs)
                ),
            ),
        ).flat_map(lambda outcome: outcome)
        if preview.failure:
            return result_type.from_failure(preview)
        if not preview.value:
            return result_type.fail("native candidate admission returned no acceptance")
        return result_type.ok(files)

    def _docs_plans(
        self,
        request: p.Infra.CodegenGenerateRequest,
        plan: m.Infra.CodegenPlan,
    ) -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]]:
        """Compose managed plans with their derived presentation and documentation.

        Returns:
            The complete candidate, retaining strict independent artifact admission.

        """
        result_type = r[tuple[m.Infra.CodegenFilePlan, ...]]
        owned = tuple(
            repository.name
            for repository in plan.repositories
            if repository.path == Path()
        )
        if request.what is not c.Infra.CodegenConformSurface.ALL or not owned:
            return result_type.ok(tuple(plan.files))
        ports = self.state.ports
        if ports is None:
            return result_type.fail(
                "complete generation requires the facade-wired docs planner; "
                "run it through FlextInfra.codegen_generate",
            )
        planner = ports.docs_planner(
            repository_root=request.root,
            projects=owned,
            include_root=True,
        )
        bundle = planner.prepare_bundle(declared_files=tuple(plan.files))
        if bundle.failure:
            return result_type.from_failure(bundle)
        rendered = planner.plan_files(bundle.value)
        if rendered.failure:
            return result_type.from_failure(rendered)
        return result_type.create_from_callable(
            lambda: u.Infra.codegen_compose_file_plans((
                *u.Infra.codegen_compose_file_plans(
                    (*plan.files, *bundle.value.metadata_files), ordered=True
                ),
                *rendered.value,
            ))
        )


__all__: list[str] = ["FlextInfraCodegenConformExecute"]
