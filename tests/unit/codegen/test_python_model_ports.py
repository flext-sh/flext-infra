"""The static model's opaque cache preserves its writable protocol contract.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import p, tm, u


class TestsFlextInfraPythonModelPorts:
    """Exercise the real parser through a caller-owned, typed mutable cache."""

    @staticmethod
    def test_parser_populates_the_injected_cache_once(tmp_path: Path) -> None:
        """The shared port retains its identity and returns the cached facts."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        tm.ok(
            u.Cli.atomic_write_text_file(
                source, "class Observed:\n    pass\n__all__ = ['Observed']\n"
            )
        )
        name = f"{package.name}.provider"
        with u.Infra.workspace_snapshot(root, (root,)) as snapshot:
            cache = snapshot.python_module_facts
            run: p.Infra.PythonModelRun = u.Infra.python_model_run(
                snapshot.engine, {name: source}, module_facts=cache
            )
            tm.that(run.modules is cache, eq=True)
            first = u.Infra.python_model_module_at(run, source, name)
            tm.that(len(cache), eq=1)
            tm.that(next(iter(cache.values())) is first, eq=True)
            second = u.Infra.python_model_module_at(run, source, name)
            tm.that(second is first, eq=True)
            tm.that(len(cache), eq=1)

    @staticmethod
    def test_type_checking_annotations_are_not_standin_defects(tmp_path: Path) -> None:
        """A type-only declaration does not exist at runtime (ADR-018 rule 5)."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "type_only.py"
        tm.ok(
            u.Cli.atomic_write_text_file(
                source,
                "from __future__ import annotations\n"
                "from pathlib import Path\n"
                "from typing import TYPE_CHECKING\n"
                "class TypeOnly:\n"
                "    if TYPE_CHECKING:\n"
                "        base_dir: Path | None\n"
                "__all__ = ['TypeOnly']\n",
            )
        )
        name = f"{package.name}.type_only"
        with u.Infra.workspace_snapshot(root, (root,)) as snapshot:
            run: p.Infra.PythonModelRun = u.Infra.python_model_run(
                snapshot.engine,
                {name: source},
                module_facts=snapshot.python_module_facts,
            )
            facts = u.Infra.python_model_module_at(run, source, name)
        tm.that(facts.class_standin_defects.get("TypeOnly", ()), empty=True)

    @staticmethod
    def test_type_checking_members_are_not_runtime_class_members(
        tmp_path: Path,
    ) -> None:
        """A type-only declaration binds no class member at runtime."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "type_only_members.py"
        tm.ok(
            u.Cli.atomic_write_text_file(
                source,
                "from typing import TYPE_CHECKING\n"
                "class TypeOnlyMembers:\n"
                "    if TYPE_CHECKING:\n"
                "        def run_raw(self) -> None: ...\n"
                "        declared: int\n"
                "    def run(self) -> None: ...\n"
                "    value = 1\n"
                "__all__ = ['TypeOnlyMembers']\n",
            )
        )
        name = f"{package.name}.type_only_members"
        with u.Infra.workspace_snapshot(root, (root,)) as snapshot:
            run: p.Infra.PythonModelRun = u.Infra.python_model_run(
                snapshot.engine,
                {name: source},
                module_facts=snapshot.python_module_facts,
            )
            facts = u.Infra.python_model_module_at(run, source, name)
        tm.that(facts.class_members["TypeOnlyMembers"], eq=("run", "value"))

    @staticmethod
    def test_unpacking_binds_every_plain_class_member(tmp_path: Path) -> None:
        """An unpacking target binds each plain name at class creation."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "unpacking_members.py"
        tm.ok(
            u.Cli.atomic_write_text_file(
                source,
                "class UnpackingMembers:\n"
                "    first, second = 1, 2\n"
                "    head, *tail = (1, 2, 3)\n"
                "    holder.attr = 4\n"
                "    def method(self) -> None: ...\n"
                "__all__ = ['UnpackingMembers']\n",
            )
        )
        name = f"{package.name}.unpacking_members"
        with u.Infra.workspace_snapshot(root, (root,)) as snapshot:
            run: p.Infra.PythonModelRun = u.Infra.python_model_run(
                snapshot.engine,
                {name: source},
                module_facts=snapshot.python_module_facts,
            )
            facts = u.Infra.python_model_module_at(run, source, name)
        tm.that(
            facts.class_members["UnpackingMembers"],
            eq=("first", "second", "head", "tail", "method"),
        )
