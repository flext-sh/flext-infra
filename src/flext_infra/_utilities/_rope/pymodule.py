"""Rope PyModule / identifier helpers — concern of FlextInfraUtilitiesRopeCore.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import ClassVar, overload

from flext_infra import t
from flext_infra._utilities._rope.rope_runtime import FlextInfraUtilitiesRopeRuntime


class FlextInfraUtilitiesRopeCorePyModule:
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
        pyname: t.Infra.RopePyName | None = None,
    ) -> int | None:
        """Return the absolute offset of one exact identifier token on a line.

        Rope returns definition line numbers but not the column for many ``PyName``
        variants. Using ``str.find(symbol)`` is incorrect because it can match a
        substring inside another token or keyword, e.g. ``except ... as e``.
        This helper resolves the first exact identifier token equal to ``symbol``
        on the reported line for lexical callers. Inventory callers supply the
        binding: candidate tokens are resolved by Rope and compared to that exact
        binding. Multiple matching tokens fail rather than guessing which is the
        definition and which is a same-line use.

        Returns:
            The absolute offset of one exact identifier token on a line.

        Raises:
            RuntimeError: If the binding has no defining module or matching tokens
                are ambiguous on its definition line.

        """
        if line < 1 or line > len(lines):
            return None
        line_start = sum(len(item) for item in lines[: line - 1])
        source_line = lines[line - 1]
        offsets = (
            line_start + match.start()
            for match in (
                FlextInfraUtilitiesRopeCorePyModule._IDENTIFIER_PATTERN.finditer(
                    source_line,
                )
            )
            if match.group(0) == symbol
        )
        if pyname is None:
            return next(offsets, None)
        pymodule = pyname.get_definition_location()[0]
        if pymodule is None:
            msg = f"rope definition binding has no module: {symbol}:{line}"
            raise RuntimeError(msg)
        matching_offsets = tuple(
            offset
            for offset in offsets
            if FlextInfraUtilitiesRopeRuntime.name_definition_resource_path(
                pymodule,
                offset,
                expected_binding=pyname,
            )
            is not None
        )
        if len(matching_offsets) > 1:
            msg = f"rope definition binding token is ambiguous: {symbol}:{line}"
            raise RuntimeError(msg)
        return matching_offsets[0] if matching_offsets else None

    @staticmethod
    def resolvable_module_resource(resource: t.Infra.RopeResource) -> bool:
        """Whether the resource can own a Python module for rope's resolver.

        A plain data directory (no ``__init__.py``, no sibling source module)
        owns no module: rope's ``find_module`` still reports it, and handing
        it to ``resolve_pymodule`` would fail loud on a non-PyModule.

        Returns:
            The resulting ``bool``.

        """
        if FlextInfraUtilitiesRopeRuntime.file_resource(resource):
            return True
        path = Path(resource.real_path)
        return (path / "__init__.py").is_file() or path.with_suffix(".py").is_file()

    @staticmethod
    @overload
    def resolve_pymodule(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeFile,
    ) -> t.Infra.RopeSourceModule: ...

    @staticmethod
    @overload
    def resolve_pymodule(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> t.Infra.RopeParsedModule: ...

    @staticmethod
    def resolve_pymodule(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> t.Infra.RopeParsedModule:
        """Resolve modules and packages with Python's namespace precedence.

        A sibling source module takes precedence over an uninitialized data
        directory; an initialized package retains precedence over that module.

        Returns:
            The resulting ``t.Infra.RopeParsedModule``.

        Raises:
            TypeError: The native result is not parsed, or a file returned a
                non-source module.

        """
        pymodule = FlextInfraUtilitiesRopeRuntime.require_parsed_module(
            rope_project.get_pymodule(resource)
            if FlextInfraUtilitiesRopeRuntime.file_resource(resource)
            else rope_project.get_relative_module(resource.name, resource.parent, 1),
        )
        if FlextInfraUtilitiesRopeRuntime.file_resource(
            resource
        ) and not FlextInfraUtilitiesRopeRuntime.source_module(pymodule):
            msg = "rope file resource returned a non-source module"
            raise TypeError(msg)
        return pymodule

    @staticmethod
    def resolve_module_imports(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> t.Infra.RopeModuleImports:
        """Resolve the module import table, raising when rope cannot build it.

        Returns:
            The resulting ``t.Infra.RopeModuleImports``.

        Raises:
            RuntimeError: If rope module import table unavailable for.

        """
        runtime_errors: tuple[type[BaseException], ...] = (
            *FlextInfraUtilitiesRopeRuntime.rope_runtime_errors(),
            TypeError,
        )
        try:
            module_imports = FlextInfraUtilitiesRopeRuntime.module_imports_for_pymodule(
                rope_project,
                FlextInfraUtilitiesRopeCorePyModule.resolve_pymodule(
                    rope_project,
                    resource,
                ),
            )
        except runtime_errors as exc:
            msg = (
                "rope module import table unavailable for "
                f"{resource.path}: {type(exc).__name__}: {exc!s}"
            )
            raise RuntimeError(msg) from exc
        result: t.Infra.RopeModuleImports = module_imports
        return result


__all__: list[str] = ["FlextInfraUtilitiesRopeCorePyModule"]
