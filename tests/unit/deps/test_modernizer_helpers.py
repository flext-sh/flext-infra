from __future__ import annotations

from collections.abc import Mapping

import pytest
import tomlkit
import tomlkit.items
from flext_tests import tm
from tests import t, u
from tomlkit.toml_document import TOMLDocument


@pytest.fixture
def doc() -> TOMLDocument:
    return tomlkit.document()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("requests", "requests"),
        ("requests>=2.0", "requests"),
        ("requests @ git+https://github.com/psf/requests.git", "requests"),
        ("my_package", "my-package"),
        ("  requests  ", "requests"),
        ("", ""),
        ("Django>=3.0,<4.0", "django"),
    ],
)
def test_dep_name(raw: str, expected: str) -> None:
    tm.that(u.dep_name(raw), eq=expected)


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
    specs: t.StrSequence,
    expected_length: int,
    expected_names: t.StrSequence,
    check_sorted: bool,
) -> None:
    deduped = u.dedupe_specs(specs)
    tm.that(deduped, length=expected_length)
    names = [u.dep_name(spec) for spec in deduped]
    for expected_name in expected_names:
        tm.that(names, has=expected_name)
    if check_sorted and len(deduped) > 1:
        assert u.dep_name(deduped[0]) < u.dep_name(deduped[1])


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("test", "test"),
        (None, None),
        ({"key": "value"}, {"key": "value"}),
    ],
)
def test_unwrap_item(value: t.Infra.InfraValue, expected: t.Infra.InfraValue) -> None:
    tm.that(u.unwrap_item(value), eq=expected)


def test_unwrap_item_toml_item(doc: TOMLDocument) -> None:
    doc["key"] = "value"
    tm.that(u.unwrap_item(doc["key"]), eq="value")


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
    value: tomlkit.items.Item | None,
    expected: t.StrSequence,
) -> None:
    tm.that(u.as_string_list(value), eq=expected)


def test_as_string_list_toml_item(doc: TOMLDocument) -> None:
    doc["items"] = ["a", "b"]
    items_array: tomlkit.items.Item = _toml_item(["a", "b"])
    tm.that(u.as_string_list(items_array), eq=["a", "b"])
    doc["value"] = 42
    int_val: tomlkit.items.Item = _toml_item(42)
    tm.that(u.as_string_list(int_val), eq=[])


@pytest.mark.parametrize(
    ("items", "expected"),
    [(["a", "b", "c"], 3), ([], 0), (["single"], 1)],
)
def test_array(items: t.StrSequence, expected: int) -> None:
    tm.that(len(u.array(items)), eq=expected)


@pytest.mark.parametrize(
    "mode",
    ["new", "existing", "replace-non-table"],
)
def test_ensure_table(mode: str) -> None:
    parent = tomlkit.table()
    if mode == "existing":
        existing = tomlkit.table()
        parent["key"] = existing
        ensured = u.ensure_table(parent, "key")
        assert ensured is existing
        return
    if mode == "replace-non-table":
        parent["key"] = "string_value"
        _ = u.ensure_table(parent, "key")
        tm.that(parent, has="key")
        return
    _ = u.ensure_table(parent, "key")
    tm.that(parent, has="key")


def _doc_with_optional_deps(optional_deps: Mapping[str, t.StrSequence]) -> TOMLDocument:
    doc = tomlkit.document()
    doc["project"] = {"optional-dependencies": optional_deps}
    return doc


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
    optional_deps: Mapping[str, t.StrSequence],
    expected_dev: t.StrSequence,
    expected_docs: t.StrSequence,
) -> None:
    groups = u.project_dev_groups(_doc_with_optional_deps(optional_deps))
    tm.that(groups.get("dev", []), eq=expected_dev)
    tm.that(groups.get("docs", []), eq=expected_docs)


def test_project_dev_groups_missing_sections(doc: TOMLDocument) -> None:
    tm.that(u.project_dev_groups(doc), eq={})
    doc["project"] = {"name": "test"}
    tm.that(u.project_dev_groups(doc), eq={})


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
    optional_deps: Mapping[str, t.StrSequence],
    expected_length: int,
    expect_pytest: bool,
) -> None:
    result = u.canonical_dev_dependencies(_doc_with_optional_deps(optional_deps))
    tm.that(result, length=expected_length)
    if expect_pytest:
        assert any("pytest" in item for item in result)


def test_declared_dependency_names_collects_all_supported_groups() -> None:
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

    result = u.declared_dependency_names(doc)

    tm.that(result, has="requests")
    tm.that(result, has="flext-infra")
    tm.that(result, has="flext-tests")
    tm.that(result, has="flext-api")
    tm.that(result, has="pytest")
