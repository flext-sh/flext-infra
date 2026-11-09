"""Admit native model-envelope refactorings from source-bound Pyrefly findings.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
from pathlib import Path

from flext_cli import u

from flext_infra import m, p
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
)
from flext_infra._utilities._semantic_cutover.declaration_payload import (
    FlextInfraUtilitiesDeclarationPayload,
)
from flext_infra._utilities.workspace_snapshot import (
    FlextInfraUtilitiesWorkspaceSnapshot,
)


class FlextInfraUtilitiesSemanticModelEnvelopes:
    """Keep valid native constructors while correcting proven protocol boundaries."""

    @staticmethod
    def _diagnostic_pair(issue: p.Infra.Issue) -> tuple[str, str, str, str] | None:
        """Read only Pyrefly's exact native argument diagnostic shape.

        Returns:
            Actual type, parameter, required type and constructor identity.

        """
        if issue.code != "bad-argument-type":
            return None
        parts = issue.message.split("`")
        shape = [
            "Argument ",
            " is not assignable to parameter ",
            " with type ",
            " in function ",
            "",
        ]
        if parts[::2] != shape or len(parts[1::2]) != len(shape) - 1:
            return None
        return parts[1], parts[3], parts[5], parts[7]

    @staticmethod
    def _protocol_twin(
        project: p.Infra.RopeProject,
        actual: str,
        expected: str,
        routes: Mapping[str, str],
    ) -> bool:
        """Authenticate protocol substitutions through generated source bindings.

        Returns:
            Whether the types differ only by an authenticated projected model.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        replaced = expected
        for model, protocol in routes.items():
            if model.startswith("m.") or model not in replaced:
                continue
            concrete = runtime.qualified_name(project, model).get_object()
            identity = runtime.native_object_identity(concrete).replace("::", ".")
            if identity != model:
                continue
            target = runtime.qualified_name(
                project, f"{model.partition('.')[0]}.{protocol}"
            ).get_object()
            projected = runtime.native_object_identity(target).replace("::", ".")
            if projected:
                replaced = replaced.replace(identity, projected)
        return replaced != expected and replaced == actual

    @classmethod
    def _model_envelope_issues(
        cls,
        project: p.Infra.RopeProject,
        issues: Sequence[p.Infra.Issue],
        routes: Mapping[str, str],
    ) -> Mapping[Path, Sequence[tuple[p.Infra.Issue, str, str]]]:
        """Retain diagnostics whose type difference has a source-owned twin.

        Returns:
            Native argument diagnostics grouped by logical source identity.

        """
        root = Path(project.root.real_path)
        admitted: dict[Path, list[tuple[p.Infra.Issue, str, str]]] = {}
        for issue in issues:
            pair = cls._diagnostic_pair(issue)
            if pair is None:
                continue
            actual, parameter, expected, constructor = pair
            if not constructor.endswith(".__init__") or not cls._protocol_twin(
                project, actual, expected, routes
            ):
                continue
            path = Path(issue.file)
            path = path if path.is_absolute() else root / path
            admitted.setdefault(path, []).append((issue, parameter, constructor))
        return admitted

    @staticmethod
    def _model_envelope_call(
        module: p.Infra.RopePyModule,
        invocation: ast.Call,
        findings: Sequence[tuple[p.Infra.Issue, str, str]],
        model_base: p.Infra.RopePyObject,
    ) -> bool:
        """Prove the native constructor and its diagnosed keyword.

        Returns:
            Whether this exact call is a native model-envelope boundary.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        located = tuple(
            owner
            for issue, parameter, owner in findings
            if any(
                keyword.arg == parameter
                and (keyword.value.lineno, keyword.value.col_offset + 1)
                <= (issue.line, issue.column)
                <= (keyword.value.end_lineno, keyword.value.end_col_offset + 1)
                for keyword in invocation.keywords
                if keyword.value.end_lineno is not None
                and keyword.value.end_col_offset is not None
            )
        )
        if (
            not located
            or invocation.args
            or any(keyword.arg is None for keyword in invocation.keywords)
        ):
            return False
        scope = runtime.scope_at(
            module, runtime.source_offset(module.source_code, invocation)
        )
        binding = runtime.resolve_symbol(scope, invocation.func)
        if (
            binding is None
            or model_base
            not in FlextInfraUtilitiesDeclarationPayload.class_ancestry(
                binding.get_object()
            )
        ):
            return False
        module_name, _separator, qualified = runtime.native_object_identity(
            binding.get_object()
        ).partition("::")
        constructor = f"{module_name}.{qualified.rpartition('.')[2]}.__init__"
        accepted = constructor in located
        u.Cli.info(
            f"mod: model-envelope candidate={module.get_name()}:{invocation.lineno} "
            f"native_constructor={constructor} diagnosed={located} admitted={accepted}"
        )
        return accepted

    @staticmethod
    def _native_envelope_change(
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        resource: p.Infra.RopeResource,
        occurrence: tuple[int, ast.Call],
        updates: Mapping[Path, str],
    ) -> p.Infra.RopeChangeContents:
        """Specialize the native call shape and let Rope retain every expression.

        Returns:
            The native content change for the authenticated call.

        Raises:
            ValueError: Native matching lost the source admitted by the analyzer.

        """
        offset, invocation = occurrence
        captures = ", ".join(
            f"{keyword.arg}=${{argument_{index}}}"
            for index, keyword in enumerate(invocation.keywords)
        )
        values = ", ".join(
            f'"{keyword.arg}": (${{argument_{index}}})'
            for index, keyword in enumerate(invocation.keywords)
        )
        with project.source_view(
            declared_files=FlextInfraUtilitiesWorkspaceSnapshot.workspace_declared_sources(
                Path(project.root.real_path), (), updates, source_project=project
            ),
            additional_source_folders=None,
        ) as candidate:
            changes = FlextInfraUtilitiesRopeRuntimeRefactors.restructure_changes(
                candidate,
                m.Infra.RopeRestructureRequest(
                    pattern=rule.pattern.replace("${arguments}", captures),
                    goal=rule.goal.replace("${arguments}", values),
                    arguments=rule.arguments,
                    resources=(resource,),
                    match_filter=lambda _module, match: match.get_region()[0] == offset,
                ),
            )
            members = FlextInfraUtilitiesRopeRuntimeRefactors.change_set_members(
                changes.changes, f"{rule.id}: invalid native envelope changes"
            ).unwrap()
            if len(members) != 1:
                message = (
                    f"{rule.id}: native envelope change lost its admitted "
                    f"source: {resource.real_path}:{invocation.lineno}"
                )
                raise ValueError(message)
            return members[0]

    @classmethod
    def model_envelope_changes(
        cls,
        project: p.Infra.RopeProject,
        rules: p.Infra.RopeContractRule,
        resources: Sequence[p.Infra.RopeResource],
        issues: Sequence[p.Infra.Issue],
        routes: Mapping[str, str],
    ) -> list[p.Infra.RopeChangeContents]:
        """Delegate admitted keyword shapes to native Rope in reverse source order.

        Returns:
            Native content plans; no source is written by this operation.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        model_base = runtime.qualified_name(project, "pydantic.BaseModel").get_object()
        admitted = cls._model_envelope_issues(project, issues, routes)

        updates: dict[Path, str] = {}
        planned: dict[Path, p.Infra.RopeChangeContents] = {}
        for resource in resources:
            path = Path(resource.real_path)
            if path not in admitted:
                continue
            module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
                project,
                FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                    resource, path
                ),
            )
            invocations = sorted(
                (
                    node
                    for node in ast.walk(module.get_ast())
                    if isinstance(node, ast.Call)
                    and cls._model_envelope_call(
                        module, node, admitted[path], model_base
                    )
                ),
                key=lambda node: runtime.source_offset(module.source_code, node),
                reverse=True,
            )
            u.Cli.info(
                f"mod: model-envelope source={path} "
                f"diagnostics={len(admitted[path])} admitted_calls={len(invocations)}"
            )
            for invocation in invocations:
                offset = runtime.source_offset(module.source_code, invocation)
                change = cls._native_envelope_change(
                    project, rules, resource, (offset, invocation), updates
                )
                planned[path] = change
                updates[path] = change.new_contents
        return list(planned.values())
