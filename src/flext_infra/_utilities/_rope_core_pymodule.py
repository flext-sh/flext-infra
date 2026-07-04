"""Rope PyModule / identifier helpers — extracted concern of FlextInfraUtilitiesRopeCore."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, ClassVar

import rope.refactor.importutils as rope_importutils
from rope.base.exceptions import RefactoringError, ResourceNotFoundError
from rope.base.pyobjectsdef import PyModule

if TYPE_CHECKING:
    from rope.base.project import Project
    from rope.base.resources import File
    from rope.refactor.importutils.module_imports import ModuleImports

    from flext_infra.typings import t


class FlextInfraUtilitiesRopeCorePyModuleMixin:
    """PyModule resolution + import-table + identifier-offset helpers.

    Composed into FlextInfraUtilitiesRopeCore via inheritance so the helpers
    stay reachable as ``FlextInfraUtilitiesRopeCore.<method>`` for all callers.
    """

    _IDENTIFIER_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"\b[A-Za-z_]\w*\b")

    @staticmethod
    def find_identifier_offset_in_lines(
        lines: t.SequenceOf[str],
        *,
        line: int,
        symbol: str,
    ) -> int | None:
        """Return the absolute offset of one exact identifier token on a line.

        Rope returns definition line numbers but not the column for many ``PyName``
        variants. Using ``str.find(symbol)`` is incorrect because it can match a
        substring inside another token or keyword, e.g. ``except ... as e``.
        This helper resolves the first exact identifier token equal to ``symbol``
        on the reported line.
        """
        if line < 1 or line > len(lines):
            return None
        line_start = sum(len(item) for item in lines[: line - 1])
        source_line = lines[line - 1]
        for (
            match
        ) in FlextInfraUtilitiesRopeCorePyModuleMixin._IDENTIFIER_PATTERN.finditer(
            source_line,
        ):
            if match.group(0) == symbol:
                offset: int = line_start + match.start()
                return offset
        return None

    @staticmethod
    def get_pymodule(
        rope_project: Project,
        resource: File,
    ) -> PyModule:
        """Resolve one concrete rope PyModule through the validated API boundary."""
        pymodule = rope_project.get_pymodule(resource)
        if not isinstance(pymodule, PyModule):
            msg = "rope project returned non-PyModule"
            raise TypeError(msg)
        return pymodule

    @staticmethod
    def get_module_imports(
        rope_project: Project,
        resource: File,
    ) -> ModuleImports | None:
        """Get module imports."""
        try:
            module_imports = rope_importutils.get_module_imports(
                rope_project,
                FlextInfraUtilitiesRopeCorePyModuleMixin.get_pymodule(
                    rope_project,
                    resource,
                ),
            )
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            return None
        return module_imports


__all__: list[str] = ["FlextInfraUtilitiesRopeCorePyModuleMixin"]
