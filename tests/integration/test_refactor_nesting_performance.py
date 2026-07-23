"""Performance benchmarks for class nesting execution."""

from __future__ import annotations

import tempfile
import time
import tracemalloc
from pathlib import Path
from typing import TYPE_CHECKING, override

from flext_infra.refactor.file_executor import FlextInfraRefactorFileExecutor
from flext_infra.refactor.scanner import FlextInfraRefactorLooseClassScanner
from tests import c, p, tm, u

if TYPE_CHECKING:
    from tests import m, t


class _FileRuleHarness(FlextInfraRefactorFileExecutor):
    def __init__(self, config_path: Path) -> None:
        self._config_path = config_path
        self._class_nesting_config = None
        self._class_nesting_policy_by_family = None
        self._class_nesting_gate = None

    @override
    def _load_class_nesting_config(self) -> dict[str, object]:
        return dict(u.Cli.yaml_load_mapping(self._config_path))

    def apply_rule(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        dry_run: bool,
    ) -> p.Infra.Result:
        """Expose class nesting through the performance harness contract."""
        return self._apply_file_rule_selection(
            c.Infra.RefactorFileRuleKind.CLASS_NESTING,
            {},
            rope_project,
            resource,
            dry_run=dry_run,
        )


class TestsFlextInfraIntegrationRefactorNestingPerformance:
    """Benchmark performance of refactor service."""

    def test_process_1000_files_in_30_seconds(self) -> None:
        """Benchmark: Process 1000 files in < 30 seconds."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            for i in range(c.Tests.REFACTOR_SCAN_FILE_COUNT):
                file_dir = tmp_path / f"pkg{i // 100}" / f"subpkg{i // 10}"
                file_dir.mkdir(parents=True, exist_ok=True)
                test_file = file_dir / f"module_{i}.py"
                test_file.write_text(
                    f"\nclass LooseClass{i}:\n"
                    f'    """Loose class {i}."""\n'
                    "    pass\n\n"
                    f"def helper_{i}():\n"
                    f"    return {i}\n"
                )
            scanner = FlextInfraRefactorLooseClassScanner()
            start = time.perf_counter()
            _ = scanner.scan(tmp_path)
            elapsed = time.perf_counter() - start
            tm.that(
                elapsed,
                lt=c.Tests.REFACTOR_SCAN_MAX_SECONDS,
                msg=(
                    f"Scan took {elapsed:.2f}s, expected "
                    f"< {c.Tests.REFACTOR_SCAN_MAX_SECONDS:g}s"
                ),
            )

    def test_peak_memory_under_500mb(self) -> None:
        """Benchmark: Peak memory < 500MB for workspace scan."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            for i in range(c.Tests.REFACTOR_MEMORY_FILE_COUNT):
                file_dir = tmp_path / f"project{i // 50}" / "src"
                file_dir.mkdir(parents=True, exist_ok=True)
                test_file = file_dir / f"file_{i}.py"
                test_file.write_text(
                    f'\n"""Module {i} with substantial content."""\n'
                    "from __future__ import annotations\n\n"
                    "from typing import Optional, List, Dict, Any\n\n"
                    f"class ClassA{i}:\n"
                    f'    """Class A variant {i}."""\n'
                    "    \n"
                    "    def __init__(self, value: int) -> None:\n"
                    "        self.value = value\n"
                    "    \n"
                    "    def process(self, items: List[str]) -> Dict[str, Any]:\n"
                    '        return {"items": items, "value": self.value}\n\n'
                    f"class ClassB{i}:\n"
                    f'    """Class B variant {i}."""\n'
                    "    \n"
                    "    @staticmethod\n"
                    "    def helper(x: Optional[int]) -> int:\n"
                    "        return x or 0\n\n"
                    f"def standalone_func_{i}(a: int, b: int) -> int:\n"
                    "    return a + b\n"
                )
            scanner = FlextInfraRefactorLooseClassScanner()
            tracemalloc.start()
            _ = scanner.scan(tmp_path)
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            peak_mb = peak / 1024 / 1024
            tm.that(
                peak_mb,
                lt=c.Tests.REFACTOR_MEMORY_MAX_MB,
                msg=(
                    f"Peak memory was {peak_mb:.1f}MB, expected "
                    f"< {c.Tests.REFACTOR_MEMORY_MAX_MB:g}MB"
                ),
            )

    def test_rule_application_performance(self) -> None:
        """Benchmark rule application on single file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            test_file = tmp_path / "test.py"
            test_file.write_text(
                "\nclass TimeoutEnforcer:\n"
                "    def enforce(self, timeout: int) -> bool:\n"
                "        return True\n\n"
                "class RateLimiter:\n"
                "    def limit(self, rate: int) -> bool:\n"
                "        return True\n"
            )
            config_file = tmp_path / "mappings.yml"
            config_file.write_text(
                "\nclass_nesting:\n"
                "  - loose_name: TimeoutEnforcer\n"
                "    current_file: test.py\n"
                "    target_namespace: FlextDispatcher\n"
                "    target_name: TimeoutEnforcer\n"
                "    confidence: high\n"
                "  - loose_name: RateLimiter\n"
                "    current_file: test.py\n"
                "    target_namespace: FlextDispatcher\n"
                "    target_name: RateLimiter\n"
                "    confidence: high\n"
            )
            rule = _FileRuleHarness(config_file)
            rope_project = u.Infra.init_rope_project(tmp_path)
            resource = u.Infra.get_resource_from_path(rope_project, test_file)
            if resource is None:
                raise FileNotFoundError(test_file)
            start = time.perf_counter()
            try:
                for _ in range(c.Tests.REFACTOR_RULE_ITERATIONS):
                    _ = rule.apply_rule(rope_project, resource, dry_run=True)
                elapsed = time.perf_counter() - start
                avg_time = elapsed / c.Tests.REFACTOR_RULE_ITERATIONS
                tm.that(
                    avg_time,
                    lt=c.Tests.REFACTOR_RULE_MAX_SECONDS,
                    msg=f"Rule application too slow: {avg_time * 1000:.2f}ms",
                )
            finally:
                rope_project.close()
