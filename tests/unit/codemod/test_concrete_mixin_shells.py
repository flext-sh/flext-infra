"""Competing declaration shells are reported natively; real contracts are kept.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from pathlib import Path

import pytest

from flext_infra.codemod import FlextInfraModGateEngine
from tests import c, p, tm, u


class TestsFlextInfraConcreteMixinShells:
    """Report declaration-only shells; keep protocols, abstract and overloads."""

    @staticmethod
    @pytest.mark.slow
    def test_inline_shells_preserve_native_declaration_identities(
        mod_workspace: Path,
        native_consumer: p.Tests.NativeConsumer,
    ) -> None:
        """Reject competing shells, not real aliased contracts or live methods."""
        owner = Path(__file__).resolve().parents[3]
        with u.Infra.codemod_workspace_snapshot(owner) as snapshot:
            plan = tm.ok(u.Infra.codemod_rule_plan(snapshot))
        rule = next(
            item
            for item in plan.rules
            if item.resource.name == "concrete-mixin-runtime-ellipsis.yml"
        )
        consumer = mod_workspace / "consumer.py"
        source = (
            c.Infra.AUTOGEN_HEADER
            + "\n"
            + """from abc import ABC as Abstract, abstractmethod as required
from typing import TYPE_CHECKING as types_only, Protocol as Contract
from typing import overload as signature, override as marked

class ReaderMixin(Contract):
    @property
    def value(self) -> str: ...

class AbstractMixin(Abstract):
    @marked
    @required
    def read(self, required: str) -> str: ...

class Overloads:
    if types_only:
        @signature
        def select(self, value: int) -> int: ...
        @signature
        def select(self, value: str) -> str: ...
    def select(self, value: int | str) -> int | str:
        return value

class InlineOwner:
    if types_only:
        @property
        def source_project(self) -> str: ...
        @staticmethod
        def generated(content: bytes | None) -> bool:
            del content
        def cleanup(self, plan: str) -> str:
            del plan
            raise NotImplementedError(type(self).__qualname__)
    def live(self, value: str) -> str:
        return value

class RuntimeMixin:
    def missing(self) -> int: ...

class Protocol:
    pass

class PretenderMixin(Protocol):
    def counterfeit(self) -> str: ...

def substitute(function):
    return function

class DecoratedMixin:
    @substitute
    def decorated_shell(self) -> str: ...

not_typing = False
class ConditionalOwner:
    if not_typing:
        def conditional(self) -> str: ...
"""
        )
        tm.ok(u.Cli.atomic_write_text_file(consumer, source))
        native_consumer(
            "from inspect import isabstract\nfrom runpy import run_path\n"
            f"observed = run_path({str(consumer)!r})\n"
            "assert isabstract(observed['AbstractMixin'])\n"
            "value = 'retained-reference'\n"
            "assert observed['InlineOwner']().live(value) is value\n"
            "assert observed['Overloads']().select(value) is value\n",
            cwd=mod_workspace,
        )
        report = tm.ok(
            FlextInfraModGateEngine.scan(
                mod_workspace,
                fix=False,
                selection=(rule.id,),
                source_files=(consumer,),
            )
        )
        expected = (
            "source_project",
            "generated",
            "cleanup",
            "missing",
            "counterfeit",
            "decorated_shell",
        )
        tm.that(len(report.entries), eq=len(expected))
        for name in expected:
            tm.that(
                sum(entry.text.startswith(f"def {name}(") for entry in report.entries),
                eq=1,
            )
        tm.that({entry.rule_id for entry in report.entries}, eq={rule.id})
        tm.that(consumer.read_text(encoding=c.DEFAULT_ENCODING), eq=source)


__all__: list[str] = ["TestsFlextInfraConcreteMixinShells"]
