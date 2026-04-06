"""Docs scope helpers for FLEXT-only discovery and project classification."""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from fnmatch import fnmatch
from pathlib import Path

from flext_cli import u
from flext_infra import c, m, r, t


class FlextInfraUtilitiesDocsScope:
    """Utility helpers for docs scope policy and project classification."""

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
    def excluded_roots(workspace_root: Path) -> set[str]:
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
    def workspace_docs_meta(workspace_root: Path) -> t.Infra.ContainerDict:
        """Return optional root ``tool.flext.docs`` metadata."""
        return FlextInfraUtilitiesDocsScope.project_docs_meta(workspace_root)

    @staticmethod
    def docs_meta_list(
        project_root: Path,
        key: str,
    ) -> t.StrSequence:
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
    def classify_project(
        project_name: str,
        project_root: Path,
    ) -> str:
        """Classify a governed FLEXT project from its canonical naming pattern."""
        docs_meta = FlextInfraUtilitiesDocsScope.project_docs_meta(project_root)
        return FlextInfraUtilitiesDocsScope.classify_project_from_meta(
            project_name,
            docs_meta,
        )

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
                                    if not package_path.parts:
                                        continue
                                    if (
                                        package_path.parts[0]
                                        != c.Infra.Paths.DEFAULT_SRC_DIR
                                    ):
                                        continue
                                    return package_path.name
        project = payload.get(c.Infra.PROJECT)
        if isinstance(project, dict):
            project_name = project.get("name")
            if isinstance(project_name, str) and project_name.strip():
                guessed = project_name.strip().replace("-", "_")
                guessed_root = (
                    project_root
                    / c.Infra.Paths.DEFAULT_SRC_DIR
                    / guessed
                    / c.Infra.Files.INIT_PY
                )
                if guessed_root.is_file():
                    return guessed
        src_dir = project_root / c.Infra.Paths.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return ""
        for child in sorted(src_dir.iterdir(), key=lambda item: item.name):
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
        projects: MutableSequence[m.Infra.ProjectInfo] = []
        try:
            for entry in sorted(workspace_root.iterdir(), key=lambda item: item.name):
                if (
                    not entry.is_dir()
                    or entry.name.startswith(".")
                    or entry.name == "cmd"
                    or entry.name in excluded
                ):
                    continue
                pyproject = entry / c.Infra.Files.PYPROJECT_FILENAME
                if not pyproject.is_file():
                    continue
                if not (entry / c.Infra.Files.MAKEFILE_FILENAME).is_file():
                    continue
                payload = FlextInfraUtilitiesDocsScope.pyproject_payload(entry)
                docs_meta = FlextInfraUtilitiesDocsScope.docs_meta_from_payload(payload)
                enabled = docs_meta.get("enabled", True)
                if isinstance(enabled, bool) and not enabled:
                    continue
                projects.append(
                    m.Infra.ProjectInfo.model_construct(
                        path=entry,
                        name=entry.name,
                        stack="python/flext",
                        has_tests=(entry / c.Infra.Directories.TESTS).is_dir(),
                        has_src=(entry / c.Infra.Paths.DEFAULT_SRC_DIR).is_dir(),
                        project_class=(
                            FlextInfraUtilitiesDocsScope.classify_project_from_meta(
                                entry.name,
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
                    )
                ),
        except OSError as exc:
            return r[Sequence[m.Infra.ProjectInfo]].fail(
                f"discovery failed: {exc}",
            )
        return r[Sequence[m.Infra.ProjectInfo]].ok(projects)

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


__all__ = ["FlextInfraUtilitiesDocsScope"]
