"""Gitignore rendering utilities for ``u.Infra``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from itertools import pairwise
from operator import itemgetter
from pathlib import Path

from flext_cli import u

from flext_infra import FlextInfraConfig, c, m, p, r
from flext_infra._utilities import (
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesProjectManagedArtifacts,
)


class FlextInfraUtilitiesGitignore:
    """Gitignore rendering utilities."""

    @staticmethod
    def codegen_templates_root(codegen: m.Infra.CodegenConfigSpec) -> Path:
        """Return the resolved template root of the installed flext-infra package.

        Returns:
            The resolved template root of the installed flext-infra package.

        """
        return (
            FlextInfraConfig.ssot_config_dir().parent
            / "templates"
            / codegen.templates.root
        ).resolve()

    @staticmethod
    def codegen_artifact_source(
        codegen: m.Infra.CodegenConfigSpec,
        entry: m.Infra.TemplateEntrySpec,
    ) -> Path:
        """Resolve a declared source inside its explicit package or template root.

        Returns:
            The confined original package asset or template source path.

        Raises:
            ValueError: If the source is absent, escapes its root, or lacks a
                unique original package directory.

        """
        if entry.source is None:
            msg = f"artifact has no source: {entry.destination}"
            raise ValueError(msg)
        if entry.source_kind == "template":
            root = FlextInfraUtilitiesGitignore.codegen_templates_root(codegen)
        else:
            if entry.source_package is None:
                msg = f"resource has no explicit package owner: {entry.destination}"
                raise ValueError(msg)
            # Per-repository resolution law: a declared artifact owner resolves
            # inside the engine's own tree only. Installed environments are
            # never consulted, where divergent member libraries would leak in
            # as artifact sources.
            engine_root = FlextInfraConfig.ssot_config_dir().parent.parent
            package = FlextInfraUtilitiesDiscovery.declared_package_dir(
                entry.source_package,
                search_paths=(str(engine_root),),
            )
            if package is None:
                msg = (
                    "resource source must name a package inside the engine's own "
                    f"tree: {entry.source_package}"
                )
                raise ValueError(msg)
            root = package.resolve()
        source = root / entry.source
        if not source.resolve().is_relative_to(root):
            msg = f"declared artifact source escapes its owner root: {entry.source}"
            raise ValueError(msg)
        return source

    @staticmethod
    def codegen_template_sources(codegen: m.Infra.CodegenConfigSpec) -> frozenset[Path]:
        """Resolve only manifest-declared template inputs, never output suffixes.

        Returns:
            The resulting ``frozenset[Path]``.

        """
        sources: set[Path] = set()
        for entry in codegen.templates.entries:
            if entry.source is None:
                continue
            sources.update(
                FlextInfraUtilitiesGitignore.codegen_artifact_source(
                    codegen,
                    entry.model_copy(update={"source": source}),
                ).resolve()
                for source in entry.source_closure or (entry.source,)
            )
        return frozenset(sources)

    @staticmethod
    def render_project_ignore(
        codegen: m.Infra.CodegenConfigSpec,
        *,
        profile: c.Infra.MakeProfile,
        project_name: str,
        workspace: m.Infra.WorkspaceSpec | None = None,
        project_dir: Path | None = None,
    ) -> p.Result[str]:
        """Render the canonical ``.ignore`` for one named project.

        Render the declared fleet sections, then retain any external blocks
        delegated by the project's typed config from its live ignore file.

        Returns:
            The resulting ``p.Result[str]``.

        """
        entry = next(
            (
                item
                for item in codegen.templates.entries
                if item.destination == c.Infra.GITIGNORE
            ),
            None,
        )
        if entry is None:
            return r[str].fail(
                "ignore template is missing from codegen configuration",
            )
        if entry.source is None:
            return r[str].fail(
                "ignore codegen entry must declare a render template source",
            )
        templates_root = FlextInfraUtilitiesGitignore.codegen_templates_root(codegen)
        project_patterns: Sequence[str] = ()
        preserved_blocks: tuple[m.Infra.ProjectGitignorePreservedBlock, ...] = ()
        if project_dir is not None:
            managed = FlextInfraUtilitiesProjectManagedArtifacts
            resolved = managed.load_project_managed_artifacts(project_dir)
            if resolved.failure:
                return r[str].from_failure(resolved)
            project_patterns = resolved.value.artifacts.Gitignore.patterns
            preserved_blocks = resolved.value.artifacts.Gitignore.preserved_blocks
        context = m.Infra.GitignoreRenderSpec(
            ignore_sections=FlextInfraUtilitiesGitignore.ignore_sections(
                codegen,
                profile=profile,
                project_name=project_name,
                workspace=workspace,
                project_patterns=project_patterns,
            ),
        )
        rendered = u.Cli.template_render(templates_root / entry.source, context)
        if rendered.failure or project_dir is None:
            return rendered
        suffix = FlextInfraUtilitiesGitignore.ignore_runtime_suffix(codegen)
        if suffix.failure:
            return r[str].from_failure(suffix)
        return FlextInfraUtilitiesGitignore.preserve_project_ignore_blocks(
            rendered.value,
            project_dir,
            preserved_blocks,
            runtime_suffix=suffix.value,
        )

    @staticmethod
    def preserve_project_ignore_blocks(
        rendered: str,
        project_dir: Path,
        blocks: tuple[m.Infra.ProjectGitignorePreservedBlock, ...],
        *,
        runtime_suffix: str = "",
    ) -> p.Result[str]:
        """Compose declared external blocks without taking ownership of their lines.

        Returns:
            The resulting ``p.Result[str]``.

        """
        if not blocks:
            return r[str].ok(rendered)

        destination = project_dir / c.Infra.GITIGNORE
        markers = frozenset(
            marker for block in blocks for marker in (block.begin, block.end)
        )
        if any(line in markers for line in rendered.splitlines()):
            return r[str].fail(
                f"generated ignore claims a declared external block: {destination}",
            )
        snapshot = u.Cli.atomic_read_binary_file_state(destination, required=False)
        if snapshot.failure:
            return r[str].from_failure(snapshot)
        content = snapshot.value.content
        if content is None:
            return r[str].ok(rendered)
        if runtime_suffix and not rendered.endswith(runtime_suffix):
            error = ValueError(
                f"generated ignore lacks its declared runtime policy: {destination}",
            )
            return r[str].fail(str(error), exception=error)
        prefix = rendered.removesuffix(runtime_suffix) if runtime_suffix else rendered
        composed = FlextInfraUtilitiesGitignore._compose_preserved_blocks(
            prefix,
            content,
            blocks,
            markers,
            destination,
        )
        return FlextInfraUtilitiesGitignore._apply_runtime_suffix(
            composed,
            runtime_suffix,
        )

    @staticmethod
    def _apply_runtime_suffix(
        composed: p.Result[str],
        runtime_suffix: str,
    ) -> p.Result[str]:
        """Re-append the runtime tracking policy after preserved external blocks.

        Returns:
            The composed ignore with its declared runtime policy restored.

        """
        if composed.failure or not runtime_suffix:
            return composed
        separator = "" if composed.value.endswith("\n\n") else "\n"
        return r[str].ok(composed.value + separator + runtime_suffix)

    @staticmethod
    def ignore_runtime_suffix(codegen: m.Infra.CodegenConfigSpec) -> p.Result[str]:
        """Render the final tracking policy from the same typed section owner.

        Returns:
            The exact final fragment, empty only when no local artifacts are declared.

        """
        sections = FlextInfraUtilitiesGitignore._runtime_ignore_sections(codegen)
        if not sections:
            return r[str].ok("")
        entry = next(
            (
                item
                for item in codegen.templates.entries
                if item.destination == c.Infra.GITIGNORE
            ),
            None,
        )
        if entry is None or entry.source is None:
            error = ValueError("ignore rendering source is not declared")
            return r[str].fail(str(error), exception=error)
        return u.Cli.template_render(
            FlextInfraUtilitiesGitignore.codegen_templates_root(codegen) / entry.source,
            m.Infra.GitignoreRenderSpec(ignore_sections=sections),
        )

    @staticmethod
    def _locate_block_markers(
        lines: Sequence[str],
        markers: frozenset[str],
        destination: Path,
    ) -> p.Result[MutableMapping[str, list[int]]]:
        """Index the exact marker lines, rejecting malformed marker prefixes.

        Returns:
            The resulting ``p.Result[MutableMapping[str, list[int]]]``.

        """
        found: MutableMapping[str, list[int]] = {marker: [] for marker in markers}
        for index, line in enumerate(lines):
            text = line.rstrip("\r\n")
            if text in found:
                found[text].append(index)
            elif any(text.startswith(marker) for marker in markers):
                return r[MutableMapping[str, list[int]]].fail(
                    f"malformed ignore preserved marker: {destination}: {text!r}",
                )
        return r[MutableMapping[str, list[int]]].ok(found)

    @staticmethod
    def _block_sections(
        blocks: tuple[m.Infra.ProjectGitignorePreservedBlock, ...],
        found: Mapping[str, list[int]],
        lines: Sequence[str],
        destination: Path,
    ) -> p.Result[tuple[tuple[int, int, str], ...]]:
        """Slice one ordered, non-overlapping external section per declared block.

        Returns:
            The resulting ``p.Result[tuple[tuple[int, int, str], ...]]``.

        """
        sections: list[tuple[int, int, str]] = []
        for block in blocks:
            begins = found[block.begin]
            ends = found[block.end]
            if not begins and not ends:
                continue
            if len(begins) != 1 or len(ends) != 1 or begins[0] >= ends[0]:
                return r[tuple[tuple[int, int, str], ...]].fail(
                    f"ambiguous ignore preserved block {block.begin!r}: {destination}",
                )
            sections.append((
                begins[0],
                ends[0],
                "".join(lines[begins[0] : ends[0] + 1]),
            ))
        sections.sort(key=itemgetter(0))
        if any(previous[1] >= current[0] for previous, current in pairwise(sections)):
            return r[tuple[tuple[int, int, str], ...]].fail(
                f"overlapping ignore preserved blocks: {destination}",
            )
        return r[tuple[tuple[int, int, str], ...]].ok(tuple(sections))

    @staticmethod
    def _compose_preserved_blocks(
        rendered: str,
        content: bytes,
        blocks: tuple[m.Infra.ProjectGitignorePreservedBlock, ...],
        markers: frozenset[str],
        destination: Path,
    ) -> p.Result[str]:
        """Append every located external block to the freshly rendered content.

        Returns:
            The resulting ``p.Result[str]``.

        """
        lines = content.decode(c.DEFAULT_ENCODING).splitlines(keepends=True)
        located = FlextInfraUtilitiesGitignore._locate_block_markers(
            lines,
            markers,
            destination,
        )
        if located.failure:
            return r[str].from_failure(located)
        sections = FlextInfraUtilitiesGitignore._block_sections(
            blocks,
            located.value,
            lines,
            destination,
        )
        if sections.failure:
            return r[str].from_failure(sections)
        composed = rendered
        for _, _, external in sections.value:
            if composed and not composed.endswith("\n"):
                composed += "\n"
            if composed and not composed.endswith("\n\n"):
                composed += "\n"
            composed += external
        return r[str].ok(composed)

    @staticmethod
    def ignore_sections(
        codegen: m.Infra.CodegenConfigSpec,
        *,
        profile: c.Infra.MakeProfile,
        project_name: str | None = None,
        workspace: m.Infra.WorkspaceSpec | None = None,
        project_patterns: Sequence[str] = (),
    ) -> tuple[m.Infra.ScaffoldGitignoreSectionSpec, ...]:
        """Derive the ordered ``.ignore`` sections for one project.

        Single owner of the section list: the profile-filtered SSOT sections,
        the workspace-root subproject whitelist derived from the live topology,
        the layout override additions and the repository-owned patterns. Every
        renderer of ``base/ignore.j2`` (conform planning, the layout engine,
        ``codegen new``) consumes this projection, so the layout gate can never
        demand a pattern that ``make gen`` does not materialize.

        Returns:
            The resulting ``tuple[m.Infra.ScaffoldGitignoreSectionSpec, ...],``.

        """
        sections = [
            section
            for section in codegen.ignore_sections
            if not section.profiles or profile in section.profiles
        ]
        # The deny-all root policy (`/*` + `/*/`) would swallow every governed
        # subproject directory, so their whitelist is DERIVED from the live workspace
        # topology instead of a hardcoded name glob: declaring a subproject in
        # local .gitmodules is the single source that makes it trackable.
        # Nested paths need every ancestor unignored, otherwise git never
        # descends far enough to reach the subproject itself. Only the
        # workspace root carries that policy; a subproject never does.
        member_patterns: list[str] = []
        if workspace is not None and profile is c.Infra.MakeProfile.WORKSPACE:
            for declared_repository in workspace.subprojects:
                parts = declared_repository.path.as_posix().strip("/").split("/")
                # Every ancestor is unignored so git can descend into the
                # subproject, then its contents are unignored with the `/**` form.
                prefixes = [
                    "/".join(parts[:depth]) for depth in range(1, len(parts) + 1)
                ]
                candidates = [f"!/{prefix}/" for prefix in prefixes]
                candidates.append(f"!/{prefixes[-1]}/**")
                for pattern in candidates:
                    if pattern not in member_patterns:
                        member_patterns.append(pattern)
        if member_patterns:
            sections.append(
                m.Infra.ScaffoldGitignoreSectionSpec(
                    name="WHITELIST: governed workspace subprojects (derived)",
                    patterns=tuple(member_patterns),
                ),
            )
        if project_name is not None:
            override = codegen.layout.project_overrides.get(project_name)
            if override is not None and override.ignore_additions:
                sections.append(
                    m.Infra.ScaffoldGitignoreSectionSpec(
                        name=c.Infra.GITIGNORE_LAYOUT_SECTION_NAME,
                        patterns=override.ignore_additions,
                    ),
                )
        if project_patterns:
            # The repository owns the ignore patterns the fleet scaffold cannot
            # know (local caches, generated runtime state); they are declared in
            # its own config/*.yaml and appended as one derived section.
            sections.append(
                m.Infra.ScaffoldGitignoreSectionSpec(
                    name=c.Infra.GITIGNORE_PROJECT_SECTION_NAME,
                    patterns=tuple(project_patterns),
                ),
            )
        sections.extend(FlextInfraUtilitiesGitignore._runtime_ignore_sections(codegen))
        return tuple(sections)

    @staticmethod
    def _runtime_ignore_sections(
        codegen: m.Infra.CodegenConfigSpec,
    ) -> tuple[m.Infra.ScaffoldGitignoreSectionSpec, ...]:
        """Declare final ignore precedence for precisely the runtime-local artifacts.

        Returns:
            The single derived policy section or an empty declaration.

        """
        local_projections = tuple(
            f"/{item.path.as_posix()}"
            for item in sorted(codegen.managed_file_specs, key=lambda item: item.path)
            if item.tracking == "runtime-local"
        )
        if local_projections:
            return (
                m.Infra.ScaffoldGitignoreSectionSpec(
                    name="RUNTIME: local projections (derived)",
                    patterns=local_projections,
                ),
            )
        return ()


__all__: list[str] = ["FlextInfraUtilitiesGitignore"]
