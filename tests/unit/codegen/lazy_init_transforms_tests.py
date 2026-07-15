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

    def test_pytest_registry_owns_plugin_import_order(self, tmp_path: Path) -> None:
        """Keep registry ownership lazy and isolated to its declaring project."""
        workspace_root = tmp_path / "workspace"
        registered_project, _registered_package = u.Tests.create_lazy_init_workspace(
            workspace_root,
            project_name="flext-registered",
            package_name="flext_registered",
        )
        peer_project, _peer_package = u.Tests.create_lazy_init_workspace(
            workspace_root, project_name="flext-peer", package_name="flext_peer"
        )
        layouts: list[tuple[Path, Path, Path]] = []
        for project_root, prefix in (
            (registered_project, "Registered"),
            (peer_project, "Peer"),
        ):
            tests_dir = project_root / "tests"
            unit_dir = tests_dir / "unit"
            plugins_dir = tests_dir / "plugins"
            unit_dir.mkdir(parents=True)
            plugins_dir.mkdir()
            for package_dir in (tests_dir, unit_dir, plugins_dir):
                (package_dir / c.Infra.INIT_PY).write_text(
                    "", encoding=c.Cli.ENCODING_DEFAULT
                )
            (unit_dir / "fixtures.py").write_text(
                f"class {prefix}Fixture:\n    pass\n", encoding=c.Cli.ENCODING_DEFAULT
            )
            (unit_dir / "helper.py").write_text(
                f"class {prefix}Helper:\n    pass\n", encoding=c.Cli.ENCODING_DEFAULT
            )
            (plugins_dir / "hooks.py").write_text(
                f"class {prefix}PluginHook:\n    pass\n",
                encoding=c.Cli.ENCODING_DEFAULT,
            )
            layouts.append((tests_dir, unit_dir, plugins_dir))
        registered_tests, registered_unit, registered_plugins = layouts[0]
        peer_tests, peer_unit, _peer_plugins = layouts[1]
        (registered_tests / "conftest.py").write_text(
            "pytest_plugins: tuple[str, ...] = (\n"
            '    "tests.unit.fixtures",\n'
            '    "tests.plugins",\n'
            ")\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        result = u.Tests.run_lazy_init(workspace_root)

        registered_tests_init = (registered_tests / c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT
        )
        registered_unit_init = (registered_unit / c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT
        )
        registered_plugins_init = (registered_plugins / c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT
        )
        peer_tests_init = (peer_tests / c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT
        )
        peer_unit_init = (peer_unit / c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT
        )
        tm.that(result, eq=0)
        tm.that(registered_unit_init, has="RegisteredHelper")
        tm.that(registered_unit_init, lacks="RegisteredFixture")
        tm.that(registered_tests_init, lacks='".plugins": ("plugins",)')
        tm.that(registered_plugins_init, has="RegisteredPluginHook")
        tm.that(peer_unit_init, has="PeerFixture")
        tm.that(peer_tests_init, has='".plugins": ("plugins",)')

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
