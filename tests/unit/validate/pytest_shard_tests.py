"""Behavioral contracts for deterministic external pytest shard manifests.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_infra import config, m
from flext_infra.validate.pytest_shards import FlextInfraPytestShardValidator
from flext_tests import tm


def _valid_manifests(
    nodeids: tuple[str, ...], shard_count: int
) -> tuple[m.Infra.PytestShardManifest, ...]:
    """Build a complete manifest set from the public stable assignment rule."""
    manifests: list[m.Infra.PytestShardManifest] = []
    for shard_index in range(shard_count):
        selected = tuple(
            nodeid
            for nodeid in nodeids
            if FlextInfraPytestShardValidator.shard_index(nodeid, shard_count)
            == shard_index
        )
        manifests.append(
            m.Infra.PytestShardManifest(
                assignment="sha256-mod-v1",
                shard_index=shard_index,
                shard_count=shard_count,
                max_workers=3,
                worker_count=3,
                full_collection=nodeids,
                selected_nodeids=selected,
                completed_nodeids=tuple(reversed(selected)),
                outcomes=dict.fromkeys(selected, "passed"),
            )
        )
    return tuple(manifests)


def _validator(workspace: Path, manifests_dir: Path) -> FlextInfraPytestShardValidator:
    """Build the public aggregate service with repository-relative outputs."""
    policy = config.Infra.codegen.ci.pytest
    return FlextInfraPytestShardValidator(
        workspace=workspace,
        manifests_dir=manifests_dir,
        coverage_output=Path(policy.coverage_output),
        summary_output=Path(policy.summary_output),
    )


def _write_manifests(
    manifests_dir: Path, manifests: tuple[m.Infra.PytestShardManifest, ...]
) -> None:
    """Persist typed producer evidence using its canonical filename contract."""
    manifests_dir.mkdir(parents=True)
    for manifest in manifests:
        (manifests_dir / f"shard-{manifest.shard_index}.json").write_text(
            manifest.model_dump_json(), encoding="utf-8"
        )


def test_sha256_mod_v1_matches_the_full_digest_protocol_vector() -> None:
    """Lock cross-repository assignment to full SHA-256, never a truncated hash."""
    tm.that(FlextInfraPytestShardValidator.shard_index("abc", 16), eq=13)


@pytest.mark.parametrize("shard_count", [2, 3, 7])
def test_stable_assignment_produces_one_complete_disjoint_union(
    shard_count: int,
) -> None:
    """Every arbitrary nodeid belongs to exactly one external shard."""
    nodeids = tuple(
        sorted(f"tests/test_feature.py::test_case[{index}]" for index in range(53))
    )
    memberships = tuple(
        FlextInfraPytestShardValidator.shard_index(nodeid, shard_count)
        for nodeid in nodeids
    )

    tm.that(all(0 <= index < shard_count for index in memberships), eq=True)
    result = FlextInfraPytestShardValidator.verify_union(
        _valid_manifests(nodeids, shard_count)
    )
    summary = tm.ok(result)
    tm.that(summary.collected_count, eq=len(nodeids))
    tm.that(summary.completed_count, eq=len(nodeids))


def test_union_rejects_one_omitted_nodeid() -> None:
    """A green subset can never masquerade as complete shard coverage."""
    nodeids = tuple(
        sorted(f"tests/test_feature.py::test_case[{index}]" for index in range(20))
    )
    manifests = list(_valid_manifests(nodeids, 4))
    owner_index = FlextInfraPytestShardValidator.shard_index(nodeids[0], 4)
    owner = manifests[owner_index]
    manifests[owner_index] = owner.model_copy(
        update={
            "completed_nodeids": tuple(
                nodeid for nodeid in owner.completed_nodeids if nodeid != nodeids[0]
            )
        }
    )

    result = FlextInfraPytestShardValidator.verify_union(tuple(manifests))

    tm.fail(result, has="omitted or added nodeids")


def test_union_rejects_duplicate_nodeid_completion() -> None:
    """Repeated execution is a failure even when set coverage appears complete."""
    nodeids = tuple(
        sorted(f"tests/test_feature.py::test_case[{index}]" for index in range(20))
    )
    manifests = list(_valid_manifests(nodeids, 4))
    owner_index = next(
        index for index, manifest in enumerate(manifests) if manifest.completed_nodeids
    )
    owner = manifests[owner_index]
    duplicate = owner.completed_nodeids[0]
    manifests[owner_index] = owner.model_copy(
        update={"completed_nodeids": (*owner.completed_nodeids, duplicate)}
    )

    result = FlextInfraPytestShardValidator.verify_union(tuple(manifests))

    tm.fail(result, has="duplicate nodeids")


def test_union_rejects_different_worker_collection() -> None:
    """Every external shard must prove the same unfiltered collection."""
    nodeids = tuple(
        sorted(f"tests/test_feature.py::test_case[{index}]" for index in range(20))
    )
    manifests = list(_valid_manifests(nodeids, 4))
    manifests[1] = manifests[1].model_copy(update={"full_collection": nodeids[:-1]})

    result = FlextInfraPytestShardValidator.verify_union(tuple(manifests))

    tm.fail(result, has="collection differs")


def test_union_rejects_worker_count_below_the_declared_ceiling() -> None:
    """Observed xdist evidence must match the bounded worker contract."""
    nodeids = tuple(
        sorted(f"tests/test_feature.py::test_case[{index}]" for index in range(20))
    )
    manifests = list(_valid_manifests(nodeids, 4))
    manifests[1] = manifests[1].model_copy(update={"worker_count": 2})

    result = FlextInfraPytestShardValidator.verify_union(tuple(manifests))

    tm.fail(result, has="observed 2 workers, expected 3")


def test_union_rejects_a_non_passing_recorded_outcome() -> None:
    """A completed runtest protocol is insufficient unless its outcome passed."""
    nodeids = ("tests/test_feature.py::test_only_case",)
    manifests = list(_valid_manifests(nodeids, 2))
    owner_index = FlextInfraPytestShardValidator.shard_index(nodeids[0], 2)
    manifests[owner_index] = manifests[owner_index].model_copy(
        update={"outcomes": {nodeids[0]: "skipped"}}
    )

    result = FlextInfraPytestShardValidator.verify_union(tuple(manifests))

    tm.fail(result, has="non-passing outcomes")


def test_union_accepts_valid_empty_external_buckets() -> None:
    """A bucket with no assigned nodeids is valid when the exact union is complete."""
    nodeids = ("tests/test_feature.py::test_only_case",)
    manifests = _valid_manifests(nodeids, 8)

    result = FlextInfraPytestShardValidator.verify_union(manifests)

    summary = tm.ok(result)
    tm.that(summary.completed_count, eq=1)
    tm.that(sum(not manifest.selected_nodeids for manifest in manifests), gt=0)


def test_union_rejects_an_empty_complete_collection() -> None:
    """A suite with no collected tests cannot produce successful CI evidence."""
    result = FlextInfraPytestShardValidator.verify_union(_valid_manifests((), 2))

    tm.fail(result, has="collection is empty")


def test_coverage_allows_missing_data_only_for_empty_buckets(tmp_path: Path) -> None:
    """Coverage is mandatory for every bucket that executed at least one test."""
    nodeids = ("tests/test_feature.py::test_only_case",)
    manifests = _valid_manifests(nodeids, 8)
    owner_index = FlextInfraPytestShardValidator.shard_index(nodeids[0], 8)
    coverage_file = tmp_path / f".coverage.shard-{owner_index}"
    coverage_file.write_bytes(b"coverage-data")

    resolved = FlextInfraPytestShardValidator.verify_coverage_files(manifests, tmp_path)

    files = tm.ok(resolved)
    tm.that(files, eq=(coverage_file,))


def test_coverage_rejects_missing_data_for_a_nonempty_bucket(tmp_path: Path) -> None:
    """A completed shard without coverage can never satisfy the aggregate gate."""
    nodeids = ("tests/test_feature.py::test_only_case",)

    resolved = FlextInfraPytestShardValidator.verify_coverage_files(
        _valid_manifests(nodeids, 8), tmp_path
    )

    tm.fail(resolved, has="coverage missing for non-empty indexes")


def test_aggregate_rejects_manifest_path_outside_workspace(tmp_path: Path) -> None:
    """CLI paths can never escape the declared repository root."""
    result = _validator(tmp_path / "workspace", tmp_path).execute()

    tm.fail(result, has="path escapes workspace")


def test_aggregate_rejects_malformed_manifest_json(tmp_path: Path) -> None:
    """Manifest JSON crosses exactly one fail-closed typed boundary."""
    manifests_dir = tmp_path / config.Infra.codegen.ci.pytest.reports_dir
    manifests_dir.mkdir(parents=True)
    (manifests_dir / "shard-0.json").write_text("{", encoding="utf-8")

    result = _validator(tmp_path, manifests_dir).execute()

    tm.fail(result, has="invalid pytest shard manifest")


def test_aggregate_rejects_filename_index_mismatch(tmp_path: Path) -> None:
    """Downloaded artifact names must preserve their producer shard identity."""
    policy = config.Infra.codegen.ci.pytest
    nodeids = ("tests/test_feature.py::test_only_case",)
    manifest = _valid_manifests(nodeids, policy.shard_count)[1]
    manifests_dir = tmp_path / policy.reports_dir
    manifests_dir.mkdir(parents=True)
    (manifests_dir / "shard-0.json").write_text(
        manifest.model_dump_json(), encoding="utf-8"
    )

    result = _validator(tmp_path, manifests_dir).execute()

    tm.fail(result, has="manifest filename mismatch")


def test_aggregate_rejects_manifest_policy_drift(tmp_path: Path) -> None:
    """Aggregate validates against the same typed policy that rendered CI."""
    manifests_dir = tmp_path / config.Infra.codegen.ci.pytest.reports_dir
    _write_manifests(
        manifests_dir, _valid_manifests(("tests/test_feature.py::test_only_case",), 2)
    )

    result = _validator(tmp_path, manifests_dir).execute()

    tm.fail(result, has="count differs from typed CI policy")


__all__: list[str] = []
