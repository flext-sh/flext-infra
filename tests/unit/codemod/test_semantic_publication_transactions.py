"""Real public semantic publication transactions, candidates and consumers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path
from types import FrameType

import pytest

from flext_infra import codegen, codemod, infra, refactor, transformers, workspace
from tests import c, m, p, r, t, tm, u


@pytest.fixture
def mod_workspace(mod_workspace: Path) -> Path:
    """Initialize the selected publication runtime before recording source queries.

    Returns:
        The original native workspace with its canonical control planes ready.

    """
    tm.ok(
        codegen.FlextInfraCodegenFileLeases.prepare_source_controlplanes((
            mod_workspace,
        ))
    )
    return mod_workspace


class TestsFlextInfraSemanticPublicationTransactions:
    """Publish semantic candidates atomically and prove the real public consumers."""

    @pytest.mark.parametrize(
        "corruption",
        [None, "inputs", "source_query_topology", "publications", "files", "exception"],
    )
    def test_native_facade_cohort_preserves_complete_analysis_before_effects(
        self,
        mod_workspace: Path,
        corruption: str | None,
    ) -> None:
        """Admit complete native source/facade/init cohorts, never repaired metadata."""
        u.Tests.run_native_callable(
            self._scenario_native_facade_cohort,
            mod_workspace,
            corruption=corruption,
        )

    @staticmethod
    def _native_type_candidate(
        root: Path,
    ) -> t.Triple[
        m.Infra.SemanticFilePlan,
        m.Infra.CodegenPhaseAnalysis,
        m.Infra.CodegenPhaseAnalysis,
    ]:
        """Build a complete native type candidate over actual original descriptors.

        Returns:
            The authored owner and original native facade/initializer analyses.

        """
        u.Tests.standalone_workspace(root, name=root.name.replace("_", "-"))
        package = root / "src" / root.name
        owner = package / "_typings" / "domain.py"
        owner.parent.mkdir()
        (owner.parent / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        owner.write_text(
            "from flext_cli import FlextCliTypes\n"
            "type Payload = FlextCliTypes.JsonMapping\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (package / "typings.py").write_text(
            c.Infra.AUTOGEN_HEADERS[0]
            + '\n"""Public native type facade."""\n'
            + "from flext_cli import FlextCliTypes\n"
            + f"from {package.name}._typings import domain\n"
            + "class ModWorkspaceTypes(FlextCliTypes):\n"
            + "    class Domain:\n"
            + "        Payload = domain.Payload\n"
            + "t = ModWorkspaceTypes\n"
            + "__all__ = ['ModWorkspaceTypes', 't']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        before = tm.ok(u.Cli.atomic_read_binary_file_state(owner, required=True))
        authored = m.Infra.SemanticFilePlan(
            project=root,
            path=owner,
            before=before,
            desired_content=(
                "from flext_cli import FlextCliTypes\n"
                "class ModWorkspaceTypes(FlextCliTypes):\n"
                "    class Domain:\n"
                "        type Payload = FlextCliTypes.JsonMapping\n"
                "t = ModWorkspaceTypes\n"
                "__all__ = ['ModWorkspaceTypes', 't']\n"
            ).encode(c.DEFAULT_ENCODING),
            desired_mode=before.mode,
        )
        providers = tm.ok(
            transformers.FlextInfraSemanticPublication.plan_semantic_file_plans((
                authored,
            ))
        )
        inputs = tm.ok(u.Infra.load_codegen_inputs(root))
        producer = codegen.FlextInfraCodegenConformExecute(
            repository_root=root,
            state=m.Infra.CodegenConformState(
                repository_root=root, provider_plans=providers.files
            ),
        )
        _, facade = tm.ok(
            producer.plan_facade(
                m.Infra.CodegenConformRequest(
                    root=root,
                    what=c.Infra.CodegenConformSurface.FACADES,
                    module=f"{package.name}.typings",
                    scope=c.Infra.CodegenConformScope.SELF,
                ),
                inputs,
            )
        )
        with u.Infra.facade_source_project(
            root,
            source_options=m.Infra.StageSourceOptions(
                inputs=inputs.sources, declared_files=providers.files
            ),
        ) as binding:
            private = tm.ok(
                codegen.FlextInfraCodegenLazyInit(
                    repository_root=root,
                    project_scope_roots=(root,),
                ).plan_files(source_project=binding[0])
            )
        tm.that(
            len(facade.inputs),
            eq=len({state.path for state in facade.inputs}),
            msg="The original native facade analysis must contain unique input paths",
        )
        tm.that(
            len(private.inputs),
            eq=len({state.path for state in private.inputs}),
            msg=(
                "The original native initializer analysis must contain "
                "unique input paths"
            ),
        )
        return authored, facade, private

    @staticmethod
    def _scenario_native_facade_cohort(root: Path, *, corruption: str | None) -> None:
        """Exercise original native receipts, preview, and real cold public imports."""
        authored, facade, private = (
            TestsFlextInfraSemanticPublicationTransactions._native_type_candidate(root)
        )
        originals = tuple(
            (file.path, file.path.read_bytes())
            for phase in (facade, private)
            for file in phase.files
        )
        first_error = ValueError("original native projection failure")
        if corruption == "publications":
            private = private.model_copy(update={corruption: ()})
        elif corruption is not None:
            facade = facade.model_copy(
                update={
                    corruption: first_error if corruption == "exception" else (),
                }
            )

        def validate(candidate_root: Path) -> p.Result[bool]:
            """Require the actual CLI alias value through the public facade.

            Returns:
                The cold native public consumer result.

            """
            consumer = u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        "from flext_cli import FlextCliTypes\n"
                        f"from {root.name}.typings import t\n"
                        "assert issubclass(t, FlextCliTypes)\n"
                        "assert t.Domain is t.__bases__[0].Domain\n"
                        "assert t.Domain.Payload.__value__ is "
                        "FlextCliTypes.JsonMapping\n"
                    ),
                ),
                cwd=candidate_root,
                options=m.Cli.ProcessOptions(
                    env={
                        c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(candidate_root / "src")
                    }
                ),
            )
            if consumer.failure:
                return r[bool].from_failure(consumer)
            return r[bool].ok(u.Cli.process_succeeded(consumer.value.outcome))

        result = transformers.FlextInfraSemanticPublication.publish_semantic_analyses(
            (facade, private),
            source_plans=(authored,),
            repository_root=root,
            options=m.Infra.SemanticPublicationOptions(
                dependency_group="complete-native-type-cohort", validator=validate
            ),
            publish=False,
        )
        tm.that(authored.path.read_bytes(), eq=authored.before.content)
        for path, content in originals:
            tm.that(path.read_bytes(), eq=content)
        if corruption is not None:
            tm.fail(result)
            if corruption == "exception":
                tm.that(result.exception, is_=ValueError)
                tm.ok(result.exception is first_error)
            else:
                tm.that(
                    result.error,
                    has=(
                        "original publication dependencies"
                        if corruption == "publications"
                        else "batch native source queries differ"
                        if corruption in {"source_query_topology", "files"}
                        else "batch inputs differ"
                    ),
                )
            return
        tm.ok(result, eq=())
        tm.ok(
            transformers.FlextInfraSemanticPublication.publish_semantic_analyses(
                (facade, private),
                source_plans=(authored,),
                repository_root=root,
                options=m.Infra.SemanticPublicationOptions(
                    dependency_group="complete-native-type-cohort", validator=validate
                ),
            )
        )
        tm.ok(validate(root))

    @staticmethod
    def test_input_union_preserves_shared_identity_and_rejects_conflicts(
        tmp_path: Path,
    ) -> None:
        """One source authority survives repeats; neither conflicting order wins."""
        source = tmp_path / "source.py"
        source.write_bytes(b"VALUE = 1\n")
        first = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
        absent = tm.ok(u.Cli.atomic_read_binary_file_state(tmp_path / "optional"))
        shared = m.Cli.AtomicFileState.model_validate_json(first.model_dump_json())
        unique_states = u.Infra.unique_states
        tm.that(
            tm.ok(
                unique_states((
                    first,
                    absent,
                    shared,
                    absent,
                ))
            ),
            eq=(first, absent),
        )
        source.write_bytes(b"VALUE = 2\n")
        changed = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
        for observations in ((first, changed), (changed, first)):
            tm.fail(
                unique_states(observations),
                has=str(source),
            )
        tm.ok(u.Cli.atomic_verify_binary_file_states((changed, absent)))

    @staticmethod
    def test_cold_public_cli_composes_semantic_ports_without_an_import_cycle() -> None:
        """A fresh native CLI process must finish API composition before dispatch."""
        u.Tests.run_native_callable(
            TestsFlextInfraSemanticPublicationTransactions._scenario_cold_cli
        )

    @staticmethod
    def _scenario_cold_cli() -> None:
        """Spawn retains the native thread hook and the real public capture graph."""
        reference = workspace.FlextInfraWorkspaceNativeReference
        tm.that(threading.excepthook is threading.__excepthook__, truth=True)
        selections = tm.ok(reference.producer_selections(threading.Thread.__init__, ()))
        before = tm.ok(reference.capture(selections))
        tm.ok(
            any(
                item.kind != "alias"
                and item.supplier == threading.excepthook.__module__
                and item.qualname == threading.excepthook.__qualname__
                for item in before.bindings
            )
        )
        result = tm.ok(u.Cli.run((sys.executable, "-I", "-m", "flext_infra", "--help")))
        tm.ok(u.Cli.process_succeeded(result.outcome))
        tm.ok(reference.compare(before, tm.ok(reference.capture(selections))))

    @staticmethod
    def test_public_workspace_factory_preserves_selected_rope_root(
        tmp_path: Path,
    ) -> None:
        """The injected factory preserves the existing scoped workspace contract."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "consumer.py"
        source = "VALUE = 1\n"
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with infra.rope_workspace(root, root) as rope:
            tm.not_none(rope.module(path))
            tm.that(rope.source(path), eq=source)

    def test_joint_phases_reconcile_an_unchanged_initializer_later_owned_by_lazy_init(
        self,
        mod_workspace: Path,
    ) -> None:
        """Joint phases reconcile an initializer that lazy init later owns.

        The unchanged initializer is reconciled against the declared exports.

        """
        u.Tests.run_native_callable(self._scenario_initializer_receipt, mod_workspace)

    @staticmethod
    def _scenario_initializer_receipt(mod_workspace: Path) -> None:
        """Keep the historical initializer proof while consuming declared exports."""
        package = mod_workspace / "src" / mod_workspace.name
        declaration = package / "service.py"
        original = (
            "class DeclaredService:\n"
            "    @staticmethod\n"
            "    def normalize(value: str) -> str:\n"
            "        return value.strip().lower()\n\n"
            "__all__ = ('DeclaredService',)\n"
        )
        declaration.write_text(original, encoding=c.DEFAULT_ENCODING)
        initializer = package / c.Infra.INIT_PY
        states = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in (declaration, initializer)
        )
        plans = tuple(
            m.Infra.CodegenFilePlan(
                project=mod_workspace,
                path=state.path,
                before=state,
                desired_content=(
                    original.replace(".lower()", ".upper()").encode(c.DEFAULT_ENCODING)
                    if state.path == declaration
                    else state.content
                ),
                desired_mode=state.mode,
                source_states=states,
            )
            for state in states
        )
        tm.ok(
            transformers.FlextInfraSemanticPublication.publish_semantic_artifact_plans(
                plans,
                repository_root=mod_workspace,
                options=m.Infra.SemanticPublicationOptions(
                    projection_roots=(mod_workspace,),
                ),
            ),
        )
        output = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {mod_workspace.name} import DeclaredService; "
                        "assert DeclaredService.normalize(' live ') == 'LIVE'"
                    ),
                ),
                cwd=mod_workspace,
                options=m.Cli.ProcessOptions(
                    env={"PYTHONPATH": str(package.parent)},
                ),
            ),
        )
        tm.ok(u.Cli.process_succeeded(output.outcome))

    @pytest.mark.parametrize("foreign_parent", [False, True])
    def test_artifact_publication_owns_declared_absent_parent_chain(
        self,
        mod_workspace: Path,
        *,
        foreign_parent: bool,
    ) -> None:
        """Artifact publication owns the declared chain of absent parent directories.

        Missing parents are created through the journal; a foreign parent is
        refused.

        """
        u.Tests.run_native_callable(
            self._scenario_absent_parents,
            mod_workspace,
            foreign_parent=foreign_parent,
        )

    @staticmethod
    def _scenario_absent_parents(mod_workspace: Path, *, foreign_parent: bool) -> None:
        """Create missing parents through the journal or refuse a foreign owner."""
        publication = transformers.FlextInfraSemanticPublication
        package = mod_workspace / "src" / mod_workspace.name
        target = package / "relocated" / "nested" / "service.py"
        chain = tm.ok(u.Cli.atomic_plan_directory_chain(target.parent))
        source = (
            "class DeclaredService:\n"
            "    @staticmethod\n"
            "    def normalize(value: str) -> str:\n"
            "        return value.strip().upper()\n\n"
            "__all__ = ('DeclaredService',)\n"
        )
        plan = m.Infra.CodegenFilePlan(
            project=mod_workspace,
            path=target,
            before=chain,
            desired_content=source.encode(c.DEFAULT_ENCODING),
            desired_mode=package.stat().st_mode & 0o666,
        )
        foreign = target.parent / "foreign.txt"
        if foreign_parent:
            tm.ok(u.Cli.ensure_dir(target.parent))
            foreign.write_text("foreign owner\n", encoding=c.DEFAULT_ENCODING)
        result = publication.publish_semantic_artifact_plans(
            (plan,),
            repository_root=mod_workspace,
            options=m.Infra.SemanticPublicationOptions(
                projection_roots=(mod_workspace,),
            ),
        )
        if foreign_parent:
            tm.fail(result, has="parent chain changed")
            tm.fail(target.exists())
            tm.that(
                foreign.read_text(encoding=c.DEFAULT_ENCODING), eq="foreign owner\n"
            )
        else:
            tm.ok(result)
            consumer = tm.ok(
                u.Cli.run(
                    (
                        sys.executable,
                        "-c",
                        (
                            f"from {mod_workspace.name}.relocated.nested import "
                            "DeclaredService; "
                            "assert DeclaredService.normalize(' live ') == 'LIVE'"
                        ),
                    ),
                    cwd=mod_workspace,
                    options=m.Cli.ProcessOptions(
                        env={"PYTHONPATH": str(package.parent)},
                    ),
                ),
            )
            tm.ok(u.Cli.process_succeeded(consumer.outcome))
            tm.that(target.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    @pytest.mark.parametrize("accepted", [False, True])
    def test_artifact_candidate_retires_old_package_before_acceptance(
        self,
        mod_workspace: Path,
        *,
        accepted: bool,
    ) -> None:
        """A package move retires the old package only on acceptance.

        The preview exposes neither retired sources nor live effects.

        """
        u.Tests.run_native_callable(
            self._scenario_retired_package,
            mod_workspace,
            accepted=accepted,
        )

    @staticmethod
    def _scenario_retired_package(mod_workspace: Path, *, accepted: bool) -> None:
        """Preview a package move without exposing retired sources or live effects."""
        publication = transformers.FlextInfraSemanticPublication
        package = mod_workspace / c.Infra.DEFAULT_SRC_DIR / mod_workspace.name
        previous = package / "previous" / "service.py"
        current = package / "current" / previous.name
        previous.parent.mkdir()
        previous.write_text('VALUE = "previous"\n', encoding=c.DEFAULT_ENCODING)
        original = tm.ok(u.Cli.atomic_read_binary_file_state(previous, required=True))
        absent = tm.ok(u.Cli.atomic_read_binary_file_state(current))
        parents = tm.ok(u.Cli.atomic_plan_directory_chain(current.parent))
        desired = 'VALUE = "current"\n'
        inputs = (original, absent)
        plans = (
            m.Infra.CodegenFilePlan(
                project=mod_workspace,
                path=previous,
                before=original,
                desired_content=None,
                desired_mode=None,
                source_states=inputs,
            ),
            m.Infra.CodegenFilePlan(
                project=mod_workspace,
                path=current,
                before=parents,
                desired_content=desired.encode(c.DEFAULT_ENCODING),
                desired_mode=original.mode,
                source_states=inputs,
            ),
        )
        previews: list[Path] = []

        def validate(candidate_root: Path) -> p.Result[bool]:
            candidate = candidate_root / current.relative_to(mod_workspace)
            retired = candidate_root / previous.relative_to(mod_workspace)
            tm.that(candidate.read_text(encoding=c.DEFAULT_ENCODING), eq=desired)
            tm.fail(retired.exists())
            if candidate_root != mod_workspace:
                previews.append(candidate_root)
                tm.ok(u.Cli.atomic_verify_binary_file_states(inputs))
                tm.fail(current.parent.exists())
            consumer = tm.ok(
                u.Cli.run(
                    (
                        sys.executable,
                        "-c",
                        (
                            f"from {package.name}.{current.parent.name}.service "
                            f"import VALUE; assert VALUE == {current.parent.name!r}"
                        ),
                    ),
                    cwd=candidate_root,
                    options=m.Cli.ProcessOptions(
                        env={
                            c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(
                                candidate_root
                                / package.parent.relative_to(mod_workspace)
                            ),
                        },
                    ),
                ),
            )
            tm.ok(u.Cli.process_succeeded(consumer.outcome))
            return r[bool].ok(accepted)

        published = publication.publish_semantic_artifact_plans(
            plans,
            repository_root=mod_workspace,
            options=m.Infra.SemanticPublicationOptions(validator=validate),
        )
        tm.that(len(previews), eq=1)
        if accepted:
            tm.that(set(tm.ok(published)), eq={previous, current})
            tm.fail(previous.exists())
            tm.that(current.read_text(encoding=c.DEFAULT_ENCODING), eq=desired)
        else:
            tm.fail(published, has="candidate acceptance rejected")
            tm.ok(u.Cli.atomic_verify_binary_file_states(inputs))
            tm.fail(current.parent.exists())

    @pytest.mark.parametrize("unchanged", [False, True])
    def test_stub_retirement_and_consumer_annotations_publish_together(
        self,
        mod_workspace: Path,
        *,
        unchanged: bool,
    ) -> None:
        """An authenticated absent-state stub plan shares its consumer's group."""
        u.Tests.run_native_callable(
            self._scenario_stub_retirement,
            mod_workspace,
            unchanged=unchanged,
        )

    @staticmethod
    def _scenario_stub_retirement(mod_workspace: Path, *, unchanged: bool) -> None:
        """The staged real consumer runs without a retiring local stub."""
        package = mod_workspace / c.Infra.DEFAULT_SRC_DIR / mod_workspace.name
        source = package / "consumer.py"
        stub = source.with_suffix(".pyi")
        desired = "def normalize(value: str) -> str:\n    return value.strip()\n"
        source.write_text(
            desired
            if unchanged
            else desired.replace("value: str", "value").replace(" -> str", ""),
            encoding=c.DEFAULT_ENCODING,
        )
        stub.write_text(
            "def normalize(value: str) -> str: ...\n", encoding=c.DEFAULT_ENCODING
        )
        states = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in (source, stub)
        )
        plans = tuple(
            m.Infra.CodegenFilePlan(
                project=mod_workspace,
                path=state.path,
                before=state,
                desired_content=None
                if state.path == stub
                else desired.encode(c.DEFAULT_ENCODING),
                desired_mode=None if state.path == stub else state.mode,
                source_states=states,
                dependency_group="consumer-stub-retirement",
            )
            for state in states
        )

        def validate(candidate_root: Path) -> p.Result[bool]:
            tm.fail((candidate_root / stub.relative_to(mod_workspace)).exists())
            if candidate_root != mod_workspace:
                tm.ok(u.Cli.atomic_verify_binary_file_states(states))
            consumer = tm.ok(
                u.Cli.run(
                    (
                        sys.executable,
                        "-c",
                        (
                            f"from {package.name}.consumer import normalize; assert "
                            f"normalize(' live ') == 'live'"
                        ),
                    ),
                    cwd=candidate_root,
                    options=m.Cli.ProcessOptions(
                        env={
                            c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(
                                candidate_root / c.Infra.DEFAULT_SRC_DIR
                            ),
                        }
                    ),
                )
            )
            tm.ok(u.Cli.process_succeeded(consumer.outcome))
            return r[bool].ok(value=True)

        tm.ok(
            transformers.FlextInfraSemanticPublication.publish_semantic_artifact_plans(
                plans,
                repository_root=mod_workspace,
                options=m.Infra.SemanticPublicationOptions(validator=validate),
            )
        )
        tm.fail(stub.exists())
        tm.that(source.read_text(encoding=c.DEFAULT_ENCODING), eq=desired)

    @pytest.mark.parametrize("unchanged", [False, True])
    def test_semantic_publication_retains_full_native_candidate_checker(
        self,
        tmp_path: Path,
        session_runtime: p.Tests.SessionRuntime,
        *,
        unchanged: bool,
    ) -> None:
        """Changed and unchanged semantic plans keep the full native checker."""
        u.Tests.run_native_callable(
            self._scenario_native_checker,
            tmp_path,
            session_runtime.directory,
            unchanged=unchanged,
        )

    @staticmethod
    def _scenario_native_checker(
        tmp_path: Path,
        runtime_directory: Path,
        *,
        unchanged: bool,
    ) -> None:
        """Changed and unchanged semantic plans keep the full default checker."""
        publication = transformers.FlextInfraSemanticPublication
        session_runtime = u.Tests.SessionRuntime(runtime_directory)
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        checkout = Path(__file__).resolve().parents[3]
        tm.ok(
            u.Tests.create_python_environment(
                root,
                dependency_projects=(
                    checkout,
                    *u.Tests.python_dependency_projects(checkout),
                ),
                session_runtime=session_runtime,
            )
        )
        target = package / "consumer.py"
        notice = u.Infra.copyright_notice(root)
        header = (
            f'"""Native semantic checker candidate.\n\n{notice}\n"""\n\n'
            "from __future__ import annotations\n\n"
        )
        source = header + 'value: int = "invalid annotation value"\n'
        target.write_text(
            source if unchanged else header + "value: int = 1\n",
            encoding=c.DEFAULT_ENCODING,
        )
        before = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
        calls: list[str] = []
        commands: list[m.Infra.RunCommand] = []

        def observe(frame: FrameType, event: str, _value: p.AttributeProbe) -> None:
            if event != "call":
                return
            if frame.f_code.co_name in {
                "normalize_source_plan",
                "consume_source_runtime",
                "_check_semantic_sources",
                "execute_candidate",
                "_execute_payload",
                "run_projects",
            }:
                calls.append(frame.f_code.co_qualname)
            if (
                frame.f_code.co_qualname
                == "FlextInfraWorkspaceChecker.execute_candidate"
            ):
                params = frame.f_locals.get("params")
                if not isinstance(params, m.Infra.RunCommand):
                    pytest.fail("Native semantic checker did not receive RunCommand")
                commands.append(params)
                tm.fail(params.repository_root == root)
                tm.that(params.file, eq=None)
                tm.that(params.gates, empty=True)
                tm.that(params.projects, empty=True)
                tm.fail(params.apply)
                tm.ok(params.check_only)
                tm.that(params.ruff_args, eq=None)
                tm.that(params.pyright_args, eq=None)
                candidate = params.repository_root / target.relative_to(root)
                tm.that(candidate.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
                tm.that(target.read_bytes(), eq=before.content)

        previous = sys.getprofile()
        try:
            sys.setprofile(observe)
            rejected = publication.publish_semantic_file_plans(
                (
                    m.Infra.SemanticFilePlan(
                        project=root,
                        path=target,
                        before=before,
                        desired_content=source.encode(c.DEFAULT_ENCODING),
                        desired_mode=before.mode,
                    ),
                ),
                repository_root=root,
            )
        finally:
            sys.setprofile(previous)
        tm.fail(rejected, has="quality checks failed for")
        tm.that(len(commands), eq=1)
        for expected in (
            "FlextInfraUtilitiesProtectedEditLinting.normalize_source_plan",
            "FlextInfraCodegenTransaction.consume_source_runtime",
            "FlextInfraSemanticPublication._check_semantic_sources",
            "FlextInfraWorkspaceChecker.execute_candidate",
            "FlextInfraWorkspaceChecker._execute_payload",
            "FlextInfraWorkspaceChecker.run_projects",
        ):
            tm.ok(expected in calls)
        tm.that(
            calls.index("FlextInfraCodegenTransaction.consume_source_runtime")
            < calls.index("FlextInfraWorkspaceChecker.execute_candidate"),
            eq=True,
        )
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True)),
            eq=before,
        )

    @staticmethod
    def test_no_effect_publication_requires_true_acceptance(
        mod_workspace: Path,
    ) -> None:
        """A successful false result rejects publication without filesystem effects."""
        publication = transformers.FlextInfraSemanticPublication
        before = tuple(
            (path, path.stat().st_mode, path.read_bytes() if path.is_file() else None)
            for path in sorted(mod_workspace.rglob("*"))
        )
        calls = 0
        accepted = False

        def validate(_candidate_root: Path) -> p.Result[bool]:
            nonlocal calls
            calls += 1
            return r[bool].ok(accepted)

        rejected = publication.publish_semantic_file_plans(
            (),
            repository_root=mod_workspace,
            options=m.Infra.SemanticPublicationOptions(validator=validate),
        )
        tm.that(calls, eq=1)
        accepted = True
        published = publication.publish_semantic_file_plans(
            (),
            repository_root=mod_workspace,
            options=m.Infra.SemanticPublicationOptions(validator=validate),
        )
        tm.that(calls, eq=2)
        tm.that(
            tuple(
                (
                    path,
                    path.stat().st_mode,
                    path.read_bytes() if path.is_file() else None,
                )
                for path in sorted(mod_workspace.rglob("*"))
            ),
            eq=before,
        )
        tm.that(tm.ok(published), eq=())
        tm.fail(rejected)

    @staticmethod
    @pytest.mark.parametrize("raises", [False, True])
    def test_no_effect_publication_retains_validator_failure(
        mod_workspace: Path,
        *,
        raises: bool,
    ) -> None:
        """An explicit consumer rejection cannot become a no-effect success."""
        publication = transformers.FlextInfraSemanticPublication
        path = mod_workspace / "consumer.py"
        source = 'raise RuntimeError("consumer rejected")\n'
        path.write_text(source, encoding="utf-8")
        failure = RuntimeError("consumer rejected")

        def reject(candidate_root: Path) -> p.Result[bool]:
            consumer = tm.ok(
                u.Cli.run_raw((
                    sys.executable,
                    str(candidate_root / path.relative_to(mod_workspace)),
                ))
            )
            tm.fail(u.Cli.process_succeeded(consumer.outcome))
            if raises:
                raise failure
            return r[bool].fail(str(failure), exception=failure)

        options = m.Infra.SemanticPublicationOptions(validator=reject)
        if raises:
            with pytest.raises(RuntimeError) as raised:
                publication.publish_semantic_file_plans(
                    (), repository_root=mod_workspace, options=options
                )
            tm.ok(raised.value is failure)
        else:
            rejected = publication.publish_semantic_file_plans(
                (), repository_root=mod_workspace, options=options
            )
            tm.fail(rejected, has=str(failure))
            tm.ok(rejected.exception is failure)
        tm.that(path.read_text(encoding="utf-8"), eq=source)

    @pytest.mark.slow
    @pytest.mark.parametrize("rejected", [False, True])
    def test_unchanged_semantic_entry_validates_generated_public_consumer(
        self,
        tmp_path: Path,
        *,
        rejected: bool,
    ) -> None:
        """An unchanged semantic entry validates the generated public consumer.

        Stale exports cannot be accepted without the entry's gates.

        """
        u.Tests.run_native_callable(
            self._scenario_unchanged_entry,
            tmp_path,
            rejected=rejected,
        )

    @staticmethod
    def _scenario_unchanged_entry(tmp_path: Path, *, rejected: bool) -> None:
        """The real semantic entry cannot accept stale exports without its gates."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.provision_checkout(root)
        notice = u.Infra.copyright_notice(root)
        path = package / "service.py"
        source = (
            f'"""Public candidate service.\n\n{notice}\n"""\n\n'
            "from __future__ import annotations\n\n\n"
            "class FlextTestProjectService:\n"
            '    """Execute the fixture consumer contract."""\n\n'
            "    @staticmethod\n"
            "    def execute() -> bool:\n"
            '        """Return the fixture service health.\n\n'
            "        Returns:\n"
            "            Whether the fixture service is healthy.\n\n"
            '        """\n'
            "        return True\n\n\n"
            + ('raise RuntimeError("consumer rejected")\n\n' if rejected else "")
            + '__all__ = ["FlextTestProjectService"]\n'
        )
        path.write_text(source, encoding="utf-8")
        initializer = package / c.Infra.INIT_PY
        initializer.write_text("", encoding="utf-8")
        original = initializer.read_bytes()
        report: m.Infra.ModOccurrenceReport[m.Infra.ModOccurrence] = (
            m.Infra.ModOccurrenceReport(
                files=frozenset(),
                entries=(),
            )
        )
        with infra.rope_workspace(root) as rope:
            result = codemod.FlextInfraCodemodSemanticApply.apply(
                root,
                report,
                rope,
                source_preview=infra.source_preview(root),
                workspace_factory=infra.rope_workspace,
            )
        if rejected:
            tm.fail(result)
        else:
            tm.ok(result)
        tm.ok(initializer.read_bytes() != original)
        consumer = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {package.name} import FlextTestProjectService; "
                        "assert FlextTestProjectService.execute()"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env={
                        c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(package.parent),
                    },
                ),
            ),
        )
        tm.that(u.Cli.process_succeeded(consumer.outcome), eq=not rejected)
        if rejected:
            tm.that(consumer.stderr, has="consumer rejected")
        tm.that(path.read_text(encoding="utf-8"), eq=source)

    def test_publication_refreshes_warm_normalized_export_route(
        self,
        mod_workspace: Path,
    ) -> None:
        """Publication refreshes the warm normalized export route.

        A moved declaration routes identically in warm and fresh consumers.

        """
        u.Tests.run_native_callable(self._scenario_warm_exports, mod_workspace)

    @staticmethod
    def _scenario_warm_exports(mod_workspace: Path) -> None:
        """A moved declaration routes identically in warm and fresh consumers."""
        package = mod_workspace / c.Infra.DEFAULT_SRC_DIR / mod_workspace.name
        previous = package / "previous.py"
        current = package / "current.py"
        consumer_path = package / "consumer.py"
        for path, exported in ((previous, True), (current, False)):
            path.write_text(
                "class DeclaredService:\n"
                "    @staticmethod\n"
                "    def execute() -> str:\n"
                f"        return {path.stem!r}\n\n"
                f"__all__ = {['DeclaredService'] if exported else []!r}\n",
                encoding=c.DEFAULT_ENCODING,
            )
        tm.ok(
            transformers.FlextInfraSemanticPublication.publish_semantic_file_plans(
                (),
                repository_root=mod_workspace,
                options=m.Infra.SemanticPublicationOptions(
                    projection_roots=(mod_workspace,)
                ),
            ),
        )
        original_source = (
            f"from {package.name}.{previous.stem} import DeclaredService\n\n"
            "def run() -> str:\n"
            "    return DeclaredService.execute()\n"
        )
        warmed = tm.not_none(
            refactor.FlextInfraImportNormalization.normalize_source(
                project_root=mod_workspace,
                file_path=consumer_path,
                source=original_source,
            ),
        )
        tm.that(warmed, has=f"from {package.name} import DeclaredService\n")
        candidate = original_source.replace(previous.stem, current.stem)
        plans: list[m.Infra.SemanticFilePlan] = []
        for path in (previous, current):
            before = tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            outgoing: t.StrSequence = ["DeclaredService"] if path == previous else []
            incoming: t.StrSequence = [] if path == previous else ["DeclaredService"]
            plans.append(
                m.Infra.SemanticFilePlan(
                    project=mod_workspace,
                    path=path,
                    before=before,
                    desired_content=tm
                    .not_none(before.content)
                    .decode(c.DEFAULT_ENCODING)
                    .replace(
                        f"__all__ = {outgoing!r}",
                        f"__all__ = {incoming!r}",
                    )
                    .encode(c.DEFAULT_ENCODING),
                    desired_mode=before.mode,
                ),
            )

        def validate(candidate_root: Path) -> p.Result[bool]:
            candidate_consumer = candidate_root / consumer_path.relative_to(
                mod_workspace
            )
            normalized = tm.not_none(
                refactor.FlextInfraImportNormalization.normalize_source(
                    project_root=candidate_root,
                    file_path=candidate_consumer,
                    source=candidate,
                ),
            )
            tm.that(normalized, eq=warmed)
            tm.that(
                refactor.FlextInfraImportNormalization.normalize_source(
                    project_root=candidate_root,
                    file_path=candidate_consumer,
                    source=normalized,
                ),
                eq=None,
            )
            fresh = tm.ok(
                u.Cli.run(
                    (
                        sys.executable,
                        "-c",
                        (
                            "from pathlib import Path\n"
                            "from flext_infra.refactor import (\n"
                            "    FlextInfraImportNormalization,\n"
                            ")\n"
                            "normalized = FlextInfraImportNormalization"
                            ".normalize_source(\n"
                            f"    project_root=Path({str(candidate_root)!r}),\n"
                            f"    file_path=Path({str(candidate_consumer)!r}),\n"
                            f"    source={candidate!r},\n"
                            ")\n"
                            f"assert normalized == {normalized!r}\n"
                            f"{normalized}\n"
                            f"assert run() == {current.stem!r}\n"
                        ),
                    ),
                    cwd=candidate_root,
                    options=m.Cli.ProcessOptions(
                        env={
                            c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(
                                candidate_root
                                / package.parent.relative_to(mod_workspace)
                            ),
                        },
                    ),
                ),
            )
            tm.ok(u.Cli.process_succeeded(fresh.outcome))
            return r[bool].ok(value=True)

        tm.ok(
            transformers.FlextInfraSemanticPublication.publish_semantic_file_plans(
                plans,
                repository_root=mod_workspace,
                options=m.Infra.SemanticPublicationOptions(
                    projection_roots=(mod_workspace,), validator=validate
                ),
            ),
        )
        initializer = package / c.Infra.INIT_PY
        published = initializer.read_bytes()
        tm.ok(
            transformers.FlextInfraSemanticPublication.publish_semantic_file_plans(
                (),
                repository_root=mod_workspace,
                options=m.Infra.SemanticPublicationOptions(
                    projection_roots=(mod_workspace,), validator=validate
                ),
            ),
        )
        tm.that(initializer.read_bytes(), eq=published)

    @pytest.mark.parametrize("accepted", [False, True])
    def test_projection_only_candidate_validates_real_public_consumer(
        self,
        mod_workspace: Path,
        *,
        accepted: bool,
    ) -> None:
        """A projection-only candidate validates the real public consumer.

        Declared exports are generated without changing authored work in progress.

        """
        u.Tests.run_native_callable(
            self._scenario_projection_consumer,
            mod_workspace,
            accepted=accepted,
        )

    @staticmethod
    def _scenario_projection_consumer(mod_workspace: Path, *, accepted: bool) -> None:
        """Generate declared exports before acceptance without changing authored WIP."""
        publication = transformers.FlextInfraSemanticPublication
        package = mod_workspace / "src" / mod_workspace.name
        declaration = package / "service.py"
        source = "class DeclaredService:\n    pass\n\n__all__ = ['DeclaredService']\n"
        declaration.write_text(source, encoding="utf-8")
        initializer = package / c.Infra.INIT_PY
        initializer.write_text("", encoding="utf-8")
        original = initializer.read_bytes()
        command = (
            sys.executable,
            "-c",
            (
                f"from {mod_workspace.name} import DeclaredService; "
                "assert isinstance(DeclaredService(), DeclaredService)"
            ),
        )
        options = m.Cli.ProcessOptions(
            env={c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(package.parent)},
        )

        def validate(candidate_root: Path) -> p.Result[bool]:
            candidate_options = options.model_copy(
                update={
                    "env": {
                        c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(
                            candidate_root / package.parent.relative_to(mod_workspace)
                        ),
                    },
                },
            )
            consumer = u.Cli.run(
                command,
                cwd=candidate_root,
                options=candidate_options,
            )
            tm.ok(consumer)
            tm.ok(u.Cli.process_succeeded(consumer.value.outcome))
            return (
                r[bool].ok(value=True)
                if accepted
                else r[bool].fail("consumer rejected")
            )

        published = publication.publish_semantic_file_plans(
            (),
            repository_root=mod_workspace,
            options=m.Infra.SemanticPublicationOptions(
                projection_roots=(mod_workspace,), validator=validate
            ),
        )
        if accepted:
            tm.ok(published)
        else:
            tm.fail(published, has="consumer rejected")
        tm.that(initializer.read_bytes() != original, eq=accepted)
        consumer = tm.ok(
            u.Cli.run(command, cwd=mod_workspace, options=options),
        )
        tm.that(u.Cli.process_succeeded(consumer.outcome), eq=accepted)
        tm.that(declaration.read_text(encoding="utf-8"), eq=source)
