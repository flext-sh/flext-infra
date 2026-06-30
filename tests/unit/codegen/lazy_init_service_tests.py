"""Tests for FlextInfraCodegenLazyInit service-level behavior."""

from __future__ import annotations

from pathlib import Path

from tests.constants import c
from tests.typings import t
from tests.utilities import u


class TestFlextInfraCodegenLazyInit:
    """Test suite for FlextInfraCodegenLazyInit service."""

    @staticmethod
    def _read_generated_file(package_root: Path, filename: str) -> str:
        return package_root.joinpath(filename).read_text(
            encoding=c.Cli.ENCODING_DEFAULT,
        )

    @classmethod
    def _assert_root_lazy_contract(
        cls,
        package_root: Path,
        *,
        expected_names: t.StrSequence,
        expected_modules: t.StrSequence,
    ) -> tuple[str, str, str, str]:
        init_content = cls._read_generated_file(package_root, c.Infra.INIT_PY)
        registry_content = cls._read_generated_file(
            package_root,
            c.Infra.ROOT_EXPORTS_FILENAME,
        )
        lazy_part_content = cls._read_generated_file(
            package_root,
            "_exports_lazy_part_01.py",
        )
        stub_content = cls._read_generated_file(package_root, c.Infra.INIT_PYI)

        assert "from flext_core.lazy import install_lazy_exports" in init_content
        assert (
            "from flext_test_project._exports import FLEXT_TEST_PROJECT_LAZY_IMPORTS"
        ) in init_content
        assert "_LAZY_IMPORTS = FLEXT_TEST_PROJECT_LAZY_IMPORTS" in init_content
        assert "_PUBLIC_EXPORTS: tuple[str, ...]" in init_content
        assert "public_exports=_PUBLIC_EXPORTS" in init_content
        assert "build_lazy_import_map(" not in init_content
        assert "merge_lazy_imports(" not in init_content
        assert "TYPE_CHECKING" not in init_content

        assert "merge_lazy_imports(" in registry_content
        assert "_exports_lazy_part_01" in registry_content
        assert "build_lazy_import_map(" in lazy_part_content
        for module_name in expected_modules:
            assert f'"{module_name}"' in lazy_part_content
        for export_name in expected_names:
            assert f'"{export_name}"' in init_content
            assert f'"{export_name}"' in lazy_part_content
            assert f"{export_name} as {export_name}" in stub_content

        return (init_content, registry_content, lazy_part_content, stub_content)

    def test_init_accepts_workspace_root(self, tmp_path: Path) -> None:
        """Test generator initialization with workspace root."""
        generator = u.Tests.create_lazy_init_service(tmp_path)

        assert generator is not None

    def test_run_with_empty_workspace_returns_zero(self, tmp_path: Path) -> None:
        """Test run() on empty workspace returns 0 (no errors)."""
        assert u.Tests.run_lazy_init(tmp_path) == 0

    def test_run_with_check_only_flag(self, tmp_path: Path) -> None:
        """Test run() respects check_only flag without modifying files."""
        assert u.Tests.run_lazy_init(tmp_path, check_only=True) == 0

    def test_modified_files_starts_empty(self, tmp_path: Path) -> None:
        """Modified files is empty before any generation occurs."""
        generator = u.Tests.create_lazy_init_service(tmp_path)

        assert tuple(generator.modified_files) == ()

    def test_run_returns_integer_exit_code(self, tmp_path: Path) -> None:
        """Test that run() returns an integer exit code."""
        result = u.Tests.run_lazy_init(tmp_path)

        assert isinstance(result, int)
        assert result >= 0

    def test_execute_method_returns_flext_result(self, tmp_path: Path) -> None:
        """execute() reports a successful public result on an empty workspace."""
        generator = u.Tests.create_lazy_init_service(tmp_path)
        result = generator.execute()

        assert result.success
        assert result.value is True

    def test_generate_from_sibling_files(self, tmp_path: Path) -> None:
        """Test that generator discovers exports from sibling .py files."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
        )
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name="FlextTestsModels",
            alias="m",
            docstring="Models.",
        )

        result = u.Tests.run_lazy_init(workspace_root)

        assert result == 0
        self._assert_root_lazy_contract(
            package_root,
            expected_names=("FlextTestsModels", "m"),
            expected_modules=(".models",),
        )

    def test_generate_bottom_up(self, tmp_path: Path) -> None:
        """Test that subdirectory exports bubble up to parent."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
        )
        sub_dir = package_root / "sub"
        sub_dir.mkdir(parents=True)
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name="FlextTestsModels",
            alias="m",
            docstring="Models.",
        )
        u.Tests.write_lazy_init_namespace_module(
            sub_dir / "service.py",
            class_name="FlextTestsService",
            alias="s",
            docstring="Service.",
        )

        result = u.Tests.run_lazy_init(workspace_root)

        assert result == 0
        child_init = sub_dir / "__init__.py"
        assert child_init.exists()
        assert "FlextTestsService" in child_init.read_text(encoding="utf-8")
        _init_content, registry_content, _lazy_part_content, _stub_content = (
            self._assert_root_lazy_contract(
                package_root,
                expected_names=("FlextTestsModels", "FlextTestsService", "m"),
                expected_modules=(".models", ".sub"),
            )
        )
        assert '(".sub",)' in registry_content

    def test_generate_rewrites_to_canonical_docstring(self, tmp_path: Path) -> None:
        """Generated wrappers use the canonical package docstring."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
        )
        (package_root / "__init__.py").write_text(
            '"""My custom package docstring."""\n\n__all__ = []\n',
            encoding="utf-8",
        )
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name="FlextTestsModels",
            alias="m",
            docstring="Models.",
        )

        result = u.Tests.run_lazy_init(workspace_root)

        assert result == 0
        content = (package_root / "__init__.py").read_text(encoding="utf-8")
        assert "My custom package docstring" not in content
        assert '"""Flext Test Project package."""' in content

    def test_resolves_public_export_collision_via_canonical_scorer(
        self, tmp_path: Path
    ) -> None:
        """Conflicting exports are resolved deterministically.

        The canonical scorer picks exactly one source; codegen succeeds and
        the init imports the chosen source only.
        """
        workspace_root, src_dir = u.Tests.create_lazy_init_workspace(tmp_path)
        (src_dir / "alpha.py").write_text(
            "from __future__ import annotations\n\n"
            '__all__: list[str] = ["Shared"]\n\n'
            "class Shared:\n    pass\n",
            encoding="utf-8",
        )
        (src_dir / "beta.py").write_text(
            "from __future__ import annotations\n\n"
            '__all__: list[str] = ["Shared"]\n\n'
            "class Shared:\n    pass\n",
            encoding="utf-8",
        )

        result = u.Tests.run_lazy_init(workspace_root)

        assert result == 0
        _init_content, _registry_content, lazy_part_content, stub_content = (
            self._assert_root_lazy_contract(
                src_dir,
                expected_names=("Shared",),
                expected_modules=(),
            )
        )
        # Exactly one of the two sources wins; the lazy registry and typing stub
        # publish the single canonical source selected by the scorer.
        alpha_imports = lazy_part_content.count('".alpha"')
        beta_imports = lazy_part_content.count('".beta"')
        assert (alpha_imports == 1 and beta_imports == 0) or (
            alpha_imports == 0 and beta_imports == 1
        ), lazy_part_content
        assert (
            "from flext_test_project.alpha import Shared as Shared" in stub_content
        ) != ("from flext_test_project.beta import Shared as Shared" in stub_content)

    def test_accepts_service_base_in_services_package(self, tmp_path: Path) -> None:
        """services/base.py must accept the canonical ServiceBase exception."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
        )
        src_dir = package_root / "services"
        src_dir.mkdir(parents=True)
        (src_dir / "base.py").write_text(
            "class TestPkgServiceBase:\n    pass\n",
            encoding="utf-8",
        )

        result = u.Tests.run_lazy_init(workspace_root)

        assert result == 0
        assert (src_dir / "__init__.py").exists()

    def test_accepts_plural_services_class_in_service_py(self, tmp_path: Path) -> None:
        """Root service.py may own a canonical plural Services facade."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
        )
        (package_root / "service.py").write_text(
            "class TestPkgServices:\n    pass\n\ns = TestPkgServices\n\n"
            '__all__ = ["TestPkgServices", "s"]\n',
            encoding="utf-8",
        )

        result = u.Tests.run_lazy_init(workspace_root)

        assert result == 0
        self._assert_root_lazy_contract(
            package_root,
            expected_names=("TestPkgServices", "s"),
            expected_modules=(".service",),
        )

    def test_nested_private_base_module_without_exports_is_not_generated(
        self,
        tmp_path: Path,
    ) -> None:
        """Nested packages without explicit exports do not get generated wrappers."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
        )
        pkg_dir = package_root / "transports"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "base.py").write_text(
            '"""Transport base."""\n\nfrom __future__ import annotations\n',
            encoding="utf-8",
        )

        result = u.Tests.run_lazy_init(workspace_root)

        assert result == 0
        assert not (pkg_dir / "__init__.py").exists()
        assert not (pkg_dir / c.Infra.ROOT_EXPORTS_FILENAME).exists()
        assert not (pkg_dir / c.Infra.INIT_PYI).exists()

    def test_generates_when_namespace_module_shape_is_invalid(
        self, tmp_path: Path
    ) -> None:
        """Namespace enforcement is not part of lazy-init generation."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
        )
        (package_root / "base.py").write_text(
            "def helper() -> None:\n    pass\n\n"
            "class TestPkgServiceBase:\n    pass\n\n"
            "class TestPkgCommandContext:\n    pass\n\n"
            '__all__ = ["TestPkgServiceBase", "TestPkgCommandContext"]\n',
            encoding="utf-8",
        )

        result = u.Tests.run_lazy_init(workspace_root)

        assert result == 0
        self._assert_root_lazy_contract(
            package_root,
            expected_names=("TestPkgServiceBase", "TestPkgCommandContext"),
            expected_modules=(".base",),
        )


__all__: t.StrSequence = []
