"""Test modernizer helpers behavior."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_tests import tm
from tests import u

if TYPE_CHECKING:
    from pathlib import Path

    from tests import t


@pytest.fixture
def doc() -> t.Cli.TomlDocument:
    """Provide a mutable TOML document fixture."""
    return u.Cli.toml_document()


def _toml_table_item() -> t.Cli.TomlItem:
    tbl = u.Cli.toml_table()
    tbl["key"] = "value"
    return tbl


def _doc_with_optional_deps(
    optional_deps: t.MappingKV[str, t.StrSequence],
) -> t.Cli.TomlDocument:
    doc = u.Cli.toml_document()
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
        """Verify dep name."""
        tm.that(u.Infra.dep_name(raw), eq=expected)

    @pytest.mark.parametrize(
        ("payload", "expected"),
        [
            pytest.param(
                {
                    "project": {
                        "dependencies": [
                            "selected @ git+https://example.invalid/repository.git"
                        ]
                    }
                },
                False,
                id="project-direct",
            ),
            pytest.param(
                {
                    "project": {
                        "optional-dependencies": {
                            "dev": ["selected @ https://example.invalid/archive.whl"]
                        }
                    }
                },
                False,
                id="optional-direct",
            ),
            pytest.param(
                {
                    "dependency-groups": {
                        "dev": [
                            (
                                "selected[extra] @ file:///workspace/selected; "
                                "python_version < '3.14'"
                            )
                        ]
                    }
                },
                False,
                id="group-direct-with-marker",
            ),
            pytest.param(
                {
                    "tool": {
                        "poetry": {
                            "dependencies": {
                                "selected": {
                                    "git": "https://example.invalid/repository.git"
                                }
                            }
                        }
                    }
                },
                False,
                id="poetry-root-git",
            ),
            pytest.param(
                {
                    "tool": {
                        "poetry": {
                            "dependencies": {
                                "selected": {
                                    "url": "https://example.invalid/archive.whl"
                                }
                            }
                        }
                    }
                },
                False,
                id="poetry-root-url",
            ),
            pytest.param(
                {
                    "tool": {
                        "poetry": {
                            "group": {
                                "dev": {
                                    "dependencies": {
                                        "selected": {"path": "../selected"}
                                    }
                                }
                            }
                        }
                    }
                },
                False,
                id="poetry-group-path",
            ),
            pytest.param(
                {"project": {"dependencies": ["selected>=1.0"]}},
                True,
                id="project-registry",
            ),
            pytest.param(
                {"project": {"optional-dependencies": {"dev": ["selected"]}}},
                True,
                id="optional-registry",
            ),
            pytest.param(
                {"dependency-groups": {"dev": ["selected~=1.0"]}},
                True,
                id="group-registry",
            ),
            pytest.param(
                {"tool": {"poetry": {"dependencies": {"selected": ">=1.0"}}}},
                True,
                id="poetry-root-registry",
            ),
            pytest.param(
                {
                    "tool": {
                        "poetry": {
                            "group": {
                                "dev": {
                                    "dependencies": {"selected": {"version": ">=1.0"}}
                                }
                            }
                        }
                    }
                },
                True,
                id="poetry-group-registry",
            ),
            pytest.param(
                {
                    "project": {
                        "dependencies": [
                            "selected @ git+https://example.invalid/repository.git"
                        ]
                    },
                    "tool": {"poetry": {"dependencies": {"selected": ">=1.0"}}},
                },
                True,
                id="mixed-registry-wins",
            ),
        ],
    )
    def test_dependency_registry_lock_classification_covers_all_tables(
        self, payload: t.JsonMapping, *, expected: bool
    ) -> None:
        """Classify the selected source consistently across every supported table."""
        declarations = u.Infra.dependency_declarations_from_payload(payload)

        tm.that(declarations, length=1)
        tm.that(declarations[0].name, eq="selected")
        tm.that(declarations[0].registry_required, eq=expected)
        tm.that(
            u.Infra.declared_dependency_names_from_payload(payload), eq=("selected",)
        )
        tm.that(
            u.Infra.dependency_requires_registry_lock_from_payload(payload, "selected"),
            eq=expected,
        )

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
        *,
        check_sorted: bool,
    ) -> None:
        """Verify dedupe specs."""
        deduped = u.Infra.dedupe_specs(specs)
        tm.that(deduped, length=expected_length)
        names = [u.Infra.dep_name(spec) for spec in deduped]
        for expected_name in expected_names:
            tm.that(names, has=expected_name)
        if check_sorted and len(deduped) > 1:
            left = u.Infra.dep_name(deduped[0])
            right = u.Infra.dep_name(deduped[1])
            tm.that(left, none=False)
            tm.that(right, none=False)
            if left is None or right is None:
                pytest.fail("deduplicated dependency names must be present")
            tm.that(left < right, eq=True)

    @pytest.mark.parametrize(
        ("value", "expected"),
        [("test", "test"), (None, None), ({"key": "value"}, {"key": "value"})],
    )
    def test_unwrap_item(
        self, value: t.Cli.TomlMappingSource | None, expected: t.Infra.InfraValue
    ) -> None:
        """Verify unwrap item."""
        actual = None if value is None else u.Cli.toml_unwrap_item(value)
        tm.that(actual, eq=expected)

    def test_unwrap_item_toml_item(self, doc: t.Cli.TomlDocument) -> None:
        """Verify unwrap item toml item."""
        doc["key"] = "value"
        tm.that(u.Cli.toml_unwrap_item(doc["key"]), eq="value")

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (u.Cli.toml_item_from_json_value(["a", "b", "c"]), ["a", "b", "c"]),
            (None, []),
            (u.Cli.toml_item_from_json_value("test"), []),
            (_toml_table_item(), []),
            (u.Cli.toml_item_from_json_value(42), []),
        ],
    )
    def test_as_string_list(
        self, value: t.Cli.TomlItem | None, expected: t.StrSequence
    ) -> None:
        """Verify as string list."""
        actual: t.StrSequence = (
            [] if value is None else u.Cli.toml_as_string_list(value)
        )
        tm.that(list(actual), eq=list(expected))

    def test_as_string_list_toml_item(self, doc: t.Cli.TomlDocument) -> None:
        """Verify as string list toml item."""
        doc["items"] = ["a", "b"]
        items_array = u.Cli.toml_item_from_json_value(["a", "b"])
        tm.that(u.Cli.toml_as_string_list(items_array), eq=["a", "b"])
        doc["value"] = 42
        int_val = u.Cli.toml_item_from_json_value(42)
        tm.that(u.Cli.toml_as_string_list(int_val), eq=[])

    @pytest.mark.parametrize(
        ("items", "expected"), [(["a", "b", "c"], 3), ([], 0), (["single"], 1)]
    )
    def test_array(self, items: t.StrSequence, expected: int) -> None:
        """Verify TOML array construction preserves item count."""
        tm.that(len(u.Cli.toml_array(items)), eq=expected)

    @pytest.mark.parametrize("mode", ["new", "existing", "replace-non-table"])
    def test_ensure_table(self, mode: str) -> None:
        """Verify ensure table."""
        parent = u.Cli.toml_table()
        if mode == "existing":
            existing = u.Cli.toml_table()
            parent["key"] = existing
            ensured = u.Cli.toml_ensure_table(parent, "key")
            tm.that(ensured is existing, eq=True)
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
        optional_deps: t.MappingKV[str, t.StrSequence],
        expected_dev: t.StrSequence,
        expected_docs: t.StrSequence,
    ) -> None:
        """Verify project dev groups."""
        groups = u.Infra.project_dev_groups(_doc_with_optional_deps(optional_deps))
        tm.that(list(groups.get("dev", [])), eq=list(expected_dev))
        tm.that(list(groups.get("docs", [])), eq=list(expected_docs))

    def test_project_dev_groups_missing_sections(self, doc: t.Cli.TomlDocument) -> None:
        """Verify project dev groups missing sections."""
        tm.that(u.Infra.project_dev_groups(doc), eq={})
        doc["project"] = {"name": "test"}
        tm.that(u.Infra.project_dev_groups(doc), eq={})

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
        optional_deps: t.MappingKV[str, t.StrSequence],
        expected_length: int,
        *,
        expect_pytest: bool,
    ) -> None:
        """Verify canonical dev dependencies."""
        result = u.Infra.canonical_dev_dependencies(
            _doc_with_optional_deps(optional_deps)
        )
        tm.that(result, length=expected_length)
        if expect_pytest:
            tm.that(any("pytest" in item for item in result), eq=True)

    def test_declared_dependency_names_collects_all_supported_groups(self) -> None:
        """Verify declared dependency names collects all supported groups."""
        doc = u.Cli.toml_document()
        doc["project"] = {
            "dependencies": ["requests>=2.0"],
            "optional-dependencies": {
                "dev": ["flext-infra", "pytest>=8.0"],
                "docs": ["mkdocs>=1.6"],
            },
        }
        doc["dependency-groups"] = {"test": ["flext-tests", "coverage>=7.0"]}
        doc["tool"] = {
            "poetry": {
                "dependencies": {"python": ">=3.13,<3.14", "flext-api": "^0.1.0"}
            }
        }

        result = u.Infra.declared_dependency_names(doc)

        tm.that(result, has="requests")
        tm.that(result, has="flext-infra")
        tm.that(result, has="flext-tests")

    def test_locked_dependency_versions_skips_non_registry_sources(
        self, tmp_path: Path
    ) -> None:
        """Verify locked dependency versions skips non registry sources."""
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
            u.Infra.locked_dependency_versions(lock_path), eq={"requests": "2.32.4"}
        )

    def test_locked_dependency_state_accepts_a_git_only_inventory(
        self, tmp_path: Path
    ) -> None:
        """Distinguish one valid Git-only lock from invalid or missing TOML."""
        lock_path = tmp_path / "uv.lock"
        lock_path.write_text(
            (
                "version = 1\n"
                "[[package]]\n"
                'name = "selected"\n'
                'version = "1.0.0"\n'
                'source = { git = "https://example.invalid/repository.git#revision" }\n'
            ),
            encoding="utf-8",
        )

        state = tm.ok(u.Infra.locked_dependency_state(lock_path))

        tm.that(state.package_names, eq=("selected",))
        tm.that(state.registry_versions, eq={})
        tm.that(u.Infra.locked_dependency_versions(lock_path), eq={})

    @pytest.mark.parametrize(
        "content",
        [None, "[invalid", "version = 1\n"],
        ids=["missing", "invalid-toml", "missing-packages"],
    )
    def test_locked_dependency_state_rejects_an_invalid_inventory(
        self, tmp_path: Path, content: str | None
    ) -> None:
        """Fail closed when the lock cannot prove its package inventory."""
        lock_path = tmp_path / "uv.lock"
        if content is not None:
            lock_path.write_text(content, encoding="utf-8")

        tm.fail(u.Infra.locked_dependency_state(lock_path))

    def test_rewrite_requirement_constraint_preserves_extras_and_markers(self) -> None:
        """Verify rewrite requirement constraint preserves extras and markers."""
        tm.that(
            u.Infra.rewrite_requirement_constraint(
                "httpx[socks]>=0.1; python_version < '3.14'",
                locked_versions={"httpx": "0.28.1"},
            ),
            eq="httpx[socks]>=0.28.1; python_version < '3.14'",
        )
