"""Codegen pipeline stage handlers — extracted concern of FlextInfraCodegenPipeline."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, config, m, t, u
from flext_infra.codegen.census import FlextInfraCodegenCensus
from flext_infra.codegen.conform import (
    FlextInfraCodegenConform,
    FlextInfraCodegenTransaction,
)
from flext_infra.codegen.fixer import FlextInfraCodegenFixer
from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit
from flext_infra.codegen.mise_artifacts import FlextInfraCodegenMiseArtifacts
from flext_infra.codegen.py_typed import FlextInfraCodegenPyTyped
from flext_infra.codegen.scaffolder import FlextInfraCodegenScaffolder
from flext_infra.deps.detector import FlextInfraRuntimeDevDependencyDetector

if TYPE_CHECKING:
    from collections.abc import Callable

    from flext_infra import p


class FlextInfraCodegenPipelineStagesMixin:
    """Seven linear codegen stage handlers, each a single fail-fast boundary.

    Composed into FlextInfraCodegenPipeline via FLEXT; every handler runs through
    the facade's ``_run_stage`` harness and caches its output in ``self._state``.
    """

    if TYPE_CHECKING:
        # Provided by the composed facade (FlextInfraCodegenPipeline); declared
        # here so the handlers type-resolve against the facade state + harness.
        _state: m.Infra.CodegenPipelineState

        def _run_stage[V](
            self,
            stage_id: str,
            action: Callable[[], V],
            emit: Callable[[V], t.JsonMapping],
        ) -> p.Result[m.Cli.PipelineStageResult]: ...

    def _stage_discover(
        self, ctx: p.Cli.PipelineStageContext, /
    ) -> p.Result[m.Cli.PipelineStageResult]:
        """Discover workspace projects once for reuse across all stages.

        Failure to enumerate projects propagates as a stage failure — no
        silent empty-tuple fallback, since downstream stages depend on the
        actual workspace inventory.
        """

        def _action() -> t.VariadicTuple[m.Infra.ProjectInfo]:
            projects_result = u.Infra.projects(ctx.repository_root)
            if projects_result.failure:
                msg = projects_result.error or "project discovery failed"
                raise RuntimeError(msg)
            return tuple(projects_result.unwrap())

        def _emit(discovered: t.VariadicTuple[m.Infra.ProjectInfo]) -> t.JsonMapping:
            self._state.discovered_projects = discovered
            return {"projects_discovered": len(discovered)}

        return self._run_stage(c.Infra.PipelineStage.DISCOVER, _action, _emit)

    def _stage_toolchain(
        self, ctx: p.Cli.PipelineStageContext, /
    ) -> p.Result[m.Cli.PipelineStageResult]:
        """Conform workspace toolchains through the canonical codegen planner."""

        def _action() -> m.Infra.CodegenResult:
            dry_run = bool(ctx.settings.get(c.Infra.PIPELINE_KEY_DRY_RUN, False))
            result = FlextInfraCodegenConform.execute_request(
                m.Infra.CodegenConformRequest(
                    root=ctx.repository_root,
                    what=c.Infra.CodegenConformSurface.ALL,
                    scope=c.Infra.CodegenConformScope.ALL,
                    mode=(
                        c.Infra.CodegenConformMode.CHECK
                        if dry_run
                        else c.Infra.CodegenConformMode.APPLY
                    ),
                )
            )
            if result.failure:
                msg = result.error or "toolchain conform failed"
                raise RuntimeError(msg)
            conformed: m.Infra.CodegenResult = result.unwrap()
            return conformed

        return self._run_stage(
            c.Infra.PipelineStage.TOOLCHAIN,
            _action,
            lambda result: {
                "repositories_conformed": len(result.plan.repositories),
                "files_written": len(result.written_files),
            },
        )

    def _stage_deps(
        self, ctx: p.Cli.PipelineStageContext, /
    ) -> p.Result[m.Cli.PipelineStageResult]:
        """Conform dependencies to reality via deptry + typing-stub detection.

        Reuses ``FlextInfraRuntimeDevDependencyDetector`` (deptry DEP001-004 +
        ``types-*`` stub hints). Apply declares missing requirements in CUSTOM
        ``project.optional-dependencies.typings`` and installs them through UV;
        dry-run reports only. Mutation failures remain stage failures.
        """

        def _action() -> bool:
            dry_run = bool(ctx.settings.get(c.Infra.PIPELINE_KEY_DRY_RUN, False))
            projects = self._state.discovered_projects
            selected = tuple(project.path.name for project in projects)
            detector = FlextInfraRuntimeDevDependencyDetector(
                repository_root=ctx.repository_root,
                apply_changes=not dry_run,
                apply_typings=not dry_run,
                selected_projects=selected,
            )
            result = detector.execute()
            if result.failure:
                msg = result.error or "dependency conform failed"
                raise RuntimeError(msg)
            applied: bool = t.Infra.BOOL_ADAPTER.validate_python(result.unwrap())
            return applied

        return self._run_stage(
            c.Infra.PipelineStage.DEPS,
            _action,
            lambda applied: {"deps_conformed": applied},
        )

    def _stage_py_typed(
        self, ctx: p.Cli.PipelineStageContext, /
    ) -> p.Result[m.Cli.PipelineStageResult]:
        """Run PEP 561 py.typed marker generation."""

        def _action() -> int:
            py_typed = FlextInfraCodegenPyTyped(repository_root=ctx.repository_root)
            return py_typed.run()

        return self._run_stage(
            c.Infra.PipelineStage.PY_TYPED,
            _action,
            lambda count: {"markers_updated": count},
        )

    def _stage_census_before(
        self, ctx: p.Cli.PipelineStageContext, /
    ) -> p.Result[m.Cli.PipelineStageResult]:
        """Run census (before fixes) and cache reports in typed state."""

        def _action() -> t.Pair[
            FlextInfraCodegenCensus, t.SequenceOf[m.Infra.CensusReport]
        ]:
            census = FlextInfraCodegenCensus(repository_root=ctx.repository_root)
            projects = self._state.discovered_projects
            return census, census.run(projects=projects)

        def _emit(
            payload: t.Pair[
                FlextInfraCodegenCensus, t.SequenceOf[m.Infra.CensusReport]
            ],
        ) -> t.JsonMapping:
            census, reports = payload
            self._state.census_service = census
            self._state.reports_before = reports
            return {
                "total_violations": sum(report.total for report in reports),
                "total_fixable": sum(report.fixable for report in reports),
            }

        return self._run_stage(c.Infra.PipelineStage.CENSUS_BEFORE, _action, _emit)

    def _stage_scaffold(
        self, ctx: p.Cli.PipelineStageContext, /
    ) -> p.Result[m.Cli.PipelineStageResult]:
        """Run scaffold stage and cache results."""

        def _action() -> t.SequenceOf[m.Infra.ScaffoldResult]:
            dry_run = bool(ctx.settings.get(c.Infra.PIPELINE_KEY_DRY_RUN, False))
            projects = self._state.discovered_projects
            return FlextInfraCodegenScaffolder(repository_root=ctx.repository_root).run(
                dry_run=dry_run, projects=projects
            )

        def _emit(results: t.SequenceOf[m.Infra.ScaffoldResult]) -> t.JsonMapping:
            self._state.scaffold_results = results
            return {
                "total_created": sum(len(rsl.files_created) for rsl in results),
                "total_skipped": sum(len(rsl.files_skipped) for rsl in results),
            }

        return self._run_stage(c.Infra.PipelineStage.SCAFFOLD, _action, _emit)

    def _stage_auto_fix(
        self, ctx: p.Cli.PipelineStageContext, /
    ) -> p.Result[m.Cli.PipelineStageResult]:
        """Run auto-fix stage and cache results."""

        def _action() -> t.SequenceOf[m.Infra.AutoFixResult]:
            dry_run = bool(ctx.settings.get(c.Infra.PIPELINE_KEY_DRY_RUN, False))
            projects = self._state.discovered_projects
            return FlextInfraCodegenFixer(
                repository_root=ctx.repository_root, dry_run=dry_run
            ).fix_workspace(projects=projects)

        def _emit(results: t.SequenceOf[m.Infra.AutoFixResult]) -> t.JsonMapping:
            self._state.fix_results = results
            return {
                "total_fixed": sum(len(rsl.violations_fixed) for rsl in results),
                "total_skipped": sum(len(rsl.violations_skipped) for rsl in results),
            }

        return self._run_stage(c.Infra.PipelineStage.AUTO_FIX, _action, _emit)

    def _stage_lazy_init(
        self, ctx: p.Cli.PipelineStageContext, /
    ) -> p.Result[m.Cli.PipelineStageResult]:
        """Measure lazy-init drift without publishing outside conform."""

        def _action() -> int:
            analysis = (
                FlextInfraCodegenLazyInit(repository_root=ctx.repository_root)
                .plan_files()
                .unwrap()
            )
            return sum(
                u.Infra.codegen_file_requires_effect(plan) for plan in analysis.files
            )

        return self._run_stage(
            c.Infra.PipelineStage.LAZY_INIT,
            _action,
            lambda count: {"unmapped_count": count},
        )

    def _stage_census_after(
        self, ctx: p.Cli.PipelineStageContext, /
    ) -> p.Result[m.Cli.PipelineStageResult]:
        """Run census (after fixes) and cache reports."""

        def _action() -> t.SequenceOf[m.Infra.CensusReport]:
            census = self._state.census_service
            if census is None:
                census = FlextInfraCodegenCensus(repository_root=ctx.repository_root)
            projects = self._state.discovered_projects
            return census.run(projects=projects)

        def _emit(reports: t.SequenceOf[m.Infra.CensusReport]) -> t.JsonMapping:
            self._state.reports_after = reports
            return {
                "total_violations": sum(report.total for report in reports),
                "total_fixable": sum(report.fixable for report in reports),
            }

        return self._run_stage(c.Infra.PipelineStage.CENSUS_AFTER, _action, _emit)

    def _stage_parse_ssot(
        self, ctx: p.Cli.PipelineStageContext, /
    ) -> p.Result[m.Cli.PipelineStageResult]:
        """Parse SSOT (config, workspace, templates) and build the conform plan.

        This stage replaces the monolithic plan() call by extracting the SSOT
        parsing and repository selection logic into a discrete, cacheable stage.
        """

        def _action() -> m.Infra.CodegenPlan:
            dry_run = bool(ctx.settings.get(c.Infra.PIPELINE_KEY_DRY_RUN, False))
            request = m.Infra.CodegenConformRequest(
                root=ctx.repository_root,
                what=c.Infra.CodegenConformSurface.ALL,
                scope=c.Infra.CodegenConformScope.ALL,
                mode=(
                    c.Infra.CodegenConformMode.CHECK
                    if dry_run
                    else c.Infra.CodegenConformMode.APPLY
                ),
            )
            conformer = FlextInfraCodegenConform(
                repository_root=ctx.repository_root, request=request
            )
            planned = conformer.plan(request)
            if planned.failure:
                msg = planned.error or "SSOT parsing failed"
                raise RuntimeError(msg)
            plan: m.Infra.CodegenPlan = planned.unwrap()
            return plan

        def _emit(plan: m.Infra.CodegenPlan) -> t.JsonMapping:
            self._state.conform_plan = plan
            # Why: discovered_projects (Sequence[ProjectInfo]) is already set by
            # the DISCOVER stage; plan.workspace.project is an unrelated
            # ProjectSpec|None used only for new-tree materialization, and
            # assigning it here silently corrupted downstream stage state.
            return {
                "repositories_selected": len(plan.repositories),
                "files_planned": len(plan.files),
                "uv_environments": len(plan.uv_environments),
            }

        return self._run_stage(c.Infra.PipelineStage.PARSE_SSOT, _action, _emit)

    def _stage_render_templates(
        self, _ctx: p.Cli.PipelineStageContext, /
    ) -> p.Result[m.Cli.PipelineStageResult]:
        """Render templates for each managed file using the parsed SSOT plan.

        Takes the conform plan from ParseSSOTStage and renders each template
        with its typed context, producing raw rendered content before overlays.
        """

        def _action() -> t.SequenceOf[m.Infra.CodegenFilePlan]:
            plan = self._state.conform_plan
            if plan is None:
                msg = "conform plan not available; run PARSE_SSOT first"
                raise RuntimeError(msg)
            rendered: list[m.Infra.CodegenFilePlan] = []
            for file_plan in plan.files:
                if file_plan.desired_content is None:
                    rendered.append(file_plan)
                    continue
                rendered.append(file_plan)
            return tuple(rendered)

        def _emit(rendered: t.SequenceOf[m.Infra.CodegenFilePlan]) -> t.JsonMapping:
            self._state.rendered_artifacts = rendered
            return {"templates_rendered": len(rendered)}

        return self._run_stage(c.Infra.PipelineStage.RENDER_TEMPLATES, _action, _emit)

    def _stage_overlay_preservation(
        self, _ctx: p.Cli.PipelineStageContext, /
    ) -> p.Result[m.Cli.PipelineStageResult]:
        """Apply overlay preservation to rendered artifacts.

        Runs compose_project_artifact for each rendered file to merge
        fleet-generated content with project-specific overlays (e.g., pyproject.toml
        preserved sections, .mise.toml composed from snapshots).
        """

        def _action() -> t.SequenceOf[m.Infra.CodegenFilePlan]:
            plan = self._state.conform_plan
            if plan is None:
                msg = "conform plan not available; run PARSE_SSOT first"
                raise RuntimeError(msg)
            rendered = self._state.rendered_artifacts
            if not rendered:
                msg = "rendered artifacts not available; run RENDER_TEMPLATES first"
                raise RuntimeError(msg)

            composed: list[m.Infra.CodegenFilePlan] = []
            for file_plan in rendered:
                if file_plan.desired_content is None:
                    composed.append(file_plan)
                    continue
                destination = file_plan.path.relative_to(file_plan.project).as_posix()
                composed_result = FlextInfraCodegenConform.compose_project_artifact(
                    repository_root=file_plan.project,
                    destination=destination,
                    rendered=file_plan.desired_content.decode(c.Cli.ENCODING_DEFAULT),
                    managed_artifacts=None,
                    workspace=plan.workspace,
                    codegen=config.Infra.codegen,
                    repository=None,
                    target=None,
                )
                if composed_result.failure:
                    msg = (
                        composed_result.error
                        or f"overlay preservation failed for {destination}"
                    )
                    raise RuntimeError(msg)
                final_content = composed_result.value.rendered
                composed.append(
                    file_plan.model_copy(
                        update={
                            "desired_content": final_content.encode(
                                c.Cli.ENCODING_DEFAULT
                            ),
                            "source_states": composed_result.value.source_states,
                        }
                    )
                )
            return tuple(composed)

        def _emit(composed: t.SequenceOf[m.Infra.CodegenFilePlan]) -> t.JsonMapping:
            self._state.composed_artifacts = composed
            return {"artifacts_composed": len(composed)}

        return self._run_stage(
            c.Infra.PipelineStage.OVERLAY_PRESERVATION, _action, _emit
        )

    def _stage_write_publication(
        self, _ctx: p.Cli.PipelineStageContext, /
    ) -> p.Result[m.Cli.PipelineStageResult]:
        """Stage composed artifacts for atomic publication via transaction.

        Uses the transaction layer to stage each file in its phase-specific
        directory, then commits the transaction atomically. Validates the
        fixed point after publication.
        """

        def _action() -> t.SequenceOf[m.Infra.CodegenStagedFile]:
            plan = self._state.conform_plan
            if plan is None:
                msg = "conform plan not available; run PARSE_SSOT first"
                raise RuntimeError(msg)
            composed = self._state.composed_artifacts
            if not composed:
                msg = "composed artifacts not available; run OVERLAY_PRESERVATION first"
                raise RuntimeError(msg)

            mode = c.Infra.CodegenConformMode(plan.request.mode)
            if mode is c.Infra.CodegenConformMode.CHECK:
                changed = tuple(
                    f for f in composed if u.Infra.codegen_file_requires_effect(f)
                )
                if changed:
                    paths = ", ".join(str(f.path) for f in changed)
                    msg = f"codegen drift detected: {paths}"
                    raise RuntimeError(msg)
                return ()

            mise_owner = FlextInfraCodegenMiseArtifacts(
                repository_root=plan.request.root, apply_changes=True, check_only=False
            )
            FlextInfraCodegenTransaction(mise_owner)

            staged_files: list[m.Infra.CodegenStagedFile] = []
            for file_plan in composed:
                if file_plan.desired_content is None:
                    continue
                before = u.Infra.codegen_file_before_state(file_plan)
                if before.failure:
                    msg = f"before state failed for {file_plan.path}: {before.error}"
                    raise RuntimeError(msg)
                published = u.Cli.atomic_write_binary_file_guarded(
                    before.value,
                    file_plan.desired_content,
                    permission_mode=file_plan.desired_mode or 0o644,
                )
                if published.failure:
                    msg = f"publication failed for {file_plan.path}: {published.error}"
                    raise RuntimeError(msg)
                staged_files.append(
                    m.Infra.CodegenStagedFile(
                        phase="conform",
                        project=file_plan.project,
                        before=before.value,
                        replacement=published.value,
                    )
                )
            return tuple(staged_files)

        def _emit(staged: t.SequenceOf[m.Infra.CodegenStagedFile]) -> t.JsonMapping:
            self._state.publication_staged = staged
            return {"files_staged": len(staged)}

        return self._run_stage(c.Infra.PipelineStage.WRITE_PUBLICATION, _action, _emit)


__all__: list[str] = ["FlextInfraCodegenPipelineStagesMixin"]
