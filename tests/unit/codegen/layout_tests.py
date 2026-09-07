"""Tests for the declarative project-layout engine (flext-0wuz, epic flext-hzox)."""

from __future__ import annotations

from pathlib import Path

from flext_infra import m
from flext_infra.gates.layout import FlextInfraLayoutGate
from flext_tests import tm
from tests import t, u
from tests.unit.codegen.layout_fixture import (
    archive_root,
    build_loose_project,
    layout_engine,
)


def test_check_reports_move_archive_review_and_gitignore(tmp_path: Path) -> None:
    """Check mode classifies every loose root entry without writing."""
    project = build_loose_project(tmp_path)
    engine = layout_engine(tmp_path)

    report = engine.check_project(project)

    by_path = {finding.path: finding for finding in report.findings}
    tm.that(by_path["guides"].rule, eq="move")
    tm.that(by_path["guides"].target, eq="docs/guides")
    tm.that(by_path["index.md"].rule, eq="move")
    tm.that(by_path["output.log"].rule, eq="archive")
    tm.that(
        by_path["output.log"].target, eq=f"{archive_root()}/{project.name}/output.log"
    )
    tm.that(by_path["loose.txt"].rule, eq="review")
    gitignore = [finding for finding in report.findings if finding.rule == "gitignore"]
    tm.that(bool(gitignore), eq=True)
    tm.that(gitignore[0].target, eq=f"{archive_root()}/")


def test_check_execute_passes_while_severity_is_warning(tmp_path: Path) -> None:
    """CLI check posture is report-only while the SSOT severity is warning."""
    build_loose_project(tmp_path)
    engine = layout_engine(tmp_path)

    result = engine.execute()

    tm.ok(result)
    tm.that(result.value, has="move guides -> docs/guides")


def test_apply_moves_archives_and_converges_idempotently(tmp_path: Path) -> None:
    """Apply reorganizes once; a second apply performs zero operations."""
    project = build_loose_project(tmp_path)
    engine = layout_engine(tmp_path, apply_changes=True)

    first = engine.execute()

    tm.ok(first)
    tm.that((project / "docs" / "guides" / "intro.md").is_file(), eq=True)
    tm.that((project / "docs" / "index.md").is_file(), eq=True)
    archived = project / archive_root() / project.name / "output.log"
    tm.that(archived.is_file(), eq=True)
    tm.that(archived.read_text(encoding="utf-8"), eq="log-line\n")
    tm.that((project / "guides").exists(), eq=False)
    tm.that((project / "output.log").exists(), eq=False)
    tm.that((project / "loose.txt").is_file(), eq=True)
    second = engine.execute()
    tm.ok(second)
    tm.that(second.value, has="0 applied")
    residual = engine.check_project(project)
    tm.that(len(residual.actionable), eq=0)
    tm.that([finding.rule for finding in residual.findings], eq=["review"])


def test_apply_docs_collision_keeps_target_and_archives_source(tmp_path: Path) -> None:
    """Different-content collisions preserve both sides (archive-not-delete)."""
    project = build_loose_project(tmp_path)
    existing = project / "docs" / "guides"
    existing.mkdir(parents=True)
    (existing / "intro.md").write_text("canonical\n", encoding="utf-8")
    engine = layout_engine(tmp_path, apply_changes=True)

    result = engine.execute()

    tm.ok(result)
    tm.that((existing / "intro.md").read_text(encoding="utf-8"), eq="canonical\n")
    archived = project / archive_root() / project.name / "guides" / "intro.md"
    tm.that(archived.is_file(), eq=True)
    tm.that(archived.read_text(encoding="utf-8"), eq="intro\n")
    tm.that((project / "guides").exists(), eq=False)


