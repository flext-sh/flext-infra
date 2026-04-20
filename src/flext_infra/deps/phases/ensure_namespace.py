"""Phase: Ensure namespace discovery is reflected across project tooling tables."""

from __future__ import annotations

from collections.abc import (
    MutableMapping,
)
from pathlib import Path

from flext_infra import FlextInfraPhaseEngine, c, m, t, u


class FlextInfraEnsureNamespaceToolingPhase:
    """Ensure namespace discovery is reflected across project tooling tables."""

    def _phase(self, detected: t.StrSequence) -> m.Infra.TomlPhaseConfig:
        """Build the deptry namespace phase for one detected namespace set."""
        return (
            m.Infra.TomlPhaseConfig
            .Builder("namespace-tooling")
            .table(c.Infra.DEPTRY)
            .list(c.Infra.KNOWN_FIRST_PARTY_UNDERSCORE, detected)
            .build()
        )

    def apply(self, doc: t.Cli.TomlDocument, *, path: Path) -> t.StrSequence:
        """Apply detected first-party namespaces to dependency tooling tables."""
        detected = sorted(
            {
                *u.Infra.discover_first_party_namespaces(path.parent),
                *u.Infra.workspace_dep_namespaces(doc),
            },
        )
        if not detected:
            return []
        return FlextInfraPhaseEngine.apply_phases(doc, self._phase(detected))

    def apply_payload(
        self,
        payload: MutableMapping[str, t.Cli.JsonValue],
        *,
        path: Path,
    ) -> t.StrSequence:
        """Apply detected first-party namespaces to one normalized payload."""
        detected = sorted(
            {
                *u.Infra.discover_first_party_namespaces(path.parent),
                *u.Infra.workspace_dep_namespaces_from_payload(payload),
            },
        )
        if not detected:
            return []
        return FlextInfraPhaseEngine.apply_payload_phases(
            payload, self._phase(detected)
        )


__all__: list[str] = ["FlextInfraEnsureNamespaceToolingPhase"]
