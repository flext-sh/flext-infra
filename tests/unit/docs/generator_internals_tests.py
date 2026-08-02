"""Public utility tests used by docs generation flows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.docs.generator import FlextInfraDocGenerator
from flext_tests import tm
from tests import m, u

if TYPE_CHECKING:
    from pathlib import Path


def test_anchorize_normalizes_headings() -> None:
    tm.that(u.Infra.anchorize("Hello World"), eq="hello-world")
    tm.that(u.Infra.anchorize("Test-Case"), eq="test-case")
    tm.that(u.Infra.anchorize(""), eq="")


def test_build_toc_lists_h2_and_h3_sections() -> None:
    toc = u.Infra.build_toc("# Main\n\n## Section 1\n\n### Subsection\n")

    tm.that(toc, has="<!-- TOC START -->")
    tm.that(toc, has="Section 1")
    tm.that(toc, has="Subsection")


def test_update_toc_replaces_existing_block() -> None:
    updated, changed = u.Infra.update_toc(
        "# Main\n\n<!-- TOC START -->\n- stale\n<!-- TOC END -->\n\n## Section\n"
    )

    tm.that(changed, eq=1)
    tm.that(updated, lacks="stale")
    tm.that(updated, has="Section")


def test_update_toc_keeps_generated_heading_before_managed_toc() -> None:
    """Generated comments never displace the required first level-one heading."""
    content = (
        "<!-- TOC START -->\n- stale\n<!-- TOC END -->\n\n"
        "<!-- AUTO-GENERATED -->\n\n"
        "# Generated\n\n"
        "## Section\n"
    )

    updated, changed = u.Infra.update_toc(content)

    tm.that(changed, eq=1)
    tm.that(updated.index("# Generated"), lt=updated.index("<!-- TOC START -->"))
    tm.that(updated, has="[Section](#section)")


def test_generated_markdown_is_toc_normalized_before_write(tmp_path: Path) -> None:
    generated = tmp_path / "generated.md"

    result = u.Infra.docs_write_if_needed(
        generated, "# Generated\n\n## Section\n", apply=True
    )

    tm.that(result.changed, eq=True)
    tm.that(generated.read_text(), has="<!-- TOC START -->")
    tm.that(generated.read_text(), has="[Section](#section)")


def test_generated_non_markdown_preserves_exact_content(tmp_path: Path) -> None:
    generated = tmp_path / "mkdocs.yml"
    content = "site_name: Generated\n"

    result = u.Infra.docs_write_if_needed(generated, content, apply=True)

    tm.that(result.changed, eq=True)
    tm.that(generated.read_text(), eq=content)


def test_generate_creates_selected_project_reports(tmp_path: Path) -> None:
    workspace = u.Tests.create_docs_workspace(
        tmp_path, project_names=("flext-a", "flext-b")
    )

    result = FlextInfraDocGenerator().generate(
        m.Infra.DocsGenerateRequest(
            workspace_root=workspace, projects=["flext-a"], apply=True
        )
    )

    tm.ok(result)
    tm.that([report.scope for report in result.value], eq=["root", "flext-a"])
