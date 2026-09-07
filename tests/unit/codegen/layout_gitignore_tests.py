"""Tests for layout gitignore, tracked-file moves, and the canonical render."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, config
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm
from tests import t, u
from tests.unit.codegen.layout_fixture import (
    archive_root,
    build_loose_project,
    layout_engine,
)


def test_apply_adds_gitignore_entries_exactly_once(tmp_path: Path) -> None:
    """Gitignore additions from the SSOT are appended once across applies."""
    project = build_loose_project(tmp_path, name="flext-cli")
    (project / "settings.json").write_text("{}\n", encoding="utf-8")
    engine = layout_engine(tmp_path, apply_changes=True)

    first = engine.execute()
    tm.ok(first)
    second = engine.execute()
    tm.ok(second)

    gitignore = (project / c.Infra.GITIGNORE).read_text(encoding="utf-8")
    # Why: count exact ENTRIES, never substrings. The SSOT also carries
    # negations such as !.vscode/settings.json, so a substring count reports
    # two occurrences for a file that was appended exactly once.
    entries = gitignore.splitlines()
    tm.that(entries.count("settings.json"), eq=1)
    tm.that(entries.count(f"{archive_root()}/"), eq=1)
    tm.that(
        (project / archive_root() / project.name / "settings.json").is_file(), eq=True
    )


def test_apply_uses_git_mv_for_tracked_files(tmp_path: Path) -> None:
    """Tracked sources move through git so history follows the rename."""
    project = build_loose_project(tmp_path)
    u.Tests.initialize_git_repo(project)
    engine = layout_engine(tmp_path, apply_changes=True)

    result = engine.execute()

    tm.ok(result)
    tracked = u.Cli.capture([c.Infra.GIT, "ls-files"], cwd=project)
    tm.ok(tracked)
    tracked_names = set(tracked.value.split())
    tm.that("docs/guides/intro.md" in tracked_names, eq=True)
    tm.that("guides/intro.md" in tracked_names, eq=False)
    tm.that(f"{archive_root()}/{project.name}/output.log" in tracked_names, eq=False)


def test_managed_gitignore_render_includes_layout_additions() -> None:
    """The canonical gitignore render owns the layout SSOT additions."""
    rendered = FlextInfraCodegenConform.render_project_gitignore(
        config.Infra.codegen,
        profile=c.Infra.MakeProfile.STANDALONE,
        project_name="flext-cli",
    )

    tm.ok(rendered)
    tm.that(rendered.value, has="settings.json")
    tm.that(rendered.value, has=f"{archive_root()}/")


__all__: t.StrSequence = []
