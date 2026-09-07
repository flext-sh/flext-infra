"""TOML, JSON, and typed-mapping test utilities for flext-infra."""

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import override

from flext_infra import config, r, u
from flext_tests import tm
from tests import c, m, p, t


class TestsFlextInfraUtilitiesTomlMixin:
    """TOML, JSON payload, and typed-mapping test helpers."""

    @staticmethod
    def codegen_file_text(plan: m.Infra.CodegenFilePlan) -> str:
        """Decode the present text payload of a generated-file test plan."""
        return tm.not_none(plan.desired_content).decode(c.Cli.ENCODING_DEFAULT)

    class TomlReaderSequence(p.Infra.TomlReader):
        """Protocol-compatible TOML reader that replays typed results."""

        def __init__(self, values: t.SequenceOf[p.Result[t.JsonMapping]]) -> None:
            """Store the ordered TOML results for replay."""
            self._values = list(values)
            self._index = 0

        @override
        def read_plain(self, path: Path) -> p.Result[t.JsonMapping]:
            del path
            current = self._index
            self._index = current + 1
            if not self._values:
                return r[t.JsonMapping].fail("toml reader sequence is empty")
            return (
                self._values[current]
                if current < len(self._values)
                else self._values[-1]
            )

    @staticmethod
    def infra_mapping(value: t.Infra.InfraMapping) -> t.JsonMapping:
        """Provide the typed test helper `infra_mapping`."""
        result: t.JsonMapping = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(value)
        return result

    @staticmethod
    def toml_table_at(content: str, *path: str) -> t.JsonMapping:
        current = TestsFlextInfraUtilitiesTomlMixin.toml_mapping(tomllib.loads(content))
        for segment in path:
            current = TestsFlextInfraUtilitiesTomlMixin.toml_mapping(current[segment])
        return current

    @staticmethod
    def toml_strings_at(content: str, *path: str) -> t.StrSequence:
        if not path:
            return ()
        table = TestsFlextInfraUtilitiesTomlMixin.toml_table_at(content, *path[:-1])
        return TestsFlextInfraUtilitiesTomlMixin.toml_strings(table[path[-1]])

    @staticmethod
    def toml_tables_at(content: str, *path: str) -> t.SequenceOf[t.JsonMapping]:
        if not path:
            return ()
        table = TestsFlextInfraUtilitiesTomlMixin.toml_table_at(content, *path[:-1])
        values = TestsFlextInfraUtilitiesTomlMixin.toml_list(table[path[-1]])
        return tuple(
            TestsFlextInfraUtilitiesTomlMixin.toml_mapping(value) for value in values
        )

    @staticmethod
    def infra_mapping_result(value: t.Infra.InfraMapping) -> p.Result[t.JsonMapping]:
        """Provide the typed test helper `infra_mapping_result`."""
        return r[t.JsonMapping].ok(
            TestsFlextInfraUtilitiesTomlMixin.infra_mapping(value)
        )

    @staticmethod
    def tool_config_document() -> m.Infra.ToolConfigDocument:
        # Tests consume the validated config singleton; the removed utility
        # loader must not survive as a hidden test path.
        """Provide the typed test helper `tool_config_document`."""
        return config.Infra.tooling

    @staticmethod
    def toml_doc(text: str) -> t.Cli.TomlDocument:
        """Parse fixture TOML text into a document, failing closed.

        ``u.Cli.toml_parse_text`` is fail-soft because production parses
        untrusted files. A fixture literal is authored valid, so a ``None``
        here means the fixture itself is broken and the test must fail with
        that reason instead of propagating an optional into every call.
        """
        document = u.Cli.toml_parse_text(text)
        tm.that(document, none=False, msg="fixture TOML failed to parse")
        if document is None:
            msg = "fixture TOML failed to parse"
            raise TypeError(msg)
        return document

    @staticmethod
    def toml_doc_mapping(doc: t.Cli.TomlDocument) -> t.JsonMapping:
        """Provide the typed test helper `toml_doc_mapping`."""
        normalized: t.JsonValue = u.normalize_to_json_value(doc.unwrap())
        tm.that(normalized, is_=Mapping)
        if not isinstance(normalized, Mapping):
            msg = "normalized TOML document is not a mapping"
            raise TypeError(msg)
        result: dict[str, t.JsonValue] = dict(normalized)
        return result

    @staticmethod
    def toml_mapping(value: t.JsonPayload | None) -> t.JsonMapping:
        """Provide the typed test helper `toml_mapping`."""
        normalized: t.JsonValue = u.normalize_to_json_value(value)
        tm.that(normalized, is_=Mapping)
        if not isinstance(normalized, Mapping):
            msg = "normalized TOML value is not a mapping"
            raise TypeError(msg)
        result: dict[str, t.JsonValue] = dict(normalized)
        return result

    @staticmethod
    def toml_list(value: t.JsonPayload | None) -> t.JsonList:
        """Provide the typed test helper `toml_list`."""
        normalized: t.JsonValue = u.normalize_to_json_value(value)
        tm.that(normalized, is_=list)
        if not isinstance(normalized, list):
            msg = "normalized TOML value is not a list"
            raise TypeError(msg)
        result: list[t.JsonValue] = []
        result.extend(normalized)
        return tuple(result)

    @staticmethod
    def toml_strings(value: t.JsonPayload | None) -> t.StrSequence:
        """Provide the typed test helper `toml_strings`."""
        normalized: t.JsonValue = u.normalize_to_json_value(value)
        tm.that(normalized, is_=list)
        if not isinstance(normalized, list):
            msg = "normalized TOML strings are not a list"
            raise TypeError(msg)
        return tuple(str(item) for item in normalized)

    @staticmethod
    def strings(value: t.JsonPayload | None) -> t.StrSequence:
        """Validate and return one JSON payload as a string sequence."""
        result: t.StrSequence = t.Infra.STR_SEQ_ADAPTER.validate_python(value)
        return result


__all__: list[str] = ["TestsFlextInfraUtilitiesTomlMixin"]
