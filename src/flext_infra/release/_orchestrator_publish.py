"""Release publish phase: notes, changelog, tag, optional push — extracted concern."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, p, u

logger = u.fetch_logger(__name__)


class FlextInfraReleaseOrchestratorPublishMixin:
    """Publish-phase implementation (parent of the release-phases class).

    Delegates note generation and release side effects to upstream dispatch policy.
    """

    if TYPE_CHECKING:

        def _generate_notes(
            self, ctx: p.Infra.ReleasePhaseDispatchConfig, output_path: Path
        ) -> p.Result[bool]: ...

        def _create_tag(self, workspace_root: Path, tag: str) -> p.Result[bool]: ...

        def _push_release(self, workspace_root: Path, tag: str) -> p.Result[bool]: ...

    def phase_publish(self, ctx: p.Infra.ReleasePhaseDispatchConfig) -> p.Result[bool]:
        """Execute publish phase: notes, changelog, tag, optional push."""
        workspace_root = ctx.workspace_root
        tag = ctx.tag
        notes_dir = (
            u.Cli.resolve_report_dir(
                workspace_root, c.Infra.PROJECT, c.Infra.RK_RELEASE
            )
            / tag
        )
        try:
            notes_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return r[bool].fail_op("report dir creation", exc)
        notes_path = notes_dir / "RELEASE_NOTES.md"
        notes_result = self._generate_notes(ctx, notes_path)
        if notes_result.failure:
            return notes_result
        if not notes_path.exists():
            return r[bool].fail(f"release notes generation did not create {notes_path}")
        if not ctx.dry_run:
            apply_result = self._publish_apply(
                workspace_root=workspace_root,
                version=ctx.version,
                tag=tag,
                notes_path=notes_path,
                push=ctx.push,
            )
            if apply_result.failure:
                return apply_result
        logger.info("release_phase_publish", tag=tag, dry_run=ctx.dry_run)
        return r[bool].ok(True)

    def _publish_apply(
        self,
        *,
        workspace_root: Path,
        version: str,
        tag: str,
        notes_path: Path,
        push: bool,
    ) -> p.Result[bool]:
        """Apply changelog, tag, and optional push for publish phase."""
        changelog_result = u.Infra.update_changelog(
            workspace_root, version, tag, notes_path
        )
        if changelog_result.failure:
            return changelog_result
        tag_result = self._create_tag(workspace_root, tag)
        if tag_result.failure:
            return tag_result
        if push:
            push_result = self._push_release(workspace_root, tag)
            if push_result.failure:
                return push_result
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraReleaseOrchestratorPublishMixin"]
