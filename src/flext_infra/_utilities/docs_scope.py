"""Docs scope helpers for FLEXT-only discovery and project classification."""

from __future__ import annotations

import operator
from fnmatch import fnmatch
from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import FlextCliUtilities as u
from flext_core.result import FlextResult as r
from flext_infra._models.workspace import FlextInfraModelsWorkspace as mw
from flext_infra._utilities.dependencies import FlextInfraUtilitiesDependencies
from flext_infra._utilities.git import FlextInfraUtilitiesGit
from flext_infra._utilities.project_discovery import FlextInfraUtilitiesProjectDiscovery
from flext_infra._utilities.pyproject import FlextInfraUtilitiesPyproject
from flext_infra.constants import FlextInfraConstants as c
from flext_infra.typings import FlextInfraTypes as t

if TYPE_CHECKING:
    from flext_infra import FlextInfraProtocols as p


class FlextInfraUtilitiesDocsScope:
    """Utility helpers for docs scope policy and project classification."""

    @staticmethod
    def _absolute_lexical(path: Path) -> Path:
        """Return an absolute lexical path without dereferencing aliases."""
        if ".." in path.parts:
            msg = f"docs path cannot contain parent traversal: {path}"
            raise ValueError(msg)
        return path if path.is_absolute() else path.absolute()

    @staticmethod
    def _physical_directory_exists(path: Path) -> bool:
        """Return presence only after descriptor-authenticated traversal."""
        planned = u.Cli.atomic_plan_directory_chain(path)
        if planned.failure:
            raise ValueError(planned.error or f"docs directory is unsafe: {path}")
        return not planned.value.directories

    @staticmethod
    def _physical_file_exists(path: Path) -> bool:
        """Return file presence only after descriptor-authenticated inspection."""
        state = u.Cli.atomic_read_binary_file_state(path, required=False)
        if state.failure:
            raise ValueError(state.error or f"docs file is unsafe: {path}")
        return state.value.content is not None

    @staticmethod
    def _project_state(project_root: Path) -> mw.ProjectPyprojectState:
        """Return freshly parsed pyproject state for one project root.

        When the pyproject is absent or empty, the returned state carries
        empty ``project_name``/``package_name`` (legitimate "not a project"
        signal). When the pyproject is present but missing ``[project]`` or
        ``[project].name``, :meth:`project_name_from_payload` raises — no
        silent fallback to directory-name.
        """
        root = FlextInfraUtilitiesDocsScope._absolute_lexical(project_root)
        pyproject_path = root / c.Infra.PYPROJECT_FILENAME
        snapshot = u.Cli.atomic_read_binary_file_state(pyproject_path, required=False)
        if snapshot.failure:
            raise ValueError(
                snapshot.error or f"cannot inspect docs pyproject: {pyproject_path}"
            )
        if snapshot.value.content is None:
            payload: t.JsonMapping = {}
        else:
            try:
                source = snapshot.value.content.decode(c.Cli.ENCODING_DEFAULT)
            except UnicodeDecodeError as exc:
                msg = f"docs pyproject is not valid UTF-8: {pyproject_path}"
                raise ValueError(msg) from exc
            parsed = u.Cli.toml_mapping_from_text(source)
            if parsed is None:
                msg = f"docs pyproject TOML is invalid: {pyproject_path}"
                raise ValueError(msg)
            validated = FlextInfraUtilitiesPyproject.validate_infra_payload(parsed)
            if validated is None:
                msg = f"docs pyproject payload is invalid: {pyproject_path}"
                raise ValueError(msg)
            payload = validated
        docs_meta = FlextInfraUtilitiesDocsScope.docs_meta_from_payload(payload)
        dependency_names = tuple(
            FlextInfraUtilitiesDependencies.declared_dependency_names_from_payload(
                payload
            )
        )
        if not payload:
            empty_state: mw.ProjectPyprojectState = (
                mw.ProjectPyprojectState.model_construct(
                    project_root=root,
                    pyproject_path=pyproject_path,
                    payload=payload,
                    docs_meta=docs_meta,
                    project_name="",
                    package_name="",
                    dependency_names=dependency_names,
                )
            )
            return empty_state
        state: mw.ProjectPyprojectState = mw.ProjectPyprojectState.model_construct(
            project_root=root,
            pyproject_path=pyproject_path,
            payload=payload,
            docs_meta=docs_meta,
            project_name=FlextInfraUtilitiesDocsScope.project_name_from_payload(
                root, payload
            ),
            package_name=FlextInfraUtilitiesDocsScope.package_name_from_payload(
                root, payload, docs_meta
            ),
            dependency_names=dependency_names,
        )
        return state

    @staticmethod
    def project_state(project_root: Path) -> mw.ProjectPyprojectState:
        """Return one fresh state bound to authenticated pyproject bytes."""
        return FlextInfraUtilitiesDocsScope._project_state(project_root)

    @staticmethod
    def docs_workspace_roots(
        workspace_root: Path, extra_roots: t.SequenceOf[Path] = ()
    ) -> p.Result[tuple[Path, ...]]:
        """Return existing physical roots from one stable workspace topology."""
        try:
            return FlextInfraUtilitiesDocsScope._docs_workspace_roots(
                workspace_root, extra_roots
            )
        except (OSError, TypeError, ValueError) as exc:
            return r[tuple[Path, ...]].fail_op("docs workspace discovery", exc)

    @staticmethod
    def _docs_workspace_roots(
        workspace_root: Path, extra_roots: t.SequenceOf[Path]
    ) -> p.Result[tuple[Path, ...]]:
        """Discover roots while the public boundary owns exception conversion."""
        root = FlextInfraUtilitiesDocsScope._absolute_lexical(workspace_root)
        if not FlextInfraUtilitiesDocsScope._physical_directory_exists(root):
            return r[tuple[Path, ...]].fail(f"docs workspace root is missing: {root}")
        manifest_path = root / c.Infra.GITMODULES
        manifest_before = u.Cli.atomic_read_binary_file_state(
            manifest_path, required=False
        )
        if manifest_before.failure:
            return r[tuple[Path, ...]].from_failure(manifest_before)
        declared = FlextInfraUtilitiesGit.git_declared_submodule_paths(root)
        if declared.failure:
            return r[tuple[Path, ...]].from_failure(declared)
        manifest_after = u.Cli.atomic_read_binary_file_state(
            manifest_path, required=False
        )
        if manifest_after.failure:
            return r[tuple[Path, ...]].from_failure(manifest_after)
        if manifest_after.value != manifest_before.value:
            return r[tuple[Path, ...]].fail(
                f"docs workspace topology changed during discovery: {manifest_path}"
            )
        candidates = [root]
        for declared_path in declared.value:
            selector = Path(declared_path)
            if selector.is_absolute() or ".." in selector.parts:
                return r[tuple[Path, ...]].fail(
                    f"invalid docs workspace member path: {selector}"
                )
            candidates.append(root / selector)
        for candidate in extra_roots:
            lexical = FlextInfraUtilitiesDocsScope._absolute_lexical(candidate)
            if not lexical.is_relative_to(root):
                return r[tuple[Path, ...]].fail(
                    f"docs source root escapes workspace {root}: {lexical}"
                )
            candidates.append(lexical)
        roots = [
            candidate
            for candidate in dict.fromkeys(candidates)
            if FlextInfraUtilitiesDocsScope._physical_directory_exists(candidate)
        ]
        return r[tuple[Path, ...]].ok(tuple(roots))

    @staticmethod
    def resolve_projects(
        workspace_root: Path, names: t.StrSequence
    ) -> p.Result[t.SequenceOf[mw.ProjectInfo]]:
        """Resolve project names through repository-local topology only."""
        discover_result = FlextInfraUtilitiesDocsScope.discover_projects(workspace_root)
        if discover_result.failure:
            return r[t.SequenceOf[mw.ProjectInfo]].fail(
                discover_result.error or "discovery failed"
            )
        projects = list(discover_result.value)
        resolved_workspace_root = FlextInfraUtilitiesDocsScope._absolute_lexical(
            workspace_root
        )
        if all(project.path != resolved_workspace_root for project in projects):
            root_project = FlextInfraUtilitiesDocsScope._project_info_for_entry(
                resolved_workspace_root,
                workspace_subprojects=FlextInfraUtilitiesDocsScope._workspace_subproject_path_set(
                    resolved_workspace_root
                ),
            )
            if root_project is not None:
                projects.append(root_project)
        if not names:
            return r[t.SequenceOf[mw.ProjectInfo]].ok(
                sorted(projects, key=operator.attrgetter("name"))
            )
        by_name: dict[str, mw.ProjectInfo] = {}
        for project in projects:
            by_name.setdefault(project.name, project)
            by_name.setdefault(project.path.name, project)
            project_path = project.path
            if project_path == resolved_workspace_root:
                by_name.setdefault(".", project)
            elif project_path.is_relative_to(resolved_workspace_root):
                by_name.setdefault(
                    project_path.relative_to(resolved_workspace_root).as_posix(),
                    project,
                )
        missing = [name for name in names if name not in by_name]
        if missing:
            missing_text = ", ".join(sorted(missing))
            return r[t.SequenceOf[mw.ProjectInfo]].fail(
                f"unknown projects: {missing_text}"
            )
        return r[t.SequenceOf[mw.ProjectInfo]].ok(
            sorted((by_name[name] for name in names), key=operator.attrgetter("name"))
        )

    @staticmethod
    def project_name_from_payload(entry: Path, payload: t.JsonMapping) -> str:
        """Return the declared project name from ``[project].name``."""
        return FlextInfraUtilitiesPyproject.project_name_from_payload(entry, payload)

    @staticmethod
    def _workspace_subproject_path_set(workspace_root: Path) -> frozenset[Path]:
        """Return lexical subprojects freshly read from this root's manifest."""
        resolved_root = FlextInfraUtilitiesDocsScope._absolute_lexical(workspace_root)
        declared = FlextInfraUtilitiesGit.git_declared_submodule_paths(resolved_root)
        if declared.failure:
            raise ValueError(declared.error or f"invalid workspace: {resolved_root}")
        return frozenset(resolved_root / path for path in declared.value)

    @staticmethod
    def _project_info_for_entry(
        entry: Path, *, workspace_subprojects: frozenset[Path]
    ) -> mw.ProjectInfo | None:
        """Build one canonical project descriptor for one discovered project root."""
        entry = FlextInfraUtilitiesDocsScope._absolute_lexical(entry)
        project_state = FlextInfraUtilitiesDocsScope.project_state(entry)
        project_section = project_state.payload.get("project")
        project_name = (
            project_section.get("name") if isinstance(project_section, dict) else None
        )
        if (
            not isinstance(project_section, dict)
            or not isinstance(project_name, str)
            or not project_name.strip()
        ):
            return None
        is_workspace_subproject = entry in workspace_subprojects
        enabled = project_state.docs_meta.get("enabled", True)
        if isinstance(enabled, bool) and not enabled:
            return None
        has_src = FlextInfraUtilitiesDocsScope._physical_directory_exists(
            entry / c.Infra.DEFAULT_SRC_DIR
        )
        has_tests = FlextInfraUtilitiesDocsScope._physical_directory_exists(
            entry / c.Infra.DIR_TESTS
        )
        has_deps = bool(project_section.get("dependencies"))
        if (
            not is_workspace_subproject
            and not has_src
            and not has_tests
            and not has_deps
        ):
            return None
        # Topology is proven by the checkout itself. Declared-subproject is
        # the aggregate's relationship to this path, not the repository's own
        # workspace/standalone classification.
        make_profile = (
            c.Infra.MakeProfile.WORKSPACE
            if FlextInfraUtilitiesDocsScope._physical_file_exists(
                entry / c.Infra.GITMODULES
            )
            else c.Infra.MakeProfile.STANDALONE
        )
        project_info: mw.ProjectInfo = mw.ProjectInfo.model_construct(
            path=entry,
            name=project_state.project_name,
            stack="python/flext",
            has_tests=has_tests,
            has_src=has_src,
            project_class=(
                FlextInfraUtilitiesDocsScope.classify_project_from_meta(
                    project_state.project_name, project_state.docs_meta
                )
            ),
            package_name=project_state.package_name,
            make_profile=make_profile,
            declared_subproject=is_workspace_subproject,
        )
        return project_info

    @staticmethod
    def config_path(workspace_root: Path) -> Path:
        """Return the minimal docs policy settings path."""
        dir_docs: str = c.Infra.DIR_DOCS
        docs_config: str = c.Infra.DOCS_CONFIG_FILENAME
        return workspace_root / dir_docs / docs_config

    @staticmethod
    def project_payload(project_root: Path) -> t.JsonMapping:
        """Return a project's ``pyproject.toml`` payload as a plain mapping."""
        return FlextInfraUtilitiesDocsScope.project_state(project_root).payload

    @staticmethod
    def load_config(workspace_root: Path) -> t.JsonMapping:
        """Load the minimal docs policy settings if present."""
        path = FlextInfraUtilitiesDocsScope.config_path(workspace_root)
        state = u.Cli.atomic_read_binary_file_state(path, required=False)
        if state.failure:
            raise ValueError(state.error or f"docs config is unsafe: {path}")
        if state.value.content is None:
            return {}
        parsed = u.Cli.json_loads(state.value.content)
        if parsed.failure:
            raise ValueError(parsed.error or f"docs config JSON is invalid: {path}")
        value = parsed.value
        if not isinstance(value, dict):
            msg = f"docs config root must be a mapping: {path}"
            raise TypeError(msg)
        validated = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(value)
        return dict(validated)

    @staticmethod
    def excluded_roots(workspace_root: Path) -> t.Infra.StrSet:
        """Return explicitly excluded root directories from docs scope."""
        payload = FlextInfraUtilitiesDocsScope.load_config(workspace_root)
        scope = payload.get("scope")
        if not isinstance(scope, dict):
            return set()
        excluded = scope.get("exclude_roots")
        if not isinstance(excluded, list):
            return set()
        return {str(item).strip() for item in excluded if str(item).strip()}

    @staticmethod
    def project_docs_meta(project_root: Path) -> t.JsonMapping:
        """Return optional ``tool.flext.docs`` metadata from a project pyproject."""
        return FlextInfraUtilitiesDocsScope.project_state(project_root).docs_meta

    @staticmethod
    def docs_meta_list(project_root: Path, key: str) -> t.StrSequence:
        """Return one normalized string-list value from ``tool.flext.docs``."""
        docs_meta = FlextInfraUtilitiesDocsScope.project_docs_meta(project_root)
        raw = docs_meta.get(key)
        if not isinstance(raw, list):
            return ()
        return [str(item).strip() for item in raw if str(item).strip()]

    @staticmethod
    def is_excluded_doc_path(project_root: Path, relative_path: Path) -> bool:
        """Return whether a relative docs path is excluded by ``tool.flext.docs``."""
        candidate = relative_path.as_posix()
        for pattern in FlextInfraUtilitiesDocsScope.docs_meta_list(
            project_root, "exclude_docs"
        ):
            if fnmatch(candidate, pattern):
                return True
        return False

    @staticmethod
    def is_governed_project(project_name: str, workspace_root: Path) -> bool:
        """Return whether a project belongs to the governed FLEXT docs scope."""
        project_root = workspace_root / project_name
        docs_meta = FlextInfraUtilitiesDocsScope.project_docs_meta(project_root)
        enabled = docs_meta.get("enabled", True)
        is_enabled = enabled if isinstance(enabled, bool) else True
        return (
            project_name.startswith(c.Infra.PKG_PREFIX_HYPHEN)
            and project_name
            not in FlextInfraUtilitiesDocsScope.excluded_roots(workspace_root)
            and is_enabled
        )

    @staticmethod
    def docs_meta_from_payload(payload: t.JsonMapping) -> t.JsonMapping:
        """Extract ``tool.flext.docs`` metadata from an already-parsed payload."""
        return FlextInfraUtilitiesPyproject.docs_meta_from_payload(payload)

    @staticmethod
    def classify_project_from_meta(project_name: str, docs_meta: t.JsonMapping) -> str:
        """Classify a project using pre-loaded docs metadata (avoids re-parsing).

        Project-prefix heuristics derive from ``c.Infra.INTEGRATION_CLASS_PREFIXES``
        (SSOT for integration project family) so adding a new family member
        requires editing only the canonical class-prefix tuple.
        """
        configured = docs_meta.get("project_class")
        if isinstance(configured, str) and configured.strip():
            return configured.strip()
        integration_prefixes = tuple(
            f"{c.Infra.PKG_PREFIX_HYPHEN}{prefix.removeprefix('Flext').lower()}-"
            for prefix in c.Infra.INTEGRATION_CLASS_PREFIXES
        )
        if project_name.startswith(integration_prefixes):
            return "integration"
        if project_name == f"{c.Infra.PKG_PREFIX_HYPHEN}infra":
            return "infra"
        if project_name == f"{c.Infra.PKG_PREFIX_HYPHEN}tests":
            return "test"
        return "domain"

    @staticmethod
    def package_name_from_payload(
        project_root: Path, payload: t.JsonMapping, docs_meta: t.JsonMapping
    ) -> str:
        """Return the primary package name using pre-loaded payload.

        Resolution order (no silent fallbacks for flext projects):
          1. Explicit ``[tool.flext.docs].package_name`` override.
          2. ``[tool.hatch.build.targets.wheel.packages]`` first entry.
          3. First ``src/<pkg>/__init__.py`` directory.
          4. Empty string for non-flext projects (roots).

        Raises ``ValueError`` only for flext- projects unable to resolve.
        """
        return FlextInfraUtilitiesPyproject.package_name_from_payload(
            project_root, payload, docs_meta
        )

    @staticmethod
    def project_package_name(project_root: Path) -> str:
        """Return the primary Python package name for a project."""
        return FlextInfraUtilitiesDocsScope.project_state(project_root).package_name

    @staticmethod
    def discover_projects(
        workspace_root: Path,
    ) -> p.Result[t.SequenceOf[mw.ProjectInfo]]:
        """Discover the root or projects declared by its own ``.gitmodules``."""
        roots = FlextInfraUtilitiesDocsScope.docs_workspace_roots(workspace_root)
        if roots.failure:
            return r[t.SequenceOf[mw.ProjectInfo]].from_failure(roots)
        workspace_root = roots.value[0]
        excluded = FlextInfraUtilitiesDocsScope.excluded_roots(workspace_root)
        workspace_subprojects = (
            FlextInfraUtilitiesDocsScope._workspace_subproject_path_set(workspace_root)
        )
        project_roots = FlextInfraUtilitiesProjectDiscovery.discover_project_candidates(
            workspace_root
        )
        root_project: mw.ProjectInfo | None = None
        projects: list[mw.ProjectInfo] = []
        for project_root in project_roots:
            if project_root.name == "cmd" or project_root.name in excluded:
                continue
            if (
                project_root == workspace_root
                and not FlextInfraUtilitiesDocsScope._physical_directory_exists(
                    project_root / c.Infra.DEFAULT_SRC_DIR
                )
            ):
                continue
            project_info = FlextInfraUtilitiesDocsScope._project_info_for_entry(
                project_root, workspace_subprojects=workspace_subprojects
            )
            if project_info is None:
                continue
            if project_root == workspace_root:
                root_project = project_info
                continue
            projects.append(project_info)
        if not projects and root_project is not None:
            return r[t.SequenceOf[mw.ProjectInfo]].ok([root_project])
        return r[t.SequenceOf[mw.ProjectInfo]].ok(projects)

    @staticmethod
    def required_project_files() -> t.StrSequence:
        """Return the required standard docs contract for FLEXT projects."""
        return [
            "README.md",
            "docs/index.md",
            "docs/guides/README.md",
            "docs/api-reference/README.md",
            "docs/api-reference/generated/overview.md",
            "docs/api-reference/generated/public-api.md",
            "docs/api-reference/generated/modules/index.md",
            "mkdocs.yml",
        ]


__all__: list[str] = ["FlextInfraUtilitiesDocsScope"]
