"""Conformance planning of governed artifacts and runtime-local bindings.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import FlextInfraConfig, c, m, p, r, t, u
from flext_infra.services._codegen import FlextInfraCodegenVscodeMixin
from flext_infra.workspace import FlextInfraWorkspaceEnvironmentContracts


class FlextInfraCodegenConformExistingPlanGovernedMixin:
    """Represent governed artifacts with their declared ownership and tracking."""

    if TYPE_CHECKING:
        generation_only: bool
        initial_workspace: m.Infra.WorkspaceSpec | None

        @staticmethod
        def file_plan(
            root: Path,
            relative_path: str,
            rendered: str,
            *,
            mode: int = 0o644,
            source_states: t.VariadicTuple[m.Cli.AtomicFileState] = (),
        ) -> p.Result[m.Infra.CodegenFilePlan]: ...

        @classmethod
        def _codegen_declaration_plan(
            cls,
            root: Path,
            path: Path,
            values: t.JsonMapping,
            *,
            sources: t.VariadicTuple[m.Cli.AtomicFileState],
        ) -> p.Result[m.Infra.CodegenFilePlan]: ...

        def _record_file_failure(
            self,
            path: Path,
            error: str,
            *,
            exception: BaseException | None = None,
        ) -> None: ...

    def _complete_governed_plans(
        self,
        target: m.Infra.RepositoryConformTarget,
        planned: t.SequenceOf[m.Infra.CodegenFilePlan],
        codegen: m.Infra.CodegenConfigSpec,
        contract: m.Infra.CodegenConformSurfaceContract,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Attach ownership metadata and represent every governed root artifact.

        Only the ``ALL`` surface completes the full governed set; the
        pyproject-scoped surfaces (``DEPENDENCIES``/``PYPROJECT``) keep the plan
        restricted to what their own planners already produced.

        Returns:
            The resulting ``p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]``.

        """
        root = target.root
        governed_by_path = {
            item.path: item
            for item in codegen.managed_file_specs
            if target.beads is not None or item.path.parts[:1] != (".beads",)
        }
        bound = self._bind_governed_ownership(root, planned, governed_by_path)
        if bound.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(bound)
        completed, represented = bound.value
        if not contract.complete_governed:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(completed))
        # Native views render after collection from every project's desired metadata.
        pending_artifacts = {
            path: item
            for path, item in governed_by_path.items()
            if path not in represented and path not in codegen.uv_resolution_pyprojects
        }
        represented_set = self._represent_ungoverned_artifacts(
            target,
            codegen,
            pending_artifacts,
        )
        if represented_set.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(
                represented_set,
            )
        completed.extend(represented_set.value)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(completed))

    @staticmethod
    def _bind_governed_ownership(
        root: Path,
        planned: t.SequenceOf[m.Infra.CodegenFilePlan],
        governed_by_path: t.MappingKV[Path, m.Infra.ManagedFileSpec],
    ) -> p.Result[t.Pair[list[m.Infra.CodegenFilePlan], set[Path]]]:
        """Stamp governed ownership onto the planned files, first plan wins.

        Returns:
            The resulting ``p.Result[t.Pair[list[m.Infra.CodegenFilePlan],
                set[Path]]]`` with the bound plans and the represented paths.

        """
        completed: list[m.Infra.CodegenFilePlan] = []
        represented: set[Path] = set()
        represented_indexes: MutableMapping[Path, int] = {}
        for file in planned:
            relative = file.path.relative_to(root)
            governed = governed_by_path.get(relative)
            if governed is None:
                completed.append(file)
                continue
            represented.add(relative)
            governed_file = file.model_copy(
                update={
                    "owner": governed.owner,
                    "policy": governed.policy,
                    "desired_mode": (
                        governed.mode if file.desired_content is not None else None
                    ),
                },
            )
            if relative in represented_indexes:
                completed[represented_indexes[relative]] = governed_file
            else:
                represented_indexes[relative] = len(completed)
                completed.append(governed_file)
        return r[t.Pair[list[m.Infra.CodegenFilePlan], set[Path]]].ok(
            (completed, represented),
        )

    def plan_runtime_bindings(
        self,
        target: m.Infra.RepositoryConformTarget,
        codegen: m.Infra.CodegenConfigSpec,
        *,
        vscode_spec: m.Infra.CodegenVscodeSpec | None = None,
        codegen_inputs: m.Infra.CodegenInputs | None = None,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Plan only bindings selected by their declared artifact policy.

        Returns:
            Runtime-local file plans, including missing declared bindings.

        """
        planned = self._represent_ungoverned_artifacts(
            target
            if vscode_spec is None
            else target.model_copy(
                update={"vscode_spec": vscode_spec},
            ),
            codegen,
            {
                item.path: item
                for item in codegen.managed_file_specs
                if item.runtime_binding
            },
            codegen_inputs=codegen_inputs,
            migrate_tracking=not self.generation_only,
        )
        if planned.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(planned)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(planned.value)

    def _represent_ungoverned_artifacts(
        self,
        target: m.Infra.RepositoryConformTarget,
        codegen: m.Infra.CodegenConfigSpec,
        governed_by_path: t.MappingKV[Path, m.Infra.ManagedFileSpec],
        *,
        migrate_tracking: bool = False,
        codegen_inputs: m.Infra.CodegenInputs | None = None,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Plan every unrepresented governed artifact in the mapping.

        Args:
            target: The conform target whose root owns the artifacts.
            codegen: The codegen configuration governing the artifacts.
            governed_by_path: Governed artifacts keyed by repository-relative
                path.
            migrate_tracking: Whether runtime-local editor tracking migrates.
            codegen_inputs: Captured codegen inputs for migration planning.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]``
            carrying one plan per represented artifact; per-artifact failures
            are recorded and skipped.

        """
        plans: list[m.Infra.CodegenFilePlan] = []
        root = target.root
        profile = target.make_profile
        vscode_spec = target.vscode_spec
        runtime_root = (
            root
            if self.initial_workspace is not None
            and target.repository.name == self.initial_workspace.repository.name
            else None
        )
        for relative, governed in governed_by_path.items():
            path = root / relative
            if path.exists() and not path.is_file():
                error = ValueError(f"governed artifact is not a regular file: {path}")
                self._record_file_failure(
                    path,
                    str(error),
                    exception=error,
                )
                continue
            if not self._governed_entry_reachable(codegen, profile, relative):
                continue
            if not path.exists() and not governed.runtime_binding:
                continue
            current = self._governed_current_text(path)
            if current.failure:
                self._record_file_failure(
                    path,
                    current.error or "cannot read governed artifact",
                    exception=current.exception,
                )
                continue
            request = m.Infra.CodegenGovernedPlanRequest(
                root=root,
                relative=relative,
                governed=governed,
                current=current.value,
                runtime_root=runtime_root,
                vscode_spec=vscode_spec,
                source_states=target.vscode_sources,
            )
            if (
                migrate_tracking
                and governed.tracking == "runtime-local"
                and governed.owner == c.Infra.CODEGEN_OWNER_VSCODE
                and runtime_root is None
            ):
                migrated = self._vscode_tracking_plans(
                    request,
                    codegen_inputs=codegen_inputs,
                )
                if migrated.failure:
                    self._record_file_failure(
                        path,
                        migrated.error or "cannot plan runtime tracking migration",
                        exception=migrated.exception,
                    )
                    continue
                plans.extend(migrated.value)
                continue
            decided = self._decide_governed_plan(request)
            if decided.failure:
                self._record_file_failure(
                    path,
                    decided.error or "cannot plan governed artifact",
                    exception=decided.exception,
                )
                continue
            decided_value, decided_present = decided.value
            if decided_present and decided_value is not None:
                plans.append(decided_value)
        return r[t.VariadicTuple[m.Infra.CodegenFilePlan]].ok(tuple(plans))

    @classmethod
    def _vscode_tracking_plans(
        cls,
        request: m.Infra.CodegenGovernedPlanRequest,
        *,
        codegen_inputs: m.Infra.CodegenInputs | None = None,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Plan portable declarations before the captured editor index retirement.

        Returns:
            Source declaration plans followed by the runtime-local binding plan.

        """
        result_type = r[t.VariadicTuple[m.Infra.CodegenFilePlan]]
        captured = u.Infra.git_capture_index_file(
            m.Infra.GitRelativePathRequest(
                repo_root=request.root,
                relative_path=request.relative.as_posix(),
            ),
        )
        if captured.failure:
            return result_type.from_failure(captured)
        state = captured.value
        if state.entry is None:
            binding = cls._vscode_merged_plan(request)
            if binding.failure:
                return result_type.from_failure(binding)
            return result_type.ok(
                () if binding.value[0] is None else (binding.value[0],),
            )
        settings = cls._vscode_tracking_settings(request, state)
        if settings.failure:
            return result_type.from_failure(settings)
        projected = cls._vscode_tracking_projection(
            request, *settings.value, codegen_inputs=codegen_inputs
        )
        if projected.failure:
            return result_type.from_failure(projected)
        effective, declarations = projected.value
        return cls._vscode_tracking_binding(request, state, effective, declarations)

    @staticmethod
    def _vscode_tracking_settings(
        request: m.Infra.CodegenGovernedPlanRequest,
        state: m.Infra.GitIndexFileState,
    ) -> p.Result[t.Pair[t.JsonMapping, t.JsonMapping]]:
        """Parse the captured index blob and live editor content independently.

        Returns:
            Indexed and live settings with their original parse failures.

        """
        result_type = r[t.Pair[t.JsonMapping, t.JsonMapping]]
        content = state.content
        if content is None:
            error = ValueError(
                f"captured editor index blob is absent: {request.relative}"
            )
            return result_type.fail(str(error), exception=error)
        decoded = r[str].create_from_callable(
            lambda: content.decode(c.DEFAULT_ENCODING),
        )
        if decoded.failure:
            return result_type.from_failure(decoded)
        indexed = FlextInfraCodegenVscodeMixin.parse_vscode_settings(decoded.value)
        live = FlextInfraCodegenVscodeMixin.parse_vscode_settings(request.current)
        if indexed.failure:
            return result_type.from_failure(indexed)
        if live.failure:
            return result_type.from_failure(live)
        return result_type.ok((indexed.value, live.value))

    @classmethod
    def _vscode_tracking_projection(
        cls,
        request: m.Infra.CodegenGovernedPlanRequest,
        indexed: t.JsonMapping,
        live: t.JsonMapping,
        *,
        codegen_inputs: m.Infra.CodegenInputs | None = None,
    ) -> p.Result[
        t.Pair[m.Infra.CodegenInputs, t.VariadicTuple[m.Infra.CodegenFilePlan]]
    ]:
        """Compose project and local overrides through captured config layers.

        Returns:
            Effective inputs and guarded source declaration plans.

        """
        result_type = r[
            t.Pair[m.Infra.CodegenInputs, t.VariadicTuple[m.Infra.CodegenFilePlan]]
        ]
        if codegen_inputs is None:
            loaded = u.Infra.load_codegen_inputs(request.root)
            if loaded.failure:
                return result_type.from_failure(loaded)
            codegen_inputs = loaded.value
        project = cls._vscode_project_projection(request.root, codegen_inputs, indexed)
        if project.failure:
            return result_type.from_failure(project)
        projections = project.value
        composed = u.Infra.project_codegen_inputs(
            request.root,
            codegen_inputs,
            projections=projections,
        )
        if composed.failure:
            return result_type.from_failure(composed)
        local = FlextInfraCodegenVscodeMixin.vscode_local_declaration_delta(
            request.root,
            indexed,
            live,
            spec=composed.value.spec.vscode,
        )
        if local.failure:
            return result_type.from_failure(local)
        if local.value.values:
            layers = FlextInfraConfig.config_layer_paths_for_repository(
                request.root,
                filename=c.Infra.CODEGEN_CONFIG_FILENAME,
            )
            projections = (
                *projections,
                m.Infra.CodegenLayerProjection(
                    path=layers[2],
                    values={"Infra": {"codegen": {"vscode": dict(local.value.values)}}},
                ),
            )
        effective = u.Infra.project_codegen_inputs(
            request.root,
            codegen_inputs,
            projections=projections,
        )
        if effective.failure:
            return result_type.from_failure(effective)
        return cls._vscode_declaration_plans(
            request.root,
            codegen_inputs,
            projections,
        ).map(lambda declarations: (effective.value, declarations))

    @staticmethod
    def _vscode_project_projection(
        root: Path,
        inputs: m.Infra.CodegenInputs,
        indexed: t.JsonMapping,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenLayerProjection]]:
        """Extract a portable project delta without promoting local configuration.

        Returns:
            A project-layer projection only when indexed settings differ.

        """
        result_type = r[t.VariadicTuple[m.Infra.CodegenLayerProjection]]
        baseline = u.Infra.project_codegen_inputs(
            root,
            inputs,
            include_local=False,
        )
        if baseline.failure:
            return result_type.from_failure(baseline)
        project = FlextInfraCodegenVscodeMixin.vscode_declaration_delta(
            root,
            indexed,
            spec=baseline.value.spec.vscode,
        )
        if project.failure:
            return result_type.from_failure(project)
        layers = FlextInfraConfig.config_layer_paths_for_repository(
            root,
            filename=c.Infra.CODEGEN_CONFIG_FILENAME,
        )
        if project.value.values and layers[1].resolve() == layers[0].resolve():
            error = ValueError(
                "project editor declarations share the distributed defaults: "
                f"{layers[1]}",
            )
            return result_type.fail(str(error), exception=error)
        return result_type.ok(
            (
                m.Infra.CodegenLayerProjection(
                    path=layers[1],
                    values={
                        "Infra": {"codegen": {"vscode": dict(project.value.values)}}
                    },
                ),
            )
            if project.value.values
            else ()
        )

    @classmethod
    def _vscode_declaration_plans(
        cls,
        root: Path,
        inputs: m.Infra.CodegenInputs,
        projections: t.VariadicTuple[m.Infra.CodegenLayerProjection],
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Bind each projected delta to its captured source without touching defaults.

        Returns:
            Guarded project and local configuration plans in dependency order.

        """
        result_type = r[t.VariadicTuple[m.Infra.CodegenFilePlan]]
        library = FlextInfraConfig.config_layer_paths_for_repository(
            root,
            filename=c.Infra.CODEGEN_CONFIG_FILENAME,
        )[0]
        declarations: list[m.Infra.CodegenFilePlan] = []
        for projection in projections:
            path = projection.path
            if path.resolve() == library.resolve():
                error = ValueError(
                    "project editor declarations share the distributed defaults: "
                    f"{path}",
                )
                return result_type.fail(str(error), exception=error)
            values = u.Cli.json_walk_path(projection.values, ("Infra", "codegen"))
            validated = u.validate_value(t.Cli.JSON_MAPPING_ADAPTER, values)
            if validated.failure:
                return result_type.from_failure(validated)
            planned = cls._codegen_declaration_plan(
                root,
                path,
                validated.value,
                sources=inputs.sources,
            )
            if planned.failure:
                return result_type.from_failure(planned)
            declarations.append(planned.value)
        return result_type.ok(tuple(declarations))

    @classmethod
    def _vscode_tracking_binding(
        cls,
        request: m.Infra.CodegenGovernedPlanRequest,
        state: m.Infra.GitIndexFileState,
        effective: m.Infra.CodegenInputs,
        declarations: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Retire captured tracking only after its portable declarations are written.

        Returns:
            Source declarations followed by their guarded editor binding.

        """
        result_type = r[t.VariadicTuple[m.Infra.CodegenFilePlan]]
        binding = cls._vscode_merged_plan(
            request.model_copy(
                update={
                    "vscode_spec": effective.spec.vscode,
                    "source_states": effective.sources,
                },
            ),
        )
        if binding.failure:
            return result_type.from_failure(binding)
        if binding.value[0] is None:
            error = ValueError(f"runtime binding plan is absent: {request.relative}")
            return result_type.fail(str(error), exception=error)
        return result_type.ok(
            (
                *declarations,
                binding.value[0].model_copy(
                    update={
                        "tracking": request.governed.tracking,
                        "index_before": state.entry,
                        "tracking_dependencies": tuple(
                            plan.path for plan in declarations
                        ),
                    },
                ),
            ),
        )

    @classmethod
    def _governed_entry_reachable(
        cls,
        codegen: m.Infra.CodegenConfigSpec,
        profile: c.Infra.MakeProfile,
        relative: Path,
    ) -> bool:
        """Whether any template entry for this destination admits the profile.

        Returns:
            True when no entry restricts the destination or the profile is
            among the admitted ones.

        """
        entry_profiles = tuple(
            entry.profiles
            for entry in codegen.templates.entries
            if entry.destination == relative.as_posix()
        )
        if not entry_profiles:
            return True
        allowed = {item for profiles in entry_profiles for item in profiles}
        return profile in allowed

    @staticmethod
    def _governed_current_text(path: Path) -> p.Result[str]:
        """Read the current bytes of an existing governed artifact.

        Returns:
            The resulting ``p.Result[str]``, empty for a non-file path.

        """
        if not path.is_file():
            return r[str].ok("")
        read = u.Cli.atomic_read_binary_file_state(path, required=True)
        if read.failure:
            return r[str].from_failure(read)
        content = read.value.content
        if content is None:
            error = ValueError(f"governed artifact has no captured bytes: {path}")
            return r[str].fail(str(error), exception=error)
        return r[str].create_from_callable(partial(content.decode, c.DEFAULT_ENCODING))

    @classmethod
    def _decide_governed_plan(
        cls,
        request: m.Infra.CodegenGovernedPlanRequest,
    ) -> p.Result[t.Pair[m.Infra.CodegenFilePlan | None, bool]]:
        """Decide the representing plan: owner merge first, plain content next.

        Returns:
            The resulting ``p.Result[t.Pair[m.Infra.CodegenFilePlan | None,
            bool]]`` with its presence flag.

        """
        special = cls._special_governed_plan(request)
        if special.failure:
            return special
        if special.value[0] is not None:
            return special
        if request.governed.runtime_binding and not special.value[1]:
            return r[t.Pair[m.Infra.CodegenFilePlan | None, bool]].fail(
                "runtime binding has no declared renderer: "
                f"{request.governed.owner} {request.relative}",
            )
        result_type = r[t.Pair[m.Infra.CodegenFilePlan | None, bool]]
        current_plan = cls.file_plan(
            request.root,
            request.relative.as_posix(),
            request.current,
            mode=request.governed.mode,
        )
        if current_plan.failure:
            return result_type.from_failure(current_plan)
        return r[t.Pair[m.Infra.CodegenFilePlan, bool]].ok(
            (
                current_plan.value.model_copy(
                    update={
                        "owner": request.governed.owner,
                        "policy": request.governed.policy,
                        "tracking": request.governed.tracking,
                    },
                ),
                True,
            ),
        )

    @classmethod
    def _special_governed_plan(
        cls,
        request: m.Infra.CodegenGovernedPlanRequest,
    ) -> p.Result[t.Pair[m.Infra.CodegenFilePlan | None, bool]]:
        """Plan owner-specific merge behavior for special governed artifacts.

        Returns:
            The resulting ``p.Result[t.Pair[m.Infra.CodegenFilePlan | None,
            bool]]`` where the boolean identifies a declared rendering owner.

        """
        vscode_merge = request.governed.policy == "merge" and (
            request.governed.owner == c.Infra.CODEGEN_OWNER_VSCODE
        )
        if vscode_merge:
            # Owner-merge dispatch: owners with a canonical document merge
            # (vscode settings today) produce their rendered content here.
            return cls._vscode_merged_plan(request)
        if request.governed.policy == "merge" and request.relative.as_posix() == (
            c.Infra.ENVRC_LOCAL_RELPATH
        ):
            # Local overrides never carry generated content: the merge strips
            # stale generated sections and deletes the file when nothing
            # custom remains, so `.envrc` stays the single beads owner.
            return cls._envrc_local_plan(request)
        return r[t.Pair[m.Infra.CodegenFilePlan, bool]].ok((None, False))

    @classmethod
    def _vscode_merged_plan(
        cls,
        request: m.Infra.CodegenGovernedPlanRequest,
    ) -> p.Result[t.Pair[m.Infra.CodegenFilePlan | None, bool]]:
        """Render the canonical vscode settings merge when it diverges.

        Returns:
            The resulting ``p.Result[t.Pair[m.Infra.CodegenFilePlan | None,
            bool]]`` with its presence flag.

        """
        result_type = r[t.Pair[m.Infra.CodegenFilePlan | None, bool]]
        spec = request.vscode_spec
        sources = request.source_states
        if spec is None:
            loaded = u.Infra.load_codegen_inputs(request.root)
            if loaded.failure:
                return result_type.from_failure(loaded)
            spec = loaded.value.spec.vscode
            sources = loaded.value.sources
        merged = FlextInfraCodegenVscodeMixin.render_vscode_settings(
            request.root,
            runtime_root=request.runtime_root,
            spec=spec,
        )
        if merged.failure:
            return result_type.from_failure(merged)
        merged_plan = cls.file_plan(
            request.root,
            request.relative.as_posix(),
            merged.value,
            mode=request.governed.mode,
            source_states=sources,
        )
        if merged_plan.failure:
            return result_type.from_failure(merged_plan)
        before = merged_plan.value.before
        if isinstance(before, m.Cli.AtomicFileState) and before.content != (
            request.current.encode(c.DEFAULT_ENCODING)
            if request.current
            else (b"" if before.content is not None else None)
        ):
            error = ValueError(
                f"editor settings changed during planning: {merged_plan.value.path}",
            )
            return result_type.fail(str(error), exception=error)
        return result_type.ok(
            (
                merged_plan.value.model_copy(
                    update={
                        "owner": request.governed.owner,
                        "policy": request.governed.policy,
                        "tracking": request.governed.tracking,
                    },
                ),
                True,
            ),
        )

    @classmethod
    def _envrc_local_plan(
        cls,
        request: m.Infra.CodegenGovernedPlanRequest,
    ) -> p.Result[t.Pair[m.Infra.CodegenFilePlan | None, bool]]:
        """Normalize the local envrc overrides or plan the file's deletion.

        Returns:
            The resulting ``p.Result[t.Pair[m.Infra.CodegenFilePlan | None,
            bool]]`` with its presence flag.

        """
        result_type = r[t.Pair[m.Infra.CodegenFilePlan | None, bool]]
        root = request.root
        relative = request.relative
        path = root / relative
        normalized = FlextInfraWorkspaceEnvironmentContracts.envrc_local_normalized(
            request.current,
        )
        if normalized == request.current:
            current_plan = cls.file_plan(
                root,
                relative.as_posix(),
                request.current,
                mode=request.governed.mode,
            )
            if current_plan.failure:
                return result_type.from_failure(current_plan)
            return result_type.ok(
                (
                    current_plan.value.model_copy(
                        update={
                            "owner": request.governed.owner,
                            "policy": request.governed.policy,
                        },
                    ),
                    True,
                ),
            )
        if not normalized:
            before = u.Cli.atomic_read_binary_file_state(path, required=False)
            if before.failure:
                return result_type.from_failure(before)
            return result_type.ok(
                (
                    m.Infra.CodegenFilePlan(
                        project=root,
                        path=path,
                        before=before.value,
                        desired_content=None,
                        desired_mode=None,
                        owner=request.governed.owner,
                        policy=request.governed.policy,
                    ),
                    True,
                ),
            )
        merged_plan = cls.file_plan(
            root,
            relative.as_posix(),
            normalized,
            mode=request.governed.mode,
        )
        if merged_plan.failure:
            return result_type.from_failure(merged_plan)
        return result_type.ok(
            (
                merged_plan.value.model_copy(
                    update={
                        "owner": request.governed.owner,
                        "policy": request.governed.policy,
                    },
                ),
                True,
            ),
        )


__all__: list[str] = ["FlextInfraCodegenConformExistingPlanGovernedMixin"]
