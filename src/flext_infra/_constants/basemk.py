"""Centralized constants for the basemk subpackage."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraConstantsBasemk:
    """Basemk infrastructure constants."""

    MAKEFILE_BOOTSTRAP_TEMPLATE: Final[str] = "makefile_bootstrap.mk.j2"
    # Git refnames legitimately allow characters the shell parses ($ ; ` space),
    # so the generated bootstrap must validate SETUP_BRANCH against a strict
    # allowlist before any recipe interpolates it into a command.
    SETUP_BRANCH_GUARD: Final[str] = "_setup_require_safe_branch"
    SETUP_BRANCH_PATTERN: Final[str] = "*[!a-zA-Z0-9._/-]*"
    TEMPLATE_ORDER: Final[t.StrSequence] = (
        "base_header.mk.j2",
        "base_detection.mk.j2",
        "base_venv.mk.j2",
        "project/base/base_mypy_limit.mk.j2",
        "base_preflight.mk.j2",
        "base_daemons.mk.j2",
        "base_pr.mk.j2",
        "base_clean.mk.j2",
    )


__all__: list[str] = ["FlextInfraConstantsBasemk"]
