"""Render-provenance contracts: every emitted artifact names its generator.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib.metadata
import os
import shutil
import stat
import sys
from pathlib import Path
from shlex import quote

import pytest

from flext_infra import config
from flext_infra.codegen import (
    FlextInfraCodegenConform,
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenPreconditions,
    FlextInfraCodegenTransaction,
    FlextInfraMiseArtifactsFiles,
)
from flext_infra.validate import FlextInfraValidateFreshImport
from tests import c, m, t, tm, u


class TestsFlextInfraRenderProvenance:
    """Rendered Make controls execute the installed, metadata-owned namespace."""

    @staticmethod
    @pytest.mark.parametrize("failure", ["none", "manifest", "binding", "name"])
    def test_native_distribution_collection_retains_resources_and_failure_order(
        tmp_path: Path,
        failure: str,
    ) -> None:
        """Real PEP 376 descriptors preserve complete resources and native barriers."""
        metadata = tmp_path / "capture_provider-1.0.dist-info"
        metadata.mkdir()
        (metadata / "METADATA").write_text(
            "Metadata-Version: 2.4\nVersion: 1.0\n"
            + ("Name: capture-provider\n" if failure != "name" else ""),
            encoding=c.DEFAULT_ENCODING,
        )
        (metadata / "resource.bin").write_bytes(b"unlisted physical resource")
        binding = tmp_path / "capture-provider.pth"
        if failure not in {"manifest", "binding"}:
            binding.write_text(str(tmp_path) + "\n", encoding=c.DEFAULT_ENCODING)
        if failure != "manifest":
            (metadata / "RECORD").write_text(
                f"{metadata.name}/METADATA,,\n{metadata.name}/RECORD,,\n"
                f"{binding.name},,\n",
                encoding=c.DEFAULT_ENCODING,
            )
        distributions = u.installed_distributions(path=(str(tmp_path),))
        tm.that(len(distributions), eq=1)
        observed = FlextInfraMiseArtifactsFiles.capture_distribution_sources(
            distributions[0]
        )
        if failure != "none":
            expected = {
                "manifest": "no native file manifest",
                "binding": str(binding),
                "name": "no declared name",
            }
            tm.fail(observed, has=expected[failure])
            return
        trees, states, paths = tm.ok(observed)
        tm.that(trees, eq=(tm.ok(u.Cli.atomic_inventory_physical_tree(metadata)),))
        expected_paths = tuple(
            entry.path
            for entry in trees[0].entries
            if entry.kind == "file" and c.Infra.DUNDER_PYCACHE not in entry.path.parts
        )
        tm.that(
            states,
            eq=tuple(
                tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
                for path in (*expected_paths, binding)
            ),
        )
        declared = tm.not_none(distributions[0].files)
        tm.that(
            paths,
            eq=tuple(
                Path(str(distributions[0].locate_file(item))).absolute()
                for item in declared
            ),
        )

    @staticmethod
    @pytest.mark.parametrize(
        "record", ["native", "parent", "prefix", "case", "backslash"]
    )
    def test_real_record_paths_preserve_native_namespace_ownership(
        tmp_path: Path,
        record: str,
    ) -> None:
        """Real descriptors retain native lexical ownership and physical coverage."""
        namespace = "record_provider_fixture"
        package = tmp_path / namespace
        package.mkdir()
        (package / c.Infra.INIT_PY).write_text(
            "def produce():\n    return 'physical provider'\n",
            encoding=c.DEFAULT_ENCODING,
        )
        metadata = tmp_path / "record_provider_fixture-1.0.dist-info"
        metadata.mkdir()
        (metadata / "METADATA").write_text(
            "Metadata-Version: 2.4\nName: record-provider-fixture\nVersion: 1.0\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (metadata / "resource.bin").write_bytes(b"unlisted physical metadata resource")
        paths = {
            "native": f"{namespace}/__init__.py",
            "parent": f"../{namespace}/__init__.py",
            "prefix": f"{namespace}_other/__init__.py",
            "case": f"{namespace.upper()}/__init__.py",
            "backslash": f"{namespace}\\__init__.py",
        }
        (metadata / "RECORD").write_text(
            f"{metadata.name}/METADATA,,\n{metadata.name}/RECORD,,\n{paths[record]},,\n",
            encoding=c.DEFAULT_ENCODING,
        )
        probe = """
