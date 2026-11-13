"""Importing a flext-infra facade loads none of its declared distributions.

The project declares its costly third-party distributions once
(``Infra.codegen.repository.deferred_distributions``). Each facade letter is
imported in a fresh interpreter, so the observation is the real import closure
and never this test process, which already holds every library.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from importlib.metadata import packages_distributions
from pathlib import Path

from packaging.utils import canonicalize_name

from tests import c, tm, u


class TestsFlextInfraFacadesDeferDeclaredDistributions:
    """The facades publish library members that load on first use."""

    @staticmethod
    def _declared_import_packages() -> tuple[str, ...]:
        """Map the project's declared distributions to their import packages.

        Returns:
            The import package names the declared distributions install.

        """
        root = Path(__file__).resolve().parents[2]
        document = tm.ok(
            u.Cli.yaml_safe_load(
                root / c.CONFIG_DIR_NAME / c.Infra.CODEGEN_CONFIG_FILENAME
            )
        )
        infra = u.Cli.toml_mapping_child(document, "Infra") or {}
        codegen = u.Cli.toml_mapping_child(infra, "codegen") or {}
        repository = u.Cli.toml_mapping_child(codegen, "repository") or {}
        names = repository.get("deferred_distributions")
        tm.that(isinstance(names, list), truth=True)
        declared = frozenset(
            canonicalize_name(str(name))
            for name in (names if isinstance(names, list) else ())
        )
        tm.that(len(declared) > 0, truth=True)
        packages = tuple(
            sorted(
                package
                for package, providers in packages_distributions().items()
                if declared & frozenset(map(canonicalize_name, providers))
            )
        )
        tm.that(len(packages) >= len(declared), truth=True)
        return packages

    @classmethod
    def _run(cls, script: str) -> str:
        """Run ``script`` in a fresh interpreter and return its standard output.

        Returns:
            The script's standard output.

        """
        result = tm.ok(u.Cli.run_raw((sys.executable, "-c", script), cwd=Path.cwd()))
        tm.that(result.outcome.raw_return_code, eq=0, msg=result.stderr)
        return result.stdout

    @c.Tests.MARK.parametrize("letter", ["c", "t", "p", "m", "u"])
    def test_facade_letter_loads_no_declared_distribution(self, letter: str) -> None:
        """A fresh import of one facade letter imports no declared library."""
        packages = self._declared_import_packages()
        script = (
            "import sys\n"
            f"from flext_infra import {letter}\n"
            f"print(sorted(set({packages!r}) & set(sys.modules)))\n"
        )
        tm.that(self._run(script), eq="[]\n")

    def test_deferred_members_resolve_to_the_library_objects(self) -> None:
        """The first member access loads the library and returns its own object."""
        script = (
            "import sys\n"
            "from flext_infra import c, t\n"
            "from flext_core.lazy import resolve_lazy_members\n"
            "before = 'libcst' in sys.modules or 'pytest' in sys.modules\n"
            "name, mark = c.Infra.Cst.Name, c.Infra.Pytest.MARK\n"
            "import libcst, pytest\n"
            "print(before, name is libcst.Name, mark is pytest.mark,\n"
            "      t.Infra.Cst.Name.__value__ is libcst.Name,\n"
            "      c.Infra.CST_DEFINITION_TYPES == "
            "(libcst.ClassDef, libcst.FunctionDef))\n"
            "from flext_infra import u\n"
            "resolve_lazy_members(c.Infra), resolve_lazy_members(t.Infra)\n"
            "resolve_lazy_members(u.Infra)\n"
            "print('resolved')\n"
        )
        tm.that(self._run(script), eq="False True True True True\nresolved\n")

    def test_import_style_vocabulary_is_the_source_engine_vocabulary(self) -> None:
        """The declared import styles are exactly the installed engine's values."""
        script = (
            "from rope.base.prefs import ImportStyle\n"
            "from flext_infra import c, config\n"
            "print(sorted(s.value for s in c.Infra.RopeImportStyle) == "
            "sorted(s.value for s in ImportStyle),\n"
            "      ImportStyle(config.Infra.rope.preferred_import_style.value).name)\n"
        )
        output = self._run(script)
        tm.that(output.startswith("True "), truth=True, msg=output)
