"""Tests for flext_infra.constants — Check, Github, Encoding, alias, and consistency.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_tests import tm

from tests import c


class TestFlextInfraConstantsCheckNamespace:
    """Tests for Check namespace constants."""

    def test_default_check_dirs_is_list(self) -> None:
        tm.that(c.Infra.DEFAULT_CHECK_DIRS, is_=tuple)

    def test_default_check_dirs_contains_standard_dirs(self) -> None:
        dirs = c.Infra.DEFAULT_CHECK_DIRS
        tm.that(dirs, contains="src")
        tm.that(dirs, contains="tests")
        tm.that(dirs, contains="examples")
        tm.that(dirs, contains="scripts")

    def test_check_dirs_subproject_is_list(self) -> None:
        tm.that(c.Infra.CHECK_DIRS_SUBPROJECT, is_=tuple)

    def test_check_dirs_subproject_excludes_scripts(self) -> None:
        dirs = c.Infra.CHECK_DIRS_SUBPROJECT
        tm.that(dirs, contains="src")
        tm.that(dirs, contains="tests")
        tm.that(dirs, contains="examples")
        assert "scripts" not in dirs

    def test_check_dirs_are_strings(self) -> None:
        for d in c.Infra.DEFAULT_CHECK_DIRS:
            tm.that(d, is_=str)
        for d in c.Infra.CHECK_DIRS_SUBPROJECT:
            tm.that(d, is_=str)


class TestFlextInfraConstantsGithubNamespace:
    """Tests for Github namespace constants."""

    def test_github_repo_url_constant(self) -> None:
        tm.that(
            c.Infra.GITHUB_REPO_URL,
            eq="https://github.com/flext-sh/flext",
        )

    def test_github_repo_name_constant(self) -> None:
        tm.that(c.Infra.GITHUB_REPO_NAME, eq="flext-sh/flext")

    def test_github_constants_are_strings(self) -> None:
        tm.that(c.Infra.GITHUB_REPO_URL, is_=str)
        tm.that(c.Infra.GITHUB_REPO_NAME, is_=str)


class TestFlextInfraConstantsEncodingNamespace:
    """Tests for Encoding namespace constants."""

    def test_default_encoding_constant(self) -> None:
        tm.that(c.Infra.ENCODING_DEFAULT, eq="utf-8")

    def test_encoding_constant_is_string(self) -> None:
        tm.that(c.Infra.ENCODING_DEFAULT, is_=str)


class TestFlextInfraConstantsAlias:
    """Tests for module-level alias."""

    def test_c_alias_is_string(self) -> None:
        tm.that(c, is_=type)

    def test_c_alias_provides_access_to_namespaces(self) -> None:
        pass

    def test_c_alias_access_to_constants(self) -> None:
        tm.that(c.Infra.VENV_BIN_REL, eq=".venv/bin")
        tm.that(c.Infra.ResultStatus.PASSED, eq="PASS")
        tm.that(c.Infra.PYPROJECT_FILENAME, eq="pyproject.toml")


class TestFlextInfraConstantsImmutability:
    """Tests for constant immutability."""

    def test_excluded_dirs_are_immutable(self) -> None:
        excluded = c.Infra.COMMON_EXCLUDED_DIRS
        tm.that(not hasattr(excluded, "add"), eq=True)

    def test_check_dirs_are_immutable(self) -> None:
        dirs = c.Infra.DEFAULT_CHECK_DIRS
        tm.that(not hasattr(dirs, "append"), eq=True)


class TestFlextInfraConstantsConsistency:
    """Tests for consistency across namespaces."""

    def test_all_status_values_are_uppercase(self) -> None:
        tm.that(c.Infra.ResultStatus.PASSED.isupper(), eq=True)
        tm.that(c.Infra.ResultStatus.FAIL.isupper(), eq=True)
        tm.that(c.Infra.ResultStatus.OK.isupper(), eq=True)
        tm.that(c.Infra.ResultStatus.WARN.isupper(), eq=True)

    def test_all_gate_values_are_lowercase(self) -> None:
        gates = [
            c.Infra.LINT,
            c.Infra.FORMAT,
            c.Infra.PYREFLY,
            c.Infra.MYPY,
            c.Infra.PYRIGHT,
            c.Infra.SECURITY,
            c.Infra.MARKDOWN,
            c.Infra.GO,
        ]
        for gate in gates:
            tm.that(gate.islower(), eq=True, msg=f"Gate {gate} should be lowercase")

    def test_excluded_dirs_no_duplicates(self) -> None:
        common = c.Infra.COMMON_EXCLUDED_DIRS
        doc = c.Infra.DOC_EXCLUDED_DIRS
        tm.that(len(common), eq=len(set(common)))
        tm.that(len(doc), eq=len(set(doc)))
