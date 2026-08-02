"""Pytest plugin for deterministic external CI shards."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import pytest

from flext_infra import m, u

_MINIMUM_SHARD_COUNT = 2
type _Outcome = Literal["passed", "failed", "skipped", "xfailed", "xpassed", "error"]


class _ShardState:
    """Mutable pytest-session evidence accumulated by hook callbacks."""

    def __init__(self, config: pytest.Config) -> None:
        self.assignment: Literal["sha256-mod-v1"] = config.getoption(
            "--flext-shard-assignment"
        )
        self.shard_count: int = config.getoption("--flext-shard-count")
        self.shard_index: int = config.getoption("--flext-shard-index")
        self.max_workers: int = config.getoption("--flext-shard-max-workers")
        self.manifest: Path = config.getoption("--flext-shard-manifest")
        self.is_worker = hasattr(config, "workerinput")
        self.full_collection: tuple[str, ...] = ()
        self.selected_nodeids: tuple[str, ...] = ()
        self.completed_nodeids: list[str] = []
        self.outcomes: dict[str, _Outcome] = {}
        self.worker_ids: set[str] = set()


_states: list[_ShardState] = []


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register the generated CI shard contract."""
    group = parser.getgroup("flext-shard")
    group.addoption("--flext-shard-count", type=int)
    group.addoption("--flext-shard-index", type=int)
    group.addoption("--flext-shard-max-workers", type=int)
    group.addoption("--flext-shard-assignment", choices=("sha256-mod-v1",))
    group.addoption("--flext-shard-manifest", type=Path)


def pytest_configure(config: pytest.Config) -> None:
    """Validate all-or-none shard options and initialize controller state."""
    values = (
        config.getoption("--flext-shard-count"),
        config.getoption("--flext-shard-index"),
        config.getoption("--flext-shard-max-workers"),
        config.getoption("--flext-shard-assignment"),
        config.getoption("--flext-shard-manifest"),
    )
    if not any(value is not None for value in values):
        return
    if any(value is None for value in values):
        msg = "all --flext-shard-* options are required together"
        raise pytest.UsageError(msg)
    shard_count, shard_index, max_workers, _, manifest = values
    if not isinstance(shard_count, int) or shard_count < _MINIMUM_SHARD_COUNT:
        msg = "--flext-shard-count must be at least 2"
        raise pytest.UsageError(msg)
    if not isinstance(shard_index, int) or not 0 <= shard_index < shard_count:
        msg = "--flext-shard-index must be within the configured shard count"
        raise pytest.UsageError(msg)
    if not isinstance(max_workers, int) or max_workers < 1:
        msg = "--flext-shard-max-workers must be positive"
        raise pytest.UsageError(msg)
    if not isinstance(manifest, Path):
        msg = "--flext-shard-manifest must be a path"
        raise pytest.UsageError(msg)
    _states.clear()
    _states.append(_ShardState(config))


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Select exactly one stable shard from the complete sorted collection."""
    state = _states[0] if _states else None
    if not isinstance(state, _ShardState) or not state.is_worker:
        return
    full_collection = tuple(sorted(item.nodeid for item in items))
    selected_ids = frozenset(
        nodeid
        for nodeid in full_collection
        if int(u.Cli.sha256_content(nodeid), 16) % state.shard_count
        == state.shard_index
    )
    selected = [item for item in items if item.nodeid in selected_ids]
    deselected = [item for item in items if item.nodeid not in selected_ids]
    state.full_collection = full_collection
    state.selected_nodeids = tuple(item.nodeid for item in selected)
    items[:] = selected
    if deselected:
        config.hook.pytest_deselected(items=deselected)


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    """Record each completed nodeid and its observable call outcome."""
    state = _states[0] if _states else None
    if not isinstance(state, _ShardState) or not state.is_worker:
        return
    if report.when == "call":
        state.outcomes[report.nodeid] = report.outcome
    if report.when == "teardown":
        state.completed_nodeids.append(report.nodeid)


def pytest_testnodedown(node: pytest.TestReport, error: BaseException | None) -> None:
    """Merge one worker's typed collection and completion evidence."""
    del error
    state = _states[0] if _states else None
    if not isinstance(state, _ShardState):
        return
    output = node.workeroutput
    state.worker_ids.add(node.gateway.id)
    full_collection = tuple(output["flext_full_collection"])
    selected_nodeids = tuple(output["flext_selected_nodeids"])
    if not state.full_collection:
        state.full_collection = full_collection
        state.selected_nodeids = selected_nodeids
    elif (
        state.full_collection != full_collection
        or state.selected_nodeids != selected_nodeids
    ):
        state.completed_nodeids.append("__worker_collection_mismatch__")
    state.completed_nodeids.extend(output["flext_completed_nodeids"])
    state.outcomes.update(output["flext_outcomes"])


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Write typed fail-closed evidence for the aggregate CI job."""
    del exitstatus
    state = _states[0] if _states else None
    if not isinstance(state, _ShardState):
        return
    workeroutput = getattr(session.config, "workeroutput", None)
    if isinstance(workeroutput, dict):
        workeroutput["flext_full_collection"] = state.full_collection
        workeroutput["flext_selected_nodeids"] = state.selected_nodeids
        workeroutput["flext_completed_nodeids"] = tuple(state.completed_nodeids)
        workeroutput["flext_outcomes"] = state.outcomes
        return
    errors: list[str] = []
    completed = tuple(state.completed_nodeids)
    if frozenset(completed) != frozenset(state.selected_nodeids):
        errors.append("completed nodeids differ from selected nodeids")
    worker_count = len(state.worker_ids)
    if worker_count != state.max_workers:
        errors.append(
            f"observed {worker_count} xdist workers, expected {state.max_workers}"
        )
    manifest = m.Infra.PytestShardManifest(
        assignment=state.assignment,
        shard_index=state.shard_index,
        shard_count=state.shard_count,
        max_workers=state.max_workers,
        worker_count=max(worker_count, 1),
        full_collection=state.full_collection,
        selected_nodeids=state.selected_nodeids,
        completed_nodeids=completed,
        outcomes=state.outcomes,
        validation_errors=tuple(errors),
    )
    state.manifest.parent.mkdir(parents=True, exist_ok=True)
    state.manifest.write_text(
        manifest.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )


__all__ = [
    "pytest_addoption",
    "pytest_collection_modifyitems",
    "pytest_configure",
    "pytest_runtest_logreport",
    "pytest_sessionfinish",
    "pytest_testnodedown",
]
