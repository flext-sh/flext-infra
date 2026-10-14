"""Desired-state file, environment, and retirement plans.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from functools import partial
from pathlib import Path

from flext_core import FlextStrictYamlConfigSource
from flext_infra import FlextInfraConfig, c, m, p, r, t, u
from flext_infra._utilities.workspace_inventory import (
    FlextInfraUtilitiesWorkspaceInventory,
)
from flext_infra.codegen._conform import FlextInfraCodegenConformBeadsRoutes


class FlextInfraCodegenConformFilePlans(FlextInfraCodegenConformBeadsRoutes):
    """Desired-state file, environment, and retirement plans."""

    @classmethod
    def repository_kind_declaration_plans(
        cls,
        root: Path,
        inputs: m.Infra.CodegenInputs,
        kind: c.Infra.ProjectKind,
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Publish an explicit kind only into the requested target's own source.

        Returns:
            A guarded source declaration, or the original input conflict.
        """
        result_type = r[m.Infra.CodegenPhaseAnalysis]
        effective = inputs.spec.repository
        if "kind" in effective.model_fields_set and effective.kind != kind:
            return result_type.fail(
                f"bootstrap kind conflicts with the target's effective declaration: {root}",
            )
        layers = FlextInfraConfig.config_layer_paths_for_repository(
            root,
            filename=c.Infra.CODEGEN_CONFIG_FILENAME,
        )
        own = next((state for state in inputs.sources if state.path == layers[1]), None)
        if own is not None and own.content is not None:
            document = u.Infra.read_codegen_config_document(own.content)
            if document.failure:
                return result_type.from_failure(document)
            declared = u.Cli.json_walk_path(
                document.value,
                ("Infra", "codegen", "repository", "kind"),
            )
            if declared is not None:
                if declared != kind.value:
                    return result_type.fail(
                        f"bootstrap kind conflicts with the target's declaration: {layers[1]}",
                    )
                return result_type.ok(
                    m.Infra.CodegenPhaseAnalysis(
                        phase=c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP,
                        files=(),
                        inputs=inputs.sources,
                    )
                )
        values: t.JsonMapping = {"repository": {"kind": kind.value}}
        composed = u.Infra.project_codegen_inputs(
            root,
            inputs,
            projections=(
                m.Infra.CodegenLayerProjection(
                    path=layers[1],
                    values={"Infra": {"codegen": dict(values)}},
                ),
            ),
        )
        if composed.failure:
            return result_type.from_failure(composed)
        if composed.value.spec.repository.kind != kind:
            return result_type.fail(
                f"bootstrap kind is overridden by the target's elected layers: {root}",
            )
        declaration = cls._codegen_declaration_plan(
            root,
            layers[1],
            values,
            sources=inputs.sources,
        )
        if declaration.failure:
            return result_type.from_failure(declaration)
        return result_type.ok(
            m.Infra.CodegenPhaseAnalysis(
                phase=c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP,
                files=(declaration.value,),
                inputs=inputs.sources,
            )
        )

    @classmethod
    def _codegen_declaration_plan(
        cls,
        root: Path,
        path: Path,
        values: t.JsonMapping,
        *,
        sources: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> p.Result[m.Infra.CodegenFilePlan]:
        """Merge captured project YAML through its canonical config primitive.

        Returns:
            A guarded source plan preserving all unrelated configuration values.
        """
        result_type = r[m.Infra.CodegenFilePlan]
        captured = cls.file_plan(
            root,
            path.relative_to(root).as_posix(),
            "",
            source_states=sources,
        )
        if captured.failure:
            return result_type.from_failure(captured)
        before = captured.value.before
        original = next((state for state in sources if state.path == path), None)
        if original is not None and before != original:
            error = ValueError(
                f"codegen declaration changed after input capture: {path}"
            )
            return result_type.fail(str(error), exception=error)
        if (
            original is None
            and isinstance(before, m.Cli.AtomicFileState)
            and before.content is not None
        ):
            error = ValueError(
                f"codegen declaration appeared after input capture: {path}"
            )
            return result_type.fail(str(error), exception=error)
        payload: t.JsonMapping = {}
        if isinstance(before, m.Cli.AtomicFileState) and before.content is not None:
            parsed = u.Infra.read_codegen_config_document(before.content)
            if parsed.failure:
                return result_type.from_failure(parsed)
            payload = parsed.value
        merged = FlextStrictYamlConfigSource.merge_values(
            dict(payload),
            {"Infra": {"codegen": dict(values)}},
        )
        serialized = r[str].create_from_callable(
            partial(u.Cli.yaml_dump_str, merged),
        )
        if serialized.failure:
            return result_type.from_failure(serialized)
        return result_type.ok(
            captured.value.model_copy(
                update={"desired_content": serialized.value.encode(c.DEFAULT_ENCODING)},
            ),
        )

    @classmethod
    def repository_declaration_migration_plans(
        cls,
        root: Path,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Project captured self-owned declarations before retiring their input.

        This is an explicit migration operation, not a configuration source.
        Runtime codegen inputs continue to come exclusively from their typed
        library, repository and local layers.

        Returns:
            The guarded own declaration and independent retirement diagnostics.
        """
        result_type = r[m.Infra.CodegenPhaseAnalysis]
        legacy_path = u.Infra.workspace_manifest_path(root)
        captured = u.Cli.atomic_read_binary_file_state(legacy_path, required=False)
        if captured.failure:
            return result_type.from_failure(captured)
        if captured.value.content is None:
            return result_type.ok(
                m.Infra.CodegenPhaseAnalysis(
                    phase=c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP,
                    files=(),
                    inputs=inputs.sources,
                ),
            )
        parsed = u.Infra.read_codegen_config_document(captured.value.content)
        if parsed.failure:
            return result_type.from_failure(parsed)
        legacy = u.validate_value(m.Infra.WorkspaceManifestSpec, parsed.value)
        if legacy.failure:
            return result_type.from_failure(legacy)
        delta = u.Infra.repository_declaration_delta(legacy.value)
        if delta.failure:
            return result_type.from_failure(delta)
        layers = FlextInfraConfig.config_layer_paths_for_repository(
            root,
            filename=c.Infra.CODEGEN_CONFIG_FILENAME,
        )
        if layers[0].resolve() == layers[1].resolve():
            error = ValueError(
                "repository declarations share the distributed codegen defaults",
            )
            return result_type.fail(str(error), exception=error)
        own_source = next(
            (state for state in inputs.sources if state.path == layers[1]),
            None,
        )
        if own_source is not None and own_source.content is not None:
            compatible = cls._repository_declaration_compatible(
                own_source.content,
                delta.value,
            )
            if compatible.failure:
                return result_type.from_failure(compatible)
        return cls._repository_declaration_retirement_plans(
            root,
            inputs,
            captured.value,
            delta.value,
            legacy.value,
        )

    @staticmethod
    def _repository_declaration_compatible(
        content: bytes,
        delta: m.Infra.RepositoryDeltaSpec,
    ) -> p.Result[bool]:
        """Reject conflicts with explicitly captured repository declarations.

        Returns:
            Whether the captured declaration admits the migration input.
        """
        own_document = u.Infra.read_codegen_config_document(content)
        if own_document.failure:
            return r[bool].from_failure(own_document)
        own_values = u.Cli.json_walk_path(
            own_document.value,
            ("Infra", "codegen", "repository"),
        )
        if own_values is None:
            return r[bool].ok(value=True)
        own_delta = u.validate_value(m.Infra.RepositoryDeltaSpec, own_values)
        if own_delta.failure:
            return r[bool].from_failure(own_delta)
        conflicting = tuple(
            field
            for field in own_delta.value.model_fields_set
            if getattr(own_delta.value, field) != getattr(delta, field)
        )
        if conflicting:
            error = ValueError(
                "repository declarations conflict with migration input: "
                + ", ".join(sorted(conflicting)),
            )
            return r[bool].fail(str(error), exception=error)
        return r[bool].ok(value=True)

    @classmethod
    def _repository_declaration_retirement_plans(
        cls,
        root: Path,
        inputs: m.Infra.CodegenInputs,
        captured: m.Cli.AtomicFileState,
        delta: m.Infra.RepositoryDeltaSpec,
        legacy: m.Infra.WorkspaceManifestSpec,
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Validate the projected declaration before planning input retirement.

        Returns:
            The guarded source declaration and its dependent retirement.
        """
        result_type = r[m.Infra.CodegenPhaseAnalysis]
        layers = FlextInfraConfig.config_layer_paths_for_repository(
            root,
            filename=c.Infra.CODEGEN_CONFIG_FILENAME,
        )
        values = delta.model_dump(
            mode="json",
            exclude_none=True,
            exclude_defaults=True,
            exclude_computed_fields=True,
        )
        composed = u.Infra.project_codegen_inputs(
            root,
            inputs,
            projections=(
                m.Infra.CodegenLayerProjection(
                    path=layers[1],
                    values={"Infra": {"codegen": {"repository": values}}},
                ),
            ),
        )
        if composed.failure:
            return result_type.from_failure(composed)
        declaration = cls._codegen_declaration_plan(
            root,
            layers[1],
            {"repository": values},
            sources=(*inputs.sources, captured),
        )
        if declaration.failure:
            return result_type.from_failure(declaration)
        retirement_obstacles: list[str] = []
        first_exception: BaseException | None = None
        if legacy.external_consumers:
            discovered = (
                FlextInfraUtilitiesWorkspaceInventory.discover_external_consumers(
                    root,
                    inputs,
                )
            )
            if discovered.failure:
                retirement_obstacles.append(str(discovered.error))
                first_exception = discovered.exception
            else:
                covered = {consumer.root for consumer in discovered.value}
                missing = tuple(
                    consumer
                    for consumer in legacy.external_consumers
                    if consumer.root.resolve() not in covered
                )
                if missing:
                    retirement_obstacles.append(
                        "manifest retirement requires verified public host inventory "
                        "coverage for its external consumers: "
                        + ", ".join(str(consumer.root) for consumer in missing),
                    )
        if legacy.candidate_dependencies:
            retirement_obstacles.append(
                "candidate dependency coordinates must be adopted by the "
                "declared dependency provenance before manifest retirement",
            )
        if retirement_obstacles:
            exception = first_exception or ValueError(retirement_obstacles[0])
            return result_type.ok(
                m.Infra.CodegenPhaseAnalysis(
                    phase=c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP,
                    files=(declaration.value,),
                    inputs=(*inputs.sources, captured),
                    issues=tuple(
                        m.Infra.Issue(
                            file=str(captured.path),
                            line=0,
                            column=0,
                            code=c.Infra.ToolOutcome.ERROR.value,
                            message=message,
                        )
                        for message in retirement_obstacles
                    ),
                    exception=exception,
                ),
            )
        retirement = cls._absent_file_plan(root, captured.path)
        if retirement.failure:
            return result_type.from_failure(retirement)
        if retirement.value.before != captured:
            error = ValueError(
                "repository declaration changed after migration input capture",
            )
            return result_type.fail(str(error), exception=error)
        return result_type.ok(
            m.Infra.CodegenPhaseAnalysis(
                phase=c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP,
                files=(
                    declaration.value,
                    retirement.value.model_copy(
                        update={"tracking_dependencies": (declaration.value.path,)},
                    ),
                ),
                inputs=(*inputs.sources, captured),
            ),
        )

    @staticmethod
    def file_plan(
        root: Path,
        relative_path: str,
        rendered: str,
        *,
        mode: int = 0o644,
        source_states: t.VariadicTuple[m.Cli.AtomicFileState] = (),
    ) -> p.Result[m.Infra.CodegenFilePlan]:
        """Snapshot one target and bind it to exact desired bytes and mode.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenFilePlan]``.

        """
        project = root.expanduser().absolute()
        path = (project / relative_path).absolute()
        before = u.Infra.codegen_target_snapshot(path)
        if before.failure:
            return r[m.Infra.CodegenFilePlan].from_failure(before)
        return r[m.Infra.CodegenFilePlan].ok(
            m.Infra.CodegenFilePlan(
                project=project,
                path=path,
                before=before.value,
                desired_content=rendered.encode(c.DEFAULT_ENCODING),
                desired_mode=mode,
                source_states=source_states,
            ),
        )

    @staticmethod
    def mise_config_plans(
        plan: m.Infra.CodegenPlan,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Select one planned Mise configuration for each selected repository.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]``.

        """
        expected = tuple(
            environment.project_root / c.Infra.MISE_TOML_FILENAME
            for environment in plan.uv_environments
        )
        if not expected:
            return r[t.VariadicTuple[m.Infra.CodegenFilePlan]].fail(
                "conform plan carries no uv environment plan for the selected "
                "repositories; the Mise transaction requires one configuration "
                "per repository",
            )
        by_path = {item.path: item for item in plan.files if item.path in expected}
        if len(set(expected)) != len(expected) or len(by_path) != len(expected):
            return r[t.VariadicTuple[m.Infra.CodegenFilePlan]].fail(
                "conform plan must contain one Mise configuration per repository",
            )
        return r[t.VariadicTuple[m.Infra.CodegenFilePlan]].ok(
            tuple(by_path[path] for path in expected),
        )

    @staticmethod
    def uv_environment_plan(
        *,
        root: Path,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        config: m.Infra.CodegenConfigSpec,
    ) -> m.Infra.UvEnvironmentPlan:
        """Describe the exact setup overlay without executing uv.

        Returns:
            The resulting ``m.Infra.UvEnvironmentPlan``.

        """
        # The native uv workspace provisions the members (`uv sync
        # --all-packages`); no extra dependency group and no editable overlay
        # plan exist any more.
        _ = workspace
        groups: t.VariadicTuple[str] = ("dev", "codegen")
        return m.Infra.UvEnvironmentPlan(
            project_root=root,
            environment_root=target.root,
            python_version=config.toolchain.python_version,
            groups=groups,
        )

    @staticmethod
    def _absent_file_plan(root: Path, path: Path) -> p.Result[m.Infra.CodegenFilePlan]:
        """Plan the removal of one retired projection.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenFilePlan]``.

        """
        target = path.expanduser().absolute()
        before = u.Cli.atomic_read_binary_file_state(target, required=True)
        if before.failure:
            return r[m.Infra.CodegenFilePlan].from_failure(before)
        return r[m.Infra.CodegenFilePlan].ok(
            m.Infra.CodegenFilePlan(
                project=root.expanduser().absolute(),
                path=target,
                before=before.value,
                desired_content=None,
                desired_mode=None,
            ),
        )

    @staticmethod
    def _retired_destinations(
        codegen: m.Infra.CodegenConfigSpec,
    ) -> p.Result[t.Pair[t.SequenceOf[str], t.MappingKV[str, str]]]:
        """Collect declared retired projections with their removal evidence.

        Returns:
            The resulting ``p.Result[t.Pair[t.SequenceOf[str],
                t.MappingKV[str, str]]]``.

        """
        result_type = r[t.Pair[t.SequenceOf[str], t.MappingKV[str, str]]]
        extra: list[str] = []
        evidence_by_path: t.StrDict = {}
        for retired in codegen.retired_projections:
            declared = retired if isinstance(retired, str) else retired.path
            relative = Path(declared)
            if relative.is_absolute() or ".." in relative.parts:
                return result_type.fail(
                    "retired projection must be a normalized relative path: "
                    f"{declared}",
                )
            if isinstance(retired, str):
                extra.append(retired)
                continue
            evidence_by_path[retired.path] = retired.evidence
            extra.append(retired.path)
        return result_type.ok((extra, evidence_by_path))

    @classmethod
    def retired_projection_plans(
        cls,
        root: Path,
        profile: c.Infra.MakeProfile,
        *,
        inputs: m.Infra.CodegenInputs | None = None,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Plan removal of generated projections this profile no longer renders.

        A projection retires either because its template entry excludes this
        profile or because no template renders it any more (a renamed or
        deleted template, declared in ``retired_projections``). Either way only
        a file carrying the generated marker is removed.

        Returns:
            The resulting ``p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]``.

        """
        if inputs is None:
            loaded = u.Infra.load_codegen_inputs(root)
            if loaded.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(loaded)
            inputs = loaded.value
        planned: list[m.Infra.CodegenFilePlan] = []
        destinations: list[str] = [
            entry.destination
            for entry in inputs.spec.templates.entries
            if profile not in entry.profiles and "{" not in entry.destination
        ]
        collected = cls._retired_destinations(inputs.spec)
        if collected.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(collected)
        extra_destinations, evidence_by_path = collected.value
        destinations.extend(extra_destinations)
        for destination in destinations:
            path = root / Path(destination)
            if not path.is_file():
                continue
            current = u.Cli.files_read_text(path)
            if current.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(current)
            evidence = evidence_by_path.get(destination)
            if evidence is not None:
                if evidence not in current.value:
                    continue
            elif not any(
                marker in current.value for marker in c.Infra.TEMPLATE_GENERATED_MARKERS
            ):
                continue
            absent_plan = cls._absent_file_plan(root, path)
            if absent_plan.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(
                    absent_plan,
                )
            planned.append(
                absent_plan.value.model_copy(
                    update={"source_states": inputs.sources},
                ),
            )
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(planned))


__all__: list[str] = ["FlextInfraCodegenConformFilePlans"]
