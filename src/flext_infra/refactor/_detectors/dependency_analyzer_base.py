"""Analyzer for building inter-project import dependency graphs.

This module analyzes import statements across projects in a workspace to build
import dependency graphs and determine transformation order based on topological
sorting.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

from flext_core import r
from pydantic import TypeAdapter, ValidationError

from flext_infra import c, m, u

from .import_collector import ImportCollector


class DependencyAnalyzer:
    """Analyzer for inter-project import dependency graphs in workspaces.

    Discovers projects within a workspace, indexes their packages, and builds
    import dependency graphs by analyzing import statements across source files.
    Supports topological sorting for transformation order determination.
    """

    def __init__(self, workspace_root: Path) -> None:
        """Initialize the DependencyAnalyzer.

        Args:
            workspace_root: Root directory of the workspace containing projects.

        """
        super().__init__()
        self._workspace_root = workspace_root.resolve()
        self._stdlib_roots = set(sys.stdlib_module_names)
        self._projects = self._discover_projects()
        self._pkg_index = self._build_package_index(self._projects)

    def _discover_projects(self) -> Sequence[m.Infra.RefactorProjectInfo]:
        """Discover all projects in the workspace.

        Returns:
            List of RefactorProjectInfo for each discovered project.

        """
        projects: MutableSequence[m.Infra.RefactorProjectInfo] = []
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
        """Discover package root names in a source directory.

        Args:
            src_path: Path to the source directory to scan.

        Returns:
            Set of package root names found.

        """
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
        projects: Sequence[m.Infra.RefactorProjectInfo],
    ) -> Mapping[str, str]:
        """Build a mapping from package names to owning project names.

        Args:
            projects: List of projects to index.

        Returns:
            Dict mapping package name to project name.

        """
        idx: MutableMapping[str, str] = {}
        for proj in projects:
            for pkg in proj.package_roots:
                _ = idx.setdefault(pkg, proj.name)
        return idx

    def _find_import_candidate_files(
        self,
        project: m.Infra.RefactorProjectInfo,
    ) -> Sequence[Path]:
        """Find all Python files with import statements in a project.

        Args:
            project: The project to scan for import statements.

        Returns:
            Sorted list of file paths containing imports.

        """
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
            on_failure=lambda _: [],
            on_success=lambda v: v,
        )

    def _scan_import_files_with_ast_grep(self, src_path: Path) -> r[set[Path]]:
        """Scan source directory for files with import statements using ast-grep.

        Args:
            src_path: Path to the source directory to scan.

        Returns:
            Result containing set of file paths with import statements.

        """
        files: set[Path] = set()
        for pattern in ("import $MODULE", "from $MODULE import $$$"):
            result = self._run_ast_grep(src_path, pattern)
            if result.is_failure:
                return r[set[Path]].fail(result.error or "ast-grep failed")
            entries: Sequence[m.Infra.AstGrepMatchEnvelope] = result.value
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
    ) -> r[Sequence[m.Infra.AstGrepMatchEnvelope]]:
        """Run ast-grep with the given pattern on source directory.

        Args:
            src_path: Path to the source directory to scan.
            pattern: The ast-grep pattern to match.

        Returns:
            Result containing list of ast-grep match envelopes.

        """
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
            return r[Sequence[m.Infra.AstGrepMatchEnvelope]].fail(
                capture.error or "capture failed",
            )
        if not capture.value:
            return r[Sequence[m.Infra.AstGrepMatchEnvelope]].ok([])
        try:
            json_raw: str | bytes | bytearray = capture.value
            envelopes: Sequence[m.Infra.AstGrepMatchEnvelope] = TypeAdapter(
                Sequence[m.Infra.AstGrepMatchEnvelope],
            ).validate_json(
                json_raw,
            )
            return r[Sequence[m.Infra.AstGrepMatchEnvelope]].ok(envelopes)
        except ValidationError as exc:
            return r[Sequence[m.Infra.AstGrepMatchEnvelope]].fail(str(exc))

    def _parse_imports(self, file_path: Path) -> r[m.Infra.FileImportData]:
        """Parse a Python file and extract its import information.

        Args:
            file_path: Path to the Python file to parse.

        Returns:
            Result containing FileImportData with imported modules and symbols.

        """
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
