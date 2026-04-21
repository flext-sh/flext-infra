"""Direct legacy-removal execution for the refactor engine."""

from __future__ import annotations

import ast
import re
from collections.abc import Mapping, MutableSequence

from flext_infra import c, t, u


class FlextInfraRefactorEngineLegacyMixin:
    """Execute legacy-removal rules directly from declarative settings."""

    def _apply_legacy_removal(
        self,
        settings: Mapping[str, t.Infra.InfraValue],
        source: str,
    ) -> t.Infra.TransformResult:
        changes: MutableSequence[str] = []
        rule_id = str(settings.get(c.Infra.RK_ID, c.Infra.DEFAULT_UNKNOWN))
        fix_action = u.Cli.json_get_str_key(
            settings,
            c.Infra.RK_FIX_ACTION,
            case="lower",
        )
        updated = source
        if "alias" in rule_id or fix_action == "remove":
            updated, alias_changes = self._remove_aliases(settings, updated)
            changes.extend(alias_changes)
        if "deprecated" in rule_id or fix_action == "remove_and_update_refs":
            updated, deprecated_changes = self._remove_deprecated(updated)
            changes.extend(deprecated_changes)
        if "wrapper" in rule_id or fix_action == "inline_and_remove":
            updated, wrapper_changes = self._remove_wrappers(updated)
            changes.extend(wrapper_changes)
        if "bypass" in rule_id or fix_action == "keep_try_only":
            updated, bypass_changes = self._remove_import_bypasses(updated)
            changes.extend(bypass_changes)
        return (updated, changes)

    @staticmethod
    def _remove_aliases(
        settings: Mapping[str, t.Infra.InfraValue],
        source: str,
    ) -> t.Infra.TransformResult:
        allow_aliases = set(
            u.Infra.string_list(settings.get(c.Infra.RK_ALLOW_ALIASES, []))
        )
        allow_target_suffixes = tuple(
            u.Infra.string_list(settings.get(c.Infra.RK_ALLOW_TARGET_SUFFIXES, []))
        )
        alias_pattern = re.compile(r"^([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\s*$")
        changes: MutableSequence[str] = []
        kept: MutableSequence[str] = []
        for line in source.splitlines(keepends=True):
            if line != line.lstrip():
                kept.append(line)
                continue
            match = alias_pattern.match(line.strip())
            if match is None:
                kept.append(line)
                continue
            target, value = match.groups()
            if (
                target in allow_aliases
                or target in {c.Infra.DUNDER_VERSION, c.Infra.DUNDER_ALL}
                or (allow_target_suffixes and target.endswith(allow_target_suffixes))
            ):
                kept.append(line)
                continue
            changes.append(f"Removed alias: {target} = {value}")
        return ("".join(kept), changes) if changes else (source, list[str]())

    @staticmethod
    def _remove_deprecated(source: str) -> t.Infra.TransformResult:
        deprecated_re = re.compile(
            r"^@deprecated.*\n(?:class|def)\s+(\w+).*?(?=\n(?:class |def |@|\Z))",
            re.MULTILINE | re.DOTALL,
        )
        changes = [
            f"Removed deprecated: {match.group(1)}"
            for match in deprecated_re.finditer(source)
        ]
        return (
            (deprecated_re.sub("", source), changes)
            if changes
            else (source, list[str]())
        )

    @classmethod
    def _remove_wrappers(cls, source: str) -> t.Infra.TransformResult:
        try:
            module = ast.parse(source)
        except SyntaxError:
            return (source, list[str]())
        lines = source.splitlines(keepends=True)
        changes: MutableSequence[str] = []
        replacements: MutableSequence[tuple[int, int, str]] = []
        for node in module.body:
            if not isinstance(node, ast.FunctionDef):
                continue
            if len(node.body) != 1 or not isinstance(node.body[0], ast.Return):
                continue
            returned = node.body[0].value
            if not isinstance(returned, ast.Call) or not isinstance(
                returned.func, ast.Name
            ):
                continue
            if not cls._is_passthrough_wrapper(node, returned):
                continue
            replacements.append((
                node.lineno - 1,
                node.end_lineno or node.lineno,
                f"{node.name} = {returned.func.id}\n",
            ))
            changes.append(f"Inlined wrapper: {node.name} -> {returned.func.id}")
        for start, end, replacement in reversed(replacements):
            lines[start:end] = [replacement]
        if not changes:
            return (source, list[str]())
        return ("".join(lines).rstrip("\n") + "\n", changes)

    @staticmethod
    def _is_passthrough_wrapper(
        func: t.Infra.AstFunctionDef,
        call: t.Infra.AstCall,
    ) -> bool:
        param_names = [arg.arg for arg in (*func.args.posonlyargs, *func.args.args)]
        keyword_names = [arg.arg for arg in func.args.kwonlyargs]
        named_keywords = {
            kw.arg: kw.value for kw in call.keywords if kw.arg is not None
        }
        keyword_unpack = [kw.value for kw in call.keywords if kw.arg is None]
        pos_index = 0

        def _is_name(node: t.Infra.AstExpr, name: str) -> bool:
            return isinstance(node, ast.Name) and node.id == name

        for name in param_names:
            if pos_index < len(call.args) and _is_name(call.args[pos_index], name):
                pos_index += 1
                continue
            if name in named_keywords and _is_name(named_keywords[name], name):
                continue
            return False
        remaining_args = call.args[pos_index:]
        if func.args.vararg is None:
            if remaining_args:
                return False
        elif (
            len(remaining_args) != 1
            or not isinstance(remaining_args[0], ast.Starred)
            or not _is_name(remaining_args[0].value, func.args.vararg.arg)
        ):
            return False
        for name in keyword_names:
            if name not in named_keywords or not _is_name(named_keywords[name], name):
                return False
        if func.args.kwarg is None:
            return not keyword_unpack
        return len(keyword_unpack) == 1 and _is_name(
            keyword_unpack[0], func.args.kwarg.arg
        )

    @staticmethod
    def _remove_import_bypasses(source: str) -> t.Infra.TransformResult:
        bypass_re = re.compile(
            r"^try:\s*\n"
            r"(?P<primary>\s+from\s+\S+\s+import\s+\S+[^\n]*)\n"
            r"except\s+ImportError:\s*\n"
            r"\s+from\s+\S+\s+import\s+\S+[^\n]*\n?",
            re.MULTILINE,
        )
        changes = ["Removed import bypass block" for _ in bypass_re.finditer(source)]
        if not changes:
            return (source, list[str]())
        return (bypass_re.sub(r"\g<primary>\n", source), changes)


__all__: list[str] = ["FlextInfraRefactorEngineLegacyMixin"]
