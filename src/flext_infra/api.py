"""Public API facade for flext-infra.

Factory-method composition over domain services.
Each domain is accessed via a static factory that returns
the domain's service **class** — ready for caller instantiation.

MRO composition is infeasible because domain services use
different type params (s[bool] vs s[str]).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, ClassVar, Self, override

from flext_core import r
from flext_infra import FlextInfraServiceBase

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfra(FlextInfraServiceBase[bool]):
    """Coordinate infrastructure operations via factory-method accessors.

    Each domain is accessed via a static factory that returns the domain's
    service **class**.  Callers instantiate with domain-specific kwargs::

        Generator = FlextInfra.basemk()
        gen = Generator(workspace_root=root)

        Checker = FlextInfra.check()
        result = Checker(workspace_root=root).execute()

    Domain services have incompatible type parameters (``s[bool]`` vs
    ``s[str]``), making MRO composition infeasible.  Factory methods
    avoid the diamond while keeping a single discovery entry point.
    """

    _instance: ClassVar[Self | None] = None

    @classmethod
    def get_instance(cls) -> Self:
        """Return the shared infra facade instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @override
    def execute(self) -> r[bool]:
        """Execute infrastructure service health check."""
        return r[bool].ok(True)

    @staticmethod
    def _load(module: str, name: str) -> type:
        """Lazy-load a class from a module to avoid circular imports."""
        cls: type = getattr(importlib.import_module(module), name)
        return cls

    # ------------------------------------------------------------------
    # Domain factory accessors — return the class, caller instantiates
    # ------------------------------------------------------------------

    @staticmethod
    def basemk() -> type[p.Infra.Generator]:
        """Return the base.mk template generator class."""
        return FlextInfra._load(
            "flext_infra.basemk.generator", "FlextInfraBaseMkGenerator"
        )

    @staticmethod
    def check() -> type[p.Infra.Checker]:
        """Return the workspace quality-gate checker class."""
        return FlextInfra._load(
            "flext_infra.check.workspace_check", "FlextInfraWorkspaceChecker"
        )

    @staticmethod
    def codegen() -> type[p.Infra.CodegenFixer]:
        """Return the codegen fixer class."""
        return FlextInfra._load("flext_infra.codegen.fixer", "FlextInfraCodegenFixer")

    @staticmethod
    def deps() -> type[p.Infra.PyprojectModernizer]:
        """Return the pyproject.toml modernizer class."""
        return FlextInfra._load(
            "flext_infra.deps.modernizer", "FlextInfraPyprojectModernizer"
        )

    @staticmethod
    def github() -> type[p.Infra.GithubService]:
        """Return the GitHub operations service class."""
        return FlextInfra._load("flext_infra.github.service", "FlextInfraGithubService")

    @staticmethod
    def refactor() -> type[p.Infra.RefactorEngine]:
        """Return the rope-based refactor engine class."""
        return FlextInfra._load(
            "flext_infra.refactor.engine", "FlextInfraRefactorEngine"
        )

    @staticmethod
    def release() -> type[p.Infra.ReleaseOrchestrator]:
        """Return the release orchestrator class."""
        return FlextInfra._load(
            "flext_infra.release.orchestrator",
            "FlextInfraReleaseOrchestrator",
        )

    @staticmethod
    def validate_scanner() -> type[p.Infra.Scanner]:
        """Return the text-pattern validation scanner class."""
        return FlextInfra._load(
            "flext_infra.validate.scanner", "FlextInfraTextPatternScanner"
        )

    @staticmethod
    def workspace() -> type[p.Infra.Orchestrator]:
        """Return the workspace orchestrator service class."""
        return FlextInfra._load(
            "flext_infra.workspace.orchestrator",
            "FlextInfraOrchestratorService",
        )


__all__ = ["FlextInfra"]
