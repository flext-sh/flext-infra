"""Formatting utilities for infrastructure code operations.

Provides canonical ruff formatting as static methods.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import contextlib
from collections.abc import MutableSequence
from pathlib import Path

from flext_infra import FlextInfraUtilitiesSubprocess, c


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
        check_cmd = [
            c.Infra.Cli.RUFF,
            c.Infra.Cli.RuffCmd.CHECK,
            "--fix",
        ]
        if quiet:
            check_cmd.append("--quiet")
        check_cmd.append(str(path))

        runner = FlextInfraUtilitiesSubprocess()
        if quiet:
            with contextlib.suppress(FileNotFoundError):
                runner.run_checked(check_cmd)
        else:
            runner.run_checked(check_cmd)

        if include_format:
            runner.run_checked([
                c.Infra.Cli.RUFF,
                c.Infra.Cli.RuffCmd.FORMAT,
                str(path),
            ])

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
            return "flext_core"
        chars: MutableSequence[str] = []
        for i, ch in enumerate(stem):
            if ch.isupper() and i > 0:
                chars.append("_")
            chars.append(ch.lower())
        return "".join(chars)


__all__ = ["FlextInfraUtilitiesFormatting"]
