"""Tests for thin lazy-init registry wrappers."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m
from flext_infra.codegen._lazy_init_planner_public_api import (
    FlextInfraCodegenLazyInitPlannerPublicApiMixin,
)
from flext_infra.codegen.codegen_generation import FlextInfraCodegenGeneration


class TestsFlextInfraLazyInitRegistryWrapper:
    """Validate generated wrappers backed by split lazy registries."""

    def test_tests_package_uses_split_registry_wrapper(self) -> None:
        """Test packages import a pre-split registry instead of inline maps."""
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

        root_wrapper = (
            FlextInfraCodegenLazyInitPlannerPublicApiMixin._lazy_import_registry_wrapper(
                tests_dir,
                "tests",
            )
        )
        unit_wrapper = (
            FlextInfraCodegenLazyInitPlannerPublicApiMixin._lazy_import_registry_wrapper(
                unit_dir,
                "tests.unit",
            )
        )

        assert root_wrapper is not None
        assert root_wrapper.generated is True
        assert root_wrapper.name == "TESTS_FLEXT_INFRA_LAZY_IMPORTS"
        assert unit_wrapper is not None
        assert unit_wrapper.generated is True
        assert unit_wrapper.name == "TESTS_FLEXT_INFRA_UNIT_LAZY_IMPORTS"

    def test_generated_registry_files_use_split_templates(self) -> None:
        """Generated registries split lazy maps into bounded template parts."""
        exports = tuple(
            f"TestsFlextInfraGenerated{index}"
            for index in range(c.Infra.LAZY_REGISTRY_PART_SIZE + 1)
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
        assert "_exports_lazy_part_01.py" in files
        assert "_exports_lazy_part_02.py" in files
        assert (
            "from tests._exports_lazy_part_01 import "
            "TESTS_FLEXT_INFRA_LAZY_IMPORTS_PART_01"
        ) in files[c.Infra.ROOT_EXPORTS_FILENAME]
        assert "build_lazy_import_map(" in files["_exports_lazy_part_01.py"]
        assert len(files["_exports_lazy_part_01.py"].splitlines()) <= c.Infra.LOC_CAP_MAX


__all__: list[str] = []
