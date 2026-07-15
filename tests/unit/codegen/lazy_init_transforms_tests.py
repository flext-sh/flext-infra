"""Tests for lazy-init transformation behavior.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from tests import c, u


class TestsFlextInfraLazyInitTransforms:
    """Behavior tests for generated lazy-init transform output."""

    def test_private_subpackage_initializer_exports_direct_symbols(
        self, tmp_path: Path
    ) -> None:
        """Publish direct public symbols from private subpackage modules."""
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

        init_content = (utilities_dir / c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT
        )
        tm.that(result, eq=0)
        tm.that(
            init_content,
            has=(
                "from .mapper import FlextDemoUtilitiesMapper "
                "as FlextDemoUtilitiesMapper"
            ),
        )
        tm.that(
            init_content, has='__all__: tuple[str, ...] = ("FlextDemoUtilitiesMapper",)'
        )
        tm.that(init_content, lacks="install_lazy_exports(")
        tm.that(init_content, lacks="__unit__")

    def test_source_packages_exclude_test_named_modules(self, tmp_path: Path) -> None:
        """Never publish test artifacts from an installable source package."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-demo", package_name="flext_demo"
        )
        models_dir = package_root / "_models"
        models_dir.mkdir()
        (models_dir / c.Infra.INIT_PY).write_text("", encoding=c.Cli.ENCODING_DEFAULT)
        (models_dir / "model.py").write_text(
            "from __future__ import annotations\n\nclass FlextDemoModel:\n    pass\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        test_modules = (
            ("_test_tmp.py", "PrivateTestArtifact"),
            ("test_fixture.py", "PrefixedTestArtifact"),
            ("model_tests.py", "SuffixedTestArtifact"),
        )
        for filename, class_name in test_modules:
            (models_dir / filename).write_text(
                "from __future__ import annotations\n\n"
                f"class {class_name}:\n"
                "    pass\n",
                encoding=c.Cli.ENCODING_DEFAULT,
            )

        result = u.Tests.run_lazy_init(workspace_root)
        init_content = (models_dir / c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT
        )

        tm.that(result, eq=0)
        tm.that(init_content, has="from .model import FlextDemoModel as FlextDemoModel")
        tm.that(init_content, has='__all__: tuple[str, ...] = ("FlextDemoModel",)')
        for _filename, class_name in test_modules:
            tm.that(init_content, lacks=class_name)
        tm.that(init_content, lacks="_test_tmp")
        tm.that(init_content, lacks="test_fixture")
        tm.that(init_content, lacks="model_tests")

    def test_version_exports_are_explicit_runtime_reexports(
        self, tmp_path: Path
    ) -> None:
        """Publish version declarations explicitly from the package root."""
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
        tm.that(result, eq=0)
        tm.that(
            content,
            has="from flext_demo.__version__ import __version__, __version_info__",
        )
        tm.that(content, has="__version__")
        tm.that(content, has="__version_info__")
        tm.that(content, lacks="__version__ as __version__")
        tm.that(content, lacks="__version_info__ as __version_info__")
        # mro-wkii.17 (Codex): version-only roots publish one static initializer.
        tm.that(content, has="__all__: tuple[str, ...]")
        tm.that(content, has='"__version__"')
        tm.that(content, has='"__version_info__"')
        tm.that(content, lacks="__unit__")
