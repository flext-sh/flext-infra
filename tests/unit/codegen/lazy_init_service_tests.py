"""Tests for FlextInfraCodegenLazyInit service-level behavior.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_core import s
from flext_infra import FlextInfraCodegenLazyInit


class TestFlextInfraCodegenLazyInit:
    """Test suite for FlextInfraCodegenLazyInit service."""

    def test_init_accepts_workspace_root(self, tmp_path: Path) -> None:
        """Test generator initialization with workspace root."""
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        tm.that(generator, none=False)

    def test_run_with_empty_workspace_returns_zero(self, tmp_path: Path) -> None:
        """Test run() on empty workspace returns 0 (no errors)."""
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        result = generator.generate_inits(check_only=False)
        tm.that(result, eq=0)

    def test_run_with_check_only_flag(self, tmp_path: Path) -> None:
        """Test run() respects check_only flag without modifying files."""
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        result = generator.generate_inits(check_only=True)
        tm.that(result, eq=0)

    def test_generator_is_flext_service(self, tmp_path: Path) -> None:
        """Test that FlextInfraCodegenLazyInit is a s."""
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        tm.that(generator, is_=s)

    def test_run_returns_integer_exit_code(self, tmp_path: Path) -> None:
        """Test that run() returns an integer exit code."""
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        result = generator.generate_inits(check_only=False)
        tm.that(result, is_=int)
        tm.that(result, gte=0)

    def test_execute_method_returns_flext_result(self, tmp_path: Path) -> None:
        """Test execute() method returns r[int]."""
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        result = generator.execute()
        tm.ok(result)
        tm.that(result.value, is_=int)

    def test_generate_from_sibling_files(self, tmp_path: Path) -> None:
        """Test that generator discovers exports from sibling .py files."""
        src_dir = tmp_path / "src" / "test_pkg"
        src_dir.mkdir(parents=True)
        # Create sibling .py file with __all__
        (src_dir / "models.py").write_text(
            '"""Models."""\n\n__all__ = ["TestModel"]\n\nclass TestModel:\n    pass\n',
        )
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        result = generator.generate_inits(check_only=False)
        tm.that(result, eq=0)
        init_file = src_dir / "__init__.py"
        tm.that(init_file.exists(), eq=True)
        content = init_file.read_text()
        tm.that(content, contains="TestModel")
        tm.that(content, contains="test_pkg.models")

    def test_generate_bottom_up(self, tmp_path: Path) -> None:
        """Test that subdirectory exports bubble up to parent."""
        src_dir = tmp_path / "src" / "pkg"
        sub_dir = src_dir / "sub"
        sub_dir.mkdir(parents=True)
        # Subdirectory has a module
        (sub_dir / "service.py").write_text(
            '"""Service."""\n\n__all__ = ["SubService"]\n\nclass SubService:\n    pass\n',
        )
        # Parent has its own module
        (src_dir / "models.py").write_text(
            '"""Models."""\n\n__all__ = ["PkgModel"]\n\nclass PkgModel:\n    pass\n',
        )
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        result = generator.generate_inits(check_only=False)
        tm.that(result, eq=0)
        # Child __init__.py should have SubService
        child_init = sub_dir / "__init__.py"
        tm.that(child_init.exists(), eq=True)
        tm.that(child_init.read_text(), contains="SubService")
        # Parent __init__.py should have both
        parent_init = src_dir / "__init__.py"
        tm.that(parent_init.exists(), eq=True)
        parent_content = parent_init.read_text()
        tm.that(parent_content, contains="PkgModel")
        tm.that(parent_content, contains="merge_lazy_imports")
        tm.that(parent_content, contains='"sub": "pkg.sub"')

    def test_generate_preserves_existing_docstring(self, tmp_path: Path) -> None:
        """Test that existing docstring is preserved in regenerated file."""
        src_dir = tmp_path / "src" / "test_pkg"
        src_dir.mkdir(parents=True)
        # Create existing __init__.py with docstring
        (src_dir / "__init__.py").write_text(
            '"""My custom package docstring."""\n\n__all__ = []\n',
        )
        # Create sibling .py file
        (src_dir / "models.py").write_text(
            '"""Models."""\n\n__all__ = ["Foo"]\n\nclass Foo:\n    pass\n',
        )
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        generator.generate_inits(check_only=False)
        content = (src_dir / "__init__.py").read_text()
        tm.that(content, contains="My custom package docstring")

    def test_fails_when_public_exports_collide(self, tmp_path: Path) -> None:
        """Conflicting exports must fail instead of generating a broken __init__.py."""
        src_dir = tmp_path / "src" / "test_pkg"
        src_dir.mkdir(parents=True)
        (src_dir / "alpha.py").write_text("def run() -> None:\n    pass\n")
        (src_dir / "beta.py").write_text("def run() -> None:\n    pass\n")
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        result = generator.generate_inits(check_only=False)
        tm.that(result, eq=1)
        tm.that((src_dir / "__init__.py").exists(), eq=False)

    def test_accepts_service_base_in_services_package(self, tmp_path: Path) -> None:
        """services/base.py must accept the canonical ServiceBase exception."""
        src_dir = tmp_path / "src" / "test_pkg" / "services"
        src_dir.mkdir(parents=True)
        (tmp_path / "src" / "test_pkg" / "__init__.py").write_text("")
        (src_dir / "base.py").write_text(
            "class TestPkgServiceBase:\n    pass\n",
        )
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        result = generator.generate_inits(check_only=False)
        tm.that(result, eq=0)
        tm.that((src_dir / "__init__.py").exists(), eq=True)

    def test_accepts_plural_services_class_in_service_py(self, tmp_path: Path) -> None:
        """Root service.py may own a canonical plural Services facade."""
        src_dir = tmp_path / "src" / "test_pkg"
        src_dir.mkdir(parents=True)
        (src_dir / "service.py").write_text(
            "class TestPkgServices:\n    pass\n\ns = TestPkgServices\n",
        )
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        result = generator.generate_inits(check_only=False)
        tm.that(result, eq=0)
        tm.that((src_dir / "__init__.py").read_text(), contains="TestPkgServices")

    def test_nested_private_base_module_does_not_trigger_root_contract(
        self,
        tmp_path: Path,
    ) -> None:
        """Nested packages like transports/base.py must not be treated as root facades."""
        pkg_dir = tmp_path / "src" / "test_pkg" / "transports"
        pkg_dir.mkdir(parents=True)
        (tmp_path / "src" / "test_pkg" / "__init__.py").write_text("")
        (pkg_dir / "base.py").write_text(
            '"""Transport base."""\n\nfrom __future__ import annotations\n',
        )
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        result = generator.generate_inits(check_only=False)
        tm.that(result, eq=0)
        tm.that((pkg_dir / "__init__.py").exists(), eq=True)

    def test_fails_when_namespace_module_shape_is_invalid(self, tmp_path: Path) -> None:
        """Namespace enforcement must abort generation on invalid module shape."""
        src_dir = tmp_path / "src" / "test_pkg"
        src_dir.mkdir(parents=True)
        (src_dir / "base.py").write_text(
            "def helper() -> None:\n    pass\n\n"
            "class TestPkgServiceBase:\n    pass\n\n"
            "class TestPkgCommandContext:\n    pass\n",
        )
        generator = FlextInfraCodegenLazyInit(workspace=tmp_path)
        result = generator.generate_inits(check_only=False)
        tm.that(result, eq=1)
        tm.that((src_dir / "__init__.py").exists(), eq=False)
