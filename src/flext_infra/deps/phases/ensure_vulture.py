"""Phase: ensure Vulture production-reachability configuration.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import m, p, t
from flext_infra.deps.toml_phase import FlextInfraTomlPhaseService


class FlextInfraEnsureVultureConfigPhase:
    """Propagate the validated Vulture policy to every project."""

    def __init__(self, vulture_config: p.Infra.VultureConfig) -> None:
        """Store the canonical tooling document."""
        self._vulture_config = vulture_config

    def _phase(self) -> p.Cli.TomlPhaseConfig:
        """Build the config-owned Vulture TOML phase."""
        # mro-j47u: reachability policy is data; projects receive no local branch.
        vulture = self._vulture_config
        return (
            m.Cli.TomlPhaseConfig
            .Builder("vulture")
            .table("vulture")
            .deprecated("min-confidence")
            .list("exclude", vulture.exclude)
            # mro-j47u (codex): Vulture TOML uses parser keys, not CLI flags.
            .value("min_confidence", vulture.min_confidence)
            .list("paths", vulture.paths)
            .value("verbose", vulture.verbose)
            .build()
        )

    def apply(self, doc: t.Cli.TomlDocument) -> t.StrSequence:
        """Apply Vulture policy to one TOML document."""
        return FlextInfraTomlPhaseService.apply_phases(doc, self._phase())

    def apply_payload(self, payload: t.MutableJsonMapping) -> t.StrSequence:
        """Apply Vulture policy to one normalized payload."""
        return FlextInfraTomlPhaseService.apply_payload_phases(payload, self._phase())


__all__: list[str] = ["FlextInfraEnsureVultureConfigPhase"]
