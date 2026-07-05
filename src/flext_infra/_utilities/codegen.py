"""Codegen utilities composition for the infrastructure namespace."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_cli import u
from flext_infra.constants import c

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra.protocols import p
    from flext_infra.typings import t


class FlextInfraUtilitiesCodegen:
    """Compose all codegen utility concerns for ``u.Infra``."""

    @staticmethod
    def run_ruff_fix(path: Path, *, quiet: bool = False) -> p.Result[bool]:
        """Run Ruff post-processing for one generated file path.

        Generated Python modules use ``ruff check --fix`` plus ``ruff format``.
        ``quiet=True`` suppresses the CLI error log; the failure still surfaces
        via ``r``.
        """
        cwd = path.parent if path.suffix else path

        def _step(args: list[str], default_msg: str) -> p.Result[str]:
            return (
                u.Cli
                .capture(args, cwd=cwd)
                .map_error(
                    lambda e: e or default_msg,
                )
                .tap_error(lambda e: None if quiet else u.Cli.error(e))
            )

        return (
            _step(
                [c.Infra.RUFF, "check", "--fix", str(path)],
                f"ruff check --fix failed: {path}",
            )
            .flat_map(
                lambda _: _step(
                    [c.Infra.RUFF, "format", str(path)],
                    f"ruff format failed: {path}",
                ),
            )
            .map(lambda _: True)
        )

    @staticmethod
    def generate_module_skeleton(
        *,
        class_name: str,
        base_class: str,
        docstring: str,
    ) -> str:
        """Generate one minimal module skeleton used by codegen scaffolding."""
        if base_class.startswith("FlextTests"):
            base_import = f"from flext_tests import {base_class}\n\n"
        elif base_class.startswith("Flext"):
            base_import = f"from flext_core import {base_class}\n\n"
        else:
            base_import = ""
        return (
            f'"""{docstring}"""\n\n'
            "from __future__ import annotations\n\n"
            f"{base_import}"
            f"class {class_name}({base_class}):\n"
            f'    """{docstring}"""\n'
            "\n"
            "\n"
            '__all__: list[str] = ["'
            f"{class_name}"
            '"]\n'
        )

    @staticmethod
    def dir_has_py_files(pkg_dir: Path) -> bool:
        """Return whether a package directory contains canonical Python files."""
        if not pkg_dir.is_dir():
            return False
        return any(
            child.is_file() and child.suffix == ".py" for child in pkg_dir.iterdir()
        )

    @staticmethod
    def parse_final_constant_definitions(
        source_lines: t.SequenceOf[str],
    ) -> t.SequenceOf[tuple[str, str, str, str, int]]:
        """Parse ``NAME: Final[...] = VALUE`` definitions with class-path context."""
        class_stack: t.MutableSequenceOf[tuple[str, int]] = []
        parsed: t.MutableSequenceOf[tuple[str, str, str, str, int]] = []
        for line_number, line in enumerate(source_lines, 1):
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            FlextInfraUtilitiesCodegen.update_class_stack(
                class_stack,
                stripped,
                indent,
            )
            match = c.Infra.DETECTION_FINAL_DECL_RE.match(line)
            if match is None:
                continue
            parsed.append((
                match.group("name"),
                match.group("ann"),
                match.group("value").strip(),
                ".".join(name for name, _ in class_stack),
                line_number,
            ))
        return tuple(parsed)

    @staticmethod
    def update_class_stack(
        class_stack: t.MutableSequenceOf[tuple[str, int]],
        stripped_line: str,
        indent: int,
    ) -> None:
        """Keep class-path stack in sync while iterating constant source lines."""
        class_match = (
            c.Infra.DETECTION_CLASS_DECL_RE.match(stripped_line)
            if stripped_line.startswith("class ") and stripped_line.endswith(":")
            else None
        )
        if class_match is not None:
            while class_stack and class_stack[-1][1] >= indent:
                class_stack.pop()
            class_stack.append((class_match.group(1), indent))
            return
        while class_stack and indent <= class_stack[-1][1]:
            class_stack.pop()


__all__: list[str] = ["FlextInfraUtilitiesCodegen"]
