"""Single owner of the workspace manifest path and the fleet-umbrella question.

Every consumer that needs to know where the workspace manifest lives, or
whether a checkout declares itself a fleet umbrella, asks here. The expression
existed in five places before this module, and the sixth copy asked the wrong
file: it tested the Beads override, which every project carries, so every
standalone project was classified as an umbrella. That misrouting silently
dropped each new project's README and project docs.

One owner exists so a seventh copy cannot be written.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .. import c

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraUtilitiesWorkspaceManifest:
    """Resolve the workspace manifest and classify a checkout by it."""

    @staticmethod
    def workspace_manifest_path(repository_root: Path) -> Path:
        """Return where the workspace manifest lives for one checkout."""
        return repository_root / c.CONFIG_DIR_NAME / c.Infra.WORKSPACE_MANIFEST_FILENAME

    @classmethod
    def is_fleet_umbrella(cls, repository_root: Path) -> bool:
        """Whether this checkout declares itself a fleet umbrella.

        The handwritten workspace manifest is the only signal. A Beads override
        is explicitly not one: every project carries ``config/beads.yaml``,
        standalone or not, so reading it here classified every project as an
        umbrella and collapsed its docs scope onto an identical root scope.
        """
        return cls.workspace_manifest_path(repository_root).is_file()


__all__: list[str] = ["FlextInfraUtilitiesWorkspaceManifest"]
