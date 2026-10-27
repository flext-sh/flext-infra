"""Own-package source roles: library boundaries, isolated execution, layer zero.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra.codemod import FlextInfraModGateEngine
from tests import c, t, tm, u


class TestsFlextInfraCodemodOwnPackageRoles:
    """Source roles follow native definitions, never filenames."""

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("surface", ["src", "tests", "scripts", "examples"])
    def test_library_boundary_scans_owned_code_without_filename_waivers(
        mod_workspace: Path, surface: str
    ) -> None:
        """Layer-zero imports are valid; homonyms and consumers remain visible.

        Visibility is asserted across the library boundary scan.
        """
        namespace = u.Infra.project_package_name(mod_workspace)
        package = (
            mod_workspace / c.Infra.DEFAULT_SRC_DIR / namespace
            if surface == c.Infra.DEFAULT_SRC_DIR
            else mod_workspace / surface
        )
        package.mkdir(parents=True, exist_ok=True)
        (package / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        sources: t.MutableSequenceOf[Path] = []
        expected: set[Path] = set()
        original: t.MutableMappingKV[Path, str] = {}
        for relative, source, finding in (
            ("_config.py", "from pydantic import BaseModel\n", False),
            ("_settings/part.py", "from pydantic import BaseModel\n", False),
            ("_models/_config.py", "from pydantic import BaseModel\n", True),
            ("_utilities/_settings.py", "from pydantic import BaseModel\n", True),
            ("consumer.py", "from pydantic import BaseModel\n", True),
            ("ordinary.py", 'message = "from pydantic import BaseModel"\n', False),
        ):
            content = (
                f"import {package.name}\n"
                f"import {package.name}._settings\n"
                f"import {package.name}._models\n"
                f"import {package.name}._utilities\n\n{source}"
                if relative == "consumer.py"
                else source
            )
            path = package / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.parent != package:
                (path.parent / c.Infra.INIT_PY).write_text(
                    "", encoding=c.DEFAULT_ENCODING
                )
            path.write_text(content, encoding=c.DEFAULT_ENCODING)
            sources.append(path)
            original[path] = content
            if finding:
                expected.add(path.resolve())
        report = tm.ok(
            FlextInfraModGateEngine.scan(
                mod_workspace,
                fix=False,
                selection=("ban-direct-pydantic-import",),
                source_files=tuple(sources),
            ),
        )
        tm.that(
            {
                u.Infra.codemod_source_path(mod_workspace, entry.file)
                for entry in report.entries
            },
            eq=expected,
        )
        for path, source in original.items():
            tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("implementation", ["_native_hook", "moved_entrypoint"])
    @pytest.mark.parametrize("framework_import", [False, True])
    def test_isolated_execution_role_uses_native_producer_and_entrypoint(
        mod_workspace: Path, implementation: str, *, framework_import: bool
    ) -> None:
        """Only a declared native entrypoint with stdlib-only imports has the role."""
        namespace = u.Infra.project_package_name(mod_workspace)
        package = mod_workspace / c.Infra.DEFAULT_SRC_DIR / namespace
        hook = "import os\nclass Hook:\n    pass\nvalue = os.getenv('ROLE_PROBE')\n"
        contents = {
            "execution.py": (
                "from flext_cli import m\nE = m.Cli.PythonScriptExecution\n"
            ),
            f"{implementation}.py": hook
            + ("from flext_cli import u\n" if framework_import else ""),
            "public_hook.py": f"from .{implementation} import Hook\n",
            "producer.py": (
                "from .execution import E\nfrom .public_hook import Hook\n"
                "def command():\n"
                "    execution = E(module=Hook.__module__, "
                "role='isolated-stdlib')\n"
                "    return execution.python_flags, execution.module\n"
            ),
            "hook_client.py": hook,
            "bootstrap.py": hook,
            "application.py": "import os\nvalue = os.getenv('ROLE_PROBE')\n",
        }
        for relative, text in contents.items():
            (package / relative).write_text(text, encoding=c.DEFAULT_ENCODING)
        environ = (
            f"{c.Infra.CODEMOD_AMBIENT_ENVIRON_SHAPE}"
            f"{c.Infra.CODEMOD_GENERATED_ID_SEPARATOR}{namespace}"
        )
        report = tm.ok(
            FlextInfraModGateEngine.scan(
                mod_workspace,
                fix=False,
                selection=(environ,),
                source_files=tuple(package / name for name in contents),
            ),
        )
        reported = {
            u.Infra.codemod_source_path(mod_workspace, entry.file)
            for entry in report.entries
        }
        expected = {"hook_client.py", "bootstrap.py", "application.py"} | (
            {f"{implementation}.py"} if framework_import else set[str]()
        )
        tm.that(reported, eq={(package / name).resolve() for name in expected})

    @staticmethod
    def test_pytest_plugin_modules_are_layer_zero() -> None:
        """Installed pytest11 plugins are root; ordinary modules stay consumers."""
        plugins = u.Infra.pytest_plugin_modules()
        tm.that(plugins, empty=False)
        for module in plugins:
            tm.that(u.Infra.import_module_role(module), eq="layer0", msg=module)
        packaged = sorted(module for module in plugins if "." in module)
        ordinary = f"{packaged[0].partition('.')[0]}.ordinary_pytest_consumer"
        tm.that(ordinary in plugins, eq=False)
        tm.that(u.Infra.import_module_role(ordinary), eq="consumer")

    @staticmethod
    def test_frozen_stdlib_module_has_no_source_bootstrap() -> None:
        """Do not read a frozen module origin as a physical source file."""
        tm.that(u.Infra.bootstrap_modules("zipimport"), eq=frozenset())
        tm.that(u.Infra.import_module_role("zipimport"), eq="consumer")


__all__: list[str] = ["TestsFlextInfraCodemodOwnPackageRoles"]
