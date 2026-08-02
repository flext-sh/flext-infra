"""Structural contracts for deterministic generated-Make pytest sharding."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_infra import u
from flext_tests import tm


@pytest.mark.parametrize("shard_count", [1, 2, 7, 19])
def test_partition_is_complete_unique_and_order_stable(shard_count: int) -> None:
    """Every arbitrary valid partition owns every node id exactly once."""
    nodeids = tuple(
        f"tests/test_module_{index % 29}.py::test_case[{index}]" for index in range(257)
    )

    first = u.Infra.partition_nodeids(nodeids, shard_count)
    second = u.Infra.partition_nodeids(tuple(reversed(nodeids)), shard_count)
    flattened = tuple(nodeid for shard in first.shards for nodeid in shard)

    tm.that(len(first.shards), eq=shard_count)
    tm.that(len(flattened), eq=len(nodeids))
    tm.that(set(flattened), eq=set(nodeids))
    tm.that(
        tuple(set(shard) for shard in first.shards),
        eq=tuple(set(shard) for shard in second.shards),
    )


def test_partition_keeps_every_source_module_in_one_shard() -> None:
    """Module-level test state cannot be split between concurrent workers."""
    nodeids = tuple(
        f"tests/test_module_{module}.py::test_case[{case}]"
        for module in range(17)
        for case in range(3)
    )

    plan = u.Infra.partition_nodeids(nodeids, 7)
    source_owner = {
        u.Infra.source_path(nodeid): shard_index
        for shard_index, shard in enumerate(plan.shards)
        for nodeid in shard
    }

    tm.that(len(source_owner), eq=17)
    for shard_index, shard in enumerate(plan.shards):
        for nodeid in shard:
            tm.that(source_owner[u.Infra.source_path(nodeid)], eq=shard_index)


def test_source_paths_are_bounded_to_unique_modules() -> None:
    """A worker receives source files, never one invocation argument per test item."""
    nodeids = (
        "tests/test_alpha.py::test_one",
        "tests/test_alpha.py::test_two[param]",
        "tests/test_beta.py::test_three",
    )

    tm.that(
        u.Infra.source_paths_for_nodeids(nodeids),
        eq=("tests/test_alpha.py", "tests/test_beta.py"),
    )


def test_worker_manifest_stays_valid_when_it_has_fewer_modules_than_all_shards(
    tmp_path: Path,
) -> None:
    """A worker consumes its owned module list instead of repartitioning it."""
    nodeids = tuple(f"tests/test_module_{index}.py::test_case" for index in range(4))
    plan = u.Infra.partition_nodeids(nodeids, 4)
    u.Infra.write_plan(tmp_path, plan)

    manifest = u.Infra.load_worker_manifest(
        tmp_path / "shard-0.expected.txt", shard_index=0
    )

    tm.that(len(manifest.nodeids), eq=1)
    tm.that(
        u.Infra.source_paths_for_nodeids(manifest.nodeids),
        eq=(u.Infra.source_path(manifest.nodeids[0]),),
    )
    tm.that(manifest.collection_digest, eq=plan.collection_digest)


def test_partition_uses_the_available_module_count_without_empty_shards() -> None:
    """A small project uses a bounded effective count instead of failing at 16."""
    nodeids = (
        "tests/test_alpha.py::test_one",
        "tests/test_alpha.py::test_two",
        "tests/test_beta.py::test_one",
    )

    plan = u.Infra.partition_nodeids(nodeids, 16)

    tm.that(len(plan.shards), eq=2)
    tm.that(all(plan.shards), eq=True)
    tm.that(plan.nodeids, eq=nodeids)


def test_partition_rejects_duplicate_nodeids() -> None:
    """A duplicate collection identity is never silently assigned twice."""
    with pytest.raises(ValueError, match="duplicate node ids"):
        u.Infra.partition_nodeids(("tests/test_a.py::test_a",) * 2, 2)


def test_partition_rejects_non_positive_shard_count() -> None:
    """Invalid configuration fails before a shard plan can be emitted."""
    with pytest.raises(ValueError, match="positive"):
        u.Infra.partition_nodeids(("tests/test_a.py::test_a",), 0)
