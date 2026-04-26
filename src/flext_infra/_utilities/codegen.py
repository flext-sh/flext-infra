"""Codegen utilities composition for the infrastructure namespace."""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path

from flext_cli import u
from flext_infra import c


class FlextInfraUtilitiesCodegen:
    """Compose all codegen utility concerns for ``u.Infra``."""

    @staticmethod
    def run_ruff_fix(path: Path, *, quiet: bool = False) -> bool:
        """Run Ruff fix + format for one file path; return success status."""
        cwd = path.parent if path.suffix else path
        check_result = u.Cli.capture(
            [c.Infra.RUFF, "check", "--fix", str(path)],
            cwd=cwd,
        )
        if check_result.failure:
            if not quiet:
                u.Cli.error(check_result.error or f"ruff check --fix failed: {path}")
            return False
        format_result = u.Cli.capture(
            [c.Infra.RUFF, "format", str(path)],
            cwd=cwd,
        )
        if format_result.failure and not quiet:
            u.Cli.error(format_result.error or f"ruff format failed: {path}")
        return not format_result.failure

    @staticmethod
    def generate_module_skeleton(
        *, class_name: str, base_class: str, docstring: str
    ) -> str:
        """Generate one minimal module skeleton used by codegen scaffolding."""
        return (
            f'"""{docstring}"""\n\n'
            "from __future__ import annotations\n\n"
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
        source_lines: Sequence[str],
    ) -> Sequence[tuple[str, str, str, str, int]]:
        """Parse ``NAME: Final[...] = VALUE`` definitions with class-path context."""
        class_stack: MutableSequence[tuple[str, int]] = []
        parsed: MutableSequence[tuple[str, str, str, str, int]] = []
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
        class_stack: MutableSequence[tuple[str, int]],
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
