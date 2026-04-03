"""Phase: Ensure namespace discovery is reflected across project tooling tables."""

from __future__ import annotations

from collections.abc import MutableSequence
from pathlib import Path

import tomlkit
from tomlkit.container import Container
from tomlkit.items import Item, Table

from flext_infra import c, t, u


class FlextInfraEnsureNamespaceToolingPhase:
    """Ensure namespace discovery is reflected across project tooling tables."""

    def apply(self, doc: tomlkit.TOMLDocument, *, path: Path) -> t.StrSequence:
        changes: MutableSequence[str] = []
        detected = sorted(
            {
                *u.discover_first_party_namespaces(path.parent),
                *u.workspace_dep_namespaces(doc),
            },
        )
        if not detected:
            return changes
        tool: Item | Container | None = None
        if c.Infra.TOOL in doc:
            tool = doc[c.Infra.TOOL]
        if not isinstance(tool, Table):
            tool = tomlkit.table()
            doc[c.Infra.TOOL] = tool
        deptry = u.ensure_table(tool, c.Infra.DEPTRY)
        current_deptry = sorted(
            u.as_string_list(
                u.get(deptry, c.Infra.KNOWN_FIRST_PARTY_UNDERSCORE),
            ),
        )
        if current_deptry != detected:
            deptry[c.Infra.KNOWN_FIRST_PARTY_UNDERSCORE] = u.array(detected)
            changes.append(f"tool.deptry.known_first_party set to {detected}")
        return changes


__all__ = ["FlextInfraEnsureNamespaceToolingPhase"]
