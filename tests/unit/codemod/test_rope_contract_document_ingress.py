"""Public Pydantic document ingress preserves strict Rope contract ownership.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests import c, m, t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRopeContractDocumentIngress:
    """Separate source values from validated operational provenance."""

    @staticmethod
    def test_document_origin_is_separate_from_json_values(tmp_path: Path) -> None:
        """Typed catalog ownership never becomes a node in the parsed document."""
        document: t.JsonMapping = {
            "rules": [
                {
                    "id": "source-origin",
                    "pattern": "${value}",
                    "goal": "${value}",
                    "arguments": {},
                    "operation": c.Infra.RopeContractOperation.RESTRUCTURE.value,
                    "phase": (
                        c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION.value
                    ),
                    "scope_kinds": [c.Infra.RopeScopeKind.CLASS.value],
                    "model_bases": [c.Infra.PYDANTIC_MODEL_IDENTITY],
                }
            ]
        }
        parsed = tm.ok(u.Cli.yaml_parse(u.Cli.yaml_dump_str(document)))
        origin = m.Infra.RopeContractOrigin(owner_root=tmp_path)

        decoded = u.Cli.config_decode(
            parsed, m.Infra.RopeContractRules, metadata=origin
        )

        rule = decoded.rules[0]
        tm.ok(rule.owner_root is origin.owner_root)
        tm.ok(rule.operation is c.Infra.RopeContractOperation.RESTRUCTURE)
        tm.ok(rule.scope_kinds[0] is c.Infra.RopeScopeKind.CLASS)
        rows = u.json_mapping_sequence_adapter().validate_python(parsed["rules"])
        tm.fail("owner_root" in rows[0])
        tm.that(type(rows[0]["phase"]), eq=str)

    @staticmethod
    def test_document_requires_its_elected_origin() -> None:
        """A document cannot elect its own root or omit operational provenance."""
        document: t.JsonMapping = {
            "rules": [
                {
                    "id": "source-origin",
                    "pattern": "${value}",
                    "goal": "${value}",
                    "arguments": {},
                }
            ]
        }

        with pytest.raises(TypeError, match="validated catalog origin"):
            u.Cli.config_decode(document, m.Infra.RopeContractRules)

        declared_root: t.JsonMapping = {
            "rules": [
                {
                    "id": "source-origin",
                    "pattern": "${value}",
                    "goal": "${value}",
                    "arguments": {},
                    "owner_root": "not-the-elected-root",
                }
            ]
        }
        with pytest.raises(m.ValidationError, match="operational owner root"):
            u.Cli.config_decode(
                declared_root,
                m.Infra.RopeContractRules,
                metadata=m.Infra.RopeContractOrigin(owner_root=None),
            )

    @staticmethod
    def test_ordinary_json_keeps_its_declared_path_contract(tmp_path: Path) -> None:
        """The document context does not alter ordinary JSON/Python model APIs."""
        document: dict[str, t.JsonValue] = {
            "id": "ordinary-json",
            "pattern": "${value}",
            "goal": "${value}",
            "arguments": {},
            "owner_root": str(tmp_path),
        }
        encoded = u.type_adapter(t.JsonValue).dump_json(document)

        rule = m.Infra.RopeContractRule.model_validate_json(encoded)

        tm.that(rule.owner_root, eq=tmp_path)
        typed = rule.model_dump()
        typed["owner_root"] = tmp_path
        restored = m.Infra.RopeContractRule.model_validate(typed)
        tm.that(restored.owner_root, eq=tmp_path)
