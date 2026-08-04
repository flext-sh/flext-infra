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
_RELEASE = _TEMPLATES / ".github" / "workflows" / "release.yml.j2"
_CI = _TEMPLATES / ".github" / "workflows" / "ci.yml.j2"


class TestsReviewTemplateContracts:
    """Lock the SSOT fixes for bootstrap pin, PROJECT selection, TestPyPI order."""

    def test_makefile_bootstrap_prefers_gitlink_oid(self) -> None:
        text = _MAKEFILE.read_text(encoding="utf-8")
        tm.that(text, has="FLEXT_INFRA_BOOTSTRAP_REF")
        tm.that(text, has='rev-parse "HEAD:{{ infra_repository.path.as_posix() }}"')
        tm.that(text, has="@$(FLEXT_INFRA_BOOTSTRAP_REF)")
        tm.that(text, lacks="@{{ infra_repository_branch }}")

    def test_makefile_deps_modernize_uses_selected_projects(self) -> None:
        text = _MAKEFILE.read_text(encoding="utf-8")
        tm.that(text, has='selected="$(strip $(SELECTED_PROJECTS))"')
        upgrade = text.split("_builtin_deps_upgrade:", 1)[1].split(
            "_builtin_build_artifacts:", 1
        )[0]
        tm.that(upgrade, lacks='selected="$(strip $(PROJECTS))"')

    def test_makefile_defines_attached_member_for_status(self) -> None:
        text = _MAKEFILE.read_text(encoding="utf-8")
        tm.that(
            text,
            has=(
                "ATTACHED_MEMBER := $(if $(filter workspace-member,"
                "$(MAKE_PROFILE)),$(PROJECT_ROOT),)"
            ),
        )

    def test_release_verifies_core_gitlink_after_setup(self) -> None:
        text = _RELEASE.read_text(encoding="utf-8")
        boot = text.index("Boot workspace")
        verify = text.index("Verify immutable flext-core gitlink")
        root_verify = text.index("Verify immutable canary root")
        tm.that(root_verify < boot, eq=True)
        tm.that(boot < verify, eq=True)
        pre = text[:boot]
        tm.that(pre, lacks="git -C flext-core rev-parse HEAD")

    def test_ci_upload_excludes_raw_report_logs(self) -> None:
        text = _CI.read_text(encoding="utf-8")
        upload = text.split("Upload reports on failure", 1)[1].split(
            "# End SECTION: ci job", 1
        )[0]
        tm.that(upload, has=".reports/**/junit.xml")
        tm.that(upload, has=".reports/**/coverage.xml")
        tm.that(".reports/**\n" not in upload.replace("junit.xml", "").replace("coverage.xml", "").replace("coverage.json", ""), eq=True)
