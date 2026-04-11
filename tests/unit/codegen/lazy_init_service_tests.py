"""Tests for FlextInfraCodegenLazyInit service-level behavior."""

from __future__ import annotations

from pathlib import Path

from tests import c, t, u


class TestFlextInfraCodegenLazyInit:
    """Test suite for FlextInfraCodegenLazyInit service."""

    def test_init_accepts_workspace_root(self, tmp_path: Path) -> None:
        """Test generator initialization with workspace root."""
        generator = u.Infra.Tests.create_lazy_init_service(tmp_path)

        assert generator is not None

    def test_run_with_empty_workspace_returns_zero(self, tmp_path: Path) -> None:
        """Test run() on empty workspace returns 0 (no errors)."""
        assert u.Infra.Tests.run_lazy_init(tmp_path) == 0

    def test_run_with_check_only_flag(self, tmp_path: Path) -> None:
        """Test run() respects check_only flag without modifying files."""
        assert u.Infra.Tests.run_lazy_init(tmp_path, check_only=True) == 0

    def test_modified_files_starts_empty(self, tmp_path: Path) -> None:
        """Modified files is empty before any generation occurs."""
        generator = u.Infra.Tests.create_lazy_init_service(tmp_path)

        assert tuple(generator.modified_files) == ()

    def test_run_returns_integer_exit_code(self, tmp_path: Path) -> None:
        """Test that run() returns an integer exit code."""
        result = u.Infra.Tests.run_lazy_init(tmp_path)

        assert isinstance(result, int)
        assert result >= 0

    def test_execute_method_returns_flext_result(self, tmp_path: Path) -> None:
        """execute() reports a successful public result on an empty workspace."""
        generator = u.Infra.Tests.create_lazy_init_service(tmp_path)
        result = generator.execute()

        assert result.is_success
        assert result.value is True

    def test_generate_from_sibling_files(self, tmp_path: Path) -> None:
        """Test that generator discovers exports from sibling .py files."""
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
        assert ".models" in init_content

    def test_generate_bottom_up(self, tmp_path: Path) -> None:
        """Test that subdirectory exports bubble up to parent."""
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
        child_init = sub_dir / "__init__.py"
        assert child_init.exists()
        assert (
            c.Infra.Tests.Fixtures.Codegen.LazyInit.CHILD_SERVICE_CLASS
            in child_init.read_text(encoding="utf-8")
        )
        parent_content = (package_root / "__init__.py").read_text(encoding="utf-8")
        assert c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_CLASS in parent_content
        assert (
            c.Infra.Tests.Fixtures.Codegen.LazyInit.CHILD_SERVICE_CLASS
            in parent_content
        )
        assert "merge_lazy_imports" in parent_content

    def test_generate_rewrites_to_canonical_docstring(self, tmp_path: Path) -> None:
        """Generated wrappers use the canonical package docstring."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
        )
        (package_root / "__init__.py").write_text(
            '"""My custom package docstring."""\n\n__all__ = []\n',
            encoding="utf-8",
        )
        u.Infra.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name=c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_CLASS,
            alias=c.Infra.Tests.Fixtures.Codegen.LazyInit.MODELS_ALIAS,
            docstring="Models.",
        )

        result = u.Infra.Tests.run_lazy_init(workspace_root)

        assert result == 0
        content = (package_root / "__init__.py").read_text(encoding="utf-8")
        assert "My custom package docstring" not in content
        assert '"""Test Pkg package."""' in content

    def test_fails_when_public_exports_collide(self, tmp_path: Path) -> None:
        """Conflicting exports must fail instead of generating a broken __init__.py."""
        src_dir = tmp_path / "src" / "test_pkg"
        src_dir.mkdir(parents=True)
        (src_dir / "alpha.py").write_text("def run() -> None:\n    pass\n")
        (src_dir / "beta.py").write_text("def run() -> None:\n    pass\n")

        result = u.Infra.Tests.run_lazy_init(tmp_path)

        assert result == 1
        assert not (src_dir / "__init__.py").exists()

    def test_accepts_service_base_in_services_package(self, tmp_path: Path) -> None:
        """services/base.py must accept the canonical ServiceBase exception."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
        )
        src_dir = package_root / "services"
        src_dir.mkdir(parents=True)
        (src_dir / "base.py").write_text(
            "class TestPkgServiceBase:\n    pass\n",
            encoding="utf-8",
        )

        result = u.Infra.Tests.run_lazy_init(workspace_root)

        assert result == 0
        assert (src_dir / "__init__.py").exists()

    def test_accepts_plural_services_class_in_service_py(self, tmp_path: Path) -> None:
        """Root service.py may own a canonical plural Services facade."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
        )
        (package_root / "service.py").write_text(
            "class TestPkgServices:\n    pass\n\ns = TestPkgServices\n",
            encoding="utf-8",
        )

        result = u.Infra.Tests.run_lazy_init(workspace_root)

        assert result == 0
        assert "TestPkgServices" in (package_root / "__init__.py").read_text(
            encoding="utf-8"
        )

    def test_nested_private_base_module_keeps_module_entry_without_root_contract(
        self,
        tmp_path: Path,
    ) -> None:
        """Nested packages like transports/base.py stay importable without facade checks."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
        )
        pkg_dir = package_root / "transports"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "base.py").write_text(
            '"""Transport base."""\n\nfrom __future__ import annotations\n',
            encoding="utf-8",
        )

        result = u.Infra.Tests.run_lazy_init(workspace_root)

        assert result == 0
        init_content = (pkg_dir / "__init__.py").read_text(encoding="utf-8")
        assert '".base": ("base",)' in init_content
        assert "TestPkgServiceBase" not in init_content

    def test_generates_when_namespace_module_shape_is_invalid(
        self, tmp_path: Path
    ) -> None:
        """Namespace enforcement is not part of lazy-init generation."""
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
        )
        (package_root / "base.py").write_text(
            "def helper() -> None:\n    pass\n\n"
            "class TestPkgServiceBase:\n    pass\n\n"
            "class TestPkgCommandContext:\n    pass\n",
            encoding="utf-8",
        )

        result = u.Infra.Tests.run_lazy_init(workspace_root)

        assert result == 0
        init_content = (package_root / "__init__.py").read_text(encoding="utf-8")
        assert "TestPkgServiceBase" in init_content
        assert "TestPkgCommandContext" in init_content


__all__: t.StrSequence = []
