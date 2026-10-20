"""Native Pyright proves exported contracts and rejects private consumers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra.deps import FlextInfraEnsurePyrightConfigPhase
from flext_infra.gates import FlextInfraPyrightGate
from tests import m, t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraPyrightPublicContract:
    """Exercise the configured semantic owner with real source and type stubs."""

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("selected", ["first", "second", "workspace"])
    def test_homonymous_test_facades_resolve_in_their_own_project(
        tmp_path: Path,
        tool_config_document: m.Infra.ToolConfigDocument,
        selected: str,
    ) -> None:
        """Identical facade imports resolve distinct inherited member contracts."""
        rules = tool_config_document.tools.pyright.path_rules
        projects = (
            ("first", "int", "7"),
            ("second", "str", "'second'"),
        )
        for name, annotation, value in projects:
            root = tmp_path / name
            tests = root / "tests"
            tests.mkdir(parents=True)
            (root / rules.source_dir).mkdir(parents=True, exist_ok=True)
            (tests / "__init__.py").write_text(
                "from typing import TYPE_CHECKING\n"
                "if TYPE_CHECKING:\n"
                "    from tests.constants import c as c\n",
                encoding="utf-8",
            )
            (tests / "constants.py").write_text(
                "from typing import ClassVar\n"
                "class Rules:\n"
                f"    RULES_CATALOG_BASIC: ClassVar[{annotation}] = {value}\n"
                "class Constants:\n"
                "    class Tests(Rules):\n"
                "        pass\n"
                "c = Constants\n",
                encoding="utf-8",
            )
            (tests / "consumer.py").write_text(
                "from tests import c\n"
                f"def catalog() -> {annotation}:\n"
                "    return c.Tests.RULES_CATALOG_BASIC\n",
                encoding="utf-8",
            )
            payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python({})
            payload["project"] = {"name": name, "version": "0.1.0"}
            FlextInfraEnsurePyrightConfigPhase(tool_config_document).apply_payload(
                payload,
                context=m.Infra.PyprojectAnalyzerContext(
                    is_root=False,
                    project_dir=root,
                    declared_python_dirs=(rules.source_dir, "tests"),
                    declared_python_dirs_are_complete=True,
                ),
            )
            (root / "pyproject.toml").write_text(
                u.Cli.toml_dumps(u.Cli.toml_document_from_mapping(payload)),
                encoding="utf-8",
            )
        project = tmp_path / selected
        if selected == "workspace":
            project = tmp_path
            u.Tests.declare_workspace_projects(tmp_path, ("first", "second"))
            u.Tests.write_project_beads_config(tmp_path, selected)
            payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python({})
            payload["project"] = {"name": selected, "version": "0.1.0"}
            FlextInfraEnsurePyrightConfigPhase(tool_config_document).apply_payload(
                payload,
                context=m.Infra.PyprojectAnalyzerContext(
                    is_root=True, repository_root=project
                ),
            )
            (project / "pyproject.toml").write_text(
                u.Cli.toml_dumps(u.Cli.toml_document_from_mapping(payload)),
                encoding="utf-8",
            )
        context = m.Infra.GateContext(
            repository_root=project,
            reports_dir=project / ".reports",
        )
        result = FlextInfraPyrightGate(project).check(project, context)

        tm.that(result.result.passed, eq=True, msg=result.raw_output)
        tm.that(result.issues, eq=(), msg=result.raw_output)

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize(
        ("consumer", "private"),
        [
            (
                (
                    "import os as operating_system\n"
                    "def exit_child() -> None:\n"
                    "    operating_system._exit(0)\n"
                ),
                False,
            ),
            (
                (
                    "from owner import Owner\n"
                    "def observe(value: Owner) -> int:\n"
                    "    return value._secret\n"
                ),
                True,
            ),
            (
                (
                    "from owner import Owner\n"
                    "def exit_child(os: Owner) -> None:\n"
                    "    os._exit(0)\n"
                ),
                True,
            ),
            (
                (
                    "from owner import _public\n"
                    "def observe() -> int:\n"
                    "    return _public()\n"
                ),
                False,
            ),
        ],
    )
    def test_publicness_uses_resolved_owner(
        tmp_path: Path,
        tool_config_document: m.Infra.ToolConfigDocument,
        consumer: str,
        *,
        private: bool,
    ) -> None:
        """Aliases and explicit exports stay public; shadowed receivers do not."""
        rules = tool_config_document.tools.pyright.path_rules
        roots = tuple(dict.fromkeys((*rules.env_dirs, rules.project_root)))
        for index, root in enumerate(roots):
            directory = tmp_path / root / "fixtures"
            directory.mkdir(parents=True, exist_ok=True)
            (directory / f"consumer_{index}.py").write_text(consumer, encoding="utf-8")
        (tmp_path / rules.source_dir / "owner.py").write_text(
            '__all__ = ["Owner", "_public"]\n'
            "class Owner:\n"
            "    _secret: int = 1\n"
            "    def _exit(self, code: int) -> None:\n"
            "        self._secret = code\n"
            "def _public() -> int:\n"
            "    return 1\n",
            encoding="utf-8",
        )
        payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python({})
        FlextInfraEnsurePyrightConfigPhase(tool_config_document).apply_payload(
            payload,
            context=m.Infra.PyprojectAnalyzerContext(
                is_root=False,
                project_dir=tmp_path,
                declared_python_dirs=roots,
                declared_python_dirs_are_complete=True,
            ),
        )
        (tmp_path / "pyproject.toml").write_text(
            u.Cli.toml_dumps(u.Cli.toml_document_from_mapping(payload)),
            encoding="utf-8",
        )
        context = m.Infra.GateContext(
            repository_root=tmp_path,
            reports_dir=tmp_path / ".reports",
        )
        result = FlextInfraPyrightGate(tmp_path).check(tmp_path, context)

        private_issues = tuple(
            issue for issue in result.issues if issue.code == "reportPrivateUsage"
        )
        assert bool(private_issues) is private
        assert result.result.passed is not private, result.raw_output
        if private:
            tm.that(len(private_issues), eq=len(roots), msg=result.raw_output)
