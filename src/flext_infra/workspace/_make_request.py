"""Typed request normalization for the generated Make runtime."""

from __future__ import annotations

import re
import shlex
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from flext_core import r
from flext_infra import c, m, p, u

if TYPE_CHECKING:
    from collections.abc import Sequence


class FlextInfraMakeRequestMixin:
    """Resolve one external Make request into its validated execution context."""

    if TYPE_CHECKING:
        verb: str
        selector_value: str
        apply_token: str

    @staticmethod
    def _input_values(
        invocation: m.Infra.MakeInvocationSpec, name: str
    ) -> tuple[str, ...]:
        return next(
            (item.values for item in invocation.inputs if item.name == name), ()
        )

    @classmethod
    def _input_flag(cls, invocation: m.Infra.MakeInvocationSpec, name: str) -> bool:
        return cls._input_values(invocation, name) == ("true",)

    @staticmethod
    def _parse_input(codec: str, raw: str) -> p.Result[tuple[str, ...]]:
        """Parse one external input once according to its typed codec."""
        value = raw.strip()
        boolean_values = {"0": (), "N": (), "1": ("true",), "Y": ("true",)}
        if any(character in value for character in "\0\r\n"):
            parsed = r[tuple[str, ...]].fail(
                "Make input contains control separators"
            )
        elif not value:
            parsed = r[tuple[str, ...]].ok(())
        elif codec == "boolean":
            boolean_value = boolean_values.get(value)
            parsed = (
                r[tuple[str, ...]].ok(boolean_value)
                if boolean_value is not None
                else r[tuple[str, ...]].fail(
                    "Make boolean input must be empty, 0, 1, N, or Y"
                )
            )
        elif codec == "argv":
            try:
                parsed = r[tuple[str, ...]].ok(tuple(shlex.split(value)))
            except ValueError as exc:
                parsed = r[tuple[str, ...]].fail_op("Make argv input", exc)
        elif codec in {"gate-selection", "project-selection"}:
            parsed = r[tuple[str, ...]].ok(
                tuple(item for item in re.split(r"[\s,]+", value) if item)
            )
        elif (
            codec == "distribution-name"
            and re.fullmatch(
                r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?", value
            )
            is None
        ):
            parsed = r[tuple[str, ...]].fail(
                "dependency must be one normalized distribution name"
            )
        else:
            parsed = r[tuple[str, ...]].ok((value,))
        return parsed

    @classmethod
    def _read_input_aliases(
        cls,
        make_config: m.Infra.MakeSpec,
        input_spec: m.Infra.MakeInputSpec,
    ) -> p.Result[tuple[tuple[str, tuple[str, ...]], ...]]:
        return r.traverse(
            input_spec.variables,
            lambda variable: cls._read_input_alias(
                make_config, input_spec, variable
            ),
        ).map(lambda groups: tuple(item for group in groups for item in group))

    @classmethod
    def _read_input_alias(
        cls,
        make_config: m.Infra.MakeSpec,
        input_spec: m.Infra.MakeInputSpec,
        variable: str,
    ) -> p.Result[tuple[tuple[str, tuple[str, ...]], ...]]:
        """Read one external Make variable into zero or one typed alias row."""
        environment_name = f"{make_config.input_environment_prefix}{variable}"
        raw_result = u.Cli.env_read(environment_name)
        if raw_result.failure:
            return r.fail(r.require_error(raw_result))
        raw = raw_result.value.strip()
        if not raw:
            return r.ok(())
        return cls._parse_input(input_spec.codec, raw).map(
            lambda values: ((variable, values),)
        )

    @staticmethod
    def _normalize_input_aliases(
        name: str, supplied: Sequence[tuple[str, tuple[str, ...]]]
    ) -> p.Result[tuple[str, ...]]:
        normalized = {values for _, values in supplied}
        if len(normalized) > 1:
            variables = ", ".join(variable for variable, _ in supplied)
            return r.fail(f"make input {name} received divergent aliases: {variables}")
        return r.ok(supplied[0][1] if supplied else ())

    @classmethod
    def _resolve_inputs(
        cls,
        make_config: m.Infra.MakeSpec,
        operation: m.Infra.MakeOperationSpec,
        handler: m.Infra.MakeHandlerSpec,
    ) -> p.Result[tuple[m.Infra.MakeInputValueSpec, ...]]:
        catalog = {item.name: item for item in make_config.inputs}
        return cls._reject_undeclared_inputs(
            make_config, operation
        ).flat_map(
            lambda _: r.traverse(
                operation.inputs,
                lambda name: cls._resolve_input(
                    make_config, catalog[name], name
                ),
            )
        ).flat_map(lambda resolved: cls._require_inputs(tuple(resolved), handler))

    @classmethod
    def _reject_undeclared_inputs(
        cls,
        make_config: m.Infra.MakeSpec,
        operation: m.Infra.MakeOperationSpec,
    ) -> p.Result[bool]:
        """Reject every supplied input absent from the selected operation SSOT."""
        declared = frozenset(operation.inputs)
        return r.traverse(
            tuple(item for item in make_config.inputs if item.name not in declared),
            lambda input_spec: cls._reject_undeclared_input(
                make_config, operation, input_spec
            ),
        ).map(lambda _: True)

    @classmethod
    def _reject_undeclared_input(
        cls,
        make_config: m.Infra.MakeSpec,
        operation: m.Infra.MakeOperationSpec,
        input_spec: m.Infra.MakeInputSpec,
    ) -> p.Result[bool]:
        """Reject one populated catalog input outside an operation contract."""
        supplied = cls._read_input_aliases(make_config, input_spec)
        if supplied.failure:
            return r.fail(r.require_error(supplied))
        if not supplied.value:
            return r.ok(True)
        variables = ", ".join(variable for variable, _ in supplied.value)
        return r.fail(
            f"Make operation {operation.name} does not accept input "
            f"{input_spec.name} via {variables}"
        )

    @classmethod
    def _resolve_input(
        cls,
        make_config: m.Infra.MakeSpec,
        input_spec: m.Infra.MakeInputSpec,
        name: str,
    ) -> p.Result[m.Infra.MakeInputValueSpec]:
        """Resolve all aliases for one canonical input name."""
        return cls._read_input_aliases(make_config, input_spec).flat_map(
            lambda aliases: cls._normalize_input_aliases(name, aliases)
        ).map(lambda values: m.Infra.MakeInputValueSpec(name=name, values=values))

    @staticmethod
    def _require_inputs(
        resolved_values: tuple[m.Infra.MakeInputValueSpec, ...],
        handler: m.Infra.MakeHandlerSpec,
    ) -> p.Result[tuple[m.Infra.MakeInputValueSpec, ...]]:
        """Require every handler-owned input after canonical alias resolution."""
        values_by_name = {item.name: item.values for item in resolved_values}
        missing = tuple(
            name
            for name in handler.required_inputs
            if not values_by_name.get(name, ())
        )
        if missing:
            return r.fail(f"Make handler requires inputs: {', '.join(missing)}")
        return r.ok(resolved_values)

    def _resolve_graph(
        self, make_config: m.Infra.MakeSpec
    ) -> p.Result[tuple[m.Infra.MakeVerbSpec, m.Infra.MakeOperationSpec]]:
        verb = next((item for item in make_config.verbs if item.name == self.verb), None)
        if verb is None:
            return r.fail(f"Make verb must resolve exactly once: {self.verb}")
        operations = {item.name: item for item in make_config.operations}
        return r.ok((verb, operations[verb.operation]))

    def _resolve_applying(self, make_config: m.Infra.MakeSpec) -> p.Result[bool]:
        applying = self.apply_token not in {"", make_config.apply_absent_value}
        if applying and self.apply_token != make_config.apply_value:
            return r.fail(
                f"{make_config.apply_variable} must be "
                f"{make_config.apply_value} when set"
            )
        return r.ok(applying)

    @staticmethod
    def _resolve_ci_scope(
        make_config: m.Infra.MakeSpec,
    ) -> p.Result[Literal["profile", "self"]]:
        ci_result = u.Cli.env_read(make_config.ci.variable)
        if ci_result.failure:
            return r.fail(r.require_error(ci_result))
        ci_token = ci_result.value.strip()
        if ci_token not in {"", make_config.ci.value}:
            return r.fail(
                f"{make_config.ci.variable} must be {make_config.ci.value} when set"
            )
        return r.ok(make_config.ci.target_scope if ci_token else "profile")

    def _resolve_handler(
        self,
        make_config: m.Infra.MakeSpec,
        verb: m.Infra.MakeVerbSpec,
        applying: bool,
    ) -> p.Result[m.Infra.MakeHandlerSpec]:
        selected_what = self.selector_value or (
            verb.apply_what if applying else verb.default_what
        )
        handler = next(
            (item for item in verb.handlers if item.what == selected_what), None
        )
        if handler is None:
            return r.fail(
                f"unsupported {verb.name} {make_config.selector}={selected_what} "
                f"(allowed: {', '.join(verb.whats)})"
            )
        if applying:
            if handler.apply_policy == "never":
                return r.fail(
                    f"Make handler {verb.name}:{selected_what} is read-only"
                )
        elif handler.apply_policy == "required":
            return r.fail(
                f"Make handler {verb.name}:{selected_what} requires "
                f"{make_config.apply_variable}={make_config.apply_value}"
            )
        return r.ok(handler)

    def _resolve_invocation(
        self, make_config: m.Infra.MakeSpec
    ) -> p.Result[m.Infra.MakeInvocationSpec]:
        return self._resolve_graph(make_config).flat_map(
            lambda graph: self._resolve_applying(make_config).flat_map(
                lambda applying: self._resolve_ci_scope(make_config).flat_map(
                    lambda target_scope: self._resolve_handler(
                        make_config, graph[0], applying
                    ).flat_map(
                        lambda handler: self._resolve_inputs(
                            make_config, graph[1], handler
                        ).map(
                            lambda inputs: m.Infra.MakeInvocationSpec(
                                verb=graph[0],
                                operation=graph[1],
                                handler=handler,
                                applying=applying,
                                target_scope=target_scope,
                                inputs=inputs,
                            )
                        )
                    )
                )
            )
        )

    @staticmethod
    def _governed_targets(
        workspace_root: Path, workspace: m.Infra.WorkspaceSpec
    ) -> tuple[m.Infra.MakeTargetSpec, ...]:
        return tuple(
            m.Infra.MakeTargetSpec(
                repository=repository, root=(workspace_root / repository.path).resolve()
            )
            for repository in (workspace.repository, *workspace.members)
            if all(
                (
                    repository.state is c.Infra.RepositoryState.ACTIVE,
                    repository.codegen is not c.Infra.CodegenKind.NONE,
                    not repository.read_only,
                )
            )
        )

__all__: list[str] = ["FlextInfraMakeRequestMixin"]
