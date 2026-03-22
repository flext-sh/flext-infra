from __future__ import annotations

from pathlib import Path

from flext_infra.refactor.project_classifier import ProjectClassifier


def _write_pyproject(project_root: Path, content: str) -> None:
    pyproject_path = project_root / "pyproject.toml"
    pyproject_path.write_text(content.strip() + "\n", encoding="utf-8")


def test_read_project_metadata_preserves_pep621_dependency_order(
    tmp_path: Path,
) -> None:
    _write_pyproject(
        tmp_path,
        """
        [project]
        name = "flext-example"
        dependencies = [
            "flext-core>=0.1.0",
            "flext-cli>=0.1.0",
            "requests>=2.0.0",
        ]
        """,
    )

    classifier = ProjectClassifier(tmp_path)
    project_name, dependencies = classifier._read_project_metadata()

    assert project_name == "flext-example"
    assert dependencies == ["flext-core", "flext-cli", "requests"]


def test_read_project_metadata_preserves_poetry_dependency_order(
    tmp_path: Path,
) -> None:
    _write_pyproject(
        tmp_path,
        """
        [tool.poetry]
        name = "flext-example"

        [tool.poetry.dependencies]
        python = "^3.13"
        flext-core = "^0.1.0"
        flext-cli = { version = "^0.1.0" }
        requests = "^2.0.0"

        [tool.poetry.group.test.dependencies]
        python = "^3.13"
        flext-ldap = "^0.1.0"
        pytest = "^8.0.0"
        """,
    )

    classifier = ProjectClassifier(tmp_path)
    project_name, dependencies = classifier._read_project_metadata()

    assert project_name == "flext-example"
    assert dependencies == [
        "flext-core",
        "flext-cli",
        "requests",
        "flext-ldap",
        "pytest",
    ]
