"""Internal generated-surface owner invoked only by serialized ``make gen``."""

from __future__ import annotations

from typing import Annotated, override

from flext_core import r
from flext_infra import c, config, m, p, u
from flext_infra.base import s
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_infra.codegen.publisher import FlextInfraCodegenPublisher


class FlextInfraMakeGenerationService(s[m.Infra.CodegenResult]):
    """Plan, consumer-validate, publish, and prove one generated fixed point."""

    applying: Annotated[
        bool, m.Field(description="Validated mutation intent from the Make handler")
    ] = False
    execution_context: Annotated[
        m.Infra.MakeExecutionContext,
        m.Field(description="Already normalized public Make execution context"),
    ]

    @classmethod
    def execute_for(
        cls, context: m.Infra.MakeExecutionContext, *, applying: bool
    ) -> p.Result[m.Infra.CodegenResult]:
        """Execute from the already serialized public Make boundary."""
        return cls(
            workspace_root=context.target.root.resolve(),
            applying=applying,
            execution_context=context,
        ).execute()

    @staticmethod
    def _validate_real_make(context: m.Infra.MakeExecutionContext) -> p.Result[bool]:
        """Exercise each selected generated wrapper in its real checkout."""
        wrapper_path = config.Infra.codegen.surfaces.make_wrapper_path
        make = context.make
        intent_environment = (
            make.apply_variable,
            make.selector,
            make.ci.variable,
            *(
                f"{make.input_environment_prefix}{variable}"
                for input_spec in make.inputs
                for variable in input_spec.variables
            ),
        )
        for selected in context.targets:
            wrapper = selected.root / wrapper_path
            if not wrapper.is_file():
                return r[bool].fail(f"generated Make wrapper is missing: {wrapper}")
            consumed = u.Cli.run_live(
                (c.Infra.MAKE, "--no-print-directory", "-f", str(wrapper), "help"),
                cwd=selected.root,
                remove_env_keys=(
                    "MAKEFLAGS",
                    "MAKELEVEL",
                    "MAKEOVERRIDES",
                    "MFLAGS",
                    *intent_environment,
                ),
            )
            if consumed.failure:
                return r[bool].fail(
                    consumed.error
                    or f"GNU Make consumer rejected generated surface: {selected.root}"
                )
        return r[bool].ok(True)

    @override
    def execute(self) -> p.Result[m.Infra.CodegenResult]:
        """Keep calculation read-only unless the resolved handler is applying."""
        context = self.execution_context
        root = context.target.root.resolve()
        request = m.Infra.CodegenConformRequest(
            root=root,
            what=c.Infra.CodegenConformSurface.ALL,
            scope=context.target.conform_scope,
        )
        planner = FlextInfraCodegenConform(
            workspace_root=root,
            projection_operation="generate",
            initial_execution_context=context,
        )
        planned = planner.plan(request)
        if planned.failure:
            return r[m.Infra.CodegenResult].fail(
                planned.error or "make generation planning failed"
            )
        plan = planned.value
        valid = planner.validate_plan(plan, allow_missing_beads=self.applying)
        if valid.failure:
            return r[m.Infra.CodegenResult].fail(
                valid.error or "make generation plan validation failed"
            )
        changed = tuple(item for item in plan.files if item.changed)
        if not self.applying:
            if changed:
                paths = ", ".join(str(item.path) for item in changed)
                return r[m.Infra.CodegenResult].fail(
                    f"generated surface drift detected: {paths}"
                )
            consumed = self._validate_real_make(context)
            if consumed.failure:
                return r[m.Infra.CodegenResult].fail(
                    consumed.error or "real generated Make consumer failed"
                )
            return r[m.Infra.CodegenResult].ok(m.Infra.CodegenResult(plan=plan))
        published = FlextInfraCodegenPublisher.apply(plan)
        if published.failure:
            return r[m.Infra.CodegenResult].fail(
                published.error or "generated surface publication failed"
            )
        consumed = self._validate_real_make(context)
        if consumed.failure:
            return r[m.Infra.CodegenResult].fail(
                consumed.error
                or "real generated Make consumer failed after publication"
            )
        verified = planner.plan(request)
        if verified.failure:
            return r[m.Infra.CodegenResult].fail(
                verified.error or "post-generation planning failed"
            )
        residual = tuple(item for item in verified.value.files if item.changed)
        if residual:
            paths = ", ".join(str(item.path) for item in residual)
            return r[m.Infra.CodegenResult].fail(
                f"make generation did not reach a fixed point: {paths}"
            )
        return r[m.Infra.CodegenResult].ok(
            m.Infra.CodegenResult(plan=verified.value, written_files=published.value)
        )


__all__: list[str] = ["FlextInfraMakeGenerationService"]
