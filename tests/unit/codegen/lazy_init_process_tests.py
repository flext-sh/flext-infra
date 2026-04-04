"""Tests for FlextInfraCodegenLazyInit._process_directory integration.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraCodegenLazyInit


class TestProcessDirectory:
    """Test the _process_directory method (integration-level)."""

    def test_generates_init_from_sibling_files(self, tmp_path: Path) -> None:
        """Test _process_directory generates __init__.py from siblings."""
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        src_dir = tmp_path / "src" / "test_pkg"
        src_dir.mkdir(parents=True)
        (src_dir / "models.py").write_text(
            '"""Models."""\n\n__all__ = ["TestModel"]\n\nclass TestModel:\n    pass\n',
        )
        dir_exports: Mapping[str, Mapping[str, tuple[str, str]]] = {}
        result, exports = generator._process_directory(
            src_dir,
            check_only=False,
            dir_exports=dir_exports,
        )
        tm.that(result, eq=0)
        tm.that(exports, contains="TestModel")
        init_content = (src_dir / "__init__.py").read_text()
        tm.that(init_content, contains="TestModel")

    def test_check_only_does_not_write(self, tmp_path: Path) -> None:
        """Test _process_directory in check_only mode doesn't write files."""
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        src_dir = tmp_path / "src" / "test_pkg"
        src_dir.mkdir(parents=True)
        (src_dir / "models.py").write_text(
            '"""Models."""\n\n__all__ = ["TestModel"]\n\nclass TestModel:\n    pass\n',
        )
        dir_exports: Mapping[str, Mapping[str, tuple[str, str]]] = {}
        result, exports = generator._process_directory(
            src_dir,
            check_only=True,
            dir_exports=dir_exports,
        )
        tm.that(result, eq=0)
        tm.that(exports, contains="TestModel")
        # __init__.py should NOT have been created
        tm.that(not (src_dir / "__init__.py").exists(), eq=True)

    def test_skips_directory_without_package(self, tmp_path: Path) -> None:
        """Test _process_directory skips dirs that can't infer package."""
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        random_dir = tmp_path / "random"
        random_dir.mkdir()
        (random_dir / "models.py").write_text("class Model: pass\n")
        dir_exports: Mapping[str, Mapping[str, tuple[str, str]]] = {}
        result, exports = generator._process_directory(
            random_dir,
            check_only=False,
            dir_exports=dir_exports,
        )
        tm.that(result, eq=None)
        tm.that(exports, eq={})

    def test_includes_child_exports(self, tmp_path: Path) -> None:
        """Test _process_directory includes child subdirectory exports."""
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        src_dir = tmp_path / "src" / "pkg"
        sub_dir = src_dir / "sub"
        sub_dir.mkdir(parents=True)
        (src_dir / "models.py").write_text(
            '"""Models."""\n\n__all__ = ["ParentModel"]\n\nclass ParentModel:\n    pass\n',
        )
        dir_exports = {
            str(sub_dir): {
                "ChildService": ("pkg.sub.service", "ChildService"),
            },
        }
        result, exports = generator._process_directory(
            src_dir,
            check_only=False,
            dir_exports=dir_exports,
        )
        tm.that(result, eq=0)
        tm.that(exports, contains="ParentModel")
        tm.that(exports, contains="ChildService")

    def test_generates_examples_tests_module_paths(self, tmp_path: Path) -> None:
        """Test nested examples/tests packages keep the examples prefix."""
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        examples_tests_dir = tmp_path / "examples" / "tests"
        examples_tests_dir.mkdir(parents=True)
        (examples_tests_dir / "test_declarative_example.py").write_text(
            '"""Example tests."""\n\n__all__ = ["load_env_config"]\n\n'
            "def load_env_config() -> None:\n    pass\n",
        )
        dir_exports: Mapping[str, Mapping[str, tuple[str, str]]] = {}
        result, exports = generator._process_directory(
            examples_tests_dir,
            check_only=False,
            dir_exports=dir_exports,
        )
        tm.that(result, eq=0)
        tm.that(exports, contains="load_env_config")
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
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir(parents=True)
        (tests_dir / "typings.py").write_text(
            '"""Typings."""\n\n__all__ = ["FlextInfraTestTypes", "t"]\n\n'
            "class FlextInfraTestTypes:\n    pass\n\n"
            "t = FlextInfraTestTypes\n",
        )
        dir_exports: Mapping[str, Mapping[str, tuple[str, str]]] = {}
        result, exports = generator._process_directory(
            tests_dir,
            check_only=False,
            dir_exports=dir_exports,
        )
        tm.that(result, eq=0)
        tm.that(exports, contains="t")
        init_content = (tests_dir / "__init__.py").read_text()
        tm.that(init_content, contains="if _t.TYPE_CHECKING:")
        tm.that(init_content, contains="__all__ = [")
        tm.that(
            init_content,
            contains='"t": ("tests.typings", "FlextInfraTestTypes")',
        )

    def test_handles_version_file(self, tmp_path: Path) -> None:
        """Test _process_directory handles __version__.py correctly."""
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        src_dir = tmp_path / "src" / "test_pkg"
        src_dir.mkdir(parents=True)
        (src_dir / "models.py").write_text(
            '"""Models."""\n\n__all__ = ["Model"]\n\nclass Model:\n    pass\n',
        )
        (src_dir / "__version__.py").write_text(
            '__version__ = "1.0.0"\n__version_info__ = (1, 0, 0)\n',
        )
        dir_exports: Mapping[str, Mapping[str, tuple[str, str]]] = {}
        result, _ = generator._process_directory(
            src_dir,
            check_only=False,
            dir_exports=dir_exports,
        )
        tm.that(result, eq=0)
        content = (src_dir / "__init__.py").read_text()
        tm.that(content, contains='__version__ = "1.0.0"')
        tm.that(content, contains="from test_pkg.__version__ import *")
        tm.that(content, contains='"__version_info__": "test_pkg.__version__"')
