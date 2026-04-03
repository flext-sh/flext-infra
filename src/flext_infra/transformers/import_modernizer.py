"""Import modernizer transformer -- rope-based implementation.

Removes forbidden imports, replaces symbol usages with runtime alias paths,
and adds missing runtime alias imports to the module header.
"""

from __future__ import annotations

import re
from collections.abc import MutableSequence, Sequence
from typing import override

from flext_infra import (
    c,
    t,
    u,
)
from flext_infra.transformers._base import FlextInfraRopeTransformer


class FlextInfraRefactorImportModernizer(FlextInfraRopeTransformer):
    """Rewrite forbidden imports and replace symbols with runtime alias paths."""

    def __init__(
        self,
        imports_to_remove: t.StrSequence,
        symbols_to_replace: t.StrMapping,
        runtime_aliases: t.Infra.StrSet,
        blocked_aliases: t.Infra.StrSet,
        on_change: t.Infra.ChangeCallback = None,
    ) -> None:
        """Initialize import rewrite configuration."""
        super().__init__(on_change=on_change)
        self._imports_to_remove = frozenset(imports_to_remove)
        self._symbols_to_replace = dict(symbols_to_replace)
        self._runtime_aliases = runtime_aliases
        self._blocked_aliases = blocked_aliases
        self.modified_imports = False
        self.aliases_needed: t.Infra.StrSet = set()
        self.aliases_present: t.Infra.StrSet = set()
        self.active_symbol_replacements: t.MutableStrMapping = {}

    @override
    def transform(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> tuple[str, Sequence[str]]:
        """Apply import modernization via rope utilities."""
        source = u.Infra.read_source(resource)
        self._scan_core_aliases(source)
        source = self._rewrite_forbidden_imports(source)
        source = self._replace_symbol_usages(source)
        source = self._inject_missing_aliases(source)
        u.Infra.write_source(
            rope_project,
            resource,
            source,
            description="modernize imports",
        )
        return source, list(self.changes)

    def apply_to_source(self, source: str) -> str:
        """Apply import modernization to source text, returning transformed source."""
        self._scan_core_aliases(source)
        source = self._rewrite_forbidden_imports(source)
        source = self._replace_symbol_usages(source)
        return self._inject_missing_aliases(source)

    def _scan_core_aliases(self, source: str) -> None:
        """Scan source for existing core alias imports."""
        core_pkg = c.Infra.Packages.CORE_UNDERSCORE
        self.aliases_present.update(
            u.Infra.collect_from_import_bound_names(
                source,
                module_name=core_pkg,
            ).intersection(self._runtime_aliases),
        )

    def _rewrite_forbidden_imports(self, source: str) -> str:
        """Remove or trim forbidden import lines via regex."""
        lines = source.splitlines(keepends=True)
        result: MutableSequence[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.lstrip()
            # Check for from X import (multiline)
            from_match = re.match(
                r"from\s+([\w.]+)\s+import\s*\(",
                stripped,
            )
            if from_match:
                module = from_match.group(1)
                if module in self._imports_to_remove:
                    # Collect full multiline import
                    import_lines = [line]
                    while i + 1 < len(lines) and ")" not in lines[i]:
                        i += 1
                        import_lines.append(lines[i])
                    full_text = "".join(import_lines)
                    rewritten = self._filter_import_names(module, full_text)
                    if rewritten is not None:
                        result.append(rewritten)
                    i += 1
                    continue
            # Check for single-line from X import Y
            from_single = re.match(
                r"from\s+([\w.]+)\s+import\s+(.+?)(?:\s*#.*)?$",
                stripped,
            )
            if from_single:
                module = from_single.group(1)
                if module in self._imports_to_remove:
                    rewritten = self._filter_import_names(module, line)
                    if rewritten is not None:
                        result.append(rewritten)
                    else:
                        pass  # Line removed entirely
                    i += 1
                    continue
            result.append(line)
            i += 1
        return "".join(result)

    def _filter_import_names(
        self,
        module: str,
        import_text: str,
    ) -> str | None:
        """Filter names from an import statement. Returns None to remove entirely."""
        # Extract all names from the import text
        names_part = (
            import_text.split("import", 1)[1] if "import" in import_text else ""
        )
        names_part = names_part.strip().strip("()")
        mapped: MutableSequence[str] = []
        unmapped: MutableSequence[str] = []
        for bare_name, bound in u.Infra.parse_import_names(names_part):
            if bare_name not in self._symbols_to_replace:
                unmapped.append(
                    bare_name if bare_name == bound else f"{bare_name} as {bound}"
                )
                continue
            alias_path = self._symbols_to_replace[bare_name]
            alias_root = alias_path.split(".")[0]
            if alias_root in self._blocked_aliases:
                unmapped.append(
                    bare_name if bare_name == bound else f"{bare_name} as {bound}"
                )
                continue
            self.active_symbol_replacements[bound] = alias_path
            self.aliases_needed.add(alias_root)
            mapped.append(bare_name)
        if not mapped:
            return import_text
        self.modified_imports = True
        self._record_change(f"Removed import: from {module}")
        if unmapped:
            return f"from {module} import {', '.join(unmapped)}\n"
        return None

    def _replace_symbol_usages(self, source: str) -> str:
        """Replace migrated symbol references with runtime-alias paths."""
        for local_name, alias_path in self.active_symbol_replacements.items():
            new_source = re.sub(rf"\b{re.escape(local_name)}\b", alias_path, source)
            if new_source != source:
                self._record_change(f"Replaced: {local_name} -> {alias_path}")
                source = new_source
        return source

    def _inject_missing_aliases(self, source: str) -> str:
        """Insert any newly required runtime alias imports."""
        missing = sorted(self.aliases_needed - self.aliases_present)
        if not (self.modified_imports and missing):
            return source
        pkg = c.Infra.Packages.CORE_UNDERSCORE
        import_line = f"from {pkg} import {', '.join(missing)}\n"
        self._record_change(f"Added: from flext_core import {', '.join(missing)}")
        lines = source.splitlines(keepends=True)
        idx = u.Infra.find_import_insert_position(lines, past_existing=False)
        lines.insert(idx, import_line)
        return "".join(lines)


__all__ = ["FlextInfraRefactorImportModernizer"]
