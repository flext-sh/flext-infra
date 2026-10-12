"""Exercise declared utility ownership through the public semantic phase.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

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
        finding = TestsFlextInfraSelfFacadeCutover._finding(
            consumer.relative_to(root),
            package.name,
        )
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.SELF_FACADE_IMPORT,
                    rope_workspace=rope,
                    sources=sources,
                    findings=(finding,),
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
                    findings=(finding,),
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
                findings=(
                    TestsFlextInfraSelfFacadeCutover._finding(
                        consumer.relative_to(root),
                        package.name,
                    ),
                ),
            )
        tm.fail(result, has=expected)
        tm.that(isinstance(result.exception, ValueError), eq=True)
        tm.that(consumer.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    def _finding(path: Path, package: str) -> m.Infra.ModScanFinding:
        rule = c.Infra.SEMANTIC_CUTOVER_RULE_IDS[
            c.Infra.SemanticCutoverPhase.SELF_FACADE_IMPORT
        ]
        return m.Infra.ModScanFinding(
            rule_file=f"{rule}.yml",
            rule_id=rule,
            repository="fixture",
            file=path,
            range={},
            text=f"from {package} import u",
            actionable=False,
            classification=c.Infra.ModScanFindingClass.DETECTION_ONLY,
            payload={},
        )
