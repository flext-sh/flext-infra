"""Fleet-owned mise distribution policy at its composition owner.

``codegen conform`` exclusively owns ``.mise.toml`` (workspace environment
sync stopped writing it when the toolchain transaction landed), so the
distribution policy is proven against ``u.Infra.compose_mise_toml`` — the one
surface that turns a repository's ``config/*.yaml`` overlay into that file.
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import config, u
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
    canonical = config.Infra.codegen.toolchain.beads.selector
    backend, separator, repository = canonical.partition(":")
    name = repository.rsplit("/", maxsplit=1)[-1]
    return f"{backend}{separator}alternate-owner/{name}"


def _fleet_render() -> str:
    """Render the fleet tool table the canonical template produces."""
    beads = config.Infra.codegen.toolchain.beads
    return f'[tools]\n"{beads.selector}" = "{beads.version}"\n'


class TestsMiseDistributionPolicy:
    """Reject alternate owners and fleet collisions through the composition owner."""

    def test_managed_artifacts_reject_alternate_distribution(
        self, tmp_path: Path
    ) -> None:
        root = _workspace(tmp_path / "project")
        config_dir = root / "config"
        config_dir.mkdir()
        selector = _alternate_selector()
        (config_dir / "tools.yaml").write_text(
            "ManagedArtifacts:\n  Mise:\n    tools:\n"
            f'      "{selector}":\n        version: "1.0.0"\n',
            encoding="utf-8",
        )

        result = u.Infra.compose_mise_toml(root, _fleet_render())

        tm.fail(result, has=["alternate distribution", selector, "tools.yaml"])

    def test_managed_artifacts_reject_short_beads_alias(self, tmp_path: Path) -> None:
        root = _workspace(tmp_path / "project")
        config_dir = root / "config"
        config_dir.mkdir()
        (config_dir / "tools.yaml").write_text(
            'ManagedArtifacts:\n  Mise:\n    tools:\n      beads:\n        version: "1.2.2"\n',
            encoding="utf-8",
        )

        result = u.Infra.compose_mise_toml(root, _fleet_render())

        tm.fail(result, has=["alternate distribution", "beads", "tools.yaml"])

    def test_managed_artifacts_reject_divergent_canonical_pin(
        self, tmp_path: Path
    ) -> None:
        root = _workspace(tmp_path / "project")
        config_dir = root / "config"
        config_dir.mkdir()
        beads = config.Infra.codegen.toolchain.beads
        (config_dir / "tools.yaml").write_text(
            "ManagedArtifacts:\n  Mise:\n    tools:\n"
            f'      "{beads.selector}":\n        version: "{beads.version}.divergent"\n',
            encoding="utf-8",
        )

        result = u.Infra.compose_mise_toml(root, _fleet_render())

        tm.fail(result, has=["collides with fleet tool", beads.selector])

    def test_custom_mise_rejects_alternate_distribution(self, tmp_path: Path) -> None:
        """A hand-written tool table cannot swap a fleet identity's owner."""
        root = _workspace(tmp_path / "project")
        selector = _alternate_selector()
        custom = root / ".mise.toml"
        custom.write_text(f'[tools]\n"{selector}" = "1.0.0"\n', encoding="utf-8")

        result = u.Infra.validate_mise_tool_selectors((selector,), source=custom)

        tm.fail(result, has=["alternate distribution", selector, ".mise.toml"])

    def test_canonical_selector_is_accepted(self, tmp_path: Path) -> None:
        """The canonical fleet selector passes the same identity validation."""
        root = _workspace(tmp_path / "project")
        beads = config.Infra.codegen.toolchain.beads

        result = u.Infra.validate_mise_tool_selectors(
            (beads.selector,), source=root / ".mise.toml"
        )

        tm.ok(result)


__all__: tuple[str, ...] = ()
