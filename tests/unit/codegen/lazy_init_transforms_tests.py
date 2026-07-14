"""Tests for lazy-init transformation behavior."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests import c
from tests import u
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraLazyInitTransforms:
    """Behavior tests for generated lazy-init transform output."""

    def test_subpackage_lazy_map_uses_symbol_names(self, tmp_path: Path) -> None:
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-demo", package_name="flext_demo"
        )
        utilities_dir = package_root / "_utilities"
        utilities_dir.mkdir()
        (utilities_dir / c.Infra.INIT_PY).write_text(
            "", encoding=c.Cli.ENCODING_DEFAULT
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
            encoding=c.Cli.ENCODING_DEFAULT
        )
        unit_content = (utilities_dir / c.Infra.UNIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT
        )
        tm.that(result, eq=0)
        tm.that(init_content, has="from flext_demo._utilities.__unit__ import (")
        tm.that(init_content, has="install_lazy_exports(")
        runtime_content = init_content.partition("if TYPE_CHECKING:")[0]
        tm.that(runtime_content, lacks="from flext_demo._utilities.mapper import")
        tm.that(unit_content, has='".mapper": ("FlextDemoUtilitiesMapper",),')
        tm.that(unit_content, lacks='"mapper"')

    def test_version_exports_are_explicit_runtime_reexports(
        self, tmp_path: Path
    ) -> None:
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-demo", package_name="flext_demo"
        )
        (package_root / "__version__.py").write_text(
            "from __future__ import annotations\n\n"
            '__version__ = "1.0.0"\n'
            "__version_info__ = (1, 0, 0)\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        result = u.Tests.run_lazy_init(workspace_root)

        content = (package_root / c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT
        )
        unit_content = (package_root / c.Infra.UNIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT
        )
        tm.that(result, eq=0)
        tm.that(content, has="from flext_demo.__version__ import (")
        tm.that(content, has="__version__ as __version__")
        tm.that(content, has="__version_info__ as __version_info__")
        # mro-i6nq.10: Every public root declares the installer-owned __all__ type.
        tm.that(content, has="from typing import TYPE_CHECKING")
        tm.that(content, has="__all__: tuple[str, ...]")
        tm.that(unit_content, has='"__version__"')
        tm.that(unit_content, has='"__version_info__"')
