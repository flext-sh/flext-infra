"""Candidate bootstrap campaigns through the public Infra facade.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from flext_infra import config, infra
from flext_infra.codegen import (
    FlextInfraCodegenConform,
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenTransaction,
)
from flext_infra.workspace import FlextInfraWorkspaceDetector
from tests import c, m, p, t, tm, u
from tests.unit.codegen import TestsFlextInfraConformSupport


def _write_candidate_targets(
    root: Path,
    targets: t.SequenceOf[m.Infra.CandidateBootstrapTargetSpec],
) -> Path:
    """Declare recovery targets through the repository's current config owner.

    Args:
        root: Workspace root whose conformed config file is rewritten.
        targets: Candidate bootstrap target specs to declare.

    Returns:
        Path of the rewritten codegen config file declaring the targets.

    """
    inputs = tm.ok(u.Infra.load_codegen_inputs(root))
    declaration = (inputs.spec.repository or m.Infra.RepositoryDeltaSpec()).model_copy(
        update={"candidate_bootstrap_targets": tuple(targets)},
    )
    path = root / c.CONFIG_DIR_NAME / c.Infra.CODEGEN_CONFIG_FILENAME
    tm.ok(u.Cli.ensure_dir(path.parent))
    tm.ok(
        u.Cli.yaml_dump(
            path,
            {
                "Infra": {
                    "codegen": {
                        "repository": declaration.model_dump(
                            mode="json",
                            exclude_none=True,
                            exclude_defaults=True,
                        ),
                    },
                },
            },
        ),
    )
    return path


def _declared_candidate_campaign(
    tmp_path: Path,
    surface: c.Infra.CodegenConformSurface,
) -> tuple[Path, Path]:
    """Render a source workspace declaring one candidate recovery target.

    Returns:
        The source workspace and the candidate it declares.

    """
    source, _ = u.Tests.render_make_environment(
        tmp_path / "source",
        c.Infra.MakeProfile.STANDALONE,
    )
    candidate, _ = u.Tests.render_make_environment(
        tmp_path / "candidate",
        c.Infra.MakeProfile.STANDALONE,
    )
    _write_candidate_targets(
        source,
        (
            m.Infra.CandidateBootstrapTargetSpec(
                path=Path(os.path.relpath(candidate, source)),
                what=surface,
            ),
        ),
    )
    return source, candidate


class TestsFlextInfraCodegenCandidateBootstrap:
    """A declared campaign publishes all recovery projections or none."""

    @staticmethod
    def _attach_independent_member(root: Path) -> Path:
        """Attach one governed member that shares no state with the failed one.

        Returns:
            The independent member root.

        """
        independent = root / "independent-member"
        beads = u.Tests.beads_project(root.name)
        u.Tests.WorktreeFixture.initialize_governed_project(
            independent,
            independent.name,
            beads=u.Tests.BeadsIdentity(
                workspace=beads.workspace,
                database=beads.database,
                issue_prefix=beads.issue_prefix,
            ),
        )
        u.Tests.WorktreeFixture.attach_submodule(
            root,
            independent,
            distribution=independent.name,
            relative_path=independent.relative_to(root).as_posix(),
        )
        return independent

    @staticmethod
    def _break_repository(
        failed: Path,
        resolution_pyprojects: t.SequenceOf[Path],
        foreign: Path,
        failure: str,
    ) -> None:
        """Corrupt exactly the input one parametrized failure names."""
        if failure == "root-source":
            projection = failed / c.PYPROJECT_FILENAME
            projection.write_text(
                projection.read_text(encoding=c.DEFAULT_ENCODING) + "\n[project]\n",
                encoding=c.DEFAULT_ENCODING,
            )
        elif failure == "member-package":
            package = failed / "src" / u.Infra.project_package_name(failed)
            (package / c.Infra.INIT_PY).unlink()
        else:
            view = failed / resolution_pyprojects[0]
            foreign.mkdir()
            view.parent.parent.mkdir(parents=True, exist_ok=True)
            view.parent.symlink_to(foreign, target_is_directory=True)

    @staticmethod
    def _tree_without_plan_report(root: Path) -> t.VariadicTuple[t.Pair[str, bytes]]:
        """Return the project tree minus the planning report every plan rewrites.

        Returns:
            The tree entries outside the planning report path.

        """
        return tuple(
            item
            for item in TestsFlextInfraConformSupport.project_tree(root)
            if item[0] != c.Infra.CODEGEN_PLAN_REPORT_RELATIVE_PATH.as_posix()
        )

    @staticmethod
    def _assert_independent_views_planned(
        independent: Path,
        plan: m.Infra.CodegenPlan,
        report: m.Infra.CodegenPlanningReport,
    ) -> None:
        """Require every independent resolution view in the plan and its report."""
        planned_paths = {file.path for file in plan.files}
        reported_paths = {file.path for item in report.outcomes for file in item.files}
        for relative in tm.ok(
            u.Infra.load_codegen_inputs(independent)
        ).spec.uv_resolution_pyprojects:
            tm.ok(independent / relative in planned_paths)
            tm.ok(independent / relative in reported_paths)

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize(
        "failure",
        ["root-source", "member-package", "root-view", "member-view"],
    )
    def test_repository_failure_preserves_independent_native_view_plans(
        tmp_path: Path,
        failure: str,
    ) -> None:
        """Public plans account for each repository without reading failed metadata."""
        root = tmp_path / "workspace"
        member = u.Tests.WorktreeFixture.governed_workspace_with_member(
            root,
            workspace=f"{c.Infra.PKG_PREFIX_HYPHEN}plan-workspace",
            member=f"{c.Infra.PKG_PREFIX_HYPHEN}plan-member",
        )
        independent = (
            TestsFlextInfraCodegenCandidateBootstrap._attach_independent_member(
                root,
            )
        )
        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))
        workspace = workspace.model_copy(
            update={
                "project": u.Tests.project_spec(workspace.repository.distribution),
                "integration": u.Tests.integration(),
            },
        )
        request = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.PYPROJECT,
            scope=c.Infra.CodegenConformScope.ALL,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        tm.that(
            tm.ok(
                FlextInfraCodegenConform(
                    repository_root=root,
                    state=m.Infra.CodegenConformState(
                        repository_root=root,
                        initial_workspace=workspace,
                    ),
                ).plan(request),
            ).issues,
            empty=True,
        )
        failed = root if failure.startswith("root-") else member
        inputs = tm.ok(u.Infra.load_codegen_inputs(failed))
        TestsFlextInfraCodegenCandidateBootstrap._break_repository(
            failed,
            inputs.spec.uv_resolution_pyprojects,
            tmp_path / "foreign",
            failure,
        )
        before = TestsFlextInfraCodegenCandidateBootstrap._tree_without_plan_report(
            root,
        )

        plan = tm.ok(
            FlextInfraCodegenConform(
                repository_root=root,
                state=m.Infra.CodegenConformState(
                    repository_root=root,
                    initial_workspace=workspace,
                ),
            ).plan(request),
        )

        tm.ok(bool(plan.issues))
        report = m.Infra.CodegenPlanningReport.model_validate_json(
            (root / c.Infra.CODEGEN_PLAN_REPORT_RELATIVE_PATH).read_bytes(),
        )
        failed_outcome = next(item for item in report.outcomes if item.root == failed)
        tm.ok(bool(failed_outcome.error or failed_outcome.issues))
        if failure == "root-source":
            tm.that(failed_outcome.error, has="live pyproject is not valid TOML")
        elif failure == "root-view":
            tm.that(
                failed_outcome.error,
                has="native resolution view escapes its repository",
            )
        tm.that(failed_outcome.files, empty=True)
        TestsFlextInfraCodegenCandidateBootstrap._assert_independent_views_planned(
            independent,
            plan,
            report,
        )
        planned_paths = {file.path for file in plan.files}
        for relative in inputs.spec.uv_resolution_pyprojects:
            tm.fail(failed / relative in planned_paths)
        if failure == "member-package":
            tm.that(
                next(item for item in report.outcomes if item.root == root).error,
                has="no successful selected plan",
            )
            tm.that(str(tm.not_none(plan.exception)), has="cannot resolve package name")
        tm.that(
            TestsFlextInfraCodegenCandidateBootstrap._tree_without_plan_report(root),
            eq=before,
        )

    @staticmethod
    @pytest.mark.slow
    def test_public_bootstrap_rewrites_own_pyproject_and_repeats(
        tmp_path: Path,
    ) -> None:
        """A self target retains declarations while its own projection advances."""
        root, _ = u.Tests.render_make_environment(
            tmp_path / "self",
            c.Infra.MakeProfile.STANDALONE,
        )
        declaration = _write_candidate_targets(
            root,
            (
                m.Infra.CandidateBootstrapTargetSpec(
                    path=Path(),
                    what=c.Infra.CodegenConformSurface.PYPROJECT,
                ),
            ),
        )
        declared = tm.ok(
            u.Cli.atomic_read_binary_file_state(declaration, required=True),
        )
        pyproject = root / c.PYPROJECT_FILENAME
        regeneration_source = tm.ok(
            u.Infra.pyproject_regeneration_source(
                pyproject.read_text(encoding=c.DEFAULT_ENCODING),
            ),
        )
        tm.ok(u.Cli.atomic_write_text_file(pyproject, regeneration_source))
        before = tm.ok(
            u.Cli.atomic_read_binary_file_state(pyproject, required=True),
        )
        command = m.Infra.CandidateBootstrapCommand(repository_root=root)
        plan = tm.ok(
            FlextInfraCodegenConform(repository_root=root).plan(
                u.Tests.conform_request(
                    root,
                    what=c.Infra.CodegenConformSurface.PYPROJECT,
                    scope=c.Infra.CodegenConformScope.SELF,
                    mode=c.Infra.CodegenConformMode.CHECK,
                ),
            ),
        )
        tm.that(plan.issues, empty=True)
        resolution = tm.ok(
            u.Infra.load_codegen_inputs(root)
        ).spec.uv_resolution_pyprojects
        views = tuple(
            file for file in plan.files if file.path.relative_to(root) in resolution
        )
        tm.that(len(views), eq=len(resolution))

        tm.ok(infra.bootstrap_candidate(command))
        projected = tm.ok(
            u.Cli.atomic_read_binary_file_state(
                pyproject,
                required=True,
            ),
        )
        tm.that(projected.content, ne=before.content)
        tm.that(
            u.Tests.toml_strings_at(
                tm.not_none(projected.content).decode(c.DEFAULT_ENCODING),
                "tool",
                "ruff",
                "lint",
                "extend-select",
            ),
            eq=tuple(
                u.Infra.native_tool_setting(
                    config.Infra.tooling, "ruff.lint", "extend-select", list[str]
                )
            ),
        )
        tm.that(
            u.Tests.toml_table_at(
                tm.not_none(projected.content).decode(c.DEFAULT_ENCODING),
                "tool",
                "ruff",
                "lint",
                "flake8-type-checking",
            ),
            has="runtime-evaluated-base-classes",
        )
        for view in views:
            tm.that(view.path.read_bytes(), eq=view.desired_content)
        tm.ok(infra.bootstrap_candidate(command))
        for view in views:
            tm.that(view.path.read_bytes(), eq=view.desired_content)

        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(declaration, required=True)),
            eq=declared,
        )
        tm.that(
            tm.ok(
                u.Cli.atomic_read_binary_file_state(
                    projected.path,
                    required=True,
                ),
            ),
            eq=projected,
        )

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("foreign_change", [False, True])
    def test_producer_continuation_requires_live_native_publication(
        tmp_path: Path,
        *,
        foreign_change: bool,
    ) -> None:
        """A real journal receipt permits continuation only while outputs are live."""
        root, _ = u.Tests.render_make_environment(
            tmp_path / "continuation",
            c.Infra.MakeProfile.STANDALONE,
        )
        source = root / "publication-input.txt"
        source.write_text("captured producer input\n", encoding=c.DEFAULT_ENCODING)
        state = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
        destination = root / "publication-output.txt"
        before = tm.ok(u.Infra.codegen_target_snapshot(destination))
        planner = FlextInfraCodegenConform(
            repository_root=root,
            state=m.Infra.CodegenConformState(repository_root=root, ports=None),
        )
        transaction = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        )
        analysis = m.Infra.CodegenPhaseAnalysis(
            phase=c.Infra.CodegenStagedFilePhase.CANDIDATE_BOOTSTRAP,
            files=(
                m.Infra.CodegenFilePlan(
                    project=root,
                    path=destination,
                    before=before,
                    desired_content=tm.not_none(state.content),
                    desired_mode=state.mode,
                    source_states=(state,),
                ),
            ),
            inputs=(state,),
        )
        receipts: list[m.Infra.CodegenPhaseOutcome] = []
        roots = {"@continuation": root}

        def publish(scope_root: Path) -> p.Result[t.VariadicTuple[Path]]:
            return transaction.publish_file_phase_locked(
                scope_root,
                roots,
                analysis,
                m.Infra.CodegenPhasePublicationPolicy(directories=()),
                publication_receipts=receipts,
            )

        tm.ok(transaction.run_files_locked(roots, publish))
        tm.ok(bool(receipts))
        if foreign_change:
            destination.write_text(
                "foreign publication mutation\n",
                encoding=c.DEFAULT_ENCODING,
            )

        continued = planner.continue_after_publication(tuple(receipts))

        tm.that(continued.success, eq=not foreign_change)
        if foreign_change:
            tm.that(continued.error, has=str(destination))
            tm.that(
                destination.read_bytes(),
                eq=b"foreign publication mutation\n",
            )
        else:
            tm.that(destination.read_bytes(), eq=state.content)

    @staticmethod
    @pytest.mark.slow
    def test_absent_resolution_parent_chains_publish_atomically_and_converge(
        tmp_path: Path,
    ) -> None:
        """The existing publication journal owns new native-view parent chains."""
        source, candidate = _declared_candidate_campaign(
            tmp_path,
            c.Infra.CodegenConformSurface.PYPROJECT,
        )
        inputs = tm.ok(u.Infra.load_codegen_inputs(candidate))
        views = tuple(
            candidate / relative for relative in inputs.spec.uv_resolution_pyprojects
        )
        tm.ok(bool(views))
        for view in views:
            tm.fail(view.parent.exists())
        before = tm.ok(
            u.Cli.atomic_read_binary_file_state(
                candidate / c.PYPROJECT_FILENAME,
                required=True,
            ),
        )
        check = infra.bootstrap_candidate(
            m.Infra.CandidateBootstrapCommand(
                repository_root=source,
                check_only=True,
            ),
        )
        tm.ok(check.failure)
        for view in views:
            tm.fail(view.parent.exists())
        tm.that(
            tm.ok(
                u.Cli.atomic_read_binary_file_state(
                    candidate / c.PYPROJECT_FILENAME,
                    required=True,
                ),
            ),
            eq=before,
        )
        command = m.Infra.CandidateBootstrapCommand(repository_root=source)
        tm.ok(infra.bootstrap_candidate(command))
        committed = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(view, required=True))
            for view in views
        )
        for view, state in zip(views, committed, strict=True):
            tm.ok(view.parent.is_dir())
            tm.fail(view.parent.is_symlink())
            tm.that(
                u.Cli.toml_mapping_from_text((state.content or b"").decode("utf-8"))
                is not None,
                eq=True,
            )
        tm.ok(infra.bootstrap_candidate(command))
        tm.that(
            tuple(
                tm.ok(u.Cli.atomic_read_binary_file_state(view, required=True))
                for view in views
            ),
            eq=committed,
        )

    @staticmethod
    @pytest.mark.slow
    def test_resolution_parent_symlink_refuses_foreign_publication(
        tmp_path: Path,
    ) -> None:
        """Missing-parent support does not authorize a foreign symlink target."""
        source, candidate = _declared_candidate_campaign(
            tmp_path,
            c.Infra.CodegenConformSurface.PYPROJECT,
        )
        inputs = tm.ok(u.Infra.load_codegen_inputs(candidate))
        view = candidate / inputs.spec.uv_resolution_pyprojects[0]
        foreign = tmp_path / "foreign"
        foreign.mkdir()
        sentinel = foreign / view.name
        sentinel.write_text("foreign content\n", encoding="utf-8")
        view.parent.parent.mkdir(parents=True, exist_ok=True)
        view.parent.symlink_to(foreign, target_is_directory=True)
        original = tm.ok(
            u.Cli.atomic_read_binary_file_state(
                candidate / c.PYPROJECT_FILENAME,
                required=True,
            ),
        )
        result = infra.bootstrap_candidate(
            m.Infra.CandidateBootstrapCommand(repository_root=source),
        )
        tm.ok(result.failure)
        tm.that(sentinel.read_text(encoding="utf-8"), eq="foreign content\n")
        tm.that(
            tm.ok(
                u.Cli.atomic_read_binary_file_state(
                    candidate / c.PYPROJECT_FILENAME,
                    required=True,
                ),
            ),
            eq=original,
        )

    @staticmethod
    def _write_runtime_probe(candidate: Path) -> t.StrSequence:
        """Declare importable descendants of the configured runtime roots.

        Returns:
            Configured roots exercised by the probe package.

        """
        policy = config.Infra.tooling.tools.ruff.lint.flake8_type_checking
        roots = policy.runtime_evaluated_roots
        source = "\n".join(
            f"import {module} as provider{index}\n\n"
            f"class BootstrapProbe{index}(provider{index}.{base}):\n    pass\n"
            f"class BootstrapConsumer{index}(BootstrapProbe{index}):\n    pass\n"
            for index, (module, _, base) in enumerate(
                root.rpartition(".") for root in roots
            )
        )
        if not roots:
            source = "class BootstrapProbe:\n    pass\n"
        probe = candidate / "src" / "bootstrap_probe" / "models.py"
        probe.parent.mkdir(parents=True, exist_ok=True)
        tm.ok(u.Cli.atomic_write_text_file(probe, source))
        return roots

    @staticmethod
    def test_current_repository_is_a_valid_relative_bootstrap_target() -> None:
        """Self recovery remains relative while invalid path inputs fail."""
        target = m.Infra.CandidateBootstrapTargetSpec.model_validate({
            "path": ".",
            "what": c.Infra.CodegenConformSurface.MAKEFILE,
        })
        tm.that(target.path, eq=Path())
        for invalid in ("", " ", Path.cwd()):
            with pytest.raises(m.ValidationError):
                m.Infra.CandidateBootstrapTargetSpec.model_validate({
                    "path": invalid,
                    "what": c.Infra.CodegenConformSurface.MAKEFILE,
                })

    @staticmethod
    def _campaign(tmp_path: Path) -> tuple[Path, Path, Path]:
        source, _ = u.Tests.render_make_environment(
            tmp_path / "source",
            c.Infra.MakeProfile.STANDALONE,
        )
        first, _ = u.Tests.render_make_environment(
            tmp_path / "first",
            c.Infra.MakeProfile.STANDALONE,
        )
        second, _ = u.Tests.render_make_environment(
            tmp_path / "second",
            c.Infra.MakeProfile.STANDALONE,
        )
        for root in (first, second):
            _write_candidate_targets(root, ())
        _write_candidate_targets(
            source,
            tuple(
                m.Infra.CandidateBootstrapTargetSpec(
                    path=Path(os.path.relpath(root, source)),
                    what=c.Infra.CodegenConformSurface.MAKEFILE,
                )
                for root in (first, second)
            ),
        )
        return source, first, second

    @staticmethod
    def test_empty_campaign_fails_loud(tmp_path: Path) -> None:
        """An empty typed list cannot produce a green no-op bootstrap.

        The refusal happens before any target is planned, so a governed
        checkout without a rendered Make environment is the whole fixture.
        """
        project_root = tmp_path / "fixture-project"
        u.Tests.WorktreeFixture.initialize_governed_project(
            project_root,
            "fixture-project",
            beads=u.Tests.BeadsIdentity(
                workspace="fixture-project",
                database="fixture_project",
                issue_prefix="fixture",
            ),
        )
        _write_candidate_targets(project_root, ())

        result = infra.bootstrap_candidate(
            m.Infra.CandidateBootstrapCommand(repository_root=project_root),
        )

        tm.ok(result.failure)
        tm.that(result.error, has="candidate bootstrap targets are not declared")

    @staticmethod
    @pytest.mark.slow
    def test_duplicate_target_worktree_is_rejected_without_publication(
        tmp_path: Path,
    ) -> None:
        """One worktree cannot receive two competing recovery surfaces."""
        source, candidate = _declared_candidate_campaign(
            tmp_path,
            c.Infra.CodegenConformSurface.PYPROJECT,
        )
        relative = Path(os.path.relpath(candidate, source))
        _write_candidate_targets(
            source,
            tuple(
                m.Infra.CandidateBootstrapTargetSpec(path=relative, what=surface)
                for surface in (
                    c.Infra.CodegenConformSurface.PYPROJECT,
                    c.Infra.CodegenConformSurface.MAKEFILE,
                )
            ),
        )
        before = TestsFlextInfraConformSupport.project_tree(candidate)

        result = infra.bootstrap_candidate(
            m.Infra.CandidateBootstrapCommand(repository_root=source),
        )

        tm.ok(result.failure)
        tm.that(result.error, has="duplicate worktrees")
        tm.that(TestsFlextInfraConformSupport.project_tree(candidate), eq=before)

    @pytest.mark.slow
    def test_initializer_surface_recovers_without_touching_module_source(
        self,
        tmp_path: Path,
    ) -> None:
        """Dynamic initializer destinations retain source and converge."""
        source, first, _ = self._campaign(tmp_path)
        package_name = u.Infra.project_package_name(first)
        tm.ok(bool(package_name))
        package = first / "src" / package_name
        tm.ok(package.is_dir())
        module = package / "domain.py"
        exported = "BootstrapCase"
        module.write_text(
            f"class {exported}:\n    pass\n__all__ = ['{exported}']\n",
            encoding="utf-8",
        )
        initializer = package / c.Infra.INIT_PY
        initializer.write_text(
            f"{c.Infra.AUTOGEN_HEADER}\n# Stale generated initializer\n",
            encoding="utf-8",
        )
        foreign = package / "authored"
        foreign.mkdir()
        authored = foreign / c.Infra.INIT_PY
        authored.write_text("OWNED = True\n", encoding="utf-8")
        authored_before = tm.ok(
            u.Cli.atomic_read_binary_file_state(authored, required=True),
        )
        _write_candidate_targets(
            source,
            (
                m.Infra.CandidateBootstrapTargetSpec(
                    path=Path(os.path.relpath(first, source)),
                    what=c.Infra.CodegenConformSurface.LAZY_INIT,
                ),
            ),
        )
        before = tm.ok(u.Cli.atomic_read_binary_file_state(module, required=True))
        command = m.Infra.CandidateBootstrapCommand(repository_root=source)

        tm.ok(infra.bootstrap_candidate(command))
        generated = tm.ok(
            u.Cli.atomic_read_binary_file_state(initializer, required=True),
        )
        tm.that(
            generated.content,
            ne=f"{c.Infra.AUTOGEN_HEADER}\n# Stale generated initializer\n".encode(
                c.DEFAULT_ENCODING
            ),
        )
        observed = tm.ok(
            u.Cli.capture(
                [
                    sys.executable,
                    "-c",
                    (
                        "import importlib, sys; "
                        "print(getattr(importlib.import_module(sys.argv[1]), "
                        "sys.argv[2]).__name__)"
                    ),
                    package_name,
                    exported,
                ],
                cwd=first,
                options=m.Cli.ProcessOptions(
                    env={"PYTHONPATH": str(first / "src")},
                ),
            ),
        )
        tm.that(observed.strip(), eq=exported)
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(authored, required=True)),
            eq=authored_before,
        )
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(module, required=True)),
            eq=before,
        )
        tm.ok(infra.bootstrap_candidate(command))
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(initializer, required=True)),
            eq=generated,
        )

    @pytest.mark.slow
    def test_complete_generation_is_refused_before_publication(
        self,
        tmp_path: Path,
    ) -> None:
        """Bootstrap cannot broaden a recovery target into full generation."""
        source, first, _ = self._campaign(tmp_path)
        declaration = source / c.CONFIG_DIR_NAME / c.Infra.CODEGEN_CONFIG_FILENAME
        declaration.write_text(
            declaration.read_text(encoding="utf-8").replace(
                "what: makefile",
                "what: all",
            ),
            encoding="utf-8",
        )
        makefile = first / c.Infra.MAKEFILE_FILENAME
        before = tm.ok(u.Cli.atomic_read_binary_file_state(makefile, required=True))

        result = infra.bootstrap_candidate(
            m.Infra.CandidateBootstrapCommand(repository_root=source),
        )

        tm.ok(result.failure)
        tm.that(result.error, has="requires one declared surface")
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(makefile, required=True)),
            eq=before,
        )

    # Real conform transactions over a fixture repository (several full plans
    # per case): integration-scale, so it runs in the slow phase under its
    # per-item bound (rules/workflow/gate-budget.md), never a raised limit.
    @pytest.mark.slow
    def test_invalid_second_target_preserves_first_and_allows_retry(
        self,
        tmp_path: Path,
    ) -> None:
        """Planning must finish for every target before any bytes are published."""
        source, first, second = self._campaign(tmp_path)
        first_makefile = first / c.Infra.MAKEFILE_FILENAME
        first_makefile.write_text("stale candidate Makefile\n", encoding="utf-8")
        before = tm.ok(
            u.Cli.atomic_read_binary_file_state(first_makefile, required=True),
        )
        second_declaration = (
            second / c.CONFIG_DIR_NAME / c.Infra.CODEGEN_CONFIG_FILENAME
        )
        original = second_declaration.read_text(encoding="utf-8")
        second_declaration.write_text("invalid: [\n", encoding="utf-8")

        with pytest.raises(u.Yaml.YAMLError):
            infra.bootstrap_candidate(
                m.Infra.CandidateBootstrapCommand(repository_root=source),
            )
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(first_makefile, required=True)),
            eq=before,
        )
        second_declaration.write_text(original, encoding="utf-8")
        tm.ok(
            infra.bootstrap_candidate(
                m.Infra.CandidateBootstrapCommand(repository_root=source),
            ),
        )

    @pytest.mark.slow
    def test_two_targets_reach_one_repeatable_fixed_point(self, tmp_path: Path) -> None:
        """A successful campaign publishes both and repeats without drift."""
        source, first, second = self._campaign(tmp_path)
        for root in (first, second):
            (root / c.Infra.MAKEFILE_FILENAME).write_text(
                "stale candidate Makefile\n",
                encoding="utf-8",
            )
        command = m.Infra.CandidateBootstrapCommand(repository_root=source)

        tm.ok(infra.bootstrap_candidate(command))
        committed = tuple(
            tm.ok(
                u.Cli.atomic_read_binary_file_state(
                    root / c.Infra.MAKEFILE_FILENAME,
                    required=True,
                ),
            )
            for root in (first, second)
        )
        tm.ok(infra.bootstrap_candidate(command))
        repeated = tuple(
            tm.ok(
                u.Cli.atomic_read_binary_file_state(
                    root / c.Infra.MAKEFILE_FILENAME,
                    required=True,
                ),
            )
            for root in (first, second)
        )
        tm.that(repeated, eq=committed)
        tm.that(
            all(state.content != b"stale candidate Makefile\n" for state in committed),
            eq=True,
        )

    @pytest.mark.slow
    def test_makefile_bootstrap_does_not_parse_corrupt_tooling(
        self,
        tmp_path: Path,
    ) -> None:
        """Declared topology repairs Make even when a tooling projection is corrupt."""
        source, first, _ = self._campaign(tmp_path)
        pyproject = first / c.PYPROJECT_FILENAME
        content = pyproject.read_text(encoding="utf-8")
        pyproject.write_text(
            content + '\n[tool.mypy]\nplugins = ["pydantic.mypy"]\n',
            encoding="utf-8",
        )
        before = tm.ok(u.Cli.atomic_read_binary_file_state(pyproject, required=True))
        makefile = first / c.Infra.MAKEFILE_FILENAME
        makefile.write_text("ifdef broken\n", encoding="utf-8")

        tm.ok(
            infra.bootstrap_candidate(
                m.Infra.CandidateBootstrapCommand(repository_root=source),
            ),
        )

        tm.that(makefile.read_text(encoding="utf-8"), lacks="ifdef broken")
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(pyproject, required=True)),
            eq=before,
        )

    @pytest.mark.slow
    def test_check_only_reports_drift_without_publication(self, tmp_path: Path) -> None:
        """A check does not enter the recoverable writer or change a target."""
        source, first, _ = self._campaign(tmp_path)
        first_makefile = first / c.Infra.MAKEFILE_FILENAME
        first_makefile.write_text("stale candidate Makefile\n", encoding="utf-8")
        before = tm.ok(
            u.Cli.atomic_read_binary_file_state(first_makefile, required=True),
        )

        result = infra.bootstrap_candidate(
            m.Infra.CandidateBootstrapCommand(repository_root=source, check_only=True),
        )

        tm.ok(result.failure)
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(first_makefile, required=True)),
            eq=before,
        )

    @staticmethod
    @pytest.mark.slow
    def test_docs_config_conflict_recovers_from_declared_template(
        tmp_path: Path,
    ) -> None:
        """A conflicted docs projection is repaired before generation parses.

        Renders two real Make environments and runs two real bootstraps,
        like its slow-phase sibling below: alone it takes ~9s of the 10s
        bounded-phase item budget, so it belongs to the declared slow phase.
        """
        source, candidate = _declared_candidate_campaign(
            tmp_path,
            c.Infra.CodegenConformSurface.DOCS_CONFIG,
        )
        projection = candidate / c.Infra.DIR_DOCS / c.Infra.DOCS_CONFIG_FILENAME
        tm.ok(u.Cli.ensure_dir(projection.parent))
        tm.ok(u.Cli.atomic_write_text_file(projection, "<<<<<<< HEAD\n"))
        command = m.Infra.CandidateBootstrapCommand(repository_root=source)

        tm.ok(infra.bootstrap_candidate(command))
        first = tm.ok(u.Cli.atomic_read_binary_file_state(projection, required=True))
        tm.ok(u.Cli.json_loads(first.content or b""))
        tm.ok(infra.bootstrap_candidate(command))
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(projection, required=True)),
            eq=first,
        )

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("conflict_section", ["tool", "dependency-groups"])
    def test_pyproject_bootstrap_uses_declared_candidate_surface(
        tmp_path: Path,
        conflict_section: str,
    ) -> None:
        """A healthy provider restores a candidate before its own Make can import."""
        source, candidate = _declared_candidate_campaign(
            tmp_path,
            c.Infra.CodegenConformSurface.PYPROJECT,
        )
        tm.fail(u.Infra.workspace_manifest_path(source).exists())
        projection = candidate / c.PYPROJECT_FILENAME
        original = projection.read_text(encoding="utf-8")
        original_groups = u.Tests.toml_table_at(original, "dependency-groups")
        roots = TestsFlextInfraCodegenCandidateBootstrap._write_runtime_probe(
            candidate,
        )
        original = tm.ok(u.Infra.pyproject_regeneration_source(original))
        corrupt = (
            original
            + "\n[tool."
            + tm.ok(u.Infra.pyproject_managed_file()).managed_tool_tables[0]
            + "]\n<<<<<<< HEAD\n=======\n>>>>>>> incoming\n"
            if conflict_section == "tool"
            else original.replace(
                "[dependency-groups]\n",
                "[dependency-groups]\n<<<<<<< HEAD\n=======\n>>>>>>> incoming\n",
                1,
            )
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                projection,
                corrupt,
            ),
        )
        before = TestsFlextInfraConformSupport.project_tree(candidate)
        command = m.Infra.CandidateBootstrapCommand(repository_root=source)
        inputs = tm.ok(u.Infra.load_codegen_inputs(candidate))
        destinations = tm.not_none(
            FlextInfraCodegenConform.surface_contract(
                c.Infra.CodegenConformSurface.PYPROJECT,
                codegen=inputs.spec,
            ).destinations,
        )

        tm.ok(infra.bootstrap_candidate(command))
        first = tm.ok(u.Cli.atomic_read_binary_file_state(projection, required=True))
        tm.that(
            u.Cli.toml_mapping_from_text((first.content or b"").decode("utf-8"))
            is not None,
            eq=True,
        )
        restored = (first.content or b"").decode("utf-8")
        tm.that(restored, lacks="<<<<<<< HEAD")
        tm.that(
            u.Tests.toml_table_at(restored, "dependency-groups"),
            eq=original_groups,
        )
        after = TestsFlextInfraConformSupport.project_tree(candidate)
        for relative in inputs.spec.uv_resolution_pyprojects:
            view = candidate / relative
            tm.ok(view.is_file())
            tm.that(dict(after), has=relative.as_posix())
            tm.that(
                u.Cli.toml_mapping_from_text(view.read_text(encoding="utf-8"))
                is not None,
                eq=True,
            )
        tm.that(
            tuple(item for item in after if item[0] not in destinations),
            eq=tuple(item for item in before if item[0] not in destinations),
            msg=TestsFlextInfraConformSupport.project_tree_diff(
                tuple(item for item in before if item[0] not in destinations),
                tuple(item for item in after if item[0] not in destinations),
            ),
        )
        tm.that(
            u.Infra.runtime_evaluated_base_classes(candidate, {}, roots),
            eq=tuple(
                sorted({
                    *roots,
                    *(
                        f"bootstrap_probe.models.BootstrapProbe{index}"
                        for index in range(len(roots))
                    ),
                })
            ),
        )
        tm.ok(infra.bootstrap_candidate(command))
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(projection, required=True)),
            eq=first,
        )
        tm.that(TestsFlextInfraConformSupport.project_tree(candidate), eq=after)

    @staticmethod
    @pytest.mark.slow
    def test_dependencies_bootstrap_projects_resolution_inputs(
        tmp_path: Path,
    ) -> None:
        """A candidate without resolution inputs regains them through dependencies.

        A consumer crossing the generator generation has no resolution
        pyprojects yet; ``make upg`` refuses to lock without them and
        ``make setup`` refuses to run without their locks, so the provider's
        dependencies surface is the only route that can project them.
        """
        source, candidate = _declared_candidate_campaign(
            tmp_path,
            c.Infra.CodegenConformSurface.DEPENDENCIES,
        )
        inputs = tm.ok(u.Infra.load_codegen_inputs(candidate))
        resolution = tuple(inputs.spec.uv_resolution_pyprojects)
        tm.that(resolution, empty=False)
        for relative in resolution:
            (candidate / relative).unlink(missing_ok=True)
        before = TestsFlextInfraConformSupport.project_tree(candidate)
        destinations = tm.not_none(
            FlextInfraCodegenConform.surface_contract(
                c.Infra.CodegenConformSurface.DEPENDENCIES,
                codegen=inputs.spec,
            ).destinations,
        )
        command = m.Infra.CandidateBootstrapCommand(repository_root=source)

        tm.ok(infra.bootstrap_candidate(command))
        after = TestsFlextInfraConformSupport.project_tree(candidate)
        for relative in resolution:
            view = candidate / relative
            tm.ok(view.is_file())
            tm.that(
                u.Cli.toml_mapping_from_text(view.read_text(encoding="utf-8"))
                is not None,
                eq=True,
            )
        tm.that(
            tuple(item for item in after if item[0] not in destinations),
            eq=tuple(item for item in before if item[0] not in destinations),
            msg=TestsFlextInfraConformSupport.project_tree_diff(
                tuple(item for item in before if item[0] not in destinations),
                tuple(item for item in after if item[0] not in destinations),
            ),
        )
        tm.ok(infra.bootstrap_candidate(command))
        tm.that(TestsFlextInfraConformSupport.project_tree(candidate), eq=after)
