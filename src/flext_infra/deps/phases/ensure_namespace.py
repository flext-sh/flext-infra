"""Phase: Ensure namespace discovery is reflected across project tooling tables."""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraToml, c, m, t, u


class FlextInfraEnsureNamespaceToolingPhase:
    """Ensure namespace discovery is reflected across project tooling tables."""

    def apply(self, doc: t.Cli.TomlDocument, *, path: Path) -> t.StrSequence:
        detected = sorted(
            {
                *u.Infra.discover_first_party_namespaces(path.parent),
                *u.Infra.workspace_dep_namespaces(doc),
            },
        )
        if not detected:
            return []
        phase = (
            m.Infra.TomlPhaseConfig
            .Builder("namespace-tooling")
            .table(c.Infra.DEPTRY)
            .list(c.Infra.KNOWN_FIRST_PARTY_UNDERSCORE, detected)
            .build()
        )
        return FlextInfraToml.apply_phases(doc, phase)


__all__ = ["FlextInfraEnsureNamespaceToolingPhase"]
