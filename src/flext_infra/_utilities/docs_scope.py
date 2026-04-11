"""Docs scope helpers for FLEXT-only discovery and project classification."""

from __future__ import annotations

from collections.abc import Sequence
from fnmatch import fnmatch
from pathlib import Path

from flext_cli import u
from flext_infra import (
    FlextInfraUtilitiesIteration,
    FlextInfraUtilitiesTomlParse,
    c,
    m,
    r,
    t,
)


class FlextInfraUtilitiesDocsScope:
    """Utility helpers for docs scope policy and project classification."""

    @staticmethod
    def resolve_projects(
        workspace_root: Path,
        names: Sequence[str],
    ) -> r[Sequence[m.Infra.ProjectInfo]]:
        """Resolve project names into canonical project descriptors."""
        discover_result = FlextInfraUtilitiesDocsScope.discover_projects(
            workspace_root,
        )
        if discover_result.is_failure:
            return r[Sequence[m.Infra.ProjectInfo]].fail(
                discover_result.error or "discovery failed",
            )
        projects = discover_result.value
        if not names:
            return r[Sequence[m.Infra.ProjectInfo]].ok(
                sorted(projects, key=lambda proj: proj.name),
            )
        by_name: dict[str, m.Infra.ProjectInfo] = {}
        for project in projects:
            by_name.setdefault(project.name, project)
            by_name.setdefault(project.path.name, project)
        missing = [name for name in names if name not in by_name]
        if missing:
            missing_text = ", ".join(sorted(missing))
            return r[Sequence[m.Infra.ProjectInfo]].fail(
                f"unknown projects: {missing_text}",
            )
        return r[Sequence[m.Infra.ProjectInfo]].ok(
            sorted((by_name[name] for name in names), key=lambda proj: proj.name),
        )

    @staticmethod
    def _project_name_from_payload(
        entry: Path,
        payload: t.Infra.ContainerDict,
    ) -> str:
        """Return the declared project name, falling back to the directory name."""
        project_section = payload.get("project")
        if isinstance(project_section, dict):
            raw_name = project_section.get("name")
            if isinstance(raw_name, str) and raw_name.strip():
                return raw_name.strip()
        return entry.name

    @staticmethod
    def _workspace_member_name_set(workspace_root: Path) -> t.Infra.StrSet:
        """Return configured uv workspace members for the current workspace root."""
        return set(FlextInfraUtilitiesIteration.workspace_member_names(workspace_root))

    @staticmethod
    def _declares_flext_core_dependency(pyproject: Path) -> bool:
        """Return whether one pyproject declares a direct dependency on flext-core."""
        document_result = u.Cli.toml_read_document(pyproject)
        if document_result.is_failure:
            return False
        dependency_names: t.Infra.StrSet = set(
            FlextInfraUtilitiesTomlParse.declared_dependency_names(
                document_result.value,
            )
        )
        return c.Infra.Packages.CORE in dependency_names

    @staticmethod
    def _project_info_for_entry(
        entry: Path,
        *,
        workspace_members: t.Infra.StrSet,
    ) -> m.Infra.ProjectInfo | None:
        """Build one canonical project descriptor when a child qualifies."""
        pyproject = entry / c.Infra.Files.PYPROJECT_FILENAME
        if not pyproject.is_file():
            return None
        is_workspace_member = entry.name in workspace_members
        if (not is_workspace_member) and (
            not FlextInfraUtilitiesDocsScope._declares_flext_core_dependency(pyproject)
        ):
            return None
        payload = FlextInfraUtilitiesDocsScope.pyproject_payload(entry)
        docs_meta = FlextInfraUtilitiesDocsScope.docs_meta_from_payload(payload)
        project_name = FlextInfraUtilitiesDocsScope._project_name_from_payload(
            entry,
            payload,
        )
        enabled = docs_meta.get("enabled", True)
        if isinstance(enabled, bool) and not enabled:
            return None
        workspace_role = (
            c.Infra.WorkspaceProjectRole.WORKSPACE_MEMBER
            if is_workspace_member
            else c.Infra.WorkspaceProjectRole.ATTACHED
        )
        return m.Infra.ProjectInfo.model_construct(
            path=entry,
            name=project_name,
            stack="python/flext",
            has_tests=(entry / c.Infra.Directories.TESTS).is_dir(),
            has_src=(entry / c.Infra.Paths.DEFAULT_SRC_DIR).is_dir(),
            project_class=(
                FlextInfraUtilitiesDocsScope.classify_project_from_meta(
                    project_name,
                    docs_meta,
                )
            ),
            package_name=(
                FlextInfraUtilitiesDocsScope.package_name_from_payload(
                    entry,
                    payload,
                    docs_meta,
                )
            ),
            workspace_role=workspace_role,
        )

    @staticmethod
    def config_path(workspace_root: Path) -> Path:
        """Return the minimal docs policy config path."""
        return workspace_root / c.Infra.Directories.DOCS / c.Infra.DOCS_CONFIG_FILENAME

    @staticmethod
    def pyproject_payload(project_root: Path) -> t.Infra.ContainerDict:
        """Return a project's ``pyproject.toml`` payload as a plain mapping."""
        pyproject = project_root / c.Infra.Files.PYPROJECT_FILENAME
        if not pyproject.exists():
            return {}
        result = u.Cli.toml_read_json(pyproject)
        return result.value if result.is_success else {}

    @staticmethod
    def load_config(
        workspace_root: Path,
    ) -> t.Infra.ContainerDict:
        """Load the minimal docs policy config if present."""
        path = FlextInfraUtilitiesDocsScope.config_path(workspace_root)
        if not path.exists():
            return {}
        result = u.Cli.json_read(path)
        return result.value if result.is_success else {}

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
    def project_docs_meta(project_root: Path) -> t.Infra.ContainerDict:
        """Return optional ``tool.flext.docs`` metadata from a project pyproject."""
        payload = FlextInfraUtilitiesDocsScope.pyproject_payload(project_root)
        tool = payload.get(c.Infra.TOOL)
        if not isinstance(tool, dict):
            return {}
        flext = tool.get("flext")
        if not isinstance(flext, dict):
            return {}
        docs = flext.get("docs")
        return docs if isinstance(docs, dict) else {}

    @staticmethod
    def docs_meta_list(
        project_root: Path,
        key: str,
    ) -> Sequence[str]:
        """Return one normalized string-list value from ``tool.flext.docs``."""
        docs_meta = FlextInfraUtilitiesDocsScope.project_docs_meta(project_root)
        raw = docs_meta.get(key)
        if not isinstance(raw, list):
            return []
        return [str(item).strip() for item in raw if str(item).strip()]

    @staticmethod
    def is_excluded_doc_path(
        project_root: Path,
        relative_path: Path,
    ) -> bool:
        """Return whether a relative docs path is excluded by ``tool.flext.docs``."""
        candidate = relative_path.as_posix()
        for pattern in FlextInfraUtilitiesDocsScope.docs_meta_list(
            project_root,
            "exclude_docs",
        ):
            if fnmatch(candidate, pattern):
                return True
        return False

    @staticmethod
    def is_governed_project(
        project_name: str,
        workspace_root: Path,
    ) -> bool:
        """Return whether a project belongs to the governed FLEXT docs scope."""
        project_root = workspace_root / project_name
        docs_meta = FlextInfraUtilitiesDocsScope.project_docs_meta(project_root)
        enabled = docs_meta.get("enabled", True)
        is_enabled = bool(enabled) if isinstance(enabled, bool) else True
        return (
            project_name.startswith("flext-")
            and project_name
            not in FlextInfraUtilitiesDocsScope.excluded_roots(workspace_root)
            and is_enabled
        )

    @staticmethod
    def docs_meta_from_payload(
        payload: t.Infra.ContainerDict,
    ) -> t.Infra.ContainerDict:
        """Extract ``tool.flext.docs`` metadata from an already-parsed payload."""
        tool = payload.get(c.Infra.TOOL)
        if not isinstance(tool, dict):
            return {}
        flext = tool.get("flext")
        if not isinstance(flext, dict):
            return {}
        docs = flext.get("docs")
        return docs if isinstance(docs, dict) else {}

    @staticmethod
    def classify_project_from_meta(
        project_name: str,
        docs_meta: t.Infra.ContainerDict,
    ) -> str:
        """Classify a project using pre-loaded docs metadata (avoids re-parsing)."""
        configured = docs_meta.get("project_class")
        if isinstance(configured, str) and configured.strip():
            return configured.strip()
        if project_name.startswith(("flext-tap-", "flext-target-", "flext-dbt-")):
            return "integration"
        if project_name == "flext-infra":
            return "infra"
        if project_name == "flext-tests":
            return "test"
        return "domain"

    @staticmethod
    def package_name_from_payload(
        project_root: Path,
        payload: t.Infra.ContainerDict,
        docs_meta: t.Infra.ContainerDict,
    ) -> str:
        """Return the primary package name using pre-loaded payload (avoids re-parsing)."""
        configured = docs_meta.get("package_name")
        if isinstance(configured, str) and configured.strip():
            return configured.strip()
        tool = payload.get(c.Infra.TOOL)
        if isinstance(tool, dict):
            hatch = tool.get("hatch")
            if isinstance(hatch, dict):
                build = hatch.get("build")
                if isinstance(build, dict):
                    targets = build.get("targets")
                    if isinstance(targets, dict):
                        wheel = targets.get("wheel")
                        if isinstance(wheel, dict):
                            packages = wheel.get("packages")
                            if isinstance(packages, list):
                                for item in packages:
                                    package_path = Path(str(item).strip())
                                    if package_path.parts:
                                        return package_path.parts[-1]
        src_dir = project_root / c.Infra.Paths.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return ""
        for child in sorted(src_dir.iterdir()):
            if child.is_dir() and (child / c.Infra.Files.INIT_PY).is_file():
                return child.name
        return ""

    @staticmethod
    def package_name(project_root: Path) -> str:
        """Return the primary Python package name for a project."""
        payload = FlextInfraUtilitiesDocsScope.pyproject_payload(project_root)
        docs_meta = FlextInfraUtilitiesDocsScope.docs_meta_from_payload(payload)
        return FlextInfraUtilitiesDocsScope.package_name_from_payload(
            project_root,
            payload,
            docs_meta,
        )

    @staticmethod
    def discover_projects(
        workspace_root: Path,
    ) -> r[Sequence[m.Infra.ProjectInfo]]:
        """Discover workspace projects that participate in the docs scope."""
        if not workspace_root.exists() or not workspace_root.is_dir():
            return r[Sequence[m.Infra.ProjectInfo]].fail(
                f"discovery failed: invalid workspace root {workspace_root}",
            )
        excluded = FlextInfraUtilitiesDocsScope.excluded_roots(workspace_root)
        workspace_members = FlextInfraUtilitiesDocsScope._workspace_member_name_set(
            workspace_root,
        )
        root_project: m.Infra.ProjectInfo | None = None
        if workspace_root.name not in excluded:
            root_project = FlextInfraUtilitiesDocsScope._project_info_for_entry(
                workspace_root,
                workspace_members=workspace_members,
            )
        projects: list[m.Infra.ProjectInfo] = []
        try:
            for entry in sorted(workspace_root.iterdir(), key=lambda item: item.name):
                if (
                    not entry.is_dir()
                    or entry.name.startswith(".")
                    or entry.name == "cmd"
                    or entry.name in excluded
                ):
                    continue
                project_info = FlextInfraUtilitiesDocsScope._project_info_for_entry(
                    entry,
                    workspace_members=workspace_members,
                )
                if project_info is None:
                    continue
                projects.append(project_info)
        except OSError as exc:
            return r[Sequence[m.Infra.ProjectInfo]].fail(
                f"discovery failed: {exc}",
            )
        if not projects and root_project is not None:
            return r[Sequence[m.Infra.ProjectInfo]].ok([root_project])
        return r[Sequence[m.Infra.ProjectInfo]].ok(projects)

    @staticmethod
    def required_project_files() -> Sequence[str]:
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


__all__ = ["FlextInfraUtilitiesDocsScope"]
