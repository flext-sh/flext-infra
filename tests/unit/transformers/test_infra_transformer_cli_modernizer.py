"""Unit tests for the CLI modernizer transformer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.transformers.cli_modernizer import FlextInfraRefactorCliModernizer

if TYPE_CHECKING:
    from collections.abc import Sequence


def _transform(source: str) -> tuple[str, Sequence[str]]:
    """Apply the CLI modernizer to source text."""
    transformer = FlextInfraRefactorCliModernizer()
    result: tuple[str, Sequence[str]] = transformer.apply_to_source(source)
    return result


class TestsFlextInfraTransformersCliModernizer:
    """Behavior contract for FlextInfraRefactorCliModernizer."""

    def test_import_typer_removed(self) -> None:
        source = "import typer\n"
        code, changes = _transform(source)
        assert "import typer" not in code
        assert changes

    def test_from_click_import_command_removed(self) -> None:
        source = "from click import command\n"
        code, changes = _transform(source)
        assert "from click import command" not in code
        assert changes

    def test_print_replaced_when_cli_imported(self) -> None:
        source = 'from flext_cli import cli\n\nprint("hi")\n'
        code, changes = _transform(source)
        assert 'cli.display_text("hi")' in code
        assert "print(" not in code
        assert changes

    def test_fstring_print_replaced_when_cli_imported(self) -> None:
        source = 'from flext_cli import cli\n\nprint(f"hi {name}")\n'
        code, changes = _transform(source)
        assert 'cli.display_text(f"hi {name}")' in code
        assert "print(" not in code
        assert changes

    def test_print_unchanged_without_cli_import(self) -> None:
        source = 'print("hi")\n'
        code, changes = _transform(source)
        assert code == source
        assert not changes

    def test_import_argparse_removed(self) -> None:
        source = "import argparse\n"
        code, changes = _transform(source)
        assert "import argparse" not in code
        assert changes

    def test_unchanged_source_returns_empty_changes(self) -> None:
        source = "x = 1\n"
        code, changes = _transform(source)
        assert code == source
        assert changes == []

    def test_manual_conversion_noted_for_typer_typer(self) -> None:
        source = "import typer\n\napp = typer.Typer()\n"
        code, changes = _transform(source)
        assert "import typer" not in code
        assert "typer.Typer()" in code
        assert any("Manual conversion required" in change for change in changes)

    def test_cli_alias_honored_for_print_rewrite(self) -> None:
        source = 'from flext_cli import cli as c\n\nprint("hi")\n'
        code, changes = _transform(source)
        assert 'c.display_text("hi")' in code
        assert "print(" not in code
        assert changes
