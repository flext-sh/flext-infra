"""Canonical facade source: upstream letter base and domain nested class.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFacadeCanonicalSource:
    """Prove the generated facade composes the upstream letter, never its name."""

    @staticmethod
    def test_single_upstream_class_name_base_becomes_the_letter(
        tmp_path: Path,
    ) -> None:
        """A class-name base of an upstream package is rewritten to its letter."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        TestsFacadeCanonicalSource._write(
            package / "_typings" / "__init__.py",
            "from flext_sample._typings.base import FlextSampleTypingsBase\n"
            "__all__ = ['FlextSampleTypingsBase']\n",
        )
        TestsFacadeCanonicalSource._write(
            package / "_typings" / "base.py",
            "class FlextSampleTypingsBase:\n"
            "    VALUE = 'base'\n\n"
            "__all__ = ['FlextSampleTypingsBase']\n",
        )
        facade = package / "typings.py"
        TestsFacadeCanonicalSource._write(
            facade,
            "from flext_cli import FlextCliTypes\n\n"
            "from flext_sample._typings import FlextSampleTypingsBase\n\n\n"
            "class FlextSampleTypes(FlextCliTypes):\n"
            "    class Sample(FlextSampleTypingsBase):\n"
            "        ...\n\n\n"
            "t = FlextSampleTypes\n"
            "__all__ = ['FlextSampleTypes', 't']\n",
        )
        rendered = TestsFacadeCanonicalSource._rendered(
            root, package, facade, family="t"
        )
        tm.that(rendered, has="from flext_cli import t\n")
        tm.that(TestsFacadeCanonicalSource._bases(rendered), eq=("t",))
        tm.that(rendered, lacks="FlextCliTypes")
        tm.that(rendered, lacks="builtins.")
        tm.that("class Sample" in rendered, eq=True)

    @staticmethod
    def test_flat_parts_move_under_the_domain_namespace(tmp_path: Path) -> None:
        """A flat generated facade nests its parts and extends the upstream letter."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        TestsFacadeCanonicalSource._write(
            package / "_typings" / "__init__.py",
            "from flext_sample._typings.base import FlextSampleTypingsBase\n"
            "from flext_sample._typings.sample import FlextSampleTypesSample\n"
            "__all__ = ['FlextSampleTypingsBase', 'FlextSampleTypesSample']\n",
        )
        TestsFacadeCanonicalSource._write(
            package / "_typings" / "base.py",
            "class FlextSampleTypingsBase:\n"
            "    VALUE = 'base'\n\n"
            "__all__ = ['FlextSampleTypingsBase']\n",
        )
        TestsFacadeCanonicalSource._write(
            package / "_typings" / "sample.py",
            "from flext_cli import FlextCliTypes\n\n\n"
            "class FlextSampleTypesSample(FlextCliTypes):\n"
            "    SAMPLE_VALUE = 'sample'\n\n"
            "__all__ = ['FlextSampleTypesSample']\n",
        )
        facade = package / "typings.py"
        TestsFacadeCanonicalSource._write(
            facade,
            f"{c.Infra.AUTOGEN_HEADER}\n"
            "from flext_sample._typings import (\n"
            "    FlextSampleTypesSample,\n"
            "    FlextSampleTypingsBase,\n"
            ")\n\n\n"
            "class FlextSampleTypes(\n"
            "    FlextSampleTypingsBase,\n"
            "    FlextSampleTypesSample,\n"
            "):\n"
            "    pass\n\n\n"
            "t = FlextSampleTypes\n"
            "__all__ = ['FlextSampleTypes', 't']\n",
        )
        rendered = TestsFacadeCanonicalSource._rendered(
            root, package, facade, family="t"
        )
        tm.that(rendered, has="from flext_cli import t\n")
        tm.that(TestsFacadeCanonicalSource._bases(rendered), eq=("t",))
        tm.that(
            TestsFacadeCanonicalSource._nested_bases(rendered, "Sample"),
            eq=("FlextSampleTypingsBase", "FlextSampleTypesSample"),
        )
        tm.that(rendered, lacks="builtins.")

    @staticmethod
    def test_flat_parts_add_the_secondary_upstream_facade(tmp_path: Path) -> None:
        """A part secondary upstream facade stays on the canonical outer class."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        TestsFacadeCanonicalSource._write(
            package / "_models" / "__init__.py",
            "from flext_test_project._models.base import ModelsBase\n"
            "from flext_test_project._models.dbt import ModelsDbt\n"
            "__all__ = ['ModelsBase', 'ModelsDbt']\n",
        )
        TestsFacadeCanonicalSource._write(
            package / "_models" / "base.py",
            "from flext_ldif import FlextLdifModels\n\n\n"
            "class ModelsBase(FlextLdifModels):\n"
            "    BASE_VALUE = 'base'\n\n"
            "__all__ = ['ModelsBase']\n",
        )
        TestsFacadeCanonicalSource._write(
            package / "_models" / "dbt.py",
            "from flext_meltano import m\n\n\n"
            "class ModelsDbt:\n"
            "    DBT_VALUE = m.ArbitraryTypesModel\n\n"
            "__all__ = ['ModelsDbt']\n",
        )
        facade = package / "models.py"
        TestsFacadeCanonicalSource._write(
            facade,
            f"{c.Infra.AUTOGEN_HEADER}\n"
            f"from {package.name}._models import ModelsBase, ModelsDbt\n\n\n"
            "class FlextTestProjectModels(ModelsBase, ModelsDbt):\n"
            "    pass\n\n\n"
            "m = FlextTestProjectModels\n"
            "__all__ = ['FlextTestProjectModels', 'm']\n",
        )
        rendered = TestsFacadeCanonicalSource._rendered(
            root, package, facade, family="m"
        )
        tm.that(rendered, has="from flext_meltano import m\n")
        tm.that(rendered, has="from flext_ldif import FlextLdifModels\n")
        tm.that(
            TestsFacadeCanonicalSource._bases(rendered),
            eq=("m", "FlextLdifModels"),
        )
        tm.that(
            TestsFacadeCanonicalSource._nested_bases(rendered, "TestProject"),
            eq=("ModelsBase", "ModelsDbt"),
        )
        tm.that(rendered, lacks="builtins.")

    @staticmethod
    def test_double_upstream_composition_keeps_the_secondary_facade(
        tmp_path: Path,
    ) -> None:
        """The family letter first keeps the secondary upstream facade intact."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        TestsFacadeCanonicalSource._write(
            package / "_models" / "__init__.py",
            "from flext_test_project._models.ledger import ModelsLedger\n"
            "__all__ = ['ModelsLedger']\n",
        )
        TestsFacadeCanonicalSource._write(
            package / "_models" / "ledger.py",
            "from flext_core import m\n\n\n"
            "class ModelsLedger:\n"
            "    class Entry(m.BaseModel):\n"
            "        amount: int = 0\n\n\n"
            "__all__ = ['ModelsLedger']\n",
        )
        TestsFacadeCanonicalSource._write(package / "_protocols" / "__init__.py", "")
        TestsFacadeCanonicalSource._write(
            package / "protocols.py",
            "class Protocols:\n    pass\n\n\n"
            "p = Protocols\n\n__all__ = ['Protocols', 'p']\n",
        )
        facade = package / "models.py"
        TestsFacadeCanonicalSource._write(
            facade,
            "from flext_meltano import m\n"
            "from flext_ldif import FlextLdifModels\n\n"
            f"from {package.name}._models import ModelsLedger\n\n\n"
            "class Models(m, FlextLdifModels):\n"
            "    class Ledger(ModelsLedger):\n"
            "        ...\n\n\n"
            "m = Models\n"
            "__all__ = ['Models', 'm']\n",
        )
        rendered = TestsFacadeCanonicalSource._rendered(
            root, package, facade, family="m"
        )
        tm.that(rendered, has="from flext_meltano import m\n")
        tm.that(
            TestsFacadeCanonicalSource._bases(rendered),
            eq=("m", "FlextLdifModels"),
        )
        tm.that(rendered, lacks="builtins.")

    @staticmethod
    def test_unbound_facade_base_fails_loud_without_builtins(
        tmp_path: Path,
    ) -> None:
        """A base no import binds fails naming the file and expression."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        TestsFacadeCanonicalSource._write(
            package / "_models" / "__init__.py",
            "from flext_test_project._models.ledger import ModelsLedger\n"
            "__all__ = ['ModelsLedger']\n",
        )
        TestsFacadeCanonicalSource._write(
            package / "_models" / "ledger.py",
            "from flext_core import m\n\n\n"
            "class ModelsLedger:\n"
            "    class Entry(m.BaseModel):\n"
            "        amount: int = 0\n\n\n"
            "__all__ = ['ModelsLedger']\n",
        )
        facade = package / "models.py"
        TestsFacadeCanonicalSource._write(
            facade,
            f"from {package.name}._models import ModelsLedger\n\n\n"
            "class Models(FlextUnknownModels):\n"
            "    class Ledger(ModelsLedger):\n"
            "        ...\n\n\n"
            "m = Models\n"
            "__all__ = ['Models', 'm']\n",
        )
        message = tm.fail(
            tm.not_none(u.Infra.render_utility_facade(package, family="m"))
        )
        tm.that(message, has="Unresolved facade base")
        tm.that(message, has="models.py:FlextUnknownModels")
        tm.that("builtins" in message, eq=False)
        tm.that(root.exists(), eq=True)

    @staticmethod
    def _rendered(
        root: Path,
        package: Path,
        facade: Path,
        *,
        family: str,
    ) -> str:
        """Render twice, proving the second pass is a no-op.

        Returns:
            The rendered facade source.

        """
        tm.ok(root.exists())
        rendered = tm.ok(
            tm.not_none(u.Infra.render_utility_facade(package, family=family))
        )
        TestsFacadeCanonicalSource._write(facade, rendered)
        tm.ok(
            tm.not_none(u.Infra.render_utility_facade(package, family=family)),
            eq=rendered,
        )
        return rendered

    @staticmethod
    def _nested_bases(rendered: str, domain: str) -> tuple[str, ...]:
        """Return the bases of the nested domain namespace.

        Returns:
            The nested base expressions in declared order.

        """
        tree = ast.parse(rendered)
        owner = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            and node.name.endswith(("Types", "Models"))
        )
        nested = next(
            child
            for child in owner.body
            if isinstance(child, ast.ClassDef) and child.name == domain
        )
        return tuple(ast.unparse(base) for base in nested.bases)

    @staticmethod
    def _bases(rendered: str) -> tuple[str, ...]:
        """Return the outer facade class base expressions.

        Returns:
            The base expressions in declared order.

        """
        tree = ast.parse(rendered)
        owner = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            and node.name.endswith(("Types", "Models"))
        )
        return tuple(ast.unparse(base) for base in owner.bases)

    @staticmethod
    def _write(path: Path, source: str) -> None:
        """Create the parent directory and write the fixture source."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
