"""Unify inline typing unions and TypeAlias declarations to canonical forms.

All transformations are syntactic and driven by ``c.Infra.*_RE`` regex
constants — no ``ast`` parsing or tree walking is required:

- **Inline-union canonicalization**: replaces permutations like
  ``int | str`` with the canonical ``t.<Alias>`` (configured via
  ``canonical_map``).
- **Built-in annotation canonicalization**: rewrites ``t.MutableMappingKV[K, V]`` →
  ``t.MutableMappingKV[K, V]``, ``t.MutableSequenceOf[X]`` → ``t.SequenceOf[X]``, and bare
  ``Any``/``object`` / ``typing.Any`` → ``t.JsonValue``. The bracket
  forms guard against false positives by requiring an immediate ``[``.
- **PEP 695 TypeAlias modernization**: rewrites ``X: TypeAlias = expr``
  into ``type X = expr``.
- **Canonical ``t`` import injection**: adds ``from <pkg> import t``
  after the last import line when ``t.`` is used but the import is
  missing.
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING, override

from flext_infra import c

from .._utilities.transformer_base import FlextInfraRopeTransformer
from ._canonical_t_import import FlextInfraEnsureCanonicalTImportMixin
from ._typing_rewrite import FlextInfraRefactorTypingUnifierRewriteMixin

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import t


class FlextInfraRefactorTypingUnifier(
    FlextInfraEnsureCanonicalTImportMixin,
    FlextInfraRopeTransformer,
    FlextInfraRefactorTypingUnifierRewriteMixin,
):
    """Unify inline type unions and modernize TypeAlias to PEP 695."""

    _description = "canonicalize types and modernize TypeAlias"

    def __init__(
        self,
        *,
        canonical_map: t.MutableMappingKV[frozenset[str], str],
        file_path: Path | None = None,
    ) -> None:
        """Initialize with canonical union map and optional file path for skip logic."""
        super().__init__()
        self._canonical_map = canonical_map
        self._file_path = file_path
        self._is_definition_file = self._is_typing_definition_file(file_path)

    @override
    def apply_to_source(self, source: str) -> t.Infra.TransformResult:
        """Apply unions, built-in canonicalization, TypeAlias and t import."""
        if self._is_definition_file:
            return source, list(self.changes)

        def union_size(item: t.Pair[frozenset[str], str]) -> int:
            return len(item[0])

        for member_set, canonical in sorted(
            self._canonical_map.items(), key=union_size, reverse=True
        ):
            pattern = self._union_pattern(member_set)
            if pattern is None:
                continue

            def replacer(match: t.Infra.RegexMatch, canonical: str = canonical) -> str:
                """Replace one matched union with the canonical alias."""
                self._record_change(
                    f"Canonicalized inline union {match.group(0)} -> {canonical}"
                )
                return canonical

            source, _count = pattern.subn(replacer, source)
        source = self._canonicalize_annotation_builtins(source)
        source = self._modernize_typealias(source)
        added, did_add = self._ensure_t_import(
            source,
            FlextInfraEnsureCanonicalTImportMixin.canonical_import_module(
                self._file_path
            ),
        )
        if did_add:
            self._record_change(
                "Added canonical t import from "
                f"{FlextInfraEnsureCanonicalTImportMixin.canonical_import_module(self._file_path)}"
            )
        source = added
        return source, list(self.changes)

    def _canonicalize_annotation_builtins(self, source: str) -> str:
        """Rewrite built-in generic annotations to canonical ``t.*`` aliases.

        Only annotation spans are rewritten. Passing the whole file to the
        annotation rewriter made it edit any text that merely looked like one:
        it rewrote the literal ``"dict["`` inside this package's own rewrite
        tables, destroying them, and left unbalanced brackets in three
        transformer modules. An annotation is an AST position, so the AST is
        what decides which text is eligible.
        """
        try:
            module = ast.parse(source)
        except SyntaxError:
            return source
        # What this transformer can prove from one module is a parameter: every
        # use of a parameter is inside its own function, so a mutation scan
        # over this module sees all of them. Declarations are excluded below
        # for the opposite reason, which also retires the separate
        # function-local exclusion that used to live here -- a local
        # declaration is a declaration.
        mutated = self._mutated_names(module)
        spans: t.MutableSequenceOf[t.Pair[int, int]] = []
        for node in ast.walk(module):
            annotations: list[ast.expr | None] = []
            if isinstance(node, ast.AnnAssign):
                # A declaration cannot be proven read-only from one module: its
                # name is reachable wherever the object is. The lazy-init
                # planner declares `_module_exports_cache` in a base class and
                # writes it from a mixin in another file, so a per-module scan
                # saw a read-only field, widened it to Mapping, and made every
                # write site in that other module an error. So a declaration
                # gets only the rewrites that change no capability -- the tuple
                # aliases and the Any/object replacements, which are exact
                # synonyms -- and never a container widening.
                if self._widens_a_container(source, node.annotation):
                    continue
                annotations.append(node.annotation)
            elif isinstance(node, ast.arg):
                if node.arg in mutated:
                    continue
                annotations.append(node.annotation)
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                returns = node.returns
                if returns is not None and self._widens_a_container(source, returns):
                    continue
                annotations.append(returns)
            for annotation in annotations:
                if annotation is None:
                    continue
                start = self._offset(source, annotation.lineno, annotation.col_offset)
                end_lineno = annotation.end_lineno
                end_col = annotation.end_col_offset
                if end_lineno is None or end_col is None:
                    continue
                spans.append((start, self._offset(source, end_lineno, end_col)))
        rewritten = source
        for start, end in sorted(spans, reverse=True):
            text = rewritten[start:end]
            replacement, changes = self._rewrite_annotation_text(text)
            if replacement == text:
                continue
            for change in changes:
                self._record_change(change)
            rewritten = f"{rewritten[:start]}{replacement}{rewritten[end:]}"
        return rewritten

    def _widens_a_container(self, source: str, annotation: ast.expr) -> bool:
        """Return whether rewriting this annotation would change a capability.

        Only a parameter can be widened for free: a function accepting Mapping
        accepts strictly more callers than one demanding dict. A return type
        promises what the caller receives, and a declaration names something
        whose writers may live in another module -- for both, handing back a
        read-only view takes capability away. The tuple aliases and the
        Any/object replacements are exact synonyms and are always allowed, so
        what this refuses is precisely a `dict`/`list` widening; the annotation
        keeps its namespace finding, which is the signal that a person should
        choose the contract.
        """
        end_lineno = annotation.end_lineno
        end_col = annotation.end_col_offset
        if end_lineno is None or end_col is None:
            return True
        text = source[
            self._offset(
                source, annotation.lineno, annotation.col_offset
            ) : self._offset(source, end_lineno, end_col)
        ]
        return any(prefix in text for prefix in ("dict[", "Dict[", "list[", "List["))

    @staticmethod
    def _mutated_names(module: ast.Module) -> frozenset[str]:
        """Return every name the module mutates in place.

        The read-only abstractions are what generalize an annotation, but a
        value the code mutates cannot be one: Mapping has no item assignment
        and Sequence has no append. Rewriting those declarations produced
        exactly those errors, so a mutated name keeps its concrete type.
        """
        mutating_methods = frozenset({
            "append",
            "extend",
            "insert",
            "pop",
            "popitem",
            "remove",
            "setdefault",
            "sort",
            "update",
            "clear",
        })
        names: set[str] = set()
        for node in ast.walk(module):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Subscript):
                        names.update(
                            FlextInfraRefactorTypingUnifier._mutated_root(target.value)
                        )
            elif isinstance(node, ast.AugAssign):
                names.update(FlextInfraRefactorTypingUnifier._mutated_root(node.target))
            elif isinstance(node, ast.Delete):
                for target in node.targets:
                    if isinstance(target, ast.Subscript):
                        names.update(
                            FlextInfraRefactorTypingUnifier._mutated_root(target.value)
                        )
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in mutating_methods
            ):
                names.update(
                    FlextInfraRefactorTypingUnifier._mutated_root(node.func.value)
                )
        return frozenset(names)

    @staticmethod
    def _mutated_root(node: ast.expr) -> frozenset[str]:
        """Return the declared name a mutation target refers to, if any.

        A mutated value is not always reached through a bare local name. A
        class-level cache is written as ``Owner._CACHE[key] = value`` or
        ``self._cache.append(item)``, whose target is an attribute rather than
        a name. Matching only ``ast.Name`` left those declarations looking
        read-only, so their ``dict`` annotations were generalized to the
        immutable ``Mapping`` alias and every write site became a type error --
        the exact regression this detector exists to prevent. The annotation
        being considered is declared as a plain name inside its class body, so
        the attribute's final segment is the name to match.
        """
        if isinstance(node, ast.Name):
            return frozenset({node.id})
        if isinstance(node, ast.Attribute):
            return frozenset({node.attr})
        return frozenset()

    @staticmethod
    def _offset(source: str, lineno: int, col: int) -> int:
        """Return the character offset of one 1-based line and 0-based column."""
        lines = source.splitlines(keepends=True)
        return sum(len(line) for line in lines[: lineno - 1]) + col

    @staticmethod
    def _union_pattern(members: frozenset[str]) -> t.Infra.RegexPattern | None:
        """Build regex matching any permutation of a ``A | B | C`` union."""
        if len(members) < c.Infra.MIN_UNION_MEMBERS:
            return None
        escaped = [c.Infra.escape(m) for m in sorted(members)]
        part = rf"(?:{'|'.join(escaped)})"
        pattern: t.Infra.RegexPattern = c.Infra.compile(
            rf"\b{part}(?:\s*\|\s*{part}){{{len(members) - 1}}}\b"
        )
        return pattern

    def _modernize_typealias(self, source: str) -> str:
        """Convert ``X: TypeAlias = expr`` to ``type X = expr`` (PEP 695)."""
        for match in c.Infra.LEGACY_TYPEALIAS_RE.finditer(source):
            self._record_change(
                f"Converted legacy TypeAlias assignment: {match.group(1)}"
            )
        new_source: str = c.Infra.LEGACY_TYPEALIAS_RE.sub(r"type \1 = \2", source)
        return new_source

    @staticmethod
    def _is_typing_definition_file(file_path: Path | None) -> bool:
        """Return whether ``file_path`` is one of the typing definition files."""
        if file_path is None:
            return False
        if file_path.name in c.Infra.TYPING_DEFINITION_FILES:
            return True
        return any(part in c.Infra.TYPING_DEFINITION_FILES for part in file_path.parts)


__all__: t.MutableSequenceOf[str] = ["FlextInfraRefactorTypingUnifier"]
