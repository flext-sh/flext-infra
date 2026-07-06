"""Tests for inline lazy-init generation and stale sidecar cleanup."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m
from flext_infra.codegen._lazy_init_generation_registry import (
    FlextInfraCodegenLazyInitGenerationRegistryMixin,
)
from flext_infra.codegen.codegen_generation import FlextInfraCodegenGeneration


class TestsFlextInfraLazyInitInlineGeneration:
    """Validate generated ``__init__.py`` files own lazy registries directly."""

    @staticmethod
    def _lazy_init_plan(tmp_path: Path, current_pkg: str) -> m.Infra.LazyInitPlan:
        """Build a minimal lazy-init plan for generated-support cleanup tests."""
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

        status = writer._cleanup_generated_support_files(plan)

        assert status == 0
        assert not stub.exists()
        assert stub in {Path(path) for path in writer._modified_files}

    def test_tests_package_uses_inline_lazy_map(self) -> None:
        """Test packages inline lazy maps even when the map is large."""
        exports = tuple(f"Alpha{index}" for index in range(c.Infra.LOC_CAP_MAX + 1))
        filtered = {
            name: (f"tests.alpha_{index}", name) for index, name in enumerate(exports)
        }

        content = FlextInfraCodegenGeneration.generate_file(
            exports,
            filtered,
            {},
            "tests",
        )

        assert "from tests._exports import" not in content
        assert "_LAZY_IMPORTS = build_lazy_import_map(" in content
        assert "install_lazy_exports(" in content
        assert "publish_all=False" in content

    def test_public_root_uses_inline_lazy_map(self) -> None:
        """Public roots publish generated lazy maps from ``__init__.py`` only."""
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
        )
        lines = content.splitlines()

        assert "from typing import TYPE_CHECKING" in content
        assert "if TYPE_CHECKING:" in content
        assert "    from flext_core import r" in content
        assert "    from flext_demo.api import FlextDemo" in content
        assert "    from flext_demo.models import FlextDemoModels, m" in content
        assert "from flext_demo.api import FlextDemo" not in lines
        assert "from flext_demo.models import FlextDemoModels, m" not in lines
        assert "from flext_demo._exports import" not in content
        assert "_LAZY_IMPORTS = build_lazy_import_map(" in content
        assert "_PUBLIC_EXPORTS: tuple[str, ...] = (" in content
        assert "public_exports=_PUBLIC_EXPORTS" in content

    def test_check_only_reports_stale_generated_sidecars_without_removing(
        self,
        tmp_path: Path,
    ) -> None:
        """Check-only mode reports generated sidecars instead of removing them."""
        writer = FlextInfraCodegenLazyInitGenerationRegistryMixin()
        writer._modified_files = set()
        plan = self._lazy_init_plan(tmp_path, "tests")
        plan.context.pkg_dir.mkdir(parents=True)
        constants_dir = plan.context.pkg_dir / c.Infra.ROOT_EXPORTS_DIR
        constants_dir.mkdir()
        stale_paths = (
            plan.context.pkg_dir / c.Infra.ROOT_EXPORTS_FILENAME,
            plan.context.pkg_dir / "_exports_lazy.py",
            plan.context.pkg_dir / "_exports_lazy_part_01.py",
            constants_dir / c.Infra.ROOT_EXPORTS_FILENAME,
        )
        stale_content = f"{c.Infra.AUTOGEN_HEADER}\n"
        for path in stale_paths:
            path.write_text(stale_content, encoding=c.Cli.ENCODING_DEFAULT)

        status = writer._cleanup_generated_support_files(plan, check_only=True)

        assert status == 0
        assert all(path.exists() for path in stale_paths)
        assert set(stale_paths) <= {Path(path) for path in writer._modified_files}

    def test_generated_sidecars_are_removed(
        self,
        tmp_path: Path,
    ) -> None:
        """Generated ``_exports*`` sidecars are removed by the inline generator."""
        writer = FlextInfraCodegenLazyInitGenerationRegistryMixin()
        writer._modified_files = set()
        plan = self._lazy_init_plan(tmp_path, "tests")
        plan.context.pkg_dir.mkdir(parents=True)
        stale_paths = (
            plan.context.pkg_dir / c.Infra.ROOT_EXPORTS_FILENAME,
            plan.context.pkg_dir / "_exports_lazy.py",
            plan.context.pkg_dir / "_exports_lazy_part_01.py",
        )
        stale_content = f"{c.Infra.AUTOGEN_HEADER}\n"
        for path in stale_paths:
            path.write_text(stale_content, encoding=c.Cli.ENCODING_DEFAULT)

        status = writer._cleanup_generated_support_files(plan)

        assert status == 0
        assert all(not path.exists() for path in stale_paths)
        assert set(stale_paths) <= {Path(path) for path in writer._modified_files}


__all__: list[str] = []
