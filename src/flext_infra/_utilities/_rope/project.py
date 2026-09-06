"""Warning-free Rope project boundary.

Rope 1.14.0 and its current upstream branch decorate
``Project._init_source_folders`` as deprecated while still calling it
unconditionally from ``Project.__init__``.  A strict warnings-as-errors runtime
therefore cannot construct the documented public ``Project`` at all.  The
boundary below preserves Rope's initializer semantics without filtering the
warning or weakening the process warning policy.
"""

from __future__ import annotations

from typing import override

from rope.base.project import Project


class FlextInfraRopeProject(Project):
    """Rope project with the upstream self-warning initializer repaired."""

    @override
    def _init_source_folders(self) -> None:
        """Initialize configured source roots without Rope's warning wrapper."""
        for path in self.prefs.get("source_folders", []) or []:
            self._custom_source_folders.append(self.get_resource(path))


__all__: list[str] = ["FlextInfraRopeProject"]
