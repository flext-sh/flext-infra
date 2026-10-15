"""Immutable source-bundle and physical-path contracts for docs planning.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import m
from flext_infra.codegen import FlextInfraMisePublication
from flext_infra.docs.generator import FlextInfraDocGenerator
from tests import p, tm, u

_DOCS_CONSUMER_SOURCE = r"""sys.path.insert(0, sys.argv[1])
from flext_infra import FlextInfraConfig, c, m
from flext_infra.codegen import (
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenPreconditions,
    FlextInfraCodegenTransaction,
    FlextInfraMiseArtifactsJournal,
    FlextInfraMiseArtifactsVerification,
    FlextInfraMisePublication,
)
from flext_infra.docs import FlextInfraDocGenerator
from tests import p, tm, u
from tests.unit.docs.generator_bundle_tests import TestsFlextInfraDocsGeneratorBundle
tmp_path = Path(sys.argv[2])
case = TestsFlextInfraDocsGeneratorBundle()

def producer_for(
    generator: p.Infra.DocsArtifactPlanner,
    operation: p.AttributeProbe,
) -> m.Infra.CodegenPhaseAnalysis:
    return tm.ok(
        FlextInfraCodegenPreconditions.capture_producer(
            runtime_root,
            entrypoint=operation,
            collaborators=(generator.publish_batch,),
        )
    )

"""


class TestsFlextInfraDocsGeneratorBundle:
    """Immutable source-bundle and physical-path contracts for docs planning."""

    @staticmethod
    def _generator(workspace: Path) -> FlextInfraDocGenerator:
        """Return the public generator for the governed fixture project.

        Returns:
            The public generator for the governed fixture project.

        """
        return FlextInfraDocGenerator(
            repository_root=workspace,
            selected_projects=["flext-a"],
        )

    @staticmethod
    def _materialize_required_parents(
        generator: FlextInfraDocGenerator,
        bundle: m.Infra.DocsGenerationBundle,
    ) -> None:
        """Materialize fixture parents after the read-only planner has named them."""
        required = generator.required_directories(bundle)
        tm.ok(required)
        for directory in required.value:
            directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def test_publication_rejects_changed_captured_source(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """Reject changed bytes from the exact bundle instead of rerendering them."""
        native_consumer(
            _DOCS_CONSUMER_SOURCE
            + r"""workspace = u.Tests.create_docs_workspace(tmp_path, project_names=("flext-a",))
