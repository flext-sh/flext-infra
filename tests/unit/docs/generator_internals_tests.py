"""Public utility tests used by docs generation flows."""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraDocGenerator
from tests import u


def test_anchorize_normalizes_headings() -> None:
    assert u.Infra.anchorize("Hello World") == "hello-world"
    assert u.Infra.anchorize("Test-Case") == "test-case"
    assert u.Infra.anchorize("") == ""


def test_build_toc_lists_h2_and_h3_sections() -> None:
    toc = u.Infra.build_toc("# Main\n\n## Section 1\n\n### Subsection\n")

    assert "<!-- TOC START -->" in toc
    assert "Section 1" in toc
    assert "Subsection" in toc


def test_update_toc_replaces_existing_block() -> None:
    updated, changed = u.Infra.update_toc(
        "# Main\n\n<!-- TOC START -->\n- stale\n<!-- TOC END -->\n\n## Section\n",
    )

    assert changed == 1
    assert "stale" not in updated
    assert "Section" in updated


def test_generate_creates_selected_project_reports(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(
        tmp_path,
        project_names=("flext-a", "flext-b"),
    )

    result = FlextInfraDocGenerator().generate(
        workspace,
        projects=["flext-a"],
        apply=True,
    )

    assert result.is_success
    assert [report.scope for report in result.value] == ["root", "flext-a"]
