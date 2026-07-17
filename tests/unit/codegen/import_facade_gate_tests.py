"""Tests for the parametrized import-facade validator gate.

Validates CLI dispatch, per-package allowlist parametrization (Case A),
and the universal deep-submodule (Case B) and bare-module (Case C) matchers
using real service instances against temporary workspaces (no mocks).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import main
from flext_infra.codegen.import_facade_gate import FlextInfraCodegenImportFacadeGate
from tests import t, u


class TestImportFacadeGateCLIDispatch:
    """CLI dispatch and argument parsing for import-facade-gate."""

    def test_dispatch_returns_int(self, tmp_path: Path) -> None:
        """main() dispatches import-facade-gate command to its handler."""
        result = main(["codegen", "import-facade-gate", "--workspace", str(tmp_path)])
        tm.that(result, is_=int)

    def test_json_format_exits_with_int(self, tmp_path: Path) -> None:
        """JSON mode returns an integer exit code."""
        result = main([
            "codegen",
            "import-facade-gate",
            "--workspace",
            str(tmp_path),
            "--output-format",
            "json",
        ])
        tm.that(result, is_=int)


class TestImportFacadeGateVerdict:
    """Verdict classification and real workspace execution."""

    def test_success_verdict_accepts_pass(self) -> None:
        """successful_verdict returns True for PASS."""
        tm.that(FlextInfraCodegenImportFacadeGate.successful_verdict("PASS"), eq=True)

    def test_success_verdict_rejects_fail(self) -> None:
        """successful_verdict returns False for FAIL."""
        tm.that(
            not FlextInfraCodegenImportFacadeGate.successful_verdict("FAIL"), eq=True
        )

    def test_empty_workspace_passes(self, tmp_path: Path) -> None:
        """A workspace with no flext imports produces a PASS report."""
        gate = FlextInfraCodegenImportFacadeGate(workspace_root=tmp_path)
        report_result = gate.build_report()
        tm.ok(report_result)
        tm.that(report_result.value, has="verdict")
        tm.that(u.Cli.json_pick_str(report_result.value, "verdict"), eq="PASS")


class TestImportFacadeGateCaseA:
    """Case A: per-package allowlist parametrization from the SSOT."""

    def test_unlisted_alias_flagged(self, tmp_path: Path) -> None:
        """Importing a name outside the package's real allowlist is flagged."""
        u.Tests.create_codegen_project(
            tmp_path=tmp_path,
            name="flext-demo",
            pkg_name="flext_demo",
            files={
                "api.py": (
                    "from __future__ import annotations\n\n"
                    "from flext_demo import not_a_facade_alias\n"
                ),
            },
        )
        gate = FlextInfraCodegenImportFacadeGate(workspace_root=tmp_path)
        report_result = gate.build_report()
        tm.ok(report_result)
        tm.that(u.Cli.json_pick_str(report_result.value, "verdict"), eq="FAIL")
        findings = u.Cli.json_deep_mapping_list(report_result.value, "findings")
        tm.that(findings, length_gte=1)

    def test_canonical_import_clean(self, tmp_path: Path) -> None:
        """Importing only canonical facade aliases produces no Case A finding."""
        u.Tests.create_codegen_project(
            tmp_path=tmp_path,
            name="flext-demo",
            pkg_name="flext_demo",
            files={
                "api.py": (
                    "from __future__ import annotations\n\n"
                    "from flext_demo import c, t\n"
                ),
            },
        )
        gate = FlextInfraCodegenImportFacadeGate(workspace_root=tmp_path)
        report_result = gate.build_report()
        tm.ok(report_result)
        tm.that(u.Cli.json_pick_str(report_result.value, "verdict"), eq="PASS")

    def test_aliased_import_flagged(self, tmp_path: Path) -> None:
        """Any ``as`` alias of a flext import is flagged regardless of name."""
        u.Tests.create_codegen_project(
            tmp_path=tmp_path,
            name="flext-demo",
            pkg_name="flext_demo",
            files={
                "api.py": (
                    "from __future__ import annotations\n\n"
                    "from flext_demo import c as constants\n"
                ),
            },
        )
        gate = FlextInfraCodegenImportFacadeGate(workspace_root=tmp_path)
        report_result = gate.build_report()
        tm.ok(report_result)
        tm.that(u.Cli.json_pick_str(report_result.value, "verdict"), eq="FAIL")


class TestImportFacadeGateUniversalCases:
    """Cases B and C: universal deep-submodule and bare-module matchers."""

    def test_deep_submodule_import_flagged(self, tmp_path: Path) -> None:
        """Case B: importing from a deep submodule path is always flagged."""
        u.Tests.create_codegen_project(
            tmp_path=tmp_path,
            name="flext-demo",
            pkg_name="flext_demo",
            files={
                "api.py": (
                    "from __future__ import annotations\n\n"
                    "from flext_demo.services import handler\n"
                ),
            },
        )
        gate = FlextInfraCodegenImportFacadeGate(workspace_root=tmp_path)
        report_result = gate.build_report()
        tm.ok(report_result)
        tm.that(u.Cli.json_pick_str(report_result.value, "verdict"), eq="FAIL")

    def test_bare_module_import_flagged(self, tmp_path: Path) -> None:
        """Case C: a bare ``import flext_<ns>`` is always flagged."""
        u.Tests.create_codegen_project(
            tmp_path=tmp_path,
            name="flext-demo",
            pkg_name="flext_demo",
            files={
                "api.py": (
                    "from __future__ import annotations\n\nimport flext_demo\n"
                ),
            },
        )
        gate = FlextInfraCodegenImportFacadeGate(workspace_root=tmp_path)
        report_result = gate.build_report()
        tm.ok(report_result)
        tm.that(u.Cli.json_pick_str(report_result.value, "verdict"), eq="FAIL")


__all__: t.StrSequence = []