guide = workspace / "flext-a" / c.Infra.DIR_DOCS / "guides/operator.md"
guide.parent.mkdir(parents=True, exist_ok=True)
guide.write_text("# Original\n", encoding="utf-8")
target = workspace / "flext-a/README.md"
original_target = target.read_bytes()
generator = case._generator(workspace)
prepared = generator.prepare_bundle(
    producer=producer_for(generator, generator.prepare_bundle)
)
tm.ok(prepared)
guide.write_text("# Changed\n", encoding="utf-8")
published = generator.publish_batch(prepared.value)
tm.fail(published)
tm.that(published.error or "", has=str(guide))
tm.that(target.read_bytes(), eq=original_target)
tm.that(
    (workspace / "flext-a" / c.Infra.DIR_DOCS / "api-reference/generated").exists(),
    eq=False,
)
""",
            str(Path(__file__).resolve().parents[3]),
            str(tmp_path),
        )

    @staticmethod
    def test_published_membership_preserves_captured_resource_dependencies(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """Keep template/config inputs while refusing a newly introduced source."""
        native_consumer(
            _DOCS_CONSUMER_SOURCE
            + r'''workspace = u.Tests.create_docs_workspace(tmp_path, project_names=("flext-a",))
generator = case._generator(workspace)
prepared = tm.ok(generator.prepare_bundle(
    producer=producer_for(generator, generator.prepare_bundle)
))
resources = tuple(
    state.path
    for state in prepared.source_states
    if state.content is not None
    and not u.Infra.docs_source_path_is_input(
        state.path,
        prepared.source_roots,
        source_scope=prepared.source_scope,
    )
)
tm.that(bool(resources), eq=True)
receipts: list[m.Infra.CodegenPhaseOutcome] = []
tm.ok(generator.publish_batch(prepared, publication_receipts=receipts))
tm.that(len(receipts), eq=1)
published_generator_sources = {
    source.path: source for source in receipts[0].generator_sources
}
captured_generator_sources = tuple(
    tm.ok(
        FlextInfraMiseArtifactsJournal.source_record(
            prepared.producer.phase, source
        )
    )
    for source in prepared.producer.inputs
)
tm.that(
    all(
        source.path in published_generator_sources
        and published_generator_sources[source.path].sha256 == source.sha256
        for source in captured_generator_sources
    ),
    eq=True,
)
published_sources = {source.path: source for source in receipts[0].sources}
captured_sources = tuple(
    tm.ok(
        FlextInfraMiseArtifactsJournal.source_record(
            receipts[0].phase, source
        )
    )
    for source in prepared.source_states
)
tm.that(
    all(
        source.path in published_sources
        and published_sources[source.path].sha256 == source.sha256
        for source in captured_sources
    ),
    eq=True,
)
tm.that(receipts[0].generator_trees, eq=prepared.producer.generator_trees)
tm.that(receipts[0].generator_modules, eq=prepared.producer.generator_modules)
tm.ok(
    FlextInfraMiseArtifactsVerification.publication_states_current(receipts[0]),
)
added = workspace / "flext-a/src/flext_a/new_source.py"
added.write_text('"""Source added after publication."""\n', encoding="utf-8")
changed = FlextInfraMiseArtifactsVerification.publication_states_current(receipts[0])
tm.fail(changed)
tm.that(changed.error or "", has=str(added))
''',
            str(Path(__file__).resolve().parents[3]),
            str(tmp_path),
        )

    @staticmethod
    def test_publication_rejects_declared_optional_layer_creation(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """An absent optional input remains part of the admitted source census."""
        native_consumer(
            _DOCS_CONSUMER_SOURCE
            + r"""workspace = u.Tests.create_docs_workspace(tmp_path, project_names=("flext-a",))
