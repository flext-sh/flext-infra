"""Test utilities for flext-infra."""

from __future__ import annotations

from flext_infra import u as flext_infra_u
from flext_tests import FlextTestsUtilities
from tests import m
from tests.utilities_codegen import TestsFlextInfraUtilitiesCodegenMixin
from tests.utilities_deps import TestsFlextInfraUtilitiesDepsMixin
from tests.utilities_fixture_docs import TestsFlextInfraUtilitiesDocsFixtureMixin
from tests.utilities_fixture_project import TestsFlextInfraUtilitiesProjectFixtureMixin
from tests.utilities_fixture_tooling import TestsFlextInfraUtilitiesToolingFixtureMixin
from tests.utilities_fixture_workspace import (
    TestsFlextInfraUtilitiesWorkspaceFixtureMixin,
)
from tests.utilities_gates import TestsFlextInfraUtilitiesGatesMixin
from tests.utilities_git import TestsFlextInfraUtilitiesGitMixin
from tests.utilities_release import TestsFlextInfraUtilitiesReleaseMixin
from tests.utilities_replay import TestsFlextInfraUtilitiesReplayRunnerMixin
from tests.utilities_replay_sequence import TestsFlextInfraUtilitiesReplaySequenceMixin
from tests.utilities_toml import TestsFlextInfraUtilitiesTomlMixin
from tests.utilities_workspace_env import TestsFlextInfraUtilitiesWorkspaceEnvMixin


