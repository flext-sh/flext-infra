"""Autonomous library pyproject conformance through the flext-cli TOML facade."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_cli import r, u
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.typings import t
from flext_infra._utilities.dependencies import FlextInfraUtilitiesDependencies
from flext_infra._utilities.repository import FlextInfraUtilitiesRepository

if TYPE_CHECKING:
    from flext_infra.protocols import p


class FlextInfraUtilitiesPyprojectConform:
    """Render repository-local project metadata deterministically."""

    # NOTE (multi-agent, mro-wkii.17.9): this pure renderer replaces the
    # mutating deps path-sync command; codegen is the only public orchestrator.

    @classmethod
    def pyproject_conform(
        cls,
        pyproject_content: str,
        *,
        providers: t.SequenceOf[m.Infra.ProviderSpec],
        workspace: p.Infra.WorkspaceSpec,
        toolchain: p.Infra.ToolchainSpec,
        required_dev_dependencies: t.StrSequence,
        uv_link_mode: str | None = None,
        uv_exclude_newer: str | None = None,
        uv_exclude_dependencies: t.SequenceOf[p.Model] = (),
    ) -> p.Result[str]:
        """Return canonical TOML with autonomous dependencies and tool policy.

        ``uv_exclude_newer`` is the per-project overlay over the fleet cooldown.
        The fleet default is a ROLLING window, which silently ages past a
        security floor declared in override-dependencies and makes resolution
        unsatisfiable; a project carrying such a floor pins the absolute cutoff
        instead. ``None`` keeps the fleet window.
        """
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

        version_result = cls._sync_project_version(project, workspace=workspace)
        if version_result.failure:
            return r[str].fail(
                version_result.error or "project version conformance failed"
            )
        cls._sync_dependency_groups(
            source,
            project_name=project_name,
            required_dev_dependencies=required_dev_dependencies,
        )
        normalized = cls._normalize_requirements(
            source, providers=providers, workspace=workspace, canonicalize_all=True
        )
        if normalized.failure:
            return r[str].fail(normalized.error or "dependency normalization failed")
        cls._remove_legacy_tooling(source)
        typecheck_paths = cls._sync_typecheck_paths(source)
        if typecheck_paths.failure:
            return r[str].fail(
                typecheck_paths.error or "type checker path conformance failed"
            )
        sources_result = cls._sync_uv_sources(
            source,
            link_mode=uv_link_mode or toolchain.uv_link_mode,
            exclude_newer=uv_exclude_newer or toolchain.uv_exclude_newer,
            exclude_newer_packages=toolchain.dependency_cooldown_exclusions,
            exclude_newer_overrides=toolchain.dependency_cooldown_overrides,
            exclude_dependencies=uv_exclude_dependencies,
        )
        if sources_result.failure:
            return r[str].fail(sources_result.error or "uv source conformance failed")
        rendered = u.Cli.toml_dumps(source)
        if u.Cli.toml_parse_text(rendered) is None:
            return r[str].fail("canonical pyproject rendering produced invalid TOML")
        return r[str].ok(rendered)

    @classmethod
    def pyproject_dependencies_conform(
        cls,
        pyproject_content: str,
        *,
        providers: t.SequenceOf[m.Infra.ProviderSpec],
        workspace: p.Infra.WorkspaceSpec,
    ) -> p.Result[str]:
        """Conform internal requirements for the current repository only."""
        source = u.Cli.toml_parse_text(pyproject_content)
        if source is None:
            return r[str].fail("pyproject content is not valid TOML")
        project = u.Cli.toml_table_child(source, c.Infra.PROJECT)
        if project is None:
            return r[str].fail("pyproject content must define [project]")
        project_name_raw = u.Cli.toml_value(project, c.Infra.NAME)
        if not isinstance(project_name_raw, str) or not project_name_raw.strip():
            return r[str].fail("[project].name must be a non-empty string")
        normalized = cls._normalize_requirements(
            source, providers=providers, workspace=workspace, canonicalize_all=False
        )
        if normalized.failure:
            return r[str].fail(normalized.error or "dependency normalization failed")
        sources_result = cls._sync_uv_sources(source, manage_repository_policy=False)
        if sources_result.failure:
            return r[str].fail(sources_result.error or "uv source conformance failed")
        rendered = u.Cli.toml_dumps(source)
        if u.Cli.toml_parse_text(rendered) is None:
            return r[str].fail("dependency conformance produced invalid TOML")
        return r[str].ok(rendered)

    @classmethod
    def _normalize_requirements(
        cls,
        document: t.Cli.TomlDocument,
        *,
        providers: t.SequenceOf[m.Infra.ProviderSpec],
        workspace: p.Infra.WorkspaceSpec,
        canonicalize_all: bool,
    ) -> p.Result[bool]:
        """Render internal requirements from the declared provider contract."""
        available = (workspace.repository,)
        project = u.Cli.toml_ensure_table(document, c.Infra.PROJECT)
        normalized = cls._normalize_requirement_field(
            project,
            c.Infra.DEPENDENCIES,
            repositories=available,
            providers=providers,
            canonicalize_all=canonicalize_all,
        )
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
                group_result = cls._normalize_requirement_field(
                    section,
                    group_name,
                    repositories=available,
                    providers=providers,
                    canonicalize_all=canonicalize_all,
                )
                if group_result.failure:
                    return group_result
        return r[bool].ok(True)

    @classmethod
    def _normalize_requirement_field(
        cls,
        container: t.Cli.TomlDocument | t.Cli.TomlTable,
        key: str,
        *,
        repositories: t.SequenceOf[p.Infra.RepositoryRef],
        providers: t.SequenceOf[m.Infra.ProviderSpec],
        canonicalize_all: bool,
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
        normalized_items: t.MutableSequenceOf[str] = []
        for item in items:
            normalized = cls._canonical_requirement(
                item, repositories=repositories, providers=providers
            )
            if normalized.failure:
                return r[bool].fail(
                    normalized.error or f"normalize dependency group {key} failed"
                )
            normalized_items.append(normalized.value)
        canonical = tuple(dict.fromkeys(normalized_items))
        if canonicalize_all:

            def requirement_key(requirement: str) -> tuple[str, str]:
                return (
                    FlextInfraUtilitiesDependencies.dep_name(requirement) or "",
                    requirement,
                )

            canonical = tuple(sorted(canonical, key=requirement_key))
        u.Cli.toml_sync_string_list(container, key, canonical)
        return r[bool].ok(True)

    @classmethod
    def _canonical_requirement(
        cls,
        requirement: str,
        *,
        repositories: t.SequenceOf[p.Infra.RepositoryRef],
        providers: t.SequenceOf[m.Infra.ProviderSpec],
    ) -> p.Result[str]:
        """Render one internal requirement from its provider-owned reference."""
        dependency_name = FlextInfraUtilitiesDependencies.dep_name(requirement)
        if dependency_name is None or not dependency_name.startswith("flext-"):
            return r[str].ok(requirement.strip())
        requirement_part, separator, marker = requirement.partition(";")
        head_match = c.Infra.PEP621_REQUIREMENT_HEAD_RE.match(requirement_part.strip())
        if head_match is None:
            return r[str].fail(f"invalid internal requirement: {requirement}")
        head = head_match.group("head").strip()
        marker_text = marker.strip()
        reference_result = cls._repository_reference(
            dependency_name, repositories=repositories, providers=providers
        )
        if reference_result.failure:
            return r[str].fail(
                reference_result.error
                or f"repository resolution failed: {dependency_name}"
            )
        reference = reference_result.value
        provider = FlextInfraUtilitiesRepository.repository_provider(
            reference, providers
        )
        if provider.failure:
            return r[str].fail(
                provider.error or "repository provider resolution failed"
            )
        git_url = cls._git_requirement_url(reference.url)
        if git_url.failure:
            return r[str].fail(git_url.error or "repository URL validation failed")
        canonical = f"{head} @ {git_url.value}@{provider.value.branch}"
        return r[str].ok(
            f"{canonical}; {marker_text}" if separator and marker_text else canonical
        )

    @staticmethod
    def _repository_reference(
        distribution: str,
        *,
        repositories: t.SequenceOf[p.Infra.RepositoryRef],
        providers: t.SequenceOf[m.Infra.ProviderSpec],
    ) -> p.Result[p.Infra.RepositoryRef]:
        """Return one unambiguous reference for a distribution.

        A distribution the workspace does not declare is still resolvable: its
        canonical source is the provider contract plus its own name. That is
        derived from generic policy, never from a catalog of projects that
        flext-infra is forbidden to own.
        """
        matches = tuple(
            repository
            for repository in repositories
            if repository.distribution == distribution
        )
        if not matches:
            return r.ok(
                FlextInfraUtilitiesRepository.derived_repository_ref(
                    distribution, provider=providers[0]
                )
            )
        reference = matches[0]
        if any(
            item.url != reference.url or item.provider != reference.provider
            for item in matches[1:]
        ):
            return r.fail(
                f"repository catalog conflicts for distribution: {distribution}"
            )
        return r.ok(reference)

    @staticmethod
    def _git_requirement_url(url: str) -> p.Result[str]:
        """Render the configured HTTPS clone URL as a PEP 508 Git URL."""
        if not url.startswith("https://"):
            return r[str].fail(
                f"repository URL must use the configured HTTPS transport: {url}"
            )
        return r[str].ok(f"git+{url}")

    @classmethod
    def _sync_dependency_groups(
        cls,
        document: t.Cli.TomlDocument,
        *,
        project_name: str,
        required_dev_dependencies: t.StrSequence,
    ) -> None:
        """Migrate optional dev dependencies and normalize declared groups."""
        project = u.Cli.toml_ensure_table(document, c.Infra.PROJECT)
        groups = u.Cli.toml_ensure_table(document, c.Infra.DEPENDENCY_GROUPS)
        optional = u.Cli.toml_table_child(project, c.Infra.OPTIONAL_DEPENDENCIES)
        optional_dev: t.StrSequence = ()
        if optional is not None:
            optional_dev = u.Cli.toml_as_string_list(
                u.Cli.toml_value(optional, str(c.Infra.DEV))
            )
        # SSOT required floors win over existing same-name pins: dedupe_specs
        # keeps the first occurrence, so toolchain floors must lead the merge.
        # Otherwise stale member pins (e.g. rumdl>=0.2.46) block exclude-newer.
        required_dev = tuple(
            requirement
            for requirement in required_dev_dependencies
            if FlextInfraUtilitiesDependencies.dep_name(requirement) != project_name
        )
        dev = [
            *required_dev,
            *u.Cli.toml_as_string_list(u.Cli.toml_value(groups, str(c.Infra.DEV))),
            *optional_dev,
        ]
        if dev:
            u.Cli.toml_sync_string_list(
                groups,
                str(c.Infra.DEV),
                FlextInfraUtilitiesDependencies.dedupe_specs(tuple(dev)),
            )
        else:
            u.Cli.toml_remove_key_if_present(groups, str(c.Infra.DEV))

        codegen = u.Cli.toml_as_string_list(u.Cli.toml_value(groups, "codegen"))
        if codegen:
            u.Cli.toml_sync_string_list(
                groups,
                "codegen",
                FlextInfraUtilitiesDependencies.dedupe_specs(tuple(codegen)),
            )
        else:
            u.Cli.toml_remove_key_if_present(groups, "codegen")
        if optional is not None:
            u.Cli.toml_remove_key_if_present(optional, str(c.Infra.DEV))
            if not tuple(optional):
                u.Cli.toml_remove_key_if_present(project, c.Infra.OPTIONAL_DEPENDENCIES)

    @staticmethod
    def _sync_project_version(
        project: t.Cli.TomlTable, *, workspace: p.Infra.WorkspaceSpec
    ) -> p.Result[bool]:
        """Keep the canonical PEP 621 version in the typed project projection."""
        mutated = u.Cli.toml_sync_value(
            project, c.Infra.VERSION, workspace.project.version
        )
        return r[bool].ok(mutated)

    @staticmethod
    def _remove_legacy_tooling(document: t.Cli.TomlDocument) -> None:
        """Delete legacy packaging owners superseded by canonical conformance.

        The ``[tool.flext]`` table is preserved as the project's explicit FLEXT
        management declaration. Repository topology never reads this table.
        """
        tool = u.Cli.toml_table_child(document, c.Infra.TOOL)
        if tool is None:
            return
        u.Cli.toml_remove_key_if_present(tool, c.Infra.POETRY)

    @staticmethod
    def _sync_typecheck_paths(document: t.Cli.TomlDocument) -> p.Result[bool]:
        """Remove checkout-absolute type checker interpreter pins.

        Search paths belong to FlextInfraExtraPathsManager. Top-level
        ``venv`` / ``venvPath`` belong to deps modernize (root vs child
        runtime). Conform must not strip those or gen oscillates.
        """
        tool = u.Cli.toml_table_child(document, c.Infra.TOOL)
        if tool is None:
            return r[bool].ok(True)
        pyrefly = u.Cli.toml_table_child(tool, c.Infra.PYREFLY)
        if pyrefly is not None:
            u.Cli.toml_remove_key_if_present(pyrefly, "python-interpreter-path")

        pyright = u.Cli.toml_table_child(tool, c.Infra.PYRIGHT)
        if pyright is None:
            return r[bool].ok(True)

        # venv / venvPath are owned by deps modernize (workspace vs child
        # runtime). Conform only strips checkout-absolute interpreter pins.
        interpreter_keys = ("pythonPath", "pythonInterpreterPath")
        for key in interpreter_keys:
            u.Cli.toml_remove_key_if_present(pyright, key)
        raw_environments = u.Cli.json_as_sequence(
            u.Cli.toml_value(pyright, "executionEnvironments")
        )
        normalized_environments: t.JsonValueList = []
        for index, environment in enumerate(raw_environments):
            if not isinstance(environment, Mapping):
                return r[bool].fail(
                    f"tool.pyright.executionEnvironments[{index}] must be a mapping"
                )
            mapping = t.Cli.JSON_MAPPING_ADAPTER.validate_python(environment)
            normalized: t.JsonDict = dict(mapping)
            root = normalized.get("root")
            normalized[c.Infra.EXTRA_PATHS] = ["src"] if root == "src" else [".", "src"]
            for key in ("venv", "venvPath", "pythonPath", "pythonInterpreterPath"):
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
        manage_repository_policy: bool = True,
        link_mode: str | None = None,
        exclude_newer: str | None = None,
        exclude_newer_packages: t.StrSequence = (),
        exclude_newer_overrides: t.StrMapping = MappingProxyType({}),
        exclude_dependencies: t.SequenceOf[p.Model] = (),
    ) -> p.Result[bool]:
        """Keep repository-local uv policy and remove topology projections."""
        has_repository_policy = bool(
            link_mode
            or exclude_newer
            or exclude_newer_packages
            or exclude_newer_overrides
            or exclude_dependencies
        )
        tool = u.Cli.toml_table_child(document, c.Infra.TOOL)
        if tool is None:
            if not manage_repository_policy or not has_repository_policy:
                return r[bool].ok(True)
            tool = u.Cli.toml_ensure_table(document, c.Infra.TOOL)
        uv = u.Cli.toml_table_child(tool, "uv")
        if uv is None:
            if not manage_repository_policy or not has_repository_policy:
                return r[bool].ok(True)
            uv = u.Cli.toml_ensure_table(tool, "uv")
        u.Cli.toml_remove_key_if_present(uv, "required-version")
        existing_constraints = u.Cli.toml_as_string_list(
            u.Cli.toml_value(uv, "constraint-dependencies")
        )
        retained_constraints = tuple(
            requirement
            for requirement in existing_constraints
            if FlextInfraUtilitiesDependencies.dep_name(requirement) != "uv"
        )
        if retained_constraints:
            u.Cli.toml_sync_string_list(
                uv, "constraint-dependencies", retained_constraints
            )
        else:
            u.Cli.toml_remove_key_if_present(uv, "constraint-dependencies")
        if manage_repository_policy and link_mode is not None:
            u.Cli.toml_sync_value(uv, "link-mode", link_mode)
        if manage_repository_policy and exclude_newer is not None:
            u.Cli.toml_sync_value(uv, "exclude-newer", exclude_newer)
        # Two shapes share this uv key. A bare exemption is `false` (waive the
        # cooldown entirely, for a reviewed security floor). An override is a
        # timestamp, needed when the shared cutoff predates a floor the project
        # legitimately requires: uv then reports the requirement unsatisfiable
        # and names this key as the remedy, so switching the cooldown off is not
        # enough — the cutoff has to move to a specific instant. Overrides win
        # on collision, being the more specific declaration of the two.
        exclude_newer_payload: t.JsonDict = dict.fromkeys(
            sorted(exclude_newer_packages), False
        )
        exclude_newer_payload.update(sorted(exclude_newer_overrides.items()))
        if manage_repository_policy:
            if exclude_newer_payload:
                u.Cli.toml_sync_value(
                    uv, "exclude-newer-package", exclude_newer_payload
                )
            else:
                u.Cli.toml_remove_key_if_present(uv, "exclude-newer-package")
        # Project is a flext-infra routing key only; uv scoped form is
        # {package={name, version?}, dependencies=[...]} (uv settings docs).
        # Emit on every owning pyproject so standalone CI clones resolve;
        # do not gate on owns_uv_root_policy (that stripped member excludes).
        exclude_payload = list(
            t.Cli.JSON_LIST_ADAPTER.validate_python([
                {
                    key: value
                    for key, value in item.model_dump(
                        mode="json", exclude_none=True
                    ).items()
                    if key != "project"
                }
                for item in exclude_dependencies
            ])
        )
        if manage_repository_policy:
            if exclude_payload:
                u.Cli.toml_sync_value(uv, "exclude-dependencies", exclude_payload)
            else:
                u.Cli.toml_remove_key_if_present(uv, "exclude-dependencies")
        u.Cli.toml_remove_key_if_present(uv, "workspace")
        sources = u.Cli.toml_table_child(uv, "sources")
        if sources is None:
            if not tuple(uv):
                u.Cli.toml_remove_key_if_present(tool, "uv")
            return r[bool].ok(True)
        for source_name in tuple(sources):
            if source_name.startswith("flext-"):
                u.Cli.toml_remove_key_if_present(sources, source_name)
        if not tuple(sources):
            u.Cli.toml_remove_key_if_present(uv, "sources")
        if not tuple(uv):
            u.Cli.toml_remove_key_if_present(tool, "uv")
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraUtilitiesPyprojectConform"]
