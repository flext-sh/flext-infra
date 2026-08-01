"""Base utilities for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_cli import u
from flext_infra.constants import c
from flext_infra.typings import t


class FlextInfraUtilitiesBase:
    """Base utilities for flext-infra project.

    Provides primitive helpers used across all infra utility subclasses.
    Generic ``validate`` and ``deep`` methods use PEP 695 type parameters
    so callers can validate ANY shape with a single SSOT helper.
    """

    @staticmethod
    def resolve_workspace_root_or_cwd(workspace_root: Path | None = None) -> Path:
        """Resolve workspace root from explicit value or current working directory."""
        target = workspace_root or Path.cwd()
        if target.is_file():
            target = target.parent
        return FlextInfraUtilitiesBase.enclosing_workspace_root(target.resolve())

    @staticmethod
    def enclosing_workspace_root(repository_root: Path) -> Path:
        """Return the superproject owning ``repository_root``, else itself.

        A managed member (e.g. ``flext-infra``) is a Git submodule of the
        workspace superproject. Every workspace-scoped derivation -- member
        discovery, path-dependency search roots, manifest lookup -- is only
        correct relative to that superproject. Defaulting to the current
        working directory silently degrades those derivations to an empty
        member set whenever a canonical verb runs from inside a member,
        which strips sibling import roots from the type-checker search path.
        """
        resolved_root = repository_root.expanduser().resolve()
        superproject = u.Cli.capture(
            [c.Infra.GIT, "rev-parse", "--show-superproject-working-tree"],
            cwd=resolved_root,
        )
        if superproject.failure:
            return resolved_root
        declared = superproject.value.strip()
        return Path(declared).resolve() if declared else resolved_root

    @staticmethod
    def normalize_optional_path(value: str | Path | None) -> Path | None:
        """Resolve one optional path-like value when present."""
        if value is None:
            return None
        path = value if isinstance(value, Path) else Path(value)
        return path.resolve()

    @staticmethod
    def normalize_cli_values(*values: str | None) -> t.StrSequence:
        """Normalize comma-separated or whitespace-separated CLI selectors."""
        return tuple(
            item.strip()
            for value in values
            for group in (value or "").split(",")
            for item in group.split()
            if item.strip()
        )

    @staticmethod
    def normalize_sequence_values(values: t.StrSequence | None) -> t.StrSequence | None:
        """Normalize repeated CLI sequence fields into a compact selector list."""
        names = FlextInfraUtilitiesBase.normalize_cli_values(*(values or ()))
        return names or None

    @staticmethod
    def normalize_make_args(values: t.StrSequence) -> t.StrSequence:
        """Return trimmed make arguments without blank entries."""
        return tuple(item.strip() for item in values if item.strip())

    @staticmethod
    def classify_process_exit(exit_code: int) -> str:
        """Classify a nonzero process status as timeout, signal, or failure."""
        if exit_code == c.Infra.PROCESS_TIMEOUT_EXIT_CODE:
            return "timeout"
        if exit_code < 0:
            return f"signal={-exit_code}"
        if exit_code >= c.Infra.PROCESS_SIGNAL_EXIT_OFFSET:
            return f"signal={exit_code - c.Infra.PROCESS_SIGNAL_EXIT_OFFSET}"
        return "failure"

    @staticmethod
    def normalize_process_exit_code(raw_exit_code: int) -> int:
        """Map a subprocess signal return code into the portable shell domain."""
        if raw_exit_code < 0:
            normalized_exit_code: int = (
                c.Infra.PROCESS_SIGNAL_EXIT_OFFSET - raw_exit_code
            )
            return normalized_exit_code
        return raw_exit_code


__all__: list[str] = ["FlextInfraUtilitiesBase"]
