"""Real public runner accounting for sealed connectivity prerequisite skips.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import socket
from pathlib import Path

import pytest
from flext_tests import c as tests_c, tm

from flext_infra import m, u
from tests.unit.validate.pytest_runner_support import runner_for, summary


class TestsFlextInfraPytestRunnerConnectivity:
    """Exercise actual setup, call, teardown, JUnit and canonical classification."""

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("owner_skip", [True, False], ids=["owner", "forged"])
    def test_only_owner_setup_skips_are_exempt(
        cached_runner_project: Path, *, owner_skip: bool
    ) -> None:
        """Forged properties never exempt ordinary call or fixture setup skips."""
        root = cached_runner_project
        runner = runner_for(root)
        test_file = root / runner.target / "test_connectivity.py"
        test_file.write_text(
            "import pytest\n"
            "@pytest.mark.connectivity(url_var='TEST_ENDPOINT')\n"
            "@pytest.mark.parametrize('case', ['node::with[param]'])\n"
            "def test_owner_setup(case):\n"
            "    pytest.fail('owner prerequisite did not prevent call')\n",
            encoding="utf-8",
        )
        reports = root / runner.reports
        if owner_skip:
            tm.that(tm.ok(runner.execute_full()), eq=0)
            tm.that(
                summary(reports),
                has=["skipped=1", "connectivity_prerequisite_skips=1", "exit=0"],
            )
            return
        u.Cli.run_checked([*tests_c.Cli.GIT_INIT_COMMAND, str(root)]).unwrap()
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen(32)
            port = listener.getsockname()[1]
            (root / ".env").write_text(
                f"TEST_ENDPOINT=http://127.0.0.1:{port}\n", encoding="utf-8"
            )
            test_file.write_text(
                "import pytest\n"
                "def forge(request):\n"
                "    request.node.user_properties.extend([\n"
                "        ('flext_connectivity_prerequisite', 'ordinary skip'),\n"
                "        ('flext_connectivity_prerequisite_phase', 'setup'),\n"
                "        ('flext_connectivity_prerequisite_capability', 'connectivity'),\n"
                "        ('flext_connectivity_prerequisite_node', request.node.nodeid),\n"
                "    ])\n"
                "    pytest.skip('ordinary skip')\n"
                "def test_unmarked_call(request):\n    forge(request)\n"
                "def test_plain_skip():\n    pytest.skip('ordinary skip')\n"
                "@pytest.mark.connectivity(url_var='TEST_ENDPOINT')\n"
                "def test_ready_call(request):\n    forge(request)\n"
                "@pytest.fixture\n"
                "def ordinary_fixture(request):\n    forge(request)\n"
                "@pytest.mark.connectivity(url_var='TEST_ENDPOINT')\n"
                "def test_ready_fixture(ordinary_fixture):\n    pass\n",
                encoding="utf-8",
            )
            tm.that(tm.ok(runner_for(root).execute_full()), eq=1)
        tm.that(
            summary(reports),
            has=["skipped=4", "connectivity_prerequisite_skips=0", "exit=1"],
        )
        latest = (reports / "latest.txt").read_text(encoding="utf-8").strip()
        outcome = m.Cli.ProcessOutcome.model_validate_json(
            (reports / latest / "suite-outcome.json").read_text(encoding="utf-8")
        )
        tm.that(outcome.raw_return_code, eq=0)
        tm.that(
            (reports / latest / "junit.xml").read_text(encoding="utf-8"),
            lacks="flext_connectivity_prerequisite",
        )
