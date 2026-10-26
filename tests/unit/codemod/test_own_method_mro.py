"""Observe inherited dispatch after the public own-method source transformation.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import c, tm, u


class TestsFlextInfraOwnMethodMro:
    """Preserve lexical identity while making subclass behavior observable."""

    @staticmethod
    def test_subclass_override_and_shadowed_binding_are_preserved(
        tmp_path: Path,
    ) -> None:
        """Dispatch inherited helpers through the receiver and preserve local names."""
        source = (
            "class Owner:\n"
            "    @staticmethod\n"
            "    def helper(): return 'base'\n"
            "    @staticmethod\n"
            "    def deliver(): return Owner.helper()\n"
            "    @staticmethod\n"
            "    def shadow(Owner): return Owner.helper()\n"
            "class Derived(Owner):\n"
            "    @staticmethod\n"
            "    def helper(): return 'derived'\n"
            "class Local:\n"
            "    @staticmethod\n"
            "    def helper(): return 'local'\n"
        )
        rewritten, changes = u.Infra.rewrite_own_method_mro_calls(source)
        tm.that(changes, eq=("own-method-mro:Owner.deliver",))
        module = tmp_path / "mro_consumer.py"
        module.write_text(rewritten, encoding=c.DEFAULT_ENCODING)
        tm.that(
            u.Tests.run_lazy_init_probe(
                "from mro_consumer import Derived, Local\n"
                "print(Derived.deliver())\n"
                "print(Derived.shadow(Local))\n",
                python_paths=(str(tmp_path),),
            ),
            eq=["derived", "local"],
        )
        second, further_changes = u.Infra.rewrite_own_method_mro_calls(rewritten)
        tm.that(further_changes, eq=())
        tm.that(second.encode(c.DEFAULT_ENCODING), eq=module.read_bytes())

    @staticmethod
    @pytest.mark.parametrize(
        ("source", "reason"),
        [
            (
                (
                    "class Owner:\n"
                    "    def helper(self): return 'instance'\n"
                    "    @staticmethod\n"
                    "    def deliver(): return Owner.helper\n"
                ),
                "unbound reference",
            ),
            (
                (
                    "class Owner:\n"
                    "    @staticmethod\n"
                    "    def helper(): return 'static'\n"
                    "    @staticmethod\n"
                    "    def deliver(cls): return Owner.helper()\n"
                ),
                "capture a parameter",
            ),
        ],
    )
    def test_invalid_receiver_semantics_fail_before_edit(
        source: str, reason: str
    ) -> None:
        """Reject transformations that would change call signatures or capture names."""
        with pytest.raises(ValueError, match=reason):
            u.Infra.rewrite_own_method_mro_calls(source)
