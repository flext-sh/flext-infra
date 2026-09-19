"""Codegen conformance base: the final class of the linear responsibility chain."""

from __future__ import annotations

from .execute import FlextInfraCodegenConformExecute


class FlextInfraCodegenConformBase(FlextInfraCodegenConformExecute):
    """Plan every selected output, then atomically write only a clean plan.

    The chain is linear in dependency order, so every responsibility statically
    inherits what it calls: bootstrap (service root, request state) <- gitignore
    <- docs ownership <- beads routes <- file plans <- pyproject policy <-
    context render <- artifact render <- existing plan <- scaffold plan <- plan
    <- execute.
    """


__all__: list[str] = ["FlextInfraCodegenConformBase"]
