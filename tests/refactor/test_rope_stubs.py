"""Wave 0 stub tests confirming rope is importable."""

from __future__ import annotations

from pathlib import Path

from flext_infra import u


def test_rope_project_wrapper(tmp_path: Path) -> None:
    """Confirm the Rope project wrapper creates a live project."""
    project = u.Infra.init_rope_project(tmp_path, project_prefix="__never__")
    try:
        assert project is not None
    finally:
        project.close()


def test_rope_module_syntax_error_wrapper() -> None:
    """Confirm the Rope exception wrapper resolves a concrete exception type."""
    assert u.Infra.module_syntax_error_type() is not None


def test_rope_find_occurrences_wrapper(tmp_path: Path) -> None:
    """Confirm occurrence search works through the utility wrapper."""
    package_dir = tmp_path / "demo"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    target = package_dir / "mod.py"
    target.write_text(
        "class Demo:\n    pass\n\nvalue = Demo()\n",
        encoding="utf-8",
    )
    project = u.Infra.init_rope_project(tmp_path, project_prefix="__never__")
    try:
        resource = u.Infra.get_resource_from_path(project, target)
        assert resource is not None
        offset = u.Infra.find_definition_offset(project, resource, "Demo")
        assert offset is not None
        hits = u.Infra.find_occurrences(project, resource, offset)
        assert hits
    finally:
        project.close()
