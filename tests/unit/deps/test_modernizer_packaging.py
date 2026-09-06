"""Packaging phase tests for deps modernizer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.deps.phases.ensure_packaging import FlextInfraEnsurePackagingPhase
from flext_tests import tm
from tests import c, m, t, u

if TYPE_CHECKING:
    from pathlib import Path


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

    def test_repository_root_with_matching_package_keeps_default_selection(
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

    def test_manifest_additional_python_roots_are_bounded_distribution_inputs(
        self, tool_config_document: m.Infra.ToolConfigDocument, tmp_path: Path
    ) -> None:
        """Project metadata includes declared root modules and packages in both artifacts."""
        package_dir = tmp_path / c.Infra.DEFAULT_SRC_DIR / "app"
        package_dir.mkdir(parents=True)
        (package_dir / c.Infra.INIT_PY).write_text("", encoding="utf-8")
        project = u.Tests.project_spec("app").model_copy(
            update={"root_modules": ("app_launch",), "root_packages": ("app_client",)}
        )
        manifest = m.Infra.WorkspaceManifestSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name="app",
            repository=u.Tests.repository_ref("app"),
            project=project,
        )
        (tmp_path / "config").mkdir()
        tm.ok(u.Cli.yaml_dump(tmp_path / "config" / "workspace.yaml", manifest))
        docs: t.JsonDict = {"package_name": "app"}
        payload: t.MutableJsonMapping = {
            "project": {"name": "application"},
            "tool": {"flext": {"docs": docs}},
        }

        changes = FlextInfraEnsurePackagingPhase(tool_config_document).apply_payload(
            payload, path=tmp_path / c.Infra.PYPROJECT_FILENAME, is_root=True
        )

        wheel = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(
            u.Cli.toml_mapping_path(
                payload, (c.Infra.TOOL, "hatch", "build", "targets", "wheel")
            )
        )
        sdist = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(
            u.Cli.toml_mapping_path(
                payload, (c.Infra.TOOL, "hatch", "build", "targets", "sdist")
            )
        )
        # The manifest write above materialises ``config/`` at the project root,
        # so the phase also ships every declared data dir present there.
        present_data_dirs = [
            data_dir
            for data_dir in tool_config_document.tools.hatch.packaged_data_dirs
            if (tmp_path / data_dir).is_dir()
        ]
        tm.that(len(changes) > 0, eq=True)
        tm.that(wheel["packages"], eq=["src/app", "src/app_client"])
        tm.that(
            wheel["force-include"],
            eq={
                "src/app_launch.py": "app_launch.py",
                **{data_dir: f"app/{data_dir}" for data_dir in present_data_dirs},
            },
        )
        tm.that(
            sdist["only-include"],
            eq=sorted(
                ["src/app", "src/app_client", "src/app_launch.py", *present_data_dirs]
            ),
        )


__all__: t.StrSequence = []
