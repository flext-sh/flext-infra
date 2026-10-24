"""Read-only publication-plan contracts for generated documentation.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra.docs.generator import FlextInfraDocGenerator
from tests import c, m, tm, u


class TestsFlextInfraDocsGeneratorPlan:
    """Read-only publication-plan contracts for generated documentation."""

    @staticmethod
    def test_duplicate_docs_targets_fail_before_effects(
        tmp_path: Path,
    ) -> None:
        """Fail before effects when two rendered artifacts claim one target."""
        workspace = u.Tests.create_docs_workspace(tmp_path, project_names=("flext-a",))

        generator = FlextInfraDocGenerator(
            repository_root=workspace,
            selected_projects=["flext-a", "flext-a"],
        )
        prepared = generator.prepare_bundle()

        tm.fail(prepared)
        tm.that(prepared.error or "", has="duplicate docs publication target")

    @staticmethod
    def test_plan_files_returns_exact_read_only_docs_plans(
        tmp_path: Path,
    ) -> None:
        """Describe generated artifacts without changing the workspace."""
        workspace = u.Tests.create_docs_workspace(tmp_path, project_names=("flext-a",))
        before = {
            path: path.read_bytes() for path in workspace.rglob("*") if path.is_file()
        }

        generator = FlextInfraDocGenerator(
            repository_root=workspace,
            selected_projects=["flext-a"],
        )
        plans = u.Tests.plan_docs_bundle(generator)

        tm.that(plans, empty=False)
        tm.that(
            all(plan.desired_mode == c.Infra.DOCS_ARTIFACT_MODE for plan in plans),
            eq=True,
        )
        tm.that(
            {
                path: path.read_bytes()
                for path in workspace.rglob("*")
                if path.is_file()
            },
            eq=before,
        )
        tm.fail((workspace / ".reports").exists())

    @staticmethod
    def test_generate_publishes_and_reaches_an_unchanged_second_run(
        tmp_path: Path,
    ) -> None:
        """The public fixed-effect command writes and converges without a mode flag."""
        workspace = u.Tests.create_docs_workspace(tmp_path)
        generator = FlextInfraDocGenerator(repository_root=workspace)
        plans = u.Tests.plan_docs_bundle(generator)
        changed = next(
            plan
            for plan in plans
            if plan.desired_content is not None
            and u.Infra.codegen_file_requires_effect(plan)
        )
        request = m.Infra.DocsGenerateRequest(repository_root=workspace)
        first = generator.generate(request)
        tm.ok(first)
        tm.ok(any(report.generated for report in first.value))
        tm.that(changed.path.read_bytes(), eq=changed.desired_content)
        second = generator.generate(request)
        tm.ok(second)
        tm.that(
            all(report.changed_files == 0 and report.passed for report in second.value),
            eq=True,
        )

    @staticmethod
    def test_stale_generated_markdown_becomes_delete_plan(tmp_path: Path) -> None:
        """Represent stale generated cleanup as a delete plan."""
        workspace = u.Tests.create_docs_workspace(tmp_path, project_names=("flext-a",))
        stale = workspace / "flext-a/docs/api-reference/generated/stale.md"
        stale.parent.mkdir(parents=True, exist_ok=True)
        stale.write_text("stale\n", encoding="utf-8")

        generator = FlextInfraDocGenerator(
            repository_root=workspace,
            selected_projects=["flext-a"],
        )
        plans = u.Tests.plan_docs_bundle(generator)

        stale_plan = next(plan for plan in plans if plan.path == stale)
        tm.that(stale_plan.desired_content, eq=None)
        tm.ok(u.Infra.codegen_file_requires_effect(stale_plan))
        tm.that(stale_plan.before.content, eq=b"stale\n")
        tm.ok(stale.exists())

    @staticmethod
    def test_scope_failure_is_not_normalized_to_empty_aggregate(
        tmp_path: Path,
    ) -> None:
        """Propagate malformed workspace topology instead of rendering an empty root."""
        workspace = u.Tests.create_docs_workspace(tmp_path)
        (workspace / ".gitmodules").write_text(
            '[submodule "broken"]\n\tpath = ../outside\n',
            encoding="utf-8",
        )

        generator = FlextInfraDocGenerator(repository_root=workspace)
        prepared = generator.prepare_bundle()

        tm.fail(prepared)
        tm.that(prepared.error or "", has="invalid Git submodule path")
