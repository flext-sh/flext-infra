"""Route config-owned dynamic environment keys through their settings owner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections import Counter
from collections.abc import Mapping, MutableMapping
from typing import TYPE_CHECKING

from flext_infra import FlextInfraConfig, c, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesProjectManagedArtifacts,
)
from flext_infra._utilities._pyproject.conform import (
    FlextInfraUtilitiesPyprojectConform,
)
from flext_infra._utilities._rope._analysis.asthelpers import (
    FlextInfraUtilitiesRopeAnalysisAstHelpers,
)
from flext_infra._utilities._rope.rope_module_patch import (
    FlextInfraUtilitiesRopeModulePatch,
)
from flext_infra._utilities._rope.rope_runtime_modules import (
    FlextInfraUtilitiesRopeRuntimeModules,
)
from flext_infra._utilities._rope.rope_runtime_refactors import (
    FlextInfraUtilitiesRopeRuntimeRefactors,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticCutoverBindings,
    FlextInfraUtilitiesSemanticCutoverEdits,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


class FlextInfraUtilitiesSemanticCutoverDynamicEnvironment(
    FlextInfraUtilitiesSemanticCutoverEdits,
    FlextInfraUtilitiesSemanticCutoverBindings,
):
    """Require resolved OS imports and same-function config provenance."""

    class _EnvironmentPlanner(FlextInfraUtilitiesRopeAnalysisAstHelpers):
        """Prove config provenance and plan settings rerouting for one module."""

        def __init__(
            self,
            project: p.Infra.RopeProject,
            module: p.Infra.RopeParsedModule,
            source: str,
            bindings: Mapping[str, int],
        ) -> None:
            runtime = FlextInfraUtilitiesRopeRuntimeModules
            self.runtime = runtime
            self.module = module
            self.source = source
            self.bindings = bindings
            self.aliases: MutableMapping[tuple[str, int], str | None] = {}
            self.packages: set[str] = set()
            self.edits: list[m.Infra.SourceRewrite] = []
            self.environ = runtime.qualified_name(project, "os.environ")
            self.environ_get = runtime.qualified_name(project, "os.environ.get")
            self.text = runtime.qualified_name(project, "builtins.str")

        def plan(self) -> None:
            """Visit every environment read and alias in native tree order."""
            parents = self.ast_parent_map(self.require_module_tree())
            for node in ast.walk(self.require_module_tree()):
                self._visit_node(node, parents)

        def _visit_node(
            self,
            node: ast.AST,
            parents: Mapping[int, ast.AST],
        ) -> None:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                for statement in node.body:
                    if isinstance(statement, ast.Assign):
                        self._register_alias(node, statement)
            elif isinstance(node, ast.Call):
                self._plan_call(node, parents)
            elif isinstance(node, ast.Subscript):
                self._plan_subscript(node, parents)
            else:
                self._visit_mutation(node)

        def _visit_mutation(self, node: ast.AST) -> None:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    self._guard_mutation(target)
            elif isinstance(node, ast.AnnAssign | ast.AugAssign):
                self._guard_mutation(node.target)
            elif isinstance(node, ast.Delete):
                for target in node.targets:
                    self._guard_mutation(target)

        def require_module_tree(self) -> ast.Module:
            """Return the native module tree this planner was built from.

            Returns:
                The resulting ``ast.Module``.

            Raises:
                TypeError: If the native module exposes no module syntax tree.

            """
            tree = self.module.get_ast()
            if not isinstance(tree, ast.Module):
                msg = "dynamic environment analysis has no native module syntax"
                raise TypeError(msg)
            return tree

        def _resolved(self, node: ast.expr) -> p.Infra.RopePyName | None:
            span = self.node_span_offsets(self.source, node)
            if span is None:
                return None
            scope = self.runtime.scope_at(
                self.module,
                span[0],
                declaration_line=node.lineno,
            )
            return self.runtime.resolve_symbol(scope, node)

        @staticmethod
        def _enclosing_function(
            node: ast.AST,
            parents: Mapping[int, ast.AST],
        ) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
            current = parents.get(id(node))
            while current is not None:
                if isinstance(current, ast.FunctionDef | ast.AsyncFunctionDef):
                    return current
                current = parents.get(id(current))
            return None

        def _config_package(
            self,
            node: ast.expr,
            function: ast.FunctionDef | ast.AsyncFunctionDef | None,
        ) -> str | None:
            if (
                isinstance(node, ast.Call)
                and len(node.args) == 1
                and (resolved := self._resolved(node.func)) is not None
                and self.runtime.same_name(resolved, self.text)
            ):
                return self._config_package(node.args[0], function)
            if isinstance(node, ast.Attribute):
                return self._config_package(node.value, function)
            if not isinstance(node, ast.Name) or self.bindings.get(node.id) != 1:
                return None
            return self._name_package(node, function)

        def _name_package(
            self,
            node: ast.Name,
            function: ast.FunctionDef | ast.AsyncFunctionDef | None,
        ) -> str | None:
            binding = self._resolved(node)
            if (
                isinstance(binding, p.Infra.RopeImportedName)
                and binding.imported_name == "config"
                and binding.imported_module.module_name is not None
            ):
                return binding.imported_module.module_name
            if function is None:
                return None
            return self.aliases.get((node.id, id(function)))

        def _register_alias(
            self,
            function: ast.FunctionDef | ast.AsyncFunctionDef,
            statement: ast.Assign,
        ) -> None:
            package = self._config_package(statement.value, function)
            for target in statement.targets:
                if isinstance(target, ast.Name):
                    self.aliases[target.id, id(function)] = package

        def _plan_call(
            self,
            node: ast.Call,
            parents: Mapping[int, ast.AST],
        ) -> None:
            resolved = self._resolved(node.func)
            if resolved is None or not self.runtime.same_name(
                resolved,
                self.environ_get,
            ):
                return
            if (
                len(node.args) != 1
                or node.keywords
                or isinstance(node.args[0], ast.Starred)
            ):
                msg = (
                    "dynamic environment lookup has an unsupported default or argument"
                )
                raise ValueError(msg)
            self._read(node, node.args[0], "env_lookup", parents)

        @staticmethod
        def _single_key(slice_node: ast.expr) -> bool:
            """Return whether one subscript reads exactly one environment key."""
            return not isinstance(slice_node, ast.Tuple | ast.Slice)

        def _plan_subscript(
            self,
            node: ast.Subscript,
            parents: Mapping[int, ast.AST],
        ) -> None:
            resolved = self._resolved(node.value)
            if resolved is None or not self.runtime.same_name(resolved, self.environ):
                return
            if not self._single_key(node.slice):
                msg = "dynamic environment lookup requires a single key"
                raise ValueError(msg)
            if isinstance(
                parents.get(id(node)),
                ast.Assign | ast.AnnAssign | ast.AugAssign | ast.Delete,
            ):
                msg = "environment mutation is not a settings lookup"
                raise TypeError(msg)
            self._read(node, node.slice, "env_required", parents)

        def _guard_mutation(self, target: ast.expr | None) -> None:
            if (
                isinstance(target, ast.Subscript)
                and (resolved := self._resolved(target.value)) is not None
                and self.runtime.same_name(resolved, self.environ)
            ):
                msg = "environment mutation is not a settings lookup"
                raise TypeError(msg)

        def _read(
            self,
            node: ast.expr,
            key: ast.expr,
            method: str,
            parents: Mapping[int, ast.AST],
        ) -> None:
            function = self._enclosing_function(key, parents)
            package = self._config_package(key, function)
            if package is None:
                msg = "environment key lacks unambiguous typed-config provenance"
                raise ValueError(msg)
            self.packages.add(package)
            node_span = self.node_span_offsets(self.source, node)
            key_span = self.node_span_offsets(self.source, key)
            if node_span is None or key_span is None:
                msg = "dynamic environment read has no complete source span"
                raise TypeError(msg)
            self.edits.append(
                m.Infra.SourceRewrite(
                    start=node_span[0],
                    end=node_span[1],
                    text=(
                        f"settings.{method}({self.source[key_span[0] : key_span[1]]})"
                    ),
                )
            )

    @classmethod
    def _plan_dynamic_environment(
        cls,
        sources: Mapping[Path, str],
        selected: frozenset[Path],
        *,
        source_project: p.Infra.RopeProject,
        owner_context: Callable[[Path], tuple[str, str, m.Infra.CodegenConfigSpec]],
    ) -> p.Result[tuple[m.Infra.SemanticMigrationEdit, ...]]:

        def rewrite(path: Path, source: str) -> t.Infra.TransformResult:
            tree = ast.parse(source)
            bindings = Counter(
                name for node in ast.walk(tree) for name in cls.bound_identifiers(node)
            )
            runtime = FlextInfraUtilitiesRopeRuntimeModules
            module = runtime.build_string_module(
                source_project,
                source,
                resource=runtime.file_resource_at(source_project, path),
            )
            planner = cls._EnvironmentPlanner(
                source_project,
                module,
                source,
                bindings,
            )
            planner.plan()
            if not planner.packages:
                return source, ()
            if len(planner.packages) != 1:
                msg = "dynamic environment reads resolve to competing settings owners"
                raise ValueError(msg)
            package = next(iter(planner.packages))
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
            updated = FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
                runtime.file_resource_at(source_project, path),
                source,
                tuple(planner.edits),
            ).new_contents
            with FlextInfraUtilitiesRopeModulePatch.candidate_module(
                module, updated
            ) as candidate:
                updated = FlextInfraUtilitiesRopeModulePatch.ensure_from_import(
                    candidate, module=package, name="settings"
                )
            return updated, ("routed config-owned environment keys through settings",)

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
        dependency_codegen: Mapping[Path, m.Infra.CodegenInputs] | None,
    ) -> Callable[[Path], tuple[str, str, m.Infra.CodegenConfigSpec]]:
        """Own one phase's memoized metadata elections.

        Returns:
            A lazy settings-owner election bound to the original source authority.

        """
        contexts: dict[Path, tuple[str, str, m.Infra.CodegenConfigSpec]] = {}

        def owner_context(
            owner_root: Path,
        ) -> tuple[str, str, m.Infra.CodegenConfigSpec]:
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
        dependency_codegen: Mapping[Path, m.Infra.CodegenInputs] | None,
    ) -> tuple[str, str, m.Infra.CodegenConfigSpec]:
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
        sources: Mapping[Path, str],
        *,
        source_project: p.Infra.RopeProject,
        owner_context: Callable[[Path], tuple[str, str, m.Infra.CodegenConfigSpec]],
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
