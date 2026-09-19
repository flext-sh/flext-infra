"""Unified, fail-closed conformance for new and existing repositories.

Implementation lives in ``flext_infra.codegen._conform.base`` via MRO composition.
"""

from __future__ import annotations

from ._conform import FlextInfraCodegenConform

__all__: list[str] = ["FlextInfraCodegenConform"]
