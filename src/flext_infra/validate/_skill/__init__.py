# AUTO-GENERATED FILE — Regenerate with: make gen
"""skill package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.validate._skill.rule_runner import (
        FlextInfraValidateSkillRuleRunner,
    )


__all__: tuple[str, ...] = ("FlextInfraValidateSkillRuleRunner",)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraValidateSkillRuleRunner": ".rule_runner",
    }),
    public_exports=__all__,
)
