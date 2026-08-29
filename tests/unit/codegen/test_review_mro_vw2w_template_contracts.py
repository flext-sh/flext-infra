"""Template contracts for Bugbot/Security review fixes (mro-vw2w)."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

_TEMPLATES = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "flext_infra"
    / "templates"
    / "project"
    / "base"
)
_MAKEFILE = _TEMPLATES / "Makefile.j2"
_CI = _TEMPLATES / ".github" / "workflows" / "ci.yml.j2"
_DOCS = _TEMPLATES / ".github" / "workflows" / "docs.yml.j2"


class TestsReviewTemplateContracts:
    """Lock repository-neutral workflow and bootstrap contracts."""

    def test_makefile_bootstrap_uses_declared_remote_revision(self) -> None:
        text = _MAKEFILE.read_text(encoding="utf-8")
        tm.that(text, has="FLEXT_INFRA_BOOTSTRAP_REF")
        tm.that(text, has="@$(FLEXT_INFRA_BOOTSTRAP_REF)")
        tm.that(text, has="git+{{ infra_repository.url }}")
        tm.that(text, lacks=['rev-parse "HEAD:', "@latest", " @ file:"])

    def test_makefile_deps_modernize_uses_selected_projects(self) -> None:
        text = _MAKEFILE.read_text(encoding="utf-8")
        tm.that(text, has='selected="$(strip $(SELECTED_PROJECTS))"')
        upgrade = text.split("_builtin_deps_upgrade:", 1)[1].split(
            "_builtin_build_artifacts:", 1
        )[0]
        tm.that(upgrade, lacks='selected="$(strip $(PROJECTS))"')
        tm.that(upgrade, has="$(if $(strip $(DEPENDENCY)),,--rewrite-constraints)")

    def test_makefile_has_no_legacy_work_lifecycle(self) -> None:
        """Gas Town is the sole lane lifecycle owner."""
        text = _MAKEFILE.read_text(encoding="utf-8")
        tm.that(text, lacks=["_builtin_work_", "make work", "work start"])

    def test_ci_upload_excludes_raw_report_logs(self) -> None:
        text = _CI.read_text(encoding="utf-8")
        upload = text.split("Upload reports on failure", 1)[1].split(
            "# End SECTION: ci job", 1
        )[0]
        tm.that(upload, has=".reports/**/junit.xml")
        tm.that(upload, has=".reports/**/coverage.xml")
        tm.that(
            ".reports/**\n"
            not in upload
            .replace("junit.xml", "")
            .replace("coverage.xml", "")
            .replace("coverage.json", ""),
            eq=True,
        )

    def test_ci_dump_excludes_raw_pytest_logs(self) -> None:
        text = _CI.read_text(encoding="utf-8")
        dump = text.split("Dump reports on failure", 1)[1].split(
            "Upload reports on failure", 1
        )[0]
        tm.that(dump, lacks="pytest.log")
        tm.that(dump, has="junit.xml")
        tm.that(dump, has="coverage.xml")

    def test_ci_template_is_yamllint_safe_at_step_and_section_boundaries(self) -> None:
        """Generated CI must not create blank-line or comment-indent violations.

        Why (aihub-g8e1j): trim-after (`-%}`) on the loop-open tag ate the
        required loop-body indentation/newlines of the following literal
        text, producing invalid YAML on render (confirmed via yaml.safe_load
        ParserError on both ai-hub's and flext-infra's own dogfooded
        ci.yml). Trim-before (`{%-`) on loop-open/endfor removes the same
        blank source lines without touching body indentation.
        """
        text = _CI.read_text(encoding="utf-8")
        tm.that(text, has='{%- for step in make.workflow if "ci" in step.contexts %}')
        tm.that(text, has="{% endfor %}")
        tm.that(text, has="  # End SECTION: ci job")
        tm.that("    # End SECTION: ci job" not in text.splitlines(), eq=True)

    def test_docs_workflow_uses_public_cli_not_removed_make_verb(self) -> None:
        text = _DOCS.read_text(encoding="utf-8")
        tm.that(text, lacks="DOCS_PHASE=")
        tm.that(text, lacks="make docs")
        tm.that(text, has="python -m flext_infra docs audit")
        tm.that(text, has="python -m flext_infra docs generate")
        tm.that(text, has="python -m flext_infra docs validate")
        tm.that(text, has="python -m flext_infra docs build")

    def test_docs_pages_environment_avoids_static_schema_enum(self) -> None:
        text = _DOCS.read_text(encoding="utf-8")
        tm.that(text, has="name: {% raw %}${{ 'github-pages' }}{% endraw %}")
        tm.that(text, lacks="      name: github-pages")

    def test_docs_upload_excludes_raw_report_logs(self) -> None:
        text = _DOCS.read_text(encoding="utf-8")
        upload = text.split("Upload docs reports on failure", 1)[1].split("build:", 1)[
            0
        ]
        tm.that(upload, has="audit-summary.json")
        tm.that(upload, has="validate-summary.json")
        tm.that(upload, lacks="path: .reports/")
        tm.that(upload, lacks=".reports/workspace/docs/")
        tm.that(upload, lacks="pytest.log")
