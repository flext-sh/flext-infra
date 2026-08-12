"""Per-project uv cooldown overlay for repositories with a security floor.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import c, config, m, u
from flext_tests import tm
from tests import u as test_u


class TestCodegenUvExcludeNewerOverlay:
    """Resolve ``[tool.uv].exclude-newer`` from the repository policy overlay.

    The fleet default is a rolling window. A repository that declares a
    security floor through ``override-dependencies`` cannot use it: once the
    pinned version ages past the window it is excluded, the floor becomes
    unsatisfiable, and resolution fails without any code change. Such a
    repository declares an absolute cutoff through the overlay instead of
    hand-editing the generated ``pyproject.toml``.
    """

    SOURCE = (
        '[project]\nname = "flext-demo"\nversion = "0.12.0.dev0"\n'
        'requires-python = ">=3.13,<3.14"\n'
    )

    @staticmethod
    def _workspace(*, overlay_window: str | None) -> m.Infra.WorkspaceSpec:
        """Build a standalone workspace, optionally carrying the overlay."""
        repository = test_u.Tests.repository_ref(config.Infra.name)
        overlays = (
            (
                m.Infra.RepositoryPolicyOverlaySpec(
                    project=repository.distribution, uv_exclude_newer=overlay_window
                ),
            )
            if overlay_window is not None
            else ()
        )
        return m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name=repository.distribution,
            repository=repository,
            repository_policy_overlays=overlays,
        )

    @classmethod
    def _render(cls, *, overlay_window: str | None) -> str:
        """Conform a minimal pyproject the way codegen does for a repository."""
        workspace = cls._workspace(overlay_window=overlay_window)
        return tm.ok(
            u.Infra.pyproject_conform(
                cls.SOURCE,
                providers=config.Infra.codegen.providers,
                workspace=workspace,
                workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
                toolchain=config.Infra.codegen.toolchain,
                required_dev_dependencies=(),
                uv_exclude_newer=overlay_window,
            )
        )

    def test_absent_overlay_keeps_the_fleet_cooldown(self) -> None:
        """Without the overlay the generated cooldown is the fleet window."""
        rendered = self._render(overlay_window=None)
        fleet = config.Infra.codegen.toolchain.uv_exclude_newer
        tm.that(rendered, has=f'exclude-newer = "{fleet}"')

    def test_overlay_pins_the_absolute_cutoff(self) -> None:
        """A declared overlay replaces the rolling fleet default."""
        pinned = "2026-08-05T00:00:00Z"
        rendered = self._render(overlay_window=pinned)
        fleet = config.Infra.codegen.toolchain.uv_exclude_newer
        tm.that(rendered, has=f'exclude-newer = "{pinned}"')
        tm.that(rendered, lacks=f'exclude-newer = "{fleet}"')

    def test_overlay_declares_an_absolute_instant_not_a_window(self) -> None:
        """The pinned form is an instant, so it never ages past a floor."""
        pinned = "2026-08-05T00:00:00Z"
        rendered = self._render(overlay_window=pinned)
        tm.that(rendered, has="exclude-newer")
        tm.that(rendered, match=r'exclude-newer = "\d{4}-\d{2}-\d{2}T[\d:]+Z"')
