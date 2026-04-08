"""Tests for public lazy-init generation behavior.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraCodegenLazyInit


class TestProcessDirectory:
    """Test public lazy-init generation scenarios."""

    def test_generates_init_from_sibling_files(self, tmp_path: Path) -> None:
        """generate_inits() generates __init__.py from sibling exports."""
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        src_dir = tmp_path / "src" / "test_pkg"
        src_dir.mkdir(parents=True)
        (src_dir / "models.py").write_text(
            '"""Models."""\n\n__all__ = ["TestModel"]\n\nclass TestModel:\n    pass\n',
        )
        result = generator.generate_inits(check_only=False)
        tm.that(result, eq=0)
        init_content = (src_dir / "__init__.py").read_text()
        tm.that(init_content, contains="TestModel")
        tm.that(init_content, contains="test_pkg.models")

    def test_check_only_does_not_write(self, tmp_path: Path) -> None:
        """check_only mode reports without creating __init__.py."""
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        src_dir = tmp_path / "src" / "test_pkg"
        src_dir.mkdir(parents=True)
        (src_dir / "models.py").write_text(
            '"""Models."""\n\n__all__ = ["TestModel"]\n\nclass TestModel:\n    pass\n',
        )
        result = generator.generate_inits(check_only=True)
        tm.that(result, eq=0)
        tm.that(not (src_dir / "__init__.py").exists(), eq=True)

    def test_skips_directory_without_package(self, tmp_path: Path) -> None:
        """Directories outside canonical package roots are skipped."""
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        random_dir = tmp_path / "random"
        random_dir.mkdir()
        (random_dir / "models.py").write_text("class Model: pass\n")
        result = generator.generate_inits(check_only=False)
        tm.that(result, eq=0)
        tm.that((random_dir / "__init__.py").exists(), eq=False)

    def test_includes_child_exports(self, tmp_path: Path) -> None:
        """Parent package includes exports discovered from child packages."""
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        src_dir = tmp_path / "src" / "pkg"
        sub_dir = src_dir / "sub"
        sub_dir.mkdir(parents=True)
        (src_dir / "models.py").write_text(
            '"""Models."""\n\n__all__ = ["ParentModel"]\n\nclass ParentModel:\n    pass\n',
        )
        (sub_dir / "service.py").write_text(
            '"""Service."""\n\n__all__ = ["ChildService"]\n\nclass ChildService:\n    pass\n',
        )
        result = generator.generate_inits(check_only=False)
        tm.that(result, eq=0)
        parent_init = (src_dir / "__init__.py").read_text()
        tm.that(parent_init, contains="ParentModel")
        tm.that(parent_init, contains="ChildService")

    def test_generates_examples_tests_module_paths(self, tmp_path: Path) -> None:
        """Test nested examples/tests packages keep the examples prefix."""
        (tmp_path / "pyproject.toml").write_text("[tool.poetry]\nname = 'demo'\n")
        (tmp_path / "Makefile").write_text("check:\n\t@true\n")
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        examples_tests_dir = tmp_path / "examples" / "tests"
        examples_tests_dir.mkdir(parents=True)
        (examples_tests_dir / "test_declarative_example.py").write_text(
            '"""Example tests."""\n\n__all__ = ["load_env_config"]\n\n'
            "def load_env_config() -> None:\n    pass\n",
        )
        result = generator.generate_inits(check_only=False)
        tm.that(result, eq=0)
        init_content = (examples_tests_dir / "__init__.py").read_text()
        tm.that(
            init_content,
            contains="examples.tests.test_declarative_example",
        )

    def test_generates_tests_root_with_static_analysis_hints(
        self,
        tmp_path: Path,
    ) -> None:
        """Test tests/ wrappers get the same static hints as src/ wrappers."""
        (tmp_path / "pyproject.toml").write_text("[tool.poetry]\nname = 'demo'\n")
        (tmp_path / "Makefile").write_text("check:\n\t@true\n")
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir(parents=True)
        (tests_dir / "typings.py").write_text(
            '"""Typings."""\n\n__all__ = ["TestsFlextDemoTypes", "t"]\n\n'
            "class TestsFlextDemoTypes:\n    pass\n\n"
            "t = TestsFlextDemoTypes\n",
        )
        result = generator.generate_inits(check_only=False)
        tm.that(result, eq=0)
        init_content = (tests_dir / "__init__.py").read_text()
        tm.that(init_content, contains="if _t.TYPE_CHECKING:")
        tm.that(init_content, contains="__all__ = [")
        tm.that(
            init_content,
            contains='"t": (".typings", "TestsFlextDemoTypes")',
        )

    def test_handles_version_file(self, tmp_path: Path) -> None:
        """Version exports are preserved in generated public wrappers."""
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        src_dir = tmp_path / "src" / "test_pkg"
        src_dir.mkdir(parents=True)
        (src_dir / "models.py").write_text(
            '"""Models."""\n\n__all__ = ["Model"]\n\nclass Model:\n    pass\n',
        )
        (src_dir / "__version__.py").write_text(
            '__version__ = "1.0.0"\n__version_info__ = (1, 0, 0)\n',
        )
        result = generator.generate_inits(check_only=False)
        tm.that(result, eq=0)
        content = (src_dir / "__init__.py").read_text()
        tm.that(content, contains='__version__ = "1.0.0"')
        tm.that(content, contains="from test_pkg.__version__ import *")
        tm.that(
            content,
            contains='"__version_info__": (".__version__", "__version_info__")',
        )
