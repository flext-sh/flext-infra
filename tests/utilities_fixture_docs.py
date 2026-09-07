"""Docs and GitHub workflow workspace fixture utilities for flext-infra."""

from __future__ import annotations

from pathlib import Path

from tests import t
from tests.utilities_fixture_project import TestsFlextInfraUtilitiesProjectFixtureMixin


class TestsFlextInfraUtilitiesDocsFixtureMixin:
    """Documentation and GitHub workflow workspace fixture helpers."""

    @staticmethod
    def create_docs_workspace(
        root: Path,
        *,
        project_names: t.StrSequence = (),
        include_fixable_link: bool = False,
    ) -> Path:
        """Create a documentation workspace fixture."""
        workspace = root / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        TestsFlextInfraUtilitiesProjectFixtureMixin.write_project_beads_config(
            workspace, "workspace"
        )

        def _write(path: Path, content: str) -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

        readme = "# Root\n"
        docs_readme = "# Docs\n\n## Overview\n"
        if include_fixable_link:
            _write(workspace / "docs/guides/setup.md", "# Setup\n")
            docs_readme = (
                "# Docs\n\n## Overview\n\nSee [Setup](guides/setup) for details.\n"
            )
        _write(workspace / "README.md", readme)
        _write(workspace / "docs/README.md", docs_readme)
        _write(workspace / "docs/index.md", "# Index\n")
        _write(workspace / "docs/architecture/README.md", "# Architecture\n")
        _write(workspace / "docs/guides/README.md", "# Guides\n")
        _write(workspace / "docs/projects/README.md", "# Projects\n")
        _write(workspace / "docs/api-reference/README.md", "# API Reference\n")
        if project_names:
            members = ", ".join(f'"{name}"' for name in project_names)
            _write(
                workspace / "pyproject.toml",
                (
                    '[project]\nname = "workspace"\n\n'
                    f"[tool.uv.workspace]\nmembers = [{members}]\n"
                ),
            )

        for name in project_names:
            project = workspace / name
            project.mkdir(parents=True, exist_ok=True)
            pkg_name = name.replace("-", "_")
            _write(
                project / "pyproject.toml",
                (f'[project]\nname = "{name}"\nversion = "0.1.0"\n'),
            )
            _write(
                project / f"src/{pkg_name}/__init__.py",
                '"""Documentation fixture package."""\n\n'
                'def hello() -> str:\n    """Return a greeting."""\n    return "hello"\n\n'
                '__all__ = ["hello"]\n',
            )
            _write(project / "README.md", f"# {name}\n")
            _write(project / "docs/README.md", "# Project Docs\n")
            _write(project / "docs/architecture.md", "# Architecture\n")
            _write(project / "docs/dev.md", "# Development\n")
            _write(project / "docs/api.md", "# API\n")
            TestsFlextInfraUtilitiesProjectFixtureMixin.write_project_beads_config(
                project, name
            )

        if project_names:
            TestsFlextInfraUtilitiesProjectFixtureMixin.declare_workspace_projects(
                workspace, project_names
            )

        return workspace

    @staticmethod
    def create_github_workspace(
        root: Path,
        *,
        project_names: t.StrSequence = (),
        source_workflow: str = "name: CI\n",
    ) -> Path:
        """Create a GitHub workflow workspace fixture."""
        workspace = root / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        TestsFlextInfraUtilitiesProjectFixtureMixin.write_project_beads_config(
            workspace, "workspace"
        )
        workflow_dir = workspace / ".github/workflows"
        workflow_dir.mkdir(parents=True, exist_ok=True)
        (workflow_dir / "ci.yml").write_text(source_workflow, encoding="utf-8")
        for name in project_names:
            project = workspace / name
            project.mkdir(parents=True, exist_ok=True)
            (project / "pyproject.toml").write_text(
                (
                    "[project]\n"
                    f'name = "{name}"\n'
                    'version = "0.1.0"\n'
                    'dependencies = ["flext-core>=0.1.0"]\n'
                ),
                encoding="utf-8",
            )
            src_dir = project / "src" / name.replace("-", "_")
            src_dir.mkdir(parents=True, exist_ok=True)
            (src_dir / "__init__.py").write_text("", encoding="utf-8")
            TestsFlextInfraUtilitiesProjectFixtureMixin.write_project_beads_config(
                project, name
            )
        if project_names:
            TestsFlextInfraUtilitiesProjectFixtureMixin.declare_workspace_projects(
                workspace, project_names
            )
        return workspace


__all__: list[str] = ["TestsFlextInfraUtilitiesDocsFixtureMixin"]
