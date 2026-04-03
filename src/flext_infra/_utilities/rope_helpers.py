# pyright: reportMissingTypeStubs=false
"""Generic helper mixin for Rope-backed refactors."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import ClassVar

from rope.refactor.importutils import get_module_imports as rope_get_module_imports

from flext_infra import FlextInfraUtilitiesRopeCore, c, m, p


class FlextInfraUtilitiesRopeHelpers:
    """Generic text, import-placement, and method-order helpers."""

    @staticmethod
    def get_rope_get_module_imports_fn() -> p.Infra.RopeGetModuleImportsFn:
        """Expose ``get_module_imports`` through the public Rope protocol boundary."""

        def _get_module_imports(
            project: p.Infra.RopeProjectLike,
            pymodule: p.Infra.RopePyModuleLike,
        ) -> p.Infra.RopeModuleImportsLike:
            return FlextInfraUtilitiesRopeCore.ensure_module_imports(
                rope_get_module_imports(project, pymodule)
            )

        return _get_module_imports

    @staticmethod
    def get_module_level_assignments(
        source: str,
    ) -> Sequence[tuple[str, str]]:
        """Return (name, value_str) for module-level simple assignments."""
        assignment_pattern = re.compile(
            r"^([A-Za-z_]\w*)\s*(?::\s*[^=]+)?=\s*(.+)$",
        )
        results: list[tuple[str, str]] = []
        scope_depth = 0
        in_multiline_assignment = False
        current_name = ""
        current_value: list[str] = []
        open_brackets = 0

        for line in source.splitlines():
            stripped = line.strip()

            if not in_multiline_assignment:
                if stripped.startswith(("class ", "def ", "@")):
                    scope_depth += 1
                elif scope_depth > 0 and line and not line[0].isspace():
                    scope_depth = 0

            if scope_depth > 0:
                continue

            if in_multiline_assignment:
                current_value.append(stripped)
                open_brackets += (
                    stripped.count("(") + stripped.count("[") + stripped.count("{")
                )
                open_brackets -= (
                    stripped.count(")") + stripped.count("]") + stripped.count("}")
                )
                if open_brackets <= 0:
                    in_multiline_assignment = False
                    results.append((current_name, " ".join(current_value)))
                continue

            match = assignment_pattern.match(line)
            if match and not line[0].isspace():
                current_name = match.group(1)
                val_start = match.group(2).strip()
                open_brackets = (
                    val_start.count("(") + val_start.count("[") + val_start.count("{")
                )
                open_brackets -= (
                    val_start.count(")") + val_start.count("]") + val_start.count("}")
                )

                if open_brackets > 0:
                    in_multiline_assignment = True
                    current_value = [val_start]
                else:
                    results.append((current_name, val_start))

        return results

    @staticmethod
    def extract_definition(
        source: str,
        name: str,
        *,
        kind: str = "function",
    ) -> str | None:
        """Extract full def/class block by name using regex."""
        if kind == "function":
            pattern = re.compile(
                rf"^((?:@\w[\w.]*(?:\([^)]*\))?\n)*"
                rf"def\s+{re.escape(name)}\s*\([^)]*\)[^\n]*\n"
                rf"(?:(?:[ \t]+[^\n]*|[ \t]*)\n)*)",
                re.MULTILINE,
            )
        elif kind == "class":
            pattern = re.compile(
                rf"^((?:@\w[\w.]*(?:\([^)]*\))?\n)*"
                rf"class\s+{re.escape(name)}\b[^\n]*\n"
                rf"(?:(?:[ \t]+[^\n]*|[ \t]*)\n)*)",
                re.MULTILINE,
            )
        else:
            return None
        match = pattern.search(source)
        return match.group(0).rstrip("\n") if match else None

    @staticmethod
    def remove_definition(
        source: str,
        name: str,
        *,
        kind: str = "function",
    ) -> str:
        """Remove a top-level def/class from source."""
        if kind == "function":
            pattern = re.compile(
                rf"^(?:@\w[\w.]*(?:\([^)]*\))?\n)*"
                rf"def\s+{re.escape(name)}\s*\([^)]*\)[^\n]*\n"
                rf"(?:(?:[ \t]+[^\n]*|[ \t]*)\n)*",
                re.MULTILINE,
            )
        elif kind == "class":
            pattern = re.compile(
                rf"^(?:@\w[\w.]*(?:\([^)]*\))?\n)*"
                rf"class\s+{re.escape(name)}\b[^\n]*\n"
                rf"(?:(?:[ \t]+[^\n]*|[ \t]*)\n)*",
                re.MULTILINE,
            )
        else:
            return source
        return pattern.sub("", source, count=1)

    @staticmethod
    def append_to_class_body(
        source: str,
        class_name: str,
        block: str,
    ) -> str:
        """Append a block of code to an existing class body."""
        if not re.search(
            rf"^class\s+{re.escape(class_name)}\b",
            source,
            re.MULTILINE,
        ):
            return source.rstrip("\n") + f"\n\nclass {class_name}:\n{block}\n"
        lines = source.splitlines(keepends=True)
        in_class = False
        insert_idx = len(lines)
        class_indent = 0
        pass_idx: int | None = None
        only_placeholder_pass = True
        for index, line in enumerate(lines):
            stripped = line.lstrip()
            if not in_class:
                if stripped.startswith((f"class {class_name}", f"class {class_name}(")):
                    in_class = True
                    class_indent = len(line) - len(stripped) + 4
                continue
            if not line.strip():
                continue
            line_indent = len(line) - len(line.lstrip())
            if line_indent < class_indent and line.strip():
                insert_idx = index
                break
            if (
                line_indent == class_indent
                and stripped.strip() == "pass"
                and pass_idx is None
            ):
                pass_idx = index
                continue
            only_placeholder_pass = False
        if pass_idx is not None and only_placeholder_pass:
            del lines[pass_idx]
            if pass_idx < insert_idx:
                insert_idx -= 1
        lines.insert(insert_idx, block.rstrip("\n") + "\n\n")
        return "".join(lines)

    @staticmethod
    def indent_block(text: str, spaces: int = 4) -> str:
        """Add indentation to each line of a block."""
        prefix = " " * spaces
        return "".join(
            f"{prefix}{line}" if line.strip() else line
            for line in text.splitlines(keepends=True)
        )

    @staticmethod
    def ensure_decorator(
        source: str,
        decorator: str = "@staticmethod",
    ) -> str:
        """Ensure a function/block has a specific decorator."""
        return source if decorator in source else f"{decorator}\n{source}"

    @staticmethod
    def has_toplevel_definition(
        source: str,
        name: str,
        *,
        kind: str = "function",
    ) -> bool:
        """Check if a top-level function or class exists by name."""
        if kind == "function":
            return (
                re.search(
                    rf"^(?:@\w[\w.]*(?:\([^)]*\))?\n)*def\s+{re.escape(name)}\s*\(",
                    source,
                    re.MULTILINE,
                )
                is not None
            )
        if kind == "class":
            return (
                re.search(rf"^class\s+{re.escape(name)}\b", source, re.MULTILINE)
                is not None
            )
        return False

    @staticmethod
    def check_visibility(name: str, visibility: str | None) -> bool:
        """Check if a method name matches the given visibility filter."""
        if visibility is None:
            return True
        if visibility == "public":
            return not name.startswith("_")
        if visibility == "protected":
            return name.startswith("_") and not name.startswith("__")
        if visibility == "private":
            return name.startswith("__") and not name.endswith("__")
        return True

    _WORD_BOUNDARY_RE_CACHE: ClassVar[dict[str, re.Pattern[str]]] = {}

    @staticmethod
    def bound_name(name_part: str) -> str:
        """Extract the bound name from 'X' or 'X as Y'."""
        item = name_part.strip()
        if " as " in item:
            return item.split(" as ", 1)[1].strip()
        return item

    @staticmethod
    def word_boundary_re(name: str) -> re.Pattern[str]:
        """Get compiled word-boundary regex for a name."""
        cache = FlextInfraUtilitiesRopeHelpers._WORD_BOUNDARY_RE_CACHE
        if name not in cache:
            cache[name] = re.compile(rf"\b{re.escape(name)}\b")
        return cache[name]

    _PROPERTY_DECORATORS: ClassVar[frozenset[str]] = frozenset(
        {"property", "cached_property", "computed_field"},
    )
    _DECORATOR_TO_CATEGORY: ClassVar[Sequence[tuple[str, str]]] = [
        ("staticmethod", "static"),
        ("classmethod", "class"),
    ]

    @staticmethod
    def matches_method_rule(
        method: m.Infra.MethodInfo,
        rule: m.Infra.MethodOrderRule,
    ) -> bool:
        """Check if a method matches an ordering rule."""
        decorators = set(method.decorators)
        excludes = set(rule.exclude_decorators)
        if excludes and decorators.intersection(excludes):
            return False
        if not FlextInfraUtilitiesRopeHelpers.check_visibility(
            method.name, rule.visibility
        ):
            return False
        if rule.decorators and not decorators.intersection(rule.decorators):
            return False
        patterns = rule.patterns
        return not patterns or any(
            re.match(pattern, method.name) for pattern in patterns
        )

    @staticmethod
    def build_method_sort_key(
        method: m.Infra.MethodInfo,
        order_config: Sequence[m.Infra.MethodOrderRule],
    ) -> tuple[int, int, str]:
        """Build a sort key tuple for method ordering."""
        for index, rule in enumerate(order_config):
            if rule.category == "class_attributes":
                continue
            if not FlextInfraUtilitiesRopeHelpers.matches_method_rule(method, rule):
                continue
            explicit_order = rule.order
            if explicit_order:
                if method.name in explicit_order:
                    return (index, explicit_order.index(method.name), method.name)
                if "*" in explicit_order:
                    return (index, explicit_order.index("*") + 1, method.name)
            return (index, 0, method.name)
        return (len(order_config), 0, method.name)

    @staticmethod
    def categorize_method(name: str, decorators: Sequence[str]) -> str:
        """Categorize a method by its decorators and name pattern."""
        if FlextInfraUtilitiesRopeHelpers._PROPERTY_DECORATORS.intersection(decorators):
            return c.Infra.MethodCategory.PROPERTY
        for (
            decorator_name,
            category,
        ) in FlextInfraUtilitiesRopeHelpers._DECORATOR_TO_CATEGORY:
            if decorator_name in decorators:
                return category
        # Fallback: categorize by name convention
        if name.startswith("__") and name.endswith("__"):
            return c.Infra.MethodCategory.MAGIC
        if name.startswith("__"):
            return c.Infra.MethodCategory.PRIVATE
        if name.startswith("_"):
            return c.Infra.MethodCategory.PROTECTED
        return c.Infra.MethodCategory.PUBLIC


__all__ = ["FlextInfraUtilitiesRopeHelpers"]
