"""Candidate bootstrap campaigns through the public Infra facade.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from flext_infra import config, infra
from flext_infra.codegen.conform import FlextInfraCodegenConform
from tests import c, m, t, tm, u
from tests.unit.codegen.conform_support import TestsFlextInfraConformSupport


def _write_candidate_targets(
    root: Path,
    targets: t.SequenceOf[m.Infra.CandidateBootstrapTargetSpec],
) -> Path:
    """Declare recovery targets through the repository's current config owner."""
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

        tm.that(result.failure, eq=True)
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

        tm.that(result.failure, eq=True)
        tm.that(result.error, has="duplicate worktrees")
        tm.that(TestsFlextInfraConformSupport.project_tree(candidate), eq=before)

    @pytest.mark.slow
    def test_initializer_surface_recovers_without_touching_module_source(
        self,
        tmp_path: Path,
    ) -> None:
        """Dynamic initializer destinations retain source and converge."""
        source, first, _ = self._campaign(tmp_path)
        package = first / "src" / "bootstrap_case"
        package.mkdir(parents=True)
        module = package / "domain.py"
        module.write_text(
            "class FlextBootstrapCase:\n    pass\n__all__ = ['FlextBootstrapCase']\n",
            encoding="utf-8",
        )
        initializer = package / c.Infra.INIT_PY
        initializer.write_text("# stale initializer\n", encoding="utf-8")
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
        tm.that(generated.content, ne=b"# stale initializer\n")
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

        tm.that(result.failure, eq=True)
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
        second_declaration = second / c.CONFIG_DIR_NAME / c.Infra.CODEGEN_CONFIG_FILENAME
        original = second_declaration.read_text(encoding="utf-8")
        second_declaration.write_text("invalid: [\n", encoding="utf-8")

        failed = infra.bootstrap_candidate(
            m.Infra.CandidateBootstrapCommand(repository_root=source),
        )

        tm.that(failed.failure, eq=True)
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

        tm.that(result.failure, eq=True)
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
        tm.that(u.Infra.workspace_manifest_path(source).exists(), eq=False)
        projection = candidate / c.PYPROJECT_FILENAME
        original = projection.read_text(encoding="utf-8")
        original_groups = u.Tests.toml_table_at(original, "dependency-groups")
        roots = TestsFlextInfraCodegenCandidateBootstrap._write_runtime_probe(
            candidate,
        )
        original = tm.ok(u.Infra.pyproject_regeneration_source(original))
        conflict = "<<<<<<< HEAD\n=======\n>>>>>>> incoming\n"
        corrupt = (
            original
            + "\n[tool."
            + tm.ok(u.Infra.pyproject_managed_file()).managed_tool_tables[0]
            + "]\n"
            + conflict
            if conflict_section == "tool"
            else original.replace(
                "[dependency-groups]\n",
                f"[dependency-groups]\n{conflict}",
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
        contract = FlextInfraCodegenConform.surface_contract(
            c.Infra.CodegenConformSurface.PYPROJECT,
            codegen=inputs.spec,
        )
        destinations = contract.destinations
        assert destinations is not None

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
            tm.that(view.is_file(), eq=True)
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
