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
from flext_infra.codegen import FlextInfraCodegenConform, FlextInfraCodegenPreconditions
from tests import c, m, t, tm, u


class TestsFlextInfraRenderProvenance:
    """Rendered Make controls execute the installed, metadata-owned namespace."""

    @staticmethod
    @pytest.mark.parametrize("mutation", ["unchanged", "changed", "added", "directory", "removed-root"])
    def test_full_producer_authentication_precedes_source_selection(
        tmp_path: Path, mutation: str,
    ) -> None:
        """An out-of-consumer resource remains part of the producer CAS closure."""
        producer = tm.ok(FlextInfraCodegenPreconditions.capture_producer())
        resource_root = tmp_path / "declared-resource-root"
        resource_root.mkdir()
        resource = resource_root / "resource.json"
        tm.ok(u.Cli.atomic_write_text_file(resource, '{"value":"before"}'))
        state = tm.ok(u.Cli.atomic_read_binary_file_state(resource, required=True))
        inventory = tm.ok(u.Cli.atomic_inventory_physical_tree(resource_root))
        context = producer.model_copy(update={
            "inputs": (*producer.inputs, state),
            "generator_trees": (*producer.generator_trees, inventory),
        })
        tm.ok(FlextInfraCodegenPreconditions.producer_current(context))
        if mutation == "changed":
            tm.ok(u.Cli.atomic_write_text_file(resource, '{"value":"after"}'))
        elif mutation == "added":
            tm.ok(u.Cli.atomic_write_text_file(resource_root / "added.json", "{}"))
        elif mutation == "directory":
            (resource_root / "added-directory").mkdir()
        elif mutation == "removed-root":
            resource_root.rename(tmp_path / "retired-resource-root")
        observed = FlextInfraCodegenPreconditions.producer_current(context)
        tm.that(observed.success, eq=mutation == "unchanged")
        if observed.failure:
            tm.that(observed.error, has=str(resource_root))
        tm.that(context.inputs[-1], eq=state)
        tm.that(context.generator_trees[-1], eq=inventory)

    @staticmethod
    def test_phase_binds_exact_preplanning_producer_inputs(tmp_path: Path) -> None:
        """The native stage receives the same authenticated identities, not origins."""
        producer = tm.ok(FlextInfraCodegenPreconditions.capture_producer())
        source = tmp_path / "source.txt"
        tm.ok(u.Cli.atomic_write_text_file(source, "before"))
        state = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
        file = m.Infra.CodegenFilePlan(
            project=tmp_path, path=source, before=state,
            desired_content=b"after", desired_mode=state.mode, source_states=(state,),
        )
        original = m.Infra.CodegenPhaseAnalysis(
            phase=c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP,
            files=(file,), inputs=(state,),
        )
        bound = tm.ok(FlextInfraCodegenPreconditions.bind_producer_analysis(original, producer))
        tm.that(bound.generator_trees, eq=producer.generator_trees)
        tm.that(bound.files[0].source_states, eq=bound.inputs)
        tm.that({item.path: item for item in bound.inputs}, eq={
            item.path: item for item in (state, *producer.inputs)
        })
        tm.that(original.inputs, eq=(state,))

    @pytest.mark.parametrize("profile", list(c.Infra.MakeProfile))
    @pytest.mark.parametrize("ci_context", [False, True])
    def test_controller_ignores_undeclared_and_caller_sources(
        self,
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
                ports=None,
            )
        )
        tm.that(
            (project / c.Infra.MAKEFILE_FILENAME).read_text(),
            has=f"{c.Infra.RENDERED_BY_MARKER}{importlib.metadata.version(config.Infra.name)}",
        )
        override = tmp_path / "caller-source"
        marker = tmp_path / "undeclared-controller-executed"
        nested = project / "flext-infra"
        tm.that(nested.exists(), eq=False)
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
            "import importlib.metadata as md,pathlib,flext_infra; "
            "from importlib.resources import files; "
            "from flext_infra import FlextInfraConfig,c,u; "
            f"d=md.distribution({config.Infra.name!r}); "
            "p=pathlib.Path(flext_infra.__file__).resolve(); "
            "print('controller-file='+str(p)); print('controller-owned='+str(any("
            "d.locate_file(f).resolve()==p for f in d.files))); "
            "resource=files(flext_infra.__name__)/c.CONFIG_DIR_NAME/"
            "c.Infra.CODEGEN_CONFIG_FILENAME; "
            f"root=pathlib.Path({str(project)!r}); "
            "sources=FlextInfraConfig.config_sources_for_repository(root,"
            "filename=c.Infra.CODEGEN_CONFIG_FILENAME); "
            "assert sources[0]==pathlib.Path(str(resource)); "
            "assert any(d.locate_file(f).resolve()==sources[0].resolve() "
            "for f in d.files); "
            "inputs=u.Infra.load_codegen_inputs(root).unwrap(); "
            "assert inputs.sources[0].content==resource.read_bytes(); "
            "print('packaged-config-owned=True')"
            "; from flext_infra.codegen import FlextInfraCodegenPreconditions; "
            "captured=FlextInfraCodegenPreconditions.capture_producer().unwrap(); "
            "elected=u.Infra.declared_package_dir(flext_infra.__name__); "
            "assert elected in {tree.root.path for tree in captured.generator_trees}; "
            "bound={state.path: state for state in captured.inputs}; "
            "assert sources[0] in bound; "
            "assert bound[sources[0]].content==resource.read_bytes(); "
            "assert any(path.parent.name.endswith('.dist-info') for path in bound); "
            "assert FlextInfraCodegenPreconditions.producer_current(captured).unwrap(); "
            "print('producer-closure-owned=True')"
        )
        try:
            custom.write_bytes(
                original
                + (
                    f"\npost-help:\n\t@$(PROJECT_INFRA_RUN) -c {quote(probe)}\n"
                    '\t@$(PROJECT_FLEXT_INFRA) workspace verify-environment --repository-root "$(RUNTIME_ROOT)"\n'
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
        tm.that(process.outcome.raw_return_code, eq=0, msg=process.stderr)
        tm.that(process.stdout, has="controller-owned=True")
        tm.that(process.stdout, has="packaged-config-owned=True")
        tm.that(process.stdout, has="producer-closure-owned=True")
        selected = Path(
            next(
                line.removeprefix("controller-file=")
                for line in process.stdout.splitlines()
                if line.startswith("controller-file=")
            )
        )
        tm.that(
            selected.is_relative_to(u.Infra.runtime_environment_dir(project)), eq=True
        )
        tm.that(marker.exists(), eq=False)
