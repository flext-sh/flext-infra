"""Per-project uv cooldown overlay for repositories with a security floor."""

from __future__ import annotations

from flext_infra import c, config, m, u
from flext_tests import tm
from tests import u as test_u


class TestCodegenUvExcludeNewerOverlay:
    """Validate the public conform surface against the repository policy overlay."""

    SOURCE = (
        '[project]\nname = "flext-demo"\nversion = "0.12.0.dev0"\n'
        'requires-python = ">=3.13,<3.14"\n'
    )

    @staticmethod
    def _repository() -> m.Infra.WorkspaceSpec:
        repository = test_u.Tests.repository_ref(config.Infra.name)
        return m.Infra.WorkspaceSpec(
            name=repository.distribution, repository=repository
        )

    @classmethod
    def _render(cls, *, overlay_window: str | None) -> str:
        repository = cls._repository()
        return tm.ok(
            u.Infra.pyproject_conform(
                cls.SOURCE,
                providers=config.Infra.codegen.providers,
                workspace=repository,
                workspace_mode=c.Infra.MakeProfile.STANDALONE,
                toolchain=config.Infra.codegen.toolchain,
                required_dev_dependencies=(),
                uv_exclude_newer=overlay_window,
            )
        )

    def test_absent_overlay_keeps_the_fleet_cooldown(self) -> None:
        rendered = self._render(overlay_window=None)
        tm.that(
            rendered,
            has=(
                f'exclude-newer = "{config.Infra.codegen.toolchain.uv_exclude_newer}"'
            ),
        )

    def test_overlay_pins_the_absolute_cutoff(self) -> None:
        pinned = "2026-08-05T00:00:00Z"
        rendered = self._render(overlay_window=pinned)
        tm.that(rendered, has=f'exclude-newer = "{pinned}"')
        tm.that(
            rendered,
            lacks=(
                f'exclude-newer = "{config.Infra.codegen.toolchain.uv_exclude_newer}"'
            ),
        )


__all__: tuple[str, ...] = ()