import importlib
import importlib.metadata
import sys
from pathlib import Path
from flext_infra import m
from flext_infra.codegen import FlextInfraCodegenPreconditions
directory, namespace = sys.argv[1:]
sys.path.insert(0, directory)
importlib.invalidate_caches()
package = Path(directory) / namespace
descriptor = importlib.metadata.distribution('record-provider-fixture')
declared = descriptor.files
assert declared is not None
owned = any(
    Path(str(descriptor.locate_file(item))).absolute().is_relative_to(package)
    for item in declared
)
importlib.import_module(namespace)
observed = FlextInfraCodegenPreconditions.observed_source_authority(
    Path(sys.prefix).parent,
    (m.Infra.SourceClassReference(target=namespace, attributes=('produce',)),))
if owned:
    evidence, _observation = observed.unwrap()
    assert (namespace, package) in evidence.generator_modules
    bound = {state.path: state for state in
             FlextInfraCodegenPreconditions.authority_inputs(evidence).unwrap()}
    for resource in (package / '__init__.py', Path(descriptor.locate_file(
        'record_provider_fixture-1.0.dist-info/resource.bin'))):
        assert bound[resource].content == resource.read_bytes()
else:
    assert observed.failure, observed
    assert 'ambiguous physical distribution ownership' in observed.error, observed.error
print('native-record-ownership=' + str(owned))
"""
        process = tm.ok(
            u.Cli.run([sys.executable, "-c", probe, str(tmp_path), namespace])
        )
        tm.that(process.stdout, has="native-record-ownership=")

    @staticmethod
    @pytest.mark.parametrize("mutation", ["unchanged", "duplicate", "rebound"])
    def test_real_third_provider_preserves_physical_election(
        tmp_path: Path,
        mutation: str,
    ) -> None:
        """A native child SDK rejects same-name/case duplicates and cold rebinding."""
        namespace = "capture_provider_fixture"
        primary = tmp_path / "primary"
        rebound = tmp_path / "rebound"
        for root in (primary, rebound):
            package = root / namespace
            package.mkdir(parents=True)
            (package / c.Infra.INIT_PY).write_text(
                "VALUE = 'physical provider'\n", encoding=c.DEFAULT_ENCODING
            )
            (package / "resource.bin").write_bytes(b"unlisted provider resource")
            for index, name in enumerate(("Capture-Provider", "capture-provider")):
                if index and mutation != "duplicate":
                    continue
                metadata = root / f"capture_provider_{index}-1.0.dist-info"
                metadata.mkdir()
                (metadata / "METADATA").write_text(
                    f"Metadata-Version: 2.4\nName: {name}\nVersion: 1.0\n",
                    encoding=c.DEFAULT_ENCODING,
                )
                (metadata / "top_level.txt").write_text(
                    namespace + "\n", encoding=c.DEFAULT_ENCODING
                )
                (metadata / "RECORD").write_text(
                    f"{metadata.name}/METADATA,,\n{metadata.name}/RECORD,,\n"
                    f"{metadata.name}/top_level.txt,,\n{namespace}/__init__.py,,\n",
                    encoding=c.DEFAULT_ENCODING,
                )
        candidate = u.Infra.declared_package_dir(
            FlextInfraCodegenPreconditions.__module__.partition(".")[0]
        )
        tm.that(candidate, none=False)
        probe = """
