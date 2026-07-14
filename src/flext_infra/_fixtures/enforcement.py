"""Pytest plugin for flext-infra enforcement detectors.

This module is loaded automatically via the ``flext_infra_enforcement`` pytest11
entry-point. It registers the detector contribution with the central
``flext_tests`` enforcement dispatcher so that infra detector violations are
tracked during test sessions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import p as tests_p
from flext_tests.enforcement import (
    EnforcementCollector,
    EnforcementContribution,
    EnforcementItem,
    register as register_enforcement_contribution,
)

from flext_infra import m, p

if TYPE_CHECKING:
    from collections.abc import Iterable

    import pytest
    from flext_tests import m as tests_m


class FlextInfraEnforcementPytestPlugin(tests_p.Tests.EnforcementBuilder):
    """Class-owned pytest contribution for flext-infra detector rules."""

    _SOURCE_KIND: str = m.EnforcementSourceKind.FLEXT_INFRA_DETECTOR.value

    @classmethod
    def source_kind(cls) -> str:
        """Return the catalog source kind owned by this plugin."""
        return cls._SOURCE_KIND

    @classmethod
    def contribution(cls) -> EnforcementContribution:
        """Return the registry contribution for the flext-tests dispatcher."""
        return EnforcementContribution(source_kind=cls.source_kind(), builder=cls())

    @classmethod
    def register(cls) -> None:
        """Register this plugin in the flext-tests enforcement registry."""
        register_enforcement_contribution(cls.source_kind(), cls.contribution())

    def __call__(
        self,
        session: pytest.Session,
        cfg: tests_m.Tests.EnforcementDispatcherConfig,
        rule: tests_m.EnforcementRuleSpec,
        context: tests_p.Tests.EnforcementBuildContext,
    ) -> list[pytest.Item]:
        """Build enforcement items from a flext-infra namespace detector report."""
        _ = cfg
        infra_report = context.infra_report
        if infra_report is None:
            return []

        grouped = self.group_violations(rule, infra_report)
        collector = EnforcementCollector.from_parent(
            parent=session, name="flext-enforcement"
        )
        return [
            EnforcementItem.from_parent(
                name=f"{rule.id}[{project}]",
                parent=collector,
                rule=rule,
                project=project,
                violations=tuple(violations),
            )
            for project, violations in grouped.items()
            if violations
        ]

    @classmethod
    def group_violations(
        cls, rule: m.EnforcementRuleSpec, report: p.AttributeProbe
    ) -> dict[str, list[p.AttributeProbe]]:
        """Group detector violations by owning project."""
        source = rule.source
        field = getattr(source, "violation_field", "")
        match_missing = bool(getattr(source, "match_missing", False))
        grouped: dict[str, list[p.AttributeProbe]] = {}
        for project, entry in cls.iter_violations(
            report, field, match_missing=match_missing
        ):
            grouped.setdefault(project, []).append(entry)
        return grouped

    @staticmethod
    def iter_violations(
        report: p.AttributeProbe, field: str, *, match_missing: bool
    ) -> Iterable[tuple[str, p.AttributeProbe]]:
        """Yield ``(project_name, violation)`` from a workspace report."""
        projects = getattr(report, "projects", ())
        for project in projects:
            project_name = getattr(project, "project", "") or getattr(
                project, "project_name", ""
            )
            entries = getattr(project, field, ())
            if match_missing:
                entries = tuple(
                    entry for entry in entries if not getattr(entry, "exists", True)
                )
            for entry in entries:
                yield str(project_name), entry


FlextInfraEnforcementPytestPlugin.register()


__all__: list[str] = ["FlextInfraEnforcementPytestPlugin"]
