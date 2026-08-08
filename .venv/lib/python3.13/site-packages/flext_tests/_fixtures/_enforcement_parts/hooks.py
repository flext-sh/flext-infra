"""Pytest hooks for enforcement dispatch."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests._fixtures._enforcement_parts.build import build_items
from flext_tests._fixtures._enforcement_parts.config import (
    SessionConfig,
    active_rules,
    resolve_config,
)

if TYPE_CHECKING:
    import pytest

    from flext_tests import p


def pytest_collection_modifyitems(
    session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Append dispatcher items to the collection when active."""
    cfg = resolve_config(config)
    if not cfg.active:
        return
    if hasattr(config, "workerinput"):
        return
    generated = build_items(session, cfg, collected_items=items)
    if not generated:
        return
    items.extend(generated)


def pytest_warning_recorded(
    warning_message: p.AttributeProbe,
    when: str,
    nodeid: str,
    location: tuple[str, int, str] | None,
) -> None:
    """Track runtime enforcement warnings."""
    _ = when, nodeid, location
    if SessionConfig.value is None:
        return
    cfg = resolve_config(SessionConfig.value)
    if not cfg.active:
        return
    category = getattr(warning_message, "category", None)
    if category is None:
        return
    dotted = f"{category.__module__}.{category.__qualname__}"
    counter = cfg.warning_counter
    counter[dotted] = counter.get(dotted, 0) + 1


def pytest_sessionstart(session: pytest.Session) -> None:
    """Expose the session config for warning-capture plumbing."""
    SessionConfig.value = session.config


def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter, exitstatus: int, config: pytest.Config
) -> None:
    """Print the per-kind breakdown at the end of the session."""
    _ = exitstatus
    cfg = resolve_config(config)
    if not cfg.active:
        return
    active = active_rules(cfg)
    kinds: dict[str, int] = {}
    for rule in active:
        kinds[rule.source.kind] = kinds.get(rule.source.kind, 0) + 1
    terminalreporter.write_sep("-", "flext-enforce", yellow=True)
    terminalreporter.write_line(
        f"catalog active: {len(active)} rules across {len(kinds)} source kinds"
    )
    for kind in sorted(kinds):
        terminalreporter.write_line(f"  {kind}: {kinds[kind]}")
    terminalreporter.write_line(
        f"runtime warnings captured: {sum(cfg.warning_counter.values())}"
    )


__all__: list[str] = [
    "pytest_collection_modifyitems",
    "pytest_sessionstart",
    "pytest_terminal_summary",
    "pytest_warning_recorded",
]
