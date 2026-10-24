"""Fail-closed public behavior of the static enforcement catalog.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config
from flext_infra.check.gate_registry import FlextInfraGateRegistry
from flext_infra.gates.enforcement_catalog import FlextInfraEnforcementCatalogGate
from tests import c, m, t, tm, u


class TestsFlextInfraEnforcementCatalogGate:
    """The packaged catalog loads; every unresolved owner fails the load."""

    @staticmethod
    def _catalog_with_reference(tmp_path: Path, reference: t.JsonMapping) -> Path:
        """Write the packaged catalog with one reference appended to its first row.

        Returns:
            The written catalog path.

        """
        packaged = tm.ok(u.Infra.enforcement_catalog())
        payload = packaged.model_dump(mode="json")
        rows = payload["rules"]
        first = rows[0]
        rows[0] = {**first, "rules": [*first["rules"], dict(reference)]}
        path = tmp_path / "catalog.yaml"
        tm.ok(u.Cli.yaml_dump(path, {**payload, "rules": rows}))
        return path

    @staticmethod
    def test_packaged_catalog_resolves_every_owner() -> None:
        """Every row of the packaged catalog names declared, enabled owners."""
        catalog = tm.ok(u.Infra.enforcement_catalog())
        ids = [row.id for row in catalog.rules]
        tm.that(len(ids), eq=len(set(ids)))
        tm.ok(all(row.rules for row in catalog.rules))

    @staticmethod
    def test_registry_exposes_the_catalog_gate(tmp_path: Path) -> None:
        """The registered gate passes on the packaged catalog."""
        registry = FlextInfraGateRegistry.default()
        tm.ok(
            registry.get(c.Infra.ENFORCEMENT_CATALOG)
            is FlextInfraEnforcementCatalogGate
        )
        execution = FlextInfraEnforcementCatalogGate(tmp_path).check(
            tmp_path,
            m.Infra.GateContext(repository_root=tmp_path, reports_dir=tmp_path / "r"),
        )
        tm.ok(execution.result.passed)
        tm.that(execution.issues, length=0)

    @staticmethod
    @pytest.mark.parametrize(
        ("engine", "rule_id", "code"),
        [
            (c.Infra.EnforcementEngine.AST_GREP, "not-a-declared-rule", None),
            (c.Infra.EnforcementEngine.GATE, "not-a-registered-gate", None),
            (c.Infra.EnforcementEngine.CODEGEN, "not-a-template-entry", None),
            (c.Infra.EnforcementEngine.GATE, c.Infra.SMELLS, "qlty:not-a-check"),
            (c.Infra.EnforcementEngine.GATE, c.Infra.LINT, "lint:any"),
        ],
    )
    def test_unresolved_owner_fails_the_load(
        tmp_path: Path,
        engine: str,
        rule_id: str,
        code: str | None,
    ) -> None:
        """A reference the owners do not declare fails closed with its row."""
        reference: t.JsonMapping = {"engine": engine, "id": rule_id}
        if code is not None:
            reference = {**reference, "code": code}
        path = TestsFlextInfraEnforcementCatalogGate._catalog_with_reference(
            tmp_path, reference
        )
        error = tm.fail(u.Infra.enforcement_catalog(path))
        tm.that(error, has=rule_id)

    @staticmethod
    def test_ruling_disabled_ruff_rule_fails_the_load(tmp_path: Path) -> None:
        """A Ruff rule the tooling SSOT disables is not an enabled owner."""
        disabled = config.Infra.tooling.tools.ruff.lint.ruling_disabled_rules[0]
        path = TestsFlextInfraEnforcementCatalogGate._catalog_with_reference(
            tmp_path, {"engine": c.Infra.EnforcementEngine.RUFF, "id": disabled}
        )
        error = tm.fail(u.Infra.enforcement_catalog(path))
        tm.that(error, has=disabled)
