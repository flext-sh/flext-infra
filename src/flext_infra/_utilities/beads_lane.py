"""Beads lane registry adapter for the make work saga."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import u
from flext_infra._utilities.git import FlextInfraUtilitiesGit
from flext_infra.models import m

_BD_UPDATE_BASE_ARGV_LENGTH = 2

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraUtilitiesBeadsLane:
    """Shell `bd` for lane metadata, labels, and evidence notes."""

    @classmethod
    def beads_resolve_root(cls, hint: Path | None = None) -> p.Result[Path]:
        """Resolve the Beads project root that owns the workspace ledger.

        Prefer the checkout under ``hint`` (git toplevel, then hint, then
        parents) when it declares `.beads/config.yaml`, so member projects
        with their own tracker stay local. Fall back to the Git superproject
        only when the member has no Beads config, so orphan members still
        reach the workspace tracker (`bd -C <workspace>`). Uses typed Git
        root reports — never raw argv helpers.
        """
        start = (hint or Path.cwd()).expanduser().resolve()
        candidates: list[Path] = []
        request = m.Infra.GitRepoRequest(repo_root=start)
        top = FlextInfraUtilitiesGit.git_show_toplevel(request)
        if top.success:
            candidates.append(top.value.workspace_root)
        candidates.append(start)
        candidates.extend(start.parents)
        superproject = FlextInfraUtilitiesGit.git_superproject_working_tree(request)
        if superproject.success and superproject.value.text.strip():
            candidates.append(Path(superproject.value.text.strip()).resolve())
        seen: set[Path] = set()
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            if (resolved / ".beads" / "config.yaml").is_file():
                return r.ok(resolved)
        return r.fail(f"no Beads config (.beads/config.yaml) found from {start}")

    @classmethod
    def _bd_command(
        cls, *parts: str, root: Path | None = None
    ) -> p.Result[tuple[str, ...]]:
        resolved = cls.beads_resolve_root(root)
        if resolved.failure:
            return r.fail(resolved.error or "failed to resolve Beads root")
        return r.ok(("bd", "-C", str(resolved.value), *parts))

    @classmethod
    def beads_show_json(
        cls, bead_id: str, *, root: Path | None = None
    ) -> p.Result[dict[str, object]]:
        """Return one issue as a JSON object."""
        cleaned = bead_id.strip()
        if not cleaned:
            return r.fail("beads show requires a non-empty bead id")
        command = cls._bd_command("show", cleaned, "--json", root=root)
        if command.failure:
            return r.fail(command.error or "failed to build bd show command")
        captured = u.Cli.capture(command.value)
        if captured.failure:
            return r.fail(captured.error or f"bd show failed for {cleaned}")
        try:
            payload = json.loads(captured.value)
        except json.JSONDecodeError as exc:
            return r.fail(f"bd show returned invalid JSON: {exc}")
        if isinstance(payload, list):
            if not payload or not isinstance(payload[0], dict):
                return r.fail(f"bd show returned empty list for {cleaned}")
            return r.ok(payload[0])
        if not isinstance(payload, dict):
            return r.fail(f"bd show returned unexpected JSON for {cleaned}")
        return r.ok(payload)

    @classmethod
    def beads_update_lane(
        cls,
        bead_id: str,
        *,
        metadata: dict[str, str] | None = None,
        labels: tuple[str, ...] = (),
        notes: str | None = None,
        claim: bool = False,
        root: Path | None = None,
    ) -> p.Result[str]:
        """Update lane registry fields on one bead."""
        cleaned = bead_id.strip()
        if not cleaned:
            return r.fail("beads update requires a non-empty bead id")
        parts: list[str] = ["update", cleaned]
        if claim:
            parts.append("--claim")
        if metadata:
            for key, value in metadata.items():
                parts.extend(("--set-metadata", f"{key}={value}"))
        for label in labels:
            parts.extend(("--add-label", label))
        if notes:
            parts.extend(("--append-notes", notes))
        if len(parts) == _BD_UPDATE_BASE_ARGV_LENGTH:
            return r.fail("beads update requires metadata, labels, notes, or claim")
        command = cls._bd_command(*parts, root=root)
        if command.failure:
            return r.fail(command.error or "failed to build bd update command")
        ran = u.Cli.run(command.value)
        if ran.failure:
            return r.fail(ran.error or f"bd update failed for {cleaned}")
        if ran.value.exit_code != 0:
            detail = (ran.value.stderr or ran.value.stdout).strip()
            return r.fail(detail or f"bd update failed for {cleaned}")
        return r.ok(cleaned)


__all__: list[str] = ["FlextInfraUtilitiesBeadsLane"]
