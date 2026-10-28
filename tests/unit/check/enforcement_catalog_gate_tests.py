"""Public behavior of the enforcement catalog derived from its owners.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path

from flext_infra import config
from flext_infra.check.gate_registry import FlextInfraGateRegistry
from flext_infra.gates.enforcement_catalog import FlextInfraEnforcementCatalogGate
from tests import c, m, t, tm, u


class TestsFlextInfraEnforcementCatalogGate:
    """Owner claims derive the catalog; duplicate and orphan claims fail it."""

    @staticmethod
    def _provider(tmp_path: Path, rules: Sequence[t.JsonMapping]) -> Path:
        """Write one ast-grep provider whose rules carry the given documents.

        Returns:
            The provider config path.

        """
        rule_dir = tmp_path / "rules"
        rule_dir.mkdir()
        for document in rules:
            tm.ok(u.Cli.yaml_dump(rule_dir / f"{document['id']}.yml", document))
        provider = tmp_path / c.Infra.CODEMOD_CONFIG_FILENAME
        tm.ok(u.Cli.yaml_dump(provider, {c.Infra.CODEMOD_RULE_DIRS_KEY: ["rules"]}))
        return provider

    @staticmethod
    def _rule(rule_id: str, enforce: Sequence[str], severity: str) -> t.JsonMapping:
        """Build one detection rule document claiming the given law ids.

        Returns:
            The rule document.

        """
        return {
            "id": rule_id,
            "language": "python",
            "severity": severity,
            "rule": {"pattern": "breakpoint()"},
            "message": f"{rule_id} fixture",
            c.Infra.CODEMOD_RULE_METADATA_KEY: {
                c.Infra.CODEMOD_RULE_ENFORCE_KEY: list(enforce),
            },
        }

    @staticmethod
    def test_packaged_owners_derive_a_valid_catalog() -> None:
        """Every packaged claim is unique per owner and has an active owner."""
        catalog = tm.ok(u.Infra.enforcement_catalog())
        keys = [
            (claim.id, claim.engine, claim.owner, claim.code)
            for claim in catalog.claims
        ]
        tm.that(len(keys), eq=len(set(keys)))
        active = {claim.id for claim in catalog.claims if claim.active}
        tm.that({claim.id for claim in catalog.claims}, eq=active)

    @staticmethod
    def test_registry_exposes_the_catalog_gate(tmp_path: Path) -> None:
        """The registered gate passes on the packaged owners."""
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
    def test_active_rule_claim_enters_the_catalog(tmp_path: Path) -> None:
        """A claim in an active rule's metadata is part of the derived catalog."""
        cls = TestsFlextInfraEnforcementCatalogGate
        provider = cls._provider(
            tmp_path, [cls._rule("fixture-active", ["ENFORCE-900"], "error")]
        )
        catalog = tm.ok(u.Infra.enforcement_catalog(provider))
        claimed = {
            (claim.id, claim.owner, claim.active)
            for claim in catalog.claims
            if claim.engine == c.Infra.EnforcementEngine.AST_GREP
        }
        tm.that(claimed, eq={("ENFORCE-900", "fixture-active", True)})

    @staticmethod
    def test_repeated_claim_fails_as_duplicate(tmp_path: Path) -> None:
        """An owner that claims the same law twice fails the derivation."""
        cls = TestsFlextInfraEnforcementCatalogGate
        provider = cls._provider(
            tmp_path,
            [cls._rule("fixture-twice", ["ENFORCE-901", "ENFORCE-901"], "error")],
        )
        error = tm.fail(u.Infra.enforcement_catalog(provider))
        tm.that(error, has="ENFORCE-901")
        tm.that(error, has="claims it twice")

    @staticmethod
    def test_claim_of_disabled_owner_fails_as_orphan(tmp_path: Path) -> None:
        """A law claimed only by a switched-off rule has no active owner."""
        cls = TestsFlextInfraEnforcementCatalogGate
        provider = cls._provider(
            tmp_path,
            [
                cls._rule("fixture-active", ["ENFORCE-900"], "error"),
                cls._rule(
                    "fixture-off",
                    ["ENFORCE-902"],
                    c.Infra.CODEMOD_RULE_SEVERITY_OFF,
                ),
            ],
        )
        error = tm.fail(u.Infra.enforcement_catalog(provider))
        tm.that(error, has="ENFORCE-902")
        tm.that(error, has="orphan")

    @staticmethod
    def test_accessor_prefix_util_projects_the_tooling_policy(
        tmp_path: Path,
    ) -> None:
        """The generated util matches exactly the declared accessor prefixes."""
        produced = u.Infra.accessor_prefix_constraints(tmp_path)
        tm.that(tuple(produced), eq=(c.Infra.ACCESSOR_PREFIX_UTIL_ID,))
        pattern = re.compile(
            str(produced[c.Infra.ACCESSOR_PREFIX_UTIL_ID]["regex"]),
        )
        prefixes = config.Infra.tooling.accessor_policy.forbidden_prefixes
        tm.ok(all(pattern.match(f"{prefix}value") for prefix in prefixes))
        tm.fail(any(pattern.match(f"x{prefix}value") for prefix in prefixes))
