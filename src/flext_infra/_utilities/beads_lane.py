"""Beads lane registry adapter for the make work saga."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import u

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraUtilitiesBeadsLane:
    """Shell `bd` for lane metadata, labels, and evidence notes."""

    @classmethod
    def beads_show_json(cls, bead_id: str) -> p.Result[dict[str, object]]:
        """Return one issue as a JSON object."""
        cleaned = bead_id.strip()
        if not cleaned:
            return r.fail("beads show requires a non-empty bead id")
        captured = u.Cli.capture(("bd", "show", cleaned, "--json"))
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
    ) -> p.Result[str]:
        """Update lane registry fields on one bead."""
        cleaned = bead_id.strip()
        if not cleaned:
            return r.fail("beads update requires a non-empty bead id")
        command: list[str] = ["bd", "update", cleaned]
        if claim:
            command.append("--claim")
        if metadata:
            for key, value in metadata.items():
                command.extend(("--set-metadata", f"{key}={value}"))
        for label in labels:
            command.extend(("--add-label", label))
        if notes:
            command.extend(("--append-notes", notes))
        base_command_length = 3  # bd update <id>
        if len(command) == base_command_length:
            return r.fail("beads update requires metadata, labels, notes, or claim")
        ran = u.Cli.run(tuple(command))
        if ran.failure:
            return r.fail(ran.error or f"bd update failed for {cleaned}")
        if ran.value.exit_code != 0:
            detail = (ran.value.stderr or ran.value.stdout).strip()
            return r.fail(detail or f"bd update failed for {cleaned}")
        return r.ok(cleaned)


__all__: list[str] = ["FlextInfraUtilitiesBeadsLane"]
