"""Public workspace sync contracts for fleet-owned mise distributions."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import config, infra, m
from flext_tests import tm

if TYPE_CHECKING:
    from flext_infra import p


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


def _sync(root: Path) -> p.Result[m.Infra.WorkspaceEnvironmentSyncResult]:
    return infra.sync_environment_files(
        m.Infra.WorkspaceEnvironmentSyncRequest(workspace_root=root)
    )


class TestsMiseDistributionPolicy:
    """Reject alternate owners and converge canonical pins through the facade."""

    def test_base_mise_contains_only_runtime_owned_tools(self, tmp_path: Path) -> None:
        root = _workspace(tmp_path / "project")

        result = _sync(root)

        tm.ok(result)
        tools = tomllib.loads((root / ".mise.toml").read_text(encoding="utf-8"))[
            "tools"
        ]
        tm.that(tools, lacks=["kubectl", "helm", "kind"])

    def test_managed_artifacts_reject_alternate_distribution(
        self, tmp_path: Path
    ) -> None:
        root = _workspace(tmp_path / "project")
        config_dir = root / "config"
        config_dir.mkdir()
        selector = _alternate_selector()
        (config_dir / "tools.yaml").write_text(
            f'ManagedArtifacts:\n  Mise:\n    tools:\n      "{selector}": "1.0.0"\n',
            encoding="utf-8",
        )

        result = _sync(root)

        tm.fail(result, has=["alternate distribution", selector, "tools.yaml"])

    def test_managed_artifacts_reject_short_beads_alias(self, tmp_path: Path) -> None:
        root = _workspace(tmp_path / "project")
        config_dir = root / "config"
        config_dir.mkdir()
        (config_dir / "tools.yaml").write_text(
            'ManagedArtifacts:\n  Mise:\n    tools:\n      beads: "1.2.2"\n',
            encoding="utf-8",
        )

        result = _sync(root)

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
            f'      "{beads.selector}": "{beads.version}.divergent"\n',
            encoding="utf-8",
        )

        result = _sync(root)

        tm.fail(result, has=["collides with fleet tool", beads.selector])

    def test_custom_mise_rejects_alternate_distribution(self, tmp_path: Path) -> None:
        root = _workspace(tmp_path / "project")
        selector = _alternate_selector()
        (root / ".mise.toml").write_text(
            f'[tools]\n"{selector}" = "1.0.0"\n', encoding="utf-8"
        )

        result = _sync(root)

        tm.fail(result, has=["alternate distribution", selector, ".mise.toml"])

    def test_custom_mise_converges_canonical_distribution_pin(
        self, tmp_path: Path
    ) -> None:
        root = _workspace(tmp_path / "project")
        beads = config.Infra.codegen.toolchain.beads
        (root / ".mise.toml").write_text(
            f'[tools]\n"{beads.selector}" = "0.0.0"\nnode = "22"\n', encoding="utf-8"
        )

        result = _sync(root)

        tm.ok(result)
        tools = tomllib.loads((root / ".mise.toml").read_text(encoding="utf-8"))[
            "tools"
        ]
        tm.that(tools[beads.selector]["version"], eq=beads.version)
        tm.that(tools[beads.selector]["prerelease"], eq=False)
        tm.that(tools["node"], eq="22")


__all__: tuple[str, ...] = ()
