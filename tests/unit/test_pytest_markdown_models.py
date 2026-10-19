"""Public Markdown observation models retain typed, session-local collections.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pytest

from tests import m


def test_markdown_collection_defaults_are_independent() -> None:
    """Native defaults instantiate without unresolved forward adapters."""
    first = m.Infra.PytestMarkdownCollection()
    second = m.Infra.PytestMarkdownCollection()
    origin = m.Infra.PytestMarkdownOrigin(
        source_path="example.md",
        start_line=0,
        source_sha256="a" * 64,
        max_retries=0,
    )
    item = m.Infra.PytestMarkdownItem(node_id="example.md::fence", origin=origin)
    first.eligible.append(origin)
    first.collected.append(item)
    assert first.eligible == [origin]
    assert first.collected == [item]
    assert not second.eligible
    assert not second.collected
    first_report = m.Infra.DiagResult()
    second_report = m.Infra.DiagResult()
    first_report.markdown_items.append(item)
    first_report.markdown_attempts.append(
        m.Infra.PytestMarkdownAttempt(node_id=item.node_id, attempts=1)
    )
    assert not second_report.markdown_items
    assert not second_report.markdown_attempts


def test_markdown_collection_validates_nested_origins() -> None:
    """Mutable defaults do not weaken validation of supplied observations."""
    with pytest.raises(ValueError, match="start_line"):
        m.Infra.PytestMarkdownCollection.model_validate(
            {
                "eligible": [
                    {
                        "source_path": "example.md",
                        "start_line": -1,
                        "source_sha256": "a" * 64,
                        "max_retries": 0,
                    },
                ],
            },
        )
