"""Public utility tests used by docs fixing flows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.docs.fixer import FlextInfraDocFixer
from flext_tests import tm
from tests import u

if TYPE_CHECKING:
    from pathlib import Path


def test_docs_maybe_fix_link_adds_md_suffix_when_target_exists(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    md_file = docs_dir / "README.md"
    md_file.write_text("# Docs\n", encoding="utf-8")
    (docs_dir / "guide.md").write_text("# Guide\n", encoding="utf-8")

    fixed = u.Infra.docs_maybe_fix_link(md_file, "guide")

    tm.that(fixed, eq="guide.md")


def test_anchorize_and_build_toc_are_public_helpers() -> None:
    tm.that(u.Infra.anchorize("Hello World"), eq="hello-world")
    tm.that(u.Infra.build_toc("# Main\n\nNo sections here.\n"), has="No sections found")


def test_fix_keeps_closing_fence_on_its_own_line(tmp_path: Path) -> None:
    workspace = u.Tests.create_docs_workspace(tmp_path, include_fixable_link=True)
    sample = workspace / "docs/fenced.md"
    sample.write_text(
        "# Fenced\n\n"
        "## Sample\n\n"
        "```python\n"
        "import os\n"
        "import sys\n\n"
        "print(sys.version)\n"
        "```\n\n"
        "## After The Block\n",
        encoding="utf-8",
    )

    result = FlextInfraDocFixer().fix(workspace, apply=True)

    tm.ok(result)
    fixed = sample.read_text(encoding="utf-8")
    tm.that(fixed, lacks=")```")
    tm.that(fixed, has="\n```\n")
    tm.that(fixed, has="## After The Block")


def test_fix_updates_docs_readme_when_apply_is_enabled(tmp_path: Path) -> None:
    workspace = u.Tests.create_docs_workspace(tmp_path, include_fixable_link=True)

    result = FlextInfraDocFixer().fix(workspace, apply=True)

    tm.ok(result)
    tm.that((workspace / "docs/README.md").read_text(), has="guides/setup.md")
