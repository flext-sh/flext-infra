"""Tests for public lazy-init generation behavior."""

from __future__ import annotations

from pathlib import Path

from tests import c, t, u


class TestProcessDirectory:
    """Test public lazy-init generation scenarios."""

    def test_generates_init_from_sibling_files(self, tmp_path: Path) -> None:
        """generate_inits() generates __init__.py from sibling exports."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
        )
        u.Infra.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name=c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_CLASS,
            alias=c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_ALIAS,
            docstring="Models.",
        )

        result = u.Infra.Tests.run_lazy_init(workspace_root)

        assert result == 0
        init_content = (package_root / "__init__.py").read_text(encoding="utf-8")
        assert c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_CLASS in init_content
        assert (
            f'".models": (("m", "{c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_CLASS}"),)'
        ) in init_content

    def test_check_only_does_not_write(self, tmp_path: Path) -> None:
        """check_only mode reports without creating __init__.py."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
        )
        u.Infra.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name=c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_CLASS,
            alias=c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_ALIAS,
            docstring="Models.",
        )
        original_init = (package_root / "__init__.py").read_text(encoding="utf-8")

        result = u.Infra.Tests.run_lazy_init(workspace_root, check_only=True)

        assert result == 0
        assert (
            (package_root / "__init__.py").read_text(encoding="utf-8")
            == original_init
        )

    def test_skips_directory_without_package(self, tmp_path: Path) -> None:
        """Directories outside canonical package roots are skipped."""
        random_dir = tmp_path / "random"
        random_dir.mkdir()
        (random_dir / "models.py").write_text("class Model: pass\n")

        result = u.Infra.Tests.run_lazy_init(tmp_path)

        assert result == 0
        assert not (random_dir / "__init__.py").exists()

    def test_includes_child_exports(self, tmp_path: Path) -> None:
        """Parent package includes exports discovered from child packages."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
        )
        sub_dir = package_root / "sub"
        sub_dir.mkdir(parents=True)
        u.Infra.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name=c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_CLASS,
            alias=c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_ALIAS,
            docstring="Models.",
        )
        u.Infra.Tests.write_lazy_init_namespace_module(
            sub_dir / "service.py",
            class_name=c.Infra.Tests.Fixtures.Codegen.LazyInit.CHILD_SERVICE_CLASS,
            alias=c.Infra.Tests.Fixtures.Codegen.LazyInit.CHILD_SERVICE_ALIAS,
            docstring="Service.",
        )

        result = u.Infra.Tests.run_lazy_init(workspace_root)

        assert result == 0
        parent_init = (package_root / "__init__.py").read_text(encoding="utf-8")
        assert c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_CLASS in parent_init
        assert (
            c.Infra.Tests.Fixtures.Codegen.LazyInit.CHILD_SERVICE_CLASS in parent_init
        )

    def test_generates_examples_tests_module_paths(self, tmp_path: Path) -> None:
        """Test nested examples/tests packages keep the examples prefix."""
        workspace_root, _package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
            package_name=c.Infra.Tests.Fixtures.Codegen.LazyInit.ROOT_PACKAGE_NAME,
        )
        examples_tests_dir = workspace_root / "examples" / "tests"
        examples_tests_dir.mkdir(parents=True)
        u.Infra.Tests.write_lazy_init_namespace_module(
            examples_tests_dir / "utilities.py",
            class_name=(
                c.Infra.Tests.Fixtures.Codegen.LazyInit.EXAMPLES_UTILITIES_CLASS
            ),
            alias=c.Infra.Tests.Fixtures.Codegen.LazyInit.EXAMPLES_UTILITIES_ALIAS,
            docstring="Example tests.",
        )

        result = u.Infra.Tests.run_lazy_init(workspace_root)

        assert result == 0
        init_content = (examples_tests_dir / "__init__.py").read_text(encoding="utf-8")
        assert '".utilities": (' in init_content
        assert (
            c.Infra.Tests.Fixtures.Codegen.LazyInit.EXAMPLES_UTILITIES_CLASS
            in init_content
        )

    def test_generates_tests_root_with_static_analysis_hints(
        self,
        tmp_path: Path,
    ) -> None:
        """Test tests/ wrappers get the same static hints as src/ wrappers."""
        workspace_root, _package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
            package_name=c.Infra.Tests.Fixtures.Codegen.LazyInit.ROOT_PACKAGE_NAME,
        )
        tests_dir = workspace_root / "tests"
        tests_dir.mkdir(parents=True)
        u.Infra.Tests.write_lazy_init_namespace_module(
            tests_dir / "typings.py",
            class_name=c.Infra.Tests.Fixtures.Codegen.LazyInit.TESTS_TYPES_CLASS,
            alias=c.Infra.Tests.Fixtures.Codegen.LazyInit.TESTS_TYPES_ALIAS,
            docstring="Typings.",
        )

        result = u.Infra.Tests.run_lazy_init(workspace_root)

        assert result == 0
        init_content = (tests_dir / "__init__.py").read_text(encoding="utf-8")
        assert "if _t.TYPE_CHECKING:" in init_content
        assert "__all__ = [" in init_content
        assert (
            f'".typings": (("t", "{c.Infra.Tests.Fixtures.Codegen.LazyInit.TESTS_TYPES_CLASS}"),)'
        ) in init_content

    def test_handles_version_file(self, tmp_path: Path) -> None:
        """Version exports are preserved in generated public wrappers."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
        )
        u.Infra.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name=c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_CLASS,
            alias=c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_ALIAS,
            docstring="Models.",
        )
        u.Infra.Tests.write_lazy_init_version_module(package_root)

        result = u.Infra.Tests.run_lazy_init(workspace_root)

        assert result == 0
        content = (package_root / "__init__.py").read_text(encoding="utf-8")
        assert (
            f'__version__ = "{c.Infra.Tests.Fixtures.Codegen.LazyInit.VERSION}"'
            in content
        )
        assert (
            "from "
            f"{c.Infra.Tests.Fixtures.Codegen.LazyInit.PACKAGE_NAME}.__version__ "
            "import *"
        ) in content
        assert '".__version__": ("__version_info__",)' in content
        assert '"__version_info__"' in content


__all__: t.StrSequence = []
