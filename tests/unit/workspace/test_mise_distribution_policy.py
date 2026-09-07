<<<<<<< Updated upstream
"""Fleet-owned mise distribution policy at its composition owner.

``codegen conform`` exclusively owns ``.mise.toml`` (workspace environment
sync stopped writing it when the toolchain transaction landed), so the
distribution policy is proven against ``u.Infra.compose_mise_toml`` — the one
surface that turns a repository's ``config/*.yaml`` overlay into that file.
"""
=======
"""Public workspace sync contracts for suspended Mise toolchains."""
>>>>>>> Stashed changes

from __future__ import annotations

from pathlib import Path

<<<<<<< Updated upstream
from flext_infra import config, u
=======
from flext_infra import infra, m
>>>>>>> Stashed changes
from flext_tests import tm


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


def _alternate_selector() -> str:
    return "github:alternate-owner/beads"


def _fleet_render() -> str:
    """Render the fleet tool table the canonical template produces."""
    beads = config.Infra.codegen.toolchain.beads
    return f'[tools]\n"{beads.selector}" = "{beads.version}"\n'


class TestsMiseDistributionPolicy:
<<<<<<< Updated upstream
    """Reject alternate owners and fleet collisions through the composition owner."""
=======
    """Reject every selector family belonging to a suspended capability."""
>>>>>>> Stashed changes

    def test_tooling_owner_rejects_suspended_distribution(
        self, tmp_path: Path
    ) -> None:
        root = _workspace(tmp_path / "project")
        config_dir = root / "config"
        config_dir.mkdir()
        selector = _alternate_selector()
<<<<<<< Updated upstream
        (config_dir / "tools.yaml").write_text(
            "ManagedArtifacts:\n  Mise:\n    tools:\n"
            f'      "{selector}":\n        version: "1.0.0"\n',
=======
        (config_dir / "tooling.yaml").write_text(
            f'ManagedArtifacts:\n  Mise:\n    tools:\n      "{selector}": "1.0.0"\n',
>>>>>>> Stashed changes
            encoding="utf-8",
        )

        result = u.Infra.compose_mise_toml(root, _fleet_render())

        tm.fail(result, has=["suspended toolchain", selector, "tooling.yaml"])

    def test_managed_artifacts_reject_short_beads_alias(self, tmp_path: Path) -> None:
        root = _workspace(tmp_path / "project")
        config_dir = root / "config"
        config_dir.mkdir()
<<<<<<< Updated upstream
        (config_dir / "tools.yaml").write_text(
            'ManagedArtifacts:\n  Mise:\n    tools:\n      beads:\n        version: "1.2.2"\n',
=======
        (config_dir / "tooling.yaml").write_text(
            'ManagedArtifacts:\n  Mise:\n    tools:\n      beads: "1.2.2"\n',
>>>>>>> Stashed changes
            encoding="utf-8",
        )

        result = u.Infra.compose_mise_toml(root, _fleet_render())

        tm.fail(result, has=["suspended toolchain", "beads", "tooling.yaml"])

    def test_non_tooling_yaml_is_not_loaded_as_managed_artifacts(
        self, tmp_path: Path
    ) -> None:
        root = _workspace(tmp_path / "project")
        config_dir = root / "config"
        config_dir.mkdir()
<<<<<<< Updated upstream
        beads = config.Infra.codegen.toolchain.beads
        (config_dir / "tools.yaml").write_text(
            "ManagedArtifacts:\n  Mise:\n    tools:\n"
            f'      "{beads.selector}":\n        version: "{beads.version}.divergent"\n',
=======
        dormant = config_dir / "beads.yaml"
        dormant.write_text(
            "version: [\nManagedArtifacts:\n  Mise:\n    tools:\n      beads: 1\n",
>>>>>>> Stashed changes
            encoding="utf-8",
        )
        before = dormant.read_bytes()

        result = u.Infra.compose_mise_toml(root, _fleet_render())

        tm.ok(result)
        tm.that(dormant.read_bytes(), eq=before)

    def test_custom_mise_rejects_alternate_distribution(self, tmp_path: Path) -> None:
        """A hand-written tool table cannot swap a fleet identity's owner."""
        root = _workspace(tmp_path / "project")
        selector = _alternate_selector()
        custom = root / ".mise.toml"
        custom.write_text(f'[tools]\n"{selector}" = "1.0.0"\n', encoding="utf-8")

        result = u.Infra.validate_mise_tool_selectors((selector,), source=custom)

        tm.fail(result, has=["suspended toolchain", selector, ".mise.toml"])

<<<<<<< Updated upstream
    def test_canonical_selector_is_accepted(self, tmp_path: Path) -> None:
        """An arbitrary non-protected selector passes identity validation."""
        root = _workspace(tmp_path / "project")
        selector = tmp_path.name

        result = u.Infra.validate_mise_tool_selectors(
            (selector,), source=root / ".mise.toml"
        )

        tm.ok(result)
=======
    def test_custom_mise_rejects_exact_suspended_distribution(
        self, tmp_path: Path
    ) -> None:
        root = _workspace(tmp_path / "project")
        (root / ".mise.toml").write_text(
            '[tools]\n"github:gastownhall/beads" = "1.2.2"\nnode = "22"\n',
            encoding="utf-8",
        )

        result = _sync(root)

        tm.fail(result, has=["suspended toolchain", "github:gastownhall/beads"])
>>>>>>> Stashed changes


__all__: tuple[str, ...] = ()
