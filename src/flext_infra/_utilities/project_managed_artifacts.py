"""Load and compose project-owned managed-artifact configuration.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import stat
from collections.abc import Callable, Mapping, MutableMapping
from copy import deepcopy
from functools import lru_cache, partial
from pathlib import Path
from typing import ClassVar
from weakref import WeakKeyDictionary

from flext_cli import u
from flext_core import FlextStrictYamlConfigSource

from flext_infra import FlextInfraConfig, c, m, p, r, t
from flext_infra._utilities import FlextInfraUtilitiesNativeTooling


class FlextInfraUtilitiesProjectManagedArtifacts(FlextInfraUtilitiesNativeTooling):
    """Single owner for ``ManagedArtifacts`` across ``config/*.yaml`` files."""

    @classmethod
    def load_codegen_inputs(
        cls,
        repository_root: Path,
        *,
        projections: t.VariadicTuple[m.Infra.CodegenLayerProjection] = (),
        source_project: p.Infra.RopeProject | None = None,
    ) -> p.Result[m.Infra.CodegenInputs]:
        """Load one root's full policy through the ordered strict YAML source.

        An injected source project serves the same file observations to its
        consumer, including read-only dependency projects.

        Returns:
            The effective codegen declaration and exact consulted file snapshots.

        """
        result_type = r[m.Infra.CodegenInputs]
        document = cls.load_config_document_inputs(
            repository_root,
            filename=c.Infra.CODEGEN_CONFIG_FILENAME,
            projections=projections,
            source_project=source_project,
        )
        if document.failure:
            return result_type.from_failure(document)
        loaded = r[m.Infra.CodegenConfigSpec].create_from_callable(
            partial(cls._repository_codegen_spec, document.value.values),
        )
        if loaded.failure:
            return result_type.from_failure(loaded)
        return result_type.ok(
            m.Infra.CodegenInputs(
                spec=loaded.value,
                sources=document.value.sources,
            ),
        )

    @classmethod
    def load_tooling_inputs(
        cls,
        repository_root: Path,
        *,
        projections: t.VariadicTuple[m.Infra.CodegenLayerProjection] = (),
        source_project: p.Infra.RopeProject | None = None,
    ) -> p.Result[m.Infra.ToolingInputs]:
        """Elect tooling policy and capture every consulted configuration layer.

        Returns:
            The project-specific document and unchanged source snapshots.

        """
        result_type = r[m.Infra.ToolingInputs]
        document = cls.load_config_document_inputs(
            repository_root,
            filename="tooling.yaml",
            projections=projections,
            source_project=source_project,
        )
        if document.failure:
            return result_type.from_failure(document)
        section = u.validate_value(
            m.Infra.ToolConfigDocument,
            u.Cli.json_walk_path(document.value.values, ("Infra", "tooling")),
        )
        if section.failure:
            return result_type.from_failure(section)
        admitted_paths = cls.native_tool_search_path_admission(
            section.value, repository_root
        )
        if admitted_paths.failure:
            return result_type.from_failure(admitted_paths)
        return result_type.ok(
            m.Infra.ToolingInputs(
                document=section.value,
                sources=document.value.sources,
            ),
        )

    @classmethod
    def load_repository_declaration_inputs(
        cls,
        repository_root: Path,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> p.Result[m.Infra.RepositoryDeclarationInputs]:
        """Validate only repository policy through the same captured YAML layers.

        An absent optional repository subsection declares no self-owned deltas.
        Invalid declared policy retains its cause; unrelated editor or tool policy
        belongs to its own typed consumer and does not determine topology.

        Returns:
            Strict repository policy with current consulted source snapshots.

        """
        if source_project is None:
            return cls._repository_declaration_inputs(repository_root)
        cache = cls._DECLARATION_CACHE.setdefault(source_project, {})
        key = str(repository_root)
        if key in cache:
            return r[m.Infra.RepositoryDeclarationInputs].ok(cache[key])
        loaded = cls._repository_declaration_inputs(
            repository_root, source_project=source_project
        )
        if loaded.success:
            cache[key] = loaded.value
        return loaded

    _DECLARATION_CACHE: ClassVar[
        WeakKeyDictionary[
            p.Infra.RopeProject, dict[str, m.Infra.RepositoryDeclarationInputs]
        ]
    ] = WeakKeyDictionary()

    @classmethod
    def _repository_declaration_inputs(
        cls,
        repository_root: Path,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> p.Result[m.Infra.RepositoryDeclarationInputs]:
        """Load repository policy once through the captured YAML layers.

        Returns:
            Strict repository policy with current consulted source snapshots.

        """
        result_type = r[m.Infra.RepositoryDeclarationInputs]
        document = cls.load_config_document_inputs(
            repository_root,
            filename=c.Infra.CODEGEN_CONFIG_FILENAME,
            source_project=source_project,
        )
        if document.failure:
            return result_type.from_failure(document)
        codegen = u.Cli.json_walk_path(document.value.values, ("Infra", "codegen"))
        section = r[t.JsonMapping].create_from_callable(
            partial(u.json_mapping_adapter().validate_python, codegen),
        )
        if section.failure:
            return result_type.from_failure(section)
        loaded = u.validate_value(
            m.Infra.RepositoryDeltaSpec,
            section.value.get("repository", {}),
        )
        if loaded.failure:
            return result_type.from_failure(loaded)
        return result_type.ok(
            m.Infra.RepositoryDeclarationInputs(
                spec=loaded.value,
                sources=document.value.sources,
            ),
        )

    @classmethod
    def load_config_document_inputs(
        cls,
        repository_root: Path,
        *,
        filename: str,
        projections: t.VariadicTuple[m.Infra.CodegenLayerProjection] = (),
        source_project: p.Infra.RopeProject | None = None,
    ) -> p.Result[m.Infra.ConfigDocumentInputs]:
        """Capture and compose one F.yaml through the same strict layer reader.

        Returns:
            The typed document and ordered snapshots, with no ambient source lookup.

        """
        result_type = r[m.Infra.ConfigDocumentInputs]
        elected = (
            r[tuple[Path, ...]].create_from_callable(
                partial(
                    FlextInfraConfig.config_sources_for_repository,
                    repository_root,
                    filename=filename,
                ),
            )
            if source_project is None
            else r[tuple[Path, ...]].ok(())
        )
        if elected.failure:
            return result_type.from_failure(elected)
        layers = FlextInfraConfig.config_layer_paths_for_repository(
            repository_root,
            filename=filename,
        )
        selected = tuple(dict.fromkeys(layers))
        if any(projection.path not in selected[1:] for projection in projections):
            error = ValueError(
                "projected codegen declaration is outside elected layers"
            )
            return result_type.fail(str(error), exception=error)
        snapshots: list[m.Cli.AtomicFileState] = []
        for path in selected:
            if source_project is not None:
                snapshots.append(
                    source_project.source_state(path, required=path == selected[0])
                )
                continue
            observed = u.Cli.atomic_read_binary_file_state(
                path,
                required=path == selected[0] or path in elected.value,
            )
            if observed.failure:
                return result_type.from_failure(observed)
            snapshots.append(observed.value)
        loaded = r[t.JsonMapping].create_from_callable(
            partial(
                cls._repository_config_document,
                selected,
                tuple(snapshots),
                projections,
                source_project=source_project,
            ),
        )
        if loaded.failure:
            return result_type.from_failure(loaded)
        return result_type.ok(
            m.Infra.ConfigDocumentInputs(
                values=loaded.value,
                sources=tuple(snapshots),
            ),
        )

    @classmethod
    def load_refactor_csv_campaigns(
        cls,
        repository_root: Path,
    ) -> p.Result[m.Infra.RefactorCsvCampaignsSpec]:
        """Elect only this target's declared campaigns through its F.yaml layers.

        Returns:
            The validated campaign declaration; generic defaults own an empty set.

        """
        document = cls.load_config_document_inputs(
            repository_root,
            filename=c.Infra.INFRA_CONFIG_FILENAME,
        )
        if document.failure:
            return r[m.Infra.RefactorCsvCampaignsSpec].from_failure(document)
        return u.validate_value(
            m.Infra.RefactorCsvCampaignsSpec,
            u.Cli.json_walk_path(
                document.value.values,
                ("Infra", "refactor_csv_campaigns"),
            ),
        )

    @classmethod
    def project_codegen_inputs(
        cls,
        repository_root: Path,
        captured: m.Infra.CodegenInputs,
        *,
        projections: t.VariadicTuple[m.Infra.CodegenLayerProjection] = (),
        include_local: bool = True,
    ) -> p.Result[m.Infra.CodegenInputs]:
        """Project pending layers from captured bytes without rereading their sources.

        Returns:
            A validated preview retaining the original input identities.

        """
        result_type = r[m.Infra.CodegenInputs]
        layers = FlextInfraConfig.config_layer_paths_for_repository(
            repository_root,
            filename=c.Infra.CODEGEN_CONFIG_FILENAME,
        )
        if not captured.sources:
            error = ValueError("codegen projection requires captured library inputs")
            return result_type.fail(str(error), exception=error)
        if captured.sources[0].path != layers[0] or any(
            state.path not in layers for state in captured.sources
        ):
            error = ValueError("captured codegen inputs do not belong to this root")
            return result_type.fail(str(error), exception=error)
        selected = tuple(
            dict.fromkeys(
                layers if include_local else layers[:2],
            ),
        )
        if any(projection.path not in selected[1:] for projection in projections):
            error = ValueError(
                "projected codegen declaration is outside elected layers"
            )
            return result_type.fail(str(error), exception=error)
        loaded = r[m.Infra.CodegenConfigSpec].create_from_callable(
            lambda: cls._repository_codegen_spec(
                cls._repository_config_document(
                    selected, captured.sources, projections
                ),
            ),
        )
        return loaded.map(
            lambda spec: m.Infra.CodegenInputs(spec=spec, sources=captured.sources),
        )

    @staticmethod
    def read_codegen_config_document(content: bytes) -> p.Result[t.JsonMapping]:
        """Parse captured YAML bytes through the single strict config transport.

        Returns:
            A mapping, including the source's defined empty-document representation.

        """
        return r[t.JsonMapping].create_from_callable(
            partial(
                FlextInfraUtilitiesProjectManagedArtifacts._parse_codegen_config_document,
                content,
            ),
        )

    @staticmethod
    def _parse_codegen_config_document(content: bytes) -> t.JsonMapping:
        """Apply the strict source's mapping and empty-document contracts.

        Returns:
            Validated configuration values from immutable source bytes.

        """
        return deepcopy(
            FlextInfraUtilitiesProjectManagedArtifacts._parsed_config_content(content),
        )

    @staticmethod
    @lru_cache(maxsize=c.Infra.CONTENT_CACHE_MAXSIZE)
    def _parsed_config_content(content: bytes) -> t.JsonMapping:
        """Memoize successful strict parsing of exact immutable source bytes.

        Exceptions leave unchanged and are never cached. The admission owner
        copies each successful value before exposing it to consumers.

        Returns:
            The validated document owned by this content memo.

        """
        parsed = FlextStrictYamlConfigSource.unique_key_load(
            content.decode(c.DEFAULT_ENCODING),
        )
        return (
            {} if parsed is None else u.json_mapping_adapter().validate_python(parsed)
        )

    @staticmethod
    def _repository_codegen_spec(
        document: t.JsonMapping,
    ) -> m.Infra.CodegenConfigSpec:
        """Validate composed policy with its model's already-compiled schema.

        Returns:
            The validated full repository codegen policy.

        Raises:
            ValueError: If the composed declaration violates the codegen
                configuration schema; third-party validation detail travels
                as the cause.

        """
        codegen = u.Cli.json_walk_path(document, ("Infra", "codegen"))
        try:
            return m.Infra.CodegenConfigSpec.model_validate(codegen)
        except m.ValidationError as error:
            # Config-authoring failures surface as the service contract's own
            # error type, never as a raw third-party validation exception.
            raise ValueError(str(error)) from error

    @classmethod
    def _repository_config_document(
        cls,
        sources: tuple[Path, ...],
        snapshots: t.VariadicTuple[m.Cli.AtomicFileState],
        projections: t.VariadicTuple[m.Infra.CodegenLayerProjection],
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> t.JsonMapping:
        """Merge ordered captured F.yaml bytes and explicitly projected layers.

        Projections replace values within their source layer. Distinct layers
        use the strict YAML source's recursive mapping and list composition.

        Returns:
            The composed document; schema consumers validate their owned section.

        """
        merged: t.JsonDict = {}
        for path in sources:
            captured = next((item for item in snapshots if item.path == path), None)
            content = (
                (captured.content if captured is not None else None)
                if source_project is None
                else (
                    source_project.source_text(path).encode(c.DEFAULT_ENCODING)
                    if source_project.source_query(path, "isfile")
                    else None
                )
            )
            if content is None:
                payload: t.JsonMapping = {}
            else:
                payload = cls._parse_codegen_config_document(content)
            projected = next(
                (item for item in projections if item.path == path),
                None,
            )
            values = (
                u.config_merge(dict(payload), dict(projected.values))
                if projected is not None
                else dict(payload)
            )
            # A command is one ordered invocation, not an additive rule list.
            beads_path = ("Infra", "codegen", "toolchain", "beads")
            declared_beads = u.Cli.json_walk_path(values, beads_path)
            if isinstance(declared_beads, Mapping) and (
                "ownership_command_prefix" in declared_beads
            ):
                retained_beads: t.JsonValue = merged
                for namespace in beads_path:
                    if not isinstance(retained_beads, dict):
                        break
                    retained_beads = retained_beads.get(namespace)
                if isinstance(retained_beads, dict):
                    retained_beads.pop("ownership_command_prefix", None)
            merged = FlextStrictYamlConfigSource.merge_values(merged, values)
        return merged

    @classmethod
    def _validated_config_roots(
        cls,
        project_dir: Path,
    ) -> p.Result[
        t.Quad[Path, t.VariadicTuple[int], t.VariadicTuple[int], t.VariadicTuple[Path]]
    ]:
        """Validate the physical project and config directories, list yaml paths.

        An absent ``config/`` directory keeps the validated identity empty; the
        caller renders that as a project with no config sources.

        Returns:
            The resulting
                ``(config dir, project identity, config identity, yaml paths)``
                quadruple.

        """
        quad = r[
            t.Quad[
                Path,
                t.VariadicTuple[int],
                t.VariadicTuple[int],
                t.VariadicTuple[Path],
            ]
        ]
        project_identity = cls._required_directory_identity(
            project_dir,
            purpose="project root",
        )
        if project_identity.failure:
            return quad.from_failure(project_identity)
        config_dir = project_dir / c.CONFIG_DIR_NAME
        identity = cls._config_directory_identity(config_dir)
        if identity.failure:
            return quad.from_failure(identity)
        if not identity.value:
            return quad.ok((config_dir, project_identity.value, (), ()))
        paths = cls._config_yaml_paths(config_dir, identity.value)
        if paths.failure:
            return quad.from_failure(paths)
        return quad.ok((
            config_dir,
            project_identity.value,
            identity.value,
            paths.value,
        ))

    @classmethod
    def _stable_snapshot_identity(
        cls,
        project_dir: Path,
        config_dir: Path,
        identity_value: t.VariadicTuple[int],
        paths_value: t.VariadicTuple[Path],
        project_identity_value: t.VariadicTuple[int],
    ) -> p.Result[t.VariadicTuple[int]]:
        """Re-read both identities and require the snapshot topology to hold.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[int]]``.

        """
        stable_paths = cls._config_yaml_paths(config_dir, identity_value)
        if stable_paths.failure:
            return r[t.VariadicTuple[int]].from_failure(stable_paths)
        if stable_paths.value != paths_value:
            return r[t.VariadicTuple[int]].fail(
                f"{c.Infra.CONFIG_SNAPSHOT_TOPOLOGY_RACE_MARKER}: {config_dir}",
            )
        stable_project = cls._required_directory_identity(
            project_dir,
            purpose="project root",
        )
        if stable_project.failure:
            return r[t.VariadicTuple[int]].from_failure(stable_project)
        if stable_project.value != project_identity_value:
            return r[t.VariadicTuple[int]].fail(
                f"{c.Infra.CONFIG_SNAPSHOT_ROOT_RACE_MARKER}: {project_dir}",
            )
        return stable_project

    @classmethod
    def _snapshot_sources(
        cls,
        project_dir: Path,
        config_dir: Path,
        identity_value: t.VariadicTuple[int],
        paths_value: t.VariadicTuple[Path],
        project_identity_value: t.VariadicTuple[int],
    ) -> p.Result[t.VariadicTuple[m.Cli.AtomicFileState]]:
        """Read every config source, then require the topology to stay stable.

        Returns:
            The resulting
                ``p.Result[t.VariadicTuple[m.Cli.AtomicFileState]]``.

        """
        sources: list[m.Cli.AtomicFileState] = []
        for path in paths_value:
            source = u.Cli.atomic_read_binary_file_state(path, required=True)
            if source.failure:
                return r[t.VariadicTuple[m.Cli.AtomicFileState]].from_failure(source)
            sources.append(source.value)
        stable_project = cls._stable_snapshot_identity(
            project_dir,
            config_dir,
            identity_value,
            paths_value,
            project_identity_value,
        )
        if stable_project.failure:
            return r[t.VariadicTuple[m.Cli.AtomicFileState]].from_failure(
                stable_project,
            )
        return r[t.VariadicTuple[m.Cli.AtomicFileState]].ok(tuple(sources))

    @staticmethod
    def direct_config_source(project_dir: Path, path: Path) -> bool:
        """Whether ``path`` is one direct ``config/*.yaml`` source of the project.

        Returns:
            True for a direct YAML child of the project's config directory.

        """
        return path.parent == project_dir / c.CONFIG_DIR_NAME and path.suffix == ".yaml"

    @classmethod
    def snapshot_config_sources(
        cls,
        project_dir: Path,
    ) -> p.Result[t.VariadicTuple[m.Cli.AtomicFileState]]:
        """Capture one stable, physical, direct ``config/*.yaml`` file set.

        A project root that is not materialized yet (a scaffold planned
        read-only) owns no config sources, exactly like an absent ``config/``.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Cli.AtomicFileState]]``.

        """
        if not project_dir.exists() and not project_dir.is_symlink():
            return r[tuple[m.Cli.AtomicFileState, ...]].ok(())
        roots = cls._validated_config_roots(project_dir)
        if roots.failure:
            return r[tuple[m.Cli.AtomicFileState, ...]].from_failure(roots)
        config_dir, project_identity, identity, paths = roots.value
        if not identity:
            return r[tuple[m.Cli.AtomicFileState, ...]].ok(())
        return cls._snapshot_sources(
            project_dir,
            config_dir,
            identity,
            paths,
            project_identity,
        )

    @classmethod
    def _required_directory_identity(
        cls,
        path: Path,
        *,
        purpose: str,
    ) -> p.Result[t.VariadicTuple[int]]:
        try:
            state = path.lstat()
        except OSError as exc:
            return r[t.VariadicTuple[int]].fail_op(f"inspect {purpose}", exc)
        attributes = getattr(state, "st_file_attributes", 0)
        reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        if not stat.S_ISDIR(state.st_mode) or attributes & reparse:
            return r[t.VariadicTuple[int]].fail(
                f"{purpose} is not a physical directory: {path}",
            )
        return r[t.VariadicTuple[int]].ok(cls._directory_state_key(state))

    @classmethod
    def _config_directory_identity(
        cls,
        config_dir: Path,
    ) -> p.Result[t.VariadicTuple[int]]:
        try:
            state = config_dir.lstat()
        except FileNotFoundError:
            return r[t.VariadicTuple[int]].ok(())
        except OSError as exc:
            return r[t.VariadicTuple[int]].fail_op(
                "inspect project config directory",
                exc,
            )
        attributes = getattr(state, "st_file_attributes", 0)
        reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        if not stat.S_ISDIR(state.st_mode) or attributes & reparse:
            return r[t.VariadicTuple[int]].fail(
                f"project config path is not a physical directory: {config_dir}",
            )
        return r[t.VariadicTuple[int]].ok(cls._directory_state_key(state))

    @staticmethod
    def empty_snapshot() -> m.Infra.ProjectManagedArtifactsSnapshot:
        """Return the explicit managed-artifact state for a future scaffold.

        Returns:
            The explicit managed-artifact state for a future scaffold.

        """
        return m.Infra.ProjectManagedArtifactsSnapshot(
            sources=(),
            resolution=m.Infra.ProjectManagedArtifactsResolution(
                artifacts=m.Infra.ProjectManagedArtifactsConfig(
                    Mise=m.Infra.ProjectMiseConfig(tools={}),
                    Gitignore=m.Infra.ProjectGitignoreConfig(patterns=()),
                ),
                mise_tool_sources={},
            ),
        )

    @classmethod
    def _config_yaml_paths(
        cls,
        config_dir: Path,
        expected_identity: t.VariadicTuple[int],
    ) -> p.Result[t.VariadicTuple[Path]]:
        try:
            paths = tuple(
                sorted(
                    path
                    for path in config_dir.iterdir()
                    if cls.direct_config_source(config_dir.parent, path)
                ),
            )
        except OSError as exc:
            return r[t.VariadicTuple[Path]].fail_op(
                "enumerate project config sources",
                exc,
            )
        current = cls._config_directory_identity(config_dir)
        if current.failure:
            return r[t.VariadicTuple[Path]].from_failure(current)
        if current.value != expected_identity:
            return r[t.VariadicTuple[Path]].fail(
                f"project config directory changed during snapshot: {config_dir}",
            )
        return r[t.VariadicTuple[Path]].ok(paths)

    @staticmethod
    def _directory_state_key(state: os.stat_result) -> t.VariadicTuple[int]:
        return (
            state.st_dev,
            state.st_ino,
            state.st_mode,
            state.st_uid,
            state.st_gid,
            state.st_size,
            state.st_mtime_ns,
            state.st_ctime_ns,
        )

    @classmethod
    def load_project_managed_artifacts(
        cls,
        project_dir: Path,
    ) -> p.Result[m.Infra.ProjectManagedArtifactsResolution]:
        """Snapshot every YAML once and parse that exact source set.

        Returns:
            The resulting ``p.Result[m.Infra.ProjectManagedArtifactsResolution]``.

        """
        snapshot = cls.snapshot_project_managed_artifacts(project_dir)
        if snapshot.failure:
            return r[m.Infra.ProjectManagedArtifactsResolution].from_failure(snapshot)
        return r[m.Infra.ProjectManagedArtifactsResolution].ok(
            snapshot.value.resolution,
        )

    @classmethod
    def snapshot_project_managed_artifacts(
        cls,
        project_dir: Path,
    ) -> p.Result[m.Infra.ProjectManagedArtifactsSnapshot]:
        """Capture and parse exactly one immutable project configuration view.

        Returns:
            The resulting ``p.Result[m.Infra.ProjectManagedArtifactsSnapshot]``.

        """
        source_snapshot = cls.snapshot_config_sources(project_dir)
        if source_snapshot.failure:
            return r[m.Infra.ProjectManagedArtifactsSnapshot].from_failure(
                source_snapshot,
            )
        resolution = cls.load_project_managed_artifacts_from_snapshot(
            source_snapshot.value,
        )
        if resolution.failure:
            return r[m.Infra.ProjectManagedArtifactsSnapshot].from_failure(resolution)
        return r[m.Infra.ProjectManagedArtifactsSnapshot].ok(
            m.Infra.ProjectManagedArtifactsSnapshot(
                sources=source_snapshot.value,
                resolution=resolution.value,
            ),
        )

    @classmethod
    def load_committed_project_managed_artifacts(
        cls,
        project_dir: Path,
        *,
        read_committed_directory: Callable[
            [Path, str], p.Result[t.MappingKV[str, bytes]]
        ],
    ) -> p.Result[m.Infra.ProjectManagedArtifactsResolution]:
        """Load ManagedArtifacts from the project's committed ``HEAD`` catalog.

        Render inputs are ``f(SSOT, templates, PINS)``. A worktree can carry
        concurrent WIP, so codegen renders project overlays only from the
        immutable commit catalog; uncommitted declarations never enter a
        projection.

        Returns:
            The resulting ``p.Result[m.Infra.ProjectManagedArtifactsResolution]``.

        """
        snapshot = cls.snapshot_committed_project_managed_artifacts(
            project_dir,
            read_committed_directory=read_committed_directory,
        )
        if snapshot.failure:
            return r[m.Infra.ProjectManagedArtifactsResolution].from_failure(snapshot)
        return r[m.Infra.ProjectManagedArtifactsResolution].ok(
            snapshot.value.resolution,
        )

    @classmethod
    def snapshot_committed_project_managed_artifacts(
        cls,
        project_dir: Path,
        *,
        read_committed_directory: Callable[
            [Path, str], p.Result[t.MappingKV[str, bytes]]
        ],
    ) -> p.Result[m.Infra.ProjectManagedArtifactsSnapshot]:
        """Capture and parse the committed catalog without physical source states.

        ``sources`` stays empty because Git objects are already immutable, so a
        physical re-read is meaningless.

        Returns:
            The resulting ``p.Result[m.Infra.ProjectManagedArtifactsSnapshot]``.

        """
        resolved = project_dir.expanduser().resolve()
        blobs = read_committed_directory(
            resolved,
            c.CONFIG_DIR_NAME,
        )
        if blobs.failure:
            return r[m.Infra.ProjectManagedArtifactsSnapshot].fail(
                f"cannot open committed project config catalog at {resolved}: "
                f"{blobs.error}",
            )
        payloads: t.MutableMappingKV[Path, bytes] = {
            resolved / c.CONFIG_DIR_NAME / name: content
            for name, content in sorted(blobs.value.items())
            if name.endswith(".yaml")
        }
        if not payloads:
            return r[m.Infra.ProjectManagedArtifactsSnapshot].ok(cls.empty_snapshot())
        resolution = cls._load_project_managed_artifacts_from_payloads(payloads)
        if resolution.failure:
            return r[m.Infra.ProjectManagedArtifactsSnapshot].from_failure(resolution)
        return r[m.Infra.ProjectManagedArtifactsSnapshot].ok(
            m.Infra.ProjectManagedArtifactsSnapshot(
                sources=(),
                resolution=resolution.value,
            ),
        )

    @classmethod
    def load_project_managed_artifacts_from_snapshot(
        cls,
        source_snapshot: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> p.Result[m.Infra.ProjectManagedArtifactsResolution]:
        """Parse one caller-owned immutable project YAML snapshot.

        Returns:
            The resulting ``p.Result[m.Infra.ProjectManagedArtifactsResolution]``.

        """
        payloads: t.MutableMappingKV[Path, bytes] = {}
        for source_state in source_snapshot:
            if source_state.content is None:
                return r[m.Infra.ProjectManagedArtifactsResolution].fail(
                    f"project config snapshot is absent: {source_state.path}",
                )
            payloads[source_state.path] = source_state.content
        return cls._load_project_managed_artifacts_from_payloads(payloads)

    @classmethod
    def _load_project_managed_artifacts_from_payloads(
        cls,
        payloads: t.MappingKV[Path, bytes],
    ) -> p.Result[m.Infra.ProjectManagedArtifactsResolution]:
        """Parse one immutable path-to-bytes project YAML catalog.

        Returns:
            The resulting ``p.Result[m.Infra.ProjectManagedArtifactsResolution]``.

        """
        if not payloads:
            return r[m.Infra.ProjectManagedArtifactsResolution].ok(
                cls.empty_snapshot().resolution,
            )
        fragments: list[tuple[Path, m.Infra.ProjectManagedArtifactsFragment]] = []
        for source, content in sorted(payloads.items()):
            parsed = cls._parse_project_fragment(source, content)
            if parsed.failure:
                return r[m.Infra.ProjectManagedArtifactsResolution].from_failure(parsed)
            fragments.append((source, parsed.value))
        return cls._compose_project_fragments(fragments)

    @staticmethod
    def _parse_project_fragment(
        source: Path,
        content: bytes,
    ) -> p.Result[m.Infra.ProjectManagedArtifactsFragment]:
        """Decode one project YAML source into its managed-artifact fragment.

        Returns:
            The fragment, empty when the source declares no ``ManagedArtifacts``.

        """
        try:
            source_text = content.decode(c.DEFAULT_ENCODING)
        except UnicodeDecodeError as exc:
            return r[m.Infra.ProjectManagedArtifactsFragment].fail_op(
                f"decode project config source {source}",
                exc,
            )
        loaded = u.Cli.yaml_parse(source_text)
        if loaded.failure:
            return r[m.Infra.ProjectManagedArtifactsFragment].from_failure(loaded)
        managed = loaded.value.get("ManagedArtifacts")
        if not managed:
            return r[m.Infra.ProjectManagedArtifactsFragment].ok(
                m.Infra.ProjectManagedArtifactsFragment(),
            )
        return u.validate_value(
            m.Infra.ProjectConfigDocument,
            {"ManagedArtifacts": managed},
        ).map(lambda document: document.ManagedArtifacts)

    @staticmethod
    def _merge_unique_keys[V](
        label: str,
        source: Path,
        items: t.MappingKV[str, V],
        merged: MutableMapping[str, V],
        owners: MutableMapping[str, Path],
    ) -> str | None:
        """Merge keyed entries of one source, refusing keys another source owns.

        Returns:
            The duplicate-key failure message, or ``None`` when every key merged.

        """
        for key, value in items.items():
            previous = owners.get(key)
            if previous is not None:
                return f"duplicate project {label} {key!r}: {previous} and {source}"
            merged[key] = value
            owners[key] = source
        return None

    @staticmethod
    def _merge_gitignore(
        source: Path,
        gitignore: m.Infra.ProjectGitignoreConfig | None,
        patterns: list[str],
        blocks: list[m.Infra.ProjectGitignorePreservedBlock],
        markers: MutableMapping[str, Path],
    ) -> str | None:
        """Merge one source's gitignore patterns and uniquely owned blocks.

        Returns:
            The duplicate-marker failure message, or ``None`` when all merged.

        """
        if gitignore is None:
            return None
        patterns.extend(
            pattern
            for pattern in dict.fromkeys(gitignore.patterns)
            if pattern not in patterns
        )
        for block in gitignore.preserved_blocks:
            failure = FlextInfraUtilitiesProjectManagedArtifacts._merge_unique_keys(
                "gitignore preserved marker",
                source,
                dict.fromkeys((block.begin, block.end), source),
                markers,
                markers,
            )
            if failure is not None:
                return failure
            blocks.append(block)
        return None

    @classmethod
    def _compose_project_fragments(
        cls,
        fragments: t.SequenceOf[tuple[Path, m.Infra.ProjectManagedArtifactsFragment]],
    ) -> p.Result[m.Infra.ProjectManagedArtifactsResolution]:
        """Compose source fragments in path order into one resolution.

        Returns:
            The resulting ``p.Result[m.Infra.ProjectManagedArtifactsResolution]``.

        """
        mise_tools: MutableMapping[str, m.Infra.ProjectMiseTool] = {}
        mise_sources: MutableMapping[str, Path] = {}
        gitignore_patterns: list[str] = []
        gitignore_blocks: list[m.Infra.ProjectGitignorePreservedBlock] = []
        gitignore_markers: MutableMapping[str, Path] = {}
        for source, fragment in fragments:
            failure = cls._merge_gitignore(
                source,
                fragment.Gitignore,
                gitignore_patterns,
                gitignore_blocks,
                gitignore_markers,
            ) or cls._merge_unique_keys(
                "Mise selector",
                source,
                fragment.Mise.tools if fragment.Mise else {},
                mise_tools,
                mise_sources,
            )
            if failure is not None:
                return r[m.Infra.ProjectManagedArtifactsResolution].fail(failure)
        artifacts = m.Infra.ProjectManagedArtifactsConfig(
            Mise=m.Infra.ProjectMiseConfig(tools=dict(sorted(mise_tools.items()))),
            Gitignore=m.Infra.ProjectGitignoreConfig(
                patterns=tuple(gitignore_patterns),
                preserved_blocks=tuple(gitignore_blocks),
            ),
        )
        return r[m.Infra.ProjectManagedArtifactsResolution].ok(
            m.Infra.ProjectManagedArtifactsResolution(
                artifacts=artifacts,
                mise_tool_sources=dict(sorted(mise_sources.items())),
            ),
        )

    @classmethod
    def compose_mise_toml_from_snapshot(
        cls,
        source_snapshot: t.VariadicTuple[m.Cli.AtomicFileState],
        rendered: str,
    ) -> p.Result[str]:
        """Add local tools from one caller-owned immutable YAML snapshot.

        Returns:
            The resulting ``p.Result[str]``.

        """
        resolved = cls.load_project_managed_artifacts_from_snapshot(source_snapshot)
        if resolved.failure:
            return r[str].from_failure(resolved)
        return cls.compose_mise_toml_from_resolution(resolved.value, rendered)

    @classmethod
    def compose_mise_toml_from_resolution(
        cls,
        resolution: m.Infra.ProjectManagedArtifactsResolution,
        rendered: str,
    ) -> p.Result[str]:
        """Add local tools from one caller-owned immutable parsed catalog.

        Returns:
            The resulting ``p.Result[str]``.

        """
        local_tools = resolution.artifacts.Mise.tools
        if not local_tools:
            return r[str].ok(rendered)
        doc = u.Cli.toml_parse_text(rendered)
        if doc is None:
            return r[str].fail("canonical .mise.toml template is invalid")
        tools = u.Cli.toml_ensure_table(doc, "tools")
        for selector, tool in local_tools.items():
            if selector in tools:
                source = resolution.mise_tool_sources[selector]
                return r[str].fail(
                    f"project Mise selector {selector!r} ({source}) "
                    "duplicates its packaged owner",
                )
            tools[selector] = tool.version
        return r[str].ok(u.Cli.toml_dumps(doc))


__all__: t.VariadicTuple[str] = ("FlextInfraUtilitiesProjectManagedArtifacts",)
