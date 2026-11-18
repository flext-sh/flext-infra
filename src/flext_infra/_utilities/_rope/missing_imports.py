"""Rope-native repair of Ruff F821 findings.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import ClassVar, cast

from rope.base.exceptions import ModuleNotFoundError as RopeModuleNotFoundError
from rope.base.pyobjects import PyClass, PyFunction
from rope.base.resources import File
from rope.contrib.autoimport import AutoImport

from flext_infra import p, r, t, u
from flext_infra._utilities._rope import FlextInfraUtilitiesRopeImports


class FlextInfraUtilitiesRopeMissingImports:
    """Repair undefined names by inserting Rope-resolved imports."""

    NAME_INDEX: ClassVar[int] = 1
    MESSAGE_PARTS: ClassVar[int] = 2
    GENERIC_NAMES: ClassVar[frozenset[str]] = frozenset({
        "Config",
        "Configuracao",
        "Conta",
        "Opcoes",
        "Papel",
        "Settings",
    })

    @staticmethod
    def repair(repository_root: Path, *, apply: bool = False) -> list[dict[str, str]]:
        """Repair F821 findings in one repository.

        Returns:
            One record per repaired name.

        """
        payload = FlextInfraUtilitiesRopeMissingImports._findings(repository_root)
        repaired: list[dict[str, str]] = []
        with u.Infra.open_project(repository_root) as project:
            autoimport = AutoImport(project)
            FlextInfraUtilitiesRopeMissingImports._prime(project, autoimport)
            for raw in payload:
                record = FlextInfraUtilitiesRopeMissingImports._repair_one(
                    project, autoimport, raw, repository_root, apply=apply
                )
                if record is not None:
                    repaired.append(record)
        return repaired

    @staticmethod
    def _prime(project: p.Infra.RopeProject, autoimport: AutoImport) -> None:
        """Index modules one by one; one unparseable module never aborts repair."""
        for resource in project.get_python_files():
            try:
                autoimport.update_resource(resource)
            except (RuntimeError, ValueError):
                continue

    @classmethod
    def execute(
        cls, request: p.Infra.RefactorNamespaceEnforceInput
    ) -> p.Result[t.Cli.ResultValue]:
        """Run the repair through the standard refactor request surface.

        Returns:
            The resulting command value.

        """
        repaired = cls.repair(request.repository_root, apply=request.apply)
        if request.verbose:
            for item in repaired:
                u.Cli.info(f"{item['file']}: {item['name']} <- {item['module']}")
        u.Cli.info(f"rope missing-imports: {len(repaired)} repaired")
        return r[t.Cli.ResultValue].ok(value=True)

    @staticmethod
    def _findings(repository_root: Path) -> list[object]:
        found = u.Cli.run_raw(
            [
                "ruff",
                "check",
                "--select",
                "F821",
                "--output-format",
                "json",
                ".",
            ],
            cwd=repository_root,
        )
        if found.failure:
            return []
        payload = cast("object", json.loads(found.value.stdout))
        return payload if isinstance(payload, list) else []

    @staticmethod
    def _target(raw: object, repository_root: Path) -> tuple[str, Path] | None:
        if not isinstance(raw, dict) or raw.get("code") != "F821":
            return None
        message = raw.get("message")
        filename = raw.get("filename")
        if not isinstance(message, str) or not isinstance(filename, str):
            return None
        parts = message.split("`")
        if len(parts) < FlextInfraUtilitiesRopeMissingImports.MESSAGE_PARTS:
            return None
        name = parts[FlextInfraUtilitiesRopeMissingImports.NAME_INDEX]
        relative = Path(filename).resolve().relative_to(repository_root.resolve())
        return name, relative

    @staticmethod
    def _module_for(
        project: p.Infra.RopeProject,
        autoimport: AutoImport,
        name: str,
        target_package: str,
        target_module: str,
    ) -> str | None:
        modules = [
            module
            for module in autoimport.get_modules(name)
            if not module.startswith(("tests.", "test."))
        ]
        if name in FlextInfraUtilitiesRopeMissingImports.GENERIC_NAMES:
            return None
        if len(modules) != 1:
            return None
        module = modules[0]
        if module == target_module:
            return None
        same_domain = module.rsplit(".", 1)[0].startswith(target_package)
        if not name[:1].isupper() and not same_domain:
            return None
        try:
            pymodule = project.get_module(module)
        except RopeModuleNotFoundError:
            pymodule = project.get_module(f"src.{module}")
        defined = pymodule[name].get_object()
        return module if isinstance(defined, (PyClass, PyFunction)) else None

    @staticmethod
    def _repair_one(
        project: p.Infra.RopeProject,
        autoimport: AutoImport,
        raw: object,
        repository_root: Path,
        *,
        apply: bool,
    ) -> dict[str, str] | None:
        target = FlextInfraUtilitiesRopeMissingImports._target(raw, repository_root)
        if target is None:
            return None
        name, relative = target
        resource = project.get_resource(str(relative))
        if not isinstance(resource, File):
            return None
        parts = relative.with_suffix("").parts
        if parts and parts[0] == "src":
            parts = parts[1:]
        target_package = ".".join(parts[:-1])
        target_module = ".".join(parts)
        module = FlextInfraUtilitiesRopeMissingImports._module_for(
            project, autoimport, name, target_package, target_module
        )
        if module is None:
            return None
        updated = FlextInfraUtilitiesRopeImports.add_import(
            project, resource, module, [name], apply=apply
        )
        return (
            {"file": str(relative), "name": name, "module": module}
            if updated is not None
            else None
        )


__all__: list[str] = ["FlextInfraUtilitiesRopeMissingImports"]
