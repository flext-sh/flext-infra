"""Desired-state file, environment, and retirement plans.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from functools import partial
from pathlib import Path

from flext_infra import FlextInfraConfig, c, m, p, r, t, u
from flext_infra.codegen._conform.bootstrap import FlextInfraCodegenConformBootstrap
from flext_infra.deps import phases as dependency_phases


class FlextInfraCodegenConformFilePlans(FlextInfraCodegenConformBootstrap):
    """Desired-state file, environment, and retirement plans."""

    @classmethod
    def repository_kind_declaration_plans(
        cls,
        root: Path,
        inputs: m.Infra.CodegenInputs,
        kind: c.Infra.ProjectKind,
    ) -> p.Result[tuple[m.Infra.CodegenFilePlan], ...]:
        """Publish an explicit kind only into the requested target's own source.

        Returns:
            The declaration plan, none when already declared, or the conflict.

        """
        result_type = r[tuple[m.Infra.CodegenFilePlan], ...]
        effective = inputs.spec.repository
        if "kind" in effective.model_fields_set and effective.kind != kind:
            return result_type.fail(
                "bootstrap kind conflicts with the target's effective "
                f"declaration: {root}",
            )
        layers = FlextInfraConfig.config_layer_paths_for_repository(
            root,
            filename=c.Infra.CODEGEN_CONFIG_FILENAME,
        )
        declared = cls._declared_kind_plans(layers[1], inputs, kind)
        if declared is not None:
            return declared
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
        return cls._codegen_declaration_plan(root, layers[1], values).map(
            lambda declaration: (declaration,)
        )

    @classmethod
    def _declared_kind_plans(
        cls,
        own_path: Path,
        inputs: m.Infra.CodegenInputs,
        kind: c.Infra.ProjectKind,
    ) -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]] | None:
        """Guard the target's own ``kind`` declaration.

        Returns:
            The conflict failure, no plans when the same kind is already
            declared, or ``None`` when no own declaration exists to guard.

        """
        own = next((state for state in inputs.sources if state.path == own_path), None)
        if own is None or own.content is None:
            return None
        document = u.Infra.read_codegen_config_document(own.content)
        if document.failure:
            return r[tuple[m.Infra.CodegenFilePlan, ...]].from_failure(document)
        declared = u.Cli.json_walk_path(
            document.value,
            ("Infra", "codegen", "repository", "kind"),
        )
        if declared is None:
            return None
        if declared != kind.value:
            return r[tuple[m.Infra.CodegenFilePlan, ...]].fail(
                f"bootstrap kind conflicts with the target's declaration: {own_path}",
            )
        return r[tuple[m.Infra.CodegenFilePlan, ...]].ok(())

    @classmethod
    def _codegen_declaration_plan(
        cls,
        root: Path,
        path: Path,
        values: t.JsonMapping,
    ) -> p.Result[m.Infra.CodegenFilePlan]:
        """Merge project YAML through its canonical config primitive.

        Returns:
            The declaration plan preserving all unrelated configuration values.

        """
        result_type = r[m.Infra.CodegenFilePlan]
        project = root.expanduser().absolute()
        target = path.expanduser().absolute()
        before = u.Infra.codegen_target_snapshot(target)
        if before.failure:
            return result_type.from_failure(before)
        payload: t.JsonMapping = {}
        if before.value.content is not None:
            parsed = u.Infra.read_codegen_config_document(before.value.content)
            if parsed.failure:
                return result_type.from_failure(parsed)
            payload = parsed.value
        serialized = r[str].create_from_callable(
            partial(
                u.Cli.yaml_dump_str,
                u.config_merge(dict(payload), {"Infra": {"codegen": dict(values)}}),
            ),
        )
        if serialized.failure:
            return result_type.from_failure(serialized)
        return result_type.ok(
            m.Infra.CodegenFilePlan(
                project=project,
                path=target,
                before=before.value,
                desired_content=serialized.value.encode(c.DEFAULT_ENCODING),
                desired_mode=0o644,
            )
        )

    @classmethod
    def repository_declaration_migration_plans(
        cls,
        root: Path,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[tuple[m.Infra.CodegenFilePlan], ...]:
        """Project self-owned declarations before retiring their input.

        This is an explicit migration operation, not a configuration source.
        Runtime codegen inputs continue to come exclusively from their typed
        library, repository and local layers.

        Returns:
            The own declaration and its retirement, or the first failure.

        """
        result_type = r[tuple[m.Infra.CodegenFilePlan], ...]
        legacy_path = u.Infra.workspace_manifest_path(root)
        project = inputs.spec.repository.project
        resource_owned = project is not None and any(
            legacy_path.is_relative_to(root / path)
            for path in project.packaged_data_paths
        )
        captured = (
            None if resource_owned else cls._captured_declaration_migration(legacy_path)
        )
        if captured is None:
            return result_type.ok(())
        if captured.failure:
            return result_type.from_failure(captured)
        state, delta, legacy = captured.value
        if delta.project is not None:
            project = delta.project
            selected = (
                dependency_phases.FlextInfraEnsurePackagingPhase.resolve_data_paths
            )(
                root,
                project.package_name,
                project.packaged_data_paths,
            )
            dependency_phases.FlextInfraEnsurePackagingPhase.resolve_data_excludes(
                root,
                selected,
                project.packaged_data_excludes,
            )
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
        compatible = cls._repository_declaration_admits(own_source, delta)
        if compatible is not None and compatible.failure:
            return result_type.from_failure(compatible)
        return cls._repository_declaration_retirement_plans(
            root,
            inputs,
            state,
            delta,
            legacy,
        )

    @classmethod
    def _captured_declaration_migration(
        cls,
        legacy_path: Path,
    ) -> (
        p.Result[
            t.Triple[
                m.Cli.AtomicFileState,
                m.Infra.RepositoryDeltaSpec,
                m.Infra.WorkspaceManifestSpec,
            ]
        ]
        | None
    ):
        """Read and validate the captured manifest with its declaration delta.

        Returns:
            The captured state with its validated declaration delta, or
            ``None`` when no manifest content is captured.

        """
        result_type = r[
            t.Triple[
                m.Cli.AtomicFileState,
                m.Infra.RepositoryDeltaSpec,
                m.Infra.WorkspaceManifestSpec,
            ]
        ]
        captured = u.Cli.atomic_read_binary_file_state(legacy_path, required=False)
        if captured.failure:
            return result_type.from_failure(captured)
        if captured.value.content is None:
            return None
        parsed = u.Infra.read_codegen_config_document(captured.value.content)
        if parsed.failure:
            return result_type.from_failure(parsed)
        legacy = u.validate_value(m.Infra.WorkspaceManifestSpec, parsed.value)
        if legacy.failure:
            return result_type.from_failure(legacy)
        delta = u.Infra.repository_declaration_delta(legacy.value)
        if delta.failure:
            return result_type.from_failure(delta)
        return result_type.ok((captured.value, delta.value, legacy.value))

    @staticmethod
    def _repository_declaration_admits(
        own_source: m.Cli.AtomicFileState | None,
        delta: m.Infra.RepositoryDeltaSpec,
    ) -> p.Result[bool] | None:
        """Check a captured own declaration against the migration delta.

        Returns:
            The compatibility verdict, or ``None`` when no own declaration
            content is captured.

        """
        if own_source is None or own_source.content is None:
            return None
        return FlextInfraCodegenConformFilePlans._repository_declaration_compatible(
            own_source.content,
            delta,
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
    ) -> p.Result[tuple[m.Infra.CodegenFilePlan], ...]:
        """Validate the projected declaration before planning input retirement.

        The input is retired unless its bytes are a declared resource.

        Returns:
            The source declaration and its dependent retirement.

        """
        result_type = r[tuple[m.Infra.CodegenFilePlan], ...]
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
        )
        if declaration.failure:
            return result_type.from_failure(declaration)
        admitted = cls._retirement_admitted(root, inputs, legacy)
        if admitted.failure:
            return result_type.from_failure(admitted)
        if delta.project is not None and any(
            captured.path.is_relative_to(root / path)
            for path in delta.project.packaged_data_paths
        ):
            return result_type.ok((declaration.value,))
        return result_type.ok((
            declaration.value,
            m.Infra.CodegenFilePlan(
                project=root.expanduser().absolute(),
                path=captured.path,
                before=captured,
                desired_content=None,
                desired_mode=None,
                tracking_dependencies=(declaration.value.path,),
            ),
        ))

    @staticmethod
    def _retirement_admitted(
        root: Path,
        inputs: m.Infra.CodegenInputs,
        legacy: m.Infra.WorkspaceManifestSpec,
    ) -> p.Result[bool]:
        """Admit manifest retirement only once its consumers are covered.

        Returns:
            Acceptance, or the first retirement obstacle.

        """
        if legacy.external_consumers:
            discovered = u.Infra.discover_external_consumers(root, inputs)
            if discovered.failure:
                return r[bool].from_failure(discovered)
            covered = {consumer.root for consumer in discovered.value}
            missing = tuple(
                consumer
                for consumer in legacy.external_consumers
                if consumer.root.resolve() not in covered
            )
            if missing:
                return r[bool].fail(
                    "manifest retirement requires verified public host inventory "
                    "coverage for its external consumers: "
                    + ", ".join(str(consumer.root) for consumer in missing),
                )
        if legacy.candidate_dependencies:
            return r[bool].fail(
                "candidate dependency coordinates must be adopted by the "
                "declared dependency provenance before manifest retirement",
            )
        return r[bool].ok(value=True)

    @staticmethod
    def file_plan(
        root: Path,
        relative_path: str,
        rendered: str,
        *,
        mode: int = 0o644,
        ownership: m.Infra.ManagedFileOwnership | None = None,
    ) -> p.Result[m.Infra.CodegenFilePlan]:
        """Snapshot one target and bind it to exact desired bytes and ownership.

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
                owner="" if ownership is None else ownership.owner,
                policy=None if ownership is None else ownership.policy,
                tracking="versioned" if ownership is None else ownership.tracking,
            ),
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
        del workspace
        groups: tuple[str, ...] = ("dev", "codegen")
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
        retired = cls._retired_destination_plans(
            root,
            destinations,
            evidence_by_path,
        )
        if retired.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(retired)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(retired.value)

    @classmethod
    def _retired_destination_plans(
        cls,
        root: Path,
        destinations: t.SequenceOf[str],
        evidence_by_path: t.MappingKV[str, ...],
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Plan removal of every still-present retired destination file.

        Returns:
            The absence plans.

        """
        result_type = r[t.SequenceOf[m.Infra.CodegenFilePlan]]
        planned: list[m.Infra.CodegenFilePlan] = []
        # A retired directory retires each file under it; the generated
        # marker (or declared evidence) below still guards every removal.
        candidates = (
            (destination, path)
            for destination in destinations
            for path in (
                sorted(
                    item for item in (root / destination).rglob("*") if item.is_file()
                )
                if (root / destination).is_dir()
                else ((root / destination),)
            )
        )
        for destination, path in candidates:
            if not path.is_file():
                continue
            current = u.Cli.files_read_text(path)
            if current.failure:
                return result_type.from_failure(current)
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
                return result_type.from_failure(absent_plan)
            planned.append(
                absent_plan.value,
            )
        return result_type.ok(tuple(planned))


__all__: list[str] = ["FlextInfraCodegenConformFilePlans"]
