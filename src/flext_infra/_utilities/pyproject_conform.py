"""Pure Git-first pyproject conformance through the flext-cli TOML facade."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import u
from flext_infra import c, r, t
from flext_infra._utilities.dependencies import FlextInfraUtilitiesDependencies

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraUtilitiesPyprojectConform:
    """Produce deterministic Git-first pyproject content without filesystem writes."""

    # NOTE (multi-agent, mro-wkii.17.9): this pure renderer replaces the
    # mutating deps path-sync command; codegen is the only public orchestrator.

    @classmethod
    def pyproject_conform(
        cls,
        pyproject_content: str,
        *,
        repositories: t.SequenceOf[p.Infra.RepositoryRef],
        workspace: p.Infra.WorkspaceSpec,
        toolchain: p.Infra.ToolchainSpec,
        build: p.Infra.ScaffoldBuildSpec,
        resources: t.SequenceOf[p.Infra.ResourceSpec],
        project_root: Path,
        package_name: str,
        allow_missing_required: bool = False,
    ) -> p.Result[str]:
        """Return canonical PEP 517/621 TOML with deterministic wheel resources."""
        source = u.Cli.toml_parse_text(pyproject_content)
        if source is None:
            return r[str].fail("pyproject content is not valid TOML")
        project = u.Cli.toml_table_child(source, c.Infra.PROJECT)
        if project is None:
            return r[str].fail("pyproject content must define [project]")
        project_name_raw = u.Cli.toml_value(project, c.Infra.NAME)
        if not isinstance(project_name_raw, str) or not project_name_raw.strip():
            return r[str].fail("[project].name must be a non-empty string")
        project_name = project_name_raw.strip()

        metadata_result = cls._validate_project_metadata(project)
        if metadata_result.failure:
            return r[str].fail(metadata_result.error or "PEP 621 metadata is invalid")

        normalized = cls._normalize_requirements(source)
        if normalized.failure:
            return r[str].fail(normalized.error or "dependency normalization failed")
        cls._sync_dependency_groups(
            source, project_name=project_name, workspace=workspace
        )
        cls._remove_legacy_tooling(source)
        typecheck_paths = cls._sync_typecheck_paths(source)
        if typecheck_paths.failure:
            return r[str].fail(
                typecheck_paths.error or "type checker path conformance failed"
            )
        sources_result = cls._sync_uv_sources(
            source,
            project_name=project_name,
            repositories=repositories,
            workspace=workspace,
            required_version=toolchain.uv_required_version,
        )
        if sources_result.failure:
            return r[str].fail(sources_result.error or "uv source conformance failed")
        # NOTE(mro-wkii.17.26, agent codex): create ``tool.uv`` before
        # ``tool.hatch`` so TOMLKit promotion preserves one stable table order.
        layout_result = cls._sync_build_and_resources(
            source,
            build=build,
            resources=resources,
            project_root=project_root,
            package_name=package_name,
            allow_missing_required=allow_missing_required,
        )
        if layout_result.failure:
            return r[str].fail(layout_result.error or "package layout is invalid")

        rendered = u.Cli.toml_dumps(source)
        if u.Cli.toml_parse_text(rendered) is None:
            return r[str].fail("canonical pyproject rendering produced invalid TOML")
        return r[str].ok(rendered)

    @staticmethod
    def _validate_project_metadata(project: t.Cli.TomlTable) -> p.Result[bool]:
        """Require the modern static PEP 621 fields shared by uv, pip, and Poetry."""
        # mro-wkii.17.26 (codex): metadata validation is read-only by contract.
        for key in ("name", "version", "description", "readme", "requires-python"):
            value = u.Cli.toml_value(project, key)
            if not isinstance(value, str) or not value.strip():
                return r[bool].fail(f"[project].{key} must be a non-empty string")
        return r[bool].ok(True)

    @classmethod
    def _sync_build_and_resources(
        cls,
        document: t.Cli.TomlDocument,
        *,
        build: p.Infra.ScaffoldBuildSpec,
        resources: t.SequenceOf[p.Infra.ResourceSpec],
        project_root: Path,
        package_name: str,
        allow_missing_required: bool,
    ) -> p.Result[bool]:
        """Generate one Hatch wheel layout from repository-root resource SSOTs."""
        package_root = project_root / "src" / package_name
        if not package_root.is_dir() and not allow_missing_required:
            return r[bool].fail(f"import package directory is missing: {package_root}")

        sources: set[str] = set()
        destinations: set[str] = set()
        wheel_resources: list[tuple[str, str]] = []
        for resource in resources:
            source = resource.source.as_posix()
            if resource.source.is_absolute() or ".." in resource.source.parts:
                return r[bool].fail(f"resource source escapes project root: {source}")
            if source in sources:
                return r[bool].fail(f"duplicate resource source: {source}")
            sources.add(source)
            resource_root = project_root / resource.source
            legacy_root = package_root / resource.source
            if resource_root.is_dir() and legacy_root.is_dir():
                return r[bool].fail(
                    "resource exists at root and inside the package namespace: "
                    f"{source}"
                )
            available = resource_root.is_dir() or legacy_root.is_dir()
            if resource.required and not available and not allow_missing_required:
                return r[bool].fail(
                    f"required resource directory is missing: {resource_root}"
                )
            if resource.wheel_destination is None or not (
                available or (resource.required and allow_missing_required)
            ):
                continue
            destination = resource.wheel_destination.format(package_name=package_name)
            destination_path = Path(destination)
            if destination_path.is_absolute() or ".." in destination_path.parts:
                return r[bool].fail(
                    f"wheel resource destination escapes package: {destination}"
                )
            if destination in destinations:
                return r[bool].fail(
                    f"duplicate wheel resource destination: {destination}"
                )
            destinations.add(destination)
            wheel_resources.append((source, destination))

        build_system = u.Cli.toml_ensure_table(document, "build-system")
        u.Cli.toml_sync_value(build_system, "build-backend", build.backend)
        u.Cli.toml_sync_string_list(
            build_system, "requires", build.requirements
        )
        tool = u.Cli.toml_ensure_table(document, c.Infra.TOOL)
        hatch = u.Cli.toml_ensure_table(tool, "hatch")
        hatch_build = u.Cli.toml_ensure_table(hatch, "build")
        targets = u.Cli.toml_ensure_table(hatch_build, "targets")
        wheel = u.Cli.toml_ensure_table(targets, "wheel")
        u.Cli.toml_sync_string_list(wheel, "packages", (f"src/{package_name}",))
        force_include = u.Cli.toml_ensure_table(wheel, "force-include")
        for key in tuple(force_include):
            u.Cli.toml_remove_key_if_present(force_include, key)
        for source, destination in wheel_resources:
            u.Cli.toml_sync_value(force_include, source, destination)
        return r[bool].ok(True)

    @classmethod
    def _normalize_requirements(cls, document: t.Cli.TomlDocument) -> p.Result[bool]:
        """Remove direct local references from every declared FLEXT requirement."""
        project = u.Cli.toml_ensure_table(document, c.Infra.PROJECT)
        normalized = cls._normalize_requirement_field(project, c.Infra.DEPENDENCIES)
        if normalized.failure:
            return normalized
        for section_name in (c.Infra.OPTIONAL_DEPENDENCIES, c.Infra.DEPENDENCY_GROUPS):
            parent = (
                project if section_name == c.Infra.OPTIONAL_DEPENDENCIES else document
            )
            section = u.Cli.toml_table_child(parent, section_name)
            if section is None:
                continue
            for group_name in tuple(section):
                group_result = cls._normalize_requirement_field(section, group_name)
                if group_result.failure:
                    return group_result
        return r[bool].ok(True)

    @classmethod
    def _normalize_requirement_field(
        cls, container: t.Cli.TomlDocument | t.Cli.TomlTable, key: str
    ) -> p.Result[bool]:
        """Normalize one dependency array and fail on model-less entries."""
        raw_value = u.Cli.toml_value(container, key)
        if raw_value is None:
            return r[bool].ok(True)
        raw_items = u.Cli.json_as_sequence(raw_value)
        try:
            items = t.Infra.STR_SEQ_ADAPTER.validate_python(raw_items, strict=True)
        except c.ValidationError as exc:
            return r[bool].fail_op(f"validate dependency group {key}", exc)
        canonical = FlextInfraUtilitiesDependencies.dedupe_specs(
            tuple(cls._canonical_requirement(item) for item in items)
        )
        u.Cli.toml_sync_string_list(container, key, canonical)
        return r[bool].ok(True)

    @staticmethod
    def _canonical_requirement(requirement: str) -> str:
        """Strip local/direct locations from FLEXT requirements only."""
        dependency_name = FlextInfraUtilitiesDependencies.dep_name(requirement)
        if dependency_name is None or not dependency_name.startswith("flext-"):
            return requirement.strip()
        requirement_part, separator, marker = requirement.partition(";")
        if " @ " in requirement_part:
            canonical = requirement_part.split(" @ ", maxsplit=1)[0].strip()
        elif (
            "../flext" in requirement_part
            or "/flext-" in requirement_part
            or ".flext-deps" in requirement_part
        ):
            canonical = dependency_name
        else:
            canonical = requirement_part.strip()
        return (
            f"{canonical};{marker.strip()}"
            if separator and marker.strip()
            else canonical
        )

    @staticmethod
    def _sync_dependency_groups(
        document: t.Cli.TomlDocument,
        *,
        project_name: str,
        workspace: p.Infra.WorkspaceSpec,
    ) -> None:
        """Migrate optional dev dependencies and set canonical generated groups."""
        project = u.Cli.toml_ensure_table(document, c.Infra.PROJECT)
        groups = u.Cli.toml_ensure_table(document, c.Infra.DEPENDENCY_GROUPS)
        optional = u.Cli.toml_table_child(project, c.Infra.OPTIONAL_DEPENDENCIES)
        optional_dev: t.StrSequence = ()
        if optional is not None:
            optional_dev = u.Cli.toml_as_string_list(
                u.Cli.toml_value(optional, str(c.Infra.DEV))
            )
        dev = [
            *u.Cli.toml_as_string_list(u.Cli.toml_value(groups, str(c.Infra.DEV))),
            *optional_dev,
        ]
        if project_name != "flext-tests":
            dev.append("flext-tests")
        u.Cli.toml_sync_string_list(
            groups,
            str(c.Infra.DEV),
            FlextInfraUtilitiesDependencies.dedupe_specs(tuple(dev)),
        )

        codegen = list(u.Cli.toml_as_string_list(u.Cli.toml_value(groups, "codegen")))
        if project_name != "flext-infra":
            codegen.append("flext-infra")
        u.Cli.toml_sync_string_list(
            groups,
            "codegen",
            FlextInfraUtilitiesDependencies.dedupe_specs(tuple(codegen)),
        )
        workspace_members = (
            tuple(sorted(member.distribution for member in workspace.members))
            if project_name == workspace.repository.distribution
            else ()
        )
        u.Cli.toml_sync_string_list(groups, "workspace", workspace_members)

        if optional is not None:
            u.Cli.toml_remove_key_if_present(optional, str(c.Infra.DEV))
            if not tuple(optional):
                u.Cli.toml_remove_key_if_present(project, c.Infra.OPTIONAL_DEPENDENCIES)

    @staticmethod
    def _remove_legacy_tooling(document: t.Cli.TomlDocument) -> None:
        """Delete topology and packaging owners superseded by config/workspace.yaml."""
        tool = u.Cli.toml_ensure_table(document, c.Infra.TOOL)
        u.Cli.toml_remove_key_if_present(tool, c.Infra.POETRY)
        uv = u.Cli.toml_table_child(tool, "uv")
        if uv is not None:
            u.Cli.toml_remove_key_if_present(uv, "workspace")
        flext = u.Cli.toml_table_child(tool, "flext")
        if flext is not None:
            u.Cli.toml_remove_key_if_present(flext, "workspace")
            if not tuple(flext):
                u.Cli.toml_remove_key_if_present(tool, "flext")

    @staticmethod
    def _sync_typecheck_paths(document: t.Cli.TomlDocument) -> p.Result[bool]:
        """Remove checkout- and interpreter-specific type checker paths."""
        tool = u.Cli.toml_ensure_table(document, c.Infra.TOOL)
        pyrefly = u.Cli.toml_table_child(tool, c.Infra.PYREFLY)
        if pyrefly is not None:
            u.Cli.toml_sync_string_list(
                pyrefly, c.Infra.SEARCH_PATH, (".", "src")
            )
        mypy = u.Cli.toml_table_child(tool, c.Infra.MYPY)
        if mypy is not None:
            u.Cli.toml_sync_string_list(mypy, "mypy_path", (".", "src"))
        pyright = u.Cli.toml_table_child(tool, c.Infra.PYRIGHT)
        if pyright is None:
            return r[bool].ok(True)
        u.Cli.toml_sync_string_list(pyright, c.Infra.EXTRA_PATHS, (".", "src"))
        interpreter_keys = (
            "venv",
            "venvPath",
            "pythonPath",
            "pythonInterpreterPath",
        )
        for key in interpreter_keys:
            u.Cli.toml_remove_key_if_present(pyright, key)
        raw_environments = u.Cli.json_as_sequence(
            u.Cli.toml_value(pyright, "executionEnvironments")
        )
        normalized_environments: t.JsonValueList = []
        for index, environment in enumerate(raw_environments):
            mapping = u.Cli.json_as_mapping(environment)
            if mapping is None:
                return r[bool].fail(
                    f"tool.pyright.executionEnvironments[{index}] must be a mapping"
                )
            normalized: t.JsonDict = dict(mapping)
            root = normalized.get("root")
            normalized[c.Infra.EXTRA_PATHS] = [
                "src"
            ] if root == "src" else [".", "src"]
            for key in interpreter_keys:
                normalized.pop(key, None)
            normalized_environments.append(normalized)
        if raw_environments:
            u.Cli.toml_sync_value(
                pyright, "executionEnvironments", normalized_environments
            )
        return r[bool].ok(True)

    @classmethod
    def _sync_uv_sources(
        cls,
        document: t.Cli.TomlDocument,
        *,
        project_name: str,
        repositories: t.SequenceOf[p.Infra.RepositoryRef],
        workspace: p.Infra.WorkspaceSpec,
        required_version: str,
    ) -> p.Result[bool]:
        """Replace managed sources with exact Git URL and branch pairs."""
        payload = u.Cli.toml_as_mapping(document)
        if payload is None:
            return r[bool].fail("pyproject document is not a TOML mapping")
        declared = set(
            FlextInfraUtilitiesDependencies.declared_dependency_names_from_payload(
                payload
            )
        )
        required_names = {name for name in declared if name.startswith("flext-")}
        if project_name == workspace.repository.distribution:
            required_names.update(member.distribution for member in workspace.members)
        available = (
            *repositories,
            workspace.repository,
            *workspace.members,
            *workspace.content_only,
        )
        resolved: t.MutableSequenceOf[p.Infra.RepositoryRef] = []
        for distribution in sorted(required_names):
            matches = tuple(
                repository
                for repository in available
                if repository.distribution == distribution
            )
            if not matches:
                return r[bool].fail(
                    f"repository catalog lacks required distribution: {distribution}"
                )
            reference = matches[0]
            if any(
                item.url != reference.url or item.branch != reference.branch
                for item in matches[1:]
            ):
                return r[bool].fail(
                    f"repository catalog conflicts for distribution: {distribution}"
                )
            resolved.append(reference)

        tool = u.Cli.toml_ensure_table(document, c.Infra.TOOL)
        uv = u.Cli.toml_ensure_table(tool, "uv")
        u.Cli.toml_sync_value(uv, "required-version", required_version)
        u.Cli.toml_remove_key_if_present(uv, "workspace")
        sources = u.Cli.toml_ensure_table(uv, "sources")
        managed_names = {
            repository.distribution
            for repository in available
            if repository.distribution.startswith("flext-")
            or repository in workspace.members
        }
        resolved_names = {repository.distribution for repository in resolved}
        for source_name in tuple(sources):
            if (
                source_name.startswith("flext-") or source_name in managed_names
            ) and source_name not in resolved_names:
                u.Cli.toml_remove_key_if_present(sources, source_name)
        for repository in resolved:
            u.Cli.toml_sync_mapping_table(
                sources,
                repository.distribution,
                {"git": repository.url, "branch": repository.branch},
            )
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraUtilitiesPyprojectConform"]
