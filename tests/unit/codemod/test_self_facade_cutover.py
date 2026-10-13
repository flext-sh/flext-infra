"""Exercise declared utility ownership through the public semantic phase.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

import pytest

from flext_infra import infra
from tests import c, m, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraSelfFacadeCutover:
    """Preserve eager execution, lexical bindings and standalone consumers."""

    @staticmethod
    def test_external_declaration_import_survives_a_local_model_mask(
        tmp_path: Path,
    ) -> None:
        """A distinct model binding cannot replace a permitted external helper."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        declarations = package / "_models"
        declarations.mkdir()
        (declarations / c.Infra.INIT_PY).write_text("", encoding="utf-8")
        consumer = declarations / "consumer.py"
        sources = {
            package / c.Infra.INIT_PY: "from .models import Models as m\n",
            package / c.Infra.MODELS_PY: (
                "from flext_core import m as core_m\n"
                "class Models(core_m):\n"
                "    empty = None\n"
                "__all__ = ('Models',)\n"
            ),
            consumer: (
                f"from {package.name} import m\n"
                "from flext_core import t, u\n"
                "from typing_extensions import TypeForm\n"
                "class Consumer(m.ContractModel):\n"
                "    values: t.MutableSequenceOf[str] = m.Field("
                "default_factory=u.empty(TypeForm(t.MutableSequenceOf[str])), "
                "description='Consumer values')\n"
            ),
        }
        for path, source in sources.items():
            path.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.SELF_FACADE_IMPORT,
                    rope_workspace=rope,
                    sources=sources,
                )
            )
        tm.that(edits, empty=True)
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    f"from {package.name}._models.consumer import Consumer; "
                    "assert Consumer().values == []; "
                    "print('external declaration accepted')",
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env={
                        c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(
                            root / c.Infra.DEFAULT_SRC_DIR
                        )
                    }
                ),
            )
        )
        tm.that(result.stdout.strip(), eq="external declaration accepted")

    @staticmethod
    @pytest.mark.parametrize("tier", ["private", "public", "examples"])
    def test_declaring_model_receiver_preserves_default_factory(
        tmp_path: Path,
        tier: str,
    ) -> None:
        """Execute the rewritten model declaration through a real package import."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        if tier == "private":
            declarations = package / "_models"
            declarations.mkdir()
            (declarations / c.Infra.INIT_PY).write_text("", encoding="utf-8")
            consumer = declarations / "consumer.py"
            module = f"{package.name}._models.consumer"
        elif tier == "public":
            consumer = package / c.Infra.MODELS_PY
            module = f"{package.name}.models"
        else:
            declarations = root / tier
            declarations.mkdir()
            (declarations / c.Infra.INIT_PY).write_text("", encoding="utf-8")
            consumer = declarations / c.Infra.MODELS_PY
            module = f"{tier}.models"
        source = (
            "from flext_core import m, t, u\n"
            "from typing_extensions import TypeForm\n"
            "type Bag[T] = t.MutableSequenceOf[T]\n"
            "class Consumer(m.ContractModel):\n"
            '    """Consumer-owned collection declaration."""\n'
            "    values: Bag[str] = m.Field(default_factory=u.empty("
            'TypeForm(Bag[str])), description="Consumer values")\n'
        )
        consumer.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.SELF_FACADE_IMPORT,
                    rope_workspace=rope,
                    sources={consumer: source},
                )
            )
            tm.that(edits, empty=False)
            for edit in edits:
                tm.ok(u.Cli.atomic_write_text_file(edit.file_path, edit.updated_source))
            remaining = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.SELF_FACADE_IMPORT,
                    rope_workspace=rope,
                    sources={consumer: consumer.read_text(encoding="utf-8")},
                )
            )
        tm.that(remaining, empty=True)
        output = tm.ok(
            u.Cli.run(
                [
                    sys.executable,
                    "-c",
                    (
                        f"from {module} import Consumer; "
                        "first, second = Consumer(), Consumer(); "
                        "first.values.append('consumer'); "
                        "assert second.values == []; "
                        "assert Consumer.model_validate_json("
                        "first.model_dump_json()).values == first.values; "
                        "print('declaration contract accepted')"
                    ),
                ],
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env={
                        c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: os.pathsep.join((
                            str(root / c.Infra.DEFAULT_SRC_DIR),
                            str(root),
                        ))
                    }
                ),
            )
        )
        tm.that(output.stdout.strip(), eq="declaration contract accepted")

    @staticmethod
    @pytest.mark.parametrize(
        "declaration",
        [
            "from {package} import u\n",
            "from {package} import u as first, u as second\n",
        ],
    )
    def test_declared_leaf_breaks_self_composition_cycle(
        tmp_path: Path,
        declaration: str,
    ) -> None:
        """Import a peripheral project in a fresh process after public planning."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        owner = package / "_utilities" / "owner.py"
        owner.parent.mkdir()
        (owner.parent / c.Infra.INIT_PY).write_text("", encoding="utf-8")
        consumer = owner.parent / "consumer.py"
        first, second = ("first", "second") if "first" in declaration else ("u", "u")
        sources = {
            package / c.Infra.INIT_PY: (
                "from .utilities import Utilities as u\n__all__ = ('u',)\n"
            ),
            package / c.Infra.UTILITIES_PY: (
                "from ._utilities.owner import Owner\n"
                "from ._utilities.consumer import Consumer\n"
                "class Utilities(Owner):\n"
                "    pass\n"
                "__all__ = ('Utilities', 'Consumer')\n"
            ),
            owner: (
                "class Owner:\n"
                "    @staticmethod\n"
                "    def render(value: str) -> str:\n"
                "        return value.upper()\n"
                "__all__ = ('Owner',)\n"
            ),
            consumer: declaration.format(package=package.name)
            + (
                f"VALUE = {first}.render('module')\n"
                "class Consumer:\n"
                f"    value = {second}.render('class')\n"
                "    @staticmethod\n"
                f"    def render(value={first}.render('default')):\n"
                "        '''Documented public operation.'''\n"
                f"        return {second}.render(value)\n"
                "def shadow(u):\n"
                "    return u.render('local')\n"
                "TEXT = 'u.render stays a string'\n"
                "__all__ = ('Consumer', 'VALUE', 'TEXT', 'shadow')\n"
            ),
        }
        for path, source in sources.items():
            path.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.SELF_FACADE_IMPORT,
                    rope_workspace=rope,
                    sources=sources,
                ),
            )
            tm.that(edits, empty=False)
            for edit in edits:
                tm.ok(
                    u.Cli.atomic_write_text_file(edit.file_path, edit.updated_source),
                )
                sources[edit.file_path] = edit.updated_source
            remaining = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.SELF_FACADE_IMPORT,
                    rope_workspace=rope,
                    sources=sources,
                ),
            )
        tm.that(remaining, empty=True)
        output = tm.ok(
            u.Cli.run(
                [
                    sys.executable,
                    "-c",
                    (
                        f"from {package.name} import u; "
                        f"from {package.name}._utilities.consumer import "
                        "Consumer, VALUE, TEXT, shadow; "
                        "assert VALUE == 'MODULE'; "
                        "assert Consumer.value == 'CLASS'; "
                        "assert Consumer.render() == 'DEFAULT'; "
                        "assert Consumer.render.__doc__ == "
                        "'Documented public operation.'; "
                        "assert shadow(u) == 'LOCAL'; "
                        "assert TEXT == 'u.render stays a string'; "
                        "print('consumer contract accepted')"
                    ),
                ],
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env={
                        c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(
                            root / c.Infra.DEFAULT_SRC_DIR,
                        ),
                    },
                ),
            ),
        )
        tm.that(output.stdout.strip(), eq="consumer contract accepted")

    @staticmethod
    @pytest.mark.parametrize(
        ("method", "body", "expected"),
        [
            (
                (
                    "    @classmethod\n"
                    "    def render(cls, value):\n"
                    "        return cls.prefix + value\n"
                ),
                "VALUE = u.render('input')\n",
                "requires facade dispatch",
            ),
            (
                ("    @staticmethod\n    def render(value):\n        return value\n"),
                "VALUE = u.unknown('input')\n",
                "callable owner is unresolved",
            ),
            (
                ("    @staticmethod\n    def render(value):\n        return value\n"),
                ("class Owner:\n    pass\nVALUE = u.render('input')\n"),
                "receiver is shadowed",
            ),
        ],
    )
    def test_owner_failure_preserves_input(
        tmp_path: Path,
        method: str,
        body: str,
        expected: str,
    ) -> None:
        """Keep unresolved and contextual bindings causal and unpublished."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        owner = package / "_utilities" / "owner.py"
        owner.parent.mkdir()
        consumer = owner.parent / "consumer.py"
        source = f"from {package.name} import u\n{body}"
        sources = {
            package / c.Infra.INIT_PY: (
                "from .utilities import Utilities as u\n__all__ = ('u',)\n"
            ),
            package / c.Infra.UTILITIES_PY: (
                "from ._utilities.owner import Owner\n"
                "class Utilities(Owner):\n"
                "    pass\n"
                "__all__ = ('Utilities',)\n"
            ),
            owner: f"class Owner:\n{method}__all__ = ('Owner',)\n",
            consumer: source,
        }
        for path, content in sources.items():
            path.write_text(content, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            result = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.SELF_FACADE_IMPORT,
                rope_workspace=rope,
                sources=sources,
            )
        tm.fail(result, has=expected)
        tm.that(isinstance(result.exception, ValueError), eq=True)
        tm.that(consumer.read_text(encoding="utf-8"), eq=source)
