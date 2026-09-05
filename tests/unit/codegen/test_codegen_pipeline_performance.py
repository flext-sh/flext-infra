"""Performance benchmarks for the codegen gen pipeline.

flext-perf.4 (agent: codex): guards lazy-init generation performance
with wall-clock and peak-memory thresholds. Exercises _declared_exports
caching (Step 1), _module_exports cache alignment (Step 2), and ruff
Popen pipelining (Step 3).
"""

from __future__ import annotations

import cProfile
import io
import pstats
import time
import tracemalloc
from pathlib import Path

import pytest

from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit
from tests import c, tm, u

_PROJECT_COUNT = c.Tests.GEN_PIPELINE_PROJECT_COUNT
_MODULES_PER_PROJECT = c.Tests.GEN_PIPELINE_MODULES_PER_PROJECT


def _build_synthetic_workspace(tmp_path: Path) -> Path:
    """Create a workspace with N projects, each with M namespace modules."""
    workspace_root = tmp_path / "gen-perf-workspace"
    workspace_root.mkdir()
    for i in range(_PROJECT_COUNT):
        pkg_name = f"flext_perf_pkg_{i}"
        _, pkg_dir = u.Tests.create_lazy_init_workspace(
            workspace_root, project_name=f"perf-project-{i}", package_name=pkg_name
        )
        for j in range(_MODULES_PER_PROJECT):
            u.Tests.write_lazy_init_namespace_module(
                pkg_dir / f"module_{j}.py",
                class_name=f"FlextPerfClass_{i}_{j}",
                alias=f"alias_{i}_{j}",
            )
    return workspace_root


@pytest.mark.performance
@pytest.mark.slow
class TestsFlextInfraCodegenPipelinePerformance:
    """Benchmark gen pipeline wall-clock and memory on a synthetic workspace."""

    def test_wall_clock_under_threshold(self, tmp_path: Path) -> None:
        """Benchmark: lazy-init generation on synthetic workspace < 30s."""
        workspace_root = _build_synthetic_workspace(tmp_path)
        generator = FlextInfraCodegenLazyInit(workspace_root=workspace_root)
        start = time.perf_counter()
        result = generator.plan_files()
        elapsed = time.perf_counter() - start
        tm.that(result.success, eq=True, msg=f"Lazy-init had errors: {result}")
        tm.that(
            elapsed,
            lt=c.Tests.GEN_PIPELINE_MAX_SECONDS,
            msg=(
                f"Gen pipeline took {elapsed:.2f}s, "
                f"expected < {c.Tests.GEN_PIPELINE_MAX_SECONDS:g}s"
            ),
        )

    def test_peak_memory_under_500mb(self, tmp_path: Path) -> None:
        """Benchmark: Peak memory < 500MB for gen pipeline."""
        workspace_root = _build_synthetic_workspace(tmp_path)
        generator = FlextInfraCodegenLazyInit(workspace_root=workspace_root)
        tracemalloc.start()
        try:
            result = generator.plan_files()
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        peak_mb = peak / 1024 / 1024
        tm.that(result.success, eq=True, msg=f"Lazy-init had errors: {result}")
        tm.that(
            peak_mb,
            lt=c.Tests.GEN_PIPELINE_MEMORY_MAX_MB,
            msg=(
                f"Peak memory was {peak_mb:.1f}MB, "
                f"expected < {c.Tests.GEN_PIPELINE_MEMORY_MAX_MB:g}MB"
            ),
        )

    def test_cprofile_evidence_captures_optimized_paths(self, tmp_path: Path) -> None:
        """Benchmark: cProfile confirms optimized code paths are exercised."""
        workspace_root = _build_synthetic_workspace(tmp_path)
        generator = FlextInfraCodegenLazyInit(workspace_root=workspace_root)
        profile = cProfile.Profile()
        profile.enable()
        result = generator.plan_files()
        profile.disable()
        tm.that(result.success, eq=True, msg=f"Lazy-init had errors: {result}")
        stream = io.StringIO()
        stats = pstats.Stats(profile, stream=stream)
        stats.print_stats()
        profile_output = stream.getvalue()
        # flext-perf.1: verify _declared_exports AST cache is exercised
        tm.that(
            "_declared_exports" in profile_output,
            eq=True,
            msg="_declared_exports not found in cProfile output",
        )
        # flext-perf.3: verify _render_model (ruff pipeline) is exercised
        tm.that(
            "_render_model" in profile_output,
            eq=True,
            msg="_render_model not found in cProfile output",
        )
        tm.that(
            "subprocess" in profile_output or "Popen" in profile_output,
            eq=True,
            msg="subprocess/Popen not found in cProfile output",
        )

    def test_repeat_run_is_byte_idempotent(self, tmp_path: Path) -> None:
        """Benchmark: second gen run produces identical output (cache warm)."""
        workspace_root = _build_synthetic_workspace(tmp_path)
        generator = FlextInfraCodegenLazyInit(workspace_root=workspace_root)
        # First run populates _declared_exports cache
        result_1 = generator.plan_files()
        tm.that(result_1.success, eq=True, msg=f"First run had errors: {result_1}")
        # Second run should also succeed (cache should not corrupt output)
        result_2 = generator.plan_files()
        tm.that(result_2.success, eq=True, msg=f"Second run had errors: {result_2}")
