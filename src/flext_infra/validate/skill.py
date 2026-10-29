"""Extracted facade class for skill.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra.validate._skill import FlextInfraValidateSkillRuleRunner


class FlextInfraValidateSkill(
    FlextInfraValidateSkillRuleRunner,
):
    """Facade for skill."""


__all__: list[str] = ["FlextInfraValidateSkill"]
