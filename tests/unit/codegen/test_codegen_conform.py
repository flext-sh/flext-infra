"""Public functional contract for new and existing project conformance.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import override

import pytest

from flext_infra import config, infra
from flext_infra.codegen import (
    FlextInfraCodegenConform,
    FlextInfraCodegenMakeBootstrap,
    FlextInfraCodegenMiseToolchainProof,
)
from flext_infra.docs import FlextInfraDocGenerator
from flext_infra.workspace import FlextInfraWorkspaceDetector
from tests import c, m, p, r, t, tm, u
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


class TestsFlextInfraCodegenConformLifecycleProbe(FlextInfraCodegenConform.Generate):
    """Exercise native planning failures without replacing owners."""

    __test__ = False

    @classmethod
    @override
    def plan_repository_task(
        cls,
        task: m.Infra.CodegenRepositoryPlanTask,
        snapshot: p.Infra.WorkspaceSnapshot,
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
        return super().plan_repository_task(task, snapshot)

    @override
    def plan(
        self,
        request: p.Infra.CodegenGenerateRequest,
    ) -> p.Result[m.Infra.CodegenPlan]:
        """Reject one planned target with a native planning exception.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenPlan]``.

        """
        planned = super().plan(request)
        if planned.failure or request.root.name != "planning-exception":
            return planned
        independent = tuple(
            file
            for file in planned.value.files
            if file.path.name in {c.Infra.MAKEFILE_FILENAME, c.Infra.MISE_TOML_FILENAME}
        )
        expected = next(
            file for file in independent if file.path.name == c.Infra.MAKEFILE_FILENAME
        )
        (request.root.parent / ".lifecycle-expected").write_bytes(
            tm.not_none(expected.desired_content),
        )
        return r[m.Infra.CodegenPlan].ok(
            m.Infra.CodegenPlan.model_validate({
                **dict(planned.value),
                "files": independent,
                "exception": _LIFECYCLE_EXCEPTION,
                "issues": (
                    *planned.value.issues,
                    m.Infra.Issue(
                        file=str(request.root / c.Infra.GITIGNORE),
                        line=0,
                        column=0,
                        code=c.Infra.ToolOutcome.ERROR.value,
                        message=str(_LIFECYCLE_EXCEPTION),
                    ),
                ),
            }),
        )


class TestsFlextInfraCodegenConform:
    """Prove one SSOT for project creation and existing-tree conformance."""

    @staticmethod
    def _declare_new_project(
        root: Path, name: str, project: m.Infra.ProjectSpec
    ) -> None:
        """Prepare Git and the target's typed declaration before initialization."""
        root.mkdir(parents=True, exist_ok=True)
        repository = u.Tests.repository_ref(
            name,
            role=c.Infra.MakeProfile.STANDALONE,
        )
        integration = u.Tests.integration()
        u.Tests.initialize_unborn_git_repo(
            root,
            origin_url=repository.url,
            branch=integration.branch,
        )
        u.Tests.copy_tracked_mise_seeds(root)
        u.Tests.write_project_beads_config(root, name)
        declaration = m.Infra.RepositoryDeltaSpec(
            project=project,
            integration=integration,
            kind=repository.kind,
        )
        tm.ok(
            u.Cli.yaml_dump(
                root / c.CONFIG_DIR_NAME / c.Infra.CODEGEN_CONFIG_FILENAME,
                {
                    "Infra": {
                        "codegen": {
                            "repository": declaration.model_dump(
                                mode="json", exclude_unset=True
                            ),
                        },
                    },
                },
            )
        )

    @staticmethod
    @pytest.fixture(scope="module")
    def conformed_template(
        tmp_path_factory: pytest.TempPathFactory,
    ) -> Path:
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
        u.Tests.standalone_workspace(template, config.Infra.name)
        request = u.Tests.conform_request(
            template,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        tm.ok(infra.codegen_conform(request))
        u.Tests.commit_git_changes(template, "Seed conformed lifecycle fixture")
        return template

    @staticmethod
    def _lifecycle_fixture(
        tmp_path: Path,
        scenario: str,
        template: Path,
    ) -> tuple[Path, m.Infra.CodegenConformRequest, Path, bytes]:
        """Clone the conformed template, then introduce one recoverable publication.

        Returns:
            The resulting ``tuple[Path, m.Infra.CodegenConformRequest, Path, bytes]``.

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
        if scenario == "planning-exception":
            ignored = root / c.Infra.GITIGNORE
            ignored.write_bytes(ignored.read_bytes() + b"\n# rejected drift\n")
        request = u.Tests.conform_request(
            root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        return root, request, published, original

    def test_public_generation_preserves_independent_gains_after_failure(
        self,
        tmp_path: Path,
        conformed_template: Path,
    ) -> None:
        """Reject a causal target without abandoning independent planned work."""
        root, request, published, original = self._lifecycle_fixture(
            tmp_path,
            "planning-exception",
            conformed_template,
        )
        rejected = root / c.Infra.GITIGNORE
        rejected_before = rejected.read_bytes()
        with pytest.raises(OSError, match="raised after begin") as raised:
            TestsFlextInfraCodegenConformLifecycleProbe.execute_request(
                request,
                execution_context=infra,
            )
        tm.ok(raised.value is _LIFECYCLE_EXCEPTION)
        tm.fail(published.read_bytes() == original)
        tm.that(
            published.read_bytes(),
            eq=(root.parent / ".lifecycle-expected").read_bytes(),
        )
        tm.that(rejected.read_bytes(), eq=rejected_before)

    def test_public_planning_reports_exception_only_outcome_as_failed(
        self,
        tmp_path: Path,
        conformed_template: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Progress and persisted evidence cannot call an exception-only worker OK."""
        root, request, _published, _original = self._lifecycle_fixture(
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
        tm.ok(bool(plan.issues))
        evidence = m.Infra.CodegenPlanningReport.model_validate_json(
            (
                tm.ok(u.Infra.refactor_report_evidence_root(root))
                / c.Infra.CODEGEN_PLAN_REPORT_RELATIVE_PATH
            ).read_bytes(),
        )
        tm.that(evidence.outcomes, len=1)
        tm.that(evidence.outcomes[0].error, eq=str(_LIFECYCLE_EXCEPTION))
        tm.that(evidence.outcomes[0].error_type, eq="builtins.OSError")
        tm.that(capsys.readouterr().out, lacks="[OK]")

    @pytest.mark.parametrize(
        ("operation", "mode"),
        [
            ("generate", c.Infra.CodegenConformMode.APPLY),
            ("conform", c.Infra.CodegenConformMode.APPLY),
            ("conform", c.Infra.CodegenConformMode.CHECK),
        ],
    )
    def test_public_generation_rejects_diagnostics_without_an_exception(
        self,
        tmp_path: Path,
        conformed_template: Path,
        mode: c.Infra.CodegenConformMode,
        operation: str,
    ) -> None:
        """A rejected Make declaration fails even beside admitted projections."""
        root, _request, _published, _original = self._lifecycle_fixture(
            tmp_path,
            "declaration-diagnostic",
            conformed_template,
        )
        (root / "custom.mk").write_text(
            "UNDECLARED_PUBLIC_VARIABLE := invalid\n",
            encoding=c.DEFAULT_ENCODING,
        )
        request = u.Tests.conform_request(
            root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=mode,
        )
        plan = tm.ok(
            FlextInfraCodegenConform.Generate(repository_root=root).plan(request)
        )
        tm.ok(bool(plan.files))
        tm.ok(bool(plan.issues))
        tm.that(plan.exception, eq=None)

        result = (
            infra.codegen_generate(request)
            if operation == "generate"
            else infra.codegen_conform(request)
        )

        tm.ok(result.failure)
        tm.that(result.error, has="custom.mk")
        tm.that(result.error, has="declares a variable")

    @pytest.mark.parametrize(
        "scenario", ["concurrent-edit", "lazy-failure", "docs-failure"]
    )
    def test_public_apply_fails_without_overwriting_live_state(
        self,
        tmp_path: Path,
        conformed_template: Path,
        scenario: str,
    ) -> None:
        """A failed apply keeps independent gains and never overwrites an edit."""
        root, request, published, original = self._lifecycle_fixture(
            tmp_path,
            scenario,
            conformed_template,
        )
        if scenario == "docs-failure":
            with pytest.raises(ValueError, match="Invalid JSON"):
                FlextInfraCodegenConform.execute_request(
                    request, execution_context=infra
                )
            tm.fail(published.read_bytes() == original)
            return
        if scenario == "lazy-failure":
            tm.fail(
                FlextInfraCodegenConform.execute_request(
                    request, execution_context=infra
                ),
                has="refusing obsolete root-support symlink",
            )
            tm.fail(published.read_bytes() == original)
            return
        planned = tm.ok(
            FlextInfraCodegenConform.Generate(repository_root=root).plan(request)
        )
        target = next(file for file in planned.files if file.path == published)
        foreign = original + b"# concurrent edit\n"
        published.write_bytes(foreign)
        tm.fail(u.Infra.publish_codegen_plans(root, (target,)), has=str(published))
        tm.that(published.read_bytes(), eq=foreign)

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

        plan = tm.ok(service.plan(request))

        tm.that(
            "\n".join(issue.message for issue in plan.issues),
            has="internal dependency direct source must be a git URL",
        )
        tm.that(
            tuple(file for file in plan.files if file.path == pyproject),
            eq=(),
        )

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
        (root / c.PYPROJECT_FILENAME).write_text(
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
        declaration = m.Infra.RepositoryDeltaSpec(
            kind=u.Tests.repository_ref(config.Infra.name).kind,
            extra_verbs=(m.Infra.MakeVerbSpec(name=verb, description=help_text),),
        )
        tm.ok(
            u.Cli.yaml_dump(
                root / c.CONFIG_DIR_NAME / c.Infra.CODEGEN_CONFIG_FILENAME,
                {
                    "Infra": {
                        "codegen": {
                            "repository": declaration.model_dump(
                                mode="json", exclude_unset=True
                            ),
                        },
                    },
                },
            )
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

        tm.fail(
            self._conform_with_rendered_makefile(
                infra_git_repo,
                canonical,
                verb=canonical,
            ),
            has="must never shadow canonical make.verbs builtins",
        )
        tm.that((infra_git_repo / c.Infra.MAKEFILE_FILENAME).exists(), eq=False)

    @staticmethod
    @pytest.mark.slow
    def test_apply_recovers_declared_managed_pyproject_conflict(
        infra_git_repo: Path,
    ) -> None:
        """Repair a committed managed block through the normal apply plan."""
        root = infra_git_repo
        distribution = u.Tests.repository_ref(config.Infra.name).distribution
        (root / c.PYPROJECT_FILENAME).write_text(
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
        rendered = (root / c.PYPROJECT_FILENAME).read_text(encoding="utf-8")
        tm.that(rendered, lacks="<<<<<<<")
        addopts = u.Tests.toml_table_at(rendered, "tool", "pytest", "ini_options")[
            "addopts"
        ]
        tm.that(
            addopts,
            eq=list(
                u.Infra.native_tool_setting(
                    config.Infra.tooling, "pytest.ini_options", "addopts", Sequence[str]
                )
            ),
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
        tm.that(editor_settings["editor.wordWrap"], eq=c.ParserBooleanToken.ON)
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
            '{"editor.wordWrap": c.ParserBooleanToken.ON}\n',
            encoding=c.DEFAULT_ENCODING,
        )
        TestsFlextInfraCodegenConform._declare_new_project(
            root,
            name,
            u.Tests.project_spec(name).model_copy(update={"upstream": "flext_cli"}),
        )
        tm.ok(
            FlextInfraCodegenMakeBootstrap(
                repository_root=root,
                kind=c.Infra.ProjectKind.INTERNAL_FLEXT,
                apply_changes=True,
            ).execute(),
            eq=True,
        )
        request = u.Tests.conform_request(
            root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        plan = tm.ok(
            FlextInfraCodegenConform.Generate(repository_root=root).plan(request)
        )
        editor_settings = u.Cli.JSON_MAPPING_ADAPTER.validate_json(
            settings_path.read_text(encoding=c.DEFAULT_ENCODING),
        )
        TestsFlextInfraCodegenConform._assert_editor_settings(
            settings_path,
            root,
            tmp_path,
            editor_settings,
        )
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
        tm.ok(all(report.changed_files == 0 for report in docs))
        tm.that(
            tuple(
                file.path
                for file in plan.files
                if u.Infra.codegen_file_requires_effect(file)
            ),
            eq=(),
        )
        makefile_plan = next(
            item for item in plan.files if item.path.name == c.Infra.MAKEFILE_FILENAME
        )
        tm.that(
            u.Tests.codegen_file_text(makefile_plan),
            has=f"MAKE_PROFILE := {c.Infra.MakeProfile.STANDALONE.value}",
        )
        tm.that(plan.request.root, eq=root.resolve())
        manifest = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))
        tm.that(manifest.name, eq=name)
        tm.ok((root / "config" / "beads.yaml").is_file())
        tm.ok((root / c.PYPROJECT_FILENAME).is_file())
        tm.ok((root / ".env.example").is_file())
        ruff_lint = config.Infra.tooling.tools.ruff.lint
        runtime_roots = ruff_lint.flake8_type_checking.runtime_evaluated_roots
        rendered_runtime_bases = u.Tests.toml_strings_at(
            (root / c.PYPROJECT_FILENAME).read_text(encoding="utf-8"),
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
        tm.ok(process, eq="✅ pong")

    @staticmethod
    @pytest.mark.slow
    def test_generated_make_uses_declared_native_uv(
        infra_git_repo: Path,
    ) -> None:
        """Inspect the generated selection and execute its declared native UV."""
        root = infra_git_repo
        workspace = TestsFlextInfraConformSupport.standalone_workspace(root)
        TestsFlextInfraConformSupport.apply_conform_surface(
            root,
            workspace,
            c.Infra.CodegenConformSurface.MAKEFILE,
        )
        selected = next(
            line
            for line in (root / c.Infra.MAKEFILE_FILENAME).read_text().splitlines()
            if line.startswith("override UV =")
        )
        tool = next(
            tool for tool in config.Infra.codegen.toolchain.tools if tool.name == "uv"
        )
        selector = tool.selector or tool.name
        tm.that(selected, has='mise -C "$(RUNTIME_ROOT)" which')
        tm.that(
            selected, has=f'which "{tool.version_probe.binary}" --tool "{selector}@'
        )
        tm.that(selected, has=f'tool "{selector}" --requested')
        tm.that(selected, lacks="UV_VERSION")
        binary = tm.ok(u.Infra.managed_mise_binary(tool.name, root))
        reader = tm.ok(u.Infra.managed_mise_self(root))
        pinned = tm.ok(u.Infra.locked_mise_version(root, selector, tool.version))
        install_root = Path(
            tm.ok(
                u.Cli.capture(
                    (str(reader), "-C", str(root), "where", f"{selector}@{pinned}"),
                    cwd=root,
                    timeout=c.Infra.TIMEOUT_SHORT,
                ),
            ),
        )
        tm.ok(
            FlextInfraCodegenMiseToolchainProof.installation(
                tool, pinned, (install_root, binary)
            ),
        )

    @staticmethod
    @pytest.mark.slow
    def test_existing_manifest_converges_to_identical_tree(
        tmp_path: Path,
        conformed_template: Path,
    ) -> None:
        """Test existing manifest converges to identical tree."""
        existing_root = tmp_path / "existing"
        shutil.copytree(conformed_template, existing_root)
        tm.that(
            tm.ok(u.Infra.exact_worktree_root(existing_root)).head_oid is not None,
            eq=True,
        )
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
                (root / c.PYPROJECT_FILENAME).read_text(encoding="utf-8"),
                "tool",
                "pyrefly",
            )["project-includes"],
            lacks="scripts/**/*.py*",
        )
        tm.that(
            u.Tests.toml_table_at(
                (root / c.PYPROJECT_FILENAME).read_text(encoding="utf-8"),
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
        create_only = {
            "LICENSE": "existing license\n",
            "custom.mk": "_custom-status-diagnostics:\n\t@true\n",
        }
        TestsFlextInfraConformSupport.seed_infra_package_tree(root)
        for relative, content in create_only.items():
            tm.ok(u.Cli.atomic_write_text_file(root / relative, content))
        u.Tests.commit_git_changes(root, "Seed manifest-less tree")

        derived = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))
        tm.that(derived.repository.name, eq=repository.name)
        tm.that(derived.repository.distribution, eq=repository.distribution)
        tm.that(derived.repository.url, eq=repository.url)
        tm.that(derived.repository.role, eq=repository.role)
        tm.that(derived.repository.path, eq=Path())
        tm.that(derived.project, eq=None)

        request = u.Tests.conform_request(
            root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        initial_plan = tm.ok(
            FlextInfraCodegenConform.Generate(repository_root=root).plan(request),
        )
        plans = {
            file.path.relative_to(root).as_posix(): file for file in initial_plan.files
        }
        for required in ("Makefile", ".mise.toml", ".python-version", ".gitignore"):
            tm.that(plans[required].path, eq=root / required)
            if not (root / required).exists():
                tm.ok(u.Infra.codegen_file_requires_effect(plans[required]))

        applied = infra.codegen_conform(request)
        tm.ok(applied)
        for relative, content in create_only.items():
            tm.that((root / relative).read_text(encoding="utf-8"), eq=content)
        tm.ok((root / "Makefile").is_file())
        tm.ok((root / ".mise.toml").is_file())
        tm.ok((root / ".python-version").is_file())
        tm.ok((root / ".gitignore").is_file())
        tm.fail((root / ".env.example").exists())
        tm.fail(root / ".env.example" in applied.value.written_files)

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
        root.mkdir()
        u.Tests.initialize_git_repo(root, origin_url=repository.url)
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

        tm.that(
            u.Tests.codegen_file_text(second_pyproject),
            eq=u.Tests.codegen_file_text(first_pyproject),
        )
        tm.that(
            addopts,
            eq=tuple(
                u.Infra.native_tool_setting(
                    config.Infra.tooling, "pytest.ini_options", "addopts", Sequence[str]
                )
            ),
        )
        tm.that(report, lacks="fail_under")

    @staticmethod
    @pytest.mark.slow
    def test_project_root_inherits_declared_upstream_facets(
        tmp_path: Path,
    ) -> None:
        # A lone consumer tree composes no members, so Git derives standalone.
        """Test project root inherits declared upstream facets."""
        project = u.Tests.project_spec("consumer").model_copy(
            update={"upstream": "flext_cli"},
        )
        root = tmp_path / "consumer"
        TestsFlextInfraCodegenConform._declare_new_project(root, "consumer", project)
        tm.ok(
            FlextInfraCodegenMakeBootstrap(
                repository_root=root,
                kind=c.Infra.ProjectKind.INTERNAL_FLEXT,
                apply_changes=True,
            ).execute(),
        )
        package_root = (root / "src/consumer/__init__.py").read_text(encoding="utf-8")
        entries, _refs = u.Infra.lazy_import_mapping_source(package_root)
        tm.that(dict(entries).get("flext_cli", ()), has="r")
        tm.that(package_root, has='"r"')
