"""Codegen utilities composition for the infrastructure namespace."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import u
from flext_core import r

from flext_infra.constants import c
from flext_infra.models import m

# mro-i6nq.10: Keep Ruff normalization behind one typed utilities owner.

if TYPE_CHECKING:
    from flext_core import p

    from flext_infra.typings import t


class FlextInfraUtilitiesCodegen:
    """Compose all codegen utility concerns for ``u.Infra``."""

    if TYPE_CHECKING:

        @staticmethod
        def project_root(file_path: Path) -> Path | None: ...

    @classmethod
    def normalize_python_source(
        cls,
        source: str,
        *,
        filename: t.Cli.TextPath,
    ) -> p.Result[str]:
        """Return Ruff-fixed and formatted source without writing ``filename``."""
        resolved_path = Path(filename).resolve()
        # mro-j47u: tool subprocesses run from the project root so package files
        # such as collections.py can never shadow Python's standard library.
        cwd = cls.project_root(resolved_path)
        if cwd is None:
            return r[str].fail(
                f"project root not found for generated source: {resolved_path}",
            )
        # mro-o6h5 (agent: kimi) — ruff via running interpreter (venv SSOT);
        # bare "ruff" breaks when .venv/bin is not on PATH (CI docs audit).
        checked = u.Cli.run_raw(
            [
                sys.executable,
                "-m",
                c.Infra.RUFF,
                "check",
                "--fix",
                "--no-cache",
                "--color",
                "never",
                "--stdin-filename",
                str(resolved_path),
                "-",
            ],
            cwd=cwd,
            timeout=c.Infra.TIMEOUT_SHORT,
            input_data=source.encode(c.Infra.ENCODING_DEFAULT),
        )
        if checked.failure:
            return r[str].fail(checked.error or f"ruff check failed: {resolved_path}")
        checked_output = checked.value
        if checked_output.exit_code != 0:
            detail = checked_output.stderr.strip() or "no diagnostic output"
            return r[str].fail(
                f"ruff check failed ({checked_output.exit_code}) for "
                f"{resolved_path}: {detail}",
            )
        formatted = u.Cli.run_raw(
            [
                sys.executable,
                "-m",
                c.Infra.RUFF,
                "format",
                "--no-cache",
                "--color",
                "never",
                "--stdin-filename",
                str(resolved_path),
                "-",
            ],
            cwd=cwd,
            timeout=c.Infra.TIMEOUT_SHORT,
            input_data=checked_output.stdout.encode(c.Infra.ENCODING_DEFAULT),
        )
        if formatted.failure:
            return r[str].fail(
                formatted.error or f"ruff format failed: {resolved_path}",
            )
        formatted_output = formatted.value
        if formatted_output.exit_code != 0:
            detail = formatted_output.stderr.strip() or "no diagnostic output"
            return r[str].fail(
                f"ruff format failed ({formatted_output.exit_code}) for "
                f"{resolved_path}: {detail}",
            )
        normalized_source = formatted_output.stdout
        if normalized_source and not normalized_source.endswith("\n"):
            normalized_source = f"{normalized_source}\n"
        return r[str].ok(normalized_source)

    @staticmethod
    def generate_module_skeleton(
        *,
        class_name: str,
        base_class: str,
        docstring: str,
    ) -> str:
        """Render one module skeleton through the cli template engine (ADR-005).

        The body lives in ``templates/module_skeleton.py.j2``; this method only
        builds the context (base-import block) and renders fail-closed via
        ``u.Cli.template_render``. A render failure is a real incident and
        surfaces via ``unwrap`` (no silent fallback).
        """
        if base_class.startswith("FlextTests"):
            base_import_block = f"from flext_tests import {base_class}\n\n"
        elif base_class.startswith("Flext"):
            base_import_block = f"from flext_core import {base_class}\n\n"
        else:
            base_import_block = ""
        template_path = (
            Path(__file__).resolve().parent.parent
            / "templates"
            / c.Infra.TEMPLATE_MODULE_SKELETON
        )
        # NOTE (multi-agent, mro-wkii.17 / agent: uv_overlay_owner): preserve
        # the exact validated model identity across the template boundary.
        context = m.Infra.ModuleSkeletonRenderContext(
            class_name=class_name,
            base_class=base_class,
            base_import_block=base_import_block,
            docstring=docstring,
        )
        rendered: p.Result[str] = u.Cli.template_render(
            template_path,
            context,
        )
        return rendered.unwrap()

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
