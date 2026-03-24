from __future__ import annotations

from collections.abc import Mapping

from pathlib import Path


class FlextInfraCodegenTestProjectFactory:
    SRC_MODULE_FILES: tuple[str, ...] = (
        "constants.py",
        "typings.py",
        "protocols.py",
        "models.py",
        "utilities.py",
    )

    @staticmethod
    def to_pascal(snake: str) -> str:
        return "".join(part.title() for part in snake.split("_"))

    @staticmethod
    def create_project(
        *,
        tmp_path: Path,
        name: str,
        pkg_name: str,
        files: Mapping[str, str],
    ) -> Path:
        project = tmp_path / name
        project.mkdir()
        (project / "Makefile").touch()
        (project / "pyproject.toml").write_text(f"[project]\nname='{name}'\n")
        (project / ".git").mkdir()
        pkg = project / "src" / pkg_name
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").touch()
        pascal_name = FlextInfraCodegenTestProjectFactory.to_pascal(pkg_name)
        (pkg / "typings.py").write_text(
            "from flext_core import FlextTypes\n"
            f"class {pascal_name}Types(FlextTypes):\n    pass\n",
        )
        (pkg / "constants.py").write_text(
            "from flext_core import FlextConstants\n"
            f"class {pascal_name}Constants(FlextConstants):\n    pass\n",
        )
        for filename, content in files.items():
            (pkg / filename).write_text(content)
        return project

    @staticmethod
    def create_scaffolder_test_project(
        *,
        tmp_path: Path,
        with_all_modules: bool,
    ) -> Path:
        project = tmp_path / "test-project"
        project.mkdir()
        (project / "Makefile").touch()
        (project / "pyproject.toml").write_text("[project]\nname='test-project'\n")
        (project / ".git").mkdir()
        pkg = project / "src" / "test_project"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").touch()
        if with_all_modules:
            for mod in FlextInfraCodegenTestProjectFactory.SRC_MODULE_FILES:
                (pkg / mod).write_text(
                    f"class TestProject{mod.split('.')[0].title()}:\n    pass\n",
                )
        return project


__all__ = ["FlextInfraCodegenTestProjectFactory"]
