"""Canonical Python module header analysis and import injection."""

from __future__ import annotations

from flext_infra.constants import c

from .._utilities.transformer_header_parser import (
    FlextInfraUtilitiesTransformerHeaderParser,
)


class FlextInfraUtilitiesTransformerHeader(FlextInfraUtilitiesTransformerHeaderParser):
    """Inject canonical aliases only when the source actually uses them."""

    @classmethod
    def ensure_future_annotations(cls, source: str) -> str:
        """Return source with exactly one correctly positioned future import."""
        normalized = cls._remove_future_annotations_lines(source)
        body = normalized.splitlines(keepends=True)
        info = cls._parse_header(normalized)
        offset = max(
            info.span.shebang_end,
            info.span.encoding_end,
            info.span.comments_end,
            info.span.docstring_end,
        )
        line_index = normalized[:offset].count("\n")
        future_line = f"{c.Infra.FUTURE_ANNOTATIONS}\n"
        if info.span.docstring_end:
            while line_index < len(body) and not body[line_index].strip():
                del body[line_index]
            insert_lines = ["\n", future_line]
            if line_index < len(body):
                insert_lines.append("\n")
            body[line_index:line_index] = insert_lines
        else:
            body.insert(line_index, future_line)
        return "".join(body)

    @classmethod
    def ensure_alias_import(cls, source: str, module: str, alias: str) -> str:
        """Inject ``from <module> import <alias>`` when the alias is actually used."""
        if not alias:
            msg = "canonical import alias must be non-empty"
            raise ValueError(msg)
        if not cls.alias_used(source, alias):
            return source
        if cls.has_alias_import(source, alias) or cls.alias_locally_bound(
            source, alias
        ):
            return source
        typed = cls._alias_import_under_type_checking(source, module, alias)
        if typed is not None:
            return typed
        info = cls._parse_header(source)
        offset = info.span.last_import_end or max(
            info.span.shebang_end,
            info.span.encoding_end,
            info.span.comments_end,
            info.span.docstring_end,
        )
        line = f"from {module} import {alias}\n"
        if offset < len(source) and not source[offset:].startswith("\n"):
            line = f"{line}\n"
        return f"{source[:offset]}{line}{source[offset:]}"

    @classmethod
    def _alias_import_under_type_checking(
        cls, source: str, module: str, alias: str
    ) -> str | None:
        """Place an annotation-only facade import inside ``if TYPE_CHECKING:``.

        A module that the package imports while initialising itself cannot
        import that same package at runtime: injecting the facade at module
        level made ``__version__.py`` raise ImportError on a partially
        initialised ``flext_infra``. With deferred annotations the alias is only
        ever read by a type checker, so the import belongs in the type-checking
        block, which is also what the facade law prescribes. Returns None when
        the module has no such block to extend.
        """
        if "from __future__ import annotations" not in source:
            return None
        lines = source.splitlines(keepends=True)
        for index, line in enumerate(lines):
            if line.rstrip() != "if TYPE_CHECKING:":
                continue
            following = lines[index + 1 :]
            indent = next(
                (
                    item[: len(item) - len(item.lstrip())]
                    for item in following
                    if item.strip()
                ),
                "    ",
            )
            lines.insert(index + 1, f"{indent}from {module} import {alias}\n")
            return "".join(lines)
        return None

    @staticmethod
    def alias_used(source: str, alias: str) -> bool:
        """Return whether ``alias`` is used as a standalone dotted identifier."""
        return (
            c.Infra.compile(rf"\b{c.Infra.escape(alias)}\.(?![0-9])").search(source)
            is not None
        )

    @classmethod
    def has_alias_import(cls, source: str, alias: str) -> bool:
        """Return whether ``alias`` is already bound by a ``from`` import."""
        info = cls._parse_header(source)
        return alias in info.aliases

    @staticmethod
    def alias_locally_bound(source: str, alias: str) -> bool:
        """Return whether a module-level definition or assignment owns an alias."""
        escaped = c.Infra.escape(alias)
        pattern = c.Infra.compile(
            rf"^(?:{escaped}\s*(?::[^=\n]+)?=(?!=)|(?:class|def)\s+{escaped}\b)",
            multiline=True,
        )
        return pattern.search(source) is not None

    @staticmethod
    def _remove_future_annotations_lines(source: str) -> str:
        """Strip every ``from __future__ import annotations`` line."""
        return "".join(
            line
            for line in source.splitlines(keepends=True)
            if line.strip() != c.Infra.FUTURE_ANNOTATIONS
        )


__all__: list[str] = ["FlextInfraUtilitiesTransformerHeader"]
