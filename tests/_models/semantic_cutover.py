"""Test-only model for the semantic cutover J2 scenarios.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import m


class TestsFlextInfraModelsSemanticCutover:
    """Semantic cutover scenario context rendered through flext-cli J2."""

    class SemanticCutoverScenario(m.Value):
        """One reusable cutover scenario; unused fields stay empty."""

        template: str = m.Field(description="J2 template name")
        module: str = m.Field(default="", description="Imported module")
        names: str = m.Field(default="", description="Imported names")
        alias: str = m.Field(default="", description="Optional import alias")
        body: str = m.Field(default="", description="Module body")
        header: str = m.Field(default="", description="Module header")
        assertions: str = m.Field(
            default="",
            description="Assert expressions, one per line",
        )
        message: str = m.Field(default="", description="Optional assert message")


__all__: list[str] = ["TestsFlextInfraModelsSemanticCutover"]
