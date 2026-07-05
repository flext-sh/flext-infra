"""Pytest plugin for flext-infra enforcement detectors.

This module is loaded automatically via the ``flext_infra_enforcement`` pytest11
entry-point. It registers the ``flext_infra_detector`` contribution with the
central ``flext_tests`` enforcement dispatcher so that namespace-enforcer
violations are surfaced as synthetic pytest items.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests.enforcement import (
    EnforcementCollector,
    EnforcementContribution,
    EnforcementItem,
    register,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    import pytest
    from flext_tests import m, p
    from flext_tests.enforcement import EnforcementBuildContext


def _iter_infra_violations(
    report: p.AttributeProbe,
    field: str,
    *,
    match_missing: bool,
) -> Iterable[tuple[str, p.AttributeProbe]]:
    """Yield ``(project_name, violation)`` from a workspace report."""
    projects = getattr(report, "projects", ())
    for project in projects:
        project_name = getattr(project, "project", "") or getattr(
            project,
            "project_name",
            "",
        )
        entries = getattr(project, field, ())
        if match_missing:
            entries = tuple(
                entry for entry in entries if not getattr(entry, "exists", True)
            )
        for entry in entries:
            yield str(project_name), entry


def _build_infra_detector_items(
    session: pytest.Session,
    _cfg: m.Tests.EnforcementDispatcherConfig,
    rule: m.EnforcementRuleSpec,
    context: EnforcementBuildContext,
) -> list[pytest.Item]:
    """Build enforcement items from a flext-infra namespace detector report."""
    infra_report = context.infra_report
    if infra_report is None:
        return []

    source = rule.source
    field = getattr(source, "violation_field", "")
    match_missing = bool(getattr(source, "match_missing", False))
    grouped: dict[str, list[p.AttributeProbe]] = {}
    for project, entry in _iter_infra_violations(
        infra_report,
        field,
        match_missing=match_missing,
    ):
        grouped.setdefault(project, []).append(entry)

    collector = EnforcementCollector(
        name="flext-enforcement",
        parent=session,
    )
    items: list[pytest.Item] = []
    for project, violations in grouped.items():
        if not violations:
            continue
        items.append(
            EnforcementItem(
                name=f"{rule.id}[{project}]",
                parent=collector,
                rule=rule,
                project=project,
                violations=violations,
            ),
        )
    return items


def _register() -> None:
    """Register flext-infra enforcement contribution when flext-tests is present."""
    register(
        "flext_infra_detector",
        EnforcementContribution(
            source_kind="flext_infra_detector",
            builder=_build_infra_detector_items,
        ),
    )


_register()


__all__: list[str] = []
