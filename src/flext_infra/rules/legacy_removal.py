"""Rule that removes legacy compatibility code patterns."""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path
from typing import NamedTuple, override

import libcst as cst
from pydantic import ValidationError

from flext_infra import (
    INFRA_MAPPING_ADAPTER,
    INFRA_SEQ_ADAPTER,
    FlextInfraRefactorAliasRemover,
    FlextInfraRefactorDeprecatedRemover,
    FlextInfraRefactorImportBypassRemover,
    FlextInfraRefactorRule,
    c,
    t,
    u,
)


class _ForwardingExpected(NamedTuple):
    positional: t.StrSequence
    kwonly: t.StrSequence
    star_arg: str | None
    star_kwarg: str | None


class _ForwardingActual(NamedTuple):
    positional: t.StrSequence
    keyword: t.StrMapping
    star: str | None
    star_kw: str | None


class FlextInfraRefactorLegacyRemovalRule(FlextInfraRefactorRule):
    """Remove aliases, deprecated classes, wrappers and import bypass blocks."""

    def _typed_config(self) -> Mapping[str, t.Infra.InfraValue]:
        """Get self.config validated as Mapping[str, InfraValue]."""
        return INFRA_MAPPING_ADAPTER.validate_python(self.config)

    @staticmethod
    def _positionals_match(
        *,
        positional_expected: t.StrSequence,
        positional_forwarded: t.StrSequence,
        keyword_forwarded: t.StrMapping,
    ) -> bool:
        """Check positional args forwarded correctly by position or by name."""
        positional_by_name = not positional_forwarded and set(
            keyword_forwarded.keys(),
        ) >= set(positional_expected)
        positional_by_position = positional_forwarded == positional_expected
        if not (positional_by_position or positional_by_name):
            return False
        return all(
            keyword_forwarded[name] == name
            for name in positional_expected
            if name in keyword_forwarded
        )

    @staticmethod
    def _kwonly_match(
        *,
        kwonly_expected: t.StrSequence,
        keyword_forwarded: t.StrMapping,
    ) -> bool:
        """Check keyword-only args forwarded correctly."""
        if kwonly_expected and not set(keyword_forwarded.keys()) >= set(
            kwonly_expected
        ):
            return False
        return all(keyword_forwarded.get(name) == name for name in kwonly_expected)

    @staticmethod
    def _variadic_matches(
        expected: str | None,
        forwarded: str | None,
    ) -> bool:
        """Check *args or **kwargs forwarding matches expectation."""
        if expected is not None:
            return forwarded == expected
        return forwarded is None

    @staticmethod
    def _is_forwarding_compatible(
        expected: _ForwardingExpected,
        actual: _ForwardingActual,
    ) -> bool:
        cls = FlextInfraRefactorLegacyRemovalRule
        extra_keywords = (
            set(actual.keyword.keys()) - set(expected.positional) - set(expected.kwonly)
        )
        return (
            cls._positionals_match(
                positional_expected=expected.positional,
                positional_forwarded=actual.positional,
                keyword_forwarded=actual.keyword,
            )
            and cls._kwonly_match(
                kwonly_expected=expected.kwonly,
                keyword_forwarded=actual.keyword,
            )
            and not extra_keywords
            and cls._variadic_matches(expected.star_arg, actual.star)
            and cls._variadic_matches(expected.star_kwarg, actual.star_kw)
        )

    @staticmethod
    def _name_value(expr: cst.BaseExpression) -> str | None:
        if isinstance(expr, (cst.Name, cst.SimpleString, cst.Integer, cst.Float)):
            return expr.value
        return None

    @override
    def apply(
        self,
        tree: cst.Module,
        _file_path: Path | None = None,
    ) -> t.Infra.Pair[cst.Module, t.StrSequence]:
        """Apply configured legacy-removal transforms to module tree."""
        changes: MutableSequence[str] = []
        fix_action = u.Infra.get_str_key(
            self.config, c.Infra.ReportKeys.FIX_ACTION, lower=True
        )
        if "alias" in self.rule_id or fix_action == "remove":
            tree, alias_changes = self._remove_aliases(tree)
            changes.extend(alias_changes)
        if "deprecated" in self.rule_id or fix_action == "remove_and_update_refs":
            tree, deprecated_changes = self._remove_deprecated(tree)
            changes.extend(deprecated_changes)
        if "wrapper" in self.rule_id or fix_action == "inline_and_remove":
            tree, wrapper_changes = self._remove_wrappers(tree)
            changes.extend(wrapper_changes)
        if "bypass" in self.rule_id or fix_action == "keep_try_only":
            tree, bypass_changes = self._remove_import_bypasses(tree)
            changes.extend(bypass_changes)
        return (tree, changes)

    @staticmethod
    def _normalize_string_items(value: t.Infra.InfraValue) -> t.StrSequence:
        if not isinstance(value, (list, tuple, set)):
            return []
        try:
            items: Sequence[t.Infra.InfraValue] = INFRA_SEQ_ADAPTER.validate_python(
                value
            )
        except ValidationError:
            return []
        output: t.StrSequence = [item for item in items if isinstance(item, str)]
        return output

    def _expected_forwarding_params(
        self,
        func: cst.FunctionDef,
    ) -> _ForwardingExpected:
        posonly_names = [param.name.value for param in func.params.posonly_params]
        positional_names = [param.name.value for param in func.params.params]
        positional_expected = posonly_names + positional_names
        kwonly_expected = [param.name.value for param in func.params.kwonly_params]
        expected_star_arg: str | None = None
        if isinstance(func.params.star_arg, cst.Param):
            expected_star_arg = func.params.star_arg.name.value
        expected_star_kwarg: str | None = None
        if isinstance(func.params.star_kwarg, cst.Param):
            expected_star_kwarg = func.params.star_kwarg.name.value
        return _ForwardingExpected(
            positional=positional_expected,
            kwonly=kwonly_expected,
            star_arg=expected_star_arg,
            star_kwarg=expected_star_kwarg,
        )

    @staticmethod
    def _single_return_call(func: cst.FunctionDef) -> cst.Call | None:
        """Extract the Call node from a single-statement 'return call()' body."""
        if not isinstance(func.body, cst.IndentedBlock):
            return None
        if len(func.body.body) != 1:
            return None
        stmt = func.body.body[0]
        if not isinstance(stmt, cst.SimpleStatementLine) or len(stmt.body) != 1:
            return None
        small_stmt = stmt.body[0]
        if not isinstance(small_stmt, cst.Return) or not isinstance(
            small_stmt.value, cst.Call
        ):
            return None
        return small_stmt.value

    def _extract_passthrough_call(
        self,
        func: cst.FunctionDef,
    ) -> t.Infra.Pair[str, Sequence[cst.Arg]] | None:
        call = self._single_return_call(func)
        if call is None or not isinstance(call.func, cst.Name):
            return None
        return (call.func.value, list(call.args))

    def _get_passthrough_target(self, func: cst.FunctionDef) -> str | None:
        passthrough = self._extract_passthrough_call(func)
        if passthrough is None:
            return None
        target_name, call_args = passthrough
        expected = self._expected_forwarding_params(func)
        actual = self._parse_forwarded_arguments(call_args)
        if actual is None:
            return None
        if not self._is_forwarding_compatible(expected, actual):
            return None
        return target_name

    def _require_name_value(self, arg: cst.Arg) -> str | None:
        """Extract a required name/literal value from an argument, or None."""
        return self._name_value(arg.value)

    def _classify_arg(
        self,
        arg: cst.Arg,
        *,
        positional: MutableSequence[str],
        keyword: t.MutableStrMapping,
        stars: t.MutableStrMapping,
    ) -> bool:
        """Classify a single call argument. Returns False if unparseable."""
        name_value = self._require_name_value(arg)
        if arg.keyword is not None:
            if name_value is None:
                return False
            keyword[arg.keyword.value] = name_value
        elif arg.star in {"*", "**"}:
            if name_value is None:
                return False
            stars[arg.star] = name_value
        elif arg.star not in {"", None}:
            return False
        else:
            if name_value is None:
                return False
            positional.append(name_value)
        return True

    def _parse_forwarded_arguments(
        self,
        call_args: Sequence[cst.Arg],
    ) -> _ForwardingActual | None:
        positional: MutableSequence[str] = []
        keyword: t.MutableStrMapping = {}
        stars: t.MutableStrMapping = {}
        for arg in call_args:
            if not self._classify_arg(
                arg, positional=positional, keyword=keyword, stars=stars
            ):
                return None
        return _ForwardingActual(
            positional=positional,
            keyword=keyword,
            star=stars.get("*"),
            star_kw=stars.get("**"),
        )

    def _remove_aliases(
        self,
        tree: cst.Module,
    ) -> t.Infra.Pair[cst.Module, t.StrSequence]:
        typed_config = self._typed_config()
        allow_aliases = set(
            self._normalize_string_items(typed_config.get("allow_aliases", [])),
        )
        allow_target_suffixes = tuple(
            self._normalize_string_items(typed_config.get("allow_target_suffixes", [])),
        )
        return self._apply_transformer(
            FlextInfraRefactorAliasRemover(
                allow_aliases=allow_aliases,
                allow_target_suffixes=allow_target_suffixes,
            ),
            tree,
        )

    def _remove_deprecated(
        self,
        tree: cst.Module,
    ) -> t.Infra.Pair[cst.Module, t.StrSequence]:
        return self._apply_transformer(FlextInfraRefactorDeprecatedRemover(), tree)

    def _remove_import_bypasses(
        self,
        tree: cst.Module,
    ) -> t.Infra.Pair[cst.Module, t.StrSequence]:
        return self._apply_transformer(FlextInfraRefactorImportBypassRemover(), tree)

    def _remove_wrappers(
        self,
        tree: cst.Module,
    ) -> t.Infra.Pair[cst.Module, t.StrSequence]:
        changes: MutableSequence[str] = []
        new_body: MutableSequence[cst.BaseStatement] = []
        for stmt in tree.body:
            if not isinstance(stmt, cst.FunctionDef):
                new_body.append(stmt)
                continue
            target_name = self._get_passthrough_target(stmt)
            if target_name is None:
                new_body.append(stmt)
                continue
            alias_assign = cst.SimpleStatementLine(
                body=[
                    cst.Assign(
                        targets=[cst.AssignTarget(target=cst.Name(stmt.name.value))],
                        value=cst.Name(target_name),
                    ),
                ],
            )
            new_body.append(alias_assign)
            changes.append(f"Inlined wrapper: {stmt.name.value} -> {target_name}")
        return (tree.with_changes(body=new_body), changes)


__all__ = ["FlextInfraRefactorLegacyRemovalRule"]
