"""Repository-local codegen extension contracts."""

from __future__ import annotations

import tomllib
from pathlib import Path

from flext_infra import c, config
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm


class TestsCodegenCatalogExtensions:
    """Prove generic extensions without a repository registry or second manifest."""

    def test_beads_toolchain_uses_an_immutable_release_selector(self) -> None:
        selector = config.Infra.codegen.toolchain.beads.version

        version_parts = selector.split(".")
        is_semver = len(version_parts) == 3 and all(
            part.isdecimal() for part in version_parts
        )
        is_commit = len(selector) == 40 and all(
            char in "0123456789abcdef" for char in selector
        )
        tm.that(is_semver or is_commit, eq=True)

    def test_bootstrap_toolchain_uses_immutable_release_selectors(self) -> None:
        toolchain = config.Infra.codegen.toolchain

        mise_parts = toolchain.mise_version.split(".")
        tm.that(len(mise_parts), eq=3)
        tm.that(all(part.isdecimal() for part in mise_parts), eq=True)
        beads_version = toolchain.beads.version
        beads_parts = beads_version.split(".")
        beads_is_semver = len(beads_parts) == 3 and all(
            part.isdecimal() for part in beads_parts
        )
        beads_is_commit = len(beads_version) == 40 and all(
            char in "0123456789abcdef" for char in beads_version
        )
        tm.that(beads_is_semver or beads_is_commit, eq=True)

    def test_setup_provisions_only_and_gen_owns_conformance(self) -> None:
        """``make setup`` provisions tooling; ``make gen`` owns conformance."""
        template = (
            Path(__file__).parents[3]
            / "src"
            / "flext_infra"
            / "templates"
            / "project"
            / "base"
            / "Makefile.j2"
        )
        content = template.read_text(encoding="utf-8")
        tm.that("_builtin_setup_conform" in content, eq=False)
        setup_env = content.split("_builtin_setup_environment:", 1)[1]
        tm.that("codegen conform" in setup_env.split("\n\n", 1)[0], eq=False)
        tm.that("_builtin_gen_check:" in content, eq=True)
        tm.that("_builtin_gen_apply:" in content, eq=True)
        verb_names = {verb.name for verb in config.Infra.codegen.make.verbs}
        tm.that("conform" in verb_names, eq=False)

    def test_conform_has_no_global_workspace_catalog_validator(self) -> None:
        tm.that(
            hasattr(FlextInfraCodegenConform, "_validate_workspace_catalog"), eq=False
        )

    def test_codegen_composes_project_mise_tools_through_toml(
        self, tmp_path: Path
    ) -> None:
        """The codegen artifact boundary consumes the project YAML overlay."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "tooling.yaml").write_text(
            "ManagedArtifacts:\n  Mise:\n    tools:\n      node: '26'\n",
            encoding="utf-8",
        )

        result = FlextInfraCodegenConform._compose_project_artifact(  # ruff: ignore[private-member-access]
            tmp_path, c.Infra.MISE_TOML_FILENAME, '[tools]\npython = "3.13"\n'
        )

        rendered = tomllib.loads(tm.ok(result))
        tm.that(rendered["tools"], eq={"python": "3.13", "node": "26"})


__all__: tuple[str, ...] = ()