_, _, local_layer = FlextInfraConfig.config_layer_paths_for_repository(
    workspace,
    filename=c.Infra.CODEGEN_CONFIG_FILENAME,
)
tm.that(local_layer.exists(), eq=False)
generator = case._generator(workspace)
prepared = tm.ok(generator.prepare_bundle(
    producer=producer_for(generator, generator.prepare_bundle)
))
captured = next(state for state in prepared.source_states if state.path == local_layer)
tm.that(captured.content, eq=None)
local_layer.parent.mkdir(parents=True, exist_ok=True)
tm.ok(u.Cli.yaml_dump(local_layer, {"Infra": {"codegen": {}}}))
published = generator.publish_batch(prepared)
tm.fail(published)
tm.that(published.error or "", has=str(local_layer))
""",
            str(Path(__file__).resolve().parents[3]),
            str(tmp_path),
        )

    def test_batch_captures_optional_configuration_absence(
        self,
        tmp_path: Path,
    ) -> None:
        """The conform batch keeps the optional layer's absence as a source fact."""
        workspace = u.Tests.create_docs_workspace(tmp_path, project_names=("flext-a",))
        _, _, local_layer = FlextInfraConfig.config_layer_paths_for_repository(
            workspace,
            filename=c.Infra.CODEGEN_CONFIG_FILENAME,
        )
        generator = self._generator(workspace)
        prepared = tm.ok(next(generator.prepare_batches()))
        captured = next(
            state for state in prepared.source_states if state.path == local_layer
        )
        tm.that(captured.content, eq=None)
        local_layer.parent.mkdir(parents=True, exist_ok=True)
        tm.ok(u.Cli.yaml_dump(local_layer, {"Infra": {"codegen": {}}}))

        published = generator.publish_batch(prepared)

        tm.fail(published)
        tm.that(published.error or "", has=str(local_layer))

    def test_publication_rejects_source_topology_addition_after_bundle(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """Reject a newly consumed source that was absent from the frozen inventory."""
        native_consumer(
            _DOCS_CONSUMER_SOURCE
            + r'''workspace = u.Tests.create_docs_workspace(tmp_path, project_names=("flext-a",))
generator = case._generator(workspace)
prepared = generator.prepare_bundle(
    producer=producer_for(generator, generator.prepare_bundle)
)
tm.ok(prepared)
added = workspace / "flext-a/src/flext_a/added.py"
added.write_text('"""Added after render."""\n', encoding="utf-8")
published = generator.publish_batch(prepared.value)
tm.fail(published)
tm.that(published.error or "", has=c.Infra.DOCS_SOURCE_TOPOLOGY_RACE_MARKER)
''',
            str(Path(__file__).resolve().parents[3]),
            str(tmp_path),
        )

    @staticmethod
    def test_publication_rejects_replaced_source_directory(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """Identical bytes under a replacement source directory retain no authority."""
        native_consumer(
            _DOCS_CONSUMER_SOURCE
            + r"""workspace = u.Tests.create_docs_workspace(tmp_path, project_names=("flext-a",))
generator = FlextInfraDocGenerator(
    repository_root=workspace,
    selected_projects=["flext-a"],
    include_root=False,
)
prepared = next(generator.prepare_batches(
    producer=producer_for(generator, generator.prepare_batches)
))
tm.ok(prepared)
package = workspace / "flext-a/src/flext_a"
relocated = workspace / "flext-a/retained_package"
package.rename(relocated)
package.mkdir()
for source in relocated.iterdir():
    if source.is_file():
        (package / source.name).write_bytes(source.read_bytes())
published = generator.publish_batch(prepared.value)
tm.fail(published)
tm.that(published.error or "", has=str(package))
""",
            str(Path(__file__).resolve().parents[3]),
            str(tmp_path),
        )

    @staticmethod
    def test_noop_destination_edit_rejects_original_publication_state(
        tmp_path: Path,
    ) -> None:
        """A no-op still proves its original state before reporting success."""
        target = tmp_path / "artifact.md"
        target.write_bytes(b"original\n")
        before = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
        plan = m.Infra.CodegenFilePlan(
            project=tmp_path,
            path=target,
            before=before,
            desired_content=before.content,
            desired_mode=before.mode,
            owner="docs",
        )
        target.write_bytes(b"concurrent\n")

        published = FlextInfraMisePublication.publish_file_plan(plan, phase="docs")

        tm.fail(published)
        tm.that(target.read_bytes(), eq=b"concurrent\n")

    @staticmethod
    def test_admitted_inputs_remain_the_publication_snapshot(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """A changed consumed input rejects publication without replacing either file."""
        native_consumer(
            _DOCS_CONSUMER_SOURCE
            + r"""root = u.Tests.git_repository(tmp_path)
source = root / "input.py"
source.write_bytes(b"value = 1\n")
captured = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
target = root / "generated.md"
before = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=False))
analysis = m.Infra.CodegenPhaseAnalysis(
    phase=c.Infra.CodegenStagedFilePhase.DOCS,
    inputs=(captured,),
    files=(
        m.Infra.CodegenFilePlan(
            project=root,
            path=target,
            before=before,
            desired_content=b"captured value = 1\n",
            desired_mode=0o644,
            source_states=(captured,),
            owner="docs",
        ),
    ),
)
producer = tm.ok(
    FlextInfraCodegenPreconditions.capture_producer(
        runtime_root, entrypoint=FlextInfraCodegenTransaction
    )
)
transaction = FlextInfraCodegenTransaction(
    FlextInfraCodegenMiseArtifacts(repository_root=root),
    producer=producer,
)
analysis = tm.ok(
    FlextInfraCodegenPreconditions.bind_producer_analysis(analysis, producer)
)
admission = tm.ok(FlextInfraMisePublication.admit_batch(analysis))
source.write_bytes(b"value = 2\n")
roots = {"@docs": root}
published = transaction.run_files_locked(
    roots,
    lambda scope: transaction.publish_file_phase_locked(
        scope,
        roots,
        analysis,
        m.Infra.CodegenPhasePublicationPolicy(
            directories=(), admission=admission
        ),
    ),
)
tm.fail(published)
tm.that(
    tm.ok(u.Cli.atomic_read_binary_file_state(target, required=False)),
    eq=before,
)
tm.that(source.read_bytes(), eq=b"value = 2\n")
""",
            str(Path(__file__).resolve().parents[3]),
            str(tmp_path),
        )

    @staticmethod
    def test_member_batch_survives_later_member_source_change(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """Settle an admitted member without a later member's source barrier."""
        native_consumer(
            _DOCS_CONSUMER_SOURCE
            + r'''workspace = u.Tests.create_docs_workspace(
    tmp_path, project_names=("flext-a", "flext-b")
)
generator = FlextInfraDocGenerator(
    repository_root=workspace,
    selected_projects=["flext-a", "flext-b"],
    include_root=False,
)
batches = generator.prepare_batches(
    producer=producer_for(generator, generator.prepare_batches)
)
first = next(batches)
tm.ok(first)
later = workspace / "flext-b/src/flext_b/later.py"
later.write_text('"""Later member input."""\n', encoding="utf-8")
published = generator.publish_batch(first.value)
tm.ok(published)
earlier_readme = workspace / "flext-a/README.md"
admitted = earlier_readme.read_bytes()
second = next(batches)
tm.ok(second)
tm.ok(generator.publish_batch(second.value))
tm.that(earlier_readme.read_bytes(), eq=admitted)
''',
            str(Path(__file__).resolve().parents[3]),
            str(tmp_path),
        )

    @staticmethod
    def test_docs_target_leaf_symlink_to_in_project_file_is_rejected(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """Never turn a managed lexical target into an unmanaged in-project referent."""
        native_consumer(
            _DOCS_CONSUMER_SOURCE
            + r"""workspace = u.Tests.create_docs_workspace(tmp_path, project_names=("flext-a",))
project = workspace / "flext-a"
unmanaged = project / "NOTES.md"
unmanaged.write_text("keep\n", encoding="utf-8")
target = project / "README.md"
target.unlink()
target.symlink_to(unmanaged.name)
generator = case._generator(workspace)
prepared = generator.prepare_bundle(
    producer=producer_for(generator, generator.prepare_bundle)
)
tm.ok(prepared)
case._materialize_required_parents(generator, prepared.value)
planned = generator.plan_files(prepared.value)
tm.fail(planned)
tm.that(planned.error or "", has="atomic")
tm.that(unmanaged.read_text(encoding="utf-8"), eq="keep\n")
""",
            str(Path(__file__).resolve().parents[3]),
            str(tmp_path),
        )

    @staticmethod
    def test_docs_generated_parent_symlink_is_rejected_before_prune(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """Reject an aliased generated tree before deriving any delete artifact."""
        native_consumer(
            _DOCS_CONSUMER_SOURCE
            + r"""workspace = u.Tests.create_docs_workspace(tmp_path, project_names=("flext-a",))
project = workspace / "flext-a"
curated = project / "curated"
curated.mkdir()
keep = curated / "keep.md"
keep.write_text("keep\n", encoding="utf-8")
generated = project / c.Infra.DIR_DOCS / "api-reference/generated"
generated.parent.mkdir(parents=True, exist_ok=True)
generated.symlink_to(curated, target_is_directory=True)
generator = case._generator(workspace)
prepared = generator.prepare_bundle(
    producer=producer_for(generator, generator.prepare_bundle)
)
tm.fail(prepared)
tm.that(prepared.error or "", has="atomic")
tm.that(keep.read_text(encoding="utf-8"), eq="keep\n")
""",
            str(Path(__file__).resolve().parents[3]),
            str(tmp_path),
        )

    @staticmethod
    def test_selected_project_symlink_cannot_escape_workspace(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """Reject a selected local path whose physical project is outside the root."""
        native_consumer(
            _DOCS_CONSUMER_SOURCE
            + r"""workspace = u.Tests.create_docs_workspace(tmp_path)
outside = tmp_path / "outside"
package = outside / "src/outside"
package.mkdir(parents=True)
(package / "__init__.py").write_text("", encoding="utf-8")
(outside / "pyproject.toml").write_text(
    '[project]\nname = "outside"\nversion = "0.1.0"\n',
    encoding="utf-8",
)
(workspace / "escaped").symlink_to(outside, target_is_directory=True)
generator = FlextInfraDocGenerator(
    repository_root=workspace,
    selected_projects=["escaped"],
)
prepared = generator.prepare_bundle(
    producer=producer_for(generator, generator.prepare_bundle)
)
tm.fail(prepared)
tm.that(prepared.error or "", has="atomic")
""",
            str(Path(__file__).resolve().parents[3]),
            str(tmp_path),
        )

    @staticmethod
    def test_bundle_captures_actual_guide_and_template_sources(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """Bind every guide and both templates that materially feed the render."""
        native_consumer(
            _DOCS_CONSUMER_SOURCE
            + r"""workspace = u.Tests.create_docs_workspace(tmp_path, project_names=("flext-a",))
guide = workspace / "flext-a" / c.Infra.DIR_DOCS / "guides/operator.md"
guide.parent.mkdir(parents=True, exist_ok=True)
guide.write_text("# Operator\n", encoding="utf-8")
generator = case._generator(workspace)
prepared = generator.prepare_bundle(
    producer=producer_for(generator, generator.prepare_bundle)
)
tm.ok(prepared)
source_paths = {state.path for state in prepared.value.source_states}
source_names = {path.name for path in source_paths}
tm.that(guide in source_paths, eq=True)
tm.that(c.Infra.TEMPLATE_MKDOCS_PROJECT in source_names, eq=True)
tm.that(c.Infra.TEMPLATE_MKDOCS_ROOT in source_names, eq=True)
""",
            str(Path(__file__).resolve().parents[3]),
            str(tmp_path),
        )

    @staticmethod
    def test_cached_pyproject_cannot_diverge_from_bundle_source_bytes(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """Render a later valid pyproject version rather than a path-keyed old value."""
        native_consumer(
            _DOCS_CONSUMER_SOURCE
            + r"""workspace = u.Tests.create_docs_workspace(tmp_path, project_names=("flext-a",))
generator = case._generator(workspace)
first = generator.prepare_bundle(
    producer=producer_for(generator, generator.prepare_bundle)
)
tm.ok(first)
pyproject = workspace / "flext-a/pyproject.toml"
pyproject.write_text(
    '[project]\nname = "flext-a"\nversion = "0.2.0"\n'
    'description = "Fresh metadata"\n',
    encoding="utf-8",
)
second = generator.prepare_bundle(
    producer=producer_for(generator, generator.prepare_bundle)
)
tm.ok(second)
readme = next(
    artifact
    for scoped in second.value.scopes
    if scoped.scope.name == "flext-a"
    for artifact in scoped.artifacts
    if artifact.relative_path.as_posix() == "README.md"
)
tm.that(readme.desired_content or b"", has=b"Fresh metadata")
""",
            str(Path(__file__).resolve().parents[3]),
            str(tmp_path),
        )
