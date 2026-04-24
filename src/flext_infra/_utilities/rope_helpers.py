"""Generic helper mixin for Rope-backed refactors."""

from __future__ import annotations

import re
from collections.abc import (
    Sequence,
)
from pathlib import Path
from typing import ClassVar

import flext_infra as infra_package
from flext_infra import c, m, p, t


class FlextInfraUtilitiesRopeHelpers:
    """Generic text, import-placement, and method-order helpers."""

    _post_hooks: ClassVar[list[p.Infra.RopePostHook]] = []
    _default_post_hooks_registered: ClassVar[bool] = False

    @classmethod
    def _ensure_default_post_hooks_registered(cls) -> None:
        """Load and register built-in rope post-hooks once."""
        if cls._default_post_hooks_registered:
            return
        cls.register_rope_post_hook(
            infra_package.FlextInfraRefactorMigrateToClassMRO.run_as_hook,
        )
        cls._default_post_hooks_registered = True

    @classmethod
    def run_rope_post_hooks(
        cls,
        path: Path,
        *,
        dry_run: bool,
    ) -> Sequence[m.Infra.Result]:
        """Run workspace-scale semantic passes after local refactors."""
        cls._ensure_default_post_hooks_registered()
        results: list[m.Infra.Result] = []
        for hook in cls._post_hooks:
            results.extend(hook(path, dry_run=dry_run))
        return results

    @classmethod
    def register_rope_post_hook(
        cls,
        hook: p.Infra.RopePostHook,
    ) -> None:
        """Register a post-processing hook for rope refactoring pipelines."""
        if hook not in cls._post_hooks:
            cls._post_hooks.append(hook)

    @staticmethod
    def get_module_level_assignments(
        source: str,
    ) -> Sequence[t.Infra.StrPair]:
        """Return (name, value_str) for module-level simple assignments."""
        assignment_pattern = re.compile(
            r"^([A-Za-z_]\w*)\s*(?::\s*[^=]+)?=\s*(.+)$",
        )
        results: list[t.Infra.StrPair] = []
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
        r"""Extract full def/class block by name using regex.

        Handles single-line signatures. Multi-line return-annotation
        signatures (``def foo() -> tuple[\n    A,\n]:``) are detected
        by a fallback bracket-balance scan that extends the regex match
        through any unclosed bracket groups.
        """
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
        if match is None:
            return None
        block = match.group(0)
        return FlextInfraUtilitiesRopeHelpers._extend_block_through_open_brackets(
            source,
            block,
            match_end=match.end(),
        ).rstrip("\n")

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
    def _extend_block_through_open_brackets(
        source: str,
        block: str,
        *,
        match_end: int,
    ) -> str:
        r"""Extend ``block`` when its regex capture ends mid-bracket-group.

        The existing regex terminates on the first column-0 non-empty line; a
        multi-line signature like ``-> tuple[\n    A,\n]:`` therefore cuts
        off at the unindented ``]:`` line. When the captured block has
        unbalanced brackets, consume further lines until balance reaches 0.
        """
        balance = FlextInfraUtilitiesRopeHelpers._bracket_balance_total(block)
        if balance <= 0:
            return block
        remaining = source[match_end:]
        additional = 0
        for line in remaining.splitlines(keepends=True):
            additional += len(line)
            balance += FlextInfraUtilitiesRopeHelpers._bracket_balance_line(line)
            if balance <= 0:
                break
        extended = block + source[match_end : match_end + additional]
        tail_start = match_end + additional
        tail = source[tail_start:]
        for line in tail.splitlines(keepends=True):
            stripped = line.strip()
            if not stripped or line.startswith((" ", "\t")):
                extended += line
                continue
            break
        return extended

    @staticmethod
    def _bracket_balance_total(text: str) -> int:
        total = 0
        for line in text.splitlines():
            total += FlextInfraUtilitiesRopeHelpers._bracket_balance_line(line)
        return total

    @staticmethod
    def _bracket_balance_line(line: str) -> int:
        delta = 0
        in_single = False
        in_double = False
        escape = False
        for ch in line:
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if in_single:
                if ch == "'":
                    in_single = False
                continue
            if in_double:
                if ch == '"':
                    in_double = False
                continue
            if ch == "#":
                break
            if ch == "'":
                in_single = True
                continue
            if ch == '"':
                in_double = True
                continue
            if ch in "([{":
                delta += 1
            elif ch in ")]}":
                delta -= 1
        return delta

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

    _PROPERTY_DECORATORS: ClassVar[frozenset[str]] = frozenset(
        {"property", "cached_property", "computed_field"},
    )
    _DECORATOR_TO_CATEGORY: ClassVar[Sequence[t.Infra.StrPair]] = [
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
        if rule.visibility == "public" and method.name.startswith("_"):
            return False
        if rule.visibility == "protected" and (
            not method.name.startswith("_") or method.name.startswith("__")
        ):
            return False
        if rule.visibility == "private" and (
            not method.name.startswith("__") or method.name.endswith("__")
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
    def categorize_method(name: str, decorators: t.StrSequence) -> str:
        """Categorize a method by its decorators and name pattern."""
        if FlextInfraUtilitiesRopeHelpers._PROPERTY_DECORATORS.intersection(decorators):
            property_cat: str = c.Infra.MethodCategory.PROPERTY
            return property_cat
        for (
            decorator_name,
            category,
        ) in FlextInfraUtilitiesRopeHelpers._DECORATOR_TO_CATEGORY:
            if decorator_name in decorators:
                cat: str = category
                return cat
        if name.startswith("__") and name.endswith("__"):
            magic: str = c.Infra.MethodCategory.MAGIC
            return magic
        if name.startswith("__"):
            private: str = c.Infra.MethodCategory.PRIVATE
            return private
        if name.startswith("_"):
            protected: str = c.Infra.MethodCategory.PROTECTED
            return protected
        public: str = c.Infra.MethodCategory.PUBLIC
        return public


__all__: list[str] = ["FlextInfraUtilitiesRopeHelpers"]
