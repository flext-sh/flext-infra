"""Shared fixtures for the declarative project-layout engine tests."""

from __future__ import annotations

from pathlib import Path

from flext_infra import config
from flext_infra.codegen.layout import FlextInfraCodegenLayout
from tests import u


def build_loose_project(tmp_path: Path, name: str = "flext-demo") -> Path:
    """Create a minimal project carrying one violation of each layout kind."""
    project = tmp_path / name
    package_dir = project / "src" / name.replace("-", "_")
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (project / "pyproject.toml").write_text(
        "[project]\nname='flext-demo'\nversion='0.1.0'\n", encoding="utf-8"
    )
    (project / "README.md").write_text("# demo\n", encoding="utf-8")
    guides = project / "guides"
    guides.mkdir()
    (guides / "intro.md").write_text("intro\n", encoding="utf-8")
    (project / "index.md").write_text("index\n", encoding="utf-8")
    (project / "output.log").write_text("log-line\n", encoding="utf-8")
    (project / "loose.txt").write_text("unknown\n", encoding="utf-8")
    u.Tests.declare_workspace_projects(tmp_path, (name,))
    return project


def layout_engine(
    repository_root: Path, *, apply_changes: bool = False
) -> FlextInfraCodegenLayout:
    """Build the layout service over one fixture repository root."""
    return FlextInfraCodegenLayout(
        repository_root=repository_root, apply_changes=apply_changes
    )


def archive_root() -> str:
    """Archive root from the same typed SSOT the engine consumes."""
    return config.Infra.codegen.layout.archive_root


__all__: list[str] = ["archive_root", "build_loose_project", "layout_engine"]
