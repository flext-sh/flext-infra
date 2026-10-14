"""Public numeric and frozenset reuse retains observable runtime contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

from tests import c, m, p, t, tm


class TestsFlextInfraImmutableConstants:
    """Observe exact scalar types and construction identity after public plans."""

    @staticmethod
    def test_integer_returns_and_frozenset_predicates_reach_fixed_point(
        constants_workspace: t.Pair[Path, Path],
        constant_candidate: Callable[
            [t.MappingKV[Path, str], t.VariadicTuple[Path]], t.MappingKV[Path, str]
        ],
        infra_subprocess: p.Cli.CommandRunner,
    ) -> None:
        """Immutable reuse preserves types, membership and fresh construction."""
        root, package = constants_workspace
        owner = package / c.Infra.CONSTANTS_PY
        initializer = package / c.Infra.INIT_PY
        consumer = package / "consumer.py"
        sources = {
            owner: (
                "from typing import ClassVar\n"
                "from enum import IntEnum\n"
                "class Values:\n"
                "    NUMBER: ClassVar[int] = 1\n"
                "    WORDS: ClassVar[frozenset[str]] = frozenset({'wire'})\n"
                "    NUMBERS: ClassVar[frozenset[int]] = frozenset({1})\n"
                "    DYNAMIC: ClassVar[frozenset[str]] = frozenset({'wire'.upper()})\n"
                "    class Code(IntEnum):\n"
                "        ONE = 1\n"
                "c = Values\n"
                "__all__ = ['c']\n"
            ),
            initializer: "from .constants import c\n__all__ = ['c']\n",
            consumer: (
                f"from {package.name} import c\n"
                "def number():\n"
                "    return 1\n"
                "def flag():\n"
                "    return True\n"
                "def fractional():\n"
                "    return 1.0\n"
                "def arithmetic():\n"
                "    return 1 + 0\n"
                "def code():\n"
                "    return c.Code.ONE\n"
                "def contains(item):\n"
                "    return item in frozenset({'wire'})\n"
                "def missing(item):\n"
                "    return item not in frozenset({'wire'})\n"
                "def numeric_contains(item):\n"
                "    return item in frozenset({1})\n"
                "def constructed():\n"
                "    return frozenset({'wire'})\n"
                "def dynamic_owner(item):\n"
                "    return item in frozenset({'WIRE'})\n"
                "def dynamic_input(item, values):\n"
                "    return item in frozenset(values)\n"
                "def shadowed(item, frozenset):\n"
                "    return item in frozenset({'wire'})\n"
                "def observed_membership(observe):\n"
                "    return observe(frozenset({'wire'})) in frozenset({'wire'})\n"
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
                        f"from {package.name} import c\n"
                        f"from {package.name} import consumer as consumer\n"
                        "assert type(consumer.number()) is int\n"
                        "assert consumer.number() == c.NUMBER\n"
                        "assert type(consumer.flag()) is bool\n"
                        "assert type(consumer.fractional()) is float\n"
                        "assert consumer.code() is c.Code.ONE\n"
                        "assert consumer.contains('wire')\n"
                        "assert not consumer.missing('wire')\n"
                        "assert consumer.numeric_contains(1)\n"
                        "assert consumer.constructed() is not consumer.constructed()\n"
                        "c.NUMBER = 23\n"
                        "c.WORDS = frozenset({'changed'})\n"
                        "c.NUMBERS = frozenset({23})\n"
                        "c.DYNAMIC = frozenset({'changed'})\n"
                        "assert consumer.number() == c.NUMBER\n"
                        "assert consumer.arithmetic() == 1\n"
                        "assert consumer.flag() is True\n"
                        "assert consumer.fractional() == 1.0\n"
                        "assert consumer.contains('changed')\n"
                        "assert not consumer.contains('wire')\n"
                        "assert consumer.missing('wire')\n"
                        "assert consumer.numeric_contains(23)\n"
                        "assert consumer.constructed() == frozenset({'wire'})\n"
                        "assert consumer.constructed() is not consumer.constructed()\n"
                        "assert consumer.dynamic_owner('WIRE')\n"
                        "assert consumer.dynamic_input('wire', {'wire'})\n"
                        "assert consumer.shadowed('custom', "
                        "lambda values: {'custom'})\n"
                        "seen = []\n"
                        "def observe(value):\n"
                        "    seen.append(value)\n"
                        "    return 'changed'\n"
                        "assert consumer.observed_membership(observe)\n"
                        "assert consumer.observed_membership(observe)\n"
                        "assert seen[0] == seen[1] == frozenset({'wire'})\n"
                        "assert seen[0] is not seen[1]\n"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )

    @staticmethod
    def test_reassigned_and_mutable_owners_are_not_candidates(
        constants_workspace: t.Pair[Path, Path],
        constant_candidate: Callable[
            [t.MappingKV[Path, str], t.VariadicTuple[Path]], t.MappingKV[Path, str]
        ],
    ) -> None:
        """Reassignment, mutable containers and call-produced values stay local."""
        _root, package = constants_workspace
        owner = package / c.Infra.CONSTANTS_PY
        consumer = package / "consumer.py"
        sources = {
            owner: (
                "class Values:\n"
                "    NUMBER = 1\n"
                "    NUMBER = 2\n"
                "    MUTABLE = {'wire'}\n"
                "    COMPUTED = int('7')\n"
                "c = Values\n"
            ),
            consumer: (
                "def reassigned():\n"
                "    return 2\n"
                "def computed():\n"
                "    return 7\n"
                "def predicate(value):\n"
                "    return value in frozenset({'wire'})\n"
            ),
        }
        constant_candidate(sources, ())
