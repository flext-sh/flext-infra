"""Tests for thin lazy-init registry wrappers."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m
from flext_infra.codegen._lazy_init_generation_registry import (
    FlextInfraCodegenLazyInitGenerationRegistryMixin,
)
from flext_infra.codegen._lazy_init_planner_public_api import (
    FlextInfraCodegenLazyInitPlannerPublicApiMixin,
)
from flext_infra.codegen.codegen_generation import FlextInfraCodegenGeneration


class TestsFlextInfraLazyInitRegistryWrapper:
    """Validate generated wrappers backed by lazy registries."""

    @staticmethod
    def _lazy_init_plan(tmp_path: Path, current_pkg: str) -> m.Infra.LazyInitPlan:
        """Build a minimal lazy-init plan for registry policy tests."""
        pkg_dir = tmp_path / current_pkg.replace(".", "/")
        return m.Infra.LazyInitPlan(
            context=m.Infra.LazyInitPackageContext(
                pkg_dir=pkg_dir,
                init_path=pkg_dir / c.Infra.INIT_PY,
                current_pkg=current_pkg,
                surface=current_pkg.split(".", maxsplit=1)[0],
                generated_init=True,
                importable=True,
            ),
        )

    def test_generated_typing_stub_is_removed_from_public_surfaces(
        self,
        tmp_path: Path,
    ) -> None:
        """Generated ``__init__.pyi`` files are stale and must be removed."""
        writer = FlextInfraCodegenLazyInitGenerationRegistryMixin()
        writer._modified_files = set()
        plan = self._lazy_init_plan(tmp_path, "flext_core")
        plan.context.pkg_dir.mkdir(parents=True)
        stub = plan.context.pkg_dir / c.Infra.INIT_PYI
        stub.write_text(
            f"{c.Infra.AUTOGEN_HEADER}\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        status = writer._write_generated_registry(plan, "")

        assert status == 0
        assert not stub.exists()
        assert stub in {Path(path) for path in writer._modified_files}

    def test_tests_package_uses_registry_wrapper(self) -> None:
        """Test packages import a registry sidecar instead of inline maps."""
        registry = m.Infra.LazyInitRegistryWrapper(
            module="tests._exports",
            name="TESTS_FLEXT_CORE_LAZY_IMPORTS",
        )
        exports = tuple(f"Alpha{index}" for index in range(c.Infra.LOC_CAP_MAX + 1))
        filtered = {
            name: (f"tests.alpha_{index}", name) for index, name in enumerate(exports)
        }

        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            {},
            "tests",
            registry_wrapper=registry,
        )

        assert "from tests._exports import TESTS_FLEXT_CORE_LAZY_IMPORTS" in content
        assert "_LAZY_IMPORTS = TESTS_FLEXT_CORE_LAZY_IMPORTS" in content
        assert "build_lazy_import_map(" not in content
        assert "merge_lazy_imports(" not in content
        assert "publish_all=False" in content
        assert len(content.splitlines()) <= 30

    def test_tests_package_synthesizes_generated_registry_wrapper(
        self,
        tmp_path: Path,
    ) -> None:
        """Tests packages without registries get codegen-owned wrapper metadata."""
        tests_dir = tmp_path / "flext-infra" / "tests"
        unit_dir = tests_dir / "unit"
        unit_dir.mkdir(parents=True)

        root_wrapper = FlextInfraCodegenLazyInitPlannerPublicApiMixin._lazy_import_registry_wrapper(
            tests_dir,
            "tests",
        )
        unit_wrapper = FlextInfraCodegenLazyInitPlannerPublicApiMixin._lazy_import_registry_wrapper(
            unit_dir,
            "tests.unit",
        )

        assert root_wrapper is not None
        assert root_wrapper.generated is True
        assert root_wrapper.name == "TESTS_FLEXT_INFRA_LAZY_IMPORTS"
        assert unit_wrapper is not None
        assert unit_wrapper.generated is True
        assert unit_wrapper.name == "TESTS_FLEXT_INFRA_UNIT_LAZY_IMPORTS"

    def test_public_package_uses_generated_lazy_sidecar(self, tmp_path: Path) -> None:
        """Public packages keep existing exports while lazy imports move to sidecar."""
        pkg_dir = tmp_path / "src" / "flext_demo"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / c.Infra.ROOT_EXPORTS_FILENAME).write_text(
            "__all__ = ('FlextDemoService',)\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        wrapper = FlextInfraCodegenLazyInitPlannerPublicApiMixin._lazy_import_registry_wrapper(
            pkg_dir,
            "flext_demo",
        )

        assert wrapper is not None
        assert wrapper.generated is True
        assert wrapper.module == "flext_demo._exports_lazy"
        assert wrapper.name == "FLEXT_DEMO_LAZY_IMPORTS"

    def test_public_registry_wrapper_keeps_runtime_thin(self) -> None:
        """Public registry wrappers publish registry names without inline imports."""
        registry = m.Infra.LazyInitRegistryWrapper(
            module="flext_demo._exports",
            name="FLEXT_DEMO_LAZY_IMPORTS",
            public_exports_name="FLEXT_DEMO_PUBLIC_EXPORTS",
        )
        generated_exports = tuple(
            f"FlextDemoGenerated{index}" for index in range(c.Infra.LOC_CAP_MAX + 1)
        )
        exports = (
            "FlextDemo",
            "FlextDemoModels",
            "m",
            "r",
            *generated_exports,
        )
        filtered = {
            "FlextDemo": ("flext_demo.api", "FlextDemo"),
            "FlextDemoModels": ("flext_demo.models", "FlextDemoModels"),
            "m": ("flext_demo.models", "m"),
            "r": ("flext_core", "r"),
            **{
                name: (f"flext_demo.generated_{index}", name)
                for index, name in enumerate(generated_exports)
            },
        }

        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            {},
            "flext_demo",
            registry_wrapper=registry,
        )
        lines = content.splitlines()

        assert "from typing import TYPE_CHECKING" in content
        assert "if TYPE_CHECKING:" in content
        assert "    from flext_core import r" in content
        assert "    from flext_demo.api import FlextDemo as FlextDemo" in content
        assert (
            "    from flext_demo.models import FlextDemoModels as FlextDemoModels"
            in content
        )
        assert "from flext_demo.api import FlextDemo as FlextDemo" not in lines
        assert (
            "from flext_demo.models import FlextDemoModels as FlextDemoModels"
            not in lines
        )
        assert "from flext_demo._exports import (" in content
        assert "FLEXT_DEMO_LAZY_IMPORTS" in content
        assert "FLEXT_DEMO_PUBLIC_EXPORTS" in content
        assert "for name, target in FLEXT_DEMO_LAZY_IMPORTS.items()" in content
        assert "if name in FLEXT_DEMO_PUBLIC_EXPORTS" in content
        assert "_PUBLIC_EXPORTS: tuple[str, ...] = FLEXT_DEMO_PUBLIC_EXPORTS" in content
        assert "__all__ =" not in content
        assert "public_exports=_PUBLIC_EXPORTS" in content

    def test_flext_core_root_removes_typing_stub_without_registry_import(
        self,
        tmp_path: Path,
    ) -> None:
        writer = FlextInfraCodegenLazyInitGenerationRegistryMixin()
        writer._modified_files = set()
        plan = self._lazy_init_plan(tmp_path, "flext_core").model_copy(
            update={
                "exports": ("FlextUtilities", "u"),
                "registry_wrapper": m.Infra.LazyInitRegistryWrapper(
                    module="flext_core._exports_lazy",
                    name="FLEXT_CORE_LAZY_IMPORTS",
                    generated=True,
                ),
            },
        )
        plan.context.pkg_dir.mkdir(parents=True)
        stub = plan.context.pkg_dir / c.Infra.INIT_PYI
        stub.write_text(
            f"{c.Infra.AUTOGEN_HEADER}\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        status = writer._write_generated_registry(
            plan,
            "from flext_core._root_exports import ROOT_ALL\n",
        )

        assert status == 0
        assert not stub.exists()

    def test_check_only_reports_stale_generated_registry_without_removing(
        self,
        tmp_path: Path,
    ) -> None:
        """Stale generated registry wrappers are reported, not removed, in checks."""
        writer = FlextInfraCodegenLazyInitGenerationRegistryMixin()
        writer._modified_files = set()
        plan = self._lazy_init_plan(tmp_path, "tests").model_copy(
            update={
                "registry_wrapper": m.Infra.LazyInitRegistryWrapper(
                    module="tests._exports",
                    name="TESTS_LAZY_IMPORTS",
                    generated=True,
                ),
            },
        )
        plan.context.pkg_dir.mkdir(parents=True)
        registry_path = plan.context.pkg_dir / c.Infra.ROOT_EXPORTS_FILENAME
        registry_part_path = plan.context.pkg_dir / "_exports_lazy_part_01.py"
        stale_content = f"{c.Infra.AUTOGEN_HEADER}\n"
        registry_path.write_text(stale_content, encoding=c.Cli.ENCODING_DEFAULT)
        registry_part_path.write_text(stale_content, encoding=c.Cli.ENCODING_DEFAULT)

        status = writer._write_generated_registry(
            plan,
            "from flext_core.lazy import install_lazy_exports\n",
            check_only=True,
        )

        assert status == 0
        assert registry_path.exists()
        assert registry_part_path.exists()
        assert {registry_path, registry_part_path} <= {
            Path(path) for path in writer._modified_files
        }

    def test_existing_registry_wrapper_reads_public_export_contract(
        self,
        tmp_path: Path,
    ) -> None:
        """Existing root registries expose lazy map and public ABI SSOT separately."""
        pkg_dir = tmp_path / "src" / "flext_demo"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / c.Infra.ROOT_EXPORTS_FILENAME).write_text(
            (
                "__all__ = (\n"
                '    "FLEXT_DEMO_LAZY_IMPORTS",\n'
                '    "FLEXT_DEMO_PUBLIC_EXPORTS",\n'
                ")\n"
            ),
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        wrapper = FlextInfraCodegenLazyInitPlannerPublicApiMixin._lazy_import_registry_wrapper(
            pkg_dir,
            "flext_demo",
        )

        assert wrapper is not None
        assert wrapper.name == "FLEXT_DEMO_LAZY_IMPORTS"
        assert wrapper.public_exports_name == "FLEXT_DEMO_PUBLIC_EXPORTS"

    def test_generated_registry_files_use_single_registry_template(self) -> None:
        """Generated registries emit one registry map without lazy part files."""
        exports = tuple(
            f"TestsFlextInfraGenerated{index}"
            for index in range(c.Infra.LOC_CAP_MAX + 1)
        )
        filtered = {
            name: (f"tests.generated_{index}", name)
            for index, name in enumerate(exports)
        }

        files = FlextInfraCodegenGeneration.generate_registry_files(
            "tests",
            "TESTS_FLEXT_INFRA_LAZY_IMPORTS",
            filtered,
            (),
            (),
        )

        assert c.Infra.ROOT_EXPORTS_FILENAME in files
        assert "_exports_lazy_part_01.py" not in files
        assert "_exports_lazy_part_02.py" not in files
        assert "build_lazy_import_map(" in files[c.Infra.ROOT_EXPORTS_FILENAME]
        assert (
            "TESTS_FLEXT_INFRA_LAZY_IMPORTS_PART"
            not in files[c.Infra.ROOT_EXPORTS_FILENAME]
        )


__all__: list[str] = []
