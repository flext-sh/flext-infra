from __future__ import annotations

import sys
from graphlib import CycleError, TopologicalSorter
from pathlib import Path

from flext_core import r
from pydantic import TypeAdapter, ValidationError

from flext_infra import c, m, u

from .import_collector import ImportCollector


class DependencyAnalyzer:
    """Build inter-project import graphs from workspace source trees."""

    def __init__(self, workspace_root: Path) -> None:
        """Initialize analyzer for the given workspace root."""
        super().__init__()
        self._workspace_root = workspace_root.resolve()
        self._stdlib_roots = set(sys.stdlib_module_names)
        self._projects = self._discover_projects()
        self._pkg_index = self._build_package_index(self._projects)
        self._graph_cache: dict[str, list[str]] | None = None

    def build_import_graph(self) -> r[dict[str, list[str]]]:
        """Build and cache the inter-project import graph."""
        if self._graph_cache is not None:
            return r[dict[str, list[str]]].ok(self._graph_cache)
        graph: dict[str, set[str]] = {p.name: set() for p in self._projects}
        for project in self._projects:
            files = self._find_import_candidate_files(project)
            for fp in files:
                parsed = self._parse_imports(fp)
                if parsed.is_failure:
                    continue
                file_data: m.Infra.FileImportData = parsed.value
                for mod_root in file_data.imported_modules:
                    if mod_root in self._stdlib_roots:
                        continue
                    dep = self._pkg_index.get(mod_root)
                    if dep and dep != project.name:
                        graph[project.name].add(dep)
        ordered = {k: sorted(v) for k, v in sorted(graph.items())}
        self._graph_cache = ordered
        return r[dict[str, list[str]]].ok(ordered)

    def find_consumers(self, class_name: str) -> r[list[Path]]:
        """Find all files importing the given class name."""
        consumers: set[Path] = set()
        for project in self._projects:
            for fp in self._find_import_candidate_files(project):
                parsed = self._parse_imports(fp)
                if parsed.is_failure:
                    continue
                file_data = parsed.value
                if class_name in file_data.imported_symbols:
                    consumers.add(fp)
        return r[list[Path]].ok(sorted(consumers))

    def determine_transformation_order(self) -> r[list[str]]:
        """Return topologically sorted project order."""
        graph_result = self.build_import_graph()
        if graph_result.is_failure:
            return r[list[str]].fail(graph_result.error or "graph build failed")
        graph: dict[str, list[str]] = graph_result.value
        if not graph:
            return r[list[str]].ok([])
        try:
            sorter: TopologicalSorter[str] = TopologicalSorter(graph)
            return r[list[str]].ok(list(sorter.static_order()))
        except CycleError:
            return r[list[str]].ok(sorted(graph))

    def _discover_projects(self) -> list[m.Infra.RefactorProjectInfo]:
        projects: list[m.Infra.RefactorProjectInfo] = []
        for candidate in sorted(self._workspace_root.iterdir()):
            if not candidate.is_dir() or candidate.name.startswith("."):
                continue
            src = candidate / c.Infra.Paths.DEFAULT_SRC_DIR
            if not src.is_dir():
                continue
            projects.append(
                m.Infra.RefactorProjectInfo(
                    name=candidate.name,
                    path=candidate,
                    src_path=src,
                    package_roots=self._discover_package_roots(src),
                ),
            )
        return projects

    def _discover_package_roots(self, src_path: Path) -> set[str]:
        roots: set[str] = set()
        for pkg_dir in src_path.iterdir():
            if pkg_dir.name.startswith("."):
                continue
            if pkg_dir.is_dir() and (pkg_dir / c.Infra.Files.INIT_PY).is_file():
                roots.add(pkg_dir.name)
            elif (
                pkg_dir.is_file()
                and pkg_dir.suffix == c.Infra.Extensions.PYTHON
                and (pkg_dir.stem != "__init__")
            ):
                roots.add(pkg_dir.stem)
        return roots

    def _build_package_index(
        self,
        projects: list[m.Infra.RefactorProjectInfo],
    ) -> dict[str, str]:
        idx: dict[str, str] = {}
        for proj in projects:
            for pkg in proj.package_roots:
                _ = idx.setdefault(pkg, proj.name)
        return idx

    def _find_import_candidate_files(
        self,
        project: m.Infra.RefactorProjectInfo,
    ) -> list[Path]:
        grep_files = self._scan_import_files_with_ast_grep(project.src_path)
        if grep_files.is_success and grep_files.value:
            path_set: set[Path] = grep_files.value
            return sorted(path_set)
        files_result = u.Infra.iter_python_files(
            workspace_root=self._workspace_root,
            project_roots=[project.path],
            include_tests=False,
            include_examples=False,
            include_scripts=False,
            src_dirs=frozenset({"src"}),
        )
        return files_result.fold(
            on_failure=lambda _: list[Path](),
            on_success=lambda v: v,
        )

    def _scan_import_files_with_ast_grep(self, src_path: Path) -> r[set[Path]]:
        files: set[Path] = set()
        for pattern in ("import $MODULE", "from $MODULE import $$$"):
            result = self._run_ast_grep(src_path, pattern)
            if result.is_failure:
                return r[set[Path]].fail(result.error or "ast-grep failed")
            entries: list[m.Infra.AstGrepMatchEnvelope] = result.value
            for entry in entries:
                fp = Path(entry.file)
                if not fp.is_absolute():
                    fp = (src_path / fp).resolve()
                if fp.suffix == c.Infra.Extensions.PYTHON:
                    files.add(fp)
        return r[set[Path]].ok(files)

    def _run_ast_grep(
        self,
        src_path: Path,
        pattern: str,
    ) -> r[list[m.Infra.AstGrepMatchEnvelope]]:
        cmd = [
            "sg",
            "--pattern",
            pattern,
            "--lang",
            c.Infra.Toml.PYTHON,
            "--json",
            str(src_path),
        ]
        capture = u.Infra.capture(cmd)
        if capture.is_failure:
            return r[list[m.Infra.AstGrepMatchEnvelope]].fail(
                capture.error or "capture failed",
            )
        if not capture.value:
            return r[list[m.Infra.AstGrepMatchEnvelope]].ok([])
        try:
            json_raw: str | bytes | bytearray = capture.value
            envelopes: list[m.Infra.AstGrepMatchEnvelope] = TypeAdapter(
                list[m.Infra.AstGrepMatchEnvelope],
            ).validate_json(
                json_raw,
            )
            return r[list[m.Infra.AstGrepMatchEnvelope]].ok(envelopes)
        except ValidationError as exc:
            return r[list[m.Infra.AstGrepMatchEnvelope]].fail(str(exc))

    def _parse_imports(self, file_path: Path) -> r[m.Infra.FileImportData]:
        tree = u.Infra.parse_module_cst(file_path)
        if tree is None:
            return r[m.Infra.FileImportData].fail(f"{file_path}: parse_failed")
        col = ImportCollector()
        _ = tree.visit(col)
        return r[m.Infra.FileImportData].ok(
            m.Infra.FileImportData(
                imported_modules=col.imported_modules,
                imported_symbols=col.imported_symbols,
            ),
        )
