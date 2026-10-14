"""Public generated config lifecycle contract.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import cProfile
import sys
from pathlib import Path

import pytest
from jinja2 import Template

from flext_infra import infra
from flext_infra.codegen import FlextInfraMiseArtifactsFiles
from tests import c, tm, u
from tests.unit.codegen import test_codegen_ci_matrix
from tests.unit.codegen.conform_support import TestsFlextInfraConformSupport

pytestmark = pytest.mark.slow


class TestsFlextInfraCodegenConfigLifecycle:
    """Exercise the generated public config rather than inspect source spelling."""

    @staticmethod
    def test_check_consumes_completed_generation_without_rendering(
        infra_git_repo: Path,
    ) -> None:
        """Apply and no-op publication both support a read-only public observation."""
        root = infra_git_repo
        TestsFlextInfraConformSupport.seed_infra_package_tree(root)
        request = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.ENVRC,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        generation = cProfile.Profile()
        result = tm.ok(generation.runcall(infra.codegen_conform, request))
        tm.that(
            any(
                entry.code is Template.render.__code__
                for entry in generation.getstats()
            ),
            eq=True,
        )
        tm.that(result.plan is not None, eq=True)
        if result.plan is None:
            pytest.fail("generation did not return its actual plan")
        destinations = tuple(file.path for file in result.plan.files)
        no_op = tm.ok(infra.codegen_conform(request))
        tm.that(no_op.written_files, eq=())
        paths = (*destinations, root / c.Infra.CODEGEN_PUBLICATION_REPORT_RELATIVE_PATH)
        before = tuple(
            tm.ok(FlextInfraMiseArtifactsFiles.read_state(path, required=True))
            for path in paths
        )
        observation = cProfile.Profile()
        checked = tm.ok(
            observation.runcall(
                infra.codegen_conform,
                request.model_copy(update={"mode": c.Infra.CodegenConformMode.CHECK}),
            ),
        )
        tm.that(checked.plan, eq=None)
        tm.that(checked.verified_publication is not None, eq=True)
        tm.that(checked.written_files, eq=())
        tm.that(
            any(
                entry.code is Template.render.__code__
                for entry in observation.getstats()
            ),
            eq=False,
        )
        after = tuple(
            tm.ok(FlextInfraMiseArtifactsFiles.read_state(path, required=True))
            for path in paths
        )
        tm.that(after, eq=before)

    @staticmethod
    def test_generated_config_keeps_settings_independent(tmp_path: Path) -> None:
        """The real generated package loads typed YAML and freezes only config."""
        root = test_codegen_ci_matrix.TestsFlextInfraCodegenCiMatrix.render_project(
            tmp_path / "project",
        )
        script = """
import sys
from importlib.resources import files
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[1]) / "src"))
from flext_cli import FlextCliConfig, u
from flext_demo import FlextDemoConfig, config, m, settings

assert FlextDemoConfig.fetch_global() is config
assert FlextCliConfig.fetch_global() is not config
source = u.Cli.yaml_safe_load(Path(str(files("flext_demo") / "config/Demo.yaml")))
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
            ),
        )
        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=True,
            msg=process.stdout + process.stderr,
        )
        tm.that(process.stdout, has="generated config: frozen YAML")

    @staticmethod
    def test_initializer_no_op_publishes_observable_request_proof(
        tmp_path: Path,
    ) -> None:
        """A settled initializer batch retains scope identity on repeated APPLY."""
        root = test_codegen_ci_matrix.TestsFlextInfraCodegenCiMatrix.render_project(
            tmp_path / "project",
        )
        request = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.LAZY_INIT,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        tm.ok(infra.codegen_conform(request))
        tm.that(tm.ok(infra.codegen_conform(request)).written_files, eq=())
        report = root / c.Infra.CODEGEN_PUBLICATION_REPORT_RELATIVE_PATH
        before = tm.ok(FlextInfraMiseArtifactsFiles.read_state(report, required=True))
        checked = tm.ok(
            infra.codegen_conform(
                request.model_copy(update={"mode": c.Infra.CodegenConformMode.CHECK}),
            ),
        )
        tm.that(checked.verified_publication is not None, eq=True)
        tm.that(checked.written_files, eq=())
        tm.that(
            tm.ok(FlextInfraMiseArtifactsFiles.read_state(report, required=True)),
            eq=before,
        )
