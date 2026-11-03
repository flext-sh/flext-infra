"""Derive authored Protocol surfaces and upstream facade owners natively.

The model-to-protocol projector compares a projected contract with an authored
Protocol and names upstream structural bases. Both facts are read from Rope's
native class graph; no list of packages or members is kept here.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Sequence
from pathlib import Path

from flext_infra import p, t
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeRuntime,
)
from flext_infra._utilities.project_discovery import FlextInfraUtilitiesProjectDiscovery


class FlextInfraUtilitiesModelsProtocolContracts:
    """Read structural Protocol members and upstream facades from native ancestry."""

    @staticmethod
    def protocol_contract_members(
        project: p.Infra.RopeProject,
        protocol: p.Infra.RopeSourceClass,
        protocols_root: Path,
    ) -> dict[str, tuple[t.Infra.AstStatement, Path]]:
        """Collect every member an authored Protocol declares.

        Members inherited from the project's own Protocol ancestors count with
        the declared ones, in native MRO precedence, so a composed contract
        is read as its complete structural surface: attributes, properties
        and callables alike.

        Returns:
            Each member's declaring statement and declaring source path.

        Raises:
            TypeError: A declaring Protocol has no authenticated source AST.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        protocol_base = runtime.qualified_name(
            project, "Protocol", module_name="typing"
        ).get_object()
        root = protocols_root.resolve()
        members: dict[str, tuple[t.Infra.AstStatement, Path]] = {}
        for ancestor in reversed(protocol.get_mro()):
            if (
                not runtime.py_class(ancestor)
                or ancestor is protocol_base
                or protocol_base not in ancestor.get_mro()
            ):
                continue
            resource = ancestor.get_module().get_resource()
            if resource is None:
                continue
            path = Path(resource.real_path).resolve()
            if not path.is_relative_to(root):
                continue
            declaration = ancestor.get_ast()
            if not isinstance(declaration, ast.ClassDef):
                message = "authored contract has no authenticated class AST"
                raise TypeError(message)
            for statement in declaration.body:
                if isinstance(statement, ast.AnnAssign) and isinstance(
                    statement.target, ast.Name
                ):
                    members[statement.target.id] = (statement, path)
                elif isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef):
                    members[statement.name] = (statement, path)
        return members

    @staticmethod
    def upstream_protocol_facade(
        chain: Sequence[p.Infra.RopePyObject],
        package: Path,
        port: p.Infra.RopeSourceClass,
        *,
        source_project: p.Infra.RopeProject,
    ) -> tuple[str, str]:
        """Elect the nearest upstream published ``p`` facade that exposes ``port``.

        A Protocol base is evaluated while its class is created, so it is named
        through an upstream facade the package composes, never through the
        package's own facade under assembly. ``chain`` is the own facade's
        native ancestry closed by the port's declaring facade.

        Returns:
            The upstream facade class name and its package import statement.

        Raises:
            ValueError: No upstream published facade exposes ``port``.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        analysis = FlextInfraUtilitiesRopeAnalysis
        for ancestor in chain:
            if not runtime.py_class(ancestor):
                continue
            module = ancestor.get_module()
            resource = module.get_resource()
            if resource is None or Path(resource.real_path).is_relative_to(package):
                continue
            published = module.get_attributes().get("p")
            exposed = ancestor.get_attributes().get(port.get_name())
            if (
                published is None
                or published.get_object() is not ancestor
                or "p" not in analysis.public_export_names_source(module)
                or exposed is None
                or exposed.get_object() is not port
            ):
                continue
            # The declared source identity, not Rope's source-folder-relative
            # name: a repository namespace package keeps its namespace prefix.
            provider = analysis.package_name_for_module(
                FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
                    module, source_project=source_project
                ),
                resource,
            )
            name = ancestor.get_name()
            return name, f"from {provider} import {name}"
        message = f"protocol facade chain has no upstream owner of {port.get_name()}"
        raise ValueError(message)


__all__: list[str] = ["FlextInfraUtilitiesModelsProtocolContracts"]
