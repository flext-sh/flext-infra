"""Migrate canonical alias imports from flext_core to the owning project.

Rope-based transformer implementing ENFORCE-080: when a project re-exports a
canonical alias locally (c/m/p/t/u), consumers inside that project must import
it from the local facade instead of from flext_core.
"""

from __future__ import annotations

from pathlib import Path
from typing import override

from flext_infra.constants import c
from flext_infra.transformers.base import FlextInfraRopeTransformer
from flext_infra.typings import t
from flext_infra.utilities import u

# Map canonical alias → local facade module suffix inside a FLEXT project.
_ALIAS_TO_LOCAL_MODULE: dict[str, str] = {
    "c": "constants",
    "m": "models",
    "p": "protocols",
    "t": "typings",
    "u": "utilities",
}


class FlextInfraRefactorProjectAliasMigrator(FlextInfraRopeTransformer):
    """Rewrite ``from flext_core import c`` to ``from <proj>.constants import c``."""

    _description = "rewrite foreign canonical alias imports to local project facade"

    def __init__(
        self,
        *,
        file_path: Path | None = None,
        project_alias_owners: t.StrSequenceMapping | None = None,
        current_project: str = "",
        on_change: t.Infra.ChangeCallback = None,
    ) -> None:
        """Initialize with project → local aliases SSOT from flext-core.

        Args:
            file_path: Optional file path used to infer the owning project.
            project_alias_owners: SSOT mapping project package → local aliases.
                Defaults to ``c.ENFORCEMENT_PROJECT_ALIAS_OWNERS``.
            current_project: Explicit project package; overrides inference.
            on_change: Optional callback invoked for each recorded change.

        """
        super().__init__(on_change=on_change)
        owners = (
            project_alias_owners
            if project_alias_owners is not None
            else c.ENFORCEMENT_PROJECT_ALIAS_OWNERS
        )
        self._project_alias_owners = dict(owners)
        self._local_aliases_by_project: dict[str, frozenset[str]] = {
            project: frozenset(aliases) for project, aliases in owners.items()
        }
        self._current_project = current_project or self._project_from_path(file_path)

    @override
    def transform(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> t.Infra.TransformResult:
        """Apply alias migration via rope utilities."""
        _ = rope_project
        source = resource.read()
        if not self._current_project:
            self._current_project = self._project_from_path(
                getattr(resource, "real_path", "") or ""
            )
        updated, changes = self.apply_to_source(source)
        if updated != source and changes:
            resource.write(updated)
        return updated, changes

    @override
    def apply_to_source(self, source: str) -> t.Infra.TransformResult:
        """Apply alias migration to source text."""
        self.changes.clear()
        updated = self._migrate_aliases(source)
        return updated, list(self.changes)

    def _migrate_aliases(self, source: str) -> str:
        """Rewrite flext_core alias imports to local project facades."""
        lines = source.splitlines(keepends=True)
        result: t.MutableSequenceOf[str] = []
        local_imports_to_add: dict[str, set[str]] = {}
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.lstrip()
            next_i, rewritten, handled = self._consume_flext_core_import(
                lines,
                i,
                stripped,
                local_imports_to_add,
            )
            if handled:
                if rewritten is not None:
                    result.append(rewritten)
                i = next_i
                continue
            result.append(line)
            i += 1

        if local_imports_to_add:
            result = self._inject_local_alias_imports(
                result,
                local_imports_to_add,
            )

        return "".join(result)

    def _consume_flext_core_import(
        self,
        lines: t.StrSequence,
        start: int,
        stripped_line: str,
        local_imports_to_add: dict[str, set[str]],
    ) -> tuple[int, str | None, bool]:
        """Process one flext_core import line/block, migrating local aliases."""
        # Parenthesized multi-line import.
        paren_match = c.Infra.FROM_IMPORT_CAPTURE_PAREN_OPEN_RE.match(stripped_line)
        if (
            paren_match is not None
            and paren_match.group(1) == c.Infra.PKG_CORE_UNDERSCORE
        ):
            end = start
            import_lines = [lines[start]]
            while end + 1 < len(lines) and ")" not in lines[end]:
                end += 1
                import_lines.append(lines[end])
            full_text = "".join(import_lines)
            rewritten = self._filter_core_import_names(full_text, local_imports_to_add)
            return end + 1, rewritten, True

        # Single-line import.
        single_match = c.Infra.FROM_IMPORT_LINE_TRIM_RE.match(stripped_line)
        if (
            single_match is not None
            and single_match.group(1) == c.Infra.PKG_CORE_UNDERSCORE
        ):
            rewritten = self._filter_core_import_names(
                lines[start], local_imports_to_add
            )
            return start + 1, rewritten, True

        return start, None, False

    def _filter_core_import_names(
        self,
        import_text: str,
        local_imports_to_add: dict[str, set[str]],
    ) -> str | None:
        """Separate local aliases from flext_core-only aliases in one import."""
        current_project = self._current_project_from_source(import_text)
        local_aliases = self._local_aliases_by_project.get(current_project, frozenset())

        names_part = (
            import_text.split("import", 1)[1] if "import" in import_text else ""
        )
        names_part = names_part.strip().strip("()")

        kept: t.MutableSequenceOf[str] = []
        for bare_name, bound in u.Infra.parse_import_names(names_part):
            display = bare_name if bare_name == bound else f"{bare_name} as {bound}"
            if bound in local_aliases and bound in _ALIAS_TO_LOCAL_MODULE:
                module_suffix = _ALIAS_TO_LOCAL_MODULE[bound]
                local_module = f"{current_project}.{module_suffix}"
                local_imports_to_add.setdefault(local_module, set()).add(display)
                self._record_change(
                    f"Migrated {bound} from flext_core to {local_module}"
                )
                continue
            kept.append(display)

        if not kept:
            return None
        return f"from {c.Infra.PKG_CORE_UNDERSCORE} import {', '.join(kept)}\n"

    def _inject_local_alias_imports(
        self,
        lines: t.MutableSequenceOf[str],
        local_imports_to_add: dict[str, set[str]],
    ) -> t.MutableSequenceOf[str]:
        """Insert newly required local alias imports near the top."""
        new_imports: list[str] = []
        for module in sorted(local_imports_to_add):
            names = sorted(local_imports_to_add[module])
            new_imports.append(f"from {module} import {', '.join(names)}\n")

        insert_pos = u.Infra.find_import_insert_position(lines, past_existing=False)
        for idx, imp in enumerate(new_imports):
            lines.insert(insert_pos + idx, imp)
        return lines

    def _current_project_from_source(self, source: str) -> str:
        """Return current project from explicit value or existing local imports."""
        if self._current_project:
            return self._current_project
        for module in sorted(self._local_aliases_by_project, key=len, reverse=True):
            if f"from {module}." in source or f"import {module}" in source:
                return module
        return ""

    def _project_from_path(self, file_path: Path | str | None) -> str:
        """Infer project package from a workspace file path."""
        if file_path is None:
            return ""
        path = Path(file_path) if isinstance(file_path, str) else file_path
        package_name = u.Infra.package_name(path)
        return package_name.split(".", maxsplit=1)[0]


__all__: list[str] = ["FlextInfraRefactorProjectAliasMigrator"]
