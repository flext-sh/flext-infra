"""Exercise the dependency-declaration gate through the public registry.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import sys
import venv
from pathlib import Path

import pytest

from flext_infra import c, m, u
from flext_infra.check import FlextInfraGateRegistry
from tests import tm


class TestsFlextInfraDepsGate:
    """Undeclared imports fail at check time, never deep inside generation."""

    @staticmethod
    def _project(tmp_path: Path, dependencies: str, imports: str) -> Path:
        root = tmp_path / "repository"
        (root / "src").mkdir(parents=True)
        (root / "pyproject.toml").write_text(
            '[project]\nname = "fixture"\nversion = "0.1.0"\n'
            f"dependencies = [{dependencies}]\n"
            '[tool.deptry]\nknown_first_party = ["fixturepkg"]\n',
            encoding="utf-8",
        )
        (root / "src" / "fixturepkg.py").write_text(imports, encoding="utf-8")
        return root

    @staticmethod
    def test_undeclared_import_blocks_at_check_time(tmp_path: Path) -> None:
        """An import the dependency list never declares is a loud finding."""
        root = TestsFlextInfraDepsGate._project(
            tmp_path,
            '"pyyaml>=6"',
            "import requests\n\n\ndef handler() -> int:\n"
            "    return len(requests.get)\n",
        )
        gate = tm.not_none(
            FlextInfraGateRegistry.default().create(c.Infra.DEPS, root),
        )
        result = gate.check(
            root,
            m.Infra.GateContext(repository_root=root, reports_dir=tmp_path / "reports"),
        )

        tm.that(result.result.passed, eq=False)
        tm.that(result.outcome, eq=c.Infra.ToolOutcome.FINDINGS)
        assert result.issues, "undeclared import must produce an issue"
        tm.that(
            result.issues[0].code.startswith(f"{c.Infra.DEPS}-"),
            eq=True,
        )

    @staticmethod
    def test_declared_imports_pass_the_gate(tmp_path: Path) -> None:
        """A checkout whose imports the dependency list declares stays green."""
        root = TestsFlextInfraDepsGate._project(
            tmp_path,
            '"pyyaml>=6", "requests>=2"',
            "import requests\nimport yaml\n\n\ndef handler() -> str:\n"
            "    return yaml.safe_dump(requests.models.__name__)\n",
        )
        gate = tm.not_none(
            FlextInfraGateRegistry.default().create(c.Infra.DEPS, root),
        )
        result = gate.check(
            root,
            m.Infra.GateContext(repository_root=root, reports_dir=tmp_path / "reports"),
        )

        tm.that(result.result.passed, eq=True)
        tm.that(result.outcome, eq=c.Infra.ToolOutcome.CLEAN)
        tm.that(result.issues, eq=())
        tm.that((root / ".reports").exists(), eq=False)

    @staticmethod
    def test_invalid_config_is_native_execution_error(tmp_path: Path) -> None:
        """The real scanner's configuration failure is not an empty findings run."""
        root = TestsFlextInfraDepsGate._project(tmp_path, "", "import os\n")
        (root / c.PYPROJECT_FILENAME).write_text("[project", encoding="utf-8")
        gate = tm.not_none(FlextInfraGateRegistry.default().create(c.Infra.DEPS, root))
        result = gate.check(
            root,
            m.Infra.GateContext(repository_root=root, reports_dir=tmp_path),
        )
        tm.that(result.outcome, eq=c.Infra.ToolOutcome.ERROR)
        tm.that(result.result.passed, eq=False)
        assert result.issues

    @staticmethod
    def test_missing_deptry_binary_fails_loud(
        tmp_path: Path,
    ) -> None:
        """A real interpreter without the console script emits native ERROR."""
        root = TestsFlextInfraDepsGate._project(tmp_path, '"pyyaml>=6"', "import os\n")
        environment = tmp_path / "runtime"
        venv.EnvBuilder(system_site_packages=True, symlinks=True).create(environment)
        executed = u.Cli.run_raw(
            (
                str(environment / "bin" / "python"),
                "-c",
                (
                    "from pathlib import Path; "
                    "from flext_infra import c, m; "
                    "from flext_infra.check import FlextInfraGateRegistry; "
                    f"root = Path({str(root)!r}); "
                    "gate = FlextInfraGateRegistry.default()."
                    "create(c.Infra.DEPS, root); "
                    "print(gate.check(root, m.Infra.GateContext("
                    "repository_root=root, reports_dir=root)).model_dump_json("
                    "round_trip=True))"
                ),
            ),
            cwd=root,
            options=m.Cli.ProcessOptions(
                env={
                    "PYTHONPATH": os.pathsep.join(
                        str(Path(path).absolute()) for path in sys.path
                    ),
                },
            ),
        ).unwrap()
        tm.that(u.Cli.process_succeeded(executed.outcome), eq=True)
        result = m.Infra.GateExecution.model_validate_json(executed.stdout)
        tm.that(result.outcome, eq=c.Infra.ToolOutcome.ERROR)
        tm.that(result.result.passed, eq=False)
        assert result.issues
        assert c.Infra.DEPTRY in result.issues[0].message

    @staticmethod
    def test_missing_config_does_not_consume_stale_report(tmp_path: Path) -> None:
        """A stale clean report cannot attest a command with missing inputs."""
        root = TestsFlextInfraDepsGate._project(tmp_path, "", "import os\n")
        stale = root / ".reports" / "deptry-check.json"
        stale.parent.mkdir()
        stale.write_text("[]", encoding="utf-8")
        (root / c.PYPROJECT_FILENAME).unlink()
        gate = tm.not_none(
            FlextInfraGateRegistry.default().create(c.Infra.DEPS, root),
        )
        result = gate.check(
            root,
            m.Infra.GateContext(repository_root=root, reports_dir=tmp_path),
        )
        tm.that(result.outcome, eq=c.Infra.ToolOutcome.ERROR)
        tm.that(result.result.passed, eq=False)
        assert result.issues
        tm.that(stale.read_text(encoding="utf-8"), eq="[]")

    @staticmethod
    @pytest.mark.parametrize(
        "payload",
        [
            "{}",
            "null",
            "[null]",
            "[{}]",
            "[",
            "[1]",
            '[{"error":{},"module":"x","location":{}}]',
            (
                '[{"error":{"code":"DEP001","message":"missing"},"module":"x",'
                '"location":{"file":"src/x.py","line":"1","column":0}}]'
            ),
        ],
    )
    def test_native_report_rejects_unrecognized_payload(
        tmp_path: Path,
        payload: str,
    ) -> None:
        """The public owned JSON boundary rejects malformed or incomplete records."""
        report = tmp_path / "deptry.json"
        report.write_text(payload, encoding="utf-8")
        with pytest.raises(ValueError, match="validation error"):
            m.Infra.DeptryNativeReport.model_validate_json(
                report.read_bytes(),
                strict=True,
            )

    @staticmethod
    def test_native_report_retains_dependency_null_locations(tmp_path: Path) -> None:
        """The external protocol permits null positions, not missing fields."""
        report = tmp_path / "deptry.json"
        report.write_text(
            '[{"error":{"code":"DEP002","message":"dependency is unused"},'
            '"module":"unused","location":{"file":"pyproject.toml",'
            '"line":null,"column":null}}]',
            encoding="utf-8",
        )
        parsed = m.Infra.DeptryNativeReport.model_validate_json(
            report.read_bytes(),
            strict=True,
        )
        tm.that(parsed.root[0].error.code, eq="DEP002")
        tm.that(parsed.root[0].location.line, eq=None)
