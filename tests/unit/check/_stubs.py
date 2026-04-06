"""Shared stubs and spy helpers for check tests.

Provides lightweight test doubles with monkeypatch-based substitution.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping, MutableSequence, Sequence

from tests import m, t
from tests.unit.check._shared_fixtures import create_gate_execution


class Spy:
    """Lightweight call-recording spy for monkeypatch substitution."""

    def __init__(
        self,
        return_value: t.Infra.InfraValue = None,
        side_effect: Sequence[t.Infra.InfraValue] | None = None,
    ) -> None:
        self.call_count: int = 0
        self.call_args: (
            tuple[tuple[t.Infra.InfraValue, ...], t.Infra.InfraMapping] | None
        ) = None
        self.call_args_list: MutableSequence[
            tuple[tuple[t.Infra.InfraValue, ...], t.Infra.InfraMapping]
        ] = []
        self.called: bool = False
        self._return_value: t.Infra.InfraValue = return_value
        self._side_effect: MutableSequence[t.Infra.InfraValue] | None = (
            list(side_effect) if side_effect else None
        )

    def __call__(
        self,
        *args: t.Infra.InfraValue,
        **kwargs: t.Infra.InfraValue,
    ) -> t.Infra.InfraValue:
        self.called = True
        self.call_count += 1
        self.call_args = (args, kwargs)
        self.call_args_list.append((args, kwargs))
        if self._side_effect:
            return self._side_effect.pop(0)
        return self._return_value

    @property
    def kwargs(self) -> t.Infra.InfraMapping:
        """Return kwargs from last call."""
        if self.call_args is None:
            return {}
        return self.call_args[1]

    @property
    def args(self) -> tuple[t.Infra.InfraValue, ...]:
        """Return positional args from last call."""
        if self.call_args is None:
            return ()
        return self.call_args[0]


def make_issue(
    file: str = "a.py",
    line: int = 1,
    column: int = 1,
    code: str = "E1",
    message: str = "Error",
) -> m.Infra.Issue:
    """Create a _m.Infra.Issue with defaults."""
    return m.Infra.Issue(
        file=file,
        line=line,
        column=column,
        code=code,
        message=message,
        severity="error",
    )


def make_project(
    name: str = "p",
    gates: MutableMapping[str, m.Infra.GateExecution] | None = None,
) -> m.Infra.ProjectResult:
    """Create a _ProjectResult with defaults."""
    resolved_gates: MutableMapping[str, m.Infra.GateExecution] = (
        gates if gates is not None else {"lint": create_gate_execution()}
    )
    return m.Infra.ProjectResult.model_validate({
        "project": name,
        "gates": resolved_gates,
    })


__all__ = [
    "Spy",
    "make_issue",
    "make_project",
]
