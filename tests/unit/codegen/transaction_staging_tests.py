"""Authenticated staging inputs and real public imports before publication.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

import pytest

from flext_infra import c, e, m, p, r
from flext_infra.codegen import (
    FlextInfraMiseArtifactsJournal,
    FlextInfraMiseArtifactsProcess,
    codegen_transaction as transaction,
)
from flext_infra.codegen.mise_artifacts import FlextInfraCodegenMiseArtifacts
from flext_infra.codegen.mise_artifacts_workspace import FlextInfraMiseWorkspacePlanner
from flext_infra.codegen.staged_package import FlextInfraStagedPackage
from flext_infra.transformers import FlextInfraSemanticPublication
from flext_infra.validate import FlextInfraValidateFreshImport
from tests import t, tm, u


class TestsFlextInfraTransactionStaging:
    """Exercise durable staging authority before publishing live destinations."""

    @staticmethod
    @pytest.mark.parametrize("consumer_root", ["tests", "examples", "scripts", "."])
    @pytest.mark.parametrize("missing", [False, True])
    def test_composed_source_preview_consumes_new_transitive_dependencies(
        tmp_path: Path,
        consumer_root: str,
        *,
        missing: bool,
    ) -> None:
        """A real SDK consumes coupled candidate bytes, never the live contract."""
        root = u.Tests.git_repository(tmp_path)
        u.Tests.src_package(
            root,
            "workspace",
            pyproject="[project]\nname = 'workspace'\nversion = '1.0.0'\n",
        )
        packages: dict[str, Path] = {}
        for name in ("receiver", "provider", "dependency"):
            packages[name] = u.Tests.src_package(
                root / name,
                name,
                pyproject=f"[project]\nname = '{name}'\nversion = '1.0.0'\n",
            )
        (root / ".gitmodules").write_text(
            "".join(f'[submodule "{name}"]\n\tpath = {name}\n' for name in packages)
        )
        declaration = packages["receiver"] / "contract.py"
        declaration.write_text("class Contract:\n    def old(self): return 1\n")
        provider = packages["provider"] / "contract.py"
        provider.write_text(
            "from dependency.contract import Parent\nclass Contract(Parent): pass\n"
        )
        dependency = packages["dependency"] / "contract.py"
        dependency.write_text(
            "from pydantic import BaseModel\n"
            "class Parent(BaseModel):\n    value: int = 2\n"
        )
        consumer = root / "receiver" / consumer_root / "consumer.py"
        consumer.parent.mkdir(parents=True, exist_ok=True)
        consumer.write_text(
            "from receiver.contract import Contract\nassert Contract().old() == 1\n"
        )
        originals = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in (declaration, consumer, provider, dependency)
        )
        updates = {
            declaration: (
                "from provider.contract import Contract\n"
                + ("import missing_candidate_dependency\n" if missing else "")
            ),
            consumer: (
                "from receiver.contract import Contract\nassert Contract().value == 2\n"
                + ("import missing_candidate_dependency\n" if missing else "")
            ),
        }
        plan = tm.ok(
            FlextInfraStagedPackage.plan_sources(root, updates, inputs=originals[:2])
        )
        tm.that({layout.package_name for layout in plan.layouts}, eq=set(packages))
        owner = transaction.FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )

        def consume(view_root: Path, candidates: t.MappingKV[Path, Path]) -> bool:
            interpreter = u.Infra.runtime_python(Path(__file__).resolve().parents[3])
            bindings = tuple(
                (name, str(view_root / package.relative_to(root) / "__init__.py"))
                for name, package in packages.items()
            )
            code = (
                "import importlib.util, runpy, sys\n"
                f"for name, path in {bindings!r}:\n"
                "    spec = importlib.util.spec_from_file_location(name, path)\n"
                "    module = importlib.util.module_from_spec(spec)\n"
                "    sys.modules[name] = module\n"
                "    spec.loader.exec_module(module)\n"
                f"runpy.run_path({str(candidates[consumer])!r})\n"
            )
            result = tm.ok(
                u.Cli.run_raw(
                    [str(interpreter), "-I", "-B", "-W", "error", "-"],
                    cwd=view_root,
                    options=m.Cli.ProcessOptions(
                        input_data=code,
                        remove_env_keys=(c.Infra.ORCHESTRATOR_ENV_PYTHONPATH,),
                    ),
                )
            )
            if missing:
                tm.that(result.stderr, has="missing_candidate_dependency")
            else:
                tm.that(
                    u.Cli.process_succeeded(result.outcome), eq=True, msg=result.stderr
                )
            return u.Cli.process_succeeded(result.outcome)

        outcome = owner.preview_sources(
            root,
            updates,
            consume,
            inputs=plan.inputs,
            runtime_root=Path(__file__).resolve().parents[3],
        )
        if missing:
            tm.fail(outcome, has="missing_candidate_dependency")
        else:
            tm.that(tm.ok(outcome), eq=True)
        for before in originals:
            tm.that(
                tm.ok(u.Cli.atomic_read_binary_file_state(before.path, required=True)),
                eq=before,
            )

    @staticmethod
    def test_source_runtime_rejects_live_package_origin_before_checks(
        tmp_path: Path,
    ) -> None:
        """A candidate cannot redirect its package path to unchanged live sources."""
        root = u.Tests.git_repository(tmp_path)
        package = u.Tests.src_package(
            root,
            "sample",
            pyproject="[project]\nname = 'sample'\nversion = '1.0.0'\n",
        )
        target = package / "__init__.py"
        (package / "contract.py").write_text("VALUE = 1\n")
        before = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
        owner = transaction.FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )

        def checks(_view_root: Path, _candidates: t.MappingKV[Path, Path]) -> bool:
            pytest.fail("checks ran before candidate runtime rejection")

        outcome = owner.preview_sources(
            root,
            {target: f"__path__ = [{str(package)!r}]\n"},
            checks,
            inputs=(before,),
            runtime_root=Path(__file__).resolve().parents[3],
        )
        tm.fail(outcome, has="unsealed candidate origin")
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True)),
            eq=before,
        )

    @staticmethod
    @pytest.mark.parametrize("mutation", ["changed", "added", "candidate"])
    def test_source_preview_rejects_validation_drift_before_publication(
        tmp_path: Path,
        mutation: str,
    ) -> None:
        """Keep shared source changes while rejecting stale acceptance receipts."""
        root = u.Tests.git_repository(tmp_path)
        package = u.Tests.src_package(
            root,
            "sample",
            pyproject="[project]\nname = 'sample'\nversion = '1.0.0'\n",
        )
        target = package / "contract.py"
        target.write_text("VALUE = 1\n")
        before = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
        owner = transaction.FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )

        def validate(view_root: Path, candidates: t.MappingKV[Path, Path]) -> bool:
            if mutation == "changed":
                target.write_text("VALUE = 3\n")
            elif mutation == "added":
                (package / "shared.py").write_text("VALUE = 3\n")
            else:
                tm.that(candidates[target].is_relative_to(view_root), eq=True)
                candidates[target].write_text("VALUE = 3\n")
            return True

        tm.fail(
            owner.preview_sources(
                root, {target: "VALUE = 2\n"}, validate, inputs=(before,)
            )
        )
        tm.that(
            target.read_text(),
            eq="VALUE = 3\n" if mutation == "changed" else "VALUE = 1\n",
        )
        tm.that((package / "shared.py").exists(), eq=mutation == "added")

    @staticmethod
    def test_source_preview_rejects_reobserved_original_identity(
        tmp_path: Path,
    ) -> None:
        """A fresh read cannot replace the caller's original source authority."""
        root = u.Tests.git_repository(tmp_path)
        package = u.Tests.src_package(
            root,
            "sample",
            pyproject="[project]\nname = 'sample'\nversion = '1.0.0'\n",
        )
        target = package / "contract.py"
        target.write_text("VALUE = 1\n")
        before = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
        target.write_text("VALUE = 3\n")
        tm.fail(
            FlextInfraStagedPackage.plan_sources(
                root, {target: "VALUE = 2\n"}, inputs=(before,)
            ),
            has="original source identity changed",
        )
        tm.that(target.read_text(), eq="VALUE = 3\n")

    @staticmethod
    def test_footprint_authorization_observes_the_serialized_current_journal(
        tmp_path: Path,
    ) -> None:
        """An independent writer's progress cannot invalidate an earlier observation."""
        root = u.Tests.git_repository(tmp_path)
        artifacts = FlextInfraCodegenMiseArtifacts(repository_root=root)
        writer = transaction.FlextInfraCodegenTransaction(artifacts)
        reader = transaction.FlextInfraCodegenTransaction(
            artifacts,
            participant_policy=m.Infra.CodegenParticipantPolicy(
                scope_root=root,
                roots=(tm.ok(u.Cli.atomic_plan_directory_chain(root)),),
            ),
        )
        previous = tm.ok(reader.inspect_journal())
        target = root / "concurrent.md"
        target.write_bytes(b"before\n")
        before = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
        roots = {"@docs-0": root}
        prepared = Event()
        observing = Event()
        finish = Event()

        def publish(scope_root: Path) -> p.Result[m.Infra.CodegenTransactionSession]:
            session = tm.ok(writer.begin_files_locked(scope_root, roots, (before,)))
            plan = m.Infra.CodegenFilePlan(
                project=root,
                path=target,
                before=before,
                desired_content=b"accepted progress\n",
                desired_mode=before.mode,
                owner="docs",
            )
            advanced = writer.append_phase_locked(session, "docs", (plan,))
            tm.ok(advanced)
            prepared.set()
            if not finish.wait(c.Infra.TIMEOUT_SHORT):
                pytest.fail("concurrent journal writer was not released")
            return advanced

        def observe() -> p.Result[m.Infra.CodegenFootprint]:
            observing.set()
            return reader.validate_footprint(previous)

        with ThreadPoolExecutor(max_workers=2) as executor:
            writing = executor.submit(writer.run_files_locked, roots, publish)
            try:
                if not prepared.wait(c.Infra.TIMEOUT_SHORT):
                    pytest.fail("concurrent journal writer did not prepare")
                reading = executor.submit(observe)
                if not observing.wait(c.Infra.TIMEOUT_SHORT):
                    pytest.fail("concurrent journal observer did not start")
            finally:
                finish.set()
            session = tm.ok(writing.result())
            current = tm.ok(reading.result())

        tm.that(current.transaction_id, eq=session.journal.transaction_id)
        tm.that(current.snapshot, eq=session.journal_state)
        tm.that(target.read_bytes(), eq=b"accepted progress\n")
        tm.ok(
            writer.run_files_locked(
                roots,
                lambda _scope: r[bool].ok(value=True),
            ),
        )
        tm.that(target.read_bytes(), eq=b"accepted progress\n")

    @staticmethod
    @pytest.mark.parametrize("mutation", ["content", "inode", "unchanged"])
    def test_semantic_commit_preserves_external_changes_after_publication(
        tmp_path: Path,
        mutation: str,
    ) -> None:
        """Settle publication without treating later external edits as failure."""
        root = u.Tests.git_repository(tmp_path)
        target = root / "sample.py"
        target.write_bytes(b"value = 1\n")
        before = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
        desired = b"value = 2\n"
        plan = m.Infra.SemanticFilePlan(
            project=root,
            path=target,
            before=before,
            desired_content=desired,
            desired_mode=before.mode,
            changes=("semantic migration",),
        )

        def validate() -> p.Result[bool]:
            published = tm.ok(
                u.Cli.atomic_read_binary_file_state(target, required=True),
            )
            tm.that(published.content, eq=desired)
            if mutation == "content":
                target.write_bytes(b"value = 3\n")
            elif mutation == "inode":
                assert published.mode is not None
                tm.ok(
                    u.Cli.atomic_write_binary_file_guarded(
                        published,
                        desired,
                        permission_mode=published.mode,
                    ),
                )
            return r[bool].ok(value=True)

        outcome = FlextInfraSemanticPublication.publish_semantic_file_plans(
            (plan,),
            repository_root=root,
            validator=validate,
        )
        tm.ok(outcome)
        tm.that(
            target.read_bytes(),
            eq=b"value = 3\n" if mutation == "content" else desired,
        )

    @staticmethod
    @pytest.mark.parametrize("inside", [False, True])
    @pytest.mark.parametrize("boundary", ["managed", "file"])
    @pytest.mark.parametrize("state", ["staging", "prepared", "committed"])
    def test_request_authorization_preserves_foreign_pending_journal(
        tmp_path: Path,
        boundary: str,
        state: str,
        *,
        inside: bool,
    ) -> None:
        """Reject undeclared capabilities without recovery or publication."""
        root = u.Tests.git_repository(tmp_path / "source")
        foreign = root / "undeclared" if inside else tmp_path / "foreign"
        foreign.mkdir()
        marker = foreign / "unknown-wip.bin"
        marker.write_bytes(b"preserve unrelated work")
        marker_before = tm.ok(
            u.Cli.atomic_read_binary_file_state(marker, required=True)
        )
        mise_owner = FlextInfraCodegenMiseArtifacts(repository_root=root)
        planner = FlextInfraMiseWorkspacePlanner(mise_owner)
        layout = tm.ok(
            planner.file_layout(root, {"@foreign-0": foreign}, transaction_id="d" * 32),
        )
        journal = tm.ok(
            FlextInfraMiseArtifactsJournal.begin(
                m.Infra.CodegenFileSessionPlan(layout=layout),
                transaction_id=tm.not_none(layout.transaction_id),
            ),
        )
        recorded = m.Infra.CodegenTransactionJournal.model_validate({
            **journal.model_dump(),
            "state": state,
        })
        before = tm.ok(
            FlextInfraMiseArtifactsJournal.write(
                layout,
                recorded,
                expected=tm.ok(
                    u.Cli.atomic_read_binary_file_state(
                        layout.journal_path,
                        required=False,
                    ),
                ),
            ),
        )
        owner = transaction.FlextInfraCodegenTransaction(
            mise_owner,
            participant_policy=m.Infra.CodegenParticipantPolicy(
                scope_root=root,
                roots=(tm.ok(u.Cli.atomic_plan_directory_chain(root)),),
            ),
        )
        observed = tm.ok(owner.inspect_journal())
        tm.that(observed.pending_roots, eq=(foreign,))
        tm.that(observed.journal_state, eq=state)

        def publish_unapproved(scope_root: Path) -> p.Result[bool]:
            """Exercise a real destination effect if authorization wrongly grants it.

            Returns:
                The actual publication outcome.
            """
            return u.Cli.atomic_write_text_file(
                scope_root / "unauthorized.txt",
                "unapproved publication\n",
            )

        if boundary == "managed":
            result = owner.run_locked(
                prepare=True,
                operation=publish_unapproved,
            )
        else:
            result = owner.run_files_locked(
                {"@current-0": root},
                publish_unapproved,
            )

        tm.fail(result, has="outside authorized roots")
        tm.that(
            tm.ok(
                u.Cli.atomic_read_binary_file_state(
                    layout.journal_path,
                    required=True,
                ),
            ),
            eq=before,
        )
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(marker, required=True)),
            eq=marker_before,
        )
        tm.that((root / "unauthorized.txt").exists(), eq=False)
        tm.that((foreign / c.Infra.TRANSACTION_STATE_DIRNAME).exists(), eq=False)
        tm.that((root / c.Infra.TRANSACTION_STATE_DIRNAME).exists(), eq=False)

    @staticmethod
    def test_effect_free_inspection_preserves_corrupt_journal(tmp_path: Path) -> None:
        """Preserve the original parser failure without creating recovery state."""
        root = u.Tests.git_repository(tmp_path)
        owner = transaction.FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        absent = tm.ok(owner.inspect_journal())
        tm.that(absent.journal_state, eq="absent")
        tm.that(absent.journal_path.exists(), eq=False)
        tm.ok(
            u.Cli.atomic_write_binary_file_guarded(
                absent.snapshot,
                b"invalid journal",
                permission_mode=c.Infra.JOURNAL_MODE,
            ),
        )
        corrupted = tm.ok(
            u.Cli.atomic_read_binary_file_state(absent.journal_path, required=True),
        )
        with pytest.raises(e.PydanticValidationError):
            owner.inspect_journal()
        tm.that(
            tm.ok(
                u.Cli.atomic_read_binary_file_state(
                    absent.journal_path,
                    required=True,
                ),
            ),
            eq=corrupted,
        )
        tm.that((root / c.Infra.TRANSACTION_STATE_DIRNAME).exists(), eq=False)

    @staticmethod
    def test_injected_root_authorization_permits_owned_recovery(
        tmp_path: Path,
    ) -> None:
        """The bound permits a genuine requested-root journal and cleanup."""
        root = u.Tests.git_repository(tmp_path)
        owner = transaction.FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
            participant_policy=m.Infra.CodegenParticipantPolicy(
                scope_root=root,
                roots=(tm.ok(u.Cli.atomic_plan_directory_chain(root)),),
            ),
        )
        roots = {"@current-0": root}
        session = tm.ok(
            owner.run_files_locked(
                roots,
                lambda scope: owner.begin_files_locked(scope, roots, ()),
            ),
        )
        tm.ok(
            owner.run_locked(
                prepare=True,
                operation=lambda _scope: r[bool].ok(value=True),
            ),
        )
        tm.that(session.plan.layout.journal_path.exists(), eq=False)

    @staticmethod
    @pytest.mark.parametrize(
        "phase",
        [
            c.Infra.CodegenStagedFilePhase.CONFORM,
            c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP,
        ],
    )
    @pytest.mark.parametrize("content", [b"", b"obsolete generated document\n"])
    def test_planned_deletion_publishes_without_a_success_none_payload(
        tmp_path: Path,
        content: bytes,
        phase: c.Infra.CodegenStagedFilePhase,
    ) -> None:
        """A journaled deletion has no replacement but a valid result receipt."""
        root = u.Tests.git_repository(tmp_path)
        target = root / "obsolete.md"
        target.write_bytes(content)
        before = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
        owner = transaction.FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
            participant_policy=m.Infra.CodegenParticipantPolicy(
                scope_root=root,
                roots=(tm.ok(u.Cli.atomic_plan_directory_chain(root)),),
            ),
        )
        roots = {"@docs-0": root}

        def publish(scope_root: Path) -> p.Result[t.VariadicTuple[Path]]:
            return owner.publish_file_phase_locked(
                scope_root,
                roots,
                m.Infra.CodegenPhaseAnalysis(
                    phase=phase,
                    inputs=(before,),
                    files=(
                        m.Infra.CodegenFilePlan(
                            project=root,
                            path=target,
                            before=before,
                            desired_content=None,
                            desired_mode=None,
                            owner="docs",
                        ),
                    ),
                ),
                m.Infra.CodegenPhasePublicationPolicy(
                    directories=(),
                    validator=lambda: r[bool].ok(value=True),
                ),
            )

        tm.ok(owner.run_files_locked(roots, publish))
        tm.that(target.exists(), eq=False)

    @staticmethod
    @pytest.mark.parametrize(
        "phase",
        [
            c.Infra.CodegenStagedFilePhase.CONFORM,
            c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP,
        ],
    )
    @pytest.mark.parametrize("scenario", ["valid", "stale-origin", "tampered"])
    def test_staged_package_public_import_precedes_publication(
        tmp_path: Path,
        scenario: str,
        phase: c.Infra.CodegenStagedFilePhase,
    ) -> None:
        """Consume isolated real modules; reject old origins and changed bytes."""
        root = u.Tests.git_repository(tmp_path)
        package = root / "src" / "stage_sample"
        (package / "_typings").mkdir(parents=True)
        target = package / "typings.py"
        target.write_text("class SampleTypes: pass\nt = SampleTypes\n")
        initializer = "from .typings import SampleTypes, t\n"
        if scenario == "stale-origin":
            initializer = f"__path__ = [{str(package)!r}]\n" + initializer
        (package / "__init__.py").write_text(initializer)
        (package / "_typings" / "__init__.py").write_text("")
        (package / "base.py").write_text("class BaseTypes: pass\n")
        (package / "_typings" / "types.py").write_text(
            "from stage_sample.base import BaseTypes\n"
            "class SampleTypes(BaseTypes):\n    class Namespace: pass\n",
        )
        before = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
        states = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in sorted(package.rglob("*.py"))
        )
        layout = m.Infra.RopeProjectLayout(
            project_root=root,
            project_name="stage-sample",
            package_name="stage_sample",
            package_alias="sample",
            class_stem="Sample",
            src_dir=root / "src",
            package_dir=package,
            init_path=package / "__init__.py",
        )
        stage_plan = m.Infra.StagePackagePlan(
            package="stage_sample",
            module="stage_sample.typings",
            classname="SampleTypes",
            owner_module="stage_sample._typings.types",
            upstream=(("stage_sample.base", "BaseTypes"),),
            members=("Namespace",),
            layouts=(layout,),
            inputs=states,
            workspace_packages=("stage_sample",),
        )
        desired = (
            b"from stage_sample._typings.types import SampleTypes as _SampleTypes\n"
            b"class SampleTypes(_SampleTypes): pass\nt = SampleTypes\n"
        )
        owner = transaction.FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root)
        )
        roots = {"@sample-0": root}

        def publish(scope_root: Path) -> p.Result[t.VariadicTuple[Path]]:
            analysis = m.Infra.CodegenPhaseAnalysis(
                phase=phase,
                inputs=states,
                files=(
                    m.Infra.CodegenFilePlan(
                        project=root,
                        path=target,
                        before=before,
                        desired_content=desired,
                        desired_mode=before.mode,
                        source_states=states,
                        owner="sample",
                    ),
                ),
            )

            def staged(
                session: m.Infra.CodegenTransactionSession,
                publications: t.VariadicTuple[m.Infra.CodegenStagedFile],
            ) -> p.Result[m.Infra.CodegenTransactionSession]:
                tm.that(publications[0].phase, eq=phase)
                materialized = owner.materialize_package_view_locked(
                    session, stage_plan, publications[0]
                )
                if materialized.failure:
                    return r[m.Infra.CodegenTransactionSession].from_failure(
                        materialized
                    )
                current, view = materialized.value
                tm.that(
                    tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True)),
                    eq=before,
                )
                if scenario == "tampered":
                    snapshot = tm.ok(
                        u.Cli.atomic_read_binary_file_state(
                            view.target.path, required=True
                        )
                    )
                    assert snapshot.mode is not None
                    tm.ok(
                        u.Cli.atomic_write_binary_file_guarded(
                            snapshot,
                            b"changed candidate\n",
                            permission_mode=snapshot.mode,
                        )
                    )
                verified = FlextInfraValidateFreshImport(
                    repository_root=Path(__file__).resolve().parents[3],
                    runtime_root=None,
                ).validate_stage_view(view, current)
                if verified.failure:
                    return r[m.Infra.CodegenTransactionSession].from_failure(verified)
                return r[m.Infra.CodegenTransactionSession].ok(current)

            return owner.publish_file_phase_locked(
                scope_root,
                roots,
                analysis,
                m.Infra.CodegenPhasePublicationPolicy(
                    directories=(),
                    validator=lambda: r[bool].ok(value=True),
                ),
                staged_validator=staged,
            )

        outcome = owner.run_files_locked(roots, publish)
        if scenario == "valid":
            tm.ok(outcome)
            tm.that(target.read_bytes(), eq=desired)
        else:
            tm.fail(outcome)
            tm.that(
                tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True)),
                eq=before,
            )

    @staticmethod
    @pytest.mark.parametrize("materialized", [False, True])
    @pytest.mark.parametrize("relocated", [False, True])
    def test_write_ahead_intentions_recover_before_physical_finalization(
        tmp_path: Path,
        *,
        materialized: bool,
        relocated: bool,
    ) -> None:
        """Retire declared desired staging without changing unpublished live bytes."""
        root = u.Tests.git_repository(tmp_path)
        target = root / "generated.md"
        target.write_bytes(b"original document\n")
        original = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
        owner = transaction.FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = {"@docs-0": root}

        def interrupted(
            scope_root: Path,
        ) -> p.Result[m.Infra.CodegenTransactionSession]:
            session = tm.ok(owner.begin_files_locked(scope_root, roots, ()))
            planned = m.Infra.CodegenFilePlan(
                project=root,
                path=target,
                before=original,
                desired_content=b"generated document\n",
                desired_mode=original.mode,
                owner="docs",
            )
            prepared = tm.ok(
                owner.prepare_phase_staging_locked(session, "docs", (planned,)),
            )
            durable, durable_state = tm.ok(
                FlextInfraMiseArtifactsJournal.read(prepared.plan.layout),
            )
            tm.that(durable, eq=prepared.journal)
            tm.that(durable_state, eq=prepared.journal_state)
            tm.that(durable.entries, eq=())
            tm.that(
                all(intent.created is None for intent in durable.staging_intents),
                eq=True,
            )
            payloads = (planned.desired_content,)
            tm.that(len(durable.staging_intents), eq=len(payloads))
            created_count = len(durable.staging_intents) if materialized else 0
            for intent, content in zip(
                durable.staging_intents[:created_count],
                payloads[:created_count],
                strict=True,
            ):
                assert content is not None
                tm.ok(
                    u.Cli.atomic_write_binary_file_guarded(
                        intent.before,
                        content,
                        permission_mode=intent.mode,
                    ),
                )
            return r[m.Infra.CodegenTransactionSession].ok(prepared)

        prepared = tm.ok(owner.run_files_locked(roots, interrupted))
        transaction_root = prepared.plan.layout.file_participants[0].transaction_root
        assert transaction_root is not None
        tm.that(transaction_root.exists(), eq=True)
        if relocated:
            previous_root = root
            root = root.with_name("relocated-repository")
            previous_root.rename(root)
            transaction_root = root / transaction_root.relative_to(previous_root)
            target = root / target.relative_to(previous_root)
            original = original.model_copy(update={"path": target})
            roots = {"@docs-0": root}
            owner = transaction.FlextInfraCodegenTransaction(
                FlextInfraCodegenMiseArtifacts(repository_root=root),
            )
            # Exercise the existing physical relocation/CAS boundary before the
            # normal file lease consumes its current participant capabilities.
            layout = tm.ok(
                FlextInfraMiseWorkspacePlanner(
                    FlextInfraCodegenMiseArtifacts(repository_root=root),
                ).file_layout(
                    root,
                    roots,
                    transaction_id=prepared.journal.transaction_id,
                ),
            )
            rebound, journal_state = tm.ok(FlextInfraMiseArtifactsJournal.read(layout))
            tm.ok(
                FlextInfraMiseArtifactsJournal.write(
                    layout,
                    rebound,
                    expected=journal_state,
                ),
            )
        tm.ok(owner.run_files_locked(roots, r[Path].ok))
        tm.that(transaction_root.exists(), eq=False)
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True)),
            eq=original,
        )

    @staticmethod
    def test_pending_intention_does_not_authorize_different_bytes(
        tmp_path: Path,
    ) -> None:
        """Preserve mismatched staging bytes instead of adopting a new inventory."""
        root = u.Tests.git_repository(tmp_path)
        target = root / "generated.md"
        owner = transaction.FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = {"@docs-0": root}

        def interrupted(scope_root: Path) -> p.Result[Path]:
            session = tm.ok(owner.begin_files_locked(scope_root, roots, ()))
            planned = m.Infra.CodegenFilePlan(
                project=root,
                path=target,
                before=tm.ok(
                    u.Cli.atomic_read_binary_file_state(target, required=False),
                ),
                desired_content=b"declared document\n",
                desired_mode=session.journal_state.mode,
                owner="docs",
            )
            prepared = tm.ok(
                owner.prepare_phase_staging_locked(session, "docs", (planned,)),
            )
            intent = prepared.journal.staging_intents[0]
            tm.ok(
                u.Cli.atomic_write_binary_file_guarded(
                    intent.before,
                    b"not the declared bytes\n",
                    permission_mode=intent.mode,
                ),
            )
            return r[Path].ok(intent.before.path)

        staging_path = tm.ok(owner.run_files_locked(roots, interrupted))
        before = tm.ok(u.Cli.atomic_read_binary_file_state(staging_path, required=True))
        tm.fail(owner.run_files_locked(roots, r[Path].ok), has="intention")
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(staging_path, required=True)),
            eq=before,
        )
        tm.that(target.exists(), eq=False)

    @staticmethod
    @pytest.mark.parametrize("index", [0, 1])
    @pytest.mark.parametrize("substitution", ["leaf", "parent"])
    def test_staging_write_binds_durable_absence_and_parent(
        tmp_path: Path,
        index: int,
        substitution: str,
    ) -> None:
        """Reject substitution after intention instead of rereading new authority."""
        root = u.Tests.git_repository(tmp_path)
        targets = (root / "generated.md", root / "second-generated.md")
        for target, content in zip(
            targets,
            (b"original document\n", b"second original document\n"),
            strict=True,
        ):
            target.write_bytes(content)
        originals = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
            for target in targets
        )
        owner = transaction.FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = {"@docs-0": root}

        def substituted(scope_root: Path) -> p.Result[bool]:
            session = tm.ok(owner.begin_files_locked(scope_root, roots, ()))
            planned = tuple(
                m.Infra.CodegenFilePlan(
                    project=root,
                    path=target,
                    before=original,
                    desired_content=desired,
                    desired_mode=original.mode,
                    owner="docs",
                )
                for target, original, desired in zip(
                    targets,
                    originals,
                    (b"generated document\n", b"second generated document\n"),
                    strict=True,
                )
            )
            prepared = tm.ok(
                owner.prepare_phase_staging_locked(session, "docs", planned),
            )
            tm.that(len(prepared.journal.staging_intents), eq=len(planned))
            intent = prepared.journal.staging_intents[index]
            path = intent.before.path
            if substitution == "parent":
                path.parent.rename(
                    path.parent.with_name(f"preserved-{path.parent.name}"),
                )
                path.parent.mkdir()
            else:
                path.write_bytes(b"foreign leaf\n")
            tampered = tm.ok(u.Cli.atomic_read_binary_file_state(path, required=False))
            content = planned[index].desired_content
            assert content is not None
            failed = FlextInfraMiseArtifactsProcess.write_new(
                path,
                content,
                intent.mode,
                intent=intent,
            )
            tm.fail(failed)
            tm.that(
                tm.ok(u.Cli.atomic_read_binary_file_state(path, required=False)),
                eq=tampered,
            )
            for target, original in zip(targets, originals, strict=True):
                tm.that(
                    tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True)),
                    eq=original,
                )
            return r[bool].ok(value=True)

        tm.ok(owner.run_files_locked(roots, substituted))
