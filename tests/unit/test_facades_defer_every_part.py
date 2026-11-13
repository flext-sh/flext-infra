"""Importing a flext-infra facade loads none of its part modules.

Every class a family facade composes by MRO is a lazy stand-in (ADR-018), so
a fresh import of one letter loads only the facade module and the package
initializers. Each letter is imported in a fresh interpreter, so the
observation is the real import closure and never this test process.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

from tests import c, tm, u


class TestsFlextInfraFacadesDeferEveryPart:
    """The facades publish part members that load on first use."""

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
    def test_facade_letter_loads_no_part_module(self, letter: str) -> None:
        """A fresh import of one facade letter loads no module of a family."""
        script = (
            "import sys\n"
            f"from flext_infra import {letter}\n"
            "print(sorted(name for name, module in sys.modules.items()\n"
            "    if name.startswith('flext_infra._')\n"
            "    and getattr(module, '__path__', None) is None))\n"
        )
        tm.that(self._run(script), eq="[]\n")

    def test_every_stand_in_lists_every_member_of_its_class(self) -> None:
        """Each generated stand-in lists every name its real class's MRO binds.

        The walk follows stand-ins nested in a real part's MRO to their own
        classes, so an index generated before a member was added fails here.
        """
        script = (
            "import importlib\n"
            "from flext_infra import c, t, p, m, u\n"
            "def target(k):\n"
            "    return vars(k).get('__flext_lazy_target__')\n"
            "def real(k):\n"
            "    module, owner, _ = target(k)\n"
            "    return getattr(importlib.import_module(module), owner)\n"
            "def plain(names):\n"
            "    return {n for n in names if not (n[:2] == '__' == n[-2:])}\n"
            "def bound(cls):\n"
            "    names = set()\n"
            "    for k in cls.__mro__:\n"
            "        names |= bound(real(k)) if target(k) else plain(vars(k))\n"
            "    return names\n"
            "seen, missing = set(), []\n"
            "def walk(cls):\n"
            "    for k in cls.__mro__:\n"
            "        if not target(k) or not target(k)[0].startswith('flext_infra')"
            " or k in seen:\n"
            "            continue\n"
            "        seen.add(k)\n"
            "        lost = bound(real(k)) - plain(vars(k))\n"
            "        missing.extend(f'{k.__name__}.{n}' for n in sorted(lost))\n"
            "        walk(real(k))\n"
            "for f in (c, t, p, m, u):\n"
            "    for root in (f, *(v for v in vars(f).values() "
            "if isinstance(v, type))):\n"
            "        walk(root)\n"
            "print(bool(seen), missing)\n"
        )
        tm.that(self._run(script), eq="True []\n")

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
