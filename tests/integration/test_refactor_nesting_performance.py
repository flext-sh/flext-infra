"""Performance benchmarks for class nesting execution."""

from __future__ import annotations

import tempfile
import time
import tracemalloc
from pathlib import Path

from flext_infra.refactor.scanner import FlextInfraRefactorLooseClassScanner
from flext_infra.refactor.service import FlextInfraRefactorService
from tests import c, tm


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

    def test_rule_application_performance(self, tmp_path: Path) -> None:
        """Benchmark one public refactor pass over a project module."""
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "app"\nversion = "0.1.0"\n', encoding="utf-8"
        )
        package_dir = tmp_path / "src" / "app" / "_dispatcher"
        package_dir.mkdir(parents=True)
        (tmp_path / "src" / "app" / "__init__.py").write_text("", encoding="utf-8")
        (package_dir / "__init__.py").write_text("", encoding="utf-8")
        target_file = package_dir / "timeout.py"
        target_file.write_text(
            "class TimeoutEnforcer:\n"
            "    def enforce(self, timeout: int) -> bool:\n"
            "        return True\n\n\n"
            "class RateLimiter:\n"
            "    def limit(self, rate: int) -> bool:\n"
            "        return True\n",
            encoding="utf-8",
        )
        service = FlextInfraRefactorService()
        tm.ok(service.load_rules())

        start = time.perf_counter()
        for _ in range(c.Tests.REFACTOR_RULE_ITERATIONS):
            _ = service.orchestrator.refactor_file(target_file, dry_run=True)
        elapsed = time.perf_counter() - start

        avg_time = elapsed / c.Tests.REFACTOR_RULE_ITERATIONS
        tm.that(
            avg_time,
            lt=c.Tests.REFACTOR_RULE_MAX_SECONDS,
            msg=f"Rule application too slow: {avg_time * 1000:.2f}ms",
        )
