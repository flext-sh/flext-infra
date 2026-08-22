"""Centralized constants for the basemk subpackage."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraConstantsBasemk:
    """Basemk infrastructure constants."""

    MAKEFILE_BOOTSTRAP_TEMPLATE: Final[str] = "makefile_bootstrap.mk.j2"
    CUSTOM_HANDLER_PREFIX: Final[str] = "_custom_"
    "Prefix naming a custom.mk handler dispatched for a project-specific WHAT."
    CUSTOM_LIFECYCLE_HOOK_PREFIXES: Final[t.StrSequence] = ("pre-", "post-")
    "Prefixes naming custom.mk lifecycle hooks running before/after a verb."
    # Why (mro-ga9q): custom.mk policy is a BLACKLIST, not a whitelist. A member
    # project may define ANY custom verb/WHAT through _custom_<verb>_<what>
    # handlers and (pre|post)-<verb>[-<what>] lifecycle hooks EXCEPT the
    # reserved surface, which stays a flext-infra monopoly. Workspace verb
    # names and builtin WHATs come from config.Infra.codegen.make (the
    # codegen.yaml SSOT); this list adds the project-surface verbs owned only
    # by the generated base.mk templates.
    CUSTOM_MK_RESERVED_PROJECT_VERBS: Final[t.StrSequence] = (
        "boot",
        "build",
        "check",
        "clean",
        "daemon-restart",
        "daemon-start",
        "daemon-start-mypy",
        "daemon-start-pyright",
        "daemon-status",
        "daemon-status-mypy",
        "daemon-status-pyright",
        "daemon-stop",
        "daemon-stop-mypy",
        "daemon-stop-pyright",
        "fix-enforcement",
        "fmt",
        "help",
        "pr",
        "run",
        "scan",
        "test",
        "val",
    )
    CUSTOM_MK_BLACKLIST_ERROR: Final[str] = (
        "reserved verbs/WHATs are a flext-infra monopoly; use "
        "_custom_<verb>_<what> with a non-reserved WHAT or "
        "(pre|post)-<verb>[-<what>] hooks"
    )
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
