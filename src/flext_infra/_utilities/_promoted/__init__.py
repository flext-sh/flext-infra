# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities. Promoted package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import defer_lazy_bases, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._utilities._promoted.commands import (
        FlextInfraUtilitiesPromotedCommands,
    )
    from flext_infra._utilities._promoted.execution import (
        FlextInfraUtilitiesPromotedExecution,
    )
    from flext_infra._utilities._promoted.header import (
        FlextInfraUtilitiesPromotedHeader,
    )
    from flext_infra._utilities._promoted.invocation import (
        FlextInfraUtilitiesPromotedInvocation,
    )
    from flext_infra._utilities._promoted.rendering import (
        FlextInfraUtilitiesPromotedRendering,
    )
    from flext_infra._utilities._promoted.workspace import (
        FlextInfraUtilitiesPromotedWorkspace,
    )


__all__: tuple[str, ...] = (
    "FlextInfraUtilitiesPromotedCommands",
    "FlextInfraUtilitiesPromotedExecution",
    "FlextInfraUtilitiesPromotedHeader",
    "FlextInfraUtilitiesPromotedInvocation",
    "FlextInfraUtilitiesPromotedRendering",
    "FlextInfraUtilitiesPromotedWorkspace",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "FlextInfraUtilitiesPromotedCommands": ".commands",
        "FlextInfraUtilitiesPromotedExecution": ".execution",
        "FlextInfraUtilitiesPromotedHeader": ".header",
        "FlextInfraUtilitiesPromotedInvocation": ".invocation",
        "FlextInfraUtilitiesPromotedRendering": ".rendering",
        "FlextInfraUtilitiesPromotedWorkspace": ".workspace",
    },
    public_exports=__all__,
    deferred_members={
        "FlextInfraUtilitiesPromotedCommands": (
            "promoted_command_headers",
            "_promoted_command_header",
            "promoted_command_stem",
            "promoted_load_command",
            "_promoted_text",
            "_promoted_texts",
        ),
        "FlextInfraUtilitiesPromotedExecution": ("promoted_run",),
        "FlextInfraUtilitiesPromotedHeader": (
            "promoted_render_header",
            "_promoted_header_body",
            "_promoted_header_name",
            "_promoted_header_value",
            "_promoted_header_string",
            "_promoted_header_margin",
            "_promoted_header_pieces",
            "_promoted_header_fits",
            "_promoted_header_escaped",
            "_promoted_header_key",
        ),
        "FlextInfraUtilitiesPromotedInvocation": (
            "promoted_validate_invocation",
            "promoted_validate_command_contract",
            "promoted_validate_all_choices",
            "promoted_param_value",
        ),
        "FlextInfraUtilitiesPromotedRendering": (
            "promoted_renders_verb_help",
            "promoted_render_help",
            "_promoted_verb_help",
            "_promoted_alias_suffix",
            "_promoted_param_details",
            "_promoted_section",
            "_promoted_example",
        ),
        "FlextInfraUtilitiesPromotedWorkspace": (
            "promoted_fail",
            "promoted_find_owner_root",
            "promoted_workspace_spec",
            "promoted_discovered_workspace_spec",
            "promoted_ensure_local_python",
            "promoted_main",
        ),
    },
)

defer_lazy_bases(
    __name__,
    {
        "FlextInfraUtilitiesPromotedCommands": (
            (".", "FlextInfraUtilitiesPromotedWorkspace"),
            ("flext_infra._utilities", "FlextInfraUtilitiesScriptMetadata"),
        ),
        "FlextInfraUtilitiesPromotedExecution": (
            (".", "FlextInfraUtilitiesPromotedInvocation"),
        ),
        "FlextInfraUtilitiesPromotedInvocation": (
            (".", "FlextInfraUtilitiesPromotedWorkspace"),
        ),
    },
)
