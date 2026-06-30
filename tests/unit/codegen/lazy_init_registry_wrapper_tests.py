"""Tests for thin lazy-init registry wrappers."""

from __future__ import annotations

from flext_infra import c, m
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


__all__: list[str] = []
