from __future__ import annotations

from collections.abc import (
    Mapping,
)
from pathlib import Path

import pytest
import tomlkit
import tomlkit.items
from flext_tests import tm
from tomlkit.toml_document import TOMLDocument

from tests import c, t, u


@pytest.fixture
def doc() -> TOMLDocument:
    return tomlkit.document()


def _toml_item(value: str | int | t.StrSequence) -> tomlkit.items.Item:
    if isinstance(value, str):
        return tomlkit.items.String.from_raw(value)
    if isinstance(value, int):
        return tomlkit.items.Integer(
            value,
            trivia=tomlkit.items.Trivia(),
            raw=str(value),
        )
    str_items: list[tomlkit.items.Item] = [
        tomlkit.items.String.from_raw(v) for v in value
    ]
    return tomlkit.items.Array(str_items, trivia=tomlkit.items.Trivia())


def _toml_table_item() -> tomlkit.items.Item:
    tbl = tomlkit.table()
    tbl["key"] = "value"
    return tbl


def _doc_with_optional_deps(optional_deps: Mapping[str, t.StrSequence]) -> TOMLDocument:
    doc = tomlkit.document()
    doc["project"] = {"optional-dependencies": optional_deps}
    return doc


class TestsFlextInfraDepsModernizerHelpers:
    """Behavior contract for test_modernizer_helpers."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("requests", "requests"),
            ("requests>=2.0", "requests"),
            ("requests @ git+https://github.com/psf/requests.git", "requests"),
            ("../flext-core", "flext-core"),
            ("my_package", "my_package"),
            ("  requests  ", "requests"),
            ("", None),
            ("Django>=3.0,<4.0", "django"),
        ],
    )
    def test_dep_name(self, raw: str, expected: str | None) -> None:
        assert u.Infra.dep_name(raw) == expected

    @pytest.mark.parametrize(
        ("specs", "expected_length", "expected_names", "check_sorted"),
        [
            (["requests>=2.0", "django>=3.0"], 2, ["requests", "django"], False),
            (["requests>=2.0", "requests>=2.1", "django>=3.0"], 2, ["requests"], False),
            ([], 0, [], False),
            (["zebra>=1.0", "apple>=1.0"], 2, [], True),
            (["Requests>=2.0", "requests>=2.1"], 1, ["requests"], False),
        ],
    )
    def test_dedupe_specs(
        self,
        specs: t.StrSequence,
        expected_length: int,
        expected_names: t.StrSequence,
        check_sorted: bool,
    ) -> None:
        deduped = u.Infra.dedupe_specs(specs)
        tm.that(deduped, length=expected_length)
        names = [u.Infra.dep_name(spec) for spec in deduped]
        for expected_name in expected_names:
            tm.that(names, has=expected_name)
        if check_sorted and len(deduped) > 1:
            left = u.Infra.dep_name(deduped[0])
            right = u.Infra.dep_name(deduped[1])
            assert left is not None
            assert right is not None
            assert left < right

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("test", "test"),
            (None, None),
            ({"key": "value"}, {"key": "value"}),
        ],
    )
    def test_unwrap_item(
        self,
        value: t.Cli.TomlMappingSource | None,
        expected: t.Infra.InfraValue,
    ) -> None:
        actual = None if value is None else u.Cli.toml_unwrap_item(value)
        assert actual == expected

    def test_unwrap_item_toml_item(self, doc: TOMLDocument) -> None:
        doc["key"] = "value"
        assert u.Cli.toml_unwrap_item(doc["key"]) == "value"

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (_toml_item(["a", "b", "c"]), ["a", "b", "c"]),
            (None, []),
            (_toml_item("test"), []),
            (_toml_table_item(), []),
            (_toml_item(42), []),
        ],
    )
    def test_as_string_list(
        self,
        value: tomlkit.items.Item | None,
        expected: t.StrSequence,
    ) -> None:
        actual: t.StrSequence = (
            [] if value is None else u.Cli.toml_as_string_list(value)
        )
        assert list(actual) == list(expected)

    def test_as_string_list_toml_item(self, doc: TOMLDocument) -> None:
        doc["items"] = ["a", "b"]
        items_array: tomlkit.items.Item = _toml_item(["a", "b"])
        assert u.Cli.toml_as_string_list(items_array) == ["a", "b"]
        doc["value"] = 42
        int_val: tomlkit.items.Item = _toml_item(42)
        assert u.Cli.toml_as_string_list(int_val) == []

    @pytest.mark.parametrize(
        ("items", "expected"),
        [(["a", "b", "c"], 3), ([], 0), (["single"], 1)],
    )
    def test_array(self, items: t.StrSequence, expected: int) -> None:
        tm.that(len(u.Cli.toml_array(items)), eq=expected)

    @pytest.mark.parametrize(
        "mode",
        ["new", "existing", "replace-non-table"],
    )
    def test_ensure_table(self, mode: str) -> None:
        parent = tomlkit.table()
        if mode == "existing":
            existing = tomlkit.table()
            parent["key"] = existing
            ensured = u.Cli.toml_ensure_table(parent, "key")
            assert ensured is existing
            return
        if mode == "replace-non-table":
            parent["key"] = "string_value"
            _ = u.Cli.toml_ensure_table(parent, "key")
            tm.that(parent, has="key")
            return
        _ = u.Cli.toml_ensure_table(parent, "key")
        tm.that(parent, has="key")

    @pytest.mark.parametrize(
        ("optional_deps", "expected_dev", "expected_docs"),
        [
            (
                {
                    "dev": ["pytest"],
                    "docs": ["sphinx"],
                    "security": ["bandit"],
                    "test": ["coverage"],
                    "typings": ["mypy"],
                },
                ["pytest"],
                ["sphinx"],
            ),
            ({"dev": ["pytest"]}, ["pytest"], []),
            ({}, [], []),
        ],
    )
    def test_project_dev_groups(
        self,
        optional_deps: Mapping[str, t.StrSequence],
        expected_dev: t.StrSequence,
        expected_docs: t.StrSequence,
    ) -> None:
        groups = u.Infra.project_dev_groups(_doc_with_optional_deps(optional_deps))
        assert list(groups.get("dev", [])) == list(expected_dev)
        assert list(groups.get("docs", [])) == list(expected_docs)

    def test_project_dev_groups_missing_sections(self, doc: TOMLDocument) -> None:
        assert u.Infra.project_dev_groups(doc) == {}
        doc["project"] = {"name": "test"}
        assert u.Infra.project_dev_groups(doc) == {}

    @pytest.mark.parametrize(
        ("optional_deps", "expected_length", "expect_pytest"),
        [
            (
                {
                    "dev": ["pytest"],
                    "docs": ["sphinx"],
                    "security": ["bandit"],
                    "test": ["coverage"],
                    "typings": ["mypy"],
                },
                5,
                True,
            ),
            ({}, 0, False),
            ({"dev": ["pytest>=7.0"], "test": ["pytest>=6.0"]}, 1, True),
        ],
    )
    def test_canonical_dev_dependencies(
        self,
        optional_deps: Mapping[str, t.StrSequence],
        expected_length: int,
        expect_pytest: bool,
    ) -> None:
        result = u.Infra.canonical_dev_dependencies(
            _doc_with_optional_deps(optional_deps)
        )
        tm.that(result, length=expected_length)
        if expect_pytest:
            assert any("pytest" in item for item in result)

    def test_declared_dependency_names_collects_all_supported_groups(self) -> None:
        doc = tomlkit.document()
        doc["project"] = {
            "dependencies": ["requests>=2.0"],
            "optional-dependencies": {
                "dev": ["flext-infra", "pytest>=8.0"],
                "docs": ["mkdocs>=1.6"],
            },
        }
        doc["dependency-groups"] = {
            "test": ["flext-tests", "coverage>=7.0"],
        }
        doc["tool"] = {
            "poetry": {
                "dependencies": {
                    "python": ">=3.13,<3.14",
                    "flext-api": "^0.1.0",
                },
            },
        }

        result = u.Infra.declared_dependency_names(doc)

        tm.that(result, has="requests")
        tm.that(result, has="flext-infra")
        tm.that(result, has="flext-tests")

    def test_locked_dependency_versions_skips_non_registry_sources(
        self,
        tmp_path: Path,
    ) -> None:
        lock_path = tmp_path / "uv.lock"
        lock_path.write_text(
            (
                "version = 1\n"
                "[manifest]\n"
                'members = ["flext-core"]\n'
                "[[package]]\n"
                'name = "requests"\n'
                'version = "2.32.4"\n'
                'source = { registry = "https://pypi.org/simple" }\n'
                "[[package]]\n"
                'name = "flext-core"\n'
                'version = "0.12.0-dev"\n'
                'source = { editable = "." }\n'
            ),
            encoding="utf-8",
        )

        tm.that(
            u.Infra.locked_dependency_versions(lock_path),
            eq={"requests": "2.32.4"},
        )

    def test_rewrite_requirement_constraint_preserves_extras_and_markers(self) -> None:
        tm.that(
            u.Infra.rewrite_requirement_constraint(
                "httpx[socks]>=0.1; python_version < '3.14'",
                locked_versions={"httpx": "0.28.1"},
                policy=c.Infra.DependencyConstraintPolicy.FLOOR,
            ),
            eq="httpx[socks]>=0.28.1; python_version < '3.14'",
        )
