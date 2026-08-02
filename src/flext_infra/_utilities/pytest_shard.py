"""Typed, deterministic module-isolated pytest shard planning."""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from pathlib import Path

from flext_infra import m, t


class FlextInfraUtilitiesPytestShard:
    """Build bounded pytest worker plans through the public utilities facade."""

    @staticmethod
    def source_path(nodeid: str) -> str:
        """Return the pytest source path that owns one collected node ID."""
        source_path, _, _ = nodeid.partition("::")
        if not source_path:
            msg = "pytest node id has no source path"
            raise ValueError(msg)
        return source_path

    @classmethod
    def partition_nodeids(
        cls, nodeids: t.SequenceOf[str], shard_count: int
    ) -> m.Infra.PytestShardPlan:
        """Balance whole source modules without loss, duplication, or splitting."""
        if shard_count <= 0:
            msg = "pytest shard count must be positive"
            raise ValueError(msg)
        if len(set(nodeids)) != len(nodeids):
            msg = "pytest shard input contains duplicate node ids"
            raise ValueError(msg)
        groups: dict[str, list[str]] = defaultdict(list)
        for nodeid in nodeids:
            groups[cls.source_path(nodeid)].append(nodeid)
        effective_shard_count = min(shard_count, len(groups))
        shards: list[list[str]] = [[] for _ in range(effective_shard_count)]
        loads = [0] * effective_shard_count
        ordered_groups = sorted(
            groups.items(),
            key=lambda item: (
                -len(item[1]),
                hashlib.sha256(item[0].encode()).hexdigest(),
                item[0],
            ),
        )
        for _source_path, group_nodeids in ordered_groups:
            shard_index = min(
                range(effective_shard_count), key=lambda index: (loads[index], index)
            )
            shards[shard_index].extend(group_nodeids)
            loads[shard_index] += len(group_nodeids)
        return m.Infra.PytestShardPlan(
            nodeids=tuple(nodeids),
            collection_digest=cls._manifest_digest(nodeids),
            shards=tuple(tuple(shard) for shard in shards),
        )

    @classmethod
    def source_paths_for_nodeids(cls, nodeids: t.SequenceOf[str]) -> t.StrSequence:
        """Bound worker collection arguments to the selected source modules."""
        return tuple(sorted({cls.source_path(nodeid) for nodeid in nodeids}))

    @staticmethod
    def read_nodeid_manifest(manifest: Path) -> tuple[str, ...]:
        """Read one nonempty, duplicate-free planned node-id manifest."""
        nodeids = tuple(
            line for line in manifest.read_text(encoding="utf-8").splitlines() if line
        )
        if not nodeids:
            msg = f"pytest shard manifest is empty: {manifest}"
            raise ValueError(msg)
        if len(set(nodeids)) != len(nodeids):
            msg = f"pytest shard manifest contains duplicate node ids: {manifest}"
            raise ValueError(msg)
        return nodeids

    @staticmethod
    def _manifest_digest(nodeids: t.SequenceOf[str]) -> str:
        """Return the exact newline-delimited manifest digest."""
        return hashlib.sha256(
            "".join(f"{nodeid}\n" for nodeid in nodeids).encode()
        ).hexdigest()

    @classmethod
    def write_plan(
        cls, plan_dir: Path, plan: m.Infra.PytestShardPlan
    ) -> None:
        """Persist the exact pre-execution plan for worker verification."""
        plan_dir.mkdir(parents=True, exist_ok=True)
        (plan_dir / "all-items.txt").write_text(
            "".join(f"{nodeid}\n" for nodeid in plan.nodeids), encoding="utf-8"
        )
        (plan_dir / "all-items.sha256").write_text(
            plan.collection_digest + "\n", encoding="utf-8"
        )
        for index, shard in enumerate(plan.shards):
            manifest = plan_dir / f"shard-{index}.expected.txt"
            manifest.write_text(
                "".join(f"{nodeid}\n" for nodeid in shard), encoding="utf-8"
            )
            manifest.with_suffix(".sha256").write_text(
                cls._manifest_digest(shard) + "\n", encoding="utf-8"
            )

    @classmethod
    def load_worker_manifest(
        cls, manifest: Path, shard_index: int
    ) -> m.Infra.PytestShardManifest:
        """Parse and verify the typed manifest assigned to one worker."""
        match = re.fullmatch(r"shard-(\d+)\.expected\.txt", manifest.name)
        if match is None or int(match.group(1)) != shard_index:
            msg = f"pytest shard manifest does not belong to shard {shard_index}: {manifest}"
            raise ValueError(msg)
        nodeids = cls.read_nodeid_manifest(manifest)
        digest_path = manifest.with_suffix(".sha256")
        digest = digest_path.read_text(encoding="utf-8").strip()
        expected_digest = cls._manifest_digest(nodeids)
        if digest != expected_digest:
            msg = f"pytest shard manifest digest mismatch: {manifest}"
            raise ValueError(msg)
        collection_manifest = manifest.parent / "all-items.txt"
        collection_digest_path = manifest.parent / "all-items.sha256"
        collection_nodeids = cls.read_nodeid_manifest(collection_manifest)
        collection_digest = collection_digest_path.read_text(encoding="utf-8").strip()
        if collection_digest != cls._manifest_digest(collection_nodeids):
            msg = f"pytest collection manifest digest mismatch: {collection_manifest}"
            raise ValueError(msg)
        return m.Infra.PytestShardManifest(
            shard_index=shard_index,
            nodeids=nodeids,
            digest=digest,
            collection_digest=collection_digest,
        )


__all__: list[str] = ["FlextInfraUtilitiesPytestShard"]
