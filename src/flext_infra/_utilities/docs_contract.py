"""Reusable docs contract helpers exposed through ``u.Infra``."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from flext_infra import c, m, t
from flext_infra._utilities.docs_api import FlextInfraUtilitiesDocsApi
from flext_infra._utilities.docs_scope import FlextInfraUtilitiesDocsScope


class FlextInfraUtilitiesDocsContract:
    """Contract helpers for docs services."""

    @staticmethod
    def docs_contract(
        project_root: Path,
        package_name: str,
    ) -> dict[str, object]:
        """Return the public docs contract for a project."""
        return dict(
            FlextInfraUtilitiesDocsApi.public_contract(project_root, package_name)
        )

    @staticmethod
    def docs_workspace_contract(
        workspace_root: Path,
    ) -> dict[str, object]:
        """Return the root docs contract using root ``pyproject.toml`` metadata."""
        payload = FlextInfraUtilitiesDocsScope.pyproject_payload(workspace_root)
        docs_meta = FlextInfraUtilitiesDocsScope.workspace_docs_meta(workspace_root)
        exclude_docs = FlextInfraUtilitiesDocsScope.docs_meta_list(
            workspace_root,
            "exclude_docs",
        )
        project_meta_value = payload.get(c.Infra.PROJECT)
        project_meta: t.Infra.ContainerDict = (
            project_meta_value if isinstance(project_meta_value, Mapping) else {}
        )
        project_urls_value = project_meta.get("urls")
        project_urls: t.Infra.ContainerDict = (
            project_urls_value if isinstance(project_urls_value, Mapping) else {}
        )
        return {
            "name": str(project_meta.get("name", "flext")).strip() or "flext",
            "description": str(project_meta.get("description", "")).strip(),
            "version": str(project_meta.get(c.Infra.VERSION, "")).strip(),
            "site_title": str(docs_meta.get("site_title", "")).strip()
            or "FLEXT Workspace",
            "site_url": str(
                project_urls.get("Documentation")
                or project_urls.get("Homepage")
                or c.Infra.GITHUB_REPO_URL
            ).strip(),
            "repo_url": str(
                project_urls.get("Repository")
                or project_urls.get("Homepage")
                or c.Infra.GITHUB_REPO_URL
            ).strip(),
            "exclude_docs": exclude_docs,
        }

    @staticmethod
    def docs_write_if_needed(
        path: Path,
        content: str,
        *,
        apply: bool,
        overwrite: bool = True,
    ) -> m.Infra.GeneratedFile:
        """Write generated content only when needed and allowed."""
        if path.exists() and not overwrite:
            return m.Infra.GeneratedFile(path=path.as_posix(), written=False)
        current = (
            path.read_text(encoding=c.Infra.Encoding.DEFAULT) if path.exists() else ""
        )
        if current == content:
            return m.Infra.GeneratedFile(path=path.as_posix(), written=False)
        if apply:
            path.parent.mkdir(parents=True, exist_ok=True)
            _ = path.write_text(content, encoding=c.Infra.Encoding.DEFAULT)
        return m.Infra.GeneratedFile(path=path.as_posix(), written=apply)


__all__ = ["FlextInfraUtilitiesDocsContract"]
