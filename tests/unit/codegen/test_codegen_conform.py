"""Public functional contract for new and existing project conformance.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import ClassVar, override

import pytest

from flext_infra import config, infra, r
from flext_infra.codegen import (
    FlextInfraCodegenConform,
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenProjectNew,
    FlextInfraCodegenTransaction,
    FlextInfraMiseWorkspacePlanner,
)
from flext_infra.docs import FlextInfraDocGenerator
from flext_infra.workspace import FlextInfraWorkspaceDetector
from tests import c, m, p, t, tm, u
from tests.unit.codegen.conform_support import TestsFlextInfraConformSupport

pytestmark = [pytest.mark.slow]

_LIFECYCLE_EXCEPTION = OSError("conform operation raised after begin")


def _assert_conform_check_reaches_fixed_point(root: Path) -> None:
    """Run a SELF CHECK conform and assert it writes nothing new."""
    fixed_point = infra.codegen_conform(
        u.Tests.conform_request(
            root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        ),
    )
    tm.ok(fixed_point)
    tm.that(fixed_point.value.written_files, eq=())


class TestsFlextInfraCodegenConformLifecycleProbe(FlextInfraCodegenConform):
    """Inject one public planning outcome after the real transaction begins."""

    __test__ = False
    SCENARIOS: ClassVar[t.VariadicTuple[str]] = (
        "planning-exception",
        "publication-source-race",
        "planning-issue-source-race",
    )

    @classmethod
    @override
    def plan_repository_task(
        cls,
        task: m.Infra.CodegenRepositoryPlanTask,
    ) -> m.Infra.CodegenRepositoryPlanOutcome:
        """Exercise a native cause with no preconstructed diagnostic fields.

        Returns:
            The resulting ``m.Infra.CodegenRepositoryPlanOutcome``.

        """
        if task.root.name == "exception-only-outcome":
            return m.Infra.CodegenRepositoryPlanOutcome(
                repository=task.repository.name,
                exception=_LIFECYCLE_EXCEPTION,
            )
        return super().plan_repository_task(task)

    @override
    def plan(
        self,
        request: m.Infra.CodegenConformRequest,
    ) -> p.Result[m.Infra.CodegenPlan]:
        """Exercise recovery from real journal, staging, and CAS state changes.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenPlan]``.

        """
        planned = super().plan(request)
        if planned.failure:
            return planned
        scenario = request.root.name
        if scenario in self.SCENARIOS:
            selected = tuple(
                file
                for file in planned.value.files
                if file.path.name
                in {
                    c.Infra.GITIGNORE,
                    c.Infra.MAKEFILE_FILENAME,
                    c.Infra.MISE_TOML_FILENAME,
                }
            )
            rejected = next(
                file for file in selected if file.path.name == c.Infra.GITIGNORE
            )
            independent = tuple(file for file in selected if file is not rejected)
            if scenario.endswith("source-race"):
                bridge, original = next(
                    (file, file.before)
                    for file in planned.value.files
                    if file not in selected
                    and file.dependency_group is None
                    and isinstance(file.before, m.Cli.AtomicFileState)
                    and not u.Infra.codegen_file_requires_effect(file)
                )
                rejected = rejected.model_copy(
                    update={"source_states": (*rejected.source_states, original)},
                )
                independent = (
                    *(
                        file.model_copy(
                            update={"source_states": (*file.source_states, original)},
                        )
                        if file.path.name == c.Infra.MAKEFILE_FILENAME
                        else file
                        for file in independent
                    ),
                    bridge,
                )
            expected = next(
                file
                for file in independent
                if file.path.name == c.Infra.MAKEFILE_FILENAME
            )
            (request.root.parent / ".lifecycle-expected").write_bytes(
                tm.not_none(expected.desired_content),
            )
            issues = (
                (
                    m.Infra.Issue(
                        file=str(rejected.path),
                        line=0,
                        column=0,
                        code=c.Infra.ToolOutcome.ERROR.value,
                        message=str(_LIFECYCLE_EXCEPTION),
                    ),
                )
                if scenario != "publication-source-race"
                else ()
            )
            if scenario == "planning-exception":
                return r[m.Infra.CodegenPlan].ok(
                    planned.value.model_copy(
                        update={
                            "files": independent,
                            "exception": _LIFECYCLE_EXCEPTION,
                            "issues": (*planned.value.issues, *issues),
                        },
                    ),
                )
            source = request.root / ".lifecycle-source"
            before = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
            source.write_bytes(b"foreign source\n")
            rejected = rejected.model_copy(
                update={"source_states": (*rejected.source_states, before)},
            )
            return r[m.Infra.CodegenPlan].ok(
                planned.value.model_copy(
                    update={
                        "files": (rejected, *independent),
                        "issues": (*planned.value.issues, *issues),
                    },
                ),
            )
        return planned

    @staticmethod
    def fail_publication(session: p.Model) -> p.Result[p.Infra.CodegenResult]:
        """Perturb a prepared native transaction inside its publication callback.

        Exception scenarios re-raise the original native exception object.

        Returns:
            The original filesystem failure or the declared publication failure.

        """
        state = m.Infra.CodegenTransactionSession.model_validate(
            session,
            from_attributes=True,
        )
        root = state.plan.layout.scope_root
        scenario = root.name
        if scenario in {"cas", "source-race"}:
            marker = root / ".lifecycle-cas"
            before = tm.ok(u.Cli.atomic_read_binary_file_state(marker, required=True))
            tm.that(before.content, eq=b"before\n")
            marker.write_bytes(b"foreign\n")
            failed = (
                u.Cli.atomic_verify_binary_file_states((before,))
                if scenario == "source-race"
                else u.Cli.atomic_write_binary_file_guarded(
                    before,
                    b"owned\n",
                    permission_mode=tm.not_none(before.mode),
                )
            )
            tm.fail(failed)
            return r[p.Infra.CodegenResult].from_failure(failed)
        journal = state.plan.layout.journal_path
        journal_bytes = journal.read_bytes()
        recorded = m.Infra.CodegenTransactionJournal.model_validate_json(journal_bytes)
        if scenario.endswith("-mixed"):
            staging = next(
                tm.not_none(directory.created).path
                for directory in recorded.directories
                if directory.disposition == "temporary"
                and directory.created is not None
            )
            (staging / "foreign.bin").write_bytes(b"foreign staging\n")
        if scenario.endswith("-changed"):
            journal.write_bytes(journal_bytes + b"\n")
        elif scenario.endswith("-replaced"):
            preserved = journal.with_suffix(".preserved")
            journal.rename(preserved)
            journal.write_bytes(preserved.read_bytes())
            journal.chmod(preserved.stat().st_mode)
        if scenario.startswith("exception-"):
            raise _LIFECYCLE_EXCEPTION
        return r[p.Infra.CodegenResult].fail("conform operation failed after begin")


class TestsFlextInfraCodegenConform:
    """Prove one SSOT for project creation and existing-tree conformance."""

    @staticmethod
    @pytest.fixture(scope="module")
    def conformed_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
        """Conform one real seed tree once per module; each scenario clones it.

        Every recovery scenario begins its own transaction on a fresh clone of
        this template, so the journal (which anchors inside the clone's Git
        directory), staging, and CAS state under test are always the clone's
        own; only the expensive seed apply is shared provisioning.

        Returns:
            The resulting ``Path``.

        """
        template = tmp_path_factory.mktemp("conform-template") / "conformed"
        template.mkdir()
        u.Tests.initialize_git_repo(
            template,
            origin_url=u.Tests.repository_ref(config.Infra.name).url,
        )
        TestsFlextInfraConformSupport.seed_infra_package_tree(template)
        workspace = u.Tests.standalone_workspace(template, config.Infra.name)
        request = u.Tests.conform_request(
            template,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        tm.ok(infra.codegen_conform(request, workspace))
        u.Tests.commit_git_changes(template, "Seed conformed lifecycle fixture")
        return template

    @staticmethod
    def _lifecycle_fixture(
        tmp_path: Path,
        scenario: str,
        template: Path,
    ) -> tuple[Path, m.Infra.CodegenConformRequest, Path, bytes, Path]:
        """Clone the conformed template, then introduce one recoverable publication.

        Returns:
            The resulting ``tuple[Path, m.Infra.CodegenConformRequest, Path, bytes,
                Path]``.

        """
        root = tmp_path / scenario
        shutil.copytree(template, root)
        published = root / c.Infra.MAKEFILE_FILENAME
        original = published.read_bytes() + b"\n# recoverable drift\n"
        published.write_bytes(original)
        if scenario == "lazy-failure":
            package = root / "src" / config.Infra.name.replace("-", "_")
            obsolete = package / next(iter(sorted(c.Infra.OBSOLETE_ROOT_SUPPORT_NAMES)))
            obsolete.symlink_to(root / "README.md")
        elif scenario == "docs-failure":
            docs_config = root / c.Infra.DIR_DOCS / c.Infra.DOCS_CONFIG_FILENAME
            docs_config.write_text("{invalid", encoding="utf-8")
        if scenario in {"cas", "source-race"}:
            (root / ".lifecycle-cas").write_bytes(b"before\n")
        if scenario in TestsFlextInfraCodegenConformLifecycleProbe.SCENARIOS:
            ignored = root / c.Infra.GITIGNORE
            ignored.write_bytes(ignored.read_bytes() + b"\n# rejected drift\n")
            (root / ".lifecycle-source").write_bytes(b"before\n")
        identity = tm.ok(u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=root)))
        journal = FlextInfraMiseWorkspacePlanner.journal_path(identity)
        request = u.Tests.conform_request(
            root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        return root, request, published, original, journal

    @pytest.mark.parametrize(
        "scenario",
        TestsFlextInfraCodegenConformLifecycleProbe.SCENARIOS,
    )
    def test_public_generation_preserves_independent_gains_after_failure(
        self,
        tmp_path: Path,
        conformed_template: Path,
        scenario: str,
    ) -> None:
        """Reject a causal target without abandoning independent authenticated work."""
        root, request, published, original, _journal = self._lifecycle_fixture(
            tmp_path,
            scenario,
            conformed_template,
        )
        rejected = root / c.Infra.GITIGNORE
        rejected_before = rejected.read_bytes()
        if scenario == "planning-exception":
            with pytest.raises(OSError, match="raised after begin") as raised:
                TestsFlextInfraCodegenConformLifecycleProbe.execute_request(
                    request,
                    execution_context=infra,
                    generation_only=True,
                )
            tm.that(raised.value is _LIFECYCLE_EXCEPTION, eq=True)
        else:
            with pytest.raises(ValueError, match="atomic source changed") as changed:
                TestsFlextInfraCodegenConformLifecycleProbe.execute_request(
                    request,
                    execution_context=infra,
                    generation_only=True,
                )
            tm.that(str(changed.value), has=str(root / ".lifecycle-source"))
            tm.that(
                (root / ".lifecycle-source").read_bytes(),
                eq=b"foreign source\n",
            )
        tm.that(published.read_bytes() == original, eq=False)
        tm.that(
            published.read_bytes()
            == (root.parent / ".lifecycle-expected").read_bytes(),
            eq=True,
        )
        tm.that(rejected.read_bytes(), eq=rejected_before)
        receipt = m.Infra.CodegenPhaseOutcome.model_validate_json(
            (root / c.Infra.CODEGEN_PUBLICATION_REPORT_RELATIVE_PATH).read_bytes(),
        )
        tm.that(receipt.completed, eq=False)
        tm.that(receipt.written_files, has=published)
        tm.that(rejected in receipt.written_files, eq=False)
        tm.that(bool(receipt.issues), eq=True)
        if scenario == "planning-issue-source-race":
            tm.that(
                any(
                    issue.message == str(_LIFECYCLE_EXCEPTION)
                    for issue in receipt.issues
                ),
                eq=True,
            )

    def test_public_planning_reports_exception_only_outcome_as_failed(
        self,
        tmp_path: Path,
        conformed_template: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Progress and persisted evidence cannot call an exception-only worker OK."""
        root, request, _published, _original, _journal = self._lifecycle_fixture(
            tmp_path,
            "exception-only-outcome",
            conformed_template,
        )
        _ = capsys.readouterr()
        plan = tm.ok(
            TestsFlextInfraCodegenConformLifecycleProbe(repository_root=root).plan(
                request,
            ),
        )
        tm.that(str(plan.exception), eq=str(_LIFECYCLE_EXCEPTION))
        tm.that(bool(plan.issues), eq=True)
        evidence = m.Infra.CodegenPlanningReport.model_validate_json(
            (root / c.Infra.CODEGEN_PLAN_REPORT_RELATIVE_PATH).read_bytes(),
        )
        tm.that(evidence.outcomes, len=1)
        tm.that(evidence.outcomes[0].error, eq=str(_LIFECYCLE_EXCEPTION))
        tm.that(evidence.outcomes[0].error_type, eq="builtins.OSError")
        tm.that(capsys.readouterr().out, lacks="[OK]")

    @pytest.mark.parametrize(
        "scenario",
        [
            "failure-changed",
            "exception-replaced",
            "failure-mixed",
            "cas",
            "source-race",
            "lazy-failure",
            "docs-failure",
        ],
    )
    def test_public_apply_recovers_only_authenticated_prepared_state(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        conformed_template: Path,
        scenario: str,
    ) -> None:
        """Exercise post-begin failures through real filesystem and CAS state."""
        root, request, published, original, journal = self._lifecycle_fixture(
            tmp_path,
            scenario,
            conformed_template,
        )
        _ = capsys.readouterr()

        def execute() -> p.Result[p.Infra.CodegenResult]:
            if scenario.endswith("-failure"):
                return FlextInfraCodegenConform.execute_request(
                    request,
                    execution_context=infra,
                )
            owner = FlextInfraCodegenTransaction(
                FlextInfraCodegenMiseArtifacts(repository_root=root),
            )
            roots = owner.capability_roots("bootstrap", (root,))
            planned = tm.ok(
                FlextInfraCodegenConform(repository_root=root).plan(request)
            )
            target = next(file for file in planned.files if file.path == published)

            def fail_prepared(scope: Path) -> p.Result[p.Infra.CodegenResult]:
                initial = tm.ok(
                    owner.begin_files_locked(scope, roots, target.source_states)
                )
                tm.ok(
                    owner.append_phase_locked(initial, "conform-bootstrap", (target,))
                )

                return owner.publish_prepared_locked(
                    initial,
                    TestsFlextInfraCodegenConformLifecycleProbe.fail_publication,
                )

            return owner.run_files_locked(roots, fail_prepared)

        if scenario.startswith("exception-"):
            with pytest.raises(OSError, match="raised after begin") as raised:
                execute()
            tm.that(raised.value is _LIFECYCLE_EXCEPTION, eq=True)
        elif scenario == "docs-failure":
            with pytest.raises(ValueError, match="Invalid JSON"):
                execute()
        else:
            failed = execute()
            expected = {
                "cas": "atomic destination content changed",
                "source-race": "atomic source changed",
                "lazy-failure": "refusing obsolete root-support symlink",
            }.get(scenario, "failed after begin")
            tm.fail(failed, has=expected)

        retained = scenario in {
            "exception-replaced",
            "failure-changed",
            "failure-mixed",
        }
        tm.that(journal.exists(), eq=retained)
        tm.that(published.read_bytes() == original, eq=False)
        if scenario == "failure-changed":
            tm.that(journal.read_bytes().endswith(b"\n"), eq=True)
        elif scenario == "exception-replaced":
            preserved = journal.with_suffix(".preserved")
            tm.that(preserved.read_bytes(), eq=journal.read_bytes())
            tm.that(preserved.stat().st_ino == journal.stat().st_ino, eq=False)
        elif scenario == "failure-mixed":
            tm.that(
                tuple(path.read_bytes() for path in tmp_path.rglob("foreign.bin")),
                eq=(b"foreign staging\n",),
            )
        elif scenario in {"cas", "source-race"}:
            tm.that((root / ".lifecycle-cas").read_bytes(), eq=b"foreign\n")
            tm.that(capsys.readouterr().out, lacks="mode=converge")

    @staticmethod
    def test_public_scaffold_exception_restores_bootstrap_state(
        tmp_path: Path,
    ) -> None:
        """A raised prepared operation removes invocation-owned root and Git state."""
        root = tmp_path / "exception-scaffold"
        # A new project is created inside a tree that already carries the lock.
        u.Tests.copy_tracked_mise_seeds(tmp_path)
        repository = u.Tests.repository_ref(
            "exception-scaffold",
            role=c.Infra.MakeProfile.STANDALONE,
        )
        workspace = u.Tests.workspace_spec(
            repository,
            project=u.Tests.project_spec(repository.name),
        )
        request = u.Tests.conform_request(
            root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )

        with pytest.raises(OSError, match="raised after begin") as raised:
            TestsFlextInfraCodegenConformLifecycleProbe.execute_request(
                request,
                workspace,
                execution_context=infra,
            )

        tm.that(raised.value is _LIFECYCLE_EXCEPTION, eq=True)
        tm.that(root.exists(), eq=False)

    @staticmethod
    def test_pyproject_plan_rejects_local_path_internal_source(
        tmp_path: Path,
    ) -> None:
        """A local-path internal source has no detectable identity: fail loud."""
        service, request = TestsFlextInfraConformSupport.self_check_conform_service(
            tmp_path,
        )
        request = request.model_copy(
            update={"what": c.Infra.CodegenConformSurface.PYPROJECT},
        )
        # The infrastructure checkout publishes its Git origin (208716f4f).
        u.Tests.initialize_git_repo(
            tmp_path,
            origin_url=u.Tests.repository_ref("flext-infra").url,
        )
        pyproject = tmp_path / c.PYPROJECT_FILENAME
        source = pyproject.read_text(encoding="utf-8")
        pyproject.write_text(
            source + 'dependencies = ["custom-runtime>=0.22", '
            '"flext-custom @ ../flext-custom"]\n',
            encoding="utf-8",
        )

        result = service.plan(request)

        tm.fail(result, has="internal dependency direct source must be a git URL")

    @staticmethod
    def _conform_with_rendered_makefile(
        root: Path,
        help_text: str,
        *,
        verb: str = "probe",
    ) -> p.Result[p.Infra.CodegenResult]:
        """Apply conform after declaring ``verb`` with ``help_text``.

        The managed Makefile renders ``verb.description`` for every declared
        ``extra_verbs`` entry into its help block, so a repository manifest
        carrying multi-line help puts those exact lines in the rendered
        artifact through the production renderer -- no substitution of it.

        Returns:
            The resulting ``p.Result[p.Infra.CodegenResult]``.

        """
        distribution = u.Tests.repository_ref(config.Infra.name).distribution
        (root / "pyproject.toml").write_text(
            f'[project]\nname = "{distribution}"\nversion = "0.12.0.dev0"\n'
            f'description = "{distribution} governed fixture"\n'
            f"requires-python = "
            f'"{config.Infra.codegen.toolchain.python_required_version}"\n'
            'authors = [{name = "FLEXT Team", email = "team@flext.dev"}]\n'
            f'license = "{u.Tests.project_spec(distribution).license}"\n'
            'dependencies = ["flext-cli"]\n',
            encoding="utf-8",
        )
        package_init = root / "src" / distribution.replace("-", "_") / "__init__.py"
        package_init.parent.mkdir(parents=True, exist_ok=True)
        package_init.write_text("", encoding="utf-8")
        u.Tests.write_standalone_workspace_manifest(
            root,
            config.Infra.name,
            extra_verbs=(m.Infra.MakeVerbSpec(name=verb, description=help_text),),
        )
        return infra.codegen_conform(
            u.Tests.conform_request(
                root,
                what=c.Infra.CodegenConformSurface.MAKEFILE,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            ),
        )

    @pytest.mark.slow
    def test_setext_underline_is_accepted_as_ordinary_content(
        self,
        infra_git_repo: Path,
    ) -> None:
        """A Markdown Setext underline is content, so conform must not reject it."""
        applied = self._conform_with_rendered_makefile(
            infra_git_repo,
            "Probe verb help\n# Title\n=======\ntrailing help",
        )

        tm.ok(applied)

    @pytest.mark.slow
    def test_declared_extra_verb_shadowing_a_canonical_builtin_fails_loud(
        self,
        infra_git_repo: Path,
    ) -> None:
        """A config-declared collision is rejected, never silently dropped."""
        canonical = config.Infra.codegen.make.verbs[0].name

        with pytest.raises(
            ValueError,
            match=r"must never shadow canonical make\.verbs builtins",
        ):
            self._conform_with_rendered_makefile(
                infra_git_repo,
                canonical,
                verb=canonical,
            )

    @staticmethod
    @pytest.mark.slow
    def test_apply_recovers_declared_managed_pyproject_conflict(
        infra_git_repo: Path,
    ) -> None:
        """Repair a committed managed block through the normal apply plan."""
        root = infra_git_repo
        distribution = u.Tests.repository_ref(config.Infra.name).distribution
        (root / "pyproject.toml").write_text(
            f'[project]\nname = "{distribution}"\nversion = "0.12.0.dev0"\n'
            f'description = "{distribution} governed fixture"\n'
            f"requires-python = "
            f'"{config.Infra.codegen.toolchain.python_required_version}"\n'
            'authors = [{name = "FLEXT Team", email = "team@flext.dev"}]\n'
            f'license = "{u.Tests.project_spec(distribution).license}"\n'
            'dependencies = ["flext-cli"]\n'
            "\n"
            "[tool.pytest.ini_options]\n"
            'addopts = ["--timeout=10"]\n',
            encoding="utf-8",
        )
        package_init = root / "src" / distribution.replace("-", "_") / "__init__.py"
        package_init.parent.mkdir(parents=True, exist_ok=True)
        package_init.write_text("", encoding="utf-8")

        applied = infra.codegen_conform(
            u.Tests.conform_request(
                root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            ),
        )

        tm.ok(applied)
        rendered = (root / "pyproject.toml").read_text(encoding="utf-8")
        tm.that(rendered, lacks="<<<<<<<")
        addopts = u.Tests.toml_table_at(rendered, "tool", "pytest", "ini_options")[
            "addopts"
        ]
        tm.that(
            addopts,
            eq=list(config.Infra.tooling.tools.pytest.standard_addopts),
        )

    @staticmethod
    def _assert_editor_settings(
        settings_path: Path,
        root: Path,
        tmp_path: Path,
        editor_settings: t.JsonMapping,
    ) -> None:
        """Assert the projected VS Code editor settings are workspace-relative."""
        interpreter = u.type_adapter(str).validate_python(
            editor_settings["python.defaultInterpreterPath"],
        )
        projected_python = root / interpreter.removeprefix("${workspaceFolder}/")
        tm.that(
            projected_python.resolve(),
            eq=u.Infra.runtime_python(root, runtime_root=root),
        )
        tm.that(editor_settings["editor.wordWrap"], eq="on")
        tm.that(
            str(tmp_path) in settings_path.read_text(encoding=c.DEFAULT_ENCODING),
            eq=False,
        )

    # This end-to-end scenario scaffolds a project and runs its console entry
    # point in a fresh interpreter. The slow marker opts into the single
    # config-owned slow-item budget; tests must not restate that policy locally.
    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("name", ["flext-demo", "flext-member"])
    def test_new_project_is_complete_and_idempotent(
        tmp_path: Path,
        name: str,
    ) -> None:
        # Generation rewrites an internal_flext repository and nothing else, so
        # a scaffold that must come out complete declares that kind; the two
        # rows prove the result does not depend on the distribution name.
        """Test new project is complete and idempotent."""
        root = tmp_path / name
        settings_path = root / c.Infra.VSCODE_DIRNAME / c.Infra.VSCODE_SETTINGS_FILENAME
        settings_path.parent.mkdir(parents=True)
        settings_path.write_text(
            '{"editor.wordWrap": "on"}\n',
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that((root / c.Infra.GIT_DIR).exists(), eq=False)
        # The governed tree above the scaffold carries the committed Mise
        # declaration and lock that activate its locked tools.
        u.Tests.copy_tracked_mise_seeds(tmp_path)
        service = FlextInfraCodegenProjectNew(
            flext_source=u.Tests.flext_source(),
            name=name,
            kind=c.Infra.ProjectKind.INTERNAL_FLEXT,
            output_root=root,
            provider="flext-sh",
            repository_url=f"https://github.com/flext-sh/{name}.git",
            repository_branch="0.12.0-dev",
            flext_repository_url=u.Tests.repository_ref(config.Infra.name).url,
            flext_repository_ref=u.Tests.provider_branch(),
            license="MIT",
            author_name="FLEXT Team",
            author_email="team@flext.dev",
            upstream="flext_cli",
            year=2026,
            apply_changes=True,
        )
        first = infra.codegen_new(service)
        first_result = tm.ok(first)
        tm.that(first_result.plan is not None, eq=True)
        first_result = m.Infra.CodegenResult.model_validate(
            first_result,
            from_attributes=True,
        )
        if first_result.plan is None:
            pytest.fail("generation did not return its actual plan")
        editor_settings = u.Cli.JSON_MAPPING_ADAPTER.validate_json(
            settings_path.read_text(encoding=c.DEFAULT_ENCODING),
        )
        TestsFlextInfraCodegenConform._assert_editor_settings(
            settings_path,
            root,
            tmp_path,
            editor_settings,
        )
        tm.that(bool(first_result.written_files), eq=True)
        tm.that(first_result.written_files.count(root / "README.md"), eq=1)
        tm.that(
            (root / "README.md").read_text(encoding="utf-8"),
            has=c.Infra.GENERATED_HEADER,
        )
        tm.that(
            (root / "docs/api-reference/generated/public-api.md").read_text(
                encoding="utf-8",
            ),
            has=f"::: {u.Infra.project_package_name(root)}\n",
        )
        tm.that(
            (root / "docs/api-reference/generated/modules/index.md").is_file(),
            eq=True,
        )
        docs = tm.ok(
            FlextInfraDocGenerator(repository_root=root).generate(
                m.Infra.DocsGenerateRequest(repository_root=root),
            ),
        )
        tm.that(all(report.changed_files == 0 for report in docs), eq=True)
        tm.that(
            tuple(
                file.path
                for file in first_result.plan.files
                if u.Infra.codegen_file_requires_effect(file)
            ),
            eq=(),
        )
        makefile_plan = next(
            item
            for item in first_result.plan.files
            if item.path.name == c.Infra.MAKEFILE_FILENAME
        )
        tm.that(
            u.Tests.codegen_file_text(makefile_plan),
            has=f"MAKE_PROFILE := {c.Infra.MakeProfile.STANDALONE.value}",
        )
        tm.that(first_result.plan.request.root, eq=root.resolve())
        # A new project serializes its own identity once from the typed
        # manifest contract; later conform runs read it as input.
        (manifest,) = tm.ok(u.Infra.load_workspace_manifest(root))
        tm.that(manifest.name, eq=name)
        tm.that((root / "config" / "beads.yaml").is_file(), eq=True)
        tm.that((root / "pyproject.toml").is_file(), eq=True)
        tm.that((root / ".env.example").is_file(), eq=True)
        ruff_lint = config.Infra.tooling.tools.ruff.lint
        runtime_roots = ruff_lint.flake8_type_checking.runtime_evaluated_roots
        rendered_runtime_bases = u.Tests.toml_strings_at(
            (root / "pyproject.toml").read_text(encoding="utf-8"),
            "tool",
            "ruff",
            "lint",
            "flake8-type-checking",
            "runtime-evaluated-base-classes",
        )
        tm.that(
            tuple(rendered_runtime_bases),
            eq=u.Infra.runtime_evaluated_base_classes(root, {}, runtime_roots),
        )
        package_name = name.replace("-", "_")
        pythonpath = os.pathsep.join(
            part
            for part in (str(root / "src"), os.environ.get("PYTHONPATH", ""))
            if part
        )
        process = u.Cli.capture(
            [sys.executable, "-m", package_name, "ping"],
            cwd=root,
            options=m.Cli.ProcessOptions(env={**os.environ, "PYTHONPATH": pythonpath}),
            timeout=c.Infra.TIMEOUT_DEFAULT,
        )
        tm.ok(process)
        tm.that(process.value, eq="✅ pong")

    @staticmethod
    @pytest.mark.slow
    def test_generated_make_uses_unpinned_environment_uv(
        infra_git_repo: Path,
    ) -> None:
        """Generated Make delegates uv selection to the caller environment."""
        root = infra_git_repo
        workspace = TestsFlextInfraConformSupport.standalone_workspace(root)
        TestsFlextInfraConformSupport.apply_conform_surface(
            root,
            workspace,
            c.Infra.CodegenConformSurface.MAKEFILE,
        )
        selected = u.Cli.run_raw(
            ["make", "-C", str(root), "--dry-run", "_builtin_status_diagnostics"],
            options=m.Cli.ProcessOptions(remove_env_keys=("MAKEFLAGS",)),
        )

        selected_process = tm.ok(selected)
        selected_output = selected_process.stdout + selected_process.stderr
        tm.that(u.Cli.process_succeeded(selected_process.outcome), eq=True)
        tm.that(selected_output, has="uv --version")
        tm.that(selected_output, lacks="uv@")
        tm.that(selected_output, lacks="UV_VERSION")

    @staticmethod
    @pytest.mark.slow
    def test_existing_manifest_converges_to_identical_tree(
        infra_git_repo: Path,
    ) -> None:
        """Test existing manifest converges to identical tree."""
        existing_root = infra_git_repo
        # The scaffolded manifest is reconciled against Git on every later
        # read, so it declares the identity the fixture clone actually has.
        repository = u.Tests.repository_ref(config.Infra.name)
        created = infra.codegen_new(
            FlextInfraCodegenProjectNew(
                flext_source=u.Tests.flext_source(),
                name=repository.name,
                kind=c.Infra.ProjectKind.INTERNAL_FLEXT,
                output_root=existing_root,
                repository_url=repository.url,
                repository_branch=u.Tests.provider_branch(),
                flext_repository_url=repository.url,
                flext_repository_ref=u.Tests.provider_branch(),
                provider=repository.provider,
                license="MIT",
                author_name="FLEXT Team",
                author_email="team@flext.dev",
                upstream="flext_cli",
                year=2026,
                apply_changes=True,
            ),
        )
        tm.ok(created)
        expected_tree = TestsFlextInfraConformSupport.project_tree(existing_root)
        tm.ok(
            u.Cli.atomic_write_text_file(
                existing_root / ".gitignore",
                "# committed managed drift\n",
            ),
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                existing_root / "Makefile",
                "# committed managed drift\n",
            ),
        )
        u.Tests.commit_git_changes(existing_root, "Seed committed drift")
        migrated = infra.codegen_conform(
            u.Tests.conform_request(
                existing_root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            ),
        )
        tm.ok(migrated)
        actual_tree = TestsFlextInfraConformSupport.project_tree(existing_root)
        tm.that(
            actual_tree,
            eq=expected_tree,
            msg=TestsFlextInfraConformSupport.project_tree_diff(
                expected_tree, actual_tree
            ),
        )

    @staticmethod
    @pytest.mark.slow
    def test_python_root_outside_env_dirs_still_reaches_a_fixed_point(
        infra_git_repo: Path,
    ) -> None:
        """The gen verb converges for a Python root beyond declarative env_dirs.

        Two derivations used to select the pyright execution environments: the
        dependency command discovered roots ON DISK, while conform planned them
        from declarative ``env_dirs``. A project owning a Python directory
        outside that list therefore oscillated between two writers. Conform is
        the sole generation owner, so it must discover and preserve the extra
        root by itself and immediately reach a fixed point.
        """
        root = infra_git_repo
        TestsFlextInfraConformSupport.seed_infra_package_tree(root)
        # The defect needs a Python root the declarative env_dirs never lists.
        extra_root = "tools"
        module = root / extra_root / "maintenance.py"
        module.parent.mkdir(parents=True, exist_ok=True)
        tm.ok(u.Cli.atomic_write_text_file(module, "VALUE = 1\n"))
        tm.that(
            extra_root
            in u.Infra.discover_python_dirs(
                root,
                workspace_excluded_top_dirs=(
                    FlextInfraWorkspaceDetector.analysis_excluded_top_dirs(
                        root,
                    ).unwrap()
                ),
            ),
            eq=True,
        )
        tm.that(
            extra_root in config.Infra.tooling.tools.pyright.path_rules.env_dirs,
            eq=False,
        )
        tm.ok(u.Cli.run_checked(["git", "add", "-A"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Seed python root beyond env_dirs"],
                cwd=root,
            ),
        )

        applied = infra.codegen_conform(
            u.Tests.conform_request(
                root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            ),
        )
        tm.ok(applied)

        _assert_conform_check_reaches_fixed_point(root)

    @staticmethod
    @pytest.mark.slow
    def test_empty_rendered_directory_is_not_a_python_root(
        infra_git_repo: Path,
    ) -> None:
        """Test empty rendered directory is not a python root."""
        root = infra_git_repo
        TestsFlextInfraConformSupport.seed_infra_package_tree(root)
        (root / "scripts").mkdir()

        result = infra.codegen_conform(
            u.Tests.conform_request(
                root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            ),
        )

        tm.ok(result)
        tm.that(
            u.Tests.toml_table_at(
                (root / "pyproject.toml").read_text(encoding="utf-8"),
                "tool",
                "pyrefly",
            )["project-includes"],
            lacks="scripts/**/*.py*",
        )
        tm.that(
            u.Tests.toml_table_at(
                (root / "pyproject.toml").read_text(encoding="utf-8"),
                "tool",
                "pyright",
            )["include"],
            lacks="scripts",
        )

    # Two conform apply cycles plus a check exercise the slow integration harness.
    @staticmethod
    @pytest.mark.slow
    def test_manifestless_existing_root_plans_artifacts_without_project_spec(
        infra_git_repo: Path,
    ) -> None:
        """Test manifestless existing root plans artifacts without project spec."""
        root = infra_git_repo
        repository = u.Tests.repository_ref(
            config.Infra.name,
            role=c.Infra.MakeProfile.STANDALONE,
        )
        local_repository = repository.model_copy(update={"path": Path()})
        create_only = {
            "LICENSE": "existing license\n",
            "custom.mk": "_custom-status-diagnostics:\n\t@true\n",
        }
        TestsFlextInfraConformSupport.seed_infra_package_tree(root)
        for relative, content in create_only.items():
            tm.ok(u.Cli.atomic_write_text_file(root / relative, content))
        u.Tests.commit_git_changes(root, "Seed manifest-less tree")

        derived = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))
        tm.that(derived.repository, eq=local_repository)
        tm.that(derived.project, eq=None)

        request = u.Tests.conform_request(
            root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        initial_plan = tm.ok(
            FlextInfraCodegenConform(repository_root=root).plan(request),
        )
        plans = {
            file.path.relative_to(root).as_posix(): file for file in initial_plan.files
        }
        for required in ("Makefile", ".mise.toml", ".python-version", ".gitignore"):
            tm.that(u.Infra.codegen_file_requires_effect(plans[required]), eq=True)

        applied = infra.codegen_conform(request)
        tm.ok(applied)
        for relative, content in create_only.items():
            tm.that((root / relative).read_text(encoding="utf-8"), eq=content)
        tm.that((root / "Makefile").is_file(), eq=True)
        tm.that((root / ".mise.toml").is_file(), eq=True)
        tm.that((root / ".python-version").is_file(), eq=True)
        tm.that((root / ".gitignore").is_file(), eq=True)
        tm.that((root / ".env.example").exists(), eq=False)
        tm.that(root / ".env.example" in applied.value.written_files, eq=False)
        tm.ok(
            FlextInfraCodegenMiseArtifacts(repository_root=root).validate_artifacts(
                root,
                root,
            ),
        )

        _assert_conform_check_reaches_fixed_point(root)

    @staticmethod
    @pytest.mark.slow
    def test_repository_root_catalog_profile_projects_no_coverage_floor(
        tmp_path: Path,
    ) -> None:
        """Route an arbitrary workspace root through its typed catalog profile."""
        provider = u.Tests.provider()
        repository = u.Tests.repository_ref("arbitrary-root").model_copy(
            update={
                "name": "arbitrary-root",
                "distribution": "arbitrary-root",
                "url": f"{provider.base_url}/arbitrary-root.git",
                "path": Path(),
                "role": c.Infra.MakeProfile.WORKSPACE,
                "package": False,
                "editable": False,
            },
        )
        workspace = u.Tests.workspace_spec(
            repository,
            project=u.Tests.project_spec("arbitrary-root"),
        )
        root = tmp_path / "arbitrary-root"
        u.Tests.copy_tracked_mise_seeds(tmp_path)
        service, request = TestsFlextInfraConformSupport.check_conform_service(
            root,
            workspace,
        )

        first = tm.ok(service.plan(request))
        second = tm.ok(service.plan(request))
        first_pyproject = next(
            item for item in first.files if item.path.name == c.PYPROJECT_FILENAME
        )
        second_pyproject = next(
            item for item in second.files if item.path.name == c.PYPROJECT_FILENAME
        )
        rendered_pyproject = u.Tests.codegen_file_text(first_pyproject)
        report = u.Tests.toml_table_at(rendered_pyproject, "tool", "coverage", "report")
        addopts = u.Tests.toml_strings_at(
            rendered_pyproject,
            "tool",
            "pytest",
            "ini_options",
            "addopts",
        )
        pytest_policy = config.Infra.tooling.tools.pytest

        tm.that(
            u.Tests.codegen_file_text(second_pyproject),
            eq=u.Tests.codegen_file_text(first_pyproject),
        )
        tm.that(addopts, eq=list(pytest_policy.standard_addopts))
        tm.that(report, lacks="fail_under")

    @staticmethod
    @pytest.mark.slow
    def test_project_root_inherits_declared_upstream_facets(
        tmp_path: Path,
    ) -> None:
        # A lone consumer tree composes no members, so Git derives standalone.
        """Test project root inherits declared upstream facets."""
        repository = u.Tests.repository_ref(
            "consumer",
            role=c.Infra.MakeProfile.STANDALONE,
        )
        project = u.Tests.project_spec("consumer").model_copy(
            update={"upstream": "flext_cli"},
        )
        workspace = u.Tests.workspace_spec(repository, project=project)
        root = tmp_path / "consumer"
        u.Tests.copy_tracked_mise_seeds(tmp_path)
        tm.ok(
            infra.codegen_conform(
                u.Tests.conform_request(
                    root,
                    scope=c.Infra.CodegenConformScope.SELF,
                    mode=c.Infra.CodegenConformMode.APPLY,
                ),
                initial_workspace=workspace,
            ),
        )
        package_root = (root / "src/consumer/__init__.py").read_text(encoding="utf-8")
        entries, _refs = u.Infra.lazy_import_mapping_source(package_root)
        tm.that(dict(entries).get("flext_cli", ()), has="r")
        tm.that(package_root, has='"r"')
