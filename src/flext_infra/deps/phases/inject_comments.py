"""Phase: Inject managed/custom markers into pyproject.toml."""

from __future__ import annotations

from collections.abc import (
    MutableSequence,
)

from flext_infra import c, t


class FlextInfraInjectCommentsPhase:
    """Inject managed/custom markers into pyproject.toml."""

    @staticmethod
    def _is_section_header(line: str) -> bool:
        stripped = line.strip()
        return stripped.startswith("[") and stripped.endswith("]")

    @staticmethod
    def _managed_marker_lines() -> t.Infra.StrSet:
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
                return str(marker)
        return None

    @classmethod
    def _strip_managed_lines(
        cls,
        lines: t.StrSequence,
    ) -> t.Infra.Pair[t.StrSequence, t.StrSequence]:
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
        emitted_markers: t.Infra.StrSet,
    ) -> None:
        managed_marker = c.Infra.DEV_OPTIONAL_DEPS_MARKER
        if managed_marker not in emitted_markers:
            out.append(managed_marker)
            changes.append("marker injected for optional-dependencies.dev")
            emitted_markers.add(managed_marker)

    @staticmethod
    def _collapse_blank_lines(lines: t.StrSequence) -> t.StrSequence:
        """Collapse repeated blank lines into a single canonical separator."""
        normalized: MutableSequence[str] = []
        previous_blank = False
        for line in lines:
            is_blank = not line.strip()
            if is_blank and previous_blank:
                continue
            normalized.append(line)
            previous_blank = is_blank
        return normalized

    def apply(self, rendered: str) -> t.Infra.Pair[str, t.StrSequence]:
        """Inject managed banner/markers and return updated TOML plus change messages."""
        changes: MutableSequence[str] = []
        lines = rendered.splitlines()
        cleaned_lines, cleanup_changes = self._strip_managed_lines(lines)
        changes.extend(cleanup_changes)
        banner_lines = c.Infra.BANNER.splitlines()
        out: MutableSequence[str] = [*banner_lines]
        if lines[: len(banner_lines)] != banner_lines:
            changes.append("managed banner injected")
        emitted_markers: set[str] = set()
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
        updated = "\n".join(self._collapse_blank_lines(out)).rstrip() + "\n"
        original = rendered.rstrip() + "\n"
        if updated == original:
            return (updated, [])
        return (updated, changes)


__all__: list[str] = ["FlextInfraInjectCommentsPhase"]
