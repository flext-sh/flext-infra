"""Public API facade for flext-infra.

Factory-method composition over domain services.
Each domain is accessed via a property/classmethod that returns
the domain's main service class instance.

MRO composition is infeasible because domain services use
different type params (s[bool] vs s[str]).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import ClassVar, Self, override

from flext_core import r
from flext_infra.base import FlextInfraServiceBase


class FlextInfra(FlextInfraServiceBase[bool]):
    """Coordinate infrastructure operations via factory-method accessors.

    Usage::

        infra = FlextInfra.get_instance()
        infra.basemk(...)   # Returns FlextInfraBaseMkGenerator instance
        infra.check(...)    # Returns FlextInfraWorkspaceChecker instance

    Domain factory accessors will be added by Plan 08 after
    Plans 02-07 complete domain refactoring.
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

    # Domain factory accessors -- filled in by Plan 08 after domain
    # refactoring.  Placeholder signatures for reference:
    #
    # def basemk(self, **kwargs) -> FlextInfraBaseMkGenerator: ...
    # def check(self, **kwargs) -> FlextInfraWorkspaceChecker: ...
    # def codegen(self, **kwargs) -> FlextInfraCodegenPipeline: ...
    # def deps(self, **kwargs) -> FlextInfraDepsModernizer: ...
    # def refactor(self, **kwargs) -> FlextInfraRefactorEngine: ...
    # def release(self, **kwargs) -> FlextInfraReleaseOrchestrator: ...
    # def validate(self, **kwargs) -> FlextInfraValidateScanner: ...
    # def workspace(self, **kwargs) -> FlextInfraOrchestratorService: ...


__all__ = ["FlextInfra"]
