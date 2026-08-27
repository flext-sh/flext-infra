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
    # Why (flext-ga9q): custom.mk policy is a BLACKLIST, not a whitelist. A member
    # project may define ANY custom verb/WHAT through _custom_<verb>_<what>
    # handlers and (pre|post)-<verb>[-<what>] lifecycle hooks EXCEPT the
    # reserved surface, which stays a flext-infra monopoly.
    #
    # Why (flext-x0rau.3): this list adds ONLY the project-surface verbs that are
    # reserved but not declared in config/codegen.yaml. R12 reorganized the verb
    # surface into verb+WHAT pairs, and 14 of the 22 names this list carried no
    # longer resolve to any recipe -- `make --dry-run <verb>` reported NO RULE
    # for boot, pr, scan, val, fix-enforcement and all ten daemon-* targets.
    # Reserving a name the generator never ships is not harmless: it forbids a
    # member from defining a verb that flext-infra does not provide either.
    # Their behaviour lives on in the living surface (val/scan -> `check`,
    # boot -> `setup WHAT=environment`, fix-enforcement -> `fix WHAT=apply`),
    # so the dead names are removed with their recipes, never reserved-but-absent.
    CUSTOM_MK_RESERVED_PROJECT_VERBS: Final[t.StrSequence] = (
        "build",
        "check",
        "clean",
        "fmt",
        "help",
        "run",
        "test",
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
    # flext-x0rau.3: base_daemons.mk.j2, base_pr.mk.j2 and base_mypy_limit.mk.j2
    # were dropped with the daemon-*/pr verbs they served. No generated Makefile
    # includes base.mk, so those recipes were unreachable, and the Mypy cap they
    # defined (MYPY_BOUNDED / VALIDATE_MYPY_LIMITS / REPORT_MYPY_FAILURE) was
    # left defined-but-never-invoked. The live cap is enforced in Python by
    # FlextInfraUtilitiesResourceLimits at the gate boundary.
    TEMPLATE_ORDER: Final[t.StrSequence] = (
        "base_header.mk.j2",
        "base_detection.mk.j2",
        "base_venv.mk.j2",
        "base_preflight.mk.j2",
        "base_clean.mk.j2",
    )


__all__: list[str] = ["FlextInfraConstantsBasemk"]