import importlib
import sys
from pathlib import Path
from flext_infra import u
from flext_infra.codegen import FlextInfraCodegenPreconditions
from flext_infra.validate import FlextInfraValidateFreshImport
primary, rebound, expected, namespace, mutation = sys.argv[1:]
sdk = FlextInfraCodegenPreconditions
assert u.Infra.declared_package_dir(sdk.__module__.partition('.')[0]) == Path(expected)
sys.path.insert(0, primary)
importlib.invalidate_caches()
importlib.import_module(namespace)
observed = FlextInfraValidateFreshImport.capture_producer(
    Path.cwd(), entrypoint=FlextInfraValidateFreshImport.capture_producer)
if mutation == 'duplicate':
    assert observed.failure, observed
    assert 'ambiguous physical distribution ownership' in observed.error, observed.error
else:
    producer = observed.unwrap()
    assert (namespace, Path(primary) / namespace) in producer.generator_modules
    resource = Path(primary) / namespace / 'resource.bin'
    bound = {state.path: state for state in producer.inputs}
    assert bound[resource].content == resource.read_bytes()
    if mutation == 'rebound':
        sys.path.remove(primary)
        sys.path.insert(0, rebound)
        importlib.invalidate_caches()
    current = sdk.producer_current(producer)
    assert current.success == (mutation == 'unchanged'), current.error
    if mutation == 'rebound':
        assert 'election changed' in current.error, current.error
