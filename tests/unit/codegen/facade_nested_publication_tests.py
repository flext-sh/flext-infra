"""Family classes reach the model facade only through MRO composition.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, p, tm, u


class TestsFacadeNestedPublication:
    """Nested classes compose; module-level ones fail; stale publications retire."""

    @staticmethod
    def _workspace(tmp_path: Path, part: str, facade: str) -> tuple[Path, Path, Path]:
        """Build one package with a model part module and its facade.

        Returns:
            The repository root, the package directory and the facade path.

        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        sources = {
            "__init__.py": "",
            "_models/__init__.py": "",
            "_models/ledger.py": part,
            "models.py": facade,
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
        return root, package, package / "models.py"

    @staticmethod
    def _nested_part() -> str:
        """Declare the ledger records inside their part class.

        Returns:
            The part module source.

        """
        return (
            "from flext_core import m\n\n\n"
            "class ModelsLedger:\n"
            '    """Ledger records."""\n\n'
            "    class Entry(m.BaseModel):\n"
            '        """One ledger entry."""\n\n'
            "        amount: int = 0\n\n"
            "    type EntryMap = dict[str, ModelsLedger.Entry]\n\n\n"
            "__all__: list[str] = ['ModelsLedger']\n"
        )

    @staticmethod
    def _facade(imports: str, body: str) -> str:
        """Write a generated model facade over the ledger part.

        Returns:
            The facade module source.

        """
        return (
            f"{c.Infra.AUTOGEN_HEADER}\n"
            '"""Model facade."""\n\n'
            "from __future__ import annotations\n\n"
            "from flext_core import FlextModels\n\n"
            f"{imports}\n\n"
            "class Models(FlextModels):\n"
            '    """Models."""\n\n'
            "    class Ledger(ModelsLedger):\n"
            f'        """Ledger namespace."""\n{body}\n\n'
            "m = Models\n\n"
            "__all__: list[str] = ['Models', 'm']\n"
        )

    @classmethod
    def test_module_level_family_class_names_its_part_class(
        cls, tmp_path: Path
    ) -> None:
        """A module-level model class fails generation with its destination."""
        _root, package, facade = cls._workspace(
            tmp_path,
            "from flext_core import m\n\n\n"
            "class Entry(m.BaseModel):\n"
            '    """One ledger entry."""\n\n'
            "    amount: int = 0\n\n\n"
            "class ModelsLedger:\n"
            '    """Ledger records."""\n\n\n'
            "__all__: list[str] = ['Entry', 'ModelsLedger']\n",
            "",
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                facade,
                cls._facade(f"from {package.name}._models import ModelsLedger", ""),
            )
        )
        message = tm.fail(
            tm.not_none(u.Infra.render_utility_facade(package, family="m"))
        )
        tm.that(message, has=f"{package.name}._models.ledger.Entry -> ModelsLedger")

    @classmethod
    def test_nested_class_reaches_the_facade_only_through_the_mro(
        cls, tmp_path: Path, native_consumer: p.Tests.NativeConsumer
    ) -> None:
        """A nested record is composed, never published by a body binding."""
        root, package, facade = cls._workspace(tmp_path, cls._nested_part(), "")
        name = package.name
        tm.ok(
            u.Cli.atomic_write_text_file(
                facade, cls._facade(f"from {name}._models import ModelsLedger", "")
            )
        )
        rendered = tm.ok(
            tm.not_none(u.Infra.render_utility_facade(package, family="m"))
        )
        tm.that(rendered, lacks="Entry =")
        tm.that(rendered, lacks="TypeAlias")
        tm.ok(u.Cli.atomic_write_text_file(facade, rendered))
        tm.ok(
            tm.not_none(u.Infra.render_utility_facade(package, family="m")),
            eq=rendered,
        )
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {name}.models import m\n"
            f"from {name}._models.ledger import ModelsLedger\n"
            "assert m.Ledger.Entry is ModelsLedger.Entry\n",
            cwd=root,
        )

    @c.Tests.MARK.parametrize("annotation", ["", ": TypeAlias"])
    def test_stale_self_publications_retire_with_their_imports(
        self,
        tmp_path: Path,
        native_consumer: p.Tests.NativeConsumer,
        annotation: str,
    ) -> None:
        """Nested records drop the old ``X = X`` lines and their dead import."""
        root, package, facade = self._workspace(tmp_path, self._nested_part(), "")
        name = package.name
        tm.ok(
            u.Cli.atomic_write_text_file(
                facade,
                self._facade(
                    ("from typing import TypeAlias\n\n" if annotation else "")
                    + f"from {name}._models import ModelsLedger\n"
                    f"from {name}._models.ledger import Entry, EntryMap",
                    f"\n        Entry{annotation} = Entry\n"
                    f"        EntryMap{annotation} = EntryMap\n",
                ),
            )
        )
        with u.Infra.facade_source_project(root) as binding:
            tm.ok(u.Infra.protocol_model_sources_from_source(root, binding[0]))
        rendered = tm.ok(
            tm.not_none(u.Infra.render_utility_facade(package, family="m"))
        )
        tm.that(rendered, lacks="= Entry")
        tm.that(rendered, lacks=f"from {name}._models.ledger import")
        tm.that(rendered, lacks="TypeAlias")
        tm.ok(u.Cli.atomic_write_text_file(facade, rendered))
        tm.ok(
            tm.not_none(u.Infra.render_utility_facade(package, family="m")),
            eq=rendered,
        )
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {name}.models import m\n"
            f"from {name}._models.ledger import ModelsLedger\n"
            "assert m.Ledger.Entry is ModelsLedger.Entry\n"
            "assert m.Ledger.Entry(amount=2).amount == 2\n",
            cwd=root,
        )

    @classmethod
    def test_authored_unresolved_publication_names_its_line(
        cls, tmp_path: Path
    ) -> None:
        """An authored facade keeps its body, so a dead binding fails located."""
        root, package, facade = cls._workspace(tmp_path, cls._nested_part(), "")
        name = package.name
        tm.ok(
            u.Cli.atomic_write_text_file(
                facade,
                cls._facade(
                    f"from {name}._models import ModelsLedger\n"
                    f"from {name}._models.ledger import Entry",
                    "\n        Entry = Entry\n",
                ).removeprefix(f"{c.Infra.AUTOGEN_HEADER}\n"),
            )
        )
        with (
            u.Infra.facade_source_project(root) as binding,
            u.Tests.raises(
                ValueError,
                match=r"models\.py:\d+: facade publication Entry = Entry resolves",
            ),
        ):
            u.Infra.protocol_model_sources_from_source(root, binding[0])
