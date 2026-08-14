"""Tests for gate registration of the new durissimas gates.

`loc-cap`, `boundary`, and `canonical-alias` must be in the SSOT-derived
ALLOWED_GATES and resolve through the registry.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, m, p, r, u
from flext_infra.check.workspace_check_gates import FlextInfraGateRegistry
from flext_infra.gates.canonical_alias import FlextInfraCanonicalAliasGate
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

    from tests import t


class TestGateRegistry:
    def test_new_gates_in_allowed(self) -> None:
        tm.that("loc-cap" in c.Infra.ALLOWED_GATES, eq=True)
        tm.that("boundary" in c.Infra.ALLOWED_GATES, eq=True)
        tm.that("canonical-alias" in c.Infra.ALLOWED_GATES, eq=True)

    def test_registry_resolves_loc_cap(self) -> None:
        tm.that(FlextInfraGateRegistry.default().get("loc-cap") is not None, eq=True)

    def test_registry_resolves_boundary(self) -> None:
        tm.that(FlextInfraGateRegistry.default().get("boundary") is not None, eq=True)

    def test_registry_resolves_canonical_alias(self) -> None:
        tm.that(
            FlextInfraGateRegistry.default().get("canonical-alias") is not None, eq=True
        )

    def test_canonical_alias_fix_fails_on_read_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        project_dir = tmp_path / "demo"
        package_dir = project_dir / "src" / "demo"
        package_dir.mkdir(parents=True)
        source_file = package_dir / "service.py"
        source_file.write_text(
            "from __future__ import annotations\n\n"
            "from flext_core import c\n\n"
            "VALUE = c.MAX_SIZE\n",
            encoding="utf-8",
        )

        def _fail_read(path: Path) -> p.Result[str]:
            return r[str].fail(f"read failed: {path.name}")

        monkeypatch.setattr(u.Cli, "files_read_text", _fail_read)
        gate = FlextInfraCanonicalAliasGate(tmp_path)
        result = gate.fix(
            project_dir,
            m.Infra.GateContext(
                workspace=tmp_path, reports_dir=tmp_path / "reports", apply_fixes=True
            ),
        )

        tm.that(result.result.passed, eq=False)
        tm.that(result.raw_output, has="read failed: service.py")


def test_every_allowed_gate_resolves_in_the_registry() -> None:
    """Every gate the Make surface accepts must be instantiable.

    mro-38p39: `format` sat in PROJECT_CHECK_GATES_ALLOWED_VALUES and
    FlextInfraRuffFormatGate declared gate_id="format" with can_fix=True, but the
    class was never listed in the registry. So `make check CHECK_GATES=format`
    named a gate that silently resolved to nothing, and the one gate that could
    repair formatting was unreachable from every verb.
    """
    registry = FlextInfraGateRegistry.default()
    unresolved = [
        gate_id
        for gate_id in c.Infra.PROJECT_CHECK_GATES_ALLOWED_VALUES
        if registry.get(gate_id) is None
    ]

    tm.that(unresolved, eq=[])


def test_fixable_gate_vocabulary_matches_the_registry() -> None:
    """The Make fixable-gate vocabulary equals the gates that declare can_fix.

    mro-38p39: `make fix APPLY=Y` routes through `check run --fix`. Without a
    gate selector that run executes EVERY gate, including pyright and mypy,
    which cannot fix anything and cost ~37s -- the verb timed out (exit 124).
    Naming the fixable gates as a literal in the template would rot the moment a
    gate flips can_fix, so the vocabulary is derived from the registry itself.

    A gate that starts declaring can_fix=True must join `make fix` with no
    template edit and no list to maintain.
    """
    registry = FlextInfraGateRegistry.default()
    declared = {
        gate_id
        for gate_id in c.Infra.PROJECT_CHECK_GATES_ALLOWED_VALUES
        if (gate_cls := registry.get(gate_id)) is not None and gate_cls.can_fix
    }

    tm.that(sorted(c.Infra.PROJECT_CHECK_GATES_FIXABLE_VALUES), eq=sorted(declared))


__all__: t.StrSequence = []
