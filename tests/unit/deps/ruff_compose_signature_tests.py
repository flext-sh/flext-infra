"""Canonical Ruff modernization retires suppression tables without narrowing rules.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra import c, config, m, t
from flext_infra.deps import FlextInfraEnsureRuffConfigPhase
from flext_infra.gates import FlextInfraRuffLintGate
from tests import tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRuffProjectPolicy:
    """One native policy replaces both fresh and formerly suppressed inputs."""

    @staticmethod
    def test_modernization_retires_all_rule_suppression_tables(tmp_path: Path) -> None:
        """Retirement preserves full declared rules and converges without exemptions."""
        payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(
            u.Tests.toml_payload(
                '[project]\nname = "retired-exemptions"\n'
                '[tool.ruff.lint]\nignore = ["F401"]\nextend-ignore = ["F821"]\n'
                '[tool.ruff.lint.per-file-ignores]\n"tests/**" = ["ALL"]\n'
                '[tool.ruff.lint.extend-per-file-ignores]\n"scripts/**" = ["ALL"]\n',
            ),
        )
        phase = FlextInfraEnsureRuffConfigPhase(config.Infra.tooling)
        phase.apply_payload(
            payload,
            path=tmp_path / c.PYPROJECT_FILENAME,
            analysis_exclusions=(),
        )
        lint = tm.not_none(u.Cli.toml_mapping_path(payload, ("tool", "ruff", "lint")))
        for retired in (
            "ignore",
            "extend-ignore",
            "per-file-ignores",
            "extend-per-file-ignores",
        ):
            tm.that(lint, lacks=retired)
        tm.that(lint["select"], eq=sorted(config.Infra.tooling.tools.ruff.lint.select))
        tm.that(
            phase.apply_payload(
                payload,
                path=tmp_path / c.PYPROJECT_FILENAME,
                analysis_exclusions=(),
            ),
            empty=True,
        )

    @staticmethod
    @pytest.mark.parametrize("surface", config.Infra.tooling.tools.ruff.src)
    def test_native_selected_scope_has_no_hidden_findings(
        tmp_path: Path,
        surface: str,
    ) -> None:
        """The native owner sees formerly masked findings on every code root."""
        project = u.Tests.mk_project(tmp_path, "native-policy")
        selected = project / surface / "selected.py"
        selected.parent.mkdir(parents=True, exist_ok=True)
        selected.write_text("import os\n", encoding="utf-8")
        payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(
            u.Tests.toml_payload(
                (project / c.PYPROJECT_FILENAME).read_text(encoding="utf-8"),
            ),
        )
        FlextInfraEnsureRuffConfigPhase(config.Infra.tooling).apply_payload(
            payload,
            path=project / c.PYPROJECT_FILENAME,
            analysis_exclusions=(),
        )
        (project / c.PYPROJECT_FILENAME).write_text(
            u.Cli.toml_dumps(u.Cli.toml_document_from_mapping(payload)),
            encoding="utf-8",
        )
        gate = FlextInfraRuffLintGate(tmp_path)
        context = m.Infra.GateContext(
            repository_root=tmp_path,
            reports_dir=tmp_path / "reports",
        )
        execution = gate.check_files((selected,), project, context)
        tm.that(execution.result.passed, eq=False)
        tm.that(execution.outcome, eq=c.Infra.ToolOutcome.FINDINGS)
        tm.that([issue.code for issue in execution.issues], has="unused-import")
        tm.that(
            all(
                issue.severity == c.Infra.GateSeverity.ERROR.value
                for issue in execution.issues
            ),
            eq=True,
        )
        tm.that(selected.read_text(encoding="utf-8"), eq="import os\n")
