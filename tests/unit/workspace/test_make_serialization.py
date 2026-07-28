"""Real-process contract for per-checkout Make validation serialization."""

from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from flext_infra import c, config, u
from flext_tests import tm


class TestsFlextInfraMakeSerialization:
    """Prove configured Make verbs share one native checkout lock."""

    _process_start_timeout_seconds = 30

    def test_config_owns_relative_checkout_lock_and_serialized_verbs(self) -> None:
        """The typed SSOT owns path, timeout, and the exact protected verbs."""
        serialization = config.Infra.codegen.make.serialization

        tm.that(serialization.lock_path.is_absolute(), eq=False)
        tm.that(serialization.timeout_seconds, gt=0)
        tm.that(serialization.verbs, eq=("check", "test", "codegen"))

    def test_check_and_test_cannot_overlap_in_one_checkout(
        self, tmp_path: Path
    ) -> None:
        """Two public CLI processes serialize their nested Make executions."""
        worker = tmp_path / "worker.py"
        worker.write_text(
            (
                "from pathlib import Path\n"
                "import sys\n"
                "import time\n"
                "root = Path(sys.argv[1])\n"
                "label = sys.argv[2]\n"
                "active = root / 'active'\n"
                "started = root / 'check-started'\n"
                "contender = root / 'test-entered'\n"
                "overlap = root / 'overlap'\n"
                "if label == 'check':\n"
                "    active.write_text(label, encoding='utf-8')\n"
                "    started.write_text(label, encoding='utf-8')\n"
                "    deadline = time.monotonic() + 0.5\n"
                "    while time.monotonic() < deadline and not contender.exists():\n"
                "        time.sleep(0.01)\n"
                "    active.unlink()\n"
                "else:\n"
                "    contender.write_text(label, encoding='utf-8')\n"
                "    try:\n"
                "        with active.open('x', encoding='utf-8') as stream:\n"
                "            stream.write(label)\n"
                "    except FileExistsError:\n"
                "        overlap.write_text(label, encoding='utf-8')\n"
                "        raise SystemExit(3)\n"
                "    active.unlink()\n"
            ),
            encoding="utf-8",
        )
        makefile = tmp_path / c.Infra.MAKEFILE_FILENAME
        makefile.write_text(
            (
                ".PHONY: _serialized_check _serialized_test\n"
                "_serialized_check:\n"
                f"\t@{sys.executable} {worker} {tmp_path} check\n"
                "_serialized_test:\n"
                f"\t@{sys.executable} {worker} {tmp_path} test\n"
            ),
            encoding="utf-8",
        )
        command = [
            sys.executable,
            "-m",
            c.Infra.PACKAGE_IMPORT_NAME,
            c.Infra.CLI_GROUP_WORKSPACE,
            "serialize-make",
            "--workspace",
            str(tmp_path),
            "--verb",
        ]

        with ThreadPoolExecutor(max_workers=2) as executor:
            check_future = executor.submit(u.Cli.run_raw, [*command, "check"], tmp_path)
            deadline = time.monotonic() + self._process_start_timeout_seconds
            while (
                not (tmp_path / "check-started").exists()
                and not check_future.done()
                and time.monotonic() < deadline
            ):
                time.sleep(0.01)
            tm.that((tmp_path / "check-started").exists(), eq=True)
            test_future = executor.submit(u.Cli.run_raw, [*command, "test"], tmp_path)
            check_process = tm.ok(
                check_future.result(timeout=self._process_start_timeout_seconds)
            )
            test_process = tm.ok(
                test_future.result(timeout=self._process_start_timeout_seconds)
            )

        tm.that(check_process.exit_code, eq=0)
        tm.that(test_process.exit_code, eq=0)
        tm.that((tmp_path / "overlap").exists(), eq=False)
        tm.that(
            (tmp_path / config.Infra.codegen.make.serialization.lock_path).is_file(),
            eq=True,
        )
