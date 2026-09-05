"""Typed filesystem ordering through the infrastructure utility facade."""

from __future__ import annotations

from pathlib import Path


class FlextInfraUtilitiesSortKeys:
    """Own deterministic path ordering for infrastructure services."""

    @staticmethod
    def path_depth(path: Path) -> int:
        """Return the number of components in a path."""
        return len(path.parts)

    @classmethod
    def path_depth_then_text(cls, path: Path) -> tuple[int, str]:
        """Order paths by depth and then stable POSIX text."""
        return cls.path_depth(path), path.as_posix()


__all__: tuple[str, ...] = ("FlextInfraUtilitiesSortKeys",)
