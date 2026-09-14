"""The fleet-umbrella question has exactly one owner and one signal.

Why this exists: the workspace-manifest path was re-derived in five places, and
a sixth copy asked the wrong file. It tested the Beads override, which every
project carries, so every standalone project was classified as a fleet umbrella.
That misrouting collapsed each project's docs scope onto an identical root scope
and silently dropped its README and project docs.

These cases pin the signal itself, independently of the docs generator, so the
classification cannot drift again.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from flext_tests import tm

from flext_infra import c, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraWorkspaceManifest:
    """Classification of a checkout as a fleet umbrella."""

    def test_invalid_manifest_cannot_expand_discovery(self, tmp_path: Path) -> None:
        """Invalid declarations fail before exclusions or refactor policy are used."""
        manifest = u.Infra.workspace_manifest_path(tmp_path)
        manifest.parent.mkdir(parents=True)
        manifest.write_text("version: invalid\n", encoding="utf-8")
        with pytest.raises(c.ValidationError):
            u.Infra.manifest_nonparticipant_paths(tmp_path)
        with pytest.raises(c.ValidationError):
            u.Infra.load_refactor_config(tmp_path)

    @staticmethod
    def _config_dir(root: Path) -> Path:
        """Create and return the checkout's config directory."""
        config = root / c.CONFIG_DIR_NAME
        config.mkdir(parents=True, exist_ok=True)
        return config

    def test_manifest_path_is_derived_from_the_declared_names(
        self, tmp_path: Path
    ) -> None:
        """The path is built from the configured directory and filename."""
        resolved = u.Infra.workspace_manifest_path(tmp_path)

        tm.that(resolved.name, eq=c.Infra.WORKSPACE_MANIFEST_FILENAME)
        tm.that(resolved.parent.name, eq=c.CONFIG_DIR_NAME)
        tm.that(resolved.parent.parent, eq=tmp_path)

    def test_a_checkout_without_the_manifest_is_not_an_umbrella(
        self, tmp_path: Path
    ) -> None:
        """Absence of the manifest is the ordinary case for a project."""
        tm.that(u.Infra.is_fleet_umbrella(tmp_path), eq=False)

    def test_the_manifest_alone_makes_a_checkout_an_umbrella(
        self, tmp_path: Path
    ) -> None:
        """The handwritten manifest is the signal."""
        manifest = TestsFlextInfraWorkspaceManifest._config_dir(tmp_path)
        (manifest / c.Infra.WORKSPACE_MANIFEST_FILENAME).write_text(
            "name: probe\n", encoding="utf-8"
        )

        tm.that(u.Infra.is_fleet_umbrella(tmp_path), eq=True)

    def test_a_beads_override_never_makes_a_checkout_an_umbrella(
        self, tmp_path: Path
    ) -> None:
        """The exact regression: every project carries the Beads override.

        Reading it here classified every standalone project as a fleet
        umbrella, which is what silently dropped their README and project docs.
        """
        config = TestsFlextInfraWorkspaceManifest._config_dir(tmp_path)
        (config / c.Infra.BEADS_CONFIG_FILENAME).write_text(
            "project: probe\n", encoding="utf-8"
        )

        tm.that(u.Infra.is_fleet_umbrella(tmp_path), eq=False)


__all__: list[str] = ["TestsFlextInfraWorkspaceManifest"]
