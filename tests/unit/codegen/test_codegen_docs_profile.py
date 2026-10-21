"""Native docs recipe profiling and invocation-isolated report contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pstats
import sys
from pathlib import Path

import pytest

from flext_infra import config
from tests import c, p, tm, u


class TestsFlextInfraDocsProfile:
    """Exercise generated recipes with the real docs and profiling consumers."""

    @staticmethod
    def _render(root: Path, profile: c.Infra.MakeProfile) -> str:
        """Return the conformed Makefile for a real fixture repository."""
        repository = u.Tests.repository_ref(root.name, role=profile)
        return u.Tests.conform_makefile_text(
            root,
            u.Tests.workspace_spec(
                repository,
                project=u.Tests.project_spec(root.name),
            ),
        )

    @staticmethod
    def _recipe(rendered: str, target: str) -> str:
        """Return the final recipe declaration rather than its earlier guard."""
        return rendered.rsplit(f"\n{target}:", 1)[1].split("\n\n", 1)[0]

    @pytest.mark.parametrize(
        "profile", [c.Infra.MakeProfile.WORKSPACE, c.Infra.MakeProfile.STANDALONE]
    )
    def test_projection_profiles_the_same_configured_docs_lifecycle(
        self, tmp_path: Path, profile: c.Infra.MakeProfile
    ) -> None:
        """Both public profiles retain action order, mutation policy and guards."""
        root = u.Tests.create_docs_workspace(tmp_path)
        rendered = self._render(root, profile)
        docs = config.Infra.codegen.make.docs
        tm.that(rendered, has=f"DOCS_ACTIONS := {' '.join(docs.actions)}")
        normal = self._recipe(rendered, "_builtin_docs_all")
        measured = self._recipe(rendered, "_builtin-profile-docs")
        for recipe in (normal, measured):
            tm.that(recipe, has="for action in $(DOCS_ACTIONS); do")
            tm.that(
                recipe,
                has=(
                    f'case "$$action" in {"|".join(docs.mutable_actions)}) mode=--apply'
                ),
            )
            tm.that(
                recipe,
                has='docs "$$action" --repository-root "$(PROJECT_ROOT)" '
                f'--output-dir "{docs.reports_dir}" $$mode --projects .;',
            )
        tm.that(normal, lacks="_profile_entry")
        tm.that(
            measured,
            has='-m flext_infra._profile_entry "$$profile_dir/$$action.pstats"',
        )
        for verb in ("profile-docs", "profile-docs-report"):
            tm.that(
                rendered,
                has=[
                    f"{verb}: _builtin_require_workspace",
                    f"_builtin-{verb}: _builtin_require_environment",
                ],
            )
        report = self._recipe(rendered, "_builtin-profile-docs-report")
        tm.that(report, has='done < "$$profile_dir/actions"')
        tm.that(report, lacks=["*.pstats", "for action in $(DOCS_ACTIONS)"])

    def test_native_failure_retains_reached_profiles_without_stale_phases(
        self, tmp_path: Path
    ) -> None:
        """A later failed run cannot inherit an earlier run's completed phase."""
        root = u.Tests.create_docs_workspace(tmp_path, include_fixable_link=True)
        rendered = self._render(root, c.Infra.MakeProfile.STANDALONE)
        reports = root / ".reports" / "cprofile"
        # Exercise emitted recipe bodies, not a replacement docs runner. Runtime
        # guards and public routing are covered by the projection contract above.
        recipes = [
            f"PROJECT_ROOT := {root}",
            f"PROFILE_REPORTS_DIR := {reports}",
            f'PROJECT_INFRA_RUN := "{sys.executable}"',
            "PROJECT_FLEXT_INFRA := $(PROJECT_INFRA_RUN) -m flext_infra",
            "DOCS_ACTIONS := fix validate",
        ]
        for target in (
            "_builtin_docs_all",
            "_builtin-profile-docs",
            "_builtin-profile-docs-report",
        ):
            body = self._recipe(rendered, target).split("\n", 1)[1]
            recipes.append(f"{target}:\n{body}")
        fixture_makefile = root / "profile-recipes.mk"
        fixture_makefile.write_text(
            "\n\n".join(recipes) + "\n", encoding=c.DEFAULT_ENCODING
        )

        def run(target: str, *arguments: str) -> p.Cli.CommandOutput:
            """Return one native fixture Make outcome without normalizing failure."""
            return tm.ok(
                u.Tests.run_isolated_make(
                    [
                        "--no-print-directory",
                        "-f",
                        str(fixture_makefile),
                        target,
                        *arguments,
                    ],
                    cwd=root,
                )
            )

        # The fixture intentionally lacks required docs, while its fixable link
        # is real input to the mutating docs service, not a recorded invocation.
        (root / "README.md").unlink()
        tm.ok(
            u.Cli.process_succeeded(
                run("_builtin-profile-docs", "DOCS_ACTIONS=fix").outcome
            )
        )
        completed_run = Path(
            (reports / "docs.latest").read_text(encoding=c.DEFAULT_ENCODING).strip()
        )
        tm.that(
            (completed_run / "status").read_text(encoding=c.DEFAULT_ENCODING),
            eq="complete\n",
        )
        reference = run("_builtin_docs_all", "DOCS_ACTIONS=validate")
        tm.fail(u.Cli.process_succeeded(reference.outcome))
        first = run("_builtin-profile-docs")
        tm.that(first.outcome.raw_return_code, eq=reference.outcome.raw_return_code)
        native_failure = reference.stderr.rsplit("Error ", 1)[1].splitlines()[0]
        tm.that(first.stderr, has=f"Error {native_failure}")
        first_run = Path(
            (reports / "docs.latest").read_text(encoding=c.DEFAULT_ENCODING).strip()
        )
        tm.that(
            (first_run / "status").read_text(encoding=c.DEFAULT_ENCODING),
            eq="incomplete\n",
        )
        tm.that(
            (first_run / "fix.status").read_text(encoding=c.DEFAULT_ENCODING),
            eq="complete\n",
        )
        tm.that(
            (first_run / "validate.status").read_text(encoding=c.DEFAULT_ENCODING),
            eq="started\n",
        )
        tm.that(
            (root / "docs/README.md").read_text(encoding=c.DEFAULT_ENCODING),
            has="(guides/setup.md)",
        )
        for action in ("fix", "validate"):
            tm.that(
                pstats
                .Stats(str(first_run / f"{action}.pstats"))
                .get_stats_profile()
                .func_profiles,
                truth=True,
            )
        report = run("_builtin-profile-docs-report")
        tm.ok(u.Cli.process_succeeded(report.outcome))
        tm.that(
            report.stdout,
            has=[
                "status=incomplete",
                "phase=fix status=complete",
                "phase=validate status=started",
            ],
        )
        tm.ok((first_run / "fix.txt").is_file())

        second = run("_builtin-profile-docs", "DOCS_ACTIONS=validate fix")
        tm.that(second.outcome.raw_return_code, eq=first.outcome.raw_return_code)
        second_run = Path(
            (reports / "docs.latest").read_text(encoding=c.DEFAULT_ENCODING).strip()
        )
        tm.that(second_run, ne=first_run)
        tm.fail((second_run / "fix.pstats").exists())
        latest = run("_builtin-profile-docs-report")
        tm.ok(u.Cli.process_succeeded(latest.outcome))
        tm.that(
            latest.stdout,
            has=[str(second_run), "status=incomplete", "phase=fix status=not-reached"],
        )
        tm.that(latest.stdout, lacks=[str(first_run), str(completed_run)])
        tm.fail((second_run / "fix.txt").exists())
        tm.ok((first_run / "fix.pstats").is_file())

    def test_report_before_any_run_fails_loud(self, tmp_path: Path) -> None:
        """No elected run means no successful empty report."""
        root = u.Tests.create_docs_workspace(tmp_path)
        rendered = self._render(root, c.Infra.MakeProfile.STANDALONE)
        report = self._recipe(rendered, "_builtin-profile-docs-report").split("\n", 1)[
            1
        ]
        makefile = root / "profile-recipes.mk"
        makefile.write_text(
            f"PROJECT_ROOT := {root}\n"
            f"PROFILE_REPORTS_DIR := {root / '.reports/cprofile'}\n"
            f"report:\n{report}\n",
            encoding=c.DEFAULT_ENCODING,
        )
        result = tm.ok(
            u.Tests.run_isolated_make(["-f", str(makefile), "report"], cwd=root)
        )
        tm.fail(u.Cli.process_succeeded(result.outcome))
        tm.that(result.stderr, has="docs.latest")