def test_apply_override_move_then_archives_emptied_dir(tmp_path: Path) -> None:
    """Override moves run before the emptied directory is archived."""
    project = tmp_path / "flext-dbt-ldif"
    profiles = project / "profiles"
    package_dir = project / "src" / "flext_dbt_ldif"
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    profiles.mkdir(parents=True)
    (project / "pyproject.toml").write_text(
        "[project]\nname='flext-dbt-ldif'\nversion='0.1.0'\n", encoding="utf-8"
    )
    (profiles / "profiles.yml").write_text("profile: 1\n", encoding="utf-8")
    u.Tests.declare_workspace_projects(tmp_path, (project.name,))
    engine = layout_engine(tmp_path, apply_changes=True)

    result = engine.execute()

    tm.ok(result)
    tm.that((project / "profiles.yml").is_file(), eq=True)
    tm.that((project / "profiles").exists(), eq=False)
    tm.that((project / archive_root() / project.name / "profiles").is_dir(), eq=True)


def test_gate_reports_violations_but_passes_on_warning(tmp_path: Path) -> None:
    """Gate posture follows the SSOT severity: warning reports, never fails."""
    project = build_loose_project(tmp_path)
    gate = FlextInfraLayoutGate(tmp_path)
    ctx = m.Infra.GateContext(
        repository_root=tmp_path, reports_dir=tmp_path / ".reports"
    )

    execution = gate.check(project, ctx)

    tm.that(execution.result.passed, eq=True)
    tm.that(bool(execution.issues), eq=True)
    tm.that(all(issue.severity == "WARNING" for issue in execution.issues), eq=True)


__all__: t.StrSequence = []


def test_keep_root_files_override(tmp_path: Path) -> None:
    """Declared keep_root_files stay at root without review findings."""
    project = tmp_path / "ai-hub"
    package_dir = project / "src" / "ai_hub"
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (project / "pyproject.toml").write_text(
        "[project]\nname='ai-hub'\nversion='0.1.0'\n", encoding="utf-8"
    )
    (project / "README.md").write_text("# ai-hub\n", encoding="utf-8")
    (project / "UNIVERSAL_CORE.md").write_text("core\n", encoding="utf-8")
    (project / "ECOSYSTEM.md").write_text("eco\n", encoding="utf-8")
    engine = layout_engine(tmp_path)

    report = engine.check_project(project)

    paths = {finding.path for finding in report.findings}
    tm.that("UNIVERSAL_CORE.md" in paths, eq=False)
    tm.that("ECOSYSTEM.md" in paths, eq=False)


def test_special_and_reference_root_dirs_skipped(tmp_path: Path) -> None:
    """data/ is skipped; external-docs/ is allowed as reference corpus."""
    project = build_loose_project(tmp_path)
    (project / "data").mkdir()
    (project / "data" / "proposal").mkdir()
    (project / "external-docs").mkdir()
    (project / "external-docs" / "note.md").write_text("ext\n", encoding="utf-8")
    engine = layout_engine(tmp_path)

    report = engine.check_project(project)

    paths = {finding.path for finding in report.findings}
    tm.that("data" in paths, eq=False)
    tm.that("external-docs" in paths, eq=False)


def test_subprojects_are_canonical_root_entries(tmp_path: Path) -> None:
    """A workspace root accepts only repository directories declared by topology."""
    declared_name = "flext-declared"
    undeclared_name = "flext-undeclared"
    (tmp_path / declared_name).mkdir()
    (tmp_path / undeclared_name).mkdir()
    u.Tests.declare_workspace_projects(tmp_path, (declared_name,))
    engine = layout_engine(tmp_path)

    report = engine.check_project(tmp_path)

    findings = {finding.path: finding for finding in report.findings}
    tm.that(declared_name in findings, eq=False)
    tm.that(findings[undeclared_name].rule, eq="review")


def test_duplicate_root_md_archives_when_docs_copy_exists(tmp_path: Path) -> None:
    """Root move_docs_files collide with docs/ -> archive root, keep docs."""
    project = build_loose_project(tmp_path)
    docs = project / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "index.md").write_text("canonical-index\n", encoding="utf-8")
    engine = layout_engine(tmp_path, apply_changes=True)

    result = engine.execute()

    tm.ok(result)
    tm.that((docs / "index.md").read_text(encoding="utf-8"), eq="canonical-index\n")
    archived = project / archive_root() / project.name / "index.md"
    tm.that(archived.is_file(), eq=True)
    tm.that(archived.read_text(encoding="utf-8"), eq="index\n")
    tm.that((project / "index.md").exists(), eq=False)
