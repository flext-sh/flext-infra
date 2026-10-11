"""Public generated config lifecycle contract.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from flext_infra import config
from tests import tm, u
from tests.unit.codegen import test_codegen_ci_matrix

pytestmark = pytest.mark.slow


class TestsFlextInfraCodegenConfigLifecycle:
    """Exercise the generated public config rather than inspect source spelling."""

    @staticmethod
    def test_generated_config_keeps_settings_independent(tmp_path: Path) -> None:
        """The real generated package loads typed YAML and freezes only config."""
        root = test_codegen_ci_matrix.TestsFlextInfraCodegenCiMatrix.render_project(
            tmp_path / "project",
        )
        script = """
import sys
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[1]) / "src"))
from flext_cli import FlextCliConfig, u
from flext_demo import FlextDemoConfig, config, m, settings

assert FlextDemoConfig.fetch_global() is config
assert FlextCliConfig.fetch_global() is not config
source = u.Cli.yaml_safe_load(Path(sys.argv[1]) / "config/Demo.yaml")
assert source.success, source.error
assert config.Demo.model_dump() == source.value["Demo"]
before = config.model_dump()
try:
    config.Demo = config.Demo
except m.ValidationError as error:
    assert all(item["type"] == "frozen_instance" for item in error.errors())
else:
    raise AssertionError("Generated config is mutable")
adjusted = settings.clone(debug=not settings.debug)
assert adjusted.debug != settings.debug
assert config.model_dump() == before
print("generated config: frozen YAML, subclass identity, independent settings")
"""
        process = tm.ok(
            u.Cli.run_raw(
                [sys.executable, "-c", script, str(root)],
                timeout=config.Infra.tooling.tools.pytest.case_timeout_seconds,
            ),
        )
        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=True,
            msg=process.stdout + process.stderr,
        )
        tm.that(process.stdout, has="generated config: frozen YAML")
