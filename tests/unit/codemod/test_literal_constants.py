"""Public literal constant reuse preserves runtime values and lexical scope.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from flext_infra import infra
from tests import c, m, tm, u


class TestsFlextInfraLiteralConstants:
    """Exercise the constants phase through its public planning boundary."""

    @staticmethod
    @pytest.mark.parametrize(
        "literal_source",
        [
            "'wire-value'",
            "'wire\\u002dvalue'",
            '"""wire-value"""',
            "'''wire-value'''",
        ],
    )
    def test_literal_return_reuses_owner_and_reaches_fixed_point(
        tmp_path: Path, literal_source: str
    ) -> None:
        """Equivalent quote forms reuse c while computed strings keep behavior."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        owner = package / c.Infra.CONSTANTS_PY
        initializer = package / c.Infra.INIT_PY
        consumer = package / "consumer.py"
        sources = {
            owner: (
                "from typing import ClassVar\n"
                "class Values:\n"
                f"    TOKEN: ClassVar[str] = {literal_source}\n"
                "    COMPUTED: ClassVar[str] = 'wire-value'.upper()\n"
                "c = Values\n"
                "__all__ = ['c']\n"
            ),
            initializer: "from .constants import c\n__all__ = ['c']\n",
            consumer: (
                "from typing import Annotated, Literal\n"
                '"""wire-value"""\n'
                "def value() -> str:\n"
                '    """wire-value"""\n'
                '    return "wire-value"  # Preserve the wire contract.\n'
                "def computed(suffix: str = 'value') -> str:\n"
                "    return 'wire-' + suffix\n"
                "def computed_owner() -> str:\n"
                "    return 'WIRE-VALUE'\n"
                "def metadata(value: Annotated[str, 'wire-value'] = 'wire-value') "
                "-> Literal['wire-value']:\n"
                "    return value\n"
            ),
        }
        for path, source in sources.items():
            path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with infra.rope_workspace(root) as workspace:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS,
                    rope_workspace=workspace,
                    sources=sources,
                )
            )
            tm.that(tuple(edit.file_path for edit in edits), eq=(consumer,))
            proposed = {
                **sources,
                **{edit.file_path: edit.updated_source for edit in edits},
            }
            repeated = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS,
                    rope_workspace=workspace,
                    sources=proposed,
                )
            )
            tm.that(repeated, empty=True)
        for path, source in proposed.items():
            path.write_text(source, encoding=c.DEFAULT_ENCODING)
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-W",
                    "error",
                    "-c",
                    (
                        f"from {package.name} import c; "
                        f"from {package.name}.consumer import "
                        "value, computed, computed_owner, metadata; "
                        "assert value() == c.TOKEN; "
                        "assert computed() == c.TOKEN; "
                        "assert computed_owner() == c.COMPUTED; "
                        "assert metadata() == c.TOKEN; "
                        "assert value.__doc__ == c.TOKEN; "
                        "c.TOKEN = 'updated-wire'; "
                        "c.COMPUTED = 'updated-computed'; "
                        "assert value() == c.TOKEN; "
                        "assert computed() == 'wire-value'; "
                        "assert computed_owner() == 'WIRE-VALUE'; "
                        "assert metadata() == 'wire-value'"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True)

    @staticmethod
    @pytest.mark.parametrize("case", ["shadowed", "ambiguous"])
    def test_unproven_literal_owner_fails_before_publication(
        tmp_path: Path, case: str
    ) -> None:
        """Lexical facade collisions and competing string owners fail closed."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        owner = package / c.Infra.CONSTANTS_PY
        consumer = package / "consumer.py"
        extra = (
            "    OTHER: ClassVar[str] = 'wire-value'\n" if case == "ambiguous" else ""
        )
        source = (
            "def value(c):\n    return 'wire-value'\n"
            if case == "shadowed"
            else "def value():\n    return 'wire-value'\n"
        )
        sources = {
            owner: (
                "from typing import ClassVar\n"
                "class Values:\n"
                "    TOKEN: ClassVar[str] = 'wire-value'\n"
                f"{extra}"
                "c = Values\n"
            ),
            consumer: source,
        }
        for path, text in sources.items():
            path.write_text(text, encoding=c.DEFAULT_ENCODING)
        message = (
            "literal constant facade c is shadowed"
            if case == "shadowed"
            else "literal return has ambiguous public constant owners"
        )
        with (
            infra.rope_workspace(root) as workspace,
            pytest.raises(ValueError, match=message),
        ):
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS,
                rope_workspace=workspace,
                sources=sources,
            )
