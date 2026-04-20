"""Guard 1 — ROPE-backed import cycle detector.

Builds a module import graph using rope's semantic import resolution
(which correctly handles ``if TYPE_CHECKING:`` blocks, ``__init__.py``
re-exports, and relative imports) and runs Tarjan's SCC algorithm.
Any strongly-connected component with more than one module is a
runtime-import cycle and blocks the validate gate.

Mandate: This is a flext-infra detector and is 100% ROPE-based per the
ROPE/beartype mandate; raw ``ast`` / ``libcst`` source analysis is
forbidden in flext-infra detectors.

Architecture: flext-infra validate layer — consumes
``u.Infra`` Rope boundary helpers.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    MutableMapping,
    MutableSequence,
    Sequence,
)
from pathlib import Path
from typing import ClassVar, override

from flext_infra import m, p, r, s, t, u


class FlextInfraValidateImportCycles(s[bool]):
    """Detects runtime import cycles using rope's semantic import resolver.

    Guard 1 of the circular-import defense-in-depth suite. Unlike a raw
    AST walker, rope correctly excludes ``if TYPE_CHECKING:`` imports
    from the runtime graph, so this validator only flags imports that
    actually execute at module load time.
    """

    _MIN_CYCLE_SIZE: ClassVar[int] = 2

    def build_report(
        self,
        workspace_root: Path,
    ) -> p.Result[m.Infra.ValidationReport]:
        """Scan ``workspace_root`` for runtime import cycles via rope.

        Args:
            workspace_root: Path under which to open a rope Project.

        Returns:
            r with ValidationReport listing each cyclic SCC as a violation.

        """
        try:
            graph = self._build_graph(workspace_root)
        except OSError as exc:
            return r[m.Infra.ValidationReport].fail(
                f"import-cycles scan failed: {exc}",
            )
        cycles = tuple(
            scc for scc in self._tarjan(graph) if len(scc) >= self._MIN_CYCLE_SIZE
        )
        violations: MutableSequence[str] = [
            "cycle: " + " -> ".join(sorted(scc)) for scc in cycles
        ]
        passed = not violations
        summary = (
            f"no runtime import cycles (scanned {len(graph)} modules)"
            if passed
            else f"found {len(cycles)} runtime import cycle(s) across {len(graph)} modules"
        )
        return r[m.Infra.ValidationReport].ok(
            m.Infra.ValidationReport(
                passed=passed,
                violations=violations,
                summary=summary,
            ),
        )

    def _build_graph(
        self,
        workspace_root: Path,
    ) -> MutableMapping[str, set[str]]:
        """Build ``{module_name: {imported_modules}}`` via rope."""
        graph: MutableMapping[str, set[str]] = {}
        with u.Infra.open_project(workspace_root) as project:
            for resource in u.Infra.python_resources(project):
                module_name = self._module_name_for(project, resource)
                if module_name is None:
                    continue
                graph.setdefault(module_name, set())
                module_imports = u.Infra.get_module_imports(
                    project,
                    resource,
                )
                if module_imports is None:
                    continue
                for imported_name in self._iter_imported_modules(module_imports):
                    graph[module_name].add(imported_name)
        return graph

    def _module_name_for(
        self,
        project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> str | None:
        """Resolve a rope resource to its fully-qualified module name."""
        try:
            pymodule = u.Infra.get_pymodule(project, resource)
        except u.Infra.RUNTIME_ERRORS:
            return None
        except TypeError:
            return None
        try:
            name = pymodule.get_name()
        except (AttributeError, TypeError):
            name = None
        if isinstance(name, str) and name:
            return name
        resource_path = resource.path
        parts = Path(resource_path).with_suffix("").parts
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        return ".".join(parts) if parts else None

    def _iter_imported_modules(
        self,
        module_imports: t.Infra.RopeModuleImports,
    ) -> Sequence[str]:
        """Extract imported module names from the boundary import-info collection.

        Rope's parser already excludes ``if TYPE_CHECKING:`` blocks and
        resolves relative imports to absolute module names.
        """
        return u.Infra.imported_module_paths(module_imports)

    def _tarjan(
        self,
        graph: MutableMapping[str, set[str]],
    ) -> Sequence[Sequence[str]]:
        """Tarjan's SCC over ``graph``; returns each SCC as a list of module names."""
        index_counter = [0]
        stack: list[str] = []
        lowlink: dict[str, int] = {}
        index: dict[str, int] = {}
        on_stack: dict[str, bool] = {}
        result: list[list[str]] = []

        def strongconnect(node: str) -> None:
            index[node] = index_counter[0]
            lowlink[node] = index_counter[0]
            index_counter[0] += 1
            stack.append(node)
            on_stack[node] = True
            for successor in graph.get(node, set()):
                if successor not in index:
                    strongconnect(successor)
                    lowlink[node] = min(lowlink[node], lowlink[successor])
                elif on_stack.get(successor):
                    lowlink[node] = min(lowlink[node], index[successor])
            if lowlink[node] == index[node]:
                scc: list[str] = []
                while True:
                    top = stack.pop()
                    on_stack[top] = False
                    scc.append(top)
                    if top == node:
                        break
                result.append(scc)

        for node in list(graph):
            if node not in index:
                strongconnect(node)
        return result

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the cycle-detection CLI flow using ``self.workspace_root``."""
        report_result = self.build_report(self.workspace_root)
        if report_result.failure:
            return r[bool].fail(
                report_result.error or "import-cycles validation failed",
            )
        report = report_result.unwrap()
        return r[bool].ok(True) if report.passed else r[bool].fail(report.summary)


__all__: t.StrSequence = ["FlextInfraValidateImportCycles"]
