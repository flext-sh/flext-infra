"""Every tier publishes its single class: suites follow the same rule as src.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import FlextInfraCli
from tests import c, m, tm, u


class TestsFlextInfraSourceExportScope:
    """Exercise both export verdicts through the real public AST command."""

    @staticmethod
    @pytest.mark.parametrize("exported", [False, True])
    def test_suite_export_policy_preserves_source_publication(
        mod_workspace: Path,
        capsys: pytest.CaptureFixture[str],
        *,
        exported: bool,
    ) -> None:
        """A suite module, like a source owner, must declare its class in __all__."""
        stem = u.derive_class_stem(mod_workspace.name.replace("_", "-"))
        suite = "tests/unit/scope_tests.py"
        suite_name = f"Tests{stem}Scope"
        sources = {
            "sample.py": f'class {stem}Sample:\n    """Importable source owner."""\n',
            suite: (
                f'class {suite_name}:\n    """Collected suite namespace."""\n'
                + (f'\n__all__ = ["{suite_name}"]\n' if exported else "")
            ),
        }
        for relative, text in sources.items():
            path = mod_workspace / relative
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, text))
        rules = ("declare-single-class-export",)
        exit_code = FlextInfraCli.infra_main([
            "refactor",
            "ast",
            "--repository-root",
            str(mod_workspace),
            "--rules",
            ",".join(rules),
        ])
        console = capsys.readouterr()
        report = m.Infra.ModScanEvidence.model_validate_json(
            (mod_workspace / c.Infra.MOD_SCAN_REPORT_RELATIVE_PATH).read_bytes(),
        )
        tm.that(exit_code, ne=0, msg=console.out + console.err)
        expected = {("declare-single-class-export", "sample.py")}
        if not exported:
            expected.add(("declare-single-class-export", suite))
        tm.that(
            {(entry.rule_id, entry.file.as_posix()) for entry in report.entries},
            eq=expected,
        )
