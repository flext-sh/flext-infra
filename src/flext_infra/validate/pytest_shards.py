"""Deterministic pytest shard assignment and exact-union validation.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Annotated, override

from flext_core import r
from flext_infra import config, m, u
from flext_infra.base import s

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraPytestShardValidator(s[bool]):
    """Verify shard manifests exactly cover collection and combine coverage."""

    workspace: Annotated[Path, m.Field(description="Repository validation root")]
    manifests_dir: Annotated[
        Path, m.Field(description="Directory containing shard manifests and coverage")
    ]
    coverage_output: Annotated[
        Path, m.Field(description="Combined Cobertura XML output path")
    ]
    summary_output: Annotated[
        Path, m.Field(description="Verified shard-union JSON summary path")
    ]

    @staticmethod
    def shard_index(nodeid: str, shard_count: int) -> int:
        """Assign one nodeid using the versioned stable SHA-256 modulo rule."""
        digest = u.Cli.sha256_content(nodeid)
        return int(digest, 16) % shard_count

    @classmethod
    def verify_union(
        cls, manifests: t.SequenceOf[m.Infra.PytestShardManifest]
    ) -> p.Result[m.Infra.PytestShardUnionSummary]:
        """Prove external shard selections are complete, disjoint, and finished."""
        if not manifests:
            return r.fail("pytest shard manifests are missing")
        first = manifests[0]
        shard_count = first.shard_count
        if len(manifests) != shard_count:
            return r.fail(
                f"pytest shard manifest count mismatch: {len(manifests)} != {shard_count}"
            )
        indexes = tuple(manifest.shard_index for manifest in manifests)
        expected_indexes = tuple(range(shard_count))
        if tuple(sorted(indexes)) != expected_indexes:
            return r.fail(
                f"pytest shard indexes mismatch: {sorted(indexes)} != {list(expected_indexes)}"
            )
        full_collection = tuple(sorted(first.full_collection))
        if not full_collection:
            return r.fail("complete pytest collection is empty")
        if first.full_collection != full_collection:
            return r.fail("complete pytest collection is not canonically sorted")
        if len(full_collection) != len(frozenset(full_collection)):
            return r.fail("complete pytest collection contains duplicate nodeids")
        completed_union: list[str] = []
        selected_union: list[str] = []
        for manifest in sorted(manifests, key=lambda item: item.shard_index):
            if manifest.shard_count != shard_count:
                return r.fail("pytest shard counts differ")
            if manifest.max_workers != first.max_workers:
                return r.fail("pytest shard worker ceilings differ")
            if manifest.worker_count != manifest.max_workers:
                return r.fail(
                    f"pytest shard {manifest.shard_index} observed "
                    f"{manifest.worker_count} workers, expected {manifest.max_workers}"
                )
            if manifest.full_collection != full_collection:
                return r.fail(f"pytest shard {manifest.shard_index} collection differs")
            if manifest.validation_errors:
                return r.fail(
                    f"pytest shard {manifest.shard_index} reported errors: "
                    + "; ".join(manifest.validation_errors)
                )
            expected_selected = tuple(
                nodeid
                for nodeid in full_collection
                if cls.shard_index(nodeid, shard_count) == manifest.shard_index
            )
            if manifest.selected_nodeids != expected_selected:
                return r.fail(
                    f"pytest shard {manifest.shard_index} selection differs "
                    "from stable nodeid assignment"
                )
            if len(manifest.completed_nodeids) != len(
                frozenset(manifest.completed_nodeids)
            ):
                return r.fail(
                    f"pytest shard {manifest.shard_index} completed duplicate nodeids"
                )
            if frozenset(manifest.completed_nodeids) != frozenset(expected_selected):
                return r.fail(
                    f"pytest shard {manifest.shard_index} omitted or added nodeids"
                )
            if frozenset(manifest.outcomes) != frozenset(expected_selected):
                return r.fail(
                    f"pytest shard {manifest.shard_index} outcome keys differ "
                    "from its selection"
                )
            unsuccessful = tuple(
                sorted(
                    nodeid
                    for nodeid, outcome in manifest.outcomes.items()
                    if outcome != "passed"
                )
            )
            if unsuccessful:
                return r.fail(
                    f"pytest shard {manifest.shard_index} has non-passing outcomes: "
                    + ", ".join(unsuccessful)
                )
            selected_union.extend(expected_selected)
            completed_union.extend(manifest.completed_nodeids)
        if len(selected_union) != len(frozenset(selected_union)):
            return r.fail("pytest shard selections overlap")
        if frozenset(selected_union) != frozenset(full_collection):
            return r.fail("pytest shard selection union omits or adds nodeids")
        if len(completed_union) != len(frozenset(completed_union)):
            return r.fail("pytest shard completed union contains duplicates")
        if frozenset(completed_union) != frozenset(full_collection):
            return r.fail("pytest shard completed union omits or adds nodeids")
        return r.ok(
            m.Infra.PytestShardUnionSummary(
                assignment=first.assignment,
                shard_count=shard_count,
                collected_count=len(full_collection),
                completed_count=len(completed_union),
            )
        )

    def _load_manifests(
        self, manifests_dir: Path
    ) -> p.Result[tuple[m.Infra.PytestShardManifest, ...]]:
        """Load every manifest through the typed JSON boundary."""
        paths = tuple(sorted(manifests_dir.glob("shard-*.json")))
        manifests: list[m.Infra.PytestShardManifest] = []
        for path in paths:
            loaded = u.Cli.files_read_text(path)
            if loaded.failure:
                return r.fail(loaded.error or f"failed to read shard manifest: {path}")
            try:
                manifest = m.Infra.PytestShardManifest.model_validate_json(loaded.value)
            except ValueError as exc:
                return r.fail(f"invalid pytest shard manifest {path}: {exc}")
            expected_name = f"shard-{manifest.shard_index}.json"
            if path.name != expected_name:
                return r.fail(
                    f"pytest shard manifest filename mismatch: {path.name} != "
                    f"{expected_name}"
                )
            manifests.append(manifest)
        return r.ok(tuple(manifests))

    @staticmethod
    def _verify_policy(
        manifests: t.SequenceOf[m.Infra.PytestShardManifest],
    ) -> p.Result[bool]:
        """Require manifests to match the typed CI policy that rendered Make."""
        if not manifests:
            return r.fail("pytest shard manifests are missing")
        policy = config.Infra.codegen.ci.pytest
        first = manifests[0]
        if first.shard_count != policy.shard_count:
            return r.fail("pytest shard count differs from typed CI policy")
        if first.max_workers != policy.max_workers_per_shard:
            return r.fail("pytest shard worker ceiling differs from typed CI policy")
        return r.ok(True)

    @staticmethod
    def verify_coverage_files(
        manifests: t.SequenceOf[m.Infra.PytestShardManifest], manifests_dir: Path
    ) -> p.Result[tuple[Path, ...]]:
        """Resolve exact per-shard data files, allowing valid empty buckets."""
        coverage_files = tuple(sorted(manifests_dir.glob(".coverage.shard-*")))
        shard_count = manifests[0].shard_count
        indexes: list[int] = []
        for path in coverage_files:
            suffix = path.name.removeprefix(".coverage.shard-")
            if not suffix.isdecimal() or str(int(suffix)) != suffix:
                return r.fail(f"invalid pytest shard coverage filename: {path.name}")
            index = int(suffix)
            if not 0 <= index < shard_count:
                return r.fail(f"pytest shard coverage index is out of range: {index}")
            if path.is_symlink() or not path.is_file() or path.stat().st_size == 0:
                return r.fail(f"pytest shard coverage file is invalid: {path.name}")
            indexes.append(index)
        if len(indexes) != len(frozenset(indexes)):
            return r.fail("pytest shard coverage indexes contain duplicates")
        required_indexes = frozenset(
            manifest.shard_index for manifest in manifests if manifest.selected_nodeids
        )
        missing = tuple(sorted(required_indexes.difference(indexes)))
        if missing:
            return r.fail(
                f"pytest shard coverage missing for non-empty indexes: {list(missing)}"
            )
        if not coverage_files:
            return r.fail("pytest shard coverage files are missing")
        return r.ok(coverage_files)

    def _combine_coverage(
        self,
        summary: m.Infra.PytestShardUnionSummary,
        manifests: t.SequenceOf[m.Infra.PytestShardManifest],
        *,
        workspace: Path,
        manifests_dir: Path,
        coverage_output: Path,
    ) -> p.Result[m.Infra.PytestShardUnionSummary]:
        """Combine verified non-empty shard coverage and enforce its threshold."""
        resolved_files = self.verify_coverage_files(manifests, manifests_dir)
        if resolved_files.failure:
            return r.fail(
                resolved_files.error or "failed to resolve pytest shard coverage files"
            )
        coverage_files = resolved_files.value
        rcfile = workspace / "pyproject.toml"
        if not rcfile.is_file():
            return r.fail(f"coverage configuration is missing: {rcfile}")
        ensure_coverage = u.Cli.ensure_dir(coverage_output.parent)
        if ensure_coverage.failure:
            return r.fail(
                ensure_coverage.error
                or "failed to create combined coverage output directory"
            )
        rendered = self._render_exact_coverage(
            coverage_files,
            workspace=workspace,
            rcfile=rcfile,
            coverage_output=coverage_output,
        )
        if rendered.failure:
            return r.fail(rendered.error or "failed to render exact shard coverage")
        if not coverage_output.is_file() or coverage_output.stat().st_size == 0:
            return r.fail("combined pytest shard coverage XML is missing or empty")
        return r.ok(
            summary.model_copy(
                update={"coverage_files": tuple(path.name for path in coverage_files)}
            )
        )

    @staticmethod
    def _render_staged_coverage(
        coverage_files: t.SequenceOf[Path],
        *,
        isolated_root: Path,
        workspace: Path,
        rcfile: Path,
        coverage_output: Path,
    ) -> p.Result[bool]:
        """Copy exact inputs, combine them, and enforce the aggregate threshold."""
        for coverage_file in coverage_files:
            copied = u.Cli.files_copy(coverage_file, isolated_root / coverage_file.name)
            if copied.failure:
                return r.fail(copied.error or "failed to stage shard coverage file")
        combined_data = isolated_root / ".coverage"
        combine = u.Cli.run(
            (
                sys.executable,
                "-m",
                "coverage",
                "combine",
                "--keep",
                f"--data-file={combined_data}",
                f"--rcfile={rcfile}",
                str(isolated_root),
            ),
            cwd=workspace,
        )
        if combine.failure:
            return r.fail(combine.error or "failed to combine pytest shard coverage")
        xml = u.Cli.run(
            (
                sys.executable,
                "-m",
                "coverage",
                "xml",
                f"--data-file={combined_data}",
                f"--rcfile={rcfile}",
                "-o",
                str(coverage_output),
            ),
            cwd=workspace,
        )
        if xml.failure:
            return r.fail(xml.error or "failed to render combined coverage XML")
        return r.ok(True)

    @classmethod
    def _render_exact_coverage(
        cls,
        coverage_files: t.SequenceOf[Path],
        *,
        workspace: Path,
        rcfile: Path,
        coverage_output: Path,
    ) -> p.Result[bool]:
        """Isolate validated coverage inputs from stale or injected data files."""
        try:
            with TemporaryDirectory(prefix="flext-coverage-") as isolated_dir:
                return cls._render_staged_coverage(
                    coverage_files,
                    isolated_root=Path(isolated_dir),
                    workspace=workspace,
                    rcfile=rcfile,
                    coverage_output=coverage_output,
                )
        except OSError as exc:
            return r.fail_op("stage exact pytest shard coverage files", exc)

    def _resolve_input_path(self, path: Path) -> p.Result[Path]:
        """Resolve one CLI path inside the declared repository root."""
        workspace = self.workspace.expanduser().resolve()
        candidate = path.expanduser()
        resolved = (
            candidate if candidate.is_absolute() else workspace / candidate
        ).resolve()
        if not resolved.is_relative_to(workspace):
            return r.fail(f"pytest shard path escapes workspace: {path}")
        return r.ok(resolved)

    @override
    def execute(self) -> p.Result[bool]:
        """Verify exact nodeid union, combine coverage, and write typed summary."""
        workspace = self.workspace.expanduser().resolve()
        resolved_manifests = self._resolve_input_path(self.manifests_dir)
        if resolved_manifests.failure:
            return r.fail(resolved_manifests.error or "invalid shard manifests path")
        resolved_coverage = self._resolve_input_path(self.coverage_output)
        if resolved_coverage.failure:
            return r.fail(resolved_coverage.error or "invalid shard coverage path")
        resolved_summary = self._resolve_input_path(self.summary_output)
        if resolved_summary.failure:
            return r.fail(resolved_summary.error or "invalid shard summary path")
        manifests_dir = resolved_manifests.value
        coverage_output = resolved_coverage.value
        summary_output = resolved_summary.value
        manifests = self._load_manifests(manifests_dir)
        if manifests.failure:
            return r.fail(manifests.error or "failed to load pytest shard manifests")
        policy = self._verify_policy(manifests.value)
        if policy.failure:
            return r.fail(policy.error or "pytest shard policy validation failed")
        verified = self.verify_union(manifests.value)
        if verified.failure:
            return r.fail(verified.error or "pytest shard union validation failed")
        combined = self._combine_coverage(
            verified.value,
            manifests.value,
            workspace=workspace,
            manifests_dir=manifests_dir,
            coverage_output=coverage_output,
        )
        if combined.failure:
            return r.fail(combined.error or "pytest shard coverage combine failed")
        ensure_output = u.Cli.ensure_dir(summary_output.parent)
        if ensure_output.failure:
            return r.fail(
                ensure_output.error or "failed to create pytest shard summary directory"
            )
        written = u.Cli.atomic_write_text_file(
            summary_output, combined.value.model_dump_json(indent=2) + "\n"
        )
        if written.failure:
            return r.fail(written.error or "failed to write pytest shard summary")
        return r.ok(True)


__all__: list[str] = ["FlextInfraPytestShardValidator"]
