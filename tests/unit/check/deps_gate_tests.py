"""Exercise the dependency-declaration gate through the public registry.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from flext_infra import c, m
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
            m.Infra.GateContext(repository_root=root, reports_dir=root),
        )

        tm.that(result.result.passed, eq=False)
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
            m.Infra.GateContext(repository_root=root, reports_dir=root),
        )

        tm.that(result.result.passed, eq=True)

    @staticmethod
    def test_missing_deptry_binary_fails_loud(
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """An environment without deptry is a loud error, never a silent pass."""
        root = TestsFlextInfraDepsGate._project(tmp_path, '"pyyaml>=6"', "import os\n")
        empty_bin = tmp_path / "venv-bin"
        empty_bin.mkdir()
        monkeypatch.setattr(sys, "executable", str(empty_bin / "python"))
        gate = tm.not_none(
            FlextInfraGateRegistry.default().create(c.Infra.DEPS, root),
        )
        with pytest.raises(FileNotFoundError, match="deptry"):
            gate.check(
                root,
                m.Infra.GateContext(repository_root=root, reports_dir=root),
            )
