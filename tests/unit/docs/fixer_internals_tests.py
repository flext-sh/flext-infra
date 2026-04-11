"""Public utility tests used by docs fixing flows."""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraDocFixer
from tests import u


def test_docs_maybe_fix_link_adds_md_suffix_when_target_exists(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    md_file = docs_dir / "README.md"
    md_file.write_text("# Docs\n", encoding="utf-8")
    (docs_dir / "guide.md").write_text("# Guide\n", encoding="utf-8")

    fixed = u.Infra.docs_maybe_fix_link(md_file, "guide")

    assert fixed == "guide.md"


def test_anchorize_and_build_toc_are_public_helpers() -> None:
    assert u.Infra.anchorize("Hello World") == "hello-world"
    assert "No sections found" in u.Infra.build_toc("# Main\n\nNo sections here.\n")


def test_fix_updates_docs_readme_when_apply_is_enabled(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(
        tmp_path,
        include_fixable_link=True,
    )

    result = FlextInfraDocFixer().fix(workspace, apply=True)

    assert result.success
    assert "guides/setup.md" in (workspace / "docs/README.md").read_text()
