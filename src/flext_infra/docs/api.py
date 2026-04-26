"""Single MRO orchestrator dispatching every docs phase via a typed discriminator.

Per AGENTS.md §2.5 (Service Facade Pattern). Provides ONE entry point for
programmatic callers — ``FlextInfraDocs(phase="audit", ...)`` — that routes to
the canonical phase service via a ``match`` dispatcher. The 5 typer-facing
service classes (auditor, builder, fixer, generator, validator) remain as
phase-specific Pydantic models so each typer route exposes only its relevant
CLI flags; this facade is the orchestrator-level SSOT.
"""

from __future__ import annotations

from typing import Annotated, override

from flext_infra import (
    FlextInfraDocAuditor,
    FlextInfraDocBuilder,
    FlextInfraDocFixer,
    FlextInfraDocGenerator,
    FlextInfraDocValidator,
    e,
    m,
    p,
    t,
)
from flext_infra.docs.base import FlextInfraDocServiceBase


class FlextInfraDocs(FlextInfraDocServiceBase):
    """Single MRO orchestrator dispatching every docs phase by discriminator.

    ``phase`` selects which canonical service runs. ``strict_mode`` is forwarded
    only when ``phase == "audit"``; the other phases ignore it. The 5 typer
    routes register the canonical phase services directly so each route exposes
    only its phase-specific CLI flags — this facade is the programmatic entry
    point shared by ``make docs DOCS_PHASE=all`` and any future single-process
    multi-phase orchestrator.
    """

    phase: Annotated[
        t.Infra.DocsPhase,
        m.Field(description="Phase to dispatch to (audit|build|fix|generate|validate)"),
    ]
    strict_mode: Annotated[
        bool,
        m.Field(
            alias="strict",
            description="Audit strict mode (ignored when phase != audit)",
        ),
    ] = False

    @override
    def execute(self) -> p.Result[bool]:
        """Construct the canonical phase service and delegate ``execute``.

        Match on the typed ``DocsPhase`` literal — Python 3.13 ``match/case``
        is exhaustive over the closed string set per AGENTS.md §3.2.
        """
        return self._dispatch().execute()

    def _dispatch(self) -> FlextInfraDocServiceBase:
        """Return the canonical phase service constructed from facade state.

        Uses Pydantic v2 ``model_dump`` to extract the inherited project-
        selection fields and ``model_validate`` to reconstruct each phase
        service — type-safe by construction (Pydantic enforces the schema)
        and SSOT (the field list lives ONCE on the parent class). Phase-
        specific extras are merged before validation.
        """
        payload = {
            field: getattr(self, field)
            for field in type(self).model_fields
            if field not in {"phase", "strict_mode"}
        }
        match self.phase:
            case "audit":
                return FlextInfraDocAuditor.model_validate(
                    payload | {"strict": self.strict_mode},
                )
            case "build":
                return FlextInfraDocBuilder.model_validate(payload)
            case "fix":
                return FlextInfraDocFixer.model_validate(payload)
            case "generate":
                return FlextInfraDocGenerator.model_validate(payload)
            case "validate":
                return FlextInfraDocValidator.model_validate(payload)
            case _:  # pragma: no cover — Pydantic rejects unknown DocsPhase at validation time.
                msg = f"unknown docs phase: {self.phase!r}"
                raise ValueError(msg)


__all__: list[str] = ["FlextInfraDocs"]


if __name__ == "__main__":  # pragma: no cover
    # Defensive — never raise on direct module execution.
    _ = e
    raise SystemExit(0)
