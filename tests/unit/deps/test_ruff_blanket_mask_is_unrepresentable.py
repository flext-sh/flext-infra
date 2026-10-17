"""Ruff exemption catalogs are rejected at the public typed policy boundary.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pytest

from flext_infra import config, m
from tests import tm, u


class TestsFlextInfraRuffBlanketMaskIsUnrepresentable:
    """Named exemptions and blanket masks are equally unrepresentable."""

    @staticmethod
    @pytest.mark.parametrize(
        "field",
        ["authorized-exceptions", "ignore", "per-file-ignores"],
    )
    def test_lint_policy_rejects_suppression_catalogs(field: str) -> None:
        """No authority record or native ignore table may bypass a rule."""
        lint = config.Infra.tooling.tools.ruff.lint
        payload = lint.model_dump(
            mode="json",
            by_alias=True,
            exclude_computed_fields=True,
        )
        payload[field] = []
        with pytest.raises(m.ValidationError, match=field):
            m.Infra.RuffLintConfig.model_validate_json(tm.ok(u.Cli.json_dumps(payload)))

    @staticmethod
    def test_ruff_policy_rejects_nonblocking_catalog() -> None:
        """The top-level policy cannot reintroduce informative-only rules."""
        ruff = config.Infra.tooling.tools.ruff
        payload = ruff.model_dump(
            mode="json",
            by_alias=True,
            exclude_computed_fields=True,
        )
        payload["informative-rules"] = []
        with pytest.raises(m.ValidationError, match="informative-rules"):
            m.Infra.RuffConfig.model_validate_json(tm.ok(u.Cli.json_dumps(payload)))
