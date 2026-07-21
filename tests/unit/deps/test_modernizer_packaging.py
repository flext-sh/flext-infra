"""Packaging phase tests for deps modernizer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.deps.phases.ensure_packaging import FlextInfraEnsurePackagingPhase
from flext_tests import tm

from tests import c
from tests import t
from tests import u

if TYPE_CHECKING:
    from pathlib import Path

    from tests import m


class TestsFlextInfraDepsModernizerPackaging:
    """Wheel targets appear exactly when hatchling default selection cannot work."""

    def test_standalone_root_with_divergent_package_gets_wheel_targets(
        self, tool_config_document: m.Infra.ToolConfigDocument, tmp_path: Path
    ) -> None:
        """Standalone root shipping src/dcdoc as cosmos-docgen gets bounded targets."""
        package_dir = tmp_path / c.Infra.DEFAULT_SRC_DIR / "dcdoc"
        package_dir.mkdir(parents=True)
        (package_dir / c.Infra.INIT_PY).write_text("", encoding="utf-8")
        docs: t.JsonDict = {"package_name": "dcdoc"}
        flext: t.JsonDict = {"docs": docs}
        tool: t.JsonDict = {"flext": flext}
        project: t.JsonDict = {"name": "cosmos-docgen"}
        payload: t.MutableJsonMapping = {"project": project, "tool": tool}

        changes = FlextInfraEnsurePackagingPhase(tool_config_document).apply_payload(
            payload, path=tmp_path / c.Infra.PYPROJECT_FILENAME, is_root=True
        )

        wheel = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(
            u.Cli.toml_mapping_path(
                payload, (c.Infra.TOOL, "hatch", "build", "targets", "wheel")
            )
        )
        tm.that(len(changes) > 0, eq=True)
        tm.that(wheel["packages"], eq=["src/dcdoc"])

    def test_workspace_root_with_matching_package_keeps_default_selection(
        self, tool_config_document: m.Infra.ToolConfigDocument, tmp_path: Path
    ) -> None:
        """Monorepo root whose name matches src/<name> keeps hatchling defaults."""
        package_dir = tmp_path / c.Infra.DEFAULT_SRC_DIR / "flext"
        package_dir.mkdir(parents=True)
        (package_dir / c.Infra.INIT_PY).write_text("", encoding="utf-8")
        docs: t.JsonDict = {"package_name": "flext"}
        flext: t.JsonDict = {"docs": docs}
        tool: t.JsonDict = {"flext": flext}
        project: t.JsonDict = {"name": "flext"}
        payload: t.MutableJsonMapping = {"project": project, "tool": tool}

        changes = FlextInfraEnsurePackagingPhase(tool_config_document).apply_payload(
            payload, path=tmp_path / c.Infra.PYPROJECT_FILENAME, is_root=True
        )

        tm.that(changes, eq=())


__all__: t.StrSequence = []
