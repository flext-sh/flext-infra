"""Readonly namespace identities do not grant name-wide lint exemptions.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import gates
from tests import c, m, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraReadonlyNamespaceContract:
    """Validate exempt identities against real sources and checkers."""

    @staticmethod
    def _semantic_project(tmp_path: Path) -> Path:
        project = u.Tests.mk_project(
            tmp_path,
            "semantic-readonly",
            pyproject=(
                '[project]\nname = "semantic-readonly"\nversion = "0.0.0"\n'
                '[tool.ruff.lint]\nselect = ["N"]\n'
                '[tool.pyrefly]\nproject-includes = ["src/**/*.py"]\n'
                'search-path = ["src"]\npython-version = "3.13"\n'
            ),
        )
        package = project / "src" / "sample"
        package.mkdir(parents=True, exist_ok=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        (package / "contracts.py").write_text(
            "from __future__ import annotations\n"
            "from typing import Protocol, runtime_checkable\n\n"
            "class Contracts:\n"
            "    @runtime_checkable\n"
            "    class BranchSettings(Protocol):\n"
            "        @property\n"
            "        def encoding(self) -> str: ...\n\n"
            "    class Settings(Protocol):\n"
            "        @property\n"
            "        def Branch(self) -> Contracts.BranchSettings: ...\n",
            encoding="utf-8",
        )
        (package / "settings.py").write_text(
            "from typing import Annotated\n"
            "from pydantic import BaseModel, Field\n\n"
            "class RuntimeSettings(BaseModel):\n"
            "    class BranchSettings(BaseModel):\n"
            "        encoding: Annotated[str, Field(description='Encoding')]"
            " = 'utf-8'\n\n"
            "    Branch: BranchSettings = Field(default_factory=BranchSettings)\n",
            encoding="utf-8",
        )
        return project

    @staticmethod
    def test_real_checker_proves_producer_compatibility_and_readonly_assignment(
        tmp_path: Path,
    ) -> None:
        """A real checker proves structural return typing and prohibits writes."""
        project = TestsFlextInfraReadonlyNamespaceContract._semantic_project(tmp_path)
        proof = project / "src" / "sample" / "proof.py"
        proof.write_text(
            "from sample.contracts import Contracts\n"
            "from sample.settings import RuntimeSettings\n\n"
            "def compatible(value: RuntimeSettings) -> Contracts.BranchSettings:\n"
            "    return value.Branch\n",
            encoding="utf-8",
        )
        context = m.Infra.GateContext(
            repository_root=tmp_path, reports_dir=tmp_path / "reports"
        )
        checker = gates.FlextInfraPyreflyGate(tmp_path)
        accepted = checker.check_files((proof,), project, context)
        tm.that(accepted.result.passed, eq=True, msg=accepted.raw_output)
        proof.write_text(
            proof.read_text(encoding="utf-8") + "\ndef forbidden(\n"
            "    value: Contracts.Settings, branch: Contracts.BranchSettings\n"
            ") -> None:\n"
            "    value.Branch = branch\n",
            encoding="utf-8",
        )
        rejected = checker.check_files((proof,), project, context)
        tm.that(rejected.result.passed, eq=False)
        tm.that(
            any("read-only" in issue.message.lower() for issue in rejected.issues),
            eq=True,
        )

    @staticmethod
    def test_exempt_identities_authenticate_only_readonly_branch_getters(
        tmp_path: Path,
    ) -> None:
        """N802 is exempt only at an authenticated settings-protocol branch."""
        project = TestsFlextInfraReadonlyNamespaceContract._semantic_project(tmp_path)
        contracts = project / "src" / "sample" / "contracts.py"
        contracts.write_text(
            contracts.read_text(encoding="utf-8")
            + "\n        def Unrelated(self) -> str: ...\n",
            encoding="utf-8",
        )
        branch_row = 12
        unrelated_row = 14
        findings = tuple(
            m.Infra.Issue(
                file=str(contracts),
                line=row,
                column=13,
                code=c.Infra.RUFF_INVALID_FUNCTION_NAME,
                message="function name should be lowercase",
                severity=c.Infra.GateSeverity.ERROR.value,
            )
            for row in (branch_row, unrelated_row)
        )
        exempt = gates.FlextInfraReadonlyNamespace.exempt_identities(project, findings)
        tm.that(
            exempt,
            eq=frozenset({
                (
                    (contracts.resolve(), branch_row, 13),
                    c.Infra.RUFF_INVALID_FUNCTION_NAME,
                )
            }),
        )
