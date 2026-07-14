"""Tests for the flext-infra pytest enforcement plugin.

The plugin is auto-registered via the ``flext_infra_enforcement`` pytest11
entry-point. These tests assert the entry-point exists and that loading the
module registers the expected detector contribution with the central
flext-tests dispatcher.
"""

from __future__ import annotations

from importlib.metadata import entry_points

from flext_tests import tm
from flext_tests.enforcement import get


class TestsFlextInfraEnforcementPlugin:
    """Entry-point and registration contract for the flext-infra plugin."""

    def test_pytest11_entry_point_registers_detector_contribution(self) -> None:
        """The installed plugin exposes its public registry contribution."""
        eps = entry_points(group="pytest11")
        names = {ep.name for ep in eps}
        tm.that(names, has="flext_infra_enforcement")
        contribution = get("flext_infra_detector")
        tm.that(contribution, none=False)
        if contribution is None:
            msg = "flext-infra detector contribution was not registered"
            raise AssertionError(msg)
        tm.that(contribution.source_kind, eq="flext_infra_detector")
        tm.that(contribution.builder, none=False)
        tm.that(contribution.warning_categories, eq=())
