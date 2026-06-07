"""Gate contract validation models."""

from __future__ import annotations

from typing import Annotated, ClassVar, Self

from flext_infra import c, m, t


class FlextInfraGateContractModels:
    """Namespaced models for gate contract validation."""

    class UsageError(Exception):
        """Invalid CLI usage."""

    class InfraError(Exception):
        """Infrastructure validation failure."""

    class Ansi:
        """Terminal colors."""

        RED = "\033[31m"
        GREEN = "\033[32m"
        YELLOW = "\033[33m"
        CYAN = "\033[36m"
        RESET = "\033[0m"

    class Violation(m.BaseModel):
        """One contract violation."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        script: Annotated[str, m.Field(description="Script path")]
        check: Annotated[str, m.Field(description="Failed check")]
        message: Annotated[str, m.Field(description="Violation message")]
        severity: Annotated[str, m.Field(description="Severity")] = (
            c.Infra.GateSeverity.ERROR.value
        )

        @classmethod
        def create(cls, payload: t.JsonMapping) -> Self:
            """Validate one violation payload."""
            return cls.model_validate(payload)

    class ScriptInfo(m.BaseModel):
        """Validation result for one script."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        path: Annotated[str, m.Field(description="Script path")]
        extension: Annotated[str, m.Field(description="File extension")]
        role: Annotated[str, m.Field(description="Script role")]
        violations: Annotated[
            tuple[FlextInfraGateContractModels.Violation, ...],
            m.Field(description="Violations"),
        ] = ()

    class Summary(m.BaseModel):
        """Aggregate counts."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        errors: Annotated[int, m.Field(description="Error count")] = 0
        gate_scripts: Annotated[int, m.Field(description="Gate script count")] = 0
        ok: Annotated[int, m.Field(description="Passing gate script count")] = 0
        warnings: Annotated[int, m.Field(description="Warning count")] = 0

    class RunResult(m.BaseModel):
        """CLI outcome."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        exit_code: Annotated[int, m.Field(description="Process exit code")]
        violation_count: Annotated[int, m.Field(description="Error count")]


__all__: list[str] = ["FlextInfraGateContractModels"]