class TestsFlextInfraUtilities(FlextTestsUtilities, flext_infra_u):
    """Typed test utilities for flext-infra."""

    class Tests(
        TestsFlextInfraUtilitiesTomlMixin,
        TestsFlextInfraUtilitiesReplayRunnerMixin,
        TestsFlextInfraUtilitiesReplaySequenceMixin,
        TestsFlextInfraUtilitiesProjectFixtureMixin,
        TestsFlextInfraUtilitiesWorkspaceFixtureMixin,
        TestsFlextInfraUtilitiesToolingFixtureMixin,
        TestsFlextInfraUtilitiesDocsFixtureMixin,
        TestsFlextInfraUtilitiesReleaseMixin,
        TestsFlextInfraUtilitiesGitMixin,
        TestsFlextInfraUtilitiesGatesMixin,
        TestsFlextInfraUtilitiesCodegenMixin,
        TestsFlextInfraUtilitiesDepsMixin,
        TestsFlextInfraUtilitiesWorkspaceEnvMixin,
        FlextTestsUtilities.Tests,
    ):
        """Canonical test helper namespace."""

        @staticmethod
            declared_subproject: bool = False,
        ) -> m.Infra.ProjectInfo:
            """Provide the typed test helper `create_project_info`."""
            return m.Infra.ProjectInfo(
                name=name,
                path=project_root,
                stack=stack,
                has_tests=has_tests,
                has_src=has_src,
                project_class=project_class,
                package_name=package_name,
                make_profile=make_profile,
                declared_subproject=declared_subproject,
            )

        @staticmethod
        def create_command_output(
            *,
            stdout: str = "",
            stderr: str = "",
            exit_code: int = 0,
            duration: float = 0.0,
        ) -> m.Cli.CommandOutput:
            """Provide the typed test helper `create_command_output`."""
            return m.Cli.CommandOutput(
                stdout=stdout,
                stderr=stderr,
                outcome=m.Cli.ProcessOutcome(
                    raw_return_code=exit_code, timed_out=False, forwarded_signal=None
                ),
                duration=duration,
            )

        @staticmethod
        def create_deptry_service(
            *,
            projects: t.SequenceOf[m.Infra.ProjectInfo] | None = None,
            selection_error: str | None = None,
            command_output: m.Cli.CommandOutput | None = None,
            run_error: str | None = None,
        ) -> FlextInfraDependencyDetectionService:
            """Provide the typed test helper `create_deptry_service`."""
            service = FlextInfraDependencyDetectionService()
            service.selector = TestsFlextInfraUtilities.Tests.DeptrySelector(
                r[Sequence[m.Infra.ProjectInfo]].fail(selection_error)
                if selection_error is not None
                else r[Sequence[m.Infra.ProjectInfo]].ok(list(projects or []))
            )
            service.runner = TestsFlextInfraUtilities.Tests.DeptryRunner(
                r[m.Cli.CommandOutput].fail(run_error)
                if run_error is not None
                else r[m.Cli.CommandOutput].ok(
                    command_output
                    or TestsFlextInfraUtilities.Tests.create_command_output()
                )
            )
            return service

        @staticmethod
        def ruff_per_file_ignores_toml() -> str:
            """Render the fleet Ruff policy as a pyproject fragment.

            Reads the same typed SSOT production reads (P0): fixture
            workspaces carry the real policy — select, ignore, preview and
            the per-file-ignores map — never a hand-rolled fragment.
            """
            ruff_cfg = config.Infra.tooling.tools.ruff
            select = ", ".join(f'"{rule}"' for rule in sorted(ruff_cfg.lint.select))
            ignore = ", ".join(
                f'"{rule}"'
                for rule in sorted({
                    *ruff_cfg.lint.ignore,
                    *ruff_cfg.lint.ignored_rule_rationales,
                })
            )
            rows = "\n".join(
                f'"{pattern}" = [{", ".join(f'"{rule}"' for rule in rules)}]'
                for pattern, rules in sorted(ruff_cfg.lint.per_file_ignores.items())
            )
            return (
                f"[tool.ruff]\npreview = {str(ruff_cfg.preview).lower()}\n\n"
                f"[tool.ruff.lint]\nselect = [{select}]\nignore = [{ignore}]\n\n"
                f"[tool.ruff.lint.per-file-ignores]\n{rows}\n"
            )

        @staticmethod
        def create_lazy_init_workspace(
            tmp_path: Path,
            *,
            project_name: str = "flext-test-project",
            package_name: str = "flext_test_project",
        ) -> tuple[Path, Path]:
            """Provide the typed test helper `create_lazy_init_workspace`."""
            workspace_root = tmp_path / project_name
            package_root = workspace_root / c.Infra.DEFAULT_SRC_DIR / package_name
            package_root.mkdir(parents=True)
            (workspace_root / "Makefile").write_text(
                "check:\n\t@true\n", encoding=c.Infra.ENCODING_DEFAULT
            )
            (workspace_root / c.Infra.PYPROJECT_FILENAME).write_text(
                (
                    f'[project]\nname = "{project_name}"\nversion = "0.1.0"\n\n'
                    + TestsFlextInfraUtilities.Tests.ruff_per_file_ignores_toml()
                ),
                encoding=c.Infra.ENCODING_DEFAULT,
            )
            (package_root / c.Infra.INIT_PY).write_text(
                "", encoding=c.Infra.ENCODING_DEFAULT
            )
            TestsFlextInfraUtilities.Tests.write_project_beads_config(
                workspace_root, project_name
            )
            return (workspace_root, package_root)

        @staticmethod
        def write_lazy_init_namespace_module(
            module_path: Path,
            *,
            class_name: str,
            alias: str,
            docstring: str = "Test namespace.",
            extra_class_names: t.StrSequence = (),
        ) -> None:
            """Write a namespace module fixture for lazy-export tests."""
            export_list = f'"{class_name}", "{alias}"'
            extra_classes = "".join(
                f"\nclass {extra_class_name}:\n    pass\n"
                for extra_class_name in extra_class_names
            )
            module_path.write_text(
                (
                    f'"""{docstring}"""\n\n'
                    "from __future__ import annotations\n\n"
                    f"__all__: list[str] = [{export_list}]\n\n"
                    f"class {class_name}:\n"
                    "    pass\n\n"
                    f"{alias} = {class_name}\n"
                    f"{extra_classes}"
                ),
                encoding=c.Infra.ENCODING_DEFAULT,
            )

        @staticmethod
        def write_lazy_init_version_module(package_root: Path) -> None:
            """Write a version module fixture for lazy-export tests."""
            (package_root / "__version__.py").write_text(
                ('__version__ = "0.1.0"\n__version_info__ = (0, 1, 0)\n'),
                encoding=c.Infra.ENCODING_DEFAULT,
            )

        @staticmethod
        def run_lazy_init(workspace_root: Path, *, check_only: bool = False) -> int:
            """Materialize immutable lazy-init plans only inside test workspaces."""
            service = FlextInfraCodegenLazyInit(repository_root=workspace_root)
            planned_result = service.plan_files()
            if planned_result.failure:
                return 1
            planned = planned_result.value
            changed = tuple(
                plan
                for plan in planned.files
                if u.Infra.codegen_file_requires_effect(plan)
            )
            if check_only:
                return len(changed)
            materialized = TestsFlextInfraUtilities.Tests.materialize_codegen_plans(
                r[tuple[m.Infra.CodegenFilePlan, ...]].ok(planned.files)
            )
            return 0 if materialized.success else 1

        @staticmethod
        def materialize_lazy_init(service: FlextInfraCodegenLazyInit) -> p.Result[bool]:
            """Publish one service plan through canonical guarded file primitives."""
            planned = service.plan_files()
            if planned.failure:
                return r[bool].from_failure(planned)
            return TestsFlextInfraUtilities.Tests.materialize_codegen_plans(
                r[tuple[m.Infra.CodegenFilePlan, ...]].ok(planned.value.files)
            )

        @staticmethod
        def materialize_docs_bundle(
            bundle: m.Infra.DocsGenerationBundle,
        ) -> p.Result[bool]:
            """Publish one immutable docs bundle through atomic file primitives."""
            required = u.Infra.docs_required_directories(bundle)
            if required.failure:
                return r[bool].from_failure(required)
            for directory in required.value:
                directory_plan = u.Cli.atomic_plan_directory_chain(directory)
                if directory_plan.failure:
                    return r[bool].from_failure(directory_plan)
                if directory_plan.value.directories:
                    created = u.Cli.atomic_create_directory_chain_guarded(
                        directory_plan.value, permission_mode=0o755
                    )
                    if created.failure:
                        return r[bool].from_failure(created)
            return TestsFlextInfraUtilities.Tests.materialize_codegen_plans(
                u.Infra.docs_file_plans(bundle)
            )

        @staticmethod
        def materialize_codegen_plans(
            planned: p.Result[tuple[m.Infra.CodegenFilePlan, ...]],
        ) -> p.Result[bool]:
            """Publish immutable codegen plans only inside test workspaces."""
            if planned.failure:
                return r[bool].from_failure(planned)
            changed = tuple(
                plan
                for plan in planned.value
                if u.Infra.codegen_file_requires_effect(plan)
            )
            for plan in changed:
                before = u.Infra.codegen_file_before_state(plan)
                if before.failure:
                    return r[bool].from_failure(before)
                if plan.desired_content is None:
                    result = u.Cli.atomic_delete_binary_file_guarded(before.value)
                else:
                    if plan.desired_mode is None:
                        return r[bool].fail(
                            f"lazy-init plan has no desired mode: {plan.path}"
                        )
                    result = u.Cli.atomic_write_binary_file_guarded(
                        before.value,
                        plan.desired_content,
                        permission_mode=plan.desired_mode,
                    )
                if result.failure:
                    return r[bool].from_failure(result)
            return r[bool].ok(True)

        @staticmethod
        def create_lazy_init_service(workspace_root: Path) -> FlextInfraCodegenLazyInit:
            """Provide the typed test helper `create_lazy_init_service`."""
            return FlextInfraCodegenLazyInit(repository_root=workspace_root)

        @staticmethod
        def extract_lazy_init_exports(source: str) -> tuple[bool, t.StrSequence]:
            """Read the published lazy export contract from generated source."""
            assignments = dict(u.Infra.get_module_level_assignments(source))
            all_value = assignments.get(c.Infra.DUNDER_ALL)
            if all_value is None:
                return (False, ())
            literal_exports = tuple(c.Tests.LAZY_INIT_EXPORT_NAME_RE.findall(all_value))
            if literal_exports:
                return (True, literal_exports)
            public_value = assignments.get("_PUBLIC_EXPORTS", "")
            return (
                "_PUBLIC_EXPORTS" in all_value,
                tuple(c.Tests.LAZY_INIT_EXPORT_NAME_RE.findall(public_value)),
            )

        @staticmethod
        def consolidate_codegen(
            *, repository_root: Path, project: str | None = None, dry_run: bool = True
        ) -> p.Result[str]:
            """Provide the typed test helper `consolidate_codegen`."""
            service: FlextInfraCodegenConsolidator = FlextInfraCodegenConsolidator(
                repository_root=repository_root, dry_run=dry_run, project_name=project
            )
            result: p.Result[str] = service.execute()
            return result

        @staticmethod
        def detect_command(
            workspace_root: Path, **overrides: t.Infra.InfraValue
        ) -> m.Infra.DetectCommand:
            """Create a validated dependency-detection command."""
            validated: m.Infra.DetectCommand = m.Infra.DetectCommand.model_validate({
                "workspace": str(workspace_root),
                **overrides,
            })
            return validated

        @staticmethod
        def create_detector_deps_stub(
            project_paths: t.SequenceOf[Path],
        ) -> TestsFlextInfraUtilities.Tests.DetectorDepsStub:
            """Provide the typed test helper `create_detector_deps_stub`."""
            return TestsFlextInfraUtilities.Tests.DetectorDepsStub(project_paths)

        @staticmethod
        def setup_detector_runtime(
            tmp_path: Path,
            deps: p.Infra.DepsService,
            *,
            deptry_exists: bool = True,
            runner: p.Infra.RunnerService | None = None,
        ) -> FlextInfraRuntimeDevDependencyDetector:
            """Provide the typed test helper `setup_detector_runtime`."""
            deptry_path = tmp_path / c.Infra.VENV_BIN_REL / c.Infra.DEPTRY
            deptry_path.parent.mkdir(parents=True, exist_ok=True)
            if deptry_exists:
                deptry_path.write_text("", encoding="utf-8")
            if runner is not None:
                return FlextInfraRuntimeDevDependencyDetector(
                    repository_root=tmp_path, deps=deps, runner=runner
                )
            return FlextInfraRuntimeDevDependencyDetector(
                repository_root=tmp_path, deps=deps
            )

        @staticmethod
        def create_gate_execution(
            gate: str = "lint",
            project: str = "p",
            *,
            passed: bool = True,
            issues: t.SequenceOf[m.Infra.Issue] | None = None,
        ) -> m.Infra.GateExecution:
            """Create a typed quality-gate execution fixture."""
            return m.Infra.GateExecution(
                result=m.Infra.GateResult(
                    gate=gate, project=project, passed=passed, errors=(), duration=0.0
                ),
                issues=tuple(issues or ()),
                raw_output="",
            )

        @staticmethod
        def make_issue(
            *,
            file: str = "a.py",
            line: int = 1,
            column: int = 1,
            code: str = "E1",
            message: str = "Error",
        ) -> m.Infra.Issue:
            """Create a typed quality issue fixture."""
            return m.Infra.Issue(
                file=file,
                line=line,
                column=column,
                code=code,
                message=message,
                severity="error",
            )

        @staticmethod
        def make_project(
            name: str = "p",
            gates: MutableMapping[str, m.Infra.GateExecution] | None = None,
        ) -> m.Infra.ProjectResult:
            """Create a typed project-result fixture."""
            resolved_gates: MutableMapping[str, m.Infra.GateExecution] = (
                gates
                if gates is not None
                else {"lint": TestsFlextInfraUtilities.Tests.create_gate_execution()}
            )
            result: m.Infra.ProjectResult = m.Infra.ProjectResult.model_validate({
                "project": name,
                "gates": resolved_gates,
            })
            return result

        @staticmethod
        def repository_profile(root: Path) -> c.Infra.MakeProfile:
            """Return the Make profile derived from the repository itself."""
            from flext_infra.workspace.detector import FlextInfraWorkspaceDetector

            mode = tm.ok(FlextInfraWorkspaceDetector().detect(root))
            by_mode: dict[c.Infra.MakeProfile, c.Infra.MakeProfile] = {
                c.Infra.MakeProfile.WORKSPACE: c.Infra.MakeProfile.WORKSPACE,
                c.Infra.MakeProfile.STANDALONE: c.Infra.MakeProfile.STANDALONE,
            }
            return by_mode[mode]

        @staticmethod
        def ignore_patterns_for(root: Path) -> tuple[str, ...]:
            """Return the ignore patterns that apply to *root*'s declared profile.

            Returns:
                Every SSOT pattern whose section targets that profile.

            """
            profile = TestsFlextInfraUtilities.Tests.repository_profile(root)
            gitignore_sections: tuple[m.Infra.ScaffoldGitignoreSectionSpec, ...] = (
                config.Infra.codegen.gitignore_sections
            )
            return tuple(
                pattern
                for section in gitignore_sections
                if not section.profiles or profile in section.profiles
                for pattern in section.patterns
            )

        @staticmethod
        def is_tracked_under(rendered: str, relative_path: str) -> bool:
            """Return whether git tracks *relative_path* under *rendered*.

            Ignore semantics are subtle (ordering, negation, directory
            prefixes), so the question is delegated to git itself against a
            throwaway repository, never reimplemented here.

            Returns:
                ``True`` when git would track the path.

            """
            import tempfile

            with tempfile.TemporaryDirectory() as raw_root:
                probe_root = Path(raw_root)
                tm.ok(u.Cli.run_checked(["git", "init", "-q", str(probe_root)]))
                (probe_root / ".gitignore").write_text(rendered, encoding="utf-8")
                target = probe_root / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("", encoding="utf-8")
                # `git check-ignore` exits 0 when the path IS ignored, so a
                # failed run is the success case for a tracked artifact.
                probe: p.Cli.CommandOutput = tm.ok(
                    u.Cli.run_raw(
                        ["git", "check-ignore", "-q", relative_path], cwd=probe_root
                    )
                )
            return probe.outcome.raw_return_code != int(c.Infra.ScriptExitCode.PASS)

        @staticmethod
        def create_checker_project(
            tmp_path: Path, *, project_name: str = "p1", with_src: bool = False
        ) -> tuple[FlextInfraWorkspaceChecker, Path]:
            """Provide the typed test helper `create_checker_project`."""
            checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
            project_dir = TestsFlextInfraUtilities.Tests.mk_project(
                tmp_path, project_name
            )
            if with_src:
                (project_dir / "src").mkdir(parents=True, exist_ok=True)
            return checker, project_dir

        @staticmethod
        def create_gate_context(
            workspace_root: Path, *, reports_dir: Path | None = None
        ) -> m.Infra.GateContext:
            """Provide the typed test helper `create_gate_context`."""
            return m.Infra.GateContext(
                workspace=workspace_root, reports_dir=reports_dir or workspace_root
            )

        @staticmethod
        def run_gate_check(
            gate_class: type[FlextInfraGate],
            workspace_root: Path,
            project_dir: Path,
            *,
            ctx: m.Infra.GateContext | None = None,
            reports_dir: Path | None = None,
            runner: p.Cli.CommandRunner | None = None,
        ) -> m.Infra.GateExecution:
            """Provide the typed test helper `run_gate_check`."""
            gate = gate_class(workspace_root, runner=runner)
            return gate.check(
                project_dir,
                ctx
                or TestsFlextInfraUtilities.Tests.create_gate_context(
                    workspace_root, reports_dir=reports_dir
                ),
            )

        class DetectorReportStub:
            """Minimal report stub for dependency detector tests."""

            def __init__(self, raw_count: int) -> None:
                """Store the raw dependency count."""
                self._raw_count = raw_count

            def model_dump(self) -> t.JsonMapping:
                """Return the dependency-report payload."""
                return {"deptry": {"raw_count": self._raw_count}}

        class DetectorDepsStub(p.Infra.DepsService, p.Infra.TypingsDepsService):
            """Typed dependency service stub for detector tests."""

            def __init__(self, project_paths: t.SequenceOf[Path]) -> None:
                """Store project paths and injectable failure states."""
                self.project_paths = project_paths
                self.discovery_failure: str | None = None
                self.deptry_failure: str | None = None
                self.typings_failure: str | None = None

            @override
            def discover_project_paths(
                self,
                repository_root: Path,
                projects_filter: t.StrSequence | None = None,
            ) -> p.Result[Sequence[Path]]:
                del repository_root, projects_filter
                if self.discovery_failure is not None:
                    return r[Sequence[Path]].fail(self.discovery_failure)
                return r[Sequence[Path]].ok(self.project_paths)

            @override
            def run_deptry(
                self,
                project_path: Path,
                venv_bin: Path,
                *,
                config_path: Path | None = None,
                json_output_path: Path | None = None,
                extend_exclude: t.StrSequence | None = None,
            ) -> p.Result[t.Pair[Sequence[t.JsonMapping], int]]:
                del project_path
                del venv_bin
                del config_path
                del json_output_path
                del extend_exclude
                if self.deptry_failure is not None:
                    return r[t.Pair[Sequence[t.JsonMapping], int]].fail(
                        self.deptry_failure
                    )
                return r[t.Pair[Sequence[t.JsonMapping], int]].ok(((), 0))

            @override
            def build_project_report(
                self, project_name: str, deptry_issues: t.SequenceOf[t.JsonMapping]
            ) -> m.Infra.ProjectDependencyReport:
                del deptry_issues
                return m.Infra.ProjectDependencyReport(
                    project=project_name or "fixture",
                    deptry=m.Infra.DeptryReport(raw_count=0),
                )

            @override
            def get_required_typings(
                self,
                project_path: Path,
                limits_path: Path | None = None,
                *,
                include_mypy: bool = True,
            ) -> p.Result[m.Infra.TypingsReport]:
                del project_path, limits_path
                del include_mypy
                if self.typings_failure is not None:
                    return r[m.Infra.TypingsReport].fail(self.typings_failure)
                return r[m.Infra.TypingsReport].ok(m.Infra.TypingsReport(to_add=[]))

            @override
            def load_dependency_limits(
                self, limits_path: Path | None = None
            ) -> t.StrMapping:
                del limits_path
                limits: dict[str, str] = {}
                return limits

        def enforcement_rule(rule_id: str) -> m.EnforcementRuleSpec:
            """Resolve one enabled rule from the canonical enforcement catalog."""
            catalog = u.build_canonical_catalog()
            rule: m.EnforcementRuleSpec = next(
                rule for rule in catalog.enabled_rules() if rule.id == rule_id
            )
            return rule

u = TestsFlextInfraUtilities

__all__: list[str] = ["TestsFlextInfraUtilities", "u"]
