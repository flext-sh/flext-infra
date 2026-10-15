"""Prove source-assertion detection through the public native codemod scan.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import flext_tests
import pytest

from flext_infra.codemod import FlextInfraModGateEngine
from tests import tm, u


class TestsFlextInfraSourceIntrospectionBoundary:
    """Keep source introspection distinct from runtime and generated artifacts."""

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize(
        ("consumer", "expected_findings"),
        [
            (
                (
                    "import inspect\n"
                    'assert "def" in inspect.getsource(inspect.isfunction)\n'
                ),
                1,
            ),
            (
                (
                    "import inspect as reflection\n"
                    'assert "def" in reflection.getsource(reflection.isfunction)\n'
                ),
                1,
            ),
            (
                (
                    "from inspect import getsource, isfunction\n"
                    'assert "def" in getsource(isfunction)\n'
                ),
                1,
            ),
            (
                (
                    "from inspect import getsource as source_of, isfunction\n"
                    'assert "def" in source_of(isfunction)\n'
                ),
                1,
            ),
            (
                (
                    "from inspect import getsource as source_of, isfunction\n"
                    "from flext_tests import tm\n"
                    'tm.that(source_of(isfunction), has="def")\n'
                ),
                1,
            ),
            (
                (
                    "import inspect\n"
                    "from flext_tests import tm\n"
                    'tm.that(inspect.getsource(inspect.isfunction), has="def", '
                    'lacks="unrelated implementation marker")\n'
                ),
                1,
            ),
            (
                (
                    "from inspect import getsource as source_of, isfunction\n"
                    "import inspect\n"
                    "reader = inspect\n"
                    'assert "def" in reader.getsource(isfunction)\n'
                ),
                1,
            ),
            (
                (
                    "from inspect import getsource as source_of, isfunction\n"
                    "from datetime import datetime as Parent\n"
                    "class Reader(Parent):\n"
                    "    @staticmethod\n"
                    "    def getsource(owner):\n"
                    "        return source_of(owner)\n"
                    'assert "def" in source_of(isfunction)\n'
                    'assert "def" in Reader.getsource(isfunction)\n'
                ),
                1,
            ),
            (
                (
                    "from inspect import getsource as source_of, isfunction\n"
                    "import inspect\n"
                    "def factory():\n"
                    "    return inspect\n"
                    'assert "def" in source_of(isfunction)\n'
                    'assert "def" in factory().getsource(isfunction)\n'
                ),
                1,
            ),
            (
                (
                    "from inspect import getsource\n"
                    "def observed(getsource):\n"
                    '    assert getsource() == "runtime output"\n'
                ),
                0,
            ),
            (
                (
                    "from pathlib import Path\n"
                    'artifact = Path("generated.txt")\n'
                    'assert artifact.read_text(encoding="utf-8") '
                    '== "generated output"\n'
                ),
                0,
            ),
        ],
    )
    def test_native_scan_resolves_only_the_standard_library_source_owner(
        mod_workspace: Path,
        consumer: str,
        expected_findings: int,
    ) -> None:
        """Aliases retain the owner, lexical shadows and product bytes do not."""
        tests_dir = mod_workspace / "tests"
        tm.ok(u.Cli.ensure_dir(tests_dir))
        source = tests_dir / "consumer.py"
        tm.ok(u.Cli.atomic_write_text_file(source, consumer))
        u.Tests.git_bootstrap(mod_workspace, ("add", "tests"))
        report = tm.ok(FlextInfraModGateEngine.scan(mod_workspace, fix=False))
        findings = tuple(
            entry
            for entry in report.entries
            if entry.rule_id == "ban-test-source-introspection-assertion"
        )
        tm.that(len(findings), eq=expected_findings)
        tm.that(tuple(entry.actionable for entry in findings), lacks=True)
        authenticated = tuple(
            state.path for finding in findings for state in finding.binding_states
        )
        tm.that(
            authenticated,
            lacks=Path(flext_tests.__file__).resolve(),
        )
        if "from datetime import" in consumer:
            tm.that(authenticated, has=Path(dt.__file__).resolve())
        tm.that(source.read_text(encoding="utf-8"), eq=consumer)