print('physical-provider-proof=' + mutation)
"""
        process = tm.ok(
            u.Cli.run([
                sys.executable,
                "-c",
                probe,
                str(primary),
                str(rebound),
                str(candidate),
                namespace,
                mutation,
            ])
        )
        tm.that(process.stdout, has=f"physical-provider-proof={mutation}")

    @staticmethod
    @pytest.mark.parametrize(
        "mutation",
        [
            "unchanged",
            "changed",
            "added",
            "directory",
            "removed-root",
            "mode",
            "timestamp",
            "link",
            "intermediate-input",
        ],
    )
    def test_full_producer_authentication_precedes_source_selection(
        tmp_path: Path,
        mutation: str,
    ) -> None:
        """An out-of-consumer resource remains part of the producer CAS closure."""
        producer = tm.ok(
            FlextInfraValidateFreshImport.capture_producer(
                Path.cwd(),
                entrypoint=FlextInfraValidateFreshImport.capture_producer,
            )
        )
        resource_root = tmp_path / "declared-resource-root"
        resource_root.mkdir()
        anchor = resource_root / "anchor.json"
        tm.ok(u.Cli.atomic_write_text_file(anchor, "{}"))
        anchor_state = tm.ok(u.Cli.atomic_read_binary_file_state(anchor, required=True))
        resource = resource_root / "resource.json"
        tm.ok(u.Cli.atomic_write_text_file(resource, '{"value":"before"}'))
        state = tm.ok(u.Cli.atomic_read_binary_file_state(resource, required=True))
        inventory = tm.ok(u.Cli.atomic_inventory_physical_tree(resource_root))
        context = producer.model_copy(
            update={
                "inputs": (*producer.inputs, anchor_state, state),
                "generator_trees": (*producer.generator_trees, inventory),
            }
        )
        tm.ok(FlextInfraCodegenPreconditions.producer_current(context))
        if mutation == "changed":
            tm.ok(u.Cli.atomic_write_text_file(resource, '{"value":"after"}'))
        elif mutation == "added":
            tm.ok(u.Cli.atomic_write_text_file(resource_root / "added.json", "{}"))
        elif mutation == "directory":
            (resource_root / "added-directory").mkdir()
        elif mutation == "removed-root":
            resource_root.rename(tmp_path / "retired-resource-root")
        elif mutation == "mode":
            mode = tm.not_none(state.mode)
            resource.chmod(mode ^ stat.S_IXUSR)
        elif mutation == "timestamp":
            before = resource.stat()
            os.utime(resource, ns=(before.st_atime_ns, before.st_mtime_ns + 1))
        elif mutation == "link":
            resource.with_suffix(".alias").hardlink_to(resource)
        elif mutation == "intermediate-input":
            # Real in-place writes preserve the inode while the captured bytes
            # disagree with the earlier tree and the final restored contents.
            resource.write_bytes(b'{"value":"intermediate"}')
            state = tm.ok(u.Cli.atomic_read_binary_file_state(resource, required=True))
            resource.write_bytes(b'{"value":"before"}')
            context = context.model_copy(
                update={"inputs": (*producer.inputs, anchor_state, state)},
            )
        observed = FlextInfraCodegenPreconditions.producer_current(context)
        tm.that(observed.success, eq=mutation == "unchanged")
        if observed.failure:
            tm.that(observed.error, has=str(resource_root))
        tm.that(context.inputs[-1], eq=state)
        tm.that(context.generator_trees[-1], eq=inventory)

    @staticmethod
    def test_optional_external_producer_input_retains_exact_absence(
        tmp_path: Path,
    ) -> None:
        """An optional path outside inventoried trees stays an authenticated input."""
        producer = tm.ok(
            FlextInfraValidateFreshImport.capture_producer(
                Path.cwd(),
                entrypoint=FlextInfraValidateFreshImport.capture_producer,
            )
        )
        optional = tmp_path / "not-materialized" / "optional-source.json"
        state = tm.ok(u.Cli.atomic_read_binary_file_state(optional, required=False))
        context = producer.model_copy(
            update={"inputs": (*producer.inputs, state)},
        )
        tm.ok(FlextInfraCodegenPreconditions.producer_current(context))
        optional.parent.mkdir()
        tm.ok(u.Cli.atomic_write_text_file(optional, '{"value":"now-present"}'))
        observed = FlextInfraCodegenPreconditions.producer_current(context)
        tm.ok(observed.failure)
        tm.that(observed.error, has=str(optional))
        tm.that(context.inputs[-1], eq=state)

    @staticmethod
    def test_phase_binds_exact_preplanning_producer_inputs(tmp_path: Path) -> None:
        """The native stage receives the same authenticated identities, not origins."""
        producer = tm.ok(
            FlextInfraValidateFreshImport.capture_producer(
                Path.cwd(),
                entrypoint=FlextInfraValidateFreshImport.capture_producer,
            )
        )
        source = tmp_path / "source.txt"
        tm.ok(u.Cli.atomic_write_text_file(source, "before"))
        state = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
        file = m.Infra.CodegenFilePlan(
            project=tmp_path,
            path=source,
            before=state,
            desired_content=b"after",
            desired_mode=state.mode,
            source_states=(state,),
        )
        original = m.Infra.CodegenPhaseAnalysis(
            phase=c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP,
            files=(file,),
            inputs=(state,),
        )
        bound = tm.ok(
            FlextInfraCodegenPreconditions.bind_producer_analysis(original, producer)
        )
        tm.that(bound.generator_trees, eq=producer.generator_trees)
        tm.that(bound.generator_modules, eq=producer.generator_modules)
        tm.that(bound.files[0].source_states, eq=bound.inputs)
        tm.that(
            {item.path: item for item in bound.inputs},
            eq={item.path: item for item in (state, *producer.inputs)},
        )
        tm.that(original.inputs, eq=(state,))

    @staticmethod
    @pytest.mark.parametrize("mutation", ["removed-provider", "moved-provider"])
    def test_entire_captured_election_is_required(
        tmp_path: Path,
        mutation: str,
    ) -> None:
        """Resource witnesses cannot admit an omitted or physically foreign provider."""
        producer = tm.ok(
            FlextInfraValidateFreshImport.capture_producer(
                Path.cwd(),
                entrypoint=FlextInfraValidateFreshImport.capture_producer,
            )
        )
        namespace, physical = producer.generator_modules[-1]
        modules = producer.generator_modules[:-1]
        if mutation == "moved-provider":
            modules = (*modules, (namespace, tmp_path / physical.name))
        context = producer.model_copy(update={"generator_modules": modules})
        observed = FlextInfraCodegenPreconditions.producer_current(context)
        tm.ok(observed.failure)
        tm.that(observed.error, has="election changed")
        tm.that(context.inputs, eq=producer.inputs)
        tm.that(context.generator_trees, eq=producer.generator_trees)

    @staticmethod
    @pytest.mark.parametrize("foreign", [False, True])
    def test_native_generation_accounts_only_admitted_source_effects(
        tmp_path: Path,
        *,
        foreign: bool,
    ) -> None:
        """A journaled source cutover succeeds; unmanifested bytes fail early."""
        root = u.Tests.git_repository(tmp_path)
        resources = root / "producer"
        resources.mkdir()
        helper = resources / "helper.py"
        helper.write_bytes(b"VALUE = 'before'\n")
        state = tm.ok(u.Cli.atomic_read_binary_file_state(helper, required=True))
        tm.that(state.content, none=False)
        producer = tm.ok(
            FlextInfraValidateFreshImport.capture_producer(
                Path.cwd(),
                entrypoint=FlextInfraValidateFreshImport.capture_producer,
            )
        )
        context = producer.model_copy(
            update={
                "inputs": (*producer.inputs, state),
                "generator_trees": (
                    *producer.generator_trees,
                    tm.ok(u.Cli.atomic_inventory_physical_tree(resources)),
                ),
            }
        )
        plan = m.Infra.CodegenFilePlan(
            project=root,
            path=helper,
            before=state,
            desired_content=b"VALUE = 'after'\n",
            desired_mode=state.mode,
            source_states=(state,),
        )
        analysis = m.Infra.CodegenPhaseAnalysis(
            phase=c.Infra.CodegenStagedFilePhase.SEMANTIC,
            files=(plan,),
            inputs=(state,),
        )
        owner = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
            producer=context,
        )
        if foreign:
            helper.write_bytes(b"VALUE = 'foreign'\n")
        observed = owner.run_files_locked(
            {"@producer": root},
            lambda scope_root: owner.publish_file_phase_locked(
                scope_root,
                {"@producer": root},
                analysis,
                m.Infra.CodegenPhasePublicationPolicy(directories=()),
            ),
        )
        if foreign:
            tm.fail(observed, has="generation authenticated state changed")
            tm.that(
                observed.error,
                has=f"expected_sha256={u.Cli.sha256_bytes(tm.not_none(state.content))}",
            )
            tm.that(helper.read_bytes(), eq=b"VALUE = 'foreign'\n")
        else:
            tm.that(tm.ok(observed), eq=(helper,))
            tm.that(helper.read_bytes(), eq=plan.desired_content)

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
            "print('packaged-config-owned=True')"
            "; from flext_infra.codegen import FlextInfraCodegenPreconditions; "
            "from flext_infra.validate import FlextInfraValidateFreshImport; "
            "from pathlib import Path; "
            "captured=FlextInfraValidateFreshImport.capture_producer("
            "Path.cwd(), entrypoint=FlextInfraValidateFreshImport.capture_producer"
            ").unwrap(); "
            "elected=u.Infra.declared_package_dir(flext_infra.__name__); "
            "assert elected in {tree.root.path for tree in captured.generator_trees}; "
            "print('controller-root='+str(elected)); "
            "bound={state.path: state for state in captured.inputs}; "
            "assert p in bound; print('controller-owned=True'); "
            "assert sources[0] in bound; "
            "assert bound[sources[0]].content==resource.read_bytes(); "
            "assert any(path.parent.name.endswith('.dist-info') for path in bound); "
            "assert FlextInfraCodegenPreconditions."
            "producer_current(captured).unwrap(); "
            "print('producer-closure-owned=True')"
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
        owned = Path(
            next(
                line.removeprefix("controller-root=")
                for line in process.stdout.splitlines()
                if line.startswith("controller-root=")
            )
        )
        tm.ok(selected.is_relative_to(owned))
        tm.fail(marker.exists())
