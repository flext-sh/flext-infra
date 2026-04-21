"""Tests for lazy-init transformation behavior."""

from __future__ import annotations

from pathlib import Path

from tests import c, u


class TestsFlextInfraLazyInitTransforms:
    """Behavior tests for generated lazy-init transform output."""

    def test_subpackage_lazy_map_uses_symbol_names(self, tmp_path: Path) -> None:
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        utilities_dir = package_root / "_utilities"
        utilities_dir.mkdir()
        (utilities_dir / c.Infra.INIT_PY).write_text(
            "",
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        (utilities_dir / "mapper.py").write_text(
            "from __future__ import annotations\n\n"
            "class FlextDemoUtilitiesMapper:\n"
            "    pass\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )

        result = u.Infra.Tests.run_lazy_init(workspace_root)

        content = (utilities_dir / c.Infra.INIT_PY).read_text(
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        assert result == 0
        assert '".mapper": (' in content
        assert '"FlextDemoUtilitiesMapper"' in content
        assert '"mapper"' not in content

    def test_version_exports_are_runtime_wildcard_imports(self, tmp_path: Path) -> None:
        workspace_root, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        (package_root / "__version__.py").write_text(
            "from __future__ import annotations\n\n"
            '__version__ = "1.0.0"\n'
            "__version_info__ = (1, 0, 0)\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )

        result = u.Infra.Tests.run_lazy_init(workspace_root)

        content = (package_root / c.Infra.INIT_PY).read_text(
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        assert result == 0
        assert "from flext_demo import  *" in content
        assert '"__version__"' in content
        assert '"__version_info__"' in content
