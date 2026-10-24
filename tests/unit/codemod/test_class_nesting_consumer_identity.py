"""Class nesting keeps aliases, registrations and cross-module consumers coherent.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

import flext_core
import pytest

from flext_infra import infra
from tests import c, tm, u
from tests.unit.codemod.class_nesting_owner_support import (
    TestsFlextInfraClassNestingSupport,
)

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraClassNestingConsumerIdentity(TestsFlextInfraClassNestingSupport):
    """Native aliases, framework hooks and consumers follow the nested owner."""

    @pytest.mark.parametrize("module_kind", ["ordinary", "utilities", "typings"])
    def test_pep695_aliases_preserve_lazy_values_and_generic_scope(
        self,
        tmp_path: Path,
        module_kind: str,
    ) -> None:
        """Cold consumers resolve recursive aliases and unshadowed type parameters."""
        source = (
            '"""Recursive and generic payloads."""\n'
            "from __future__ import annotations\n\n"
            "from collections.abc import Callable\n\n"
            "type Leaf = str | int\n"
            "type Payload = Leaf | list[Payload] | dict[str, Payload]\n"
            "type Item = int\n"
            "type Box[Item] = tuple[Item, Payload]\n"
            "type Items[*Item] = tuple[*Item]\n"
            "type Callback[**Item] = Callable[Item, Payload]\n"
            'type Quoted[Item] = tuple["Item", Payload]\n'
            "type Defaults[T: Leaf = str] = tuple[T, Leaf]\n"
            "type Forward = list[Later]\n"
            "type Later = tuple[Forward]\n\n"
            "class _Record:\n    type Field = Payload\n"
            "\ndef echo(value: Payload) -> Payload:\n    return value\n"
        )
        if module_kind == "utilities":
            root, module = self._family_module(tmp_path, "payload", source)
        else:
            root, package = u.Tests.create_lazy_init_workspace(tmp_path)
            module = package / (
                c.Infra.TYPINGS_PY if module_kind == "typings" else "payload.py"
            )
        tm.ok(u.Cli.atomic_write_text_file(module, source))
        imported = ".".join(
            module.relative_to(root / c.Infra.DEFAULT_SRC_DIR).with_suffix("").parts,
        )
        consumer = module.parent / "consumer.py"
        consumer_source = (
            '"""Alias consumer."""\n'
            "from __future__ import annotations\n"
            "from typing import get_args, get_type_hints\n"
            f"from {imported} import (\n"
            "    Payload as Data, Leaf, Item, Box, Items, Callback, Quoted, Defaults,\n"
            "    Forward, Later, _Record, echo,\n)\n\n"
            "class Consumer:\n"
            "    @staticmethod\n"
            "    def run(value: Data) -> Data:\n        return value\n\n"
            "    @staticmethod\n"
            "    def inspect() -> tuple[bool, ...]:\n"
            "        return (\n"
            "            get_args(Data.__value__)[0] is Leaf,\n"
            "            get_args(get_args(Data.__value__)[1])[0] is Data,\n"
            "            Item.__value__ is int,\n"
            "            get_args(Box.__value__)[0] is Box.__type_params__[0],\n"
            "            get_args(Box.__value__)[1] is Data,\n"
            "            get_args(get_args(Items.__value__)[0])[0]\n"
            "            is Items.__type_params__[0],\n"
            "            get_args(Callback.__value__)[0]\n"
            "            is Callback.__type_params__[0],\n"
            '            Box.__type_params__[0].__name__ == "Item",\n'
            '            Items.__type_params__[0].__name__ == "Item",\n'
            '            Callback.__type_params__[0].__name__ == "Item",\n'
            '            get_args(Quoted.__value__)[0] == "Item",\n'
            "            Defaults.__type_params__[0].__bound__ is Leaf,\n"
            "            Defaults.__type_params__[0].__default__ is str,\n"
            "            get_args(Forward.__value__)[0] is Later,\n"
            "            get_args(Later.__value__)[0] is Forward,\n"
            "            _Record.Field.__value__ is Data,\n"
            "            get_type_hints(Consumer.run)['return'] is Data,\n"
            "            get_type_hints(echo)['return'] is Data,\n"
            "            echo('value') == 'value',\n"
            "        )\n"
        )
        tm.ok(u.Cli.atomic_write_text_file(consumer, consumer_source))
        probe = (
            f"from {imported.rpartition('.')[0]}.consumer import Consumer\n"
            "print(all(Consumer.inspect()))\n"
            "print(Consumer.run({'items': ['value', 1]}))\n"
        )
        paths = (str(root / c.Infra.DEFAULT_SRC_DIR),)
        before = u.Tests.run_lazy_init_probe(probe, python_paths=paths, cwd=root)

        updated, residue = self._plan(
            root,
            {module: source, consumer: consumer_source},
        )

        tm.that(
            any(
                isinstance(node, ast.TypeAlias)
                for node in ast.parse(updated[module]).body
            ),
            eq=False,
        )
        for path, nested in updated.items():
            tm.ok(u.Cli.atomic_write_text_file(path, nested))
        after = u.Tests.run_lazy_init_probe(probe, python_paths=paths, cwd=root)
        tm.that(before[0], eq="True")
        tm.that(after, eq=before)
        tm.that(residue, eq={})

    @pytest.mark.parametrize(
        ("stem", "declaration"),
        [
            ("conftest", "def configure() -> None:\n    pass\n"),
            ("plugin", "def pytest_configure(config) -> None:\n    pass\n"),
            ("test_behavior", "def test_behavior() -> None:\n    pass\n"),
            ("fixtures", "@pytest.fixture\ndef resource() -> int:\n    return 1\n"),
        ],
    )
    def test_framework_registration_requires_a_coordinated_cutover(
        self,
        tmp_path: Path,
        stem: str,
        declaration: str,
    ) -> None:
        """Implicit module discovery must not silently lose hooks or fixtures."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        module = package / f"{stem}.py"
        source = '"""Framework registration."""\nimport pytest\n\n' + declaration
        tm.ok(u.Cli.atomic_write_text_file(module, source))

        if stem == "conftest":
            updated, residue = self._plan(root, {module: source})
            tree = ast.parse(updated[module])
            tm.that(
                all(
                    isinstance(node, ast.Import | ast.ImportFrom | ast.ClassDef)
                    for node in tree.body
                ),
                eq=True,
            )
            tm.that(
                len([node for node in tree.body if isinstance(node, ast.ClassDef)]),
                eq=1,
            )
            tm.that(updated[module], has="@staticmethod\n    def configure(")
            tm.that(residue, eq={})
            return

        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                rope_workspace=rope,
                sources={module: source},
            )

        tm.fail(planned, has="framework registration contract must move")
        tm.that(module.read_text(), eq=source)

    def test_module_alias_consumers_read_the_owner(self, tmp_path: Path) -> None:
        """Module-alias and member imports are rewired to the owner."""
        root, module = self._family_module(tmp_path, "atomic_thing", self.LOOSE_MODULE)
        owner = self._derived_owner(root, "atomic_thing")
        package = module.parent
        consumer_owner = self._derived_owner(root, "consumer_thing")
        imported = ".".join(
            module.relative_to(root / c.Infra.DEFAULT_SRC_DIR).with_suffix("").parts,
        )
        consumer_source = (
            '"""Consumer of the loose module."""\n\n'
            "from __future__ import annotations\n\n"
            f"from {imported.rsplit('.', 1)[0]} import atomic_thing as thing\n"
            f"from {imported} import write\n\n\n"
            f"class {consumer_owner}:\n"
            '    """Consumer owner."""\n\n'
            "    @staticmethod\n"
            "    def run() -> int:\n"
            '        return thing.write("x") + write("y") + thing.LIMIT\n\n\n'
            f'__all__: list[str] = ["{consumer_owner}"]\n'
        )
        consumer = package / "consumer_thing.py"
        tm.ok(u.Cli.atomic_write_text_file(consumer, consumer_source))
        probe = (
            f"import {imported} as original\n"
            f"import {imported.rpartition('.')[0]}.consumer_thing as consumer\n"
            f"print(consumer.{consumer_owner}.run())\n"
            "print(consumer.thing is original)\n"
        )
        before = u.Tests.run_lazy_init_probe(
            probe,
            python_paths=(str(root / c.Infra.DEFAULT_SRC_DIR),),
            cwd=root,
        )

        updated, residue = self._plan(
            root,
            {module: self.LOOSE_MODULE, consumer: consumer_source},
        )

        rewired = updated[consumer.resolve()]
        tm.that(rewired, has="import atomic_thing as thing")
        tm.that(rewired, lacks="import write")
        tm.that(
            rewired,
            has=f'thing.{owner}.write("x")',
        )
        for path, source in updated.items():
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        tm.that(
            u.Tests.run_lazy_init_probe(
                probe,
                python_paths=(str(root / c.Infra.DEFAULT_SRC_DIR),),
                cwd=root,
            ),
            eq=before,
        )
        tm.that(residue, eq={})

    def test_private_class_cross_module_reference_follows_plain_import(
        self,
        tmp_path: Path,
    ) -> None:
        """A dotted private-class reference through a plain module import rewires."""
        root, module = self._family_module(tmp_path, "atomic_thing", self.LOOSE_MODULE)
        owner = self._derived_owner(root, "atomic_thing")
        package = module.parent
        consumer_owner = self._derived_owner(root, "marker_client")
        imported = ".".join(
            module.relative_to(root / c.Infra.DEFAULT_SRC_DIR).with_suffix("").parts,
        )
        consumer_source = (
            '"""Marker client."""\n\n'
            "from __future__ import annotations\n\n"
            f"from {imported.rsplit('.', 1)[0]} import atomic_thing\n\n\n"
            f"class {consumer_owner}:\n"
            '    """Consumer owner."""\n\n'
            "    @staticmethod\n"
            "    def marked(marker: atomic_thing._Marker) -> bool:\n"
            "        return isinstance(marker, atomic_thing._Marker)\n\n\n"
            f'__all__: list[str] = ["{consumer_owner}"]\n'
        )
        consumer = package / "marker_client.py"
        tm.ok(u.Cli.atomic_write_text_file(consumer, consumer_source))
        paths = (str(root / c.Infra.DEFAULT_SRC_DIR),)
        before = u.Tests.run_lazy_init_probe(
            f"import {imported} as atomic_thing\n"
            f"from {imported.rpartition('.')[0]}.marker_client import (\n"
            f"    {consumer_owner}\n"
            f")\n"
            f"print({consumer_owner}.marked(atomic_thing._Marker()))\n",
            python_paths=paths,
            cwd=root,
        )

        updated, residue = self._plan(
            root,
            {module: self.LOOSE_MODULE, consumer: consumer_source},
        )

        rewired = updated[consumer.resolve()]
        tm.that(rewired, has=f"{owner}._Marker")
        tm.that(rewired, lacks="atomic_thing._Marker")
        for path, source in updated.items():
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        after = u.Tests.run_lazy_init_probe(
            f"import {imported} as atomic_thing\n"
            f"from {imported.rpartition('.')[0]}.marker_client import (\n"
            f"    {consumer_owner}\n"
            f")\n"
            f"print({consumer_owner}.marked(atomic_thing.{owner}._Marker()))\n",
            python_paths=paths,
            cwd=root,
        )
        tm.that(before, eq=["True"])
        tm.that(after, eq=before)
        tm.that(residue, eq={})

    def test_module_constant_from_import_survives_nesting(
        self,
        tmp_path: Path,
    ) -> None:
        """A consumer from-import of a call-free constant follows its owner."""
        root, module = self._family_module(tmp_path, "atomic_thing", self.LOOSE_MODULE)
        owner = self._derived_owner(root, "atomic_thing")
        package = module.parent
        consumer_owner = self._derived_owner(root, "limit_client")
        imported = ".".join(
            module.relative_to(root / c.Infra.DEFAULT_SRC_DIR).with_suffix("").parts,
        )
        consumer_source = (
            '"""Limit client."""\n\n'
            "from __future__ import annotations\n\n"
            f"from {imported} import LIMIT\n\n\n"
            f"class {consumer_owner}:\n"
            '    """Consumer owner."""\n\n'
            "    @staticmethod\n"
            "    def bounded(value: int) -> int:\n"
            "        return min(value, LIMIT)\n\n\n"
            f'__all__: list[str] = ["{consumer_owner}"]\n'
        )
        consumer = package / "limit_client.py"
        tm.ok(u.Cli.atomic_write_text_file(consumer, consumer_source))

        updated, residue = self._plan(
            root,
            {module: self.LOOSE_MODULE, consumer: consumer_source},
        )

        rewired = updated[consumer.resolve()]
        tm.that(rewired, has=f"from {imported} import {owner}")
        tm.that(rewired, has=f"return min(value, {owner}.LIMIT)")
        tm.that(rewired, lacks="import LIMIT")
        tm.that(residue, eq={})

    @staticmethod
    def test_family_suffix_excludes_the_shared_core_stem() -> None:
        """Every family suffix follows one shared, non-empty core class stem.

        A suffix spanning the whole core facade name doubles the stem in every
        derived owner (``<Project>FlextUtilities<Module>``).
        """
        stems = {
            getattr(flext_core, letter).__name__.removesuffix(family.suffix)
            for letter, family in u.Infra.facade_families().items()
        }
        tm.that(len(stems), eq=1)
        tm.that(stems.pop(), ne="")

    def test_owner_creation_reads_stay_module_level(self, tmp_path: Path) -> None:
        """A metaclass factory, its builder and their sentinel never nest."""
        root, module = self._family_module(tmp_path, "lazy_helpers", "")
        owner = self._derived_owner(root, "lazy_helpers")
        source = (
            '"""Lazy assembly of one family facade."""\n\n'
            "from __future__ import annotations\n\n"
            "from typing import Any\n\n\n"
            "_SENTINEL: type | None = None\n\n\n"
            "def _build_tree() -> type:\n"
            '    """Assemble the tree on first access."""\n'
            "    global _SENTINEL\n"
            "    if _SENTINEL is not None:\n"
            "        return _SENTINEL\n\n"
            "    class Tree:\n"
            '        """Assembled tree."""\n\n'
            "    _SENTINEL = Tree\n"
            "    return _SENTINEL\n\n\n"
            "def _lazy_meta() -> type:\n"
            '    """Build the lazy metaclass."""\n\n'
            "    class _Meta(type):\n"
            '        """Assemble the tree on first class-level access."""\n\n'
            "        def __getattr__(cls, name: str) -> Any:\n"
            '            if name == "Tree":\n'
            "                tree = _build_tree()\n"
            "                cls.Tree = tree\n"
            "                return tree\n"
            '            msg = f"no attribute {name!r}"\n'
            "            raise AttributeError(msg)\n\n"
            "    return _Meta\n\n\n"
            f"class {owner}(metaclass=_lazy_meta()):\n"
            '    """The facade owner."""\n\n'
            f'__all__: list[str] = ["{owner}"]\n'
        )
        tm.ok(u.Cli.atomic_write_text_file(module, source))

        updated, residue = self._plan(root, {module: source})

        kept = updated[module.resolve()]
        tm.that(
            self._top_level(kept),
            eq=(
                "_SENTINEL",
                "_build_tree",
                "_lazy_meta",
                owner,
                "__all__",
            ),
        )
        tm.that(kept, has="def _lazy_meta() -> type:")
        tm.that(kept, has="tree = _build_tree()")
        tm.that(residue, eq={})
        compile(kept, str(module), "exec")
