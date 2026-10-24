"""Lazy-init ``__init__.py`` publication planner (PEP 562).

Auto-discovers exports from sibling ``.py`` files and describes clean
lazy-loading ``__init__.py`` artifacts using ``flext_core``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter
from typing import TYPE_CHECKING, Annotated, override

from flext_infra import c, config, m, r, t, u
from flext_infra.codegen import (
    FlextInfraCodegenLazyInitGenerationMixin,
    FlextInfraCodegenLazyInitPlanner,
    FlextInfraCodegenLazyInitProjectionManifest,
)
from flext_infra.workspace import FlextInfraRopeWorkspace

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenLazyInit(
    FlextInfraCodegenLazyInitGenerationMixin,
):
    """Plan ``__init__.py`` artifacts with PEP 562 lazy imports.

    Scans sibling ``.py`` files in each package directory, discovers their
    exports, and returns immutable file plans for the generation transaction.
    Processes bottom-up so child packages are generated before parents.
    """

    _modified_files: t.Infra.StrSet = m.PrivateAttr(default_factory=set)
    _source_indexes: t.MutableMappingKV[
        Path, t.Pair[m.Infra.RopeWorkspaceIndex, m.Infra.CodegenPhaseAnalysis]
    ] = m.PrivateAttr(
        default_factory=dict[
            Path, t.Pair[m.Infra.RopeWorkspaceIndex, m.Infra.CodegenPhaseAnalysis]
        ],
    )
    project_scope_roots: Annotated[
        t.VariadicTuple[Path] | None,
        m.Field(
            default=...,
            description=(
                "Repository roots selected by conformance; None plans every "
                "package of the workspace"
            ),
        ),
    ] = None

    @property
    def modified_files(self) -> t.StrSequence:
        """Initializer artifacts whose immutable plans require an effect."""
        return tuple(sorted(self._modified_files))

    @override
    def execute(self) -> p.Result[bool]:
        """Check lazy-init drift; publication belongs to conform's transaction.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        planned = self.plan_files()
        if planned.failure:
            return r[bool].from_failure(planned)
        if planned.value.exception is not None:
            raise planned.value.exception
        if planned.value.issues:
            return r[bool].fail(
                "; ".join(issue.formatted for issue in planned.value.issues)
            )
        if not self.effective_dry_run:
            return r[bool].fail(
                "lazy-init publication is owned by codegen conform; "
                "the generation transaction must publish plan_files()",
            )
        changed = tuple(
            plan
            for plan in planned.value.files
            if u.Infra.codegen_file_requires_effect(plan)
        )
        if changed:
            drifted_files = ", ".join(str(plan.path) for plan in changed)
            return r[bool].fail(
                f"init drift detected in {len(changed)} "
                f"generated artifacts: {drifted_files}",
            )
        return r[bool].ok(value=True)

    def plan_files(
        self,
        *,
        source_project: p.Infra.RopeProject | None = None,
        source_publications: t.MutableSequenceOf[
            t.Pair[Path, m.Infra.CodegenPhaseAnalysis]
        ]
        | None = None,
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Return one complete immutable lazy-init analysis receipt.

        Planning is read-only; conform owns effects and aggregate evidence.

        Returns:
            One complete immutable lazy-init analysis receipt.

        """
        # Receipts belong to this invocation's authority alone.
        self._source_indexes.clear()
        self._publication_receipts.clear()
        self._modified_files.clear()
        if not (
            self.repository_root.is_dir()
            if source_project is None
            else source_project.source_query(self.repository_root, "isdir")
        ):
            return r[m.Infra.CodegenPhaseAnalysis].fail(
                f"lazy-init workspace is not a directory: {self.repository_root}",
            )
        started_at = perf_counter()
        u.Cli.info(
            f"lazy-init: planning read-only artifacts for {self.repository_root}",
        )
        planned = self._plan_in_workspace(
            source_project=source_project,
            source_publications=source_publications,
        )
        if planned.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(planned)
        analysis = planned.value
        changed = tuple(
            plan
            for plan in analysis.files
            if u.Infra.codegen_file_requires_effect(plan)
        )
        self._modified_files.update(str(plan.path) for plan in changed)
        u.Cli.info(
            f"Lazy-init plan: {len(changed)} effects "
            f"({perf_counter() - started_at:.2f}s)",
        )
        return r[m.Infra.CodegenPhaseAnalysis].ok(analysis)

    def _plan_in_workspace(
        self,
        *,
        source_project: p.Infra.RopeProject | None = None,
        source_publications: t.MutableSequenceOf[
            t.Pair[Path, m.Infra.CodegenPhaseAnalysis]
        ]
        | None = None,
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Plan once against one original epoch with isolated artifact consumers.

        Selected roots have canonical physical-path order. The enclosing
        transaction owns aggregate evidence publication after verified effects;
        planning has no filesystem effects. File plans, publications and issues
        retain physical attribution, with manifests after ordered root plans.
        Each completed output retains its authentic native input receipt.
        Changed dependencies retain the original exception beside independent
        plans; publication re-proves each component without re-planning.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenPhaseAnalysis]``.

        """
        roots = (
            (self.repository_root.resolve(),)
            if self.project_scope_roots is None
            else tuple(sorted({root.resolve() for root in self.project_scope_roots}))
        )
        if not roots:
            return r[m.Infra.CodegenPhaseAnalysis].ok(
                m.Infra.CodegenPhaseAnalysis(
                    phase=c.Infra.CodegenStagedFilePhase.LAZY_INIT,
                    files=(),
                    inputs=(),
                ),
            )
        publications: list[t.Pair[Path, m.Infra.CodegenPhaseAnalysis]] = []
        failures: list[m.Infra.CodegenPhaseAnalysis] = []
        with self._source_binding(
            self.repository_root.resolve(),
            source_project,
            roots,
            (publications, failures),
        ) as project:
            with project.source_consumption() as consumption:
                planned = self._plan_roots(roots, source_project=project)
            if planned.success:
                publications.extend(
                    (Path(path), receipt)
                    for path, receipt in self._publication_receipts.items()
                )
                for target, receipt in planned.value.failed_targets:
                    publications.append((target, receipt))
            else:
                receipt = consumption.receipt()
                publications.append((self.repository_root.resolve(), receipt))
            if source_project is not None:
                verified = u.Infra.verify_source_publications(project, publications)
                if verified.issues:
                    failures.append(verified)
        if source_publications is not None:
            source_publications.extend(publications)
        if planned.failure:
            return planned
        return r[m.Infra.CodegenPhaseAnalysis].ok(
            self.composed_analysis((planned.value, *failures))
            if failures
            else planned.value
        )

    def _plan_roots(
        self,
        roots: t.VariadicTuple[Path],
        *,
        source_project: p.Infra.RopeProject,
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Compose explicitly selected repositories without widening their indexes.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenPhaseAnalysis]``.

        """
        composed_analyses = self._composed_repository_analyses(
            roots, source_project=source_project
        )
        if composed_analyses.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(composed_analyses)
        analyses, _inputs, target_roots = composed_analyses.value
        if self.module and not target_roots and not analyses:
            return r[m.Infra.CodegenPhaseAnalysis].fail(
                f"lazy-init target module not found: {self.module}",
            )
        composed = tuple(file for analysis in analyses for file in analysis.files)
        manifests = (
            FlextInfraCodegenLazyInitProjectionManifest.projection_manifest_plans(
                files=composed,
            )
        )
        if manifests.failure:
            original = self._first_recorded_exception(analyses)
            if original is not None:
                return r[m.Infra.CodegenPhaseAnalysis].fail(
                    f"{original}\n{manifests.error}",
                    exception=original,
                )
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(manifests)
        return r[m.Infra.CodegenPhaseAnalysis].ok(
            self.composed_analysis(analyses, manifests=manifests.value)
        )

    @classmethod
    def plan_scope_root(cls, scope: t.Pair[Path, Path]) -> m.Infra.CodegenPhaseAnalysis:
        """Plan one selected repository of a workspace as an independent fleet task.

        The workspace authority binds only the selected repository, exactly as
        a one-root ``project_scope_roots`` invocation does, so fleet workers can
        plan the repositories of one generation concurrently.

        Args:
            scope: The workspace authority root and the selected repository root.

        Returns:
            The selected repository's complete analysis receipt.

        """
        return (
            cls(repository_root=scope[0], project_scope_roots=(scope[1],))
            .plan_files()
            .unwrap()
        )

    @classmethod
    def composed_analysis(
        cls,
        analyses: t.SequenceOf[m.Infra.CodegenPhaseAnalysis],
        *,
        manifests: t.VariadicTuple[m.Infra.CodegenFilePlan] = (),
    ) -> m.Infra.CodegenPhaseAnalysis:
        """Fold per-repository analyses into one phase analysis receipt.

        Args:
            analyses: Per-repository analyses in canonical root order.
            manifests: Projection manifest plans derived from the composed files.

        Returns:
            One analysis whose inputs and directory receipts derive from every
            composed file and publication.

        """
        composed = (
            *(file for analysis in analyses for file in analysis.files),
            *manifests,
        )
        publications = tuple(
            plan for analysis in analyses for plan in analysis.publications
        )
        directories, topology = u.Cli.atomic_merge_directory_query_receipts(
            tuple(item for plan in composed for item in plan.source_directories)
            + tuple(item for plan in publications for item in plan.source_directories),
            tuple(item for plan in composed for item in plan.source_query_topology)
            + tuple(
                item for plan in publications for item in plan.source_query_topology
            ),
        )
        return m.Infra.CodegenPhaseAnalysis(
            phase=c.Infra.CodegenStagedFilePhase.LAZY_INIT,
            files=composed,
            inputs=m.Infra.CodemodBindingSnapshot(
                states=tuple(state for plan in composed for state in plan.source_states)
                + tuple(state for plan in publications for state in plan.source_states),
            ).states,
            source_directories=directories,
            source_query_topology=topology,
            publications=publications,
            failed_targets=tuple(
                target for analysis in analyses for target in analysis.failed_targets
            ),
            issues=tuple(issue for analysis in analyses for issue in analysis.issues),
            exception=cls._first_recorded_exception(analyses),
        )

    @staticmethod
    @contextmanager
    def _source_binding(
        root: Path,
        source_project: p.Infra.RopeProject | None,
        scope_roots: t.VariadicTuple[Path],
        source_publications: t.Pair[
            t.MutableSequenceOf[t.Pair[Path, m.Infra.CodegenPhaseAnalysis]],
            t.MutableSequenceOf[m.Infra.CodegenPhaseAnalysis],
        ],
    ) -> Generator[p.Infra.RopeProject]:
        """Bind the shared original authority without replacing an injected epoch.

        Yields:
            The shared source authority, not a warmed semantic consumer.

        Raises:
            ValueError: When the injected authority does not cover the
                invocation root.

        """
        if source_project is None:
            # The authority elects exactly the selected scope roots inside this
            # repository: unselected members stay installed libraries and are
            # never captured or indexed here.
            with u.Infra.facade_source_project(
                root,
                project_roots=tuple(
                    scope for scope in scope_roots if scope.is_relative_to(root)
                ),
                source_publications=source_publications,
            ) as binding:
                yield binding[0]
            return
        if not source_project.authenticated_sources or not root.is_relative_to(
            Path(source_project.root.real_path)
        ):
            msg = "lazy-init consumer is outside its authenticated original authority"
            raise ValueError(msg)
        yield source_project

    def _composed_repository_analyses(
        self,
        roots: t.VariadicTuple[Path],
        *,
        source_project: p.Infra.RopeProject,
    ) -> p.Result[
        t.Triple[
            list[m.Infra.CodegenPhaseAnalysis],
            t.MappingKV[Path, m.Cli.AtomicFileState],
            int,
        ]
    ]:
        """Plan every selected repository and fold their shared inputs.

        Returns:
            The resulting ``p.Result[t.Triple[list[m.Infra.CodegenPhaseAnalysis],
                t.MappingKV[Path, m.Cli.AtomicFileState], int]]``.

        """
        analyses: list[m.Infra.CodegenPhaseAnalysis] = []
        inputs: t.MutableMappingKV[Path, m.Cli.AtomicFileState] = {}
        candidates = self._target_repository_candidates(roots, source_project)
        consumption: p.Infra.RopeSourceConsumption | None = None
        target_roots = sum(len(paths) for paths, _ in candidates.values())
        for root in roots:
            if root in candidates and not candidates[root][0]:
                continue
            consumption = None
            if (
                not root.is_relative_to(self.repository_root.resolve())
                or not root.is_dir()
            ):
                analyzed = r[m.Infra.CodegenPhaseAnalysis].fail(
                    "lazy-init repository scope is missing or outside "
                    f"{self.repository_root.resolve()}: {root}",
                )
            else:
                with self._root_workspace(root, source_project) as (
                    consumption,
                    binding,
                    rope,
                ):
                    if root in candidates:
                        binding.replay_source_consumption(
                            candidates[root][1].receipt(),
                        )
                    analyzed = self._authenticated_root_analysis(
                        rope,
                        analyses=analyses,
                    )
            if analyzed.failure:
                receipt = consumption.receipt() if consumption is not None else None
                analysis = m.Infra.CodegenPhaseAnalysis(
                    phase=c.Infra.CodegenStagedFilePhase.LAZY_INIT,
                    files=(),
                    inputs=receipt.inputs if receipt is not None else (),
                    source_directories=(
                        receipt.source_directories if receipt is not None else ()
                    ),
                    source_query_topology=(
                        receipt.source_query_topology if receipt is not None else ()
                    ),
                    failed_targets=((root, receipt),) if receipt is not None else (),
                    issues=(
                        m.Infra.Issue(
                            file=str(root),
                            line=0,
                            column=0,
                            code=c.Infra.ToolOutcome.ERROR.value,
                            message=analyzed.error
                            or f"lazy-init analysis failed: {root}",
                            locations=(),
                            related_locations=(),
                        ),
                    ),
                    exception=analyzed.exception,
                )
            else:
                analysis = analyzed.value
            if (
                target_roots > 1
                and root in candidates
                and candidates[root][0]
                and consumption is not None
            ):
                analysis = analysis.model_copy(
                    update={
                        "files": (),
                        "publications": (),
                        "failed_targets": ((root, consumption.receipt()),),
                        "issues": (
                            *analysis.issues,
                            m.Infra.Issue(
                                file=str(root),
                                line=0,
                                column=0,
                                code=c.Infra.ToolOutcome.ERROR.value,
                                message=(
                                    "lazy-init target module is ambiguous: "
                                    f"{self.module}"
                                ),
                                locations=(),
                                related_locations=(),
                            ),
                        ),
                    }
                )
            analyses.append(analysis)
            inputs = self._merged_input_states(inputs, analysis, analyses)
        return r[
            t.Triple[
                list[m.Infra.CodegenPhaseAnalysis],
                t.MappingKV[Path, m.Cli.AtomicFileState],
                int,
            ]
        ].ok((analyses, inputs, target_roots))

    @staticmethod
    def _first_recorded_exception(
        analyses: t.SequenceOf[m.Infra.CodegenPhaseAnalysis],
    ) -> BaseException | None:
        """Read the first exception an earlier analysis already recorded.

        Returns:
            The first recorded exception, or ``None`` when none recorded.

        """
        return next(
            (item.exception for item in analyses if item.exception is not None),
            None,
        )

    def _authenticated_root_analysis(
        self,
        rope: FlextInfraRopeWorkspace,
        *,
        analyses: t.SequenceOf[m.Infra.CodegenPhaseAnalysis],
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Plan one repository against its authenticated source authority.

        Returns:
            One selected repository's analysis.

        """
        result_type = r[m.Infra.CodegenPhaseAnalysis]
        planned = self._plan_open_workspace(rope)
        if planned.failure:
            original = self._first_recorded_exception(analyses)
            if original is not None:
                return result_type.fail(
                    f"{original}\n{planned.error}", exception=original
                )
            return result_type.from_failure(planned)
        return result_type.ok(planned.value)

    @staticmethod
    def _merged_input_states(
        inputs: t.MappingKV[Path, m.Cli.AtomicFileState],
        analysis: m.Infra.CodegenPhaseAnalysis,
        analyses: t.SequenceOf[m.Infra.CodegenPhaseAnalysis],
    ) -> t.MutableMappingKV[Path, m.Cli.AtomicFileState]:
        """Fold one repository's input states into the shared per-path mapping.

        Returns:
            The unique captured states indexed by their physical paths.

        """
        runtime_errors: tuple[type[Exception], ...] = (OSError, *c.EXC_BROAD_RUNTIME)
        try:
            merged = m.Infra.CodemodBindingSnapshot(
                states=(*inputs.values(), *analysis.inputs)
            ).states
        except runtime_errors as exc:
            original = FlextInfraCodegenLazyInit._first_recorded_exception(analyses)
            if original is not None:
                raise original from exc
            raise
        return {state.path: state for state in merged}

    @contextmanager
    def _root_workspace(
        self,
        root: Path,
        source_project: p.Infra.RopeProject,
    ) -> Generator[
        t.Triple[
            p.Infra.RopeSourceConsumption,
            p.Infra.RopeProject,
            FlextInfraRopeWorkspace,
        ]
    ]:
        """Open one root's indexed workspace inside its own consumption scope.

        Yields:
            The consumption scope, the isolated consumer and its workspace.

        """
        indexed = self._source_indexes.get(root)
        with (
            source_project.source_consumption() as consumption,
            source_project.source_consumer(consumer_root=root) as binding,
            FlextInfraRopeWorkspace.open_workspace(
                root,
                rope_repository_root=Path(binding.root.real_path),
                source_project=binding,
                workspace_index=indexed[0] if indexed is not None else None,
                index_receipt=indexed[1] if indexed is not None else None,
            ) as rope,
        ):
            yield consumption, binding, rope

    def _target_repository_candidates(
        self,
        roots: t.VariadicTuple[Path],
        source_project: p.Infra.RopeProject,
    ) -> t.MutableMappingKV[
        Path, t.Pair[t.VariadicTuple[Path], p.Infra.RopeSourceConsumption]
    ]:
        """Capture the selected target packages before repository analysis.

        Returns:
            Candidate paths and their original native source consumption.

        """
        candidates: t.MutableMappingKV[
            Path, t.Pair[t.VariadicTuple[Path], p.Infra.RopeSourceConsumption]
        ] = {}
        if self.module:
            for root in roots:
                if (
                    not root.is_relative_to(self.repository_root.resolve())
                    or not root.is_dir()
                ):
                    continue
                with self._root_workspace(root, source_project) as (
                    consumption,
                    _binding,
                    rope,
                ):
                    candidates[root] = (
                        self._target_package_dirs(rope.workspace_index, root),
                        consumption,
                    )
                    self._source_indexes[root] = (
                        rope.workspace_index,
                        rope.source_index_receipt,
                    )
        return candidates

    def _target_package_dirs(
        self,
        index: m.Infra.RopeWorkspaceIndex,
        root: Path,
    ) -> t.VariadicTuple[Path]:
        """Resolve the target through the current repository's authenticated index.

        Returns:
            The resulting ``t.VariadicTuple[Path]``.

        """
        if self.module is None:
            return ()
        mapped = index.package_dir_by_name.get(self.module)
        targets = {
            entry.package_dir.resolve()
            for entry in index.modules_by_path.values()
            if entry.module_name == self.module
            and (self.project_scope_roots is None or entry.project_root == root)
        }
        if mapped is not None and (
            self.project_scope_roots is None
            or index.packages_by_dir[str(mapped)].project_root == root
        ):
            targets.add(mapped.resolve())
        return tuple(sorted(targets))

    def _plan_open_workspace(
        self,
        rope: FlextInfraRopeWorkspace,
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Build immutable plans from one stable Rope workspace snapshot.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenPhaseAnalysis]``.

        """
        self._source_project = rope.rope_project
        workspace_index = rope.workspace_index
        resolved_repository_root = rope.repository_root.resolve()
        candidate_entries = tuple(
            workspace_index.packages_by_dir[str(package_dir)]
            for package_dir in workspace_index.package_dirs
            if package_dir.is_relative_to(resolved_repository_root)
            and not frozenset(package_dir.relative_to(resolved_repository_root).parts)
            & c.Infra.OBSOLETE_ROOT_SUPPORT_NAMES
        )
        if self.project_scope_roots is not None:
            unowned = tuple(
                entry.package_dir
                for entry in candidate_entries
                if entry.project_root is None
            )
            if unowned:
                return r[m.Infra.CodegenPhaseAnalysis].fail(
                    f"lazy-init package has no repository owner: {unowned[0]}",
                )
            candidate_entries = tuple(
                entry
                for entry in candidate_entries
                if entry.project_root == rope.repository_root.resolve()
            )
        indexed_package_dirs = tuple(
            sorted(
                (entry.package_dir.resolve() for entry in candidate_entries),
                key=u.Infra.path_depth,
                reverse=True,
            ),
        )
        target = self._resolved_target_package_dir(
            workspace_index,
            indexed_package_dirs,
            resolved_repository_root,
        )
        if target.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(target)
        package_dirs = self._package_dirs_for_target(
            indexed_package_dirs,
            target_package_dir=target.value[0],
        )
        with rope.rope_project.source_capture():
            snapshots = self._snapshot_planner_inputs(
                workspace_index,
                package_dirs,
                source_project=rope.rope_project,
            )
        if snapshots.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(snapshots)
        return self._analyzed_workspace(
            rope,
            package_dirs,
            target.value[0],
            workspace_index,
            snapshots.value,
        )

    def _resolved_target_package_dir(
        self,
        workspace_index: m.Infra.RopeWorkspaceIndex,
        indexed_package_dirs: t.VariadicTuple[Path],
        repository_root: Path,
    ) -> p.Result[t.Pair[Path | None, bool]]:
        """Resolve the single target package dir when a target module is set.

        Returns:
            The resulting ``p.Result[t.Pair[Path | None, bool]]`` where the
            boolean marks resolution (False: no target module is set).

        """
        result_type = r[t.Pair[Path | None, bool]]
        if not self.module:
            return result_type.ok((None, False))
        sorted_target_dirs = self._target_package_dirs(
            workspace_index,
            repository_root,
        )
        if not sorted_target_dirs:
            return result_type.fail(
                f"lazy-init target module not found: {self.module}",
            )
        if sorted_target_dirs[1:]:
            return result_type.fail(
                f"lazy-init target module is ambiguous: {self.module}",
            )
        target_package_dir = sorted_target_dirs[0]
        if target_package_dir not in indexed_package_dirs:
            return result_type.fail(
                f"lazy-init target belongs to retired support: {self.module}",
            )
        return result_type.ok((target_package_dir, True))

    def _analyzed_workspace(
        self,
        rope: FlextInfraRopeWorkspace,
        package_dirs: t.VariadicTuple[Path],
        target_package_dir: Path | None,
        workspace_index: m.Infra.RopeWorkspaceIndex,
        snapshots: t.MappingKV[Path, m.Cli.AtomicFileState],
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Plan every initializer, build file plans, and re-verify snapshots.

        One writer per destination (render purity, v4 §2.1): templates own
        every generated surface; alignment is a semantic phase of ``make
        mod`` (codemod/semantic_apply.py phase 0), never a second writer
        inside the gen transaction.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenPhaseAnalysis]``.

        """
        result_type = r[m.Infra.CodegenPhaseAnalysis]
        planner = FlextInfraCodegenLazyInitPlanner(
            rope_workspace=rope,
            lazy_init=config.Infra.tooling.lazy_init,
        )
        u.Cli.info(f"lazy-init: planning {len(package_dirs)} package dirs")
        package_plans = planner.plan_all_inits(
            package_dirs,
            target_package_dir=target_package_dir,
        )
        if package_plans.failure:
            return result_type.from_failure(package_plans)
        file_plans = self._build_file_plans(
            package_plans.value,
            index=workspace_index,
            snapshots=snapshots,
            source_receipts={
                str(plan.context.pkg_dir.resolve()): planner.source_receipt(
                    plan.context.pkg_dir
                )
                for plan in package_plans.value
            },
        )
        if file_plans.failure:
            return result_type.from_failure(file_plans)
        all_plans = file_plans.value
        analysis = m.Infra.CodegenPhaseAnalysis(
            phase=c.Infra.CodegenStagedFilePhase.LAZY_INIT,
            files=all_plans,
            inputs=(),
            publications=tuple(
                plan.model_copy(
                    update={
                        "source_states": receipt.inputs,
                        "source_directories": receipt.source_directories,
                        "source_query_topology": receipt.source_query_topology,
                    }
                )
                for plan in package_plans.value
                for receipt in (
                    self._publication_receipts[str(plan.context.pkg_dir.resolve())],
                )
            ),
        )
        return result_type.ok(self.composed_analysis((analysis,)))

    @staticmethod
    def _package_dirs_for_target(
        indexed_package_dirs: t.SequenceOf[Path],
        *,
        target_package_dir: Path | None,
    ) -> t.VariadicTuple[Path]:
        """Plan only the target tree; native reads capture external dependencies.

        Returns:
            The resulting ``t.VariadicTuple[Path]``.

        """
        if target_package_dir is None:
            return tuple(indexed_package_dirs)
        return tuple(
            package_dir
            for package_dir in indexed_package_dirs
            if package_dir.is_relative_to(target_package_dir)
        )


__all__: list[str] = ["FlextInfraCodegenLazyInit"]
