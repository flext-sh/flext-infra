"""Reusable docs contract helpers exposed through ``u.Infra``."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from flext_cli import u
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.typings import t
from flext_infra._utilities.docs_scope import FlextInfraUtilitiesDocsScope

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraUtilitiesDocsContract:
    """Contract helpers for docs services."""

    @staticmethod
    def docs_update_toc(content: str) -> t.StrIntPair:
        """Normalize the managed table of contents in Markdown content."""
        toc = FlextInfraUtilitiesDocsContract.docs_build_toc(content)
        if c.Infra.TOC_START in content and c.Infra.TOC_END in content:
            updated = c.Infra.TOC_BLOCK_RE.sub(toc, content, count=1)
            return (updated, int(updated != content))
        lines = content.splitlines()
        if lines and lines[0].startswith("# "):
            insert_at = 1
            while insert_at < len(lines) and (not lines[insert_at].strip()):
                insert_at += 1
            lines.insert(insert_at, "")
            lines.insert(insert_at + 1, toc)
            lines.insert(insert_at + 2, "")
            updated = "\n".join(lines) + ("\n" if content.endswith("\n") else "")
            return (updated, 1)
        return (toc + "\n\n" + content, 1)

    @staticmethod
    def docs_anchorize(text: str) -> str:
        """Convert a heading title to a GitHub-compatible anchor slug."""
        normalized: str = u.norm_str(text, case="lower")
        alnum_only: str = c.Infra.ANCHOR_NON_ALNUM_RE.sub("", normalized)
        collapsed_whitespace: str = c.Infra.ANCHOR_WHITESPACE_RE.sub("-", alnum_only)
        slug: str = c.Infra.ANCHOR_DASH_COLLAPSE_RE.sub(
            "-", collapsed_whitespace
        ).strip("-")
        return slug

    @staticmethod
    def docs_build_toc(content: str) -> str:
        """Generate a managed TOC block from second- and third-level headings."""
        items: t.MutableSequenceOf[str] = []
        for level, title in c.Infra.HEADING_H2_H3_RE.findall(content):
            anchor = FlextInfraUtilitiesDocsContract.docs_anchorize(title)
            if anchor:
                indent = "  " if level == "###" else ""
                items.append(f"{indent}- [{title}](#{anchor})")
        if not items:
            items = ["- No sections found"]
        return f"{c.Infra.TOC_START}\n" + "\n".join(items) + f"\n{c.Infra.TOC_END}"

    @staticmethod
    def docs_workspace_contract(workspace_root: Path) -> t.JsonMapping:
        """Return the root docs contract using root ``pyproject.toml`` metadata."""
        payload = FlextInfraUtilitiesDocsScope.project_payload(workspace_root)
        docs_meta = FlextInfraUtilitiesDocsScope.project_docs_meta(workspace_root)
        exclude_docs = FlextInfraUtilitiesDocsScope.docs_meta_list(
            workspace_root, "exclude_docs"
        )
        project_meta_value = payload.get(c.Infra.PROJECT)
        project_meta: t.JsonMapping = (
            t.Infra.INFRA_MAPPING_ADAPTER.validate_python(project_meta_value)
            if isinstance(project_meta_value, Mapping)
            else t.Infra.INFRA_MAPPING_ADAPTER.validate_python({})
        )
        project_urls_value = project_meta.get("urls")
        project_urls: t.JsonMapping = (
            t.Infra.INFRA_MAPPING_ADAPTER.validate_python(project_urls_value)
            if isinstance(project_urls_value, Mapping)
            else t.Infra.INFRA_MAPPING_ADAPTER.validate_python({})
        )
        result: t.JsonMapping = t.Infra.INFRA_MAPPING_ADAPTER.validate_python({
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
            "exclude_docs": list(exclude_docs),
        })
        return result

    @staticmethod
    def docs_write_if_needed(
        path: Path, content: str, *, apply: bool, overwrite: bool = True
    ) -> m.Infra.GeneratedFile:
        """Write generated content only when needed and allowed."""
        if path.exists() and not overwrite:
            return m.Infra.GeneratedFile(
                path=path.as_posix(), changed=False, written=False
            )
        current = (
            path.read_text(encoding=c.Cli.ENCODING_DEFAULT) if path.exists() else ""
        )
        normalized = (
            FlextInfraUtilitiesDocsContract.docs_update_toc(content)[0]
            if path.suffix == ".md"
            else content
        )
        changed = current != normalized
        if changed and apply:
            path.parent.mkdir(parents=True, exist_ok=True)
            _ = path.write_text(normalized, encoding=c.Cli.ENCODING_DEFAULT)
        return m.Infra.GeneratedFile(
            path=path.as_posix(), changed=changed, written=changed and apply
        )


__all__: list[str] = ["FlextInfraUtilitiesDocsContract"]
