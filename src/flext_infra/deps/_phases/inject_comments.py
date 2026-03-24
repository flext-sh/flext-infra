"""Phase: Inject managed/custom markers into pyproject.toml."""

from __future__ import annotations

from collections.abc import MutableSequence

from flext_core import FlextTypes as t

from flext_infra import c


class FlextInfraInjectCommentsPhase:
    """Inject managed/custom markers into pyproject.toml."""

    @staticmethod
    def _is_section_header(line: str) -> bool:
        stripped = line.strip()
        return stripped.startswith("[") and stripped.endswith("]")

    @staticmethod
    def _managed_marker_lines() -> set[str]:
        markers = {marker for _section_prefix, marker in c.Infra.COMMENT_MARKERS}
        markers.add(c.Infra.DEV_OPTIONAL_DEPS_MARKER)
        markers.add(c.Infra.LEGACY_AUTO_MARKER)
        markers.add(c.Infra.LEGACY_AUTO_BANNER_LINE)
        markers.update(c.Infra.BANNER.splitlines())
        return markers

    @staticmethod
    def _marker_for_section(section_header: str) -> str | None:
        for section_prefix, marker in c.Infra.COMMENT_MARKERS:
            if section_header.startswith(section_prefix):
                return marker
        return None

    @classmethod
    def _strip_managed_lines(
        cls,
        lines: t.StrSequence,
    ) -> tuple[t.StrSequence, t.StrSequence]:
        changes: MutableSequence[str] = []
        managed_lines = cls._managed_marker_lines()
        cleaned: MutableSequence[str] = []
        skip_broken_group_section = False
        broken_removed = False
        for line in lines:
            stripped = line.strip()
            if skip_broken_group_section:
                if cls._is_section_header(line):
                    skip_broken_group_section = False
                else:
                    continue
            # Remove legacy banner variants so canonical banner can be re-injected.
            if stripped.startswith("# Sections with [MANAGED] are enforced"):
                continue
            if stripped == c.Infra.LEGACY_AUTO_BANNER_LINE:
                continue
            if stripped == "[group.dev.dependencies]":
                skip_broken_group_section = True
                broken_removed = True
                continue
            if stripped in managed_lines:
                continue
            cleaned.append(line)
        if broken_removed:
            changes.append("broken [group.dev.dependencies] section removed")
        return cleaned, changes

    @staticmethod
    def _inject_dev_markers(
        out: MutableSequence[str],
        changes: MutableSequence[str],
        emitted_markers: set[str],
    ) -> None:
        managed_marker = c.Infra.DEV_OPTIONAL_DEPS_MARKER
        if managed_marker not in emitted_markers:
            out.append(managed_marker)
            changes.append("marker injected for optional-dependencies.dev")
            emitted_markers.add(managed_marker)

    def apply(self, rendered: str) -> tuple[str, t.StrSequence]:
        changes: MutableSequence[str] = []
        lines = rendered.splitlines()
        cleaned_lines, cleanup_changes = self._strip_managed_lines(lines)
        changes.extend(cleanup_changes)
        banner_lines = c.Infra.BANNER.splitlines()
        out: MutableSequence[str] = [*banner_lines]
        if lines[: len(banner_lines)] != banner_lines:
            changes.append("managed banner injected")
        emitted_markers = set[str]()
        for line in cleaned_lines:
            stripped = line.strip()
            marker = self._marker_for_section(stripped)
            if marker and marker not in emitted_markers:
                out.append(marker)
                changes.append(f"marker injected for {stripped}")
                emitted_markers.add(marker)
            if stripped == "[project.optional-dependencies]" or stripped.startswith(
                "optional-dependencies.dev",
            ):
                self._inject_dev_markers(out, changes, emitted_markers)
            out.append(line)
        return ("\n".join(out).rstrip() + "\n", changes)


__all__ = ["FlextInfraInjectCommentsPhase"]
