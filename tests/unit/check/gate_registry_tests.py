"""Gate vocabulary contract: one SSOT, every gate reachable.

``c.Infra.GATE_TOOLS_BY_KIND`` owns the gate ids; the registry classes
declare their ids from the same constants and the `make check` vocabulary
is derived from it, so the surfaces cannot diverge.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import config
from flext_infra.check import FlextInfraGateRegistry
from tests import c, tm


class TestsFlextInfraGateRegistry:
    """Tests for ``FlextInfraGateRegistry``."""

    @staticmethod
    def test_every_allowed_gate_resolves_in_registry() -> None:
        """Test every allowed gate resolves in registry."""
        registry = FlextInfraGateRegistry.default()
        for gate_id in c.Infra.ALLOWED_GATES:
            gate_cls = registry.get(gate_id)
            tm.ok(gate_cls is not None)
            tm.ok(gate_cls is not None and gate_cls.gate_id == gate_id)

    @staticmethod
    def test_check_vocabulary_is_the_whole_registry() -> None:
        """Every registered gate checks read-only, the formatters included."""
        tm.that(frozenset(c.Infra.CANONICAL_GATE_IDS), eq=c.Infra.ALLOWED_GATES)

    @staticmethod
    def test_default_and_fixable_are_subsets_of_check_vocabulary() -> None:
        """Default, CI, commit and fixable gates stay in the check vocabulary."""
        make = config.Infra.codegen.make
        allowed = frozenset(make.check_gates_allowed)
        tm.ok(frozenset(make.check_gates_default) <= allowed)
        tm.ok(frozenset(make.pre_commit_check_gates) <= allowed)
        tm.ok(frozenset(make.check_gates_ci) <= allowed)
        tm.that(
            frozenset(c.Infra.CANONICAL_FIXABLE_GATE_IDS)
            <= frozenset(c.Infra.CANONICAL_GATE_IDS),
            eq=True,
        )

    @staticmethod
    def test_fixable_gate_vocabulary_matches_the_registry() -> None:
        """The Make fixable-gate vocabulary equals the gates that declare can_fix.

        `make fix` routes through `check run --fix`. Without a
        gate selector that run executes EVERY gate, including pyright and
        mypy, which cannot fix anything and cost ~37s -- the verb timed out
        (exit 124).

        Runtime contract: verbs own tools by intent. `fmt` owns formatting
        (ruff format plus the fmt_gates writers such as markdown-format),
        `fix` repairs findings (markdown, markdown-code, smells), `check` is
        read-only: it runs every gate's read-only side, including ``format
        --check``, and `format` stays out of FIXABLE (fix never formats).
        """
        registry = FlextInfraGateRegistry.default()
        mutating = {
            gate_id
            for gate_id in c.Infra.ALLOWED_GATES
            if (gate_cls := registry.get(gate_id)) is not None and gate_cls.can_fix
        }
        # `make fix` owns every mutating check-gate EXCEPT the fmt-owned
        # formatters (single-pass verb law: one operation per tool per verb).
        fmt_owned = set(config.Infra.codegen.make.fmt_gates)
        tm.that(set(c.Infra.CANONICAL_FIXABLE_GATE_IDS), eq=mutating - fmt_owned)
        tm.ok(fmt_owned & set(c.Infra.CANONICAL_GATE_IDS) <= mutating)
        tm.ok(fmt_owned <= mutating)
        # `format` applies only through `make fmt`; check runs its read-only
        # side, and fix never formats.
        tm.ok(c.Infra.FORMAT not in c.Infra.CANONICAL_FIXABLE_GATE_IDS)
        tm.ok(c.Infra.FORMAT in c.Infra.CANONICAL_GATE_IDS)
