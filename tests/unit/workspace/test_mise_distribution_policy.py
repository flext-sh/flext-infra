"""Fleet-owned mise tool composition at its owner.

``codegen conform`` exclusively owns ``.mise.toml`` (workspace environment
sync stopped writing it when the toolchain transaction landed), so the
composition rule is proven against ``u.Infra.compose_mise_toml`` — the one
surface that turns a repository's ``config/*.yaml`` overlay into that file.
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import config, u


class TestsFlextInfraMiseDistributionPolicy:
    """Fleet tools win over a project's stale local declaration."""

    @staticmethod
    def _workspace(root: Path) -> Path:
        root.mkdir(parents=True)
        (root / "pyproject.toml").write_text(
            "[project]\n"
            'name = "fixture"\n'
            'version = "0.1.0"\n'
            'requires-python = ">=3.13,<3.14"\n',
            encoding="utf-8",
        )
        return root

    def test_managed_artifacts_fleet_wins_over_divergent_pin(
        self, tmp_path: Path
    ) -> None:
        """A project pin diverging from a tool the fleet now owns is residue.

        Resilient composition (operator law 2026-09-18): promoting a project
        tool to the fleet SSOT must never block generation in any consumer.
        The fleet version wins and the stale local declaration is reported
        for removal instead of failing the projection.
        """
        root = self._workspace(tmp_path / "project")
        config_dir = root / "config"
        config_dir.mkdir()
        toolchain = config.Infra.codegen.toolchain
        selector, version = toolchain.qlty_selector, toolchain.qlty_version
        (config_dir / "tools.yaml").write_text(
            "ManagedArtifacts:\n  Mise:\n    tools:\n"
            f'      "{selector}":\n        version: "{version}.divergent"\n',
            encoding="utf-8",
        )

        result = u.Infra.compose_mise_toml(
            root, f'[tools]\n"{selector}" = "{version}"\n'
        )

        tm.ok(result)
        tm.that(result.value, has=f'"{selector}" = "{version}"')
        tm.that(result.value, lacks="divergent")
