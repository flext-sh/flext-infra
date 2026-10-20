"""Authenticated staging inputs and real public imports before publication.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from typing import Literal

import pytest

from flext_infra import infra
from flext_infra.codegen import (
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenStaging,
    FlextInfraMiseArtifactsJournal,
    FlextInfraMiseArtifactsProcess,
    FlextInfraMiseWorkspacePlanner,
    FlextInfraStagedPackage,
    codegen_transaction as transaction,
)
from flext_infra.transformers import FlextInfraSemanticPublication
from flext_infra.validate import FlextInfraValidateFreshImport
from tests import c, e, m, p, r, t, tm, u


class TestsFlextInfraTransactionStaging:
    """Exercise durable staging authority before publishing live destinations."""

    @staticmethod
    def test_participant_policy_view_retains_native_root_authority(
        tmp_path: Path,
    ) -> None:
        """The typed policy boundary retains the original physical proof object."""
        native = tm.ok(u.Cli.atomic_plan_directory_chain(tmp_path))
        policy: p.Infra.CodegenParticipantPolicy = m.Infra.CodegenParticipantPolicy(
            scope_root=native.target,
            roots=(native,),
        )
        result: p.Result[p.Infra.CodegenParticipantPolicy] = r[
            p.Infra.CodegenParticipantPolicy
        ].ok(policy)

        tm.ok(isinstance(result.value, p.Infra.CodegenParticipantPolicy))
        tm.that(
            isinstance(result.value.roots[0], p.Infra.CodegenParticipantRoot),
            eq=True,
        )
        tm.that(result.value.scope_root, eq=native.target)
        tm.ok(result.value.roots[0] is native)

    @staticmethod
    def test_capability_roots_bind_through_the_file_participant_contract(
        tmp_path: Path,
    ) -> None:
        """Roots keyed by the transaction's selector owner bind every participant.

        A caller that keyed roots by a repository name instead of the owner's
        selector grammar failed participant validation during ``make gen``.
        """
        root = u.Tests.git_repository(tmp_path / "flext-demo")
        member = root / "flext-demo-member"
        member.mkdir()
        roots = transaction.FlextInfraCodegenTransaction.capability_roots(
            "lazy-init",
            (root, member),
        )
        layout = tm.ok(
            FlextInfraMiseWorkspacePlanner(
                FlextInfraCodegenMiseArtifacts(repository_root=root),
            ).file_layout(root, roots, transaction_id="e" * 32),
        )
        tm.that(
            {item.selector: item.root for item in layout.file_participants},
            eq=dict(roots),
        )

    @staticmethod
    def test_missing_required_member_manifest_rejects_source_planning(
        tmp_path: Path,
    ) -> None:
        """Missing mandatory Python input cannot become a native-member exemption."""
        root = u.Tests.git_repository(tmp_path)
        package = u.Tests.src_package(
            root,
            "preview_receiver",
            pyproject="[project]\nname = 'preview-receiver'\nversion = '1.0.0'\n",
        )
        receiver = package / "__init__.py"
        receiver.write_text("VALUE = 1\n", encoding=c.DEFAULT_ENCODING)
        missing = root / "required-member"
        missing.mkdir()
        (root / c.Infra.GITMODULES).write_text(
            '[submodule "required-member"]\n\tpath = required-member\n',
            encoding=c.DEFAULT_ENCODING,
        )
        before = receiver.read_bytes()

        result = FlextInfraStagedPackage.plan_sources(
            root,
            {receiver: "VALUE = 2\n"},
        )

        tm.fail(result, has=str(missing / c.PYPROJECT_FILENAME))
        tm.that(receiver.read_bytes(), eq=before)
        tm.fail((missing / c.PYPROJECT_FILENAME).exists())

    @staticmethod
    @pytest.mark.parametrize(
        ("policy", "manifest_present"),
        [
            ("unmanaged", False),
            ("native", False),
            ("unmanaged", True),
            ("native", True),
            ("read-only", True),
        ],
    )
    def test_dependency_closure_is_independent_of_generation_applicability(
        tmp_path: Path,
        policy: str,
        manifest_present: bool,
    ) -> None:
        """Real Python providers remain importable beside declared native members."""
        root = u.Tests.git_repository(tmp_path)
        receiver_package = u.Tests.src_package(
            root,
            "preview_receiver",
            pyproject="[project]\nname = 'preview-receiver'\nversion = '1.0.0'\n",
        )
        provider_root = root / "provider"
        provider_package = u.Tests.src_package(
            provider_root,
            "preview_provider",
            pyproject="[project]\nname = 'preview-provider'\nversion = '1.0.0'\n",
        )
        receiver = receiver_package / "__init__.py"
        receiver.write_text(
            "from preview_provider import VALUE\ndef read():\n    return VALUE\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (provider_package / "__init__.py").write_text(
            "VALUE = 7\n",
            encoding=c.DEFAULT_ENCODING,
        )
        participant = provider_root if manifest_present else root / "native-member"
        participant.mkdir(exist_ok=True)
        declarations = '[submodule "provider"]\n\tpath = provider\n'
        if not manifest_present:
            declarations += '[submodule "native-member"]\n\tpath = native-member\n'
        if policy == "unmanaged":
            declarations += "\tflext-managed = false\n"
        else:
            directory = participant / c.Infra.CODEGEN_CONFIG_DIR
            directory.mkdir()
            declaration = "codegen: none" if policy == "native" else "read_only: true"
            (directory / "codegen.yaml").write_text(
                f"Infra:\n  codegen:\n    repository:\n      {declaration}\n",
                encoding=c.DEFAULT_ENCODING,
            )
        (root / c.Infra.GITMODULES).write_text(
            declarations,
            encoding=c.DEFAULT_ENCODING,
        )
        before = receiver.read_bytes()
        provider_before = (provider_root / c.PYPROJECT_FILENAME).read_bytes()
        desired = receiver.read_text(encoding=c.DEFAULT_ENCODING) + "\n"

        planned = tm.ok(
            FlextInfraStagedPackage.plan_sources(
                root,
                {receiver: desired},
            ),
        )

        tm.that(planned.updates[receiver], eq=desired)
        tm.that(
            {layout.package_name for layout in planned.layouts},
            eq={"preview_receiver", "preview_provider"},
        )
        bindings = tuple(
            (layout.package_name, str(layout.init_path)) for layout in planned.layouts
        )
        code = (
            "import importlib.util, sys\n"
            f"bindings = {bindings!r}\n"
            "for name, path in reversed(bindings):\n"
            "    spec = importlib.util.spec_from_file_location(name, path)\n"
            "    module = importlib.util.module_from_spec(spec)\n"
            "    sys.modules[name] = module\n"
            "    spec.loader.exec_module(module)\n"
            "import preview_receiver\n"
            "assert preview_receiver.read() == 7\n"
        )
        tm.ok(
            u.Cli.run_checked(
                [sys.executable, "-I", "-c", code],
                cwd=tmp_path,
            ),
        )
        tm.that(receiver.read_bytes(), eq=before)
        tm.that(
            (provider_root / c.PYPROJECT_FILENAME).read_bytes(),
            eq=provider_before,
        )
        if not manifest_present:
            tm.fail((participant / c.PYPROJECT_FILENAME).exists())

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
            FlextInfraStagedPackage.plan_sources(
                root, updates, options=m.Infra.StageSourceOptions(inputs=originals[:2])
            )
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
            options=m.Infra.CodegenSourcePreviewOptions(
                inputs=plan.inputs,
                runtime_root=u.Infra.runtime_environment_dir(
                    Path(__file__).resolve().parents[3]
                ).parent,
            ),
        )
        if missing:
            tm.fail(outcome, has="missing_candidate_dependency")
        else:
            tm.ok(tm.ok(outcome))
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
            options=m.Infra.CodegenSourcePreviewOptions(
                inputs=(before,),
                runtime_root=u.Infra.runtime_environment_dir(
                    Path(__file__).resolve().parents[3]
                ).parent,
            ),
        )
        tm.fail(outcome, has="unsealed candidate origin")
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True)),
            eq=before,
        )

    @staticmethod
    @pytest.mark.parametrize("borrowed", [False, True])
    def test_source_runtime_rejects_borrowed_environment_before_checks(
        tmp_path: Path,
        *,
        borrowed: bool,
    ) -> None:
        """Neither a linked environment nor a borrowed interpreter owns this runtime."""
        root = u.Tests.git_repository(tmp_path)
        package = u.Tests.src_package(
            root,
            "sample",
            pyproject="[project]\nname = 'sample'\nversion = '1.0.0'\n",
        )
        target = package / "contract.py"
        target.write_text("VALUE = 1\n")
        before = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
        if borrowed:
            u.Tests.provision_checkout(root)
        else:
            u.Infra.runtime_environment_dir(root).symlink_to(
                u.Infra.runtime_environment_dir(Path(__file__).resolve().parents[3]),
                target_is_directory=True,
            )

        def checks(_view_root: Path, _candidates: t.MappingKV[Path, Path]) -> bool:
            pytest.fail("checks ran before candidate runtime rejection")

        outcome = transaction.FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        ).preview_sources(
            root,
            {target: "VALUE = 2\n"},
            checks,
            options=m.Infra.CodegenSourcePreviewOptions(
                inputs=(before,),
                runtime_root=root,
            ),
        )
        tm.fail(
            outcome,
            has=(
                "candidate interpreter escaped declared physical runtime"
                if borrowed
                else "candidate runtime must be physical"
            ),
        )
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

        calls = 0

        def validate(view_root: Path, candidates: t.MappingKV[Path, Path]) -> bool:
            nonlocal calls
            calls += 1
            tm.that(candidates[target].read_text(), eq="VALUE = 2\n")
            if mutation == "changed":
                target.write_text("VALUE = 3\n")
            elif mutation == "added":
                (package / "shared.py").write_text("VALUE = 3\n")
            else:
                tm.ok(candidates[target].is_relative_to(view_root))
                candidates[target].write_text("VALUE = 3\n")
            return True

        tm.fail(
            owner.preview_sources(
                root,
                {target: "VALUE = 2\n"},
                validate,
                options=m.Infra.CodegenSourcePreviewOptions(
                    inputs=(before,),
                    runtime_root=u.Infra.runtime_environment_dir(
                        Path(__file__).resolve().parents[3]
                    ).parent,
                ),
            ),
            has=(
                "generation authenticated state changed"
                if mutation == "changed"
                else "source directory membership changed"
                if mutation == "added"
                else "source preview candidate changed during validation"
            ),
        )
        tm.that(calls, eq=1)
        tm.that(
            target.read_text(),
            eq="VALUE = 3\n" if mutation == "changed" else "VALUE = 1\n",
        )
        tm.that((package / "shared.py").exists(), eq=mutation == "added")

    @staticmethod
    @pytest.mark.parametrize("original_role", ["target", "dependency", "metadata"])
    def test_source_preview_rejects_reobserved_original_identity(
        tmp_path: Path,
        original_role: Literal["target", "dependency", "metadata"],
    ) -> None:
        """Original authentication precedes parsing even when live bytes are invalid."""
        root = u.Tests.git_repository(tmp_path)
        package = u.Tests.src_package(
            root,
            "sample",
            pyproject="[project]\nname = 'sample'\nversion = '1.0.0'\n",
        )
        target = package / "contract.py"
        target.write_text("VALUE = 1\n")
        dependency = package / "provider.py"
        dependency.write_text("VALUE = 1\n")
        original = {
            "target": target,
            "dependency": dependency,
            "metadata": root / c.PYPROJECT_FILENAME,
        }[original_role]
        before = tm.ok(u.Cli.atomic_read_binary_file_state(original, required=True))
        changed = b"not a valid source [\n"
        original.write_bytes(changed)

        refused = FlextInfraStagedPackage.plan_sources(
            root,
            {target: "VALUE = 2\n"},
            options=m.Infra.StageSourceOptions(inputs=(before,)),
        )

        tm.fail(refused, has="generation authenticated state changed")
        tm.that(str(refused.error), has=str(original))
        tm.that(
            str(refused.error),
            has=f"expected_sha256={u.Cli.sha256_bytes(tm.not_none(before.content))}",
        )
        tm.that(
            str(refused.error),
            has=f"observed_sha256={u.Cli.sha256_bytes(changed)}",
        )
        tm.ok(isinstance(refused.exception, ValueError))
        tm.that(original.read_bytes(), eq=changed)

    @staticmethod
    def test_source_candidate_reuses_original_receipts_and_checks_full_python_inputs(
        tmp_path: Path,
    ) -> None:
        """Whole-project native gates keep their positive non-effect Python inputs."""
        root = u.Tests.git_repository(tmp_path)
        package = u.Tests.src_package(
            root,
            "sample",
            pyproject="[project]\nname = 'sample'\nversion = '1.0.0'\n",
        )
        target = package / "contract.py"
        target.write_text("VALUE = 1\n")
        helper = root / "tests" / "support.py"
        helper.parent.mkdir()
        helper.write_text("VALUE = 1\n")
        originals = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in (target, helper, root / c.PYPROJECT_FILENAME)
        )
        plan = tm.ok(
            FlextInfraStagedPackage.plan_sources(
                root,
                {target: "VALUE = 2\n"},
                options=m.Infra.StageSourceOptions(inputs=originals),
            )
        )
        for original in originals:
            retained = next(
                state for state in plan.inputs if state.path == original.path
            )
            tm.ok(retained is original)
        helper.write_text("VALUE = 3\n")

        tm.fail(
            FlextInfraStagedPackage.source_inputs_current(plan),
            has=str(helper),
        )
        tm.that(target.read_bytes(), eq=originals[0].content)

    @staticmethod
    def test_source_candidate_keeps_an_unconsumed_provider_independent(
        tmp_path: Path,
    ) -> None:
        """An unelected sibling's content is not a candidate input."""
        root = u.Tests.git_repository(tmp_path)
        package = u.Tests.src_package(
            root,
            "sample",
            pyproject="[project]\nname = 'sample'\nversion = '1.0.0'\n",
        )
        provider = root / "provider"
        provider_package = u.Tests.src_package(
            provider,
            "independent",
            pyproject="[project]\nname = 'independent'\nversion = '1.0.0'\n",
        )
        (root / c.Infra.GITMODULES).write_text(
            '[submodule "provider"]\n\tpath = provider\n',
        )
        source = provider_package / c.Infra.INIT_PY
        source.write_text("VALUE = 1\n")
        target = package / "contract.py"
        target.write_text("VALUE = 1\n")
        plan = tm.ok(
            FlextInfraStagedPackage.plan_sources(root, {target: "VALUE = 2\n"})
        )
        source.write_text("VALUE = 3\n")

        tm.ok(FlextInfraStagedPackage.source_inputs_current(plan))
        candidate = tmp_path / "candidate"
        tm.ok(FlextInfraStagedPackage.materialize_sources(plan, candidate))
        tm.that(
            (candidate / target.relative_to(root)).read_text(),
            eq=plan.updates[target],
        )
        tm.that(source.read_text(), eq="VALUE = 3\n")

    @staticmethod
    @pytest.mark.parametrize(
        "selector",
        ["what", "scope", "mode", "module", "declaration_kind"],
    )
    def test_footprint_request_rejects_generation_selectors(
        tmp_path: Path,
        selector: str,
    ) -> None:
        """Inspection cannot silently accept prospective generation selectors."""
        with pytest.raises(e.PydanticValidationError):
            m.Infra.CodegenFootprintRequest.model_validate({
                "root": tmp_path,
                selector: "generation-selector",
            })

    @staticmethod
    @pytest.mark.parametrize(
        "mutation", ["target", "dependency", "metadata", "membership"]
    )
    @pytest.mark.parametrize("timing", ["before", "after-consumer"])
    def test_prepared_receipt_rejects_changes_without_refreshing_authority(
        tmp_path: Path,
        session_runtime: p.Tests.SessionRuntime,
        mutation: Literal["target", "dependency", "metadata", "membership"],
        timing: Literal["before", "after-consumer"],
    ) -> None:
        """A closed native epoch survives cold consumption but never source drift."""
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
        target = package / "prepared.py"
        target.write_text("VALUE = 1\n")
        dependency = package / "provider.py"
        dependency.write_text("VALUE = 1\n")
        before = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
        owner = transaction.FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = {"@prepared-0": root}
        changed = {
            "target": target,
            "dependency": dependency,
            "metadata": root / c.PYPROJECT_FILENAME,
            "membership": package / "arrived.py",
        }[mutation]

        def validate(scope_root: Path) -> p.Result[bool]:
            session = tm.ok(owner.begin_files_locked(scope_root, roots, (before,)))
            prepared = tm.ok(
                FlextInfraCodegenStaging.prepare_python_plans(
                    root,
                    (
                        m.Infra.CodegenFilePlan(
                            project=root,
                            path=target,
                            before=before,
                            desired_content=b"VALUE = 2\n",
                            desired_mode=before.mode,
                        ),
                    ),
                )
            )
            receipt = tm.not_none(prepared[0].prepared_sources)
            if not isinstance(receipt, m.Infra.StageSourcePlan):
                pytest.fail("Preparation did not return the canonical source receipt")
            originals = receipt.inputs
            calls = 0

            def consume(
                view: Path,
                candidate: m.Infra.StageSourcePlan,
                project: Path,
                runtime_report: m.Infra.ValidationReport,
            ) -> p.Result[bool]:
                nonlocal calls
                calls += 1
                tm.that(project, eq=root)
                tm.ok(runtime_report.passed)
                tm.that(candidate.inputs, eq=originals)
                consumed = tm.ok(
                    u.Cli.run_raw(
                        (
                            sys.executable,
                            "-c",
                            (
                                "import runpy, sys; assert runpy.run_path(sys.argv[1])"
                                "['VALUE'] == 2"
                            ),
                            str(view / target.relative_to(root)),
                        ),
                        cwd=view,
                    )
                )
                tm.ok(u.Cli.process_succeeded(consumed.outcome))
                changed.write_bytes(b"invalid source [\n")
                return r[bool].ok(value=True)

            if timing == "before":
                changed.write_bytes(b"invalid source [\n")
            refused = FlextInfraCodegenStaging.validate_python_plans(
                session,
                (),
                plans=prepared,
                workspace=root,
                validator=consume,
            )
            tm.fail(
                refused,
                has=(
                    "source directory membership changed"
                    if mutation == "membership"
                    else "generation authenticated state changed"
                ),
            )
            tm.ok(isinstance(refused.exception, ValueError))
            tm.that(calls, eq=0 if timing == "before" else 1)
            tm.ok(receipt.inputs is originals)
            tm.ok(prepared[0].prepared_sources is receipt)
            tm.that(changed.read_bytes(), eq=b"invalid source [\n")
            if mutation != "target":
                tm.that(target.read_bytes(), eq=before.content)
            tm.fail(FlextInfraCodegenStaging.prepare_python_plans(root, prepared))
            return r[bool].ok(value=True)

        tm.ok(owner.run_files_locked(roots, validate))

    @staticmethod
    @pytest.mark.parametrize("unchanged", [False, True])
    @pytest.mark.parametrize(
        "rejection", ["import", "census", "false", "failure", "candidate"]
    )
    def test_staged_admission_keeps_runtime_and_guarded_consumer_failures(
        tmp_path: Path,
        session_runtime: p.Tests.SessionRuntime,
        rejection: str,
        *,
        unchanged: bool,
    ) -> None:
        """Even no-effect plans require native runtime before read-only callbacks."""
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
        target = package / "candidate.py"
        source = (
            "import missing_admission_dependency\n"
            if rejection == "import"
            else "class Plain:\n    pass\n"
            if rejection == "census"
            else "VALUE = 2\n"
        )
        target.write_text(source if unchanged else "VALUE = 1\n")
        before = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
        prepared = tm.ok(
            FlextInfraCodegenStaging.prepare_python_plans(
                root,
                (
                    m.Infra.CodegenFilePlan(
                        project=root,
                        path=target,
                        before=before,
                        desired_content=source.encode(c.DEFAULT_ENCODING),
                        desired_mode=before.mode,
                    ),
                ),
            )
        )
        tm.that(u.Infra.codegen_file_requires_effect(prepared[0]), eq=not unchanged)
        owner = transaction.FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = owner.capability_roots("admission", (root,))
        calls = 0
        original = OSError("native consumer rejected the admitted candidate")

        def reject(
            view: Path,
            candidate: m.Infra.StageSourcePlan,
            project: Path,
            runtime_report: m.Infra.ValidationReport,
        ) -> p.Result[bool]:
            nonlocal calls
            calls += 1
            tm.ok(runtime_report.passed)
            tm.that(project, eq=root)
            tm.ok(FlextInfraStagedPackage.source_inputs_current(candidate))
            destination = view / target.relative_to(root)
            tm.that(destination.read_text(), eq=source)
            tm.that(target.read_bytes(), eq=before.content)
            if rejection == "failure":
                return r[bool].fail(
                    str(original), exception=original, error_code="native-consumer"
                )
            if rejection == "candidate":
                destination.write_text("VALUE = 3\n")
                return r[bool].ok(value=True)
            return r[bool].ok(value=False)

        def validate(scope_root: Path) -> p.Result[bool]:
            session = tm.ok(owner.begin_files_locked(scope_root, roots, (before,)))
            refused = FlextInfraCodegenStaging.validate_python_plans(
                session,
                (),
                plans=prepared,
                workspace=root,
                validator=reject,
            )
            if rejection == "import":
                tm.fail(refused, has="missing_admission_dependency")
                tm.that(str(refused.error), has="candidate runtime consumer failed")
            elif rejection == "census":
                tm.fail(refused, has="candidate runtime rejected")
                tm.that(str(refused.error), has="runtime census found")
                tm.that(str(refused.error), has="Plain [class_prefix]")
            elif rejection == "failure":
                tm.fail(refused, has=str(original))
                tm.ok(refused.exception is original)
                tm.that(refused.error_code, eq="native-consumer")
            elif rejection == "candidate":
                tm.fail(
                    refused, has="source candidate changed during read-only admission"
                )
            else:
                tm.fail(refused, has=f"candidate check rejected: {root}")
            tm.that(calls, eq=0 if rejection in {"import", "census"} else 1)
            tm.that(
                tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True)),
                eq=before,
            )
            return r[bool].ok(value=True)

        tm.ok(owner.run_files_locked(roots, validate))

    @staticmethod
    @pytest.mark.parametrize("tamper", ["bytes", "mode"])
    def test_prepared_receipt_rejects_an_altered_effect(
        tmp_path: Path,
        tamper: Literal["bytes", "mode"],
    ) -> None:
        """Admission consumes the original sealed candidate, not a replacement plan."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        target = package / "prepared.py"
        target.write_text("VALUE = 1\n")
        before = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
        owner = transaction.FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = {"@prepared-0": root}

        def validate(scope_root: Path) -> p.Result[bool]:
            session = tm.ok(owner.begin_files_locked(scope_root, roots, (before,)))
            prepared = tm.ok(
                FlextInfraCodegenStaging.prepare_python_plans(
                    root,
                    (
                        m.Infra.CodegenFilePlan(
                            project=root,
                            path=target,
                            before=before,
                            desired_content=b"VALUE = 2\n",
                            desired_mode=before.mode,
                        ),
                    ),
                )
            )
            altered = prepared[0].model_copy(
                update=(
                    {"desired_content": b"VALUE = 3\n"}
                    if tamper == "bytes"
                    else {"desired_mode": tm.not_none(prepared[0].desired_mode) ^ 0o100}
                )
            )
            refused = FlextInfraCodegenStaging.validate_python_plans(
                session,
                (),
                plans=(altered,),
                workspace=root,
            )
            tm.fail(refused, has="differs from sealed preparation")
            tm.that(
                tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True)),
                eq=before,
            )
            tm.fail(FlextInfraCodegenStaging.prepare_python_plans(root, (altered,)))
            return r[bool].ok(value=True)

        tm.ok(owner.run_files_locked(roots, validate))

    @staticmethod
    def test_public_footprint_does_not_plan_sources_or_publish_reports(
        tmp_path: Path,
    ) -> None:
        """An absent journal needs topology, not parseable generation sources."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "unreadable_source.py"
        source.write_bytes(b"\xffnot Python\n")
        report = root / c.Infra.CODEGEN_PLAN_REPORT_RELATIVE_PATH
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_bytes(b"preserve the existing report\n")
        originals = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in (source, report)
        )
        owner = transaction.FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        observed = tm.ok(owner.inspect_journal())
        policy = tm.ok(owner.participant_policy())
        expected = observed.model_copy(
            update={"authorized_roots": tuple(item.target for item in policy.roots)},
        )
        request = m.Infra.CodegenFootprintRequest(root=root)

        for _ in range(2):
            tm.that(
                tm.ok(infra.codegen_footprint(request)),
                eq=expected.model_dump_json(),
            )
            tm.that(tm.ok(owner.inspect_journal()), eq=observed)
            tm.that(
                tuple(
                    tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
                    for path in (source, report)
                ),
                eq=originals,
            )
            tm.fail(observed.journal_path.exists())
            tm.fail((root / c.Infra.TRANSACTION_STATE_DIRNAME).exists())

    @staticmethod
    @pytest.mark.parametrize("state", ["staging", "prepared", "committed"])
    def test_public_footprint_retains_all_recorded_pending_effects(
        tmp_path: Path,
        state: str,
    ) -> None:
        """Retain native journal authority without recovery or publication."""
        root, _package = u.Tests.create_lazy_init_workspace(tmp_path)
        target = root / "recorded.md"
        target.write_bytes(b"original document\n")
        before = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
        owner = transaction.FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        roots = {"@docs-0": root}

        def record(scope_root: Path) -> p.Result[m.Infra.CodegenTransactionSession]:
            session = tm.ok(owner.begin_files_locked(scope_root, roots, (before,)))
            plan = m.Infra.CodegenFilePlan(
                project=root,
                path=target,
                before=before,
                desired_content=b"recorded document\n",
                desired_mode=before.mode,
                owner="docs",
            )
            if state == "staging":
                return owner.prepare_phase_staging_locked(session, "docs", (plan,))
            prepared = tm.ok(owner.append_phase_locked(session, "docs", (plan,)))
            if state == "committed":
                journal = m.Infra.CodegenTransactionJournal.model_validate({
                    **prepared.journal.model_dump(),
                    "state": state,
                })
                written = tm.ok(
                    FlextInfraMiseArtifactsJournal.write(
                        prepared.plan.layout,
                        journal,
                        expected=prepared.journal_state,
                    ),
                )
                prepared = prepared.model_copy(
                    update={"journal": journal, "journal_state": written},
                )
            return r[m.Infra.CodegenTransactionSession].ok(prepared)

        tm.ok(owner.run_files_locked(roots, record))
        observed = tm.ok(owner.inspect_journal())
        tm.that(observed.journal_state, eq=state)
        tm.ok(bool(observed.pending_roots))
        tm.ok(bool(observed.pending_directories))
        tm.ok(bool(observed.pending_staging))
        tm.that(bool(observed.pending_destinations), eq=state != "staging")
        policy = tm.ok(owner.participant_policy())
        expected = observed.model_copy(
            update={"authorized_roots": tuple(item.target for item in policy.roots)},
        )
        target_state = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))

        tm.that(
            tm.ok(infra.codegen_footprint(m.Infra.CodegenFootprintRequest(root=root))),
            eq=expected.model_dump_json(),
        )
        tm.that(tm.ok(owner.inspect_journal()), eq=observed)
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True)),
            eq=target_state,
        )
        tm.fail((root / c.Infra.CODEGEN_PLAN_REPORT_RELATIVE_PATH).exists())

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
    def test_semantic_candidate_rejects_external_changes_before_publication(
        tmp_path: Path,
        mutation: str,
    ) -> None:
        """Consumer acceptance cannot overwrite a concurrent live-file update."""
        root, _package = u.Tests.create_lazy_init_workspace(tmp_path)
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

        def validate(candidate_root: Path) -> p.Result[bool]:
            candidate = candidate_root / target.relative_to(root)
            consumed = tm.ok(
                u.Cli.run_raw(
                    (
                        sys.executable,
                        "-c",
                        (
                            "import runpy, sys; "
                            "assert runpy.run_path(sys.argv[1])['value'] == 2"
                        ),
                        str(candidate),
                    ),
                    cwd=candidate_root,
                ),
            )
            tm.ok(u.Cli.process_succeeded(consumed.outcome))
            original = tm.ok(
                u.Cli.atomic_read_binary_file_state(target, required=True),
            )
            tm.that(original.content, eq=before.content)
            if mutation == "content":
                target.write_bytes(b"value = 3\n")
            elif mutation == "inode":
                tm.that(original.mode, none=False)
                tm.ok(
                    u.Cli.atomic_write_binary_file_guarded(
                        original,
                        tm.not_none(before.content),
                        permission_mode=original.mode,
                    ),
                )
            return r[bool].ok(value=True)

        outcome = FlextInfraSemanticPublication.publish_semantic_file_plans(
            (plan,),
            repository_root=root,
            options=m.Infra.SemanticPublicationOptions(validator=validate),
        )
        if mutation == "unchanged":
            tm.ok(outcome)
        else:
            tm.fail(outcome)
        tm.that(
            target.read_bytes(),
            eq=(
                b"value = 3\n"
                if mutation == "content"
                else before.content
                if mutation == "inode"
                else desired
            ),
        )

    @staticmethod
    @pytest.mark.parametrize("inside", [False, True])
    @pytest.mark.parametrize("boundary", ["managed", "file", "footprint"])
    @pytest.mark.parametrize("state", ["staging", "prepared", "committed"])
    def test_request_authorization_preserves_foreign_pending_journal(
        tmp_path: Path,
        boundary: str,
        state: str,
        *,
        inside: bool,
    ) -> None:
        """Reject undeclared capabilities without recovery or publication."""
        root, _package = u.Tests.create_lazy_init_workspace(tmp_path / "source")
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

        result: p.Result[str] | p.Result[bool]
        if boundary == "footprint":
            result = infra.codegen_footprint(m.Infra.CodegenFootprintRequest(root=root))
        elif boundary == "managed":
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
        tm.fail((root / "unauthorized.txt").exists())
        tm.fail((foreign / c.Infra.TRANSACTION_STATE_DIRNAME).exists())
        tm.fail((root / c.Infra.TRANSACTION_STATE_DIRNAME).exists())

    @staticmethod
    def test_effect_free_inspection_preserves_corrupt_journal(tmp_path: Path) -> None:
        """Preserve the original parser failure without creating recovery state."""
        root, _package = u.Tests.create_lazy_init_workspace(tmp_path)
        owner = transaction.FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        absent = tm.ok(owner.inspect_journal())
        tm.that(absent.journal_state, eq="absent")
        tm.fail(absent.journal_path.exists())
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
        with pytest.raises(e.PydanticValidationError):
            infra.codegen_footprint(m.Infra.CodegenFootprintRequest(root=root))
        tm.that(
            tm.ok(
                u.Cli.atomic_read_binary_file_state(
                    absent.journal_path,
                    required=True,
                ),
            ),
            eq=corrupted,
        )
        tm.fail((root / c.Infra.TRANSACTION_STATE_DIRNAME).exists())

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
        tm.fail(session.plan.layout.journal_path.exists())

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
                            source_states=(before,),
                            owner="docs",
                        ),
                    ),
                ),
                m.Infra.CodegenPhasePublicationPolicy(
                    directories=(),
                ),
            )

        tm.ok(owner.run_files_locked(roots, publish))
        tm.fail(target.exists())

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
                    tm.that(snapshot.mode, none=False)
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
                    staged_validator=staged,
                ),
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
                tm.that(content, none=False)
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
        tm.that(transaction_root, none=False)
        tm.ok(transaction_root.exists())
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
        tm.fail(transaction_root.exists())
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
        tm.fail(target.exists())

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
            tm.that(content, none=False)
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
