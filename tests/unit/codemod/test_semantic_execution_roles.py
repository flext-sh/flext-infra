"""Owned code retains native process and isolated-execution applicability.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from flext_infra import c, m, t, u
from flext_infra.codemod import FlextInfraModGateEngine
from tests import c, tm


class TestsSemanticExecutionRoles:
    """Native role evidence, not entrypoint spelling, controls applicability."""

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("surface", ["src", "tests", "scripts", "examples"])
    def test_all_owned_surfaces_use_the_same_native_rule_contracts(
        mod_workspace: Path, surface: str
    ) -> None:
        """Real reads/imports block while homonyms and ordinary strings stay intact."""
        namespace = u.Infra.project_package_name(mod_workspace)
        package = (
            mod_workspace / c.Infra.DEFAULT_SRC_DIR / namespace
            if surface == c.Infra.DEFAULT_SRC_DIR
            else mod_workspace / surface
        )
        package.mkdir(parents=True, exist_ok=True)
        (package / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        contents = {
            "application.py": "import os as env\nvalue = env.getenv('ROLE_PROBE')\n",
            "hook_client.py": (
                "from os import getenv as read\nvalue = read('ROLE_PROBE')\n"
            ),
            "bootstrap.py": "import os\nvalue = os.environ['ROLE_PROBE']\n",
            "processes.py": "import subprocess\n",
            "primitive_shadow.py": (
                "from flext_cli import u\n"
                "process = u.Cli.process_start\n"
                "process = None\n"
                "import subprocess\n"
            ),
            "shadow.py": (
                "import os\n"
                "class Other:\n"
                "    @staticmethod\n"
                "    def getenv(key):\n"
                "        return key\n"
                "os = Other\n"
                "value = os.getenv('ROLE_PROBE')\n"
            ),
            "ordinary.py": (
                "message = \"os.getenv('ROLE_PROBE'); import subprocess\"\n"
            ),
        }
        for relative, text in contents.items():
            (package / relative).write_text(text, encoding=c.DEFAULT_ENCODING)
        report = tm.ok(
            FlextInfraModGateEngine.scan(
                mod_workspace,
                fix=False,
                selection=(
                    "ban-ambient-environ-read",
                    "ban-subprocess-outside-run-owner",
                ),
                source_files=tuple(package / name for name in contents),
            ),
        )
        tm.that(
            {
                (
                    u.Infra.codemod_source_path(mod_workspace, entry.file),
                    entry.rule_id,
                )
                for entry in report.entries
            },
            eq={
                ((package / name).resolve(), "ban-ambient-environ-read")
                for name in ("application.py", "hook_client.py", "bootstrap.py")
            }
            | {
                ((package / name).resolve(), "ban-subprocess-outside-run-owner")
                for name in ("processes.py", "primitive_shadow.py")
            },
        )
        for relative, text in contents.items():
            tm.that(
                (package / relative).read_text(encoding=c.DEFAULT_ENCODING), eq=text
            )

    @staticmethod
    @pytest.mark.parametrize(
        "flags", [("-I",), ("-S",), ("-I", "-S"), ("-I", "-S", "-P")]
    )
    def test_isolated_role_does_not_accept_caller_interpreter_policy(
        flags: t.StrSequence,
    ) -> None:
        """Flags are derived from the shared role, never independently promised."""
        with pytest.raises(ValueError, match="python_flags"):
            m.Cli.PythonScriptExecution.model_validate_json(
                json.dumps({
                    "module": "role_probe.entrypoint",
                    "role": "isolated-stdlib",
                    "python_flags": flags,
                })
            )

    @staticmethod
    def test_isolated_role_derives_the_native_interpreter_contract() -> None:
        """The actual producer gets both Python isolation/no-site protocol flags."""
        execution = m.Cli.PythonScriptExecution(
            module="role_probe.entrypoint", role="isolated-stdlib"
        )
        tm.ok({"-I", "-S"} <= set(execution.python_flags))
