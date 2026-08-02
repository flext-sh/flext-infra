"""Public contract for governed repository-root artifact ownership."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, config
from flext_tests import tm


class TestsRootArtifactOwnership:
    """Prove codegen config is the sole root-artifact ownership catalog."""

    def test_toolchain_surfaces_cover_every_repository_profile(self) -> None:
        """Every generated repository consumes the configured toolchain surfaces."""
        entries = tuple(
            entry
            for entry in config.Infra.codegen.surfaces.entries
            if entry.render_context == "toolchain"
        )

        tm.that(entries, empty=False)
        for entry in entries:
            tm.that(set(entry.profiles), eq=set(c.Infra.MakeProfile))

    def test_governed_artifacts_have_one_explicit_policy(self) -> None:
        configured = config.Infra.codegen.surfaces.entries
        paths = tuple(item.path for item in configured)

        tm.that(len(paths), eq=len(set(paths)))
        github_surfaces = {
            item.path: item
            for item in configured
            if Path(item.path).parts[:1] == (".github",)
        }
        tm.that(github_surfaces, empty=False)
        for owned in github_surfaces.values():
            tm.that(owned.policy, eq="full")

    def test_every_packaged_github_template_is_declared(self) -> None:
        """Keep the packaged GitHub tree and typed render manifest bijective."""
        surface_catalog = config.Infra.codegen.surfaces
        template_root = (
            Path(__file__).parents[3]
            / "src"
            / "flext_infra"
            / "templates"
            / surface_catalog.root
        )
        physical = {
            path.relative_to(template_root).as_posix()
            for path in (template_root / "base" / ".github").rglob("*.j2")
        }
        declared = {
            entry.source.as_posix()
            for entry in surface_catalog.entries
            if entry.source is not None and Path(entry.path).parts[:1] == (".github",)
        }

        tm.that(physical, eq=declared)


__all__: list[str] = []
