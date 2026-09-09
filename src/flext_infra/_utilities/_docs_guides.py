"""Root-owned project-guide generation for documentation utilities."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, m

from ._docs_command_contract import FlextInfraUtilitiesDocsCommandContractMixin
from ._docs_generate_plan import (
    DocsRenderedArtifactTuple,
    FlextInfraUtilitiesDocsGeneratePlanMixin,
)

if TYPE_CHECKING:
    from flext_infra import p, t


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
    def docs_project_guides_artifacts(
        scope: m.Infra.DocScope,
        *,
        repository_root: Path,
        source_states: t.SequenceOf[m.Cli.AtomicFileState],
    ) -> p.Result[t.VariadicTuple[DocsRenderedArtifactTuple]]:
        """Plan root-owned guide projections from authenticated snapshot bytes."""
        source_root = repository_root / c.Infra.DIR_DOCS / "guides"
        destination_root = scope.path / c.Infra.DIR_DOCS / "guides"
        if source_root == destination_root:
            # Same-root inputs are authoritative, never their own projections.
            return r[tuple[DocsRenderedArtifactTuple, ...]].ok(())
        if not scope.path.is_relative_to(repository_root):
            return r[tuple[DocsRenderedArtifactTuple, ...]].fail(
                f"docs guide scope escapes repository {repository_root}: {scope.path}"
            )
        sources: dict[Path, str] = {}
        destinations: dict[Path, str] = {}
        for state in source_states:
            path = state.path
            if (
                path.parent not in {source_root, destination_root}
                or path.suffix != ".md"
                or path.name == "README.md"
            ):
                continue
            if state.content is None:
                return r[tuple[DocsRenderedArtifactTuple, ...]].fail(
                    f"docs guide source is absent: {path}"
                )
            content = state.content.decode(c.Cli.ENCODING_DEFAULT)
            if path.parent == source_root:
                sources[path] = content
            else:
                destinations[path] = content
        owned: set[Path] = set()
        for path, content in destinations.items():
            ownership = FlextInfraUtilitiesDocsGuidesMixin.docs_project_guide_content(
                "", scope.name, path.name
            ).partition("\n\n")[0]
            if content.startswith(ownership + "\n\n"):
                owned.add(path)
        artifacts: list[DocsRenderedArtifactTuple] = []
        expected_paths = {destination_root / path.name for path in sources}
        for source_path, source in sorted(sources.items()):
            destination = destination_root / source_path.name
            if destination in destinations and destination not in owned:
                return r[tuple[DocsRenderedArtifactTuple, ...]].fail(
                    f"canonical guide collides with protected custom guide: {destination}"
                )
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
            artifacts.append((
                scope.path,
                destination,
                FlextInfraUtilitiesDocsGuidesMixin.docs_sanitize_internal_anchor_links(
                    rendered
                ),
            ))
        artifacts.extend(
            (scope.path, path, None) for path in sorted(owned - expected_paths)
        )
        return FlextInfraUtilitiesDocsGeneratePlanMixin.docs_normalize_artifacts(
            artifacts
        )


__all__: list[str] = ["FlextInfraUtilitiesDocsGuidesMixin"]
