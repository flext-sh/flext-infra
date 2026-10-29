"""Public pyproject conformer over the requirement and uv-source owners.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from functools import cache, partial
from pathlib import Path
from typing import Annotated, ClassVar

from flext_cli import u
from packaging.utils import canonicalize_name
from typing_extensions import TypeForm

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesDependencies,
    FlextInfraUtilitiesGit,
    FlextInfraUtilitiesManagedConflicts,
    FlextInfraUtilitiesProjectManagedArtifacts,
)
from flext_infra._utilities._pyproject.overlay import (
    FlextInfraUtilitiesPyprojectOverlay,
)
from flext_infra._utilities._pyproject.uv_sources import (
    FlextInfraUtilitiesPyprojectUvSources,
)


class FlextInfraUtilitiesPyprojectDocument(FlextInfraUtilitiesPyprojectUvSources):
    """Render root workspace and autonomous library metadata deterministically."""

    _live_text_memo: ClassVar[dict[str, p.Result[str]]] = {}

    @classmethod
    def declared_dependency_payload(
        cls,
        pyproject_path: Path,
    ) -> p.Result[t.JsonMapping]:
        """Read owner-recovered TOML without admitting generated group inputs.

        Returns:
            The parsed mapping with authored dependency-group entries only.

        """
        text = cls.live_pyproject_text(pyproject_path)
        if text.failure:
            return r[t.JsonMapping].from_failure(text)
        payload = u.Cli.toml_mapping_from_text(text.value)
        if payload is None:
            return r[t.JsonMapping].fail(
                f"pyproject is not valid TOML: {pyproject_path}",
            )
        groups = u.Cli.toml_mapping_path(payload, (c.Infra.DEPENDENCY_GROUPS,))
        if groups is not None:
            for group in (str(c.Infra.DEV), c.Infra.DependencyGroup.CODEGEN):
                selected = cls.dependency_group_name(tuple(groups), str(group))
                if selected not in groups:
                    continue
                custom = cls.custom_dev_additions(payload, text.value, group=selected)
                if custom.failure:
                    return r[t.JsonMapping].from_failure(custom)
                groups[selected] = cls.dependency_group_wire(custom.value)
        return r[t.JsonMapping].ok(payload)

    @staticmethod
    def recover_live_pyproject_text(raw: str) -> p.Result[str]:
        """Return live pyproject text with merge-control lines resolved.

        Unconflicted text is returned unchanged. A conflict is resolved only
        inside owner-declared managed TOML sections
        (``config.Infra.codegen.managed_file_specs``) via
        ``FlextInfraUtilitiesManagedConflicts.recover_managed_toml``; a
        conflict outside those sections fails loud through that utility's
        own contract. Read-only: no file is written here.

        The recovery is a pure function of the text and the frozen managed
        file declaration, so one recovery per distinct text serves every
        reader of the process.

        Returns:
            Live pyproject text with merge-control lines resolved.

        """
        recovered = FlextInfraUtilitiesPyprojectDocument._live_text_memo.get(raw)
        if recovered is not None:
            return recovered
        spec_result = FlextInfraUtilitiesManagedConflicts.pyproject_managed_file()
        if spec_result.failure:
            return r[str].from_failure(spec_result)
        recovered = FlextInfraUtilitiesManagedConflicts.recover_managed_toml(
            raw,
            conflict_sections=spec_result.value.conflict_sections,
        )
        FlextInfraUtilitiesPyprojectDocument._live_text_memo[raw] = recovered
        return recovered

    @staticmethod
    def live_pyproject_text(
        pyproject_path: Path,
        *,
        regenerate_managed_tools: bool = False,
    ) -> p.Result[str]:
        """Read one live pyproject and resolve managed merge conflicts.

        Returns:
            The resulting ``p.Result[str]``.

        """
        raw = u.Cli.atomic_read_binary_file_state(pyproject_path, required=True)
        if raw.failure:
            return r[str].from_failure(raw)
        content = raw.value.content
        if content is None:
            return r[str].fail(f"pyproject is absent: {pyproject_path}")
        live = FlextInfraUtilitiesPyprojectDocument.recover_live_pyproject_text(
            content.decode(c.DEFAULT_ENCODING),
        )
        if live.failure or not regenerate_managed_tools:
            return live
        return FlextInfraUtilitiesManagedConflicts.pyproject_regeneration_source(
            live.value,
        )

    @staticmethod
    def read_project_metadata_result(
        project_root: Path,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> p.Result[p.ProjectMetadata]:
        """Read retained metadata from the canonical single-document ingress.

        Returns:
            The original structural metadata or its causal ingress failure.

        """
        state = FlextInfraUtilitiesPyprojectDocument.read_project_metadata_state(
            project_root,
            source_project=source_project,
        )
        if state.failure:
            return r[p.ProjectMetadata].from_failure(state)
        return r[p.ProjectMetadata].ok(state.value.metadata)

    @staticmethod
    def read_project_metadata_state(
        project_root: Path,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> p.Result[m.Infra.ProjectMetadataState]:
        """Parse metadata and packaging declarations without importing source exports.

        Returns:
            Retained typed metadata and packaging facts from one live TOML read.

        """
        result_type = r[m.Infra.ProjectMetadataState]
        live = (
            FlextInfraUtilitiesPyprojectDocument.live_pyproject_text(
                project_root / c.PYPROJECT_FILENAME
            )
            if source_project is None
            else FlextInfraUtilitiesPyprojectDocument.recover_live_pyproject_text(
                source_project.source_text(project_root / c.PYPROJECT_FILENAME),
            )
        )
        if live.failure:
            return result_type.from_failure(live)
        # The facade returns None for unparseable text rather than raising, so
        # the invalid case is named here instead of reaching model_validate as
        # a None that fails with a shape error about the wrong subject.
        payload = u.Cli.toml_mapping_from_text(live.value)
        if payload is None:
            return result_type.fail(
                f"cannot read project metadata from {project_root}: "
                f"{c.PYPROJECT_FILENAME} is not valid TOML",
            )
        try:
            document = u.PyprojectDocument.model_validate(payload)
            packaging = m.Infra.ProjectPackagingDeclaration.model_validate(payload)
            metadata = u.build_project_metadata(project_root, document)
        except (OSError, ValueError) as exc:
            return result_type.fail(
                f"cannot read project metadata from {project_root}: {exc}",
                exception=exc,
            )
        return result_type.ok(
            m.Infra.ProjectMetadataState(metadata=metadata, packaging=packaging),
        )

    @staticmethod
    def project_package_participation(
        declaration: m.Infra.ProjectPackagingDeclaration,
    ) -> bool:
        """Apply native project defaults without consulting directories or exports.

        Args:
            declaration: Packaging declaration read from the project payload.

        Returns:
            Whether the project participates in packaging under native defaults.

        """
        return (
            declaration.build_backend is not None
            if declaration.uv_package is None
            else declaration.uv_package
        )

    @staticmethod
    def pyproject_payload(
        pyproject_path: Path,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> t.JsonMapping:
        """Return the shared TOML ingress's validated ``pyproject.toml`` mapping.

        The payload is parsed from the live text with managed merge
        conflicts resolved (``live_pyproject_text``).

        Returns:
            One mapping validated by the shared TOML ingress.

        Raises:
            RuntimeError: If failed to read pyproject payload at; or if pyproject
                payload at.

        """
        if not (
            pyproject_path.is_file()
            if source_project is None
            else source_project.source_query(pyproject_path, "isfile")
        ):
            return {}
        live = (
            FlextInfraUtilitiesPyprojectDocument.live_pyproject_text(pyproject_path)
            if source_project is None
            else FlextInfraUtilitiesPyprojectDocument.recover_live_pyproject_text(
                source_project.source_text(pyproject_path)
            )
        )
        if live.failure:
            msg = f"failed to read pyproject payload at {pyproject_path}: {live.error}"
            raise RuntimeError(msg)
        # The parse is memoized by the live text, never by the path alone: a
        # process that rewrites a manifest (gen, mod, a test) reads its new
        # content on the next call instead of a stale parse.
        return FlextInfraUtilitiesPyprojectDocument._parsed_pyproject_payload(
            pyproject_path,
            live.value,
        )

    @staticmethod
    @cache
    def _parsed_pyproject_payload(pyproject_path: Path, text: str) -> t.JsonMapping:
        """Parse and validate one manifest text (memoized per exact content).

        Returns:
            The validated mapping of ``text``.

        Raises:
            RuntimeError: If ``text`` is not valid TOML.

        """
        payload = u.Cli.toml_mapping_from_text(text)
        if payload is None:
            msg = f"pyproject payload at {pyproject_path} is not valid TOML"
            raise RuntimeError(msg)
        return payload

    @staticmethod
    def normalized_toml_payload(document: t.Cli.TomlDocument) -> t.JsonMapping:
        """Return the shared TOML ingress's validated document mapping.

        Returns:
            One mapping validated by the shared TOML ingress.

        """
        payload = u.Cli.toml_as_mapping(document)
        if not payload:
            return {}
        return payload

    @classmethod
    def sync_document_values(
        cls,
        document: t.Cli.TomlDocument | t.Cli.TomlTable,
        payload: t.JsonMapping,
    ) -> None:
        """Synchronize changed semantic values through the original TOML tree."""
        for key, value in payload.items():
            if u.Cli.toml_value(document, key) == value:
                continue
            child = u.Cli.toml_table_child(document, key)
            if child is not None and isinstance(value, Mapping):
                cls.sync_document_values(child, value)
            elif isinstance(value, list) and all(
                isinstance(item, str) for item in value
            ):
                u.Cli.toml_sync_string_list(
                    document,
                    key,
                    tuple(item for item in value if isinstance(item, str)),
                )
            else:
                u.Cli.toml_sync_value(document, key, value)

    @staticmethod
    def tool_flext_meta(project_root: Path) -> t.JsonMapping:
        """Return the normalized ``tool.flext`` table from a project root.

        Returns:
            The normalized ``tool.flext`` table from a project root.

        """
        payload = FlextInfraUtilitiesPyprojectDocument.pyproject_payload(
            project_root / c.PYPROJECT_FILENAME,
        )
        tool = payload.get(c.Infra.TOOL)
        if not isinstance(tool, dict):
            return {}
        flext = tool.get("flext")
        return flext if isinstance(flext, dict) else {}

    @staticmethod
    def docs_meta_from_payload(payload: t.JsonMapping) -> t.JsonMapping:
        """Extract ``tool.flext.docs`` metadata from an already-parsed payload.

        Returns:
            The resulting ``t.JsonMapping``.

        """
        tool = payload.get(c.Infra.TOOL)
        if not isinstance(tool, dict):
            return {}
        flext = tool.get("flext")
        if not isinstance(flext, dict):
            return {}
        docs = flext.get("docs")
        return docs if isinstance(docs, dict) else {}

    @staticmethod
    def project_name_from_payload(entry: Path, payload: t.JsonMapping) -> str:
        """Return the declared project name from ``[project].name``.

        Returns:
            The declared project name from ``[project].name``.

        Raises:
            TypeError: If ``not isinstance(project_section, dict)``.
            ValueError: If ``not isinstance(raw_name, str) or not raw_name.strip()``.

        """
        project_section = payload.get("project")
        if not isinstance(project_section, dict):
            msg = f"{entry}: missing [project] table in pyproject.toml"
            raise TypeError(msg)
        raw_name = project_section.get("name")
        if not isinstance(raw_name, str) or not raw_name.strip():
            msg = f"{entry}: missing or empty [project].name in pyproject.toml"
            raise ValueError(msg)
        return raw_name.strip()

    @staticmethod
    def _hatch_wheel_package(payload: t.JsonMapping) -> str | None:
        """Return the package name the hatch wheel targets declare.

        Returns:
            The resulting ``str | None``.

        """
        current: t.JsonMapping | None = payload
        for key in (c.Infra.TOOL, "hatch", "build", "targets", "wheel"):
            if current is None:
                break
            candidate = current.get(key)
            current = candidate if isinstance(candidate, dict) else None
        packages = current.get("packages") if current is not None else None
        if not isinstance(packages, list):
            return None
        for item in packages:
            package_path = Path(str(item).strip())
            if package_path.parts:
                return package_path.parts[-1]
        return None

    @staticmethod
    def _src_dir_package(project_root: Path) -> str | None:
        """Return the first ``src`` child package carrying an initializer.

        Returns:
            The resulting ``str | None``.

        """
        src_dir = project_root / c.Infra.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return None
        for child in sorted(src_dir.iterdir()):
            if child.is_dir() and (child / c.Infra.INIT_PY).is_file():
                return child.name
        return None

    @staticmethod
    def package_name_from_payload(
        project_root: Path,
        payload: t.JsonMapping,
        docs_meta: t.JsonMapping,
        *,
        source_paths: Sequence[Path] | None = None,
    ) -> str:
        """Return the primary package name using pre-loaded pyproject payload.

        Returns:
            The primary package name using pre-loaded pyproject payload.

        Raises:
            ValueError: If ``project_name.startswith(c.Infra.PKG_PREFIX_HYPHEN)``.

        """
        configured = docs_meta.get("package_name")
        if isinstance(configured, str) and configured.strip():
            return configured.strip()
        wheel_package = FlextInfraUtilitiesPyprojectDocument._hatch_wheel_package(
            payload
        )
        if wheel_package is not None:
            return wheel_package
        source_package = (
            next(
                (
                    path.parent.name
                    for path in sorted(source_paths)
                    if path.name == c.Infra.INIT_PY
                    and path.parent.parent == project_root / c.Infra.DEFAULT_SRC_DIR
                ),
                None,
            )
            if source_paths is not None
            else FlextInfraUtilitiesPyprojectDocument._src_dir_package(project_root)
        )
        if source_package is not None:
            return source_package
        # A manifest without a [project] table declares no package at all:
        # it configures tools only and owns no importable provider.
        if isinstance(payload.get("project"), dict):
            project_name = (
                FlextInfraUtilitiesPyprojectDocument.project_name_from_payload(
                    project_root,
                    payload,
                )
            )
            if project_name.startswith(c.Infra.PKG_PREFIX_HYPHEN):
                msg = (
                    f"{project_root}: cannot resolve package name — "
                    "no [tool.flext.docs].package_name, no hatch wheel packages, "
                    "and no src/<pkg>/__init__.py present"
                )
                raise ValueError(msg)
        return ""

    @staticmethod
    def project_package_name(
        project_root: Path,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> str:
        """Return the primary Python package name for a project root.

        Returns:
            The primary Python package name for a project root.

        """
        payload = FlextInfraUtilitiesPyprojectDocument.pyproject_payload(
            project_root / c.PYPROJECT_FILENAME,
            source_project=source_project,
        )
        docs_meta = FlextInfraUtilitiesPyprojectDocument.docs_meta_from_payload(payload)
        source_paths: tuple[Path, ...] | None = None
        if source_project is not None:
            src = project_root / c.Infra.DEFAULT_SRC_DIR
            source_paths = (
                tuple(
                    child / c.Infra.INIT_PY
                    for child in source_project.source_children(src)
                    if source_project.source_query(child, "isdir")
                    and source_project.source_query(child / c.Infra.INIT_PY, "isfile")
                )
                if source_project.source_query(src, "isdir")
                else ()
            )
        return FlextInfraUtilitiesPyprojectDocument.package_name_from_payload(
            project_root,
            payload,
            docs_meta,
            source_paths=source_paths,
        )

    @staticmethod
    @cache
    def workspace_project_paths(repository_root: Path) -> Sequence[str]:
        """Return governed project paths declared by this directory's ``.gitmodules``.

        A missing file denotes a standalone project and therefore an empty
        sequence. A malformed declaration is an invalid workspace contract and
        remains a loud error; no pyproject table or parent directory is used as
        an alternate topology source. A submodule that opts out through
        ``flext-managed`` is not a workspace project, the same contract the
        workspace detector applies; every governed path stays in the sequence
        so a missing or unreadable member pyproject still fails at its reader.

        Returns:
            Governed project paths declared by this directory's ``.gitmodules``.

        Raises:
            ValueError: If ``declared.failure``.

        """
        if not (repository_root / c.Infra.GITMODULES).exists(follow_symlinks=False):
            return ()
        declared = FlextInfraUtilitiesGit.git_submodule_declarations(repository_root)
        if declared.failure:
            msg = declared.error or f"invalid workspace topology: {repository_root}"
            raise ValueError(msg)
        return tuple(
            item.path.as_posix() for item in declared.value if item.managed is not False
        )

    @staticmethod
    @cache
    def workspace_member_layer_names(
        project_root: Path,
    ) -> tuple[frozenset[str], frozenset[str]]:
        """Derive declared domain/platform member name sets from the topology.

        The containing workspace root resolves first (the superproject when
        this checkout is a member, the checkout itself otherwise), so a
        member project classifies through the same declared per-member
        ``flext-layer`` attributes the workspace composes. A standalone
        repository (no ``.gitmodules``) declares no members and both sets
        stay empty — the same topology contract the modernizer applies to
        internal dependency names. Unknown layer declarations fail closed at
        the declaration parser.

        Returns:
            The resulting ``(domain_names, platform_names)`` pair.

        Raises:
            ValueError: If the topology root or the declarations are invalid.

        """
        topology = FlextInfraUtilitiesGit.git_repository_root(
            m.Infra.GitRepoRequest(repo_root=project_root),
        )
        if topology.failure:
            msg = topology.error or f"invalid repository topology: {project_root}"
            raise ValueError(msg)
        declared = FlextInfraUtilitiesGit.git_submodule_declarations(
            topology.value.repository_root,
        )
        if declared.failure:
            msg = (
                declared.error
                or f"invalid workspace topology: {topology.value.repository_root}"
            )
            raise ValueError(msg)
        domain: set[str] = set()
        platform: set[str] = set()
        for item in declared.value:
            if item.layer == c.Infra.MemberArchitectureLayer.DOMAIN:
                domain.add(item.path.name)
            elif item.layer == c.Infra.MemberArchitectureLayer.PLATFORM:
                platform.add(item.path.name)
        return (frozenset(domain), frozenset(platform))

    type _CustomGroupsPair = tuple[
        Sequence[str | m.Infra.DependencyGroupInclude],
        Sequence[str | m.Infra.DependencyGroupInclude],
    ]
    type _ConformedProvenance = tuple[
        t.Cli.TomlDocument,
        str,
        m.Infra.RequirementsProvenance,
    ]

    class PyprojectConformOptions(m.ImmutableValueModel):
        """Detected integration provenance for internal requirements and dev floors."""

        flext_line: Annotated[
            m.Infra.WorkspaceIntegrationSpec | None,
            m.Field(
                description="Detected provider and branch for internal requirements",
            ),
        ] = None

    @classmethod
    def parsed_pyproject(
        cls,
        pyproject_content: str,
    ) -> p.Result[tuple[t.Cli.TomlDocument, str, t.JsonMapping]]:
        """Parse a source, its distribution identity, and its mapping once.

        Returns:
            The validated document, project name, and metadata mapping.

        """
        result = r[tuple[t.Cli.TomlDocument, str, t.JsonMapping]]
        source = u.Cli.toml_parse_text(pyproject_content)
        if source is None:
            return result.fail(
                "pyproject content is not valid TOML",
            )
        project = u.Cli.toml_table_child(source, c.Infra.PROJECT)
        if project is None:
            return result.fail(
                "pyproject content must define [project]",
            )
        project_name_raw = u.Cli.toml_value(project, c.Infra.NAME)
        if not isinstance(project_name_raw, str) or not project_name_raw.strip():
            return result.fail(
                "[project].name must be a non-empty string",
            )
        payload = u.Cli.toml_as_mapping(source)
        if payload is None:
            return result.fail("root metadata is not a TOML mapping")
        return result.ok((source, project_name_raw.strip(), payload))

    @classmethod
    def pyproject_conform(
        cls,
        pyproject_content: str,
        *,
        workspace: m.Infra.WorkspaceSpec,
        required_dev_dependencies: Sequence[str],
        uv_resolution: m.Infra.UvResolutionSpec,
        options: PyprojectConformOptions | None = None,
    ) -> p.Result[str]:
        """Return canonical TOML with autonomous dependencies and uv policy.

        The workspace manifest owns the topology facts, including the
        namespace production scope its project declares and the members a
        workspace root environment serves. Attached members, of any family,
        retain their authored source refs. Generated bare dev floors use the
        detected provider line in ``options.flext_line``, like the scaffold;
        CUSTOM requirements never acquire provenance from provider policy unless
        that dependency is a declared floor or native source.

        Returns:
            Canonical TOML with autonomous dependencies and uv policy.

        """
        prepared = cls._conformed_provenance(
            pyproject_content,
            workspace=workspace,
            required_dev_dependencies=required_dev_dependencies,
            options=options,
        )
        if prepared.failure:
            return r[str].from_failure(prepared)
        source, project_name, source_context = prepared.value
        custom_groups = cls._workspace_custom_groups(
            source,
            pyproject_content=pyproject_content,
            workspace=workspace,
        )
        if custom_groups.failure:
            return r[str].from_failure(custom_groups)
        grouped = cls._sync_dependency_groups(
            source,
            project_name=project_name,
            required_dev_dependencies=required_dev_dependencies,
            provenance=source_context,
        )
        if grouped.failure:
            return r[str].from_failure(grouped)
        requirement_sources = cls._normalized_requirement_sources(
            source,
            source_context,
        )
        if requirement_sources.failure:
            return r[str].from_failure(requirement_sources)
        (
            local_requirements,
            _superseded_sources,
            candidate_sources,
        ) = requirement_sources.value
        if workspace.repository.role == c.Infra.MakeProfile.WORKSPACE:
            owned = cls._sync_root_environment_provenance(
                source,
                custom_groups.value,
                source_context,
            )
            if owned.failure:
                return r[str].from_failure(owned)
        cls._remove_legacy_tooling(source)
        return cls._synced_conform_tables(
            source,
            uv_resolution=uv_resolution,
            candidate_sources=candidate_sources,
            local_requirements=local_requirements,
            workspace=workspace,
        ).flat_map(lambda _synced: cls._render_pyproject(source))

    @classmethod
    def _conformed_provenance(
        cls,
        pyproject_content: str,
        *,
        workspace: m.Infra.WorkspaceSpec,
        required_dev_dependencies: Sequence[str],
        options: PyprojectConformOptions | None,
    ) -> p.Result[_ConformedProvenance]:
        """Parse the source and compose its declared requirement provenance.

        Returns:
            The parsed document, its project name, the composed requirement
            provenance.

        """
        result = r[FlextInfraUtilitiesPyprojectDocument._ConformedProvenance]
        parsed = cls.parsed_pyproject(pyproject_content)
        if parsed.failure:
            return result.from_failure(parsed)
        source, project_name = parsed.value[0], parsed.value[1]
        provenance = options if options is not None else cls.PyprojectConformOptions()
        origins = cls._declared_requirement_sources(
            project_name=project_name,
            workspace=workspace,
            required_dev_dependencies=required_dev_dependencies,
            flext_line=provenance.flext_line,
        )
        if origins.failure:
            return result.from_failure(origins)
        declared_sources, candidate_sources = origins.value
        tool = u.Cli.toml_mapping_child(parsed.value[2], c.Infra.TOOL)
        uv = u.Cli.toml_mapping_child(tool, "uv") if tool is not None else None
        native_sources = (
            u.Cli.toml_mapping_child(uv, "sources") if uv is not None else None
        )
        source_context = m.Infra.RequirementsProvenance(
            declared_sources=declared_sources,
            candidate_sources=candidate_sources,
            native_sources=(
                tuple(canonicalize_name(name) for name in native_sources)
                if native_sources is not None
                else ()
            ),
        )
        return result.ok((
            source,
            project_name,
            source_context,
        ))

    @classmethod
    def _workspace_custom_groups(
        cls,
        source: t.Cli.TomlDocument,
        *,
        pyproject_content: str,
        workspace: m.Infra.WorkspaceSpec,
    ) -> p.Result[_CustomGroupsPair]:
        """Synchronize root environment groups for workspace-role repositories.

        Returns:
            The synchronized custom group pair, empty outside the workspace role.

        """
        if workspace.repository.role != c.Infra.MakeProfile.WORKSPACE:
            return r[FlextInfraUtilitiesPyprojectDocument._CustomGroupsPair].ok((
                (),
                (),
            ))
        return cls._sync_root_environment_groups(
            source,
            pyproject_content,
        )

    @classmethod
    def _normalized_requirement_sources(
        cls,
        source: t.Cli.TomlDocument,
        provenance: m.Infra.RequirementsProvenance,
    ) -> p.Result[tuple[Sequence[str], Mapping[str, str], Mapping[str, str]]]:
        """Validate composed declarations before applying the one source context.

        Returns:
            Local requirements and source mappings, or the original failure.

        """
        result_type = r[tuple[Sequence[str], Mapping[str, str], Mapping[str, str]]]
        local = cls.document_requirement_lines(source)
        if local.failure:
            return result_type.from_failure(
                local,
            )
        unused_candidates = sorted(
            provenance.candidate_sources.keys()
            - set(FlextInfraUtilitiesDependencies.declared_dependency_names(source)),
        )
        if unused_candidates:
            return result_type.fail(
                "candidate dependencies are not declared requirements: "
                + ", ".join(unused_candidates),
            )
        normalized = cls._normalize_requirements(
            source,
            declared_sources=provenance.declared_sources,
            candidate_sources=provenance.candidate_sources,
            native_sources=provenance.native_sources,
        )
        if normalized.failure:
            return result_type.from_failure(
                normalized,
            )
        return result_type.ok(
            (local.value, provenance.declared_sources, provenance.candidate_sources),
        )

    @classmethod
    def _sync_root_environment_groups(
        cls,
        source: t.Cli.TomlDocument,
        original: str,
    ) -> p.Result[_CustomGroupsPair]:
        """Retain authored groups while removing identified generated additions.

        Returns:
            Custom DEV and CODEGEN requirements, or the original parse failure.

        """
        result_type = r[FlextInfraUtilitiesPyprojectDocument._CustomGroupsPair]
        payload = u.Cli.toml_as_mapping(source)
        if payload is None:
            return result_type.fail(
                "root metadata is not a TOML mapping",
            )
        groups = u.Cli.toml_ensure_table(source, c.Infra.DEPENDENCY_GROUPS)
        retained: MutableMapping[
            str, Sequence[str | m.Infra.DependencyGroupInclude]
        ] = {}
        for group in (str(c.Infra.DEV), c.Infra.DependencyGroup.CODEGEN):
            authored_name = cls.dependency_group_name(groups, str(group))
            custom = cls.custom_dev_additions(
                payload,
                original,
                group=group,
            )
            if custom.failure:
                return result_type.from_failure(custom)
            retained[group] = cls.merge_dependency_group_entries((), custom.value)
            u.Cli.toml_sync_value(
                groups,
                authored_name,
                cls.dependency_group_wire(retained[group]),
            )
        return result_type.ok(
            (retained[str(c.Infra.DEV)], retained[c.Infra.DependencyGroup.CODEGEN]),
        )

    @classmethod
    def _sync_root_environment_provenance(
        cls,
        source: t.Cli.TomlDocument,
        custom_groups: _CustomGroupsPair,
        context: m.Infra.RequirementsProvenance,
    ) -> p.Result[bool]:
        """Tag derived occurrences after normalizing their declared origins.

        Returns:
            Success after publication to the document, or the original failure.

        """
        for group, custom in zip(
            (str(c.Infra.DEV), c.Infra.DependencyGroup.CODEGEN),
            custom_groups,
            strict=True,
        ):
            normalized_custom: MutableSequence[
                str | m.Infra.DependencyGroupInclude
            ] = []
            for value in custom:
                if not isinstance(value, str):
                    normalized_custom.append(value)
                    continue
                canonical = cls._canonical_requirement(value, provenance=context)
                if canonical.failure:
                    return r[bool].from_failure(canonical)
                normalized_custom.append(canonical.value)
            FlextInfraUtilitiesPyprojectOverlay.sync_member_dev_provenance(
                source,
                custom=normalized_custom,
                group=group,
            )
        return r[bool].ok(value=True)

    @staticmethod
    def _declared_floor_sources(
        workspace: m.Infra.WorkspaceSpec,
        *,
        project_name: str,
        requirements: Sequence[str],
        flext_line: m.Infra.WorkspaceIntegrationSpec | None,
    ) -> p.Result[Mapping[str, str]]:
        """Derive governed source defaults solely for generated bare floors.

        Returns:
            Declared sources, or the missing provider URL failure.

        """
        declared_sources = (
            {
                member.distribution: f"git+{member.url}@{workspace.integration.branch}"
                for member in workspace.subprojects
            }
            if workspace.integration is not None
            else {}
        )
        if flext_line is not None:
            floors = {
                name
                for requirement in requirements
                if (name := FlextInfraUtilitiesDependencies.dep_name(requirement))
                and name not in {project_name, *declared_sources}
                and name.startswith("flext-")
                and requirement.strip() == name
            }
            if floors and flext_line.base_url is None:
                return r[Mapping[str, str]].fail(
                    "detected FLEXT line carries no provider base URL",
                )
            declared_sources.update({
                name: f"git+{flext_line.base_url}/{name}.git@{flext_line.branch}"
                for name in floors
            })
        return r[Mapping[str, str]].ok(declared_sources)

    @staticmethod
    def _render_pyproject(source: t.Cli.TomlDocument) -> p.Result[str]:
        """Serialize the conformed document and validate the rendered TOML.

        Returns:
            Rendered TOML, or the original invalid-render failure.

        """
        original = u.Cli.toml_dumps(source)
        payload = u.Cli.toml_as_mapping(source)
        if payload is None:
            return r[str].fail("canonical pyproject document is not a TOML mapping")
        tool = u.Cli.toml_mapping_child(payload, c.Infra.TOOL)
        if tool is not None:
            uv = u.Cli.toml_mapping_child(tool, "uv")
            if uv is not None:
                payload = u.json_mapping_adapter().validate_python({
                    **payload,
                    c.Infra.TOOL: {
                        **tool,
                        "uv": {key: uv[key] for key in sorted(uv)},
                    },
                })
        normalized = u.Cli.toml_document_from_mapping(payload)
        groups = u.Cli.toml_table_child(source, c.Infra.DEPENDENCY_GROUPS)
        if groups is not None:
            for group in (str(c.Infra.DEV), c.Infra.DependencyGroup.CODEGEN):
                if u.Cli.toml_value(groups, group) is None:
                    continue
                custom = FlextInfraUtilitiesPyprojectDocument.custom_dev_additions(
                    payload,
                    original,
                    group=group,
                )
                if custom.failure:
                    return r[str].from_failure(custom)
                FlextInfraUtilitiesPyprojectOverlay.sync_member_dev_provenance(
                    normalized,
                    custom=custom.value,
                    group=group,
                )
        rendered = u.Cli.toml_dumps(normalized)
        if u.Cli.toml_parse_text(rendered) is None:
            return r[str].fail("canonical pyproject rendering produced invalid TOML")
        return r[str].ok(rendered)

    @classmethod
    def _declared_requirement_sources(
        cls,
        *,
        project_name: str,
        workspace: m.Infra.WorkspaceSpec,
        required_dev_dependencies: Sequence[str],
        flext_line: m.Infra.WorkspaceIntegrationSpec | None,
    ) -> p.Result[tuple[Mapping[str, str], Mapping[str, str]]]:
        """Return the declared and candidate Git sources of internal requirements.

        Explicit requirement URLs and refs remain authoritative. Source-less
        members use their governed workspace line; generated bare ``flext-*``
        floors use the detected FLEXT line. Candidate dependencies must be
        declared requirements.

        Returns:
            The declared and candidate requirement sources.

        """
        declared = cls._declared_floor_sources(
            workspace,
            project_name=project_name,
            requirements=required_dev_dependencies,
            flext_line=flext_line,
        )
        if declared.failure:
            return r[tuple[Mapping[str, str], Mapping[str, str]]].from_failure(declared)
        declared_sources = declared.value
        candidate_sources = {
            item.distribution: f"git+{item.url}@{item.commit}"
            for item in workspace.candidate_dependencies
        }
        return r[tuple[Mapping[str, str], Mapping[str, str]]].ok(
            (declared_sources, candidate_sources),
        )

    @classmethod
    def _synced_conform_tables(
        cls,
        source: t.Cli.TomlDocument,
        *,
        uv_resolution: m.Infra.UvResolutionSpec,
        candidate_sources: Mapping[str, str],
        local_requirements: Sequence[str],
        workspace: m.Infra.WorkspaceSpec,
    ) -> p.Result[bool]:
        """Sync the canonical typecheck, namespace, uv, and provenance tables.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        cls._remove_legacy_tooling(source)
        project = u.Cli.toml_table_child(source, c.Infra.PROJECT)
        optional = (
            u.Cli.toml_table_child(project, c.Infra.OPTIONAL_DEPENDENCIES)
            if project is not None
            else None
        )
        deptry = u.Cli.toml_ensure_path(source, (c.Infra.TOOL, c.Infra.DEPTRY))
        u.Cli.toml_sync_string_list(
            deptry,
            "optional_dependencies_dev_groups",
            [
                group
                for group in (
                    FlextInfraUtilitiesProjectManagedArtifacts.native_tool_setting(
                        config.Infra.tooling,
                        c.Infra.DEPTRY,
                        "optional_dependencies_dev_groups",
                        TypeForm(Sequence[str]),
                    )
                )
                if optional is not None and group in optional
            ],
        )
        typecheck_paths = cls._sync_typecheck_paths(source)
        if typecheck_paths.failure:
            return r[bool].from_failure(typecheck_paths)
        namespace_scope = cls._sync_namespace_scope(
            source,
            workspace.project.namespace_scan_dirs
            if workspace.project is not None
            else None,
        )
        if namespace_scope.failure:
            return r[bool].from_failure(namespace_scope)
        cls._sync_project_documentation(source, workspace.project)
        sources_result = cls._sync_uv_sources(
            source,
            resolution=uv_resolution,
            candidate_sources=candidate_sources,
            workspace=workspace,
            local_requirements=local_requirements,
        )
        if sources_result.failure:
            return r[bool].from_failure(sources_result)
        provenance_result = cls._validate_dependency_provenance(
            source,
            workspace=workspace,
        )
        if provenance_result.failure:
            return r[bool].from_failure(provenance_result)
        return r[bool].ok(value=True)

    @staticmethod
    def _remove_legacy_tooling(document: t.Cli.TomlDocument) -> None:
        """Delete legacy packaging owners superseded by canonical conformance.

        The ``[tool.flext]`` table is preserved because it carries project-local
        tooling policy unrelated to repository topology.
        """
        tool = u.Cli.toml_table_child(document, c.Infra.TOOL)
        if tool is None:
            return
        u.Cli.toml_remove_key_if_present(tool, c.Infra.POETRY)

    @staticmethod
    def _sync_project_documentation(
        document: t.Cli.TomlDocument,
        project: m.Infra.ProjectSpec | None,
    ) -> None:
        """Resolve the sole project declaration through the owned leaf policy."""
        FlextInfraUtilitiesPyprojectDocument._sync_documentation_language(
            document,
            project.documentation_language if project is not None else "en",
        )

    @classmethod
    def project_documentation_metadata(
        cls,
        source: str,
        project: m.Infra.ProjectSpec | None,
    ) -> p.Result[str]:
        """Project only documentation metadata without conformance planning.

        Returns:
            Strictly validated metadata, retaining exact unchanged source bytes.

        """
        payload = u.Cli.toml_mapping_from_text(source)
        if payload is None:
            return r[str].fail("invalid documentation pyproject TOML")
        validated = r[u.PyprojectDocument].create_from_callable(
            partial(u.PyprojectDocument.model_validate, payload)
        )
        if validated.failure:
            return r[str].from_failure(validated)
        document = u.Cli.toml_parse_text(source)
        if document is None:
            return r[str].fail("invalid documentation pyproject document")
        before = u.Cli.toml_dumps(document)
        cls._sync_project_documentation(document, project)
        projected = u.Cli.toml_dumps(document)
        if projected == before:
            return r[str].ok(source)
        desired = u.Cli.toml_mapping_from_text(projected)
        checked = r[u.PyprojectDocument].create_from_callable(
            partial(u.PyprojectDocument.model_validate, desired)
        )
        if checked.failure:
            return r[str].from_failure(checked)
        return r[str].ok(projected)

    @staticmethod
    def _sync_documentation_language(
        document: t.Cli.TomlDocument,
        language: t.Infra.DocumentationLanguage,
    ) -> None:
        """Project one owned leaf without taking over CUSTOM documentation policy."""
        tool = u.Cli.toml_table_child(document, c.Infra.TOOL)
        flext = u.Cli.toml_table_child(tool, "flext") if tool is not None else None
        docs = u.Cli.toml_table_child(flext, "docs") if flext is not None else None
        if language == "en":
            if docs is not None:
                u.Cli.toml_remove_key_if_present(docs, "documentation_language")
            return
        if docs is None:
            docs = u.Cli.toml_ensure_path(document, (c.Infra.TOOL, "flext", "docs"))
        if u.Cli.toml_value(docs, "documentation_language") == language:
            return
        docs["documentation_language"] = language

    @staticmethod
    def _sync_namespace_scope(
        document: t.Cli.TomlDocument,
        namespace_scan_dirs: Sequence[str] | None,
    ) -> p.Result[bool]:
        """Sync ``[tool.flext.namespace].scan_dirs`` from the project SSOT.

        ``None`` or an empty sequence leaves the section untouched: projects
        without a declared scope keep the dynamic every-root behavior. A
        non-empty sequence is the workspace manifest's production scope.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if not namespace_scan_dirs:
            return r[bool].ok(value=True)
        namespace = u.Cli.toml_ensure_path(document, c.Infra.CONFORM_NAMESPACE_TABLE)
        u.Cli.toml_sync_string_list(namespace, "scan_dirs", list(namespace_scan_dirs))
        return r[bool].ok(value=True)

    @staticmethod
    def _sync_typecheck_paths(document: t.Cli.TomlDocument) -> p.Result[bool]:
        """Remove checkout-absolute type checker interpreter pins.

        Search paths belong to the analyzer phase. Preserve its member-local
        execution environments and their order through full generation.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        tool = u.Cli.toml_table_child(document, c.Infra.TOOL)
        if tool is None:
            return r[bool].ok(value=True)
        pyrefly = u.Cli.toml_table_child(tool, c.Infra.PYREFLY)
        if pyrefly is not None:
            u.Cli.toml_remove_key_if_present(pyrefly, "python-interpreter-path")

        pyright = u.Cli.toml_table_child(tool, c.Infra.PYRIGHT)
        if pyright is None:
            return r[bool].ok(value=True)

        # Environment selection is owned by Make and the opened editor folder.
        interpreter_keys = ("pythonPath", "pythonInterpreterPath")
        for key in interpreter_keys:
            u.Cli.toml_remove_key_if_present(pyright, key)
        raw_environments = u.Cli.json_as_sequence(
            u.Cli.toml_value(pyright, "executionEnvironments"),
        )
        normalized_environments: list[t.JsonValue] = []
        for index, environment in enumerate(raw_environments):
            if not isinstance(environment, Mapping):
                return r[bool].fail(
                    f"tool.pyright.executionEnvironments[{index}] must be a mapping",
                )
            mapping = u.json_mapping_adapter().validate_python(environment)
            normalized: t.JsonDict = dict(mapping)
            for key in ("venv", "venvPath", "pythonPath", "pythonInterpreterPath"):
                normalized.pop(key, None)
            normalized_environments.append(normalized)
        if raw_environments:
            u.Cli.toml_sync_value(
                pyright,
                "executionEnvironments",
                normalized_environments,
            )
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraUtilitiesPyprojectDocument"]
