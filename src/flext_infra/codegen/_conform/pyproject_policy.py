"""Pyproject provenance and custom Make policy projections.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path

from flext_infra import c, config, m, p, r, t
from flext_infra.__version__ import __version__
from flext_infra.codegen._conform.file_plans import FlextInfraCodegenConformFilePlans


class FlextInfraCodegenConformPyprojectPolicy(FlextInfraCodegenConformFilePlans):
    """Pyproject provenance and custom Make policy projections."""

    @classmethod
    def rendered_by_stamp(cls) -> str:
        """Return the render-provenance line for the running generator.

        Returns:
            The provenance marker followed by the generator version.

        """
        return f"{c.Infra.RENDERED_BY_MARKER}{__version__}"

    @staticmethod
    def _scaffold_python_dirs(
        entries: t.SequenceOf[p.Infra.TemplateEntrySpec],
        profile: c.Infra.MakeProfile,
        *,
        package: bool = True,
    ) -> t.StrSequence:
        """Return Python roots the selected scaffold manifest actually creates.

        Returns:
            Python roots the selected scaffold manifest actually creates.

        """
        generated_roots = {
            Path(entry.destination).parts[0]
            for entry in entries
            if profile in entry.profiles
            and entry.source is not None
            and Path(entry.destination).parts
        }
        source_dir = config.Infra.tooling.tools.pyright.path_rules.source_dir
        return tuple(
            directory
            for directory in config.Infra.tooling.tools.pyright.path_rules.env_dirs
            if directory in generated_roots and (package or directory != source_dir)
        )

    @classmethod
    def validate_custom_make(
        cls,
        content: str,
        policy: m.Infra.CustomHandlerPolicy,
    ) -> p.Result[bool]:
        """Reject public targets, aliases, includes, and toolchain declarations.

        Returns:
            The resulting custom-handler validation.

        """
        target_re = re.compile(policy.target_pattern)
        logical_lines = cls._logical_make_lines(content, policy)
        if logical_lines.failure:
            return r[bool].from_failure(logical_lines)
        in_define = False
        for line_number, raw_line in logical_lines.value:
            if in_define:
                in_define = not raw_line.startswith("endef")
                continue
            if raw_line.startswith("define "):
                if not policy.allow_toolchain_declarations:
                    return r[bool].fail(
                        f"{policy.filename} line {line_number} "
                        "declares a macro, which this profile forbids",
                    )
                in_define = True
                continue
            if cls._skippable_make_line(raw_line):
                continue
            verdict = cls._judge_make_line(target_re, policy, line_number, raw_line)
            if verdict is not None:
                return verdict
        return r[bool].ok(value=True)

    @staticmethod
    def _judge_make_line(
        target_re: re.Pattern[str],
        policy: m.Infra.CustomHandlerPolicy,
        line_number: int,
        raw_line: str,
    ) -> p.Result[bool] | None:
        """Judge one logical make line against the custom-handler policy.

        Returns:
            A validation failure or None when the line is accepted.

        """
        phony_names = (
            raw_line.partition(":")[2].strip().split()
            if raw_line.startswith(".PHONY:")
            else None
        )
        target = raw_line.partition(":")[0].strip() if ":" in raw_line else ""
        banned = target in {"pre-commit", "_custom-pre-commit"} or (
            phony_names is not None
            and bool({"pre-commit", "_custom-pre-commit"} & set(phony_names))
        )
        if banned:
            return r[bool].fail("mandatory approval cannot be a custom target")
        if phony_names is not None:
            if phony_names and all(target_re.fullmatch(name) for name in phony_names):
                return None
        elif target and target_re.fullmatch(target):
            return None
        if c.Infra.MAKE_ASSIGNMENT_RE.match(
            raw_line,
        ) or c.Infra.MAKE_DIRECTIVE_RE.match(raw_line):
            return (
                None
                if policy.allow_toolchain_declarations
                else r[bool].fail(
                    f"{policy.filename} line {line_number} "
                    "declares a variable, which this profile forbids",
                )
            )
        if target and policy.allow_public_targets:
            return None
        return r[bool].fail(
            f"{policy.filename} line {line_number} is not a private custom handler",
        )

    @staticmethod
    def _skippable_make_line(raw_line: str) -> bool:
        """Whether a logical make line carries no handler-decision weight.

        Returns:
            Whether this line needs no handler validation.

        """
        if not raw_line or raw_line.lstrip().startswith("#"):
            return True
        if raw_line[0].isspace():
            return True
        return bool(c.Infra.MAKE_CONDITIONAL_RE.match(raw_line))

    @staticmethod
    def _logical_make_lines(
        content: str,
        policy: m.Infra.CustomHandlerPolicy,
    ) -> p.Result[tuple[t.Pair[int, str]], ...]:
        """Collapse backslash continuations into reportable logical lines.

        Returns:
            The logical lines and their first physical line numbers.

        """
        result_type = (r[tuple[t.Pair[int, str]], ...],)
        logical_lines: list[t.Pair[int, str]] = []
        pending_line: str | None = None
        pending_number: int = 0
        for line_number, raw_line in enumerate(content.splitlines(), start=1):
            if (
                raw_line
                and not raw_line[0].isspace()
                and raw_line.rstrip().endswith("\\")
            ):
                trimmed = raw_line.rstrip()[:-1].rstrip()
                if pending_line is None:
                    pending_line = trimmed
                    pending_number = line_number
                else:
                    pending_line += " " + trimmed
                continue
            logical_line = raw_line
            logical_number = line_number
            if pending_line is not None:
                joined = pending_line + " " + raw_line.strip()
                if joined.rstrip().endswith("\\"):
                    pending_line = joined.rstrip()[:-1].rstrip()
                    continue
                logical_line = joined
                logical_number = pending_number
                pending_line = None
            logical_lines.append((logical_number, logical_line))
        if pending_line is not None:
            if pending_line.startswith(".PHONY:"):
                return result_type.fail(
                    f"{policy.filename} has an unterminated .PHONY continuation",
                )
            logical_lines.append((pending_number, pending_line))
        return result_type.ok(tuple(logical_lines))


__all__: list[str] = ["FlextInfraCodegenConformPyprojectPolicy"]
