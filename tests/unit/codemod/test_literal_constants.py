"""Public literal constant reuse preserves runtime values and lexical scope.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from tests import c, m, p, t, tm


class TestsFlextInfraConstantsLiteral:
    """Exercise the constants phase through its public planning boundary."""

    @staticmethod
    @pytest.mark.parametrize(
        ("literal_source", "return_source"),
        [
            ("'wire-value'", '"wire-value"'),
            ("'wire\\u002dvalue'", '"wire-value"'),
            ('"""wire-value"""', '"wire-value"'),
            ("'''wire-value'''", '"wire-value"'),
            ("r'wire-value'", 'r"wire-value"'),
            ("u'wire-value'", 'u"wire-value"'),
        ],
    )
    def test_literal_return_reuses_owner_and_reaches_fixed_point(
        constants_workspace: tuple[Path, Path],
        constant_candidate: t.Tests.SourceCandidate,
        infra_subprocess: p.Cli.CommandRunner,
        literal_source: str,
        return_source: str,
    ) -> None:
        """Equivalent quote forms reuse c while computed strings keep behavior."""
        root, package = constants_workspace
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
                f"    return {return_source}  # Preserve the wire contract.\n"
                "def computed(suffix: str = 'value') -> str:\n"
                "    return 'wire-' + suffix\n"
                "def computed_owner() -> str:\n"
                "    return 'WIRE-VALUE'\n"
                "def metadata(value: Annotated[str, 'wire-value'] = 'wire-value') "
                "-> Literal['wire-value']:\n"
                "    return value\n"
            ),
        }
        constant_candidate(sources, (consumer,))
        tm.ok(
            infra_subprocess.capture(
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

    @staticmethod
    @pytest.mark.parametrize("case", ["shadowed", "ambiguous"])
    def test_unproven_literal_owner_fails_before_publication(
        constants_workspace: tuple[Path, Path],
        constant_candidate: t.Tests.SourceCandidate,
        case: str,
    ) -> None:
        """Lexical facade collisions and competing string owners fail closed."""
        _root, package = constants_workspace
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
        message = (
            "literal constant facade c is shadowed"
            if case == "shadowed"
            else "literal return has ambiguous public constant owners"
        )
        with pytest.raises(ValueError, match=message):
            constant_candidate(sources, ())
