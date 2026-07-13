"""Pure Git-first pyproject conformance through the flext-cli TOML facade."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_cli import u
from flext_core import r

from flext_infra import c, t
from flext_infra._utilities.dependencies import FlextInfraUtilitiesDependencies

if TYPE_CHECKING:
    from flext_infra import m, p


class FlextInfraUtilitiesPyprojectConform:
    """Produce deterministic Git-first pyproject content without filesystem writes."""

    # NOTE (multi-agent, mro-wkii.17.9): this pure renderer replaces the
    # mutating deps path-sync command; codegen is the only public orchestrator.

    @classmethod
    def pyproject_conform(
        cls,
        pyproject_content: str,
        *,
        repositories: t.SequenceOf[m.Infra.RepositoryRef],
        workspace: m.Infra.WorkspaceSpec,
        toolchain: m.Infra.ToolchainSpec,
    ) -> p.Result[str]:
        """Return canonical TOML with Git sources, PEP 735 groups, and uv pins."""
        source = u.Cli.toml_mapping_from_text(pyproject_content)
        if source is None:
            return r[str].fail("pyproject content is not valid TOML")
        payload: t.MutableJsonMapping = {key: source[key] for key in source}
        project = u.Cli.toml_mapping_child(payload, c.Infra.PROJECT)
        if project is None:
            return r[str].fail("pyproject content must define [project]")
        project_name_raw = project.get(c.Infra.NAME, None)
        if not isinstance(project_name_raw, str) or not project_name_raw.strip():
            return r[str].fail("[project].name must be a non-empty string")
        project_name = project_name_raw.strip()

        normalized = cls._normalize_requirements(payload)
        if normalized.failure:
            return r[str].fail(normalized.error or "dependency normalization failed")
        cls._sync_dependency_groups(
            payload,
            project_name=project_name,
            workspace=workspace,
        )
        cls._remove_legacy_tooling(payload)
        cls._sync_typecheck_paths(payload)
        sources_result = cls._sync_uv_sources(
            payload,
            project_name=project_name,
            repositories=repositories,
            workspace=workspace,
            required_version=toolchain.uv_required_version,
        )
        if sources_result.failure:
            return r[str].fail(sources_result.error or "uv source conformance failed")

        rendered = u.Cli.toml_dumps(u.Cli.toml_document_from_mapping(payload))
        if u.Cli.toml_mapping_from_text(rendered) is None:
            return r[str].fail("canonical pyproject rendering produced invalid TOML")
        return r[str].ok(rendered)

    @classmethod
    def _normalize_requirements(
        cls,
        payload: t.MutableJsonMapping,
    ) -> p.Result[bool]:
        """Remove direct local references from every declared FLEXT requirement."""
        project = u.Cli.toml_mapping_ensure_table(payload, c.Infra.PROJECT)
        normalized = cls._normalize_requirement_field(
            project,
            c.Infra.DEPENDENCIES,
        )
        if normalized.failure:
            return normalized
        for section_name in (
            c.Infra.OPTIONAL_DEPENDENCIES,
            c.Infra.DEPENDENCY_GROUPS,
        ):
            section = u.Cli.toml_mapping_child(
                project if section_name == c.Infra.OPTIONAL_DEPENDENCIES else payload,
                section_name,
            )
            if section is None:
                continue
            mutable_section = u.Cli.toml_mapping_ensure_table(
                project if section_name == c.Infra.OPTIONAL_DEPENDENCIES else payload,
                section_name,
            )
            for group_name in tuple(section):
                group_result = cls._normalize_requirement_field(
                    mutable_section,
                    group_name,
                )
                if group_result.failure:
                    return group_result
        return r[bool].ok(True)

    @classmethod
    def _normalize_requirement_field(
        cls,
        container: t.MutableJsonMapping,
        key: str,
    ) -> p.Result[bool]:
        """Normalize one dependency array and fail on model-less entries."""
        raw_value = container.get(key, None)
        if raw_value is None:
            return r[bool].ok(True)
        raw_items = u.Cli.json_as_sequence(raw_value)
        try:
            items = t.Infra.STR_SEQ_ADAPTER.validate_python(raw_items, strict=True)
        except c.ValidationError as exc:
            return r[bool].fail_op(f"validate dependency group {key}", exc)
        canonical = FlextInfraUtilitiesDependencies.dedupe_specs(
            tuple(cls._canonical_requirement(item) for item in items),
        )
        u.Cli.toml_mapping_sync_string_list(container, key, canonical)
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
        payload: t.MutableJsonMapping,
        *,
        project_name: str,
        workspace: m.Infra.WorkspaceSpec,
    ) -> None:
        """Migrate optional dev dependencies and set canonical generated groups."""
        project = u.Cli.toml_mapping_ensure_table(payload, c.Infra.PROJECT)
        groups = u.Cli.toml_mapping_ensure_table(payload, c.Infra.DEPENDENCY_GROUPS)
        optional = u.Cli.toml_mapping_child(project, c.Infra.OPTIONAL_DEPENDENCIES)
        optional_dev: t.StrSequence = ()
        if optional is not None:
            optional_dev = u.Cli.toml_as_string_list(optional.get(str(c.Infra.DEV)))
        dev = [
            *u.Cli.toml_as_string_list(groups.get(str(c.Infra.DEV))),
            *optional_dev,
        ]
        if project_name != "flext-tests":
            dev.append("flext-tests")
        u.Cli.toml_mapping_sync_string_list(
            groups,
            str(c.Infra.DEV),
            FlextInfraUtilitiesDependencies.dedupe_specs(tuple(dev)),
        )

        codegen = list(u.Cli.toml_as_string_list(groups.get("codegen")))
        if project_name != "flext-infra":
            codegen.append("flext-infra")
        u.Cli.toml_mapping_sync_string_list(
            groups,
            "codegen",
            FlextInfraUtilitiesDependencies.dedupe_specs(tuple(codegen)),
        )
        workspace_members = (
            tuple(sorted(member.distribution for member in workspace.members))
            if project_name == workspace.repository.distribution
            else ()
        )
        u.Cli.toml_mapping_sync_string_list(
            groups,
            "workspace",
            workspace_members,
        )

        optional_mutable = u.Cli.toml_mapping_path(
            payload,
            (c.Infra.PROJECT, c.Infra.OPTIONAL_DEPENDENCIES),
        )
        if optional_mutable is not None:
            u.Cli.toml_mapping_remove_key_if_present(
                optional_mutable,
                str(c.Infra.DEV),
            )
            if not optional_mutable:
                u.Cli.toml_mapping_remove_key_if_present(
                    project,
                    c.Infra.OPTIONAL_DEPENDENCIES,
                )

    @staticmethod
    def _remove_legacy_tooling(payload: t.MutableJsonMapping) -> None:
        """Delete topology and packaging owners superseded by config/workspace.yaml."""
        tool = u.Cli.toml_mapping_ensure_table(payload, c.Infra.TOOL)
        u.Cli.toml_mapping_remove_key_if_present(tool, c.Infra.POETRY)
        uv = u.Cli.toml_mapping_child(tool, "uv")
        if uv is not None:
            mutable_uv = u.Cli.toml_mapping_ensure_table(tool, "uv")
            u.Cli.toml_mapping_remove_key_if_present(mutable_uv, "workspace")
        flext = u.Cli.toml_mapping_child(tool, "flext")
        if flext is not None:
            mutable_flext = u.Cli.toml_mapping_ensure_table(tool, "flext")
            u.Cli.toml_mapping_remove_key_if_present(mutable_flext, "workspace")
            if not mutable_flext:
                u.Cli.toml_mapping_remove_key_if_present(tool, "flext")

    @staticmethod
    def _sync_typecheck_paths(payload: t.MutableJsonMapping) -> None:
        """Remove checkout- and interpreter-specific type checker paths."""
        tool = u.Cli.toml_mapping_ensure_table(payload, c.Infra.TOOL)
        pyrefly = u.Cli.toml_mapping_child(tool, c.Infra.PYREFLY)
        if pyrefly is not None:
            u.Cli.toml_mapping_sync_string_list(
                u.Cli.toml_mapping_ensure_table(tool, c.Infra.PYREFLY),
                c.Infra.SEARCH_PATH,
                (".", "src"),
            )
        mypy = u.Cli.toml_mapping_child(tool, c.Infra.MYPY)
        if mypy is not None:
            u.Cli.toml_mapping_sync_string_list(
                u.Cli.toml_mapping_ensure_table(tool, c.Infra.MYPY),
                "mypy_path",
                (".", "src"),
            )
        pyright = u.Cli.toml_mapping_child(tool, c.Infra.PYRIGHT)
        if pyright is None:
            return
        mutable_pyright = u.Cli.toml_mapping_ensure_table(tool, c.Infra.PYRIGHT)
        u.Cli.toml_mapping_sync_string_list(
            mutable_pyright,
            c.Infra.EXTRA_PATHS,
            (".", "src"),
        )
        for key in ("venv", "venvPath", "pythonPath", "pythonInterpreterPath"):
            u.Cli.toml_mapping_remove_key_if_present(mutable_pyright, key)
        environments = u.Cli.json_as_sequence(
            mutable_pyright.get("executionEnvironments"),
        )
        for environment in environments:
            if not isinstance(environment, dict):
                continue
            root = environment.get("root")
            expected_paths = ("src",) if root == "src" else (".", "src")
            u.Cli.toml_mapping_sync_string_list(
                environment,
                c.Infra.EXTRA_PATHS,
                expected_paths,
            )
            for key in ("venv", "venvPath", "pythonPath", "pythonInterpreterPath"):
                u.Cli.toml_mapping_remove_key_if_present(environment, key)

    @classmethod
    def _sync_uv_sources(
        cls,
        payload: t.MutableJsonMapping,
        *,
        project_name: str,
        repositories: t.SequenceOf[m.Infra.RepositoryRef],
        workspace: m.Infra.WorkspaceSpec,
        required_version: str,
    ) -> p.Result[bool]:
        """Replace managed sources with exact Git URL and branch pairs."""
        declared = set(
            FlextInfraUtilitiesDependencies.declared_dependency_names_from_payload(
                payload,
            ),
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
        resolved: t.MutableSequenceOf[m.Infra.RepositoryRef] = []
        for distribution in sorted(required_names):
            matches = tuple(
                repository
                for repository in available
                if repository.distribution == distribution
            )
            if not matches:
                return r[bool].fail(
                    f"repository catalog lacks required distribution: {distribution}",
                )
            reference = matches[0]
            if any(
                item.url != reference.url or item.branch != reference.branch
                for item in matches[1:]
            ):
                return r[bool].fail(
                    f"repository catalog conflicts for distribution: {distribution}",
                )
            resolved.append(reference)

        tool = u.Cli.toml_mapping_ensure_table(payload, c.Infra.TOOL)
        uv = u.Cli.toml_mapping_ensure_table(tool, "uv")
        u.Cli.toml_mapping_sync_value(uv, "required-version", required_version)
        u.Cli.toml_mapping_remove_key_if_present(uv, "workspace")
        sources = u.Cli.toml_mapping_ensure_table(uv, "sources")
        managed_names = {
            repository.distribution
            for repository in available
            if repository.distribution.startswith("flext-")
            or repository in workspace.members
        }
        for source_name in tuple(sources):
            if source_name.startswith("flext-") or source_name in managed_names:
                u.Cli.toml_mapping_remove_key_if_present(sources, source_name)
        for repository in resolved:
            u.Cli.toml_mapping_sync_mapping_table(
                sources,
                repository.distribution,
                {"git": repository.url, "branch": repository.branch},
            )
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraUtilitiesPyprojectConform"]
