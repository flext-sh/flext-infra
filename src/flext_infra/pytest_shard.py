"""Deterministic pytest item partitioning for generated Make test sessions."""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import u


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register generated-Make-only shard boundary options."""
    group = parser.getgroup("flext-shard")
    group.addoption("--flext-shard-count", type=int)
    group.addoption("--flext-shard-index", type=int)
    group.addoption("--flext-shard-manifest", type=Path)
    group.addoption("--flext-shard-plan-dir", type=Path)
    group.addoption("--flext-shard-source-manifest", type=Path)


def pytest_configure(config: pytest.Config) -> None:
    """Restrict worker collection to the exact planned node ids."""
    source_manifest = config.getoption("--flext-shard-source-manifest")
    if source_manifest is None:
        return
    if not isinstance(source_manifest, Path):
        msg = "--flext-shard-source-manifest must be a path"
        raise pytest.UsageError(msg)
    shard_index = config.getoption("--flext-shard-index")
    if not isinstance(shard_index, int):
        msg = "--flext-shard-index is required with a source manifest"
        raise pytest.UsageError(msg)
    try:
        worker_manifest = u.Infra.load_worker_manifest(source_manifest, shard_index)
    except (OSError, ValueError) as exc:
        msg = f"cannot read pytest shard manifest {source_manifest}: {exc}"
        raise pytest.UsageError(msg) from exc
    config.args[:] = u.Infra.source_paths_for_nodeids(worker_manifest.nodeids)


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Select one stable shard and write its exact item manifest."""
    shard_count = config.getoption("--flext-shard-count")
    shard_index = config.getoption("--flext-shard-index")
    manifest = config.getoption("--flext-shard-manifest")
    plan_dir = config.getoption("--flext-shard-plan-dir")
    source_manifest = config.getoption("--flext-shard-source-manifest")
    if (
        shard_count is None
        and shard_index is None
        and manifest is None
        and plan_dir is None
        and source_manifest is None
    ):
        return
    if not isinstance(shard_count, int) or shard_count <= 0:
        msg = "--flext-shard-count must be a positive integer"
        raise pytest.UsageError(msg)
    if plan_dir is not None:
        if (
            shard_index is not None
            or manifest is not None
            or source_manifest is not None
        ):
            msg = "--flext-shard-plan-dir cannot be combined with worker shard options"
            raise pytest.UsageError(msg)
        if not isinstance(plan_dir, Path):
            msg = "--flext-shard-plan-dir must be a path"
            raise pytest.UsageError(msg)
        nodeids = tuple(item.nodeid for item in items)
        try:
            plan = u.Infra.partition_nodeids(nodeids, shard_count)
        except ValueError as exc:
            raise pytest.UsageError(str(exc)) from exc
        u.Infra.write_plan(plan_dir, plan)
        return
    if not isinstance(shard_index, int) or not 0 <= shard_index < shard_count:
        msg = "--flext-shard-index must be within the configured shard count"
        raise pytest.UsageError(msg)
    if not isinstance(manifest, Path):
        msg = "--flext-shard-manifest is required"
        raise pytest.UsageError(msg)
    if not isinstance(source_manifest, Path):
        msg = "--flext-shard-source-manifest is required"
        raise pytest.UsageError(msg)
    try:
        worker_manifest = u.Infra.load_worker_manifest(source_manifest, shard_index)
    except (OSError, ValueError) as exc:
        raise pytest.UsageError(str(exc)) from exc
    expected = worker_manifest.nodeids
    nodeids = tuple(item.nodeid for item in items)
    if len(nodeids) != len(expected) or set(nodeids) != set(expected):
        missing = set(expected).difference(nodeids)
        unexpected = set(nodeids).difference(expected)
        msg = (
            "pytest shard collection differs from its plan "
            f"(missing={len(missing)}, unexpected={len(unexpected)})"
        )
        raise pytest.UsageError(msg)
    manifest.write_text("".join(f"{item.nodeid}\n" for item in items), encoding="utf-8")


__all__ = ["pytest_addoption", "pytest_collection_modifyitems", "pytest_configure"]
