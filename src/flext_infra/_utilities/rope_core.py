"""Shared Rope lifecycle helpers."""

from __future__ import annotations

import warnings
from collections.abc import (
    Generator,
)
from contextlib import contextmanager
from pathlib import Path
from typing import ClassVar

from rope.base.exceptions import (
    ModuleSyntaxError,
    RefactoringError,
    ResourceNotFoundError,
)
from rope.base.project import Project
from rope.base.pyobjects import AbstractClass
from rope.base.pyobjectsdef import PyFunction

from flext_core import t
from flext_infra._constants.rope import FlextInfraConstantsRope
from flext_infra._constants.validate import FlextInfraConstantsSharedInfra
from flext_infra._utilities._rope_core_pymodule import (
    FlextInfraUtilitiesRopeCorePyModuleMixin,
)
from flext_infra._utilities._rope_core_resources import (
    FlextInfraUtilitiesRopeCoreResourcesMixin,
)
from flext_infra._utilities.namespace_config import FlextInfraUtilitiesNamespaceConfig
from flext_infra._utilities.project_discovery import FlextInfraUtilitiesProjectDiscovery
from flext_infra._utilities.rope_pep695_patch import (
    FlextInfraUtilitiesRopePep695Patch,
)


class FlextInfraUtilitiesRopeCore(
    FlextInfraUtilitiesRopeCoreResourcesMixin,
    FlextInfraUtilitiesRopeCorePyModuleMixin,
):
    """Core Rope lifecycle helpers."""

    SYNTAX_ERRORS: ClassVar[tuple[type[BaseException], ...]] = (
        SyntaxError,
        ModuleSyntaxError,
    )
    RUNTIME_ERRORS: ClassVar[tuple[type[BaseException], ...]] = (
        RefactoringError,
        ResourceNotFoundError,
        AttributeError,
    )
    ABSTRACT_CLASS_TYPES: ClassVar[tuple[type[AbstractClass], ...]] = (AbstractClass,)
    PY_FUNCTION_TYPES: ClassVar[tuple[type[PyFunction], ...]] = (PyFunction,)

    @staticmethod
    def init_rope_project(
        workspace_root: Path,
        *,
        project_prefix: str = FlextInfraConstantsSharedInfra.PKG_PREFIX_HYPHEN,
        src_dir: str = FlextInfraConstantsSharedInfra.DEFAULT_SRC_DIR,
        ignored_resources: t.StrSequence = (
            FlextInfraConstantsRope.ROPE_IGNORED_RESOURCES
        ),
    ) -> Project:
        """Create a rope Project over workspace_root with no disk artifacts."""
        _ = (project_prefix, src_dir)
        FlextInfraUtilitiesRopePep695Patch.apply()
        resolved_root = workspace_root.resolve()
        project_roots = FlextInfraUtilitiesProjectDiscovery.discover_project_roots(
            resolved_root,
        )
        source_folders = sorted({
            str(scan_path.relative_to(resolved_root))
            for project_root in project_roots
            for dir_name in FlextInfraUtilitiesNamespaceConfig.namespace_scan_dirs(
                project_root,
            )
            if (scan_path := project_root / dir_name).is_dir()
        })
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Delete once deprecated functions are gone",
                category=DeprecationWarning,
            )
            return Project(
                str(resolved_root),
                ropefolder="",
                save_objectdb=False,
                ignored_resources=list(ignored_resources),
                source_folders=source_folders,
            )

    @staticmethod
    @contextmanager
    def open_project(
        workspace_root: Path,
    ) -> Generator[Project]:
        """Open one Rope project and always close it through the core boundary."""
        rope_project = FlextInfraUtilitiesRopeCore.init_rope_project(workspace_root)
        try:
            yield rope_project
        finally:
            rope_project.close()


__all__: list[str] = ["FlextInfraUtilitiesRopeCore"]
