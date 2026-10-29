"""Root-owned project-guide generation for documentation utilities.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import u

from flext_infra import c, m, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesProjectManagedArtifacts,
)
from flext_infra._utilities._docs import (
    FlextInfraUtilitiesDocsCommandContract,
    FlextInfraUtilitiesDocsGeneratePlan,
    FlextInfraUtilitiesDocsRender,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraUtilitiesDocsGuides:
    """Project guide projections derived from root ``docs/guides`` sources."""

    @staticmethod
    def docs_make_contract_plan(
        repository_root: Path,
        declared_files: tuple[m.Infra.CodegenFilePlan, ...] = (),
    ) -> p.Result[m.Infra.CodegenFilePlan | None]:
        """Plan the declared catalog section against its original guide observation.

        Returns:
            The mixed-file effect, no effect when undeclared, or the original failure.

        Raises:
            ValueError: The declared section or template heading is not unique.

        """
        result = r[m.Infra.CodegenFilePlan | None]
        owner = FlextInfraUtilitiesProjectDiscovery.runtime_owner_root(repository_root)
        if owner.failure:
            return result.from_failure(owner)
        repository_root = owner.value
        loaded = FlextInfraUtilitiesProjectManagedArtifacts.load_codegen_inputs(
            repository_root
        )
        if loaded.failure:
            return result.from_failure(loaded)
        make = loaded.value.spec.make
        if make.docs.contract_guide is None:
            return result.ok(None)
        path = repository_root / make.docs.contract_guide
        previous = next((plan for plan in declared_files if plan.path == path), None)
        captured = (
            r[m.Cli.AtomicFileState].ok(previous.before)
            if previous is not None
            else u.Cli.atomic_read_binary_file_state(path, required=True)
        )
        if captured.failure:
            return result.from_failure(captured)
        content = previous.desired_content if previous is not None else captured.value.content
        if content is None:
            return result.fail(f"declared Make contract guide is absent: {path}")
        rendered = FlextInfraUtilitiesDocsRender.docs_make_contract(make)
        if rendered.failure:
            return result.from_failure(rendered)
        section = rendered.value.rendered
        declared_headings = u.Cli.markdown_headings(section)
        if len(declared_headings) != 1:
            msg = "Make contract template must declare exactly one section heading"
            raise ValueError(msg)
        heading = declared_headings[0]
        source = content.decode(c.DEFAULT_ENCODING)
        headings = u.Cli.markdown_headings(source)
        matches = tuple(
            item
            for item in headings
            if item.level == heading.level and item.text == heading.text
        )
        if len(matches) != 1:
            msg = f"Make contract section is absent or ambiguous: {path}: {heading.text}"
            raise ValueError(msg)
        selected = matches[0]
        lines = source.splitlines(keepends=True)
        end = next(
            (
                item.line - 1
                for item in headings
                if item.line > selected.line and item.level <= selected.level
            ),
            len(lines),
        )
        updated = (
            "".join(lines[: selected.line - 1])
            + section.rstrip()
            + "\n\n"
            + "".join(lines[end:])
        )
        return result.ok(
            m.Infra.CodegenFilePlan(
                project=repository_root,
                path=path,
                before=captured.value,
                desired_content=updated.encode(c.DEFAULT_ENCODING),
                desired_mode=(previous.desired_mode if previous is not None else captured.value.mode),
                owner="docs",
                policy="merge",
                inputs=(
                    *loaded.value.sources,
                    *rendered.value.source_states,
                    *(previous.inputs if previous is not None else ()),
                ),
            )
        )

    @staticmethod
    def docs_project_guide_content(
        content: str,
        project_name: str,
        guide_name: str,
    ) -> str:
        """Render a member guide with explicit source and regeneration ownership.

        Returns:
            The resulting ``str``.

        """
        lines = content.splitlines()
        title = Path(guide_name).stem.replace("_", " ").replace("-", " ").strip()
        body_lines = lines
        heading = next(iter(u.Cli.markdown_headings(content)), None)
        if heading is not None:
            title = heading.text or title
            body_lines = lines[heading.line :]
        body = "\n".join(body_lines).lstrip()
        header = (
            "<!-- AUTO-GENERATED FILE — regenerate through `make gen` "
            "from the workspace root. -->\n"
            f"<!-- Source of truth: `<workspace-root>/docs/guides/{guide_name}`; "
            "adjust that workspace source, never this member projection. -->\n\n"
            f"# {project_name} - {title}\n\n"
            f"> Project profile: `{project_name}`"
        )
        return f"{header}\n\n{body}".rstrip() + "\n"

    @staticmethod
    def docs_sanitize_internal_anchor_links(content: str) -> str:
        """Replace local Markdown links with text while retaining external links.

        Returns:
            The resulting ``str``.

        """
        preserved = (
            *(f"{scheme}:" for scheme in sorted(c.Infra.DOCS_EXTERNAL_SCHEMES)),
            c.Infra.DOCS_FRAGMENT_PREFIX,
        )

        # The declared scheme catalog is the only authority for what survives:
        # a second list here drifted into preserving `http://` while the
        # insecure scheme is rejected elsewhere.
        return u.Cli.markdown_unlink(
            content,
            lambda link: not link.image and not link.target.startswith(preserved),
        )

    @staticmethod
    def _classified_guide_sources(
        source_root: Path,
        destination_root: Path,
        declared_files: tuple[m.Infra.CodegenFilePlan, ...] = (),
    ) -> tuple[MutableMapping[Path, str], MutableMapping[Path, str]]:
        """Read the canonical guides and their current scope projections.

        Returns:
            The resulting ``(sources, destinations)`` mapping pair.

        """
        sources, destinations = (
            {
                path: path.read_text(encoding=c.DEFAULT_ENCODING)
                for path in sorted(root.glob("*.md"))
                if path.name != "README.md" and path.is_file()
            }
            for root in (source_root, destination_root)
        )
        for plan in declared_files:
            if plan.path.parent == source_root:
                if plan.desired_content is None:
                    sources.pop(plan.path, None)
                else:
                    sources[plan.path] = plan.desired_content.decode(c.DEFAULT_ENCODING)
        return sources, destinations

    @staticmethod
    def _owned_destinations(
        scope: m.Infra.DocScope,
        destinations: Mapping[Path, str],
    ) -> set[Path]:
        """Collect destination guides still carrying a canonical ownership header.

        Returns:
            The resulting ``set[Path]``.

        """
        owned: set[Path] = set()
        for path, content in destinations.items():
            lines = content.splitlines()
            generated = (
                "<!-- AUTO-GENERATED FILE — regenerate through `make gen` "
                "from the workspace root. -->"
            )
            source_headers = {
                (
                    f"<!-- Source of truth: `docs/guides/{path.name}`; "
                    "adjust that source, never this projection. -->"
                ),
                (
                    f"<!-- Source of truth: `<workspace-root>/docs/guides/{path.name}`"
                    "; adjust that workspace source, never this member projection. -->"
                ),
            }
            if (
                len(lines) >= c.Infra.DOCS_OWNED_HEADER_LINES
                and lines[0] == generated
                and lines[1] in source_headers
            ):
                owned.add(path)
                continue
            ownership = FlextInfraUtilitiesDocsGuides.docs_project_guide_content(
                "",
                scope.name,
                path.name,
            ).partition("\n\n")[0]
            previous_ownership = ownership.replace("`<workspace-root>/", "`")
            legacy_ownership = (
                "<!-- AUTO-GENERATED FILE — regenerate through `make gen` "
                "from the workspace root. -->\n"
                f"<!-- Source of truth: `docs/guides/{path.name}`; "
                "adjust that workspace source, never this member projection. -->"
            )
            if content.startswith((
                ownership + "\n\n",
                previous_ownership + "\n\n",
                legacy_ownership + "\n\n",
            )):
                owned.add(path)
        return owned

    @classmethod
    def _rendered_guide_artifacts(
        cls,
        scope: m.Infra.DocScope,
        workspace_root: Path,
        sources: Mapping[Path, str],
        destinations: Mapping[Path, str],
        owned: set[Path],
    ) -> p.Result[list[t.Infra.DocsRenderedArtifactTuple]]:
        """Render every canonical guide and drop retired owned projections.

        Returns:
            The resulting ``p.Result[list[t.Infra.DocsRenderedArtifactTuple]]``.

        Raises:
            ValueError: If issues.

        """
        loaded = FlextInfraUtilitiesProjectManagedArtifacts.load_codegen_inputs(
            workspace_root,
        )
        if loaded.failure:
            return r[list[t.Infra.DocsRenderedArtifactTuple]].from_failure(loaded)
        effective_verbs = (
            *loaded.value.spec.make.verbs,
            *(
                loaded.value.spec.repository.extra_verbs
                if loaded.value.spec.repository
                else ()
            ),
        )
        destination_root = scope.path / c.Infra.DIR_DOCS / "guides"
        artifacts: list[t.Infra.DocsRenderedArtifactTuple] = []
        for source_path, source in sorted(sources.items()):
            destination = destination_root / source_path.name
            if destination in destinations and destination not in owned:
                return r[list[t.Infra.DocsRenderedArtifactTuple]].fail(
                    f"canonical guide collides with protected custom guide: "
                    f"{destination}",
                )
            relative_path = source_path.relative_to(workspace_root).as_posix()
            contract_mixin = FlextInfraUtilitiesDocsCommandContract
            issues = contract_mixin.docs_command_contract_content_issues(
                source,
                relative_path=relative_path,
                effective_verbs=effective_verbs,
            )
            if issues:
                first = issues[0]
                msg = f"{first.file}: {first.message}"
                raise ValueError(msg)
            rendered = FlextInfraUtilitiesDocsGuides.docs_project_guide_content(
                source,
                scope.name,
                source_path.name,
            )
            artifacts.append((
                scope.path,
                destination,
                FlextInfraUtilitiesDocsGuides.docs_sanitize_internal_anchor_links(
                    rendered,
                ),
            ))
        expected_paths = {destination_root / path.name for path in sources}
        artifacts.extend(
            (scope.path, path, None) for path in sorted(owned - expected_paths)
        )
        return r[list[t.Infra.DocsRenderedArtifactTuple]].ok(artifacts)

    @classmethod
    def docs_project_guides_artifacts(
        cls,
        scope: m.Infra.DocScope,
        *,
        repository_root: Path,
    ) -> p.Result[tuple[t.Infra.DocsRenderedArtifactTuple, ...]]:
        """Plan root-owned guide projections from the canonical guides.

        The canonical guides belong to the containing workspace elected by the
        runtime owner: an attached member resolves them from its declaring
        workspace, so a member-scoped generation refreshes its projections
        exactly as a root generation does. A standalone checkout and the
        workspace itself own their guides, which are never their own
        projections.

        Returns:
            The resulting
                ``p.Result[tuple[t.Infra.DocsRenderedArtifactTuple, ...]]``.

        """
        if not scope.path.is_relative_to(repository_root):
            return r[tuple[t.Infra.DocsRenderedArtifactTuple, ...]].fail(
                f"docs guide scope escapes repository {repository_root}: {scope.path}",
            )
        workspace = FlextInfraUtilitiesProjectDiscovery.runtime_owner_root(
            repository_root,
        )
        if workspace.failure:
            return r[tuple[t.Infra.DocsRenderedArtifactTuple, ...]].from_failure(
                workspace,
            )
        source_root = workspace.value / c.Infra.DIR_DOCS / "guides"
        destination_root = scope.path / c.Infra.DIR_DOCS / "guides"
        if source_root == destination_root.resolve():
            # Same-root inputs are authoritative, never their own projections.
            return r[tuple[t.Infra.DocsRenderedArtifactTuple, ...]].ok(())
        sources, destinations = cls._classified_guide_sources(
            source_root, destination_root, scope.declared_files
        )
        owned = cls._owned_destinations(scope, destinations)
        artifacts = cls._rendered_guide_artifacts(
            scope,
            workspace.value,
            sources,
            destinations,
            owned,
        )
        if artifacts.failure:
            return r[tuple[t.Infra.DocsRenderedArtifactTuple, ...]].from_failure(
                artifacts,
            )
        return FlextInfraUtilitiesDocsGeneratePlan.docs_normalize_artifacts(
            artifacts.value,
        )


__all__: list[str] = ["FlextInfraUtilitiesDocsGuides"]
