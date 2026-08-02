"""Tests for flext_infra.constants — Check, Github, Encoding, alias, and consistency.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_tests import tm
from tests import c


class TestsFlextInfraInfraConstantsExtra:
    """Tests for Check namespace constants."""

    def test_check_dirs_subproject_is_list(self) -> None:
        """Expose subproject check directories as an immutable tuple."""
        tm.that(c.Infra.CHECK_DIRS_SUBPROJECT, is_=tuple)

    def test_check_dirs_subproject_is_productive_src_only(self) -> None:
        """Restrict subproject checks to the productive source directory."""
        tm.that(c.Infra.CHECK_DIRS_SUBPROJECT, eq=("src",))

    def test_check_dirs_are_strings(self) -> None:
        """Represent every subproject check directory as a string."""
        for d in c.Infra.CHECK_DIRS_SUBPROJECT:
            tm.that(d, is_=str)

    def test_github_repo_url_constant(self) -> None:
        """Expose the canonical FLEXT GitHub repository URL."""
        tm.that(c.Infra.GITHUB_REPO_URL, eq="https://github.com/flext-sh/flext")

    def test_github_repo_name_constant(self) -> None:
        """Expose the canonical FLEXT GitHub repository slug."""
        tm.that(c.Infra.GITHUB_REPO_NAME, eq="flext-sh/flext")

    def test_github_constants_are_strings(self) -> None:
        """Represent public GitHub repository identifiers as strings."""
        tm.that(c.Infra.GITHUB_REPO_URL, is_=str)
        tm.that(c.Infra.GITHUB_REPO_NAME, is_=str)

    def test_default_encoding_constant(self) -> None:
        """Expose UTF-8 as the default text encoding contract."""
        tm.that(c.Infra.ENCODING_DEFAULT, eq="utf-8")

    def test_encoding_constant_is_string(self) -> None:
        """Represent the default encoding as a string."""
        tm.that(c.Infra.ENCODING_DEFAULT, is_=str)

    def test_c_alias_is_string(self) -> None:
        """Expose the constants facade alias as a class namespace."""
        tm.that(c, is_=type)

    def test_c_alias_access_to_constants(self) -> None:
        """Resolve public constants through the canonical constants facade."""
        tm.that(c.Infra.VENV_BIN_REL, eq=".venv/bin")
        tm.that(c.Infra.ResultStatus.PASSED, eq="PASS")
        tm.that(c.Infra.PYPROJECT_FILENAME, eq="pyproject.toml")

    def test_excluded_dirs_are_immutable(self) -> None:
        """Keep the common directory exclusion collection immutable."""
        excluded = c.Infra.COMMON_EXCLUDED_DIRS
        tm.that(excluded, is_=frozenset)

    def test_all_status_values_are_uppercase(self) -> None:
        """Encode every result status using uppercase protocol values."""
        tm.that(c.Infra.ResultStatus.PASSED.isupper(), eq=True)
        tm.that(c.Infra.ResultStatus.FAIL.isupper(), eq=True)
        tm.that(c.Infra.ResultStatus.OK.isupper(), eq=True)
        tm.that(c.Infra.ResultStatus.WARN.isupper(), eq=True)

    def test_all_gate_values_are_lowercase(self) -> None:
        """Encode every validation gate identifier in lowercase."""
        gates = [
            c.Infra.LINT,
            c.Infra.FORMAT,
            c.Infra.PYREFLY,
            c.Infra.MYPY,
            c.Infra.PYRIGHT,
            c.Infra.SECURITY,
            c.Infra.MARKDOWN,
        ]
        for gate in gates:
            tm.that(gate.islower(), eq=True, msg=f"Gate {gate} should be lowercase")

    def test_excluded_dirs_no_duplicates(self) -> None:
        """Keep common and documentation directory exclusions unique."""
        common = c.Infra.COMMON_EXCLUDED_DIRS
        doc = c.Infra.DOC_EXCLUDED_DIRS
        tm.that(len(common), eq=len(set(common)))
        tm.that(len(doc), eq=len(set(doc)))
