"""Generic member classes are published so mypy can subscript them.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, m, p, tm, u


class TestsFacadeGenericPublication:
    """A generic member class keeps its identity and gains one publication."""

    @staticmethod
    def _part(*, generic: bool) -> str:
        """Declare one generic (or plain) summary beside a plain entry.

        Returns:
            The part module source.

        """
        summary = (
            "    class Summary[V](m.RootModel[dict[str, V]]):\n"
            if generic
            else "    class Summary(m.RootModel[dict[str, int]]):\n"
        )
        return (
            "from flext_core import m\n\n\n"
            "class ModelsLedger:\n"
            '    """Ledger records."""\n\n'
            "    class Entry(m.BaseModel):\n"
            '        """One ledger entry."""\n\n'
            "        amount: int = 0\n\n"
            f"{summary}"
            '        """One value per ledger file."""\n\n\n'
            "__all__: list[str] = ['ModelsLedger']\n"
        )

    @staticmethod
    def _workspace(tmp_path: Path) -> tuple[Path, Path, Path]:
        """Build one package with a model part and its generated facade.

        Returns:
            The repository root, the package directory and the facade path.

        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        sources = {
            "__init__.py": "",
            "_models/__init__.py": "",
            "_models/ledger.py": TestsFacadeGenericPublication._part(generic=True),
            "models.py": "",
            "_protocols/__init__.py": "",
            "protocols.py": (
                "class Protocols:\n    pass\n\n\n"
                "p = Protocols\n\n__all__: list[str] = ['Protocols', 'p']\n"
            ),
        }
        for relative, source in sources.items():
            path = package / relative
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        facade = package / "models.py"
        tm.ok(
            u.Cli.atomic_write_text_file(
                facade,
                f"{c.Infra.AUTOGEN_HEADER}\n"
                '"""Model facade."""\n\n'
                "from __future__ import annotations\n\n"
                "from flext_core import FlextModels\n\n"
                f"from {package.name}._models import ModelsLedger\n\n\n"
                "class Models(FlextModels):\n"
                '    """Models."""\n\n'
                "    class Ledger(ModelsLedger):\n"
                '        """Ledger namespace."""\n\n\n'
                "m = Models\n\n"
                "__all__: list[str] = ['Models', 'm']\n",
            )
        )
        return root, package, facade

    @classmethod
    def _rendered(cls, package: Path, facade: Path) -> str:
        """Render the facade twice, proving the second render is a no-op.

        Returns:
            The rendered facade source.

        """
        rendered = tm.ok(
            tm.not_none(u.Infra.render_utility_facade(package, family="m"))
        )
        tm.ok(u.Cli.atomic_write_text_file(facade, rendered))
        tm.ok(
            tm.not_none(u.Infra.render_utility_facade(package, family="m")),
            eq=rendered,
        )
        return rendered

    @classmethod
    def test_generic_member_is_published_and_keeps_its_identity(
        cls, tmp_path: Path, native_consumer: p.Tests.NativeConsumer
    ) -> None:
        """Only the generic member gains ``Name: TypeAlias = Part.Name``."""
        root, package, facade = cls._workspace(tmp_path)
        rendered = cls._rendered(package, facade)
        tm.that(rendered, has="        Summary: TypeAlias = ModelsLedger.Summary\n")
        tm.that(rendered, has="from typing import TypeAlias\n")
        tm.that(rendered, lacks="Entry: TypeAlias")
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name}.models import m\n"
            f"from {package.name}._models.ledger import ModelsLedger\n"
            "assert m.Ledger.Summary is ModelsLedger.Summary\n"
            "assert m.Ledger.Entry is ModelsLedger.Entry\n"
            "assert m.Ledger.Summary[int]({'a.csv': 1}).root == {'a.csv': 1}\n",
            cwd=root,
        )

    @classmethod
    def test_publication_retires_when_the_member_stops_being_generic(
        cls, tmp_path: Path
    ) -> None:
        """A member that is no longer generic returns to pure MRO composition."""
        _root, package, facade = cls._workspace(tmp_path)
        cls._rendered(package, facade)
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / "_models/ledger.py", cls._part(generic=False)
            )
        )
        rendered = cls._rendered(package, facade)
        tm.that(rendered, lacks="TypeAlias")

    @staticmethod
    def test_real_facade_generic_member_subscripts_and_calls() -> None:
        """The published generic member types and runs through ``m.Infra``."""
        counts = m.Infra.ModScanCounts[m.Infra.ModScanFinding](entries=())
        tm.that(counts.findings, eq=0)
        tm.that(isinstance(counts, p.Infra.ModScanCounts), eq=True)
