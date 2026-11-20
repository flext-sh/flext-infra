"""A declared root facade class defers its in-package parts like a family facade.

A project declares in ``deferred_facades`` a root facade class beyond the
namespace families (operator ruling 2026-11-19); the generated initializer
publishes every in-package class it composes by MRO as a stand-in, so importing
the facade loads no part module, while the first member read loads it. Without
the declaration the parts stay plain lazy exports.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

from tests import c, tm, u


class TestsFlextInfraCodegenLazyInitDeferredFacade:
    """The initializer defers the parts of a declared service facade."""

    @staticmethod
    def _workspace(tmp_path: Path) -> tuple[Path, Path]:
        """Create a package whose root facade composes one service part.

        Returns:
            The repository root and its package directory.

        """
        repository, package = u.Tests.create_lazy_init_workspace(tmp_path)
        servicos = package / "_servicos"
        servicos.mkdir()
        servicos.joinpath(c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        servicos.joinpath("eco.py").write_text(
            "class DemoServicosEco:\n"
            '    """Service part composed by the facade."""\n\n'
            "    def eco(self, texto: str) -> str:\n"
            '        """Return the text."""\n'
            "        return texto\n\n"
            "__all__ = ['DemoServicosEco']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        package.joinpath("api.py").write_text(
            f"from {package.name}._servicos import DemoServicosEco\n\n"
            "class DemoApi(DemoServicosEco):\n"
            '    """Root facade composing the service part."""\n\n'
            "__all__ = ['DemoApi']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        return repository, package

    def test_declared_facade_defers_its_parts(self, tmp_path: Path) -> None:
        """Importing the facade loads no part; the first member read loads it."""
        repository, package = self._workspace(tmp_path)
        u.Tests.override_repository_declaration(
            repository, {"deferred_facades": ["DemoApi"]}
        )
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        tm.that(u.Tests.run_lazy_init(repository, check_only=True), eq=0)
        tm.that(
            u.Tests.generated_init(package / "_servicos"),
            has='    deferred_members=(\n        "DemoServicosEco",\n    ),\n',
        )
        parte = f"{package.name}._servicos.eco"
        tm.that(
            u.Tests.run_lazy_init_probe(
                "import sys\n"
                f"from {package.name}.api import DemoApi\n"
                f"print({parte!r} in sys.modules)\n"
                "print(DemoApi().eco('ok'))\n"
                f"print({parte!r} in sys.modules)\n",
                python_paths=(str(package.parent), *sys.path),
                cwd=repository,
            ),
            eq=["False", "ok", "True"],
        )

    def test_undeclared_facade_keeps_its_parts_real(self, tmp_path: Path) -> None:
        """Without the declaration the parts stay plain lazy exports."""
        repository, package = self._workspace(tmp_path)
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        tm.that(u.Tests.generated_init(package / "_servicos"), lacks="deferred_members")
