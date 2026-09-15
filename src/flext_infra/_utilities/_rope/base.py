"""Shared constants, caches, and rope parse primitives."""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import ClassVar

from flext_infra.models import m
from flext_infra.typings import t

from ..rope_core import FlextInfraUtilitiesRopeCore
from ..rope_runtime import FlextInfraUtilitiesRopeRuntime


class FlextInfraUtilitiesRopeAnalysisBase:
    """Shared constants, caches, and rope parse primitives."""

    _INSTALL_LAZY_IMPORTS_ARG_INDEX: ClassVar[int] = 2
    _STRING_LITERAL_MIN_LENGTH: ClassVar[int] = 2
    _TRIPLE_QUOTE_LENGTH: ClassVar[int] = 3
    _IMPORT_ALIAS_AS_PARTS: ClassVar[int] = 3

    _parse_project: ClassVar[t.Infra.RopeProject | None] = None
    _SEMANTIC_STATE_CACHE: ClassVar[
        MutableMapping[tuple[str, str, int], m.Infra.ModuleSemanticState]
    ] = {}
    _EXPORT_NAMES_CACHE: ClassVar[
        MutableMapping[
            tuple[str, str, int, bool, bool, bool, bool, bool], t.StrSequence
        ]
    ] = {}

    @staticmethod
    def _shared_parse_project() -> t.Infra.RopeProject:
        """Return a process-wide rope project usable for string parsing."""
        cached = FlextInfraUtilitiesRopeAnalysisBase._parse_project
        if cached is None:
            # flext-o6h5 (agent: kimi) — root-cause fix: the anchor was a hardcoded
            # operator path that crashed CI (FileNotFoundError) and silently bound
            # the parse project to the wrong tree locally. Anchor on the validated
            # settings SSOT, with cwd as last resort — both exist where CLI runs.
            # Path() coercion keeps this correct while settings migrates the
            # field from str to Path (both accepted).
            from flext_infra import settings

            repository_root = settings.Infra.repository_root
            anchor = Path(repository_root) if repository_root else Path.cwd()
            cached = FlextInfraUtilitiesRopeCore.init_rope_project(anchor)
            FlextInfraUtilitiesRopeAnalysisBase._parse_project = cached
        return cached

    @staticmethod
    def parse_string_module(source: str) -> t.Infra.RopePyModule:
        """Parse ``source`` to a rope ``PyModule`` via a shared parsing project.

        Uses rope's ``libutils.get_string_module`` so callers don't need to
        manage temporary files. Parse failures raise; rope contract failures
        escape — the function never returns ``None``.
        """
        rope_project = FlextInfraUtilitiesRopeAnalysisBase._shared_parse_project()
        result: t.Infra.RopePyModule = FlextInfraUtilitiesRopeRuntime.get_string_module(
            rope_project, source
        )
        return result

    @staticmethod
    def _open_pymodule(
        project_root: Path, file_path: Path
    ) -> t.Pair[t.Infra.RopePyModule, t.Infra.RopeProject] | None:
        """Open a rope project and resolve ``file_path`` to a ``PyModule``."""
        rope_project = FlextInfraUtilitiesRopeCore.init_rope_project(project_root)
        resource = FlextInfraUtilitiesRopeCore.fetch_python_resource(
            rope_project, file_path
        )
        if resource is None:
            rope_project.close()
            return None
        pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(rope_project, resource)
        return pymodule, rope_project


__all__ = ["FlextInfraUtilitiesRopeAnalysisBase"]
