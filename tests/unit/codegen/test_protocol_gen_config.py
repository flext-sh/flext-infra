"""Config load + schema validation for protocol_gen rules-as-data (LAW-1).

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import u
from flext_tests import tm

_ROOT = Path(__file__).resolve().parents[3]


class TestProtocolGenConfig:
    """Validate the protocol_gen rules-as-data config against its JSON Schema."""

    def test_config_loads_and_validates_against_schema(self) -> None:
        """Config loads and passes JSON-Schema validation with expected values."""
        cfg = _ROOT / "config" / "protocol_gen.yaml"
        schema = _ROOT / "config" / "schemas" / "protocol_gen.schema.json"
        loaded = u.Cli.config_load(cfg, schema_path=schema, expand_env=False)
        tm.ok(loaded)
        data = loaded.value.data
        tm.that(data["field_only_max_methods"], eq=0)
        tm.that(data["banned_annotations"], has="Any")
        tm.that(data["banned_annotations"], has="object")
        tm.that(data["warning_severities"]["out_of_contract"], eq="HIGH")
