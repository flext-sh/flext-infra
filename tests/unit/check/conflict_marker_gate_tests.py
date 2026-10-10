"""Exercise conflict detection through the public registry and real Git files.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import FlextInfraGateRegistry, c, m
from tests import u


class TestsFlextInfraConflictMarkerGate:
    """Unpublished files, source failures and native severities remain blocking."""

    @staticmethod
    def _root(tmp_path: Path) -> Path:
        root = tmp_path / "repository"
        root.mkdir()
        (root / "README.md").write_text("# Native repository\n", encoding="utf-8")
        u.Tests.initialize_git_repo(root)
        return root

    @staticmethod
    @pytest.mark.parametrize("control", c.Infra.MERGE_CONFLICT_CONTROLS)
    def test_untracked_control_line_blocks(
        tmp_path: Path,
        control: tuple[str, str],
    ) -> None:
        """The real index/status inventory includes a new unpublished file."""
        root = TestsFlextInfraConflictMarkerGate._root(tmp_path)
        kind, token = control
        source = root / "unpublished.txt"
        content = f"ordinary source\n{token} native conflict\n"
        source.write_text(content, encoding="utf-8")
        gate = tm.not_none(
            FlextInfraGateRegistry.default().create(c.Infra.CONFLICT_MARKERS, root)
        )

        result = gate.check(
            root, m.Infra.GateContext(repository_root=root, reports_dir=root)
        )

        tm.that(result.result.passed, eq=False)
        tm.that(result.issues[0].file, eq=str(source))
        tm.that(result.issues[0].line, eq=2)
        tm.that(result.issues[0].code, eq=f"{c.Infra.CONFLICT_MARKERS}-{kind}")
        tm.that(source.read_text(encoding="utf-8"), eq=content)

    @staticmethod
    def test_binary_and_literal_symlink_are_not_followed(tmp_path: Path) -> None:
        """The scanner reads bytes and never follows a source link outside Git."""
        root = TestsFlextInfraConflictMarkerGate._root(tmp_path)
        (root / "binary.bin").write_bytes(b"\x89PNG\x00\xff\nbinary payload\n")
        outside = tmp_path / "outside.txt"
        token = c.Infra.MERGE_CONFLICT_CONTROLS[0][1]
        outside.write_text(f"{token} outside source\n", encoding="utf-8")
        (root / "literal-link").symlink_to(outside)
        gate = tm.not_none(
            FlextInfraGateRegistry.default().create(c.Infra.CONFLICT_MARKERS, root)
        )

        result = gate.check(
            root, m.Infra.GateContext(repository_root=root, reports_dir=root)
        )

        tm.that(result.result.passed, eq=True)
        tm.that(result.issues, eq=())
        tm.that(result.raw_output, has="checked=")

    @staticmethod
    def test_scoped_path_cannot_escape_the_owner(tmp_path: Path) -> None:
        """Parent traversal is rejected before the foreign file is read."""
        root = TestsFlextInfraConflictMarkerGate._root(tmp_path)
        outside = tmp_path / "outside.txt"
        outside.write_text("foreign content\n", encoding="utf-8")
        gate = tm.not_none(
            FlextInfraGateRegistry.default().create(c.Infra.CONFLICT_MARKERS, root)
        )
        with pytest.raises(ValueError, match="outside the project"):
            gate.check_files(
                (root / ".." / outside.name,),
                root,
                m.Infra.GateContext(repository_root=root, reports_dir=root),
            )

    @staticmethod
    @pytest.mark.parametrize("severity", list(c.Infra.GateSeverity))
    def test_no_finding_severity_becomes_approval(
        severity: c.Infra.GateSeverity,
    ) -> None:
        """Warning and note classifications preserve their blocking findings."""
        issue = m.Infra.Issue(
            file="native.txt",
            line=1,
            column=1,
            code="native-finding",
            message="Native checker finding",
            severity=severity.value,
        )
        tm.that(u.Infra.blocking_gate_findings((issue,)), eq=(issue,))
