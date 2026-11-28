"""Tests for the declarative project-layout engine (flext-0wuz, epic flext-hzox).

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

from flext_infra.gates import FlextInfraGatesLayout
from tests import FlextInfraConfig, c, config, m, p, t, tm, u
from tests.unit.codegen import TestsFlextInfraCodegenLayoutSupport

pytestmark = c.Tests.MARK.slow


class TestsFlextInfraCodegenLayout:
    """Test suite for the declarative project-layout engine."""

    @staticmethod
    def _fresh_layout_report(project: Path) -> p.Infra.LayoutProjectReport:
        """Load consumer-owned configuration in a new public-service process.

        Returns:
            The resulting ``m.Infra.LayoutProjectReport``.

        """
        process = tm.ok(
            u.Cli.run_raw(
                [
                    sys.executable,
                    "-c",
                    (
                        "from pathlib import Path\n"
                        "from flext_infra.codegen import FlextInfraCodegenLayout\n"
                        "root = Path.cwd()\n"
                        "report = FlextInfraCodegenLayout(repository_root=root)"
                        ".check_project(root)\n"
                        "print(report.model_dump_json(exclude_computed_fields=True))\n"
                    ),
                ],
                cwd=project,
                options=m.Cli.ProcessOptions(
                    env={
                        "FLEXT_INFRA_CONFIG_DIR": str(
                            FlextInfraConfig.ssot_config_dir(),
                        ),
                    },
                ),
            ),
        )
        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=True,
            msg=process.stdout + process.stderr,
        )
        return m.Infra.LayoutProjectReport.model_validate_json(process.stdout)

    @classmethod
    def _assert_keep_override(
        cls,
        tmp_path: Path,
        *,
        distribution: str,
        checkout_name: str,
        keep_count: int,
    ) -> None:
        """Prove declared files change classification without changing defaults."""
        project = TestsFlextInfraCodegenLayoutSupport.build_loose_project(
            tmp_path, name=distribution
        )
        if project.name != checkout_name:
            project = project.rename(tmp_path / checkout_name)
        candidates = tuple(f"consumer-note-{index}.fixture" for index in range(3))
        for filename in candidates:
            (project / filename).write_text(f"{filename}\n", encoding="utf-8")
        u.Tests.git_run(project, "add", "--", *candidates)
        # Why in-process: no org overlay exists yet, so the baseline carries no
        # config the long-lived worker's frozen config singleton could leak
        # across parametrized cases. Only the post-override read below (which
        # must observe the just-written project-scoped overlay) pays for a
        # fresh interpreter; halving the subprocess count keeps both reads
        # inside the default per-test budget.
        baseline = TestsFlextInfraCodegenLayoutSupport.layout_engine(
            project
        ).check_project(project)
        baseline_paths = {finding.path for finding in baseline.findings}
        tm.ok(set(candidates) <= baseline_paths)
        override = m.Infra.LayoutProjectOverrideSpec(
            keep_root_files=candidates[:keep_count],
        )
        # The org overlay is a partial delta file; the real config loader
        # deep-merges it and validates the merged result against the strict
        # root model, which the layout subprocess below exercises.
        overlay: t.JsonMapping = {
            "Infra": {
                "codegen": {
                    "checkout_submodules_overrides": {},
                    "ci_private_submodules": {},
                    "layout": {
                        "project_overrides": {
                            distribution: override.model_dump(mode="json"),
                        },
                    },
                },
            },
        }
        _, _, local_overlay = FlextInfraConfig.config_layer_paths_for_repository(
            project,
            filename=c.Infra.CODEGEN_CONFIG_FILENAME,
        )
        tm.ok(local_overlay.is_relative_to(tmp_path))
        local_overlay.parent.mkdir(exist_ok=True)
        tm.ok(u.Cli.yaml_dump(local_overlay, overlay))

        report = cls._fresh_layout_report(project)

        tm.that(report.project, eq=distribution)
        paths = {finding.path for finding in report.findings}
        tm.that(
            paths & set(candidates),
            eq=set(candidates) - set(override.keep_root_files),
        )
        for filename in candidates:
            tm.that(
                (project / filename).read_text(encoding="utf-8"),
                eq=f"{filename}\n",
            )

    @staticmethod
    def test_check_reports_move_retirement_and_review(
        tmp_path: Path,
    ) -> None:
        """Check mode classifies every loose root entry without writing."""
        project = TestsFlextInfraCodegenLayoutSupport.build_loose_project(tmp_path)
        engine = TestsFlextInfraCodegenLayoutSupport.layout_engine(tmp_path)

        report = engine.check_project(project)

        by_path = {finding.path: finding for finding in report.findings}
        tm.that(by_path["guides"].rule, eq="move")
        tm.that(by_path["guides"].target, eq="docs/guides")
        tm.that(by_path["index.md"].rule, eq="move")
        tm.that(by_path["output.log"].rule, eq="retire")
        tm.that(by_path["output.log"].target, eq="")
        tm.that(by_path["loose.txt"].rule, eq="review")
        ignore = [finding for finding in report.findings if finding.rule == "gitignore"]
        tm.that(ignore, eq=[])

    @staticmethod
    def test_check_execute_fails_on_layout_findings(
        tmp_path: Path,
    ) -> None:
        """A layout finding blocks the check at every severity."""
        TestsFlextInfraCodegenLayoutSupport.build_loose_project(tmp_path)
        engine = TestsFlextInfraCodegenLayoutSupport.layout_engine(tmp_path)

        result = engine.execute()

        tm.fail(result, has="move guides -> docs/guides")

    @staticmethod
    def test_apply_moves_retires_and_converges_idempotently(
        tmp_path: Path,
    ) -> None:
        """Apply reorganizes once; a second apply performs zero operations."""
        project = TestsFlextInfraCodegenLayoutSupport.build_loose_project(tmp_path)
        engine = TestsFlextInfraCodegenLayoutSupport.layout_engine(
            tmp_path, apply_changes=True
        )

        first = engine.execute()

        tm.ok(first)
        tm.ok((project / "docs" / "guides" / "intro.md").is_file())
        tm.ok((project / "docs" / "index.md").is_file())
        tm.that(u.Tests.git_capture(project, "show", "HEAD:output.log"), eq="log-line")
        tm.fail((project / "guides").exists())
        tm.fail((project / "output.log").exists())
        tm.ok((project / "loose.txt").is_file())
        second = engine.execute()
        tm.ok(second)
        tm.that(second.value, has="0 applied")
        residual = engine.check_project(project)
        tm.that(len(residual.actionable), eq=0)
        tm.that([finding.rule for finding in residual.findings], eq=["review"])

    @staticmethod
    def test_apply_docs_collision_fails_and_preserves_both_sources(
        tmp_path: Path,
    ) -> None:
        """Different-content collisions fail while preserving both original paths."""
        project = TestsFlextInfraCodegenLayoutSupport.build_loose_project(tmp_path)
        existing = project / "docs" / "guides"
        existing.mkdir(parents=True)
        (existing / "intro.md").write_text("canonical\n", encoding="utf-8")
        engine = TestsFlextInfraCodegenLayoutSupport.layout_engine(
            tmp_path, apply_changes=True
        )

        result = engine.execute()

        tm.fail(result, has="layout collision")
        tm.that((existing / "intro.md").read_text(encoding="utf-8"), eq="canonical\n")
        tm.that(
            (project / "guides" / "intro.md").read_text(encoding="utf-8"), eq="intro\n"
        )

    @staticmethod
    @c.Tests.MARK.parametrize("relative", ["index.md", "guides/intro.md"])
    def test_identical_docs_duplicate_retires_only_the_committed_source(
        tmp_path: Path, relative: str
    ) -> None:
        """Identical destinations remain canonical while Git retains the original."""
        project = TestsFlextInfraCodegenLayoutSupport.build_loose_project(tmp_path)
        source = project / relative
        original = source.read_bytes()
        target = project / "docs" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(original)
        engine = TestsFlextInfraCodegenLayoutSupport.layout_engine(
            tmp_path, apply_changes=True
        )

        tm.ok(engine.execute())

        tm.fail(source.exists())
        tm.that(target.read_bytes(), eq=original)
        tm.that(
            u.Tests.git_capture(project, "show", f"HEAD:{relative}"),
            eq=original.decode(c.DEFAULT_ENCODING).strip(),
        )

    @staticmethod
    def test_identical_docs_bytes_with_different_modes_remain_a_collision(
        tmp_path: Path,
    ) -> None:
        """A duplicate's executable mode cannot be discarded by byte equality."""
        project = TestsFlextInfraCodegenLayoutSupport.build_loose_project(tmp_path)
        source = project / "index.md"
        target = project / "docs" / source.name
        target.parent.mkdir(parents=True)
        target.write_bytes(source.read_bytes())
        source.chmod(0o644)
        target.chmod(0o755)
        engine = TestsFlextInfraCodegenLayoutSupport.layout_engine(
            tmp_path, apply_changes=True
        )
        original = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
        canonical = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))

        tm.fail(engine.execute(), has="layout collision")

        tm.ok(u.Cli.atomic_verify_binary_file_states((original, canonical)))

    @staticmethod
    @c.Tests.MARK.parametrize(
        "state", ["modified", "staged", "index_only", "untracked", "staged_only"]
    )
    def test_retirement_preserves_content_not_committed_in_its_current_state(
        tmp_path: Path, state: str
    ) -> None:
        """Uncommitted worktree or index content blocks retirement without loss."""
        project = TestsFlextInfraCodegenLayoutSupport.build_loose_project(tmp_path)
        engine = TestsFlextInfraCodegenLayoutSupport.layout_engine(
            tmp_path, apply_changes=True
        )
        source = project / (
            "new-output.log" if state in {"untracked", "staged_only"} else "output.log"
        )
        source.write_bytes(b"unique work in progress\n")
        if state in {"staged", "staged_only", "index_only"}:
            tm.ok(u.Tests.git_run(project, "add", "--", source.name))
        if state == "index_only":
            source.write_bytes(b"log-line\n")
        before = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
        request = m.Infra.GitRelativePathRequest(
            repo_root=project, relative_path=source.name
        )
        index = tm.ok(u.Infra.git_capture_index_file(request))

        tm.fail(engine.execute(), has="requires unchanged content committed in Git")

        tm.ok(u.Cli.atomic_verify_binary_file_states((before,)))
        tm.that(tm.ok(u.Infra.git_capture_index_file(request)), eq=index)

    @staticmethod
    @c.Tests.MARK.parametrize("ignored", [False, True])
    def test_directory_retirement_preserves_uncommitted_descendants(
        tmp_path: Path, *, ignored: bool
    ) -> None:
        """Physical inventory protects ignored and untracked bytes within a tree."""
        project = TestsFlextInfraCodegenLayoutSupport.build_loose_project(tmp_path)
        logs = project / "logs"
        logs.mkdir()
        committed = logs / "saved.txt"
        committed.write_bytes(b"committed log\n")
        engine = TestsFlextInfraCodegenLayoutSupport.layout_engine(
            tmp_path, apply_changes=True
        )
        unique = logs / "current.local"
        unique.write_bytes(b"uncommitted log\n")
        if ignored:
            (project / c.Infra.GITIGNORE).write_text("*.local\n", encoding="utf-8")

        tm.fail(engine.execute(), has="requires unchanged content committed in Git")

        tm.that(committed.read_bytes(), eq=b"committed log\n")
        tm.that(unique.read_bytes(), eq=b"uncommitted log\n")

    @staticmethod
    def test_directory_retirement_preserves_exact_bytes_in_git(
        tmp_path: Path,
    ) -> None:
        """Committed binary content remains recoverable after physical retirement."""
        project = TestsFlextInfraCodegenLayoutSupport.build_loose_project(tmp_path)
        nested = project / "logs" / "nested"
        nested.mkdir(parents=True)
        original = b"\x00saved\xff\r\n"
        (nested / "saved.bin").write_bytes(original)
        engine = TestsFlextInfraCodegenLayoutSupport.layout_engine(
            tmp_path, apply_changes=True
        )

        tm.ok(engine.execute())

        tm.fail((project / "logs").exists())
        saved = tm.ok(u.Infra.git_committed_directory_blobs(project, "logs/nested"))
        tm.that(saved["saved.bin"], eq=original)
        tm.that(u.Tests.git_capture(project, "ls-files", "--", "logs"), eq="")

    @staticmethod
    def test_changed_layout_input_blocks_a_previously_planned_retirement(
        tmp_path: Path,
    ) -> None:
        """The configuration selecting deletion is reverified before any effect."""
        project = TestsFlextInfraCodegenLayoutSupport.build_loose_project(tmp_path)
        engine = TestsFlextInfraCodegenLayoutSupport.layout_engine(
            tmp_path, apply_changes=True
        )
        TestsFlextInfraCodegenLayoutSupport.declare_layout_override(
            project, m.Infra.LayoutProjectOverrideSpec()
        )
        report = engine.check_project(project)
        _, declaration, _ = FlextInfraConfig.config_layer_paths_for_repository(
            project, filename=c.Infra.CODEGEN_CONFIG_FILENAME
        )
        declaration.write_bytes(declaration.read_bytes() + b"\n# changed after planning\n")

        tm.fail(engine.apply_project(project, report), has="atomic source changed")

        tm.that((project / "output.log").read_bytes(), eq=b"log-line\n")
        tm.that((project / "guides" / "intro.md").read_bytes(), eq=b"intro\n")

    @staticmethod
    def test_git_tracking_failure_cannot_fall_back_to_a_filesystem_move(
        tmp_path: Path,
    ) -> None:
        """A genuine unreadable Git index keeps the source at its original path."""
        project = TestsFlextInfraCodegenLayoutSupport.build_loose_project(tmp_path)
        engine = TestsFlextInfraCodegenLayoutSupport.layout_engine(
            tmp_path, apply_changes=True
        )
        report = engine.check_project(project)
        (project / c.GIT_DIR_NAME / "index").write_bytes(b"invalid Git index\n")

        tm.fail(
            engine.apply_project(project, report), has="failed to check tracked status"
        )

        tm.that((project / "guides" / "intro.md").read_bytes(), eq=b"intro\n")
        tm.fail((project / "docs").exists())

    @staticmethod
    def test_serialized_report_cannot_apply_without_its_captured_inputs(
        tmp_path: Path,
    ) -> None:
        """A display report does not carry the read authority for deletion."""
        project = TestsFlextInfraCodegenLayoutSupport.build_loose_project(tmp_path)
        engine = TestsFlextInfraCodegenLayoutSupport.layout_engine(
            tmp_path, apply_changes=True
        )
        planned = engine.check_project(project)
        report = m.Infra.LayoutProjectReport.model_validate_json(
            planned.model_dump_json(exclude_computed_fields=True)
        )

        tm.fail(engine.apply_project(project, report), has="captured configuration inputs")

        tm.that((project / "output.log").read_bytes(), eq=b"log-line\n")
        tm.that((project / "guides" / "intro.md").read_bytes(), eq=b"intro\n")

    @staticmethod
    @c.Tests.MARK.parametrize("extra_file", [False, True])
    def test_apply_override_move_prunes_only_an_empty_dir(
        tmp_path: Path,
        *,
        extra_file: bool,
    ) -> None:
        """Declared moves retain content before pruning their emptied directory."""
        project = tmp_path / "flext-dbt-ldif"
        profiles = project / "profiles"
        package_dir = project / "src" / "flext_dbt_ldif"
        package_dir.mkdir(parents=True)
        (package_dir / "__init__.py").write_text("", encoding="utf-8")
        profiles.mkdir(parents=True)
        (project / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname='flext-dbt-ldif'\nversion='0.1.0'\n",
            encoding="utf-8",
        )
        (profiles / "profiles.yml").write_text("profile: 1\n", encoding="utf-8")
        u.Tests.declare_workspace_projects(tmp_path, (project.name,))
        engine = TestsFlextInfraCodegenLayoutSupport.layout_engine(
            tmp_path, apply_changes=True
        )
        TestsFlextInfraCodegenLayoutSupport.declare_layout_override(
            project,
            m.Infra.LayoutProjectOverrideSpec(
                moves=(
                    m.Infra.LayoutMoveSpec(
                        source="profiles/profiles.yml", target="profiles.yml"
                    ),
                ),
                prune_empty_dirs=("profiles",),
                keep_root_files=("profiles.yml",),
            ),
        )
        if extra_file:
            (profiles / "keep.txt").write_bytes(b"authored content\n")

        result = engine.execute()

        if extra_file:
            tm.fail(result, has="directory still contains preserved content")
            tm.that((profiles / "keep.txt").read_bytes(), eq=b"authored content\n")
        else:
            tm.ok(result)
            tm.fail(profiles.exists())
        tm.that((project / "profiles.yml").read_bytes(), eq=b"profile: 1\n")
        tm.that(
            u.Tests.git_capture(project, "ls-files", "--", "profiles.yml"),
            eq="profiles.yml",
        )

    @staticmethod
    def test_gate_reports_violations_as_blocking_errors(tmp_path: Path) -> None:
        """Every layout finding fails the gate and is reported at error severity."""
        project = TestsFlextInfraCodegenLayoutSupport.build_loose_project(tmp_path)
        gate = FlextInfraGatesLayout(tmp_path)
        ctx = m.Infra.GateContext(
            repository_root=tmp_path,
            reports_dir=tmp_path / ".reports",
        )

        execution = gate.check(project, ctx)

        tm.fail(execution.result.passed)
        tm.ok(bool(execution.issues))
        tm.that(
            {issue.severity for issue in execution.issues},
            eq={c.Infra.GateSeverity.ERROR.value},
        )

    @c.Tests.MARK.parametrize("keep_count", [0, 1, 3])
    def test_keep_root_files_override(self, tmp_path: Path, keep_count: int) -> None:
        """Arbitrary consumer keep-lists preserve only their declared root files."""
        self._assert_keep_override(
            tmp_path,
            distribution="fixture-layout-consumer",
            checkout_name="fixture-layout-consumer",
            keep_count=keep_count,
        )

    @c.Tests.MARK.parametrize("keep_count", [0, 1, 3])
    def test_override_resolves_by_declared_name_not_checkout_directory(
        self,
        tmp_path: Path,
        keep_count: int,
    ) -> None:
        """Renamed checkouts still consume the PEP 621 distribution's keep-list."""
        self._assert_keep_override(
            tmp_path,
            distribution="fixture-declared-layout",
            checkout_name="independent-checkout-name",
            keep_count=keep_count,
        )

    @staticmethod
    def test_special_and_reference_root_dirs_skipped(tmp_path: Path) -> None:
        """data/ is skipped; external-docs/ is allowed as reference corpus."""
        project = TestsFlextInfraCodegenLayoutSupport.build_loose_project(tmp_path)
        (project / "data").mkdir()
        (project / "data" / "proposal").mkdir()
        (project / "external-docs").mkdir()
        (project / "external-docs" / "note.md").write_text("ext\n", encoding="utf-8")
        engine = TestsFlextInfraCodegenLayoutSupport.layout_engine(tmp_path)

        report = engine.check_project(project)

        paths = {finding.path for finding in report.findings}
        tm.fail("data" in paths)
        tm.fail("external-docs" in paths)

    @staticmethod
    def test_catalog_roots_are_canonical_for_their_make_profile(
        tmp_path: Path,
    ) -> None:
        """A root the template catalog projects is canonical for its profile only."""
        roots: dict[c.Infra.MakeProfile, set[str]] = {
            profile: {
                Path(entry.destination).parts[0]
                for entry in config.Infra.codegen.templates.entries
                if profile in entry.profiles and not entry.destination.startswith(".")
            }
            for profile in c.Infra.MakeProfile
        }
        project = TestsFlextInfraCodegenLayoutSupport.build_loose_project(tmp_path)
        for root, names in (
            (project, roots[c.Infra.MakeProfile.STANDALONE]),
            (tmp_path, roots[c.Infra.MakeProfile.WORKSPACE]),
        ):
            for name in names:
                if not (root / name).exists():
                    (root / name).write_text("generated\n", encoding="utf-8")
        engine = TestsFlextInfraCodegenLayoutSupport.layout_engine(tmp_path)

        standalone = {
            finding.path for finding in engine.check_project(project).findings
        }
        workspace = {
            finding.path for finding in engine.check_project(tmp_path).findings
        }

        tm.that(standalone & roots[c.Infra.MakeProfile.STANDALONE], eq=set())
        tm.that(workspace & roots[c.Infra.MakeProfile.WORKSPACE], eq=set())
        workspace_only = (
            roots[c.Infra.MakeProfile.WORKSPACE] - roots[c.Infra.MakeProfile.STANDALONE]
        )
        for name in workspace_only:
            (project / name).write_text("generated\n", encoding="utf-8")
        reviewed = {finding.path for finding in engine.check_project(project).findings}
        tm.that(workspace_only - reviewed, eq=set())

    @staticmethod
    def test_infrastructure_root_is_canonical(tmp_path: Path) -> None:
        """Pulumi and Ansible share the canonical root infrastructure directory."""
        project = TestsFlextInfraCodegenLayoutSupport.build_loose_project(tmp_path)
        infrastructure = project / "infra"
        infrastructure.mkdir()
        (infrastructure / "Pulumi.yaml").write_text("name: fixture\n", encoding="utf-8")
        engine = TestsFlextInfraCodegenLayoutSupport.layout_engine(tmp_path)

        report = engine.check_project(project)

        paths = {finding.path for finding in report.findings}
        tm.fail("infra" in paths)

    @staticmethod
    def test_declared_repositories_are_canonical_root_entries(
        tmp_path: Path,
    ) -> None:
        """A workspace root accepts only repository directories declared by topology."""
        declared_name = "flext-declared"
        undeclared_name = "flext-undeclared"
        (tmp_path / declared_name).mkdir()
        (tmp_path / undeclared_name).mkdir()
        # Why: an empty directory carries no git-trackable content — git status
        # never reports it, so the layout engine's git-tracked-entries scope (the
        # current contract) would silently skip it rather than flag it. A real
        # file makes the untracked directory visible to `git status`, matching
        # how an actual undeclared repository shows up on disk.
        (tmp_path / undeclared_name / "marker.txt").write_text("x", encoding="utf-8")
        u.Tests.declare_workspace_projects(tmp_path, (declared_name,))
        engine = TestsFlextInfraCodegenLayoutSupport.layout_engine(tmp_path)

        report = engine.check_project(tmp_path)

        findings = {finding.path: finding for finding in report.findings}
        tm.fail(declared_name in findings)
        tm.that(findings[undeclared_name].rule, eq="review")

    @staticmethod
    def test_duplicate_root_md_fails_when_docs_copy_differs(
        tmp_path: Path,
    ) -> None:
        """A canonical Markdown destination cannot hide a divergent root source."""
        project = TestsFlextInfraCodegenLayoutSupport.build_loose_project(tmp_path)
        docs = project / "docs"
        docs.mkdir(parents=True, exist_ok=True)
        (docs / "index.md").write_text("canonical-index\n", encoding="utf-8")
        engine = TestsFlextInfraCodegenLayoutSupport.layout_engine(
            tmp_path, apply_changes=True
        )

        result = engine.execute()

        tm.fail(result, has="layout collision")
        tm.that((docs / "index.md").read_text(encoding="utf-8"), eq="canonical-index\n")
        tm.that((project / "index.md").read_text(encoding="utf-8"), eq="index\n")
