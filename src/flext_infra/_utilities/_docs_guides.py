"""Root-owned project-guide generation for documentation utilities."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m
from flext_infra._utilities._docs_command_contract import (
    FlextInfraUtilitiesDocsCommandContractMixin,
)
from flext_infra._utilities.docs_contract import FlextInfraUtilitiesDocsContract

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraUtilitiesDocsGuidesMixin:
    """Project guide projections derived from root ``docs/guides`` sources."""

    @staticmethod
    def docs_project_guide_content(
        content: str, project_name: str, guide_name: str
    ) -> str:
        """Render a member guide with explicit source and regeneration ownership."""
        lines = content.splitlines()
        title = Path(guide_name).stem.replace("_", " ").replace("-", " ").strip()
        body_lines = lines
        for index, line in enumerate(lines):
            match = c.Infra.HEADING_RE.match(line)
            if match is None:
                continue
            title = match.group(1).strip() or title
            body_lines = lines[index + 1 :]
            break
        body = "\n".join(body_lines).lstrip()
        header = (
            "<!-- AUTO-GENERATED FILE — regenerate through `make gen APPLY=Y` "
            "from the workspace root. -->\n"
            f"<!-- Source of truth: `docs/guides/{guide_name}`; adjust that source, "
            "never this projection. -->\n\n"
            f"# {project_name} - {title}\n\n"
            f"> Project profile: `{project_name}`"
        )
        return f"{header}\n\n{body}".rstrip() + "\n"

    @staticmethod
    def docs_sanitize_internal_anchor_links(content: str) -> str:
        """Replace local Markdown links with text while retaining external links."""
        preserved = (
            *(f"{scheme}:" for scheme in sorted(c.Infra.DOCS_EXTERNAL_SCHEMES)),
            c.Infra.DOCS_FRAGMENT_PREFIX,
        )

        def sanitize_link(match: re.Match[str]) -> str:
            # The declared scheme catalog is the only authority for what
            # survives: a second list here drifted into preserving `http://`
            # while the insecure scheme is rejected elsewhere.
            target = match.group(2)
            return match.group(0) if target.startswith(preserved) else match.group(1)

        return re.sub(c.Infra.MARKDOWN_LINK_RE, sanitize_link, content)

    @staticmethod
    def docs_project_guides_files(
        scope: m.Infra.DocScope, *, repository_root: Path, apply: bool
    ) -> t.SequenceOf[m.Infra.GeneratedFile]:
        """Project every canonical root guide into one member docs tree."""
        source_root = repository_root / c.Infra.DIR_DOCS / "guides"
        destination_root = scope.path / c.Infra.DIR_DOCS / "guides"
        if source_root.resolve() == destination_root.resolve():
            # A standalone package has no distinct workspace guide source. Its
            # own ``docs/guides`` tree is already the generated projection, so
            # reading it as input would prepend another heading/profile on each
            # generation. The workspace root remains the only source for member
            # guide projections; a direct package run must be a fixed point.
            return []
        if not source_root.is_dir():
            msg = f"canonical guide source not found: {source_root}"
            raise FileNotFoundError(msg)
        source_paths = sorted(
            path for path in source_root.glob("*.md") if path.name != "README.md"
        )
        expected_paths = {
            destination_root / "README.md",
            *(destination_root / path.name for path in source_paths),
        }
        files: t.MutableSequenceOf[m.Infra.GeneratedFile] = []
        for source_path in source_paths:
            source = source_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
            relative_path = source_path.relative_to(repository_root).as_posix()
            issues = FlextInfraUtilitiesDocsCommandContractMixin.docs_command_contract_content_issues(
                source, relative_path=relative_path
            )
            if issues:
                first = issues[0]
                msg = f"{first.file}: {first.message}"
                raise ValueError(msg)
            rendered = FlextInfraUtilitiesDocsGuidesMixin.docs_project_guide_content(
                source, scope.name, source_path.name
            )
            files.append(
                FlextInfraUtilitiesDocsContract.docs_write_if_needed(
                    destination_root / source_path.name,
                    FlextInfraUtilitiesDocsGuidesMixin.docs_sanitize_internal_anchor_links(
                        rendered
                    ),
                    apply=apply,
                )
            )
        for destination_path in sorted(destination_root.glob("*.md")):
            if destination_path in expected_paths:
                continue
            existing = destination_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
            if not existing.startswith(
                "<!-- AUTO-GENERATED FILE"
            ) and not existing.startswith("<!-- Generated from docs/guides/"):
                continue
            if apply:
                destination_path.unlink()
            files.append(
                m.Infra.GeneratedFile(
                    path=destination_path.as_posix(), changed=True, written=apply
                )
            )
        return files


__all__: list[str] = ["FlextInfraUtilitiesDocsGuidesMixin"]
