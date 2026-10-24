"""Render-provenance contracts: every emitted artifact names its generator.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib.metadata
import shutil
from pathlib import Path
from shlex import quote

import pytest

from flext_infra import config
from flext_infra.codegen import FlextInfraCodegenConform
from tests import c, m, t, tm, u


class TestsFlextInfraRenderProvenance:
    """Rendered Make controls execute the installed, metadata-owned namespace."""

    @staticmethod
    @pytest.mark.parametrize("profile", list(c.Infra.MakeProfile))
    @pytest.mark.parametrize("ci_context", [False, True])
    def test_controller_ignores_undeclared_and_caller_sources(
        tmp_path: Path,
        resolved_make_templates: t.MappingKV[c.Infra.MakeProfile, Path],
        profile: c.Infra.MakeProfile,
        *,
        ci_context: bool,
    ) -> None:
        """Real provisioned consumers reject both source-shadowing entry points."""
        project = resolved_make_templates[profile]
        tm.ok(
            FlextInfraCodegenConform.execute_request(
                m.Infra.CodegenConformRequest(
                    root=project,
                    what=c.Infra.CodegenConformSurface.MAKEFILE,
                    mode=c.Infra.CodegenConformMode.APPLY,
                ),
                execution_context=None,
            )
        )
        tm.that(
            (project / c.Infra.MAKEFILE_FILENAME).read_text(),
            has=f"{c.Infra.RENDERED_BY_MARKER}{importlib.metadata.version(config.Infra.name)}",
        )
        override = tmp_path / "caller-source"
        marker = tmp_path / "undeclared-controller-executed"
        nested = project / "flext-infra"
        tm.fail(nested.exists())
        for source in (nested / "src", override):
            package = source / "flext_infra"
            package.mkdir(parents=True, exist_ok=True)
            (package / c.Infra.INIT_PY).write_text(
                f"from pathlib import Path\nPath({str(marker)!r}).touch()\n"
                "raise RuntimeError('undeclared controller executed')\n",
                encoding=c.DEFAULT_ENCODING,
            )
        custom = project / c.Infra.CUSTOM_MAKE_FILENAME
        original = custom.read_bytes()
        probe = (
            "import pathlib,flext_infra; "
            "from importlib.resources import files; "
            "from flext_infra import FlextInfraConfig,c,u; "
            "p=pathlib.Path(flext_infra.__file__).resolve(); "
            "print('controller-file='+str(p)); "
            "resource=files(flext_infra.__name__)/c.CONFIG_DIR_NAME/"
            "c.Infra.CODEGEN_CONFIG_FILENAME; "
            f"root=pathlib.Path({str(project)!r}); "
            "sources=FlextInfraConfig.config_sources_for_repository(root,"
            "filename=c.Infra.CODEGEN_CONFIG_FILENAME); "
            "assert sources[0]==pathlib.Path(str(resource)); "
            "inputs=u.Infra.load_codegen_inputs(root).unwrap(); "
            "assert inputs.sources[0].content==resource.read_bytes(); "
            "print('packaged-config-owned=True'); "
            "elected=u.Infra.declared_package_dir(flext_infra.__name__); "
            "assert p.is_relative_to(elected); "
            "print('controller-root='+str(elected))"
        )
        try:
            custom.write_bytes(
                original
                + (
                    f"\npost-help:\n\t@$(PROJECT_INFRA_RUN) -c {quote(probe)}\n"
                    "\t@$(PROJECT_FLEXT_INFRA) workspace verify-environment "
                    '--repository-root "$(RUNTIME_ROOT)"\n'
                ).encode(c.DEFAULT_ENCODING)
            )
            process = tm.ok(
                u.Tests.run_isolated_make(
                    [f"FLEXT_INFRA_SUBMODULE_SRC={override}", "help"],
                    cwd=project,
                    env={
                        "PYTHONPATH": str(override),
                        "MYPYPATH": str(override),
                        "VIRTUAL_ENV": str(override),
                        "UV_PROJECT": str(override),
                        "UV_PROJECT_ENVIRONMENT": str(override),
                        config.Infra.codegen.make.ci.variable: (
                            config.Infra.codegen.make.ci.value if ci_context else ""
                        ),
                    },
                )
            )
        finally:
            custom.write_bytes(original)
            shutil.rmtree(nested)
        tm.that(u.Cli.process_succeeded(process.outcome), eq=True, msg=process.stderr)
        tm.that(process.stdout, has="packaged-config-owned=True")
        selected = Path(
            next(
                line.removeprefix("controller-file=")
                for line in process.stdout.splitlines()
                if line.startswith("controller-file=")
            )
        )
        owned = Path(
            next(
                line.removeprefix("controller-root=")
                for line in process.stdout.splitlines()
                if line.startswith("controller-root=")
            )
        )
        tm.ok(selected.is_relative_to(owned))
        tm.fail(marker.exists())
