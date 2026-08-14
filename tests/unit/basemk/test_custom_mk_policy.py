"""Unit tests for the custom.mk reserved-target blacklist policy.

The custom.mk surface is a BLACKLIST (mro-ga9q): members may define ANY custom
verb/WHAT through ``_custom_<verb>_<what>`` handlers and ``(pre|post)-`` hooks
EXCEPT the reserved verbs/WHATs that stay a flext-infra monopoly. These tests
pin the typed owner of that rule; the generated base.mk enforces the same
blacklist at make parse time (see test_make_contract.py).
"""

from __future__ import annotations

from flext_infra.basemk.custom_policy import FlextInfraCustomMkPolicy
from flext_tests import tm


class TestsFlextInfraCustomMkPolicy:
    """Behavior contract for test_custom_mk_policy."""

    def test_reserved_verb_redefinition_fails_loud(self) -> None:
        """Redefining a reserved public verb target is rejected."""
        result = FlextInfraCustomMkPolicy.validate_content("check:\n\t@echo evil\n")

        tm.that(result.failure, eq=True)
        tm.that(result.error or "", has=["custom.mk", "check", "monopoly"])

    def test_reserved_builtin_what_handler_fails_loud(self) -> None:
        """A _custom handler naming a builtin (verb, WHAT) pair is rejected."""
        result = FlextInfraCustomMkPolicy.validate_content(
            "_custom_check_all:\n\t@true\n"
        )

        tm.that(result.failure, eq=True)
        tm.that(result.error or "", has="_custom_check_all")

    def test_arbitrary_custom_verb_and_what_pass(self) -> None:
        """Any non-reserved custom verb/WHAT handler is permitted."""
        content = (
            "_custom_ship_fast:\n\t@true\n"
            "_custom_mod_circuit:\n\t@true\n"
            "_custom_check_mygate:\n\t@true\n"
        )

        tm.that(tm.ok(FlextInfraCustomMkPolicy.validate_content(content)), eq=True)

    def test_lifecycle_hooks_and_variables_pass(self) -> None:
        """Lifecycle hooks, .PHONY, assignments, and comments are permitted."""
        content = (
            ".PHONY: pre-check post-test-all\n"
            "pre-check:\n\t@true\n"
            "post-test-all:\n\t@true\n"
            "CUSTOM_TOOL := ruff\n"
            "# comment only\n"
        )

        tm.that(tm.ok(FlextInfraCustomMkPolicy.validate_content(content)), eq=True)

    def test_reserved_verbs_cover_workspace_and_project_surfaces(self) -> None:
        """Reserved verbs derive from the codegen SSOT plus base.mk verbs."""
        reserved = FlextInfraCustomMkPolicy.reserved_verbs()

        tm.that({"check", "gen", "work"} <= reserved, eq=True)
        tm.that({"pr", "clean"} <= reserved, eq=True)

    def test_reserved_targets_cover_builtin_what_pairs(self) -> None:
        """Reserved targets include every builtin _custom_<verb>_<what> pair."""
        targets = FlextInfraCustomMkPolicy.reserved_targets()

        tm.that("_custom_check_all" in targets, eq=True)
        tm.that("_custom_run_default" in targets, eq=True)
        tm.that("_custom_ship_fast" in targets, eq=False)
