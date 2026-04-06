"""Formatting utilities for infrastructure code operations.

Provides canonical ruff formatting as static methods.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import contextlib
from collections.abc import MutableSequence
from pathlib import Path

from flext_cli import u
from flext_core import r
from flext_infra import c, t


class FlextInfraUtilitiesFormatting:
    """Static formatting utilities for code normalization.

    All methods are ``@staticmethod`` — no instantiation required.
    Exposed via ``u.Infra.run_ruff_fix()`` through MRO.
    """

    @staticmethod
    def run_ruff_fix(
        path: Path,
        *,
        include_format: bool = True,
        quiet: bool = False,
    ) -> None:
        """Run ruff check --fix and optionally ruff format on a file.

        Args:
            path: Path to the file to fix.
            include_format: When True, also run ``ruff format`` after fixing.
            quiet: When True, add ``--quiet`` flag and suppress FileNotFoundError.

        """
        if not path.exists():
            return

        use_quiet = quiet or path.name == c.Infra.Files.INIT_PY
        check_cmd = [
            c.Infra.RUFF,
            c.Infra.CHECK,
            "--fix",
        ]
        if use_quiet:
            check_cmd.append("--quiet")
        check_cmd.append(str(path))

        def _run_checked(cmd: t.StrSequence) -> r[bool]:
            return u.Cli.run_checked(cmd)

        def _require_success(result: r[bool]) -> None:
            if result.is_failure:
                raise ValueError(result.error or "ruff post-process failed")

        if use_quiet:
            with contextlib.suppress(FileNotFoundError):
                _run_checked(check_cmd)
        else:
            _run_checked(check_cmd)

        if include_format:
            format_cmd = [
                c.Infra.RUFF,
                c.Infra.FORMAT,
            ]
            if use_quiet:
                format_cmd.append("--quiet")
            format_cmd.append(str(path))
            _require_success(_run_checked(format_cmd))

    @staticmethod
    def class_name_to_module(class_name: str) -> str:
        """Convert a facade class name like ``FlextMeltanoModels`` to its module.

        E.g. ``FlextMeltanoModels`` → ``flext_meltano``,
        ``FlextDbOracleModels`` → ``flext_db_oracle``.
        """
        for suffix in c.Infra.FAMILY_SUFFIXES.values():
            if class_name.endswith(suffix):
                stem = class_name[: -len(suffix)]
                break
        else:
            stem = class_name
        if stem == "Flext":
            return c.Infra.Packages.CORE_UNDERSCORE
        chars: MutableSequence[str] = []
        for i, ch in enumerate(stem):
            if ch.isupper() and i > 0:
                chars.append("_")
            chars.append(ch.lower())
        return "".join(chars)

    @staticmethod
    def generate_module_skeleton(
        class_name: str, base_class: str, docstring: str
    ) -> str:
        """Generate a basic python module containing a single class structure."""
        all_var = "__all__"
        return f'''"""{docstring}

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations


class {class_name}({base_class}):
    pass


{all_var} = ["{class_name}"]
'''


__all__ = ["FlextInfraUtilitiesFormatting"]
