"""Rule that removes legacy compatibility code patterns."""

from __future__ import annotations

import ast
import re
from collections.abc import Mapping, MutableSequence

from flext_infra import (
    c,
    t,
    u,
)


class FlextInfraRefactorLegacyRemovalRule:
    """Remove aliases, deprecated classes, wrappers and import bypass blocks."""

    def __init__(self, config: Mapping[str, t.Infra.InfraValue]) -> None:
        """Initialize rule metadata from rule config."""
        self.config = dict(config)
        rule_id = self.config.get(c.Infra.RK_ID, c.Infra.DEFAULT_UNKNOWN)
        self.rule_id = str(rule_id)

    def apply(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        dry_run: bool = False,
    ) -> t.Infra.TransformResult:
        """Apply configured legacy-removal transforms to resource."""
        source = resource.read()
        changes: MutableSequence[str] = []
        fix_action = u.Infra.get_str_key(
            self.config,
            c.Infra.RK_FIX_ACTION,
            case="lower",
        )
        new_source = source
        if "alias" in self.rule_id or fix_action == "remove":
            new_source, alias_changes = self._remove_aliases(
                rope_project,
                resource,
                new_source,
            )
            changes.extend(alias_changes)
        if "deprecated" in self.rule_id or fix_action == "remove_and_update_refs":
            new_source, deprecated_changes = self._remove_deprecated(
                new_source,
            )
            changes.extend(deprecated_changes)
        if "wrapper" in self.rule_id or fix_action == "inline_and_remove":
            new_source, wrapper_changes = self._remove_wrappers(new_source)
            changes.extend(wrapper_changes)
        if "bypass" in self.rule_id or fix_action == "keep_try_only":
            new_source, bypass_changes = self._remove_import_bypasses(
                new_source,
            )
            changes.extend(bypass_changes)
        if new_source != source and not dry_run:
            resource.write(new_source)
        return (new_source, changes)

    def _remove_aliases(
        self,
        _rope_project: t.Infra.RopeProject,
        _resource: t.Infra.RopeResource,
        source: str,
    ) -> t.Infra.TransformResult:
        """Remove module-level alias assignments."""
        allow_aliases = set(
            u.Infra.string_list(
                self.config.get("allow_aliases", []),
            ),
        )
        allow_target_suffixes = tuple(
            u.Infra.string_list(
                self.config.get("allow_target_suffixes", []),
            ),
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
        if not changes:
            no_changes: list[str] = []
            return (source, no_changes)
        return ("".join(kept), changes)

    @staticmethod
    def _remove_deprecated(source: str) -> t.Infra.TransformResult:
        """Remove classes/functions decorated with @deprecated."""
        deprecated_re = re.compile(
            r"^@deprecated.*\n(?:class|def)\s+(\w+).*?(?=\n(?:class |def |@|\Z))",
            re.MULTILINE | re.DOTALL,
        )
        changes: MutableSequence[str] = []
        new_source = source
        for match in deprecated_re.finditer(source):
            changes.append(f"Removed deprecated: {match.group(1)}")
        new_source = deprecated_re.sub("", source)
        return (new_source, changes)

    @staticmethod
    def _remove_wrappers(source: str) -> t.Infra.TransformResult:
        """Inline single-return passthrough wrappers as aliases."""
        changes: MutableSequence[str] = []
        try:
            module = ast.parse(source)
        except SyntaxError:
            return (source, changes)
        lines = source.splitlines(keepends=True)
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
            if not FlextInfraRefactorLegacyRemovalRule._is_passthrough_wrapper(
                node,
                returned,
            ):
                continue
            replacements.append((
                node.lineno - 1,
                node.end_lineno or node.lineno,
                f"{node.name} = {returned.func.id}\n",
            ))
            changes.append(f"Inlined wrapper: {node.name} -> {returned.func.id}")
        for start, end, replacement in reversed(replacements):
            lines[start:end] = [replacement]
        no_changes: list[str] = []
        return (
            ("".join(lines).rstrip("\n") + "\n", changes)
            if changes
            else (source, no_changes)
        )

    @staticmethod
    def _is_passthrough_wrapper(
        func: t.Infra.AstFunctionDef,
        call: t.Infra.AstCall,
    ) -> bool:
        """Return True when call forwards parameters without changing values."""
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
        """Collapse try/except ImportError import bypasses to the primary import."""
        bypass_re = re.compile(
            r"^try:\s*\n"
            r"(?P<primary>\s+from\s+\S+\s+import\s+\S+[^\n]*)\n"
            r"except\s+ImportError:\s*\n"
            r"\s+from\s+\S+\s+import\s+\S+[^\n]*\n?",
            re.MULTILINE,
        )
        changes: MutableSequence[str] = []
        for _match in bypass_re.finditer(source):
            changes.append("Removed import bypass block")
        new_source = bypass_re.sub(
            lambda match: match.group("primary").lstrip() + "\n",
            source,
        )
        return (new_source, changes)


__all__ = ["FlextInfraRefactorLegacyRemovalRule"]
