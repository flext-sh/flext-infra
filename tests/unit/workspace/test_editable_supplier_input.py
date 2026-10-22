"""Cold settings-input election for editable suppliers and hosted runners.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from tests import m, tm, u


class TestsFlextInfraEditableSupplierInput:
    """Hosted execution ignores host-only paths before native path validation."""

    @staticmethod
    @pytest.mark.parametrize("supplier", ["missing", "relative"])
    def test_hosted_cold_import_ignores_host_supplier(
        tmp_path: Path, supplier: str
    ) -> None:
        """A runner never depends on an inherited local workspace directory."""
        selected = str(tmp_path / "missing") if supplier == "missing" else "relative"
        output = tm.ok(
            u.Cli.run_raw(
                [
                    sys.executable,
                    "-I",
                    "-c",
                    (
                        "from flext_infra import settings; "
                        "print(settings.Infra.editable_supplier_root is None)"
                    ),
                ],
                cwd=tmp_path,
                options=m.Cli.ProcessOptions(
                    env={
                        "GITHUB_ACTIONS": "true",
                        "FLEXT_INFRA_EDITABLE_SUPPLIER_ROOT": selected,
                        "HOME": str(tmp_path),
                        "XDG_CONFIG_HOME": str(tmp_path / "xdg"),
                    },
                    inherit_environment=False,
                ),
            )
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)
        tm.that(output.stdout.strip(), eq="True")
        tm.that(output.stderr, eq="")

    @staticmethod
    def test_local_cold_import_refuses_relative_supplier(tmp_path: Path) -> None:
        """Ignoring the host path is restricted to the actual hosted mode."""
        output = tm.ok(
            u.Cli.run_raw(
                [sys.executable, "-I", "-c", "from flext_infra import settings"],
                cwd=tmp_path,
                options=m.Cli.ProcessOptions(
                    env={
                        "GITHUB_ACTIONS": "false",
                        "FLEXT_INFRA_EDITABLE_SUPPLIER_ROOT": "relative",
                        "HOME": str(tmp_path),
                        "XDG_CONFIG_HOME": str(tmp_path / "xdg"),
                    },
                    inherit_environment=False,
                ),
            )
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=False)
        tm.that(output.stderr, has="editable supplier root must be an absolute path")
