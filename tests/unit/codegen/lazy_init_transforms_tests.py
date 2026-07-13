"""Tests for lazy-init transformation behavior."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.constants import c
from tests.utilities import u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraLazyInitTransforms:
    """Behavior tests for generated lazy-init transform output."""

    def test_subpackage_lazy_map_uses_symbol_names(self, tmp_path: Path) -> None:
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        utilities_dir = package_root / "_utilities"
        utilities_dir.mkdir()
        (utilities_dir / c.Infra.INIT_PY).write_text(
            "",
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        (utilities_dir / "mapper.py").write_text(
            "from __future__ import annotations\n\n"
            "class FlextDemoUtilitiesMapper:\n"
            "    pass\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        result = u.Tests.run_lazy_init(workspace_root)

        # mro-i6nq.10: Every package exposes symbols through its local manifest.
        init_content = (utilities_dir / c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        unit_content = (utilities_dir / c.Infra.UNIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        assert result == 0
        assert "from flext_demo._utilities.__unit__ import (" in init_content
        assert "install_lazy_exports(" in init_content
        runtime_content = init_content.partition("if TYPE_CHECKING:")[0]
        assert "from flext_demo._utilities.mapper import" not in runtime_content
        assert '".mapper": ("FlextDemoUtilitiesMapper",),' in unit_content
        assert '"mapper"' not in unit_content

    def test_version_exports_are_explicit_runtime_reexports(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        (package_root / "__version__.py").write_text(
            "from __future__ import annotations\n\n"
            '__version__ = "1.0.0"\n'
            "__version_info__ = (1, 0, 0)\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        result = u.Tests.run_lazy_init(workspace_root)

        content = (package_root / c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        unit_content = (package_root / c.Infra.UNIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        assert result == 0
        assert "from flext_demo.__version__ import (" in content
        assert "__version__ as __version__" in content
        assert "__version_info__ as __version_info__" in content
        # mro-i6nq.10: Every public root declares the installer-owned __all__ type.
        assert "from typing import TYPE_CHECKING" in content
        assert "__all__: tuple[str, ...]" in content
        assert '"__version__"' in unit_content
        assert '"__version_info__"' in unit_content
