"""Lazy-init ``__init__.py`` generator (PEP 562).

Auto-discovers exports from sibling ``.py`` files and generates clean
lazy-loading ``__init__.py`` files using ``flext_core.lazy``.

The generator **never** reads existing ``__init__.py`` content for exports
or import mappings.  It discovers everything by scanning sibling ``.py``
files' ``__all__`` and AST definitions.  You can DELETE every
``__init__.py`` and regenerate them perfectly from scratch.

Processes directories bottom-up (deepest first) so child packages are
generated before parents, and parent packages can include child exports.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import contextlib
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar, override

from flext_core import r, s

from flext_infra import (
    FlextInfraCodegenGeneration,
    c,
    output,
    t,
    u,
)

# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------


class FlextInfraCodegenLazyInit(s[int]):
    """Generates ``__init__.py`` with PEP 562 lazy imports.

    Scans sibling ``.py`` files in each package directory, discovers their
    exports via ``__all__`` or AST scanning, and generates clean lazy-loading
    ``__init__.py`` files.  Processes bottom-up so child packages are
    generated before parents.
    """

    def __init__(self, workspace_root: Path) -> None:
        """Initialize lazy init generator with workspace root."""
        super().__init__(
            config_type=None,
            config_overrides=None,
            initial_context=None,
            subproject=None,
            services=None,
            factories=None,
            resources=None,
            container_overrides=None,
            wire_modules=None,
            wire_packages=None,
            wire_classes=None,
        )
        self._root: Path = workspace_root

    _TYPEVAR_CALL_NAMES: ClassVar[frozenset[str]] = frozenset({
        "TypeVar",
        "ParamSpec",
        "TypeVarTuple",
    })

    @override
    def execute(self) -> r[int]:
        """Execute the lazy-init generation process."""
        return r[int].ok(self.run(check_only=False))

    def run(self, *, check_only: bool = False) -> int:
        """Process all package directories in the workspace.

        Dynamically discovers ALL package directories with Python files
        (including but not limited to ``src/``, ``tests/``, ``examples/``,
        ``scripts/``, ``docs/``, ``tools/``, etc.), processes them bottom-up
        (deepest first), and generates PEP 562 lazy-import ``__init__.py`` files.

        Args:
            check_only: If True, only report without writing.

        Returns the number of errors (0 = perfect).

        """
        pkg_dirs = self._find_package_dirs()
        total = ok = errors = 0
        # Bottom-up: child exports computed before parents consume them
        dir_exports: MutableMapping[str, t.Infra.LazyImportMap] = {}

        for pkg_dir in pkg_dirs:
            total += 1
            result, exports = self._process_directory(
                pkg_dir,
                check_only=check_only,
                dir_exports=dir_exports,
            )
            if exports:
                dir_exports[str(pkg_dir)] = exports
            if result is None:
                continue
            if result < 0:
                errors += 1
            else:
                ok += 1

        # Phase 2: break circular imports in generated __init__.py files
        if not check_only:
            cycle_fixes = 0
            for pkg_dir in pkg_dirs:
                init_file = pkg_dir / "__init__.py"
                if not init_file.is_file():
                    continue
                modified, changes = u.Infra.break_import_cycles(pkg_dir)
                if modified:
                    for change in changes:
                        output.info(f"  CYCLE-FIX: {change}")
                    cycle_fixes += len(changes)
            if cycle_fixes:
                output.info(f"Cycle-fix: {cycle_fixes} circular imports resolved")

        output.info(
            f"Lazy-init summary: {ok} generated, {errors} errors"
            f" ({total} dirs scanned)",
        )
        return errors

    def _find_package_dirs(self) -> Sequence[Path]:
        """Find all package directories across every workspace project.

        Uses ``u.Infra.iter_python_files`` with automatic project discovery
        to scan ``src/``, ``tests/``, ``examples/``, ``scripts/`` in every
        project that has a ``pyproject.toml`` + ``Makefile``.

        Returns:
            Sorted by depth (deepest first) for bottom-up processing.

        """
        pkg_dirs: t.Infra.PathSet = set()
        files_result = u.Infra.iter_python_files(
            workspace_root=self._root,
        )
        if files_result.is_failure:
            return []
        files = files_result.value
        for py_file in files:
            if any(
                part.startswith(".") or part in {"vendor", "node_modules", ".venv"}
                for part in py_file.parts
            ):
                continue
            parent = py_file.parent
            if self._dir_has_py_files(parent):
                pkg_dirs.add(parent)
        return sorted(pkg_dirs, key=lambda p: len(p.parts), reverse=True)

    def _process_directory(
        self,
        pkg_dir: Path,
        *,
        check_only: bool,
        dir_exports: Mapping[str, t.Infra.LazyImportMap],
    ) -> t.Infra.LazyInitProcessResult:
        """Process a single directory to generate its ``__init__.py``.

        Args:
            pkg_dir: Directory to process.
            check_only: If True, count exports without writing.
            dir_exports: Pre-computed exports from child directories.

        Returns:
            ``(result_code, exports_dict)``.
            result_code is ``None`` if skipped, ``0`` if OK, ``<0`` on error.

        """
        init_path = pkg_dir / "__init__.py"
        current_pkg = u.Infra.infer_package(init_path)
        if not current_pkg:
            return (None, {})

        # 1. Read ONLY docstring from existing __init__.py
        docstring = self._read_existing_docstring(init_path)
        if not docstring:
            docstring = self._default_docstring(pkg_dir.name)

        # 2. Build lazy map from sibling .py files
        lazy_map = self._build_sibling_export_index(pkg_dir, current_pkg)

        # 3. Add exports from child subdirectories (already computed)
        self._merge_child_exports(pkg_dir, current_pkg, lazy_map, dir_exports)

        # 4. Handle __version__.py
        inline_constants, version_lazy = self._extract_version_exports(
            pkg_dir,
            current_pkg,
        )
        lazy_map.update(version_lazy)

        # 5. Handle single-letter aliases via ALIAS_TO_SUFFIX
        # IMPORTANT: Only generate single-letter aliases at root-level public packages.
        # Internal packages (_models, _utilities, _dispatcher, etc.) MUST NOT receive
        # short aliases — they conflict with the root namespace MRO (d, m, s, r, …).
        if not pkg_dir.name.startswith("_"):
            self._resolve_aliases(lazy_map, pkg_dir=pkg_dir)

        # 6. Remove infrastructure names (eagerly imported, not lazy)
        for infra_name in ("cleanup_submodule_namespace", "lazy_getattr"):
            lazy_map.pop(infra_name, None)

        # 6b. Detect TypeVars — must be eager, not lazy
        eager_tvars = frozenset(
            self._detect_eager_typevar_names(pkg_dir) & set(lazy_map),
        )

        # 7. Remove inline constants from lazy map (inlined directly)
        for k in inline_constants:
            lazy_map.pop(k, None)

        # 8. Build final exports list (includes both lazy and eager)
        exports = sorted(set(lazy_map) | set(inline_constants) | eager_tvars)
        if not exports:
            return (None, dict(lazy_map))

        if check_only:
            return (0, dict(lazy_map))

        # 9. Generate the __init__.py file
        return self._write_init(
            init_path,
            docstring,
            exports,
            lazy_map,
            inline_constants,
            current_pkg,
            eager_tvars,
        )

    def _write_init(
        self,
        init_path: Path,
        docstring: str,
        exports: t.StrSequence,
        lazy_map: t.Infra.LazyImportMap,
        inline_constants: t.StrMapping,
        current_pkg: str,
        eager_typevar_names: frozenset[str] = frozenset(),
    ) -> t.Infra.LazyInitWriteResult:
        """Write the generated ``__init__.py`` and run ruff fix."""
        try:
            generated = self._generate_file(
                docstring,
                exports,
                lazy_map,
                inline_constants,
                current_pkg,
                eager_typevar_names,
            )
            init_path.write_text(generated, encoding=c.Infra.Encoding.DEFAULT)
            self._run_ruff_fix(init_path)
        except (OSError, ValueError) as exc:
            output.error(f"generating {init_path}: {exc}")
            return (-1, dict(lazy_map))

        rel_path = (
            init_path.relative_to(self._root)
            if self._root in init_path.parents
            else init_path
        )
        output.info(f"  OK: {rel_path} — {len(exports)} exports")
        return (0, dict(lazy_map))

    # ---------------------------------------------------------------------------
    # Directory / package helpers
    # ---------------------------------------------------------------------------

    @staticmethod
    def _dir_has_py_files(pkg_dir: Path) -> bool:
        """Return True if directory has ``.py`` files besides ``__init__.py``."""
        return any(
            f.name != "__init__.py" and f.suffix == ".py"
            for f in pkg_dir.iterdir()
            if f.is_file()
        )

    # ---------------------------------------------------------------------------
    # Source-file scanning (the core of auto-discovery)
    # ---------------------------------------------------------------------------

    @staticmethod
    def _default_docstring(dir_name: str) -> str:
        """Generate a default module docstring from directory name."""
        label = dir_name.replace("_", " ").replace("-", " ").strip()
        return f'"""{label.capitalize()} package."""'

    @staticmethod
    def _read_existing_docstring(init_path: Path) -> str:
        """Read ONLY the docstring from an existing ``__init__.py``.

        This is the **only** thing we read from existing ``__init__.py`` files.
        Everything else is auto-discovered from sibling ``.py`` source files.
        """
        if not init_path.exists():
            return ""
        try:
            content = init_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        except OSError:
            return ""
        # NOTE: source text needed below - cannot delegate to u.Infra.parse_module_ast
        tree = u.Infra.parse_ast_from_source(content)
        if tree is None:
            return ""
        if (
            tree.body
            and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)
        ):
            ds = tree.body[0]
            return "\n".join(content.splitlines()[ds.lineno - 1 : ds.end_lineno])
        return ""

    @staticmethod
    def _build_sibling_export_index(
        pkg_dir: Path,
        current_pkg: str,
    ) -> t.Infra.MutableLazyImportMap:
        """Scan sibling ``.py`` files for exports (including nested submodules).

        For each non-private, non-dunder sibling ``.py`` file (at any depth):

        1. If it has ``__all__`` → use those names.
        2. If no ``__all__`` → scan AST for public classes/functions/assignments.

        Recursively discovers exports at unlimited hierarchy depth, including
        files in nested submodules (e.g., ``_context/_data.py``).
        Returns ``{export_name: (module_path, attr_name)}``.
        """
        index: t.Infra.MutableLazyImportMap = {}
        for py_file in sorted(pkg_dir.rglob("*.py")):
            if py_file.name in {"__init__.py", "__main__.py", "__version__.py"}:
                continue
            # Only filter underscore files in root dir, not in nested submodules
            rel_path = py_file.relative_to(pkg_dir)
            if len(rel_path.parts) == 1 and py_file.name.startswith("_"):
                continue
            if py_file.stem[0:1].isdigit():
                continue

            # Build full module path from relative path
            mod_parts = rel_path.with_suffix("").parts
            mod_stem = ".".join(mod_parts)
            mod_path = f"{current_pkg}.{mod_stem}" if current_pkg else mod_stem

            sibling_tree = u.Infra.parse_module_ast(py_file)
            if sibling_tree is None:
                output.warning(f"skipping {py_file.name}: parse failed")
                continue

            # Prefer __all__ when available
            has_all, all_exports = u.Infra.extract_exports(
                sibling_tree,
            )
            if has_all and all_exports:
                for name in all_exports:
                    if name not in index:
                        index[name] = (mod_path, name)
            else:
                FlextInfraCodegenLazyInit._scan_ast_public_defs(
                    sibling_tree,
                    mod_path,
                    index,
                )

        return index

    @staticmethod
    def _scan_ast_public_defs(
        tree: ast.Module,
        mod_path: str,
        index: t.Infra.MutableLazyImportMap,
    ) -> None:
        """Scan AST for public classes, functions, and assignments."""
        for node in ast.iter_child_nodes(tree):
            names: MutableSequence[str] = []
            match node:
                case ast.FunctionDef() | ast.AsyncFunctionDef() | ast.ClassDef():
                    names.append(node.name)
                case ast.Assign():
                    names.extend(
                        target.id
                        for target in node.targets
                        if isinstance(target, ast.Name)
                    )
                case ast.AnnAssign(target=ast.Name() as ann_target):
                    names.append(ann_target.id)
                case _:
                    pass
            for name in names:
                if not name.startswith("_"):
                    index[name] = (mod_path, name)

    @staticmethod
    def _detect_eager_typevar_names(pkg_dir: Path) -> t.Infra.StrSet:
        """Detect module-level TypeVar/ParamSpec names in typings.py.

        These MUST be exported eagerly (not via lazy __getattr__) because
        Python needs them available at class definition time for Generic[T].
        """
        typings_file = pkg_dir / "typings.py"
        if not typings_file.exists():
            return set()
        tree = u.Infra.parse_module_ast(typings_file)
        if tree is None:
            return set()
        names: t.Infra.StrSet = set()
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            if not (
                isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id in FlextInfraCodegenLazyInit._TYPEVAR_CALL_NAMES
            ):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    names.add(target.id)
        return names

    # ---------------------------------------------------------------------------
    # Child-directory export merging (bottom-up)
    # ---------------------------------------------------------------------------

    @staticmethod
    def _should_bubble_up(name: str) -> bool:
        """Check if an export should bubble up to the parent package.

        Filters out private names, entry points, and ALL_CAPS utility constants.
        """
        if name.startswith("_"):
            return False
        if name == "__init__":
            return False
        if name == "main":
            return False
        # Skip ALL_CAPS constants (e.g., BLUE, BOLD, SYM_ARROW)
        return not name.isupper()

    @staticmethod
    def _merge_child_exports(
        pkg_dir: Path,
        current_pkg: str,
        lazy_map: t.Infra.MutableLazyImportMap,
        dir_exports: Mapping[str, t.Infra.LazyImportMap],
    ) -> None:
        """Merge child subdirectory exports into parent's lazy map.

        For each immediate subdirectory that has computed exports,
        add their exports to the parent.  Also extracts re-exports
        from the child's __init__.py (e.g., _models._context re-exports
        FlextModelsContextData).  Sibling file exports take precedence
        over child exports.
        """
        for subdir in sorted(pkg_dir.iterdir()):
            if not subdir.is_dir() or subdir.name.startswith("."):
                continue
            subdir_key = str(subdir)
            if subdir_key not in dir_exports:
                continue
            if subdir.name != "__init__" and subdir.name not in lazy_map:
                submodule = (
                    f"{current_pkg}.{subdir.name}" if current_pkg else subdir.name
                )
                lazy_map[subdir.name] = (submodule, "")
            sub_exports = dir_exports[subdir_key]
            # Merge module-level exports from sibling .py files
            for name, (mod, attr) in sub_exports.items():
                if not FlextInfraCodegenLazyInit._should_bubble_up(name):
                    continue
                # Sibling file exports take precedence
                if name not in lazy_map:
                    lazy_map[name] = (mod, attr)

    # ---------------------------------------------------------------------------
    # Version and alias resolution
    # ---------------------------------------------------------------------------

    @staticmethod
    def _extract_version_exports(
        pkg_dir: Path,
        current_pkg: str,
    ) -> t.Infra.VersionExportsResult:
        """Extract version-related exports from ``__version__.py``.

        Returns:
            ``(inline_constants, lazy_entries)``.
            ``inline_constants``: String constants to inline (``__version__``).
            ``lazy_entries``: Non-string dunder constants for lazy loading
            (``__version_info__``).

        """
        ver_file = pkg_dir / "__version__.py"
        if not ver_file.exists():
            return ({}, {})
        tree = u.Infra.parse_module_ast(ver_file)
        if tree is None:
            return ({}, {})

        inline = u.Infra.extract_inline_constants(tree)
        ver_mod = f"{current_pkg}.__version__" if current_pkg else "__version__"

        lazy: t.Infra.MutableLazyImportMap = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if (
                    isinstance(target, ast.Name)
                    and target.id.startswith("__")
                    and target.id.endswith("__")
                    and target.id not in inline
                ):
                    lazy[target.id] = (ver_mod, target.id)

        return (inline, lazy)

    @staticmethod
    def _resolve_aliases(
        lazy_map: t.Infra.MutableLazyImportMap,
        pkg_dir: Path | None = None,
    ) -> None:
        """Resolve single-letter aliases from ``ALIAS_TO_SUFFIX`` mapping.

        Strategy (canonical facade module enforcement):
        1. Derive the exact expected module name from the suffix
           (e.g., Models -> 'models', Types -> 'typings').
        2. Only accept classes ending with the suffix IF they reside in
           the EXACT canonical depth-1 module.
        3. This guarantees we never confuse internal packages (_models)
           or other public modules with the true facade.
        """
        for alias, suffix in c.Infra.ALIAS_TO_SUFFIX.items():
            expected_module = "typings" if suffix == "Types" else suffix.lower()

            if alias in lazy_map:
                existing = lazy_map[alias]
                existing_basename = existing[0].rsplit(".", 1)[-1]
                if (
                    existing[1].endswith(suffix)
                    and existing[0].count(".") == 1
                    and existing_basename == expected_module
                ):
                    continue

            matched = False
            for name, (mod, _attr) in list(lazy_map.items()):
                basename = mod.rsplit(".", 1)[-1]
                if (
                    name.endswith(suffix)
                    and mod.count(".") == 1
                    and basename == expected_module
                ):
                    lazy_map[alias] = (mod, name)
                    matched = True
                    break
            if matched:
                continue
            # Phase 2: no local facade — delegate to parent package
            if pkg_dir is not None:
                parent_pkg = FlextInfraCodegenLazyInit._discover_parent_package(
                    pkg_dir,
                )
                if parent_pkg:
                    lazy_map[alias] = (parent_pkg, alias)

    @staticmethod
    def _discover_parent_package(pkg_dir: Path) -> str | None:
        """Discover the parent flext package by inspecting constants.py MRO.

        Reads ``constants.py`` and finds the first ``from <pkg> import``
        of a class whose name starts with ``Flext`` and ends with the
        same facade suffix. Returns the package name (e.g. ``flext_core``).

        This is fully dynamic — works for any project without hardcoded
        package names.
        """
        constants_file = pkg_dir / "constants.py"
        if not constants_file.exists():
            return None
        tree = u.Infra.parse_module_ast(constants_file)
        if tree is None:
            return None
        for node in ast.iter_child_nodes(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.module is None:
                continue
            for alias_node in node.names:
                name = alias_node.name
                if name.startswith("Flext") and name.endswith("Constants"):
                    return node.module.split(".")[0]
        return None

    # ---------------------------------------------------------------------------
    # Code generation
    # ---------------------------------------------------------------------------

    @staticmethod
    def _generate_file(
        docstring_source: str,
        exports: t.StrSequence,
        filtered: t.Infra.LazyImportMap,
        inline_constants: t.StrMapping,
        current_pkg: str,
        eager_typevar_names: frozenset[str] = frozenset(),
    ) -> str:
        """Generate the complete ``__init__.py`` content."""
        return FlextInfraCodegenGeneration.generate_file(
            docstring_source,
            exports,
            filtered,
            inline_constants,
            current_pkg,
            eager_typevar_names,
        )

    # ---------------------------------------------------------------------------
    # Post-generation cleanup
    # ---------------------------------------------------------------------------

    @staticmethod
    def _run_ruff_fix(path: Path) -> None:
        """Run ``ruff --fix`` on the given file to auto-fix lint issues."""
        with contextlib.suppress(FileNotFoundError):
            u.Infra.run_checked([
                c.Infra.RUFF,
                c.Infra.CHECK,
                "--fix",
                "--quiet",
                str(path),
            ])


__all__ = ["FlextInfraCodegenLazyInit"]
