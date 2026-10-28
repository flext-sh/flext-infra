"""Real collected Markdown execution owns temporary modules without leaking them.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from flext_infra import config
from tests import c, m, tm, u


class TestsFlextInfraMarkdownModule:
    """Exercise registration and cleanup through the installed SDK executor."""

    @staticmethod
    @pytest.mark.parametrize(
        ("previous", "failure", "replacement"),
        [
            (False, False, False),
            (True, False, False),
            (False, True, False),
            (True, True, False),
            (True, True, True),
        ],
    )
    def test_collected_fences_restore_modules_and_supplier_binding(
        tmp_path: Path,
        *,
        previous: bool,
        failure: bool,
        replacement: bool,
    ) -> None:
        """Generics see their exact globals; failed fences cannot leak state."""
        (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
        (tmp_path / "conftest.py").write_text(
            "import sys\n"
            "import types\n"
            "from pathlib import Path\n"
            "from types import ModuleType\n"
            "import pytest\n"
            "from pytest_markdown_docs import plugin\n"
            "from flext_tests import tm\n\n"
            "original_types = plugin.types\n"
            f"expected = ModuleType('fence') if {previous!r} else None\n"
            "if expected is not None:\n"
            "    sys.modules['fence'] = expected\n"
            "seen: list[ModuleType] = []\n\n"
            "def pytest_markdown_docs_globals() -> dict[str, ModuleType]:\n"
            "    return {'probe': sys.modules[__name__]}\n\n"
            "def pytest_runtest_teardown(item: pytest.Item) -> None:\n"
            "    tm.that(plugin.types is original_types, eq=True)\n"
            "    tm.that(types.ModuleType is ModuleType, eq=True)\n"
            "    tm.that(sys.modules.get('fence') is expected, eq=True)\n"
            "    if expected is None:\n"
            "        tm.that('fence' in sys.modules, eq=False)\n\n"
            "def pytest_sessionfinish(session: pytest.Session) -> None:\n"
            "    tm.that(len(seen), eq=2)\n"
            "    tm.that(seen[0] is seen[1], eq=False)\n"
            "    Path(session.config.rootpath, 'lifecycle.txt').write_text(\n"
            "        'clean', encoding='utf-8')\n",
            encoding="utf-8",
        )
        fence = (
            "import sys\n"
            "from types import ModuleType\n"
            "from flext_core import m, r\n"
            "from flext_tests import tm\n"
            "tm.that(type(sys.modules[__name__]) is ModuleType, eq=True)\n"
            "tm.that(sys.modules[__name__].__dict__ is globals(), eq=True)\n"
            "tm.that('fence_marker' in globals(), eq=False)\n"
            "fence_marker = 'local to this execution'\n"
            "probe.seen.append(sys.modules[__name__])\n"
            "class FenceValue[T](m.Value):\n"
            "    value: T\n"
            "tm.that(FenceValue[int](value=7).value, eq=7)\n"
            "tm.that(r[int].ok(7).unwrap(), eq=7)\n"
        )
        ending = (
            "probe.expected = ModuleType(__name__)\n"
            "sys.modules[__name__] = probe.expected\n"
            if replacement
            else ""
        ) + ("raise ValueError('requested fence failure')\n" if failure else "")
        (tmp_path / "sample.md").write_text(
            f"```python\n{fence}{ending}```\n\n```python\n{fence}```\n",
            encoding="utf-8",
        )
        output = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-m",
                    "pytest",
                    "sample.md",
                    "--markdown-docs",
                    "-p",
                    "pytest_markdown_docs.plugin",
                    "-p",
                    "pytest_reportlog.plugin",
                    "-p",
                    config.Infra.tooling.tools.pytest.enforcement_plugin,
                    "-p",
                    "flext_infra._pytest.collection",
                ),
                cwd=tmp_path,
                timeout=config.Infra.tooling.tools.pytest.slow_timeout_seconds,
                options=m.Cli.ProcessOptions(
                    env={"PYTEST_DISABLE_PLUGIN_AUTOLOAD": c.ParserBooleanToken.ONE},
                    remove_env_keys=("PYTEST_ADDOPTS",),
                ),
            ),
        )
        tm.that(output.outcome.timed_out, eq=False)
        tm.that(
            output.outcome.raw_return_code,
            eq=int(failure),
            msg=output.stdout + output.stderr,
        )
        tm.that(
            output.stdout,
            has="1 failed, 1 passed" if failure else "2 passed",
        )
        if failure:
            tm.that(output.stdout, has="requested fence failure")
        tm.that((tmp_path / "lifecycle.txt").read_text(encoding="utf-8"), eq="clean")
