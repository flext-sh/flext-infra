"""Release reporting utilities for the u.Infra MRO chain."""

from __future__ import annotations

from pathlib import Path

from flext_cli import u

from flext_infra import c, m, p, r, t
from flext_infra._utilities.base import FlextInfraUtilitiesBase


class FlextInfraUtilitiesRelease:
    """Release notes and changelog utility methods exposed via u.Infra."""

    @staticmethod
    def resolve_phase_names(phase: str) -> t.StrSequence:
        """Expand release phase selectors to the canonical ordered phase list."""
        if phase == c.Infra.RELEASE_PHASE_ALL:
            return tuple(c.Infra.ReleasePhase)
        return FlextInfraUtilitiesBase.normalize_cli_values(phase)

    @staticmethod
    def generate_notes(
        version: str,
        tag: str,
        project_list: t.SequenceOf[m.Infra.ProjectInfo],
        changes: str,
        output_path: Path,
    ) -> p.Result[bool]:
        """Generate release notes markdown from release context."""
        lines: t.MutableSequenceOf[str] = [
            f"# Release {tag}",
            "",
            "## Status",
            "",
            "- Quality: Alpha",
            "- Usage: Non-production",
            "",
            "## Scope",
            "",
            f"- Workspace release version: {version}",
            f"- Projects packaged: {len(project_list) + 1}",
            "",
            "## Projects impacted",
            "",
            "- root",
        ]
        lines.extend(f"- {proj.name}" for proj in project_list)
        lines.extend([
            "",
            "## Changes since last tag",
            "",
            changes or "- Initial tagged release",
            "",
            "## Verification",
            "",
            "- make rel INTERACTIVE=0 CREATE_BRANCHES=0 RELEASE_PHASE=all",
            "- make val VALIDATE_SCOPE=workspace",
            "- make build",
        ])
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            u.write_file(
                output_path,
                "\n".join(lines).rstrip() + "\n",
                encoding=c.Cli.ENCODING_DEFAULT,
            )
            u.fetch_logger(__name__).info(
                "release_notes_written", path=str(output_path)
            )
            return r[bool].ok(True)
        except OSError as exc:
            return r[bool].fail(f"failed to write release notes: {exc}")

    @staticmethod
    def update_changelog(
        workspace_root: Path, version: str, tag: str, notes_path: Path
    ) -> p.Result[bool]:
        """Update docs/changelog and docs/releases entries."""
        docs = workspace_root / c.Infra.DIR_DOCS
        changelog_path = docs / "CHANGELOG.md"
        latest_path = docs / "releases" / "latest.md"
        tagged_path = docs / "releases" / f"{tag}.md"
        try:
            FlextInfraUtilitiesRelease._write_changelog_files(
                changelog_path=changelog_path,
                latest_path=latest_path,
                tagged_path=tagged_path,
                version=version,
                tag=tag,
                notes_path=notes_path,
            )
        except OSError as exc:
            return r[bool].fail_op("changelog update", exc)
        return r[bool].ok(True)

    @staticmethod
    def _write_changelog_files(
        *,
        changelog_path: Path,
        latest_path: Path,
        tagged_path: Path,
        version: str,
        tag: str,
        notes_path: Path,
    ) -> None:
        """Write changelog and release note files."""
        notes_text = notes_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
        existing = (
            changelog_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
            if changelog_path.exists()
            else "# Changelog\n\n"
        )
        updated = FlextInfraUtilitiesRelease._updated_changelog(
            existing=existing, version=version, tag=tag
        )
        changelog_path.parent.mkdir(parents=True, exist_ok=True)
        u.write_file(changelog_path, updated, encoding=c.Cli.ENCODING_DEFAULT)
        latest_path.parent.mkdir(parents=True, exist_ok=True)
        u.write_file(latest_path, notes_text, encoding=c.Cli.ENCODING_DEFAULT)
        u.write_file(tagged_path, notes_text, encoding=c.Cli.ENCODING_DEFAULT)
        u.fetch_logger(__name__).info(
            "release_changelog_written", path=str(changelog_path)
        )
        u.fetch_logger(__name__).info(
            "release_tagged_notes_written", path=str(tagged_path)
        )

    @staticmethod
    def _updated_changelog(*, existing: str, version: str, tag: str) -> str:
        """Return changelog text with a release section for the version."""
        date = u.now().date().isoformat()
        heading = f"## {version} - "
        section = f"{heading}{date}\n\n- Workspace release tag: `{tag}`\n- Status: Alpha, non-production\n\nFull notes: `docs/releases/{tag}.md`\n\n"
        if heading in existing:
            return existing
        marker = "# Changelog\n\n"
        if marker in existing:
            return existing.replace(marker, marker + section, 1)
        return "# Changelog\n\n" + section + existing


__all__: list[str] = ["FlextInfraUtilitiesRelease"]
