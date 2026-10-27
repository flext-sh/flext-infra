"""Route config-owned dynamic environment keys through their settings owner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections import Counter
from typing import TYPE_CHECKING, override

import libcst as cst
from libcst.codemod import CodemodContext
from libcst.codemod.visitors import AddImportsVisitor
from libcst.metadata import (
    MetadataWrapper,
    ParentNodeProvider,
    QualifiedNameProvider,
    QualifiedNameSource,
)

from flext_infra import FlextInfraConfig, c, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesProjectManagedArtifacts,
)
from flext_infra._utilities._pyproject.conform import (
    FlextInfraUtilitiesPyprojectConform,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticCutoverBindings,
    FlextInfraUtilitiesSemanticCutoverEdits,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from flext_infra import m, p


class FlextInfraUtilitiesSemanticCutoverDynamicEnvironment(
    FlextInfraUtilitiesSemanticCutoverEdits,
    FlextInfraUtilitiesSemanticCutoverBindings,
):
    """Require resolved OS imports and same-function config provenance."""

    class _EnvironmentTransformer(cst.CSTTransformer):
        METADATA_DEPENDENCIES = (ParentNodeProvider, QualifiedNameProvider)

        def __init__(self, bindings: t.MappingKV[str, int]) -> None:
            self.aliases: t.MutableMappingKV[
                t.Pair[str, t.Infra.Cst.FunctionDef], str
            ] = {}
            self.packages: set[str] = set()
            self.bindings = bindings

        def _qualified(self, node: t.Infra.Cst.CSTNode, expected: str) -> bool:
            names = self.get_metadata(QualifiedNameProvider, node, ())
            return bool(names) and all(name.name == expected for name in names)

        def _function(
            self, node: t.Infra.Cst.CSTNode
        ) -> t.Infra.Cst.FunctionDef | None:
            while parent := self.get_metadata(ParentNodeProvider, node, None):
                if isinstance(parent, c.Infra.Cst.FunctionDef):
                    return parent
                node = parent
            return None

        def _config_package(self, node: t.Infra.Cst.BaseExpression) -> str | None:
            if (
                isinstance(node, c.Infra.Cst.Call)
                and self._qualified(node.func, "builtins.str")
                and len(node.args) == 1
            ):
                return self._config_package(node.args[0].value)
            if isinstance(node, c.Infra.Cst.Attribute):
                return self._config_package(node.value)
            if not isinstance(node, c.Infra.Cst.Name):
                return None
            if self.bindings.get(node.value) != 1:
                return None
            names = self.get_metadata(QualifiedNameProvider, node, ())
            packages: set[str] = set()
            for name in names:
                if name.source is QualifiedNameSource.IMPORT and name.name.endswith(
                    ".config",
                ):
                    packages.add(name.name.removesuffix(".config"))
                elif (function := self._function(node)) is not None:
                    package = self.aliases.get((name.name, function))
                    if package is not None:
                        packages.add(package)
            return next(iter(packages)) if len(packages) == 1 else None

        @override
        def visit_Assign(self, node: t.Infra.Cst.Assign) -> None:
            parent = self.get_metadata(ParentNodeProvider, node)
            if not isinstance(parent, c.Infra.Cst.SimpleStatementLine):
                return
            block = self.get_metadata(ParentNodeProvider, parent)
            if not isinstance(block, c.Infra.Cst.IndentedBlock):
                return
            function = self.get_metadata(ParentNodeProvider, block, None)
            if not isinstance(function, c.Infra.Cst.FunctionDef):
                return
            package = self._config_package(node.value)
            for target in node.targets:
                if not isinstance(target.target, c.Infra.Cst.Name):
                    continue
                for name in self.get_metadata(QualifiedNameProvider, target.target, ()):
                    key = (name.name, function)
                    if package is None:
                        self.aliases.pop(key, None)
                    else:
                        self.aliases[key] = package

        def _read(
            self, key: t.Infra.Cst.BaseExpression, method: str
        ) -> t.Infra.Cst.Call:
            package = self._config_package(key)
            if package is None:
                msg = "environment key lacks unambiguous typed-config provenance"
                raise ValueError(msg)
            self.packages.add(package)
            return cst.Call(
                cst.Attribute(cst.Name("settings"), cst.Name(method)),
                (cst.Arg(key),),
            )

        @override
        def leave_Call(
            self,
            original_node: t.Infra.Cst.Call,
            updated_node: t.Infra.Cst.Call,
        ) -> t.Infra.Cst.BaseExpression:
            if not self._qualified(original_node.func, "os.environ.get"):
                return updated_node
            if (
                len(original_node.args) != 1
                or original_node.args[0].keyword is not None
                or original_node.args[0].star
            ):
                msg = (
                    "dynamic environment lookup has an unsupported default or argument"
                )
                raise ValueError(msg)
            return self._read(original_node.args[0].value, "env_lookup")

        @override
        def leave_Subscript(
            self,
            original_node: t.Infra.Cst.Subscript,
            updated_node: t.Infra.Cst.Subscript,
        ) -> t.Infra.Cst.BaseExpression:
            if not self._qualified(original_node.value, "os.environ"):
                return updated_node
            if len(original_node.slice) != 1 or not isinstance(
                original_node.slice[0].slice,
                c.Infra.Cst.Index,
            ):
                msg = "dynamic environment lookup requires a single key"
                raise ValueError(msg)
            parent = self.get_metadata(ParentNodeProvider, original_node)
            if isinstance(
                parent,
                c.Infra.Cst.AssignTarget | c.Infra.Cst.Del | c.Infra.Cst.AugAssign,
            ):
                msg = "environment mutation is not a settings lookup"
                raise TypeError(msg)
            return self._read(original_node.slice[0].slice.value, "env_required")

    @classmethod
    def _plan_dynamic_environment(
        cls,
        sources: t.MappingKV[Path, str],
        selected: frozenset[Path],
        *,
        source_project: p.Infra.RopeProject,
        owner_context: Callable[[Path], t.Triple[str, str, m.Infra.CodegenConfigSpec]],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:

        def rewrite(_path: Path, source: str) -> t.Infra.TransformResult:
            del _path
            tree = ast.parse(source)
            bindings = Counter(
                name for node in ast.walk(tree) for name in cls.bound_identifiers(node)
            )
            transformer = cls._EnvironmentTransformer(bindings)
            updated = MetadataWrapper(cst.parse_module(source)).visit(transformer)
            if not transformer.packages:
                return source, ()
            if len(transformer.packages) != 1:
                msg = "dynamic environment reads resolve to competing settings owners"
                raise ValueError(msg)
            package = next(iter(transformer.packages))
            cls._require_settings_owner(
                package,
                sources,
                source_project=source_project,
                owner_context=owner_context,
            )
            for node in ast.walk(tree):
                if "settings" in cls.bound_identifiers(node) and not (
                    isinstance(node, ast.ImportFrom)
                    and node.module == package
                    and not node.level
                    and any(
                        alias.name == "settings" and alias.asname is None
                        for alias in node.names
                    )
                ):
                    msg = (
                        "dynamic environment migration conflicts "
                        "with a settings binding"
                    )
                    raise ValueError(msg)
                if isinstance(node, ast.ImportFrom) and any(
                    alias.name == "*" for alias in node.names
                ):
                    msg = (
                        "dynamic environment migration cannot resolve wildcard imports"
                    )
                    raise ValueError(msg)
            context = CodemodContext()
            AddImportsVisitor.add_needed_import(context, package, "settings")
            updated = AddImportsVisitor(context).transform_module(updated)
            return updated.code, (
                "routed config-owned environment keys through settings",
            )

        return cls._semantic_edits(
            tuple(
                item for item in cls._editable_sources(sources) if item[0] in selected
            ),
            rewrite,
        )

    @classmethod
    def _settings_owner_contexts(
        cls,
        repository_root: Path,
        codegen: m.Infra.CodegenConfigSpec,
        source_project: p.Infra.RopeProject,
        dependency_codegen: t.MappingKV[Path, m.Infra.CodegenInputs] | None,
    ) -> Callable[[Path], t.Triple[str, str, m.Infra.CodegenConfigSpec]]:
        """Own one phase's memoized metadata elections.

        Returns:
            A lazy settings-owner election bound to the original source authority.

        """
        contexts: dict[Path, t.Triple[str, str, m.Infra.CodegenConfigSpec]] = {}

        def owner_context(
            owner_root: Path,
        ) -> t.Triple[str, str, m.Infra.CodegenConfigSpec]:
            if owner_root not in contexts:
                contexts[owner_root] = cls._settings_owner_context(
                    owner_root,
                    source_project,
                    repository_root,
                    codegen,
                    dependency_codegen,
                )
            return contexts[owner_root]

        return owner_context

    @staticmethod
    def _settings_owner_context(
        owner_root: Path,
        source_project: p.Infra.RopeProject,
        repository_root: Path,
        codegen: m.Infra.CodegenConfigSpec,
        dependency_codegen: t.MappingKV[Path, m.Infra.CodegenInputs] | None,
    ) -> t.Triple[str, str, m.Infra.CodegenConfigSpec]:
        """Read the namespace and validate the exact policy inputs of one owner.

        Returns:
            The declared distribution, package and original policy by reference.

        Raises:
            ValueError: A supplied policy belongs to another root or epoch.

        """
        payload = FlextInfraUtilitiesPyprojectConform.pyproject_payload(
            owner_root / c.PYPROJECT_FILENAME, source_project=source_project
        )
        project_name = FlextInfraUtilitiesPyprojectConform.project_name_from_payload(
            owner_root, payload
        )
        package_name = FlextInfraUtilitiesPyprojectConform.project_package_name(
            owner_root, source_project=source_project
        )
        if owner_root == repository_root.resolve():
            return project_name, package_name, codegen
        captured = (
            dependency_codegen.get(owner_root)
            if dependency_codegen is not None
            else None
        )
        if captured is None:
            captured = FlextInfraUtilitiesProjectManagedArtifacts.load_codegen_inputs(
                owner_root, source_project=source_project
            ).unwrap()
        layers = FlextInfraConfig.config_layer_paths_for_repository(
            owner_root, filename=c.Infra.CODEGEN_CONFIG_FILENAME
        )
        if tuple(state.path for state in captured.sources) != tuple(
            dict.fromkeys(layers)
        ):
            msg = f"settings owner policy belongs to another root: {owner_root}"
            raise ValueError(msg)
        for state in captured.sources:
            if (
                source_project.source_state(
                    state.path, required=state.content is not None
                )
                != state
            ):
                msg = f"settings owner configuration changed: {state.path}"
                raise ValueError(msg)
        return project_name, package_name, captured.spec

    @staticmethod
    def _require_settings_owner(
        package: str,
        sources: t.MappingKV[Path, str],
        *,
        source_project: p.Infra.RopeProject,
        owner_context: Callable[[Path], t.Triple[str, str, m.Infra.CodegenConfigSpec]],
    ) -> None:
        """Require the destination settings API to exist in the source inventory.

        Raises:
            ValueError: If dynamic environment migration requires one declared settings
                owner; or if settings owner lacks optional/required dynamic environment
                reads.

        """
        owners: list[str] = []
        for path, source in sources.items():
            if path.parent.name != package.rsplit(".", maxsplit=1)[-1]:
                continue
            owner_root = FlextInfraUtilitiesDiscovery.project_root(
                path, source_project=source_project
            )
            if owner_root is None:
                msg = f"settings source has no declared owning project: {path}"
                raise ValueError(msg)
            project_name, package_name, owner_codegen = owner_context(owner_root)
            if package_name != package:
                continue
            if (
                FlextInfraUtilitiesCodegenNamespace.runtime_singleton_export(
                    path.name,
                    project_name=project_name,
                    codegen=owner_codegen,
                )
                == "settings"
            ):
                owners.append(source)
        if len(owners) != 1:
            msg = (
                f"dynamic environment migration requires one "
                f"declared settings owner: {package}"
            )
            raise ValueError(msg)
        methods = {
            node.name
            for node in ast.walk(ast.parse(owners[0]))
            if isinstance(node, ast.FunctionDef)
        }
        if not {"env_lookup", "env_required"} <= methods:
            msg = (
                f"settings owner lacks optional/required "
                f"dynamic environment reads: {package}"
            )
            raise ValueError(msg)


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverDynamicEnvironment"]
