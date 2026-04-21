"""Tests for flext_infra.constants — core namespace constants.

Tests cover Paths, Files, Gates, Status, and Excluded namespaces.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_tests import tm

from tests import c


class TestFlextInfraConstantsPathsNamespace:
    """Tests for Paths namespace constants."""

    def test_venv_bin_rel_constant(self) -> None:
        tm.that(c.Infra.VENV_BIN_REL, eq=".venv/bin")

    def test_default_src_dir_constant(self) -> None:
        tm.that(c.Infra.DEFAULT_SRC_DIR, eq="src")

    def test_paths_constants_are_strings(self) -> None:
        tm.that(c.Infra.VENV_BIN_REL, is_=str)
        tm.that(c.Infra.DEFAULT_SRC_DIR, is_=str)


class TestFlextInfraConstantsFilesNamespace:
    """Tests for Files namespace constants."""

    def test_pyproject_filename_constant(self) -> None:
        tm.that(c.Infra.PYPROJECT_FILENAME, eq="pyproject.toml")

    def test_makefile_filename_constant(self) -> None:
        tm.that(c.Infra.MAKEFILE_FILENAME, eq="Makefile")

    def test_base_mk_constant(self) -> None:
        tm.that(c.Infra.BASE_MK, eq="base.mk")

    def test_go_mod_constant(self) -> None:
        tm.that(c.Infra.GO_MOD, eq="go.mod")

    def test_files_constants_are_strings(self) -> None:
        tm.that(c.Infra.PYPROJECT_FILENAME, is_=str)
        tm.that(c.Infra.MAKEFILE_FILENAME, is_=str)
        tm.that(c.Infra.BASE_MK, is_=str)
        tm.that(c.Infra.GO_MOD, is_=str)


class TestFlextInfraConstantsGatesNamespace:
    """Tests for Gates namespace constants."""

    def test_gate_constants_exist(self) -> None:
        tm.that(c.Infra.LINT, eq="lint")
        tm.that(c.Infra.FORMAT, eq="format")
        tm.that(c.Infra.PYREFLY, eq="pyrefly")
        tm.that(c.Infra.MYPY, eq="mypy")
        tm.that(c.Infra.PYRIGHT, eq="pyright")
        tm.that(c.Infra.SECURITY, eq="security")
        tm.that(c.Infra.MARKDOWN, eq="markdown")
        tm.that(c.Infra.GO, eq="go")

    def test_type_alias_gate(self) -> None:
        tm.that(c.Infra.TYPE_ALIAS, eq="type")

    def test_default_csv_contains_gates(self) -> None:
        csv = c.Infra.DEFAULT_CSV
        tm.that(csv, contains="lint")
        tm.that(csv, contains="format")
        tm.that(csv, contains="mypy")
        tm.that(csv, contains="pyright")

    def test_default_csv_is_comma_separated(self) -> None:
        csv = c.Infra.DEFAULT_CSV
        gates = csv.split(",")
        tm.that(gates, length_gt=0)
        for g in gates:
            tm.that(g, is_=str)


class TestFlextInfraConstantsStatusNamespace:
    """Tests for Status namespace constants."""

    def test_pass_status_constant(self) -> None:
        tm.that(c.Infra.ResultStatus.PASSED, eq="PASS")

    def test_fail_status_constant(self) -> None:
        tm.that(c.Infra.ResultStatus.FAIL, eq="FAIL")

    def test_ok_status_constant(self) -> None:
        tm.that(c.Infra.ResultStatus.OK, eq="OK")

    def test_warn_status_constant(self) -> None:
        tm.that(c.Infra.ResultStatus.WARN, eq="WARN")

    def test_status_constants_are_result_status_members(self) -> None:
        tm.that(c.Infra.ResultStatus.PASSED, is_=c.Infra.ResultStatus)
        tm.that(c.Infra.ResultStatus.FAIL, is_=c.Infra.ResultStatus)
        tm.that(c.Infra.ResultStatus.OK, is_=c.Infra.ResultStatus)
        tm.that(c.Infra.ResultStatus.WARN, is_=c.Infra.ResultStatus)


class TestFlextInfraConstantsExcludedNamespace:
    """Tests for Excluded namespace constants."""

    def test_common_excluded_dirs_is_string(self) -> None:
        excluded = c.Infra.COMMON_EXCLUDED_DIRS
        tm.that(excluded, is_=frozenset)

    def test_common_excluded_dirs_contains_standard_dirs(self) -> None:
        excluded = c.Infra.COMMON_EXCLUDED_DIRS
        assert ".git" in excluded
        assert ".venv" in excluded
        assert "__pycache__" in excluded
        assert "dist" in excluded
        assert "build" in excluded

    def test_doc_excluded_dirs_includes_common(self) -> None:
        doc_excluded = c.Infra.DOC_EXCLUDED_DIRS
        common = c.Infra.COMMON_EXCLUDED_DIRS
        tm.that(doc_excluded.issuperset(common), eq=True)

    def test_doc_excluded_dirs_includes_site(self) -> None:
        assert "site" in c.Infra.DOC_EXCLUDED_DIRS

    def test_pyproject_skip_dirs_includes_common(self) -> None:
        skip_dirs = c.Infra.PYPROJECT_SKIP_DIRS
        common = c.Infra.COMMON_EXCLUDED_DIRS
        tm.that(skip_dirs.issuperset(common), eq=True)

    def test_pyproject_skip_dirs_includes_flext_dirs(self) -> None:
        skip_dirs = c.Infra.PYPROJECT_SKIP_DIRS
        assert ".flext-deps" in skip_dirs
        assert ".sisyphus" in skip_dirs

    def test_check_excluded_dirs_includes_common(self) -> None:
        check_excluded = c.Infra.CHECK_EXCLUDED_DIRS
        common = c.Infra.COMMON_EXCLUDED_DIRS
        tm.that(check_excluded.issuperset(common), eq=True)

    def test_check_excluded_dirs_includes_flext_deps(self) -> None:
        assert ".flext-deps" in c.Infra.CHECK_EXCLUDED_DIRS

    def test_excluded_dirs_are_strings(self) -> None:
        tm.that(c.Infra.DOC_EXCLUDED_DIRS, is_=frozenset)
        tm.that(c.Infra.PYPROJECT_SKIP_DIRS, is_=frozenset)
        tm.that(c.Infra.CHECK_EXCLUDED_DIRS, is_=frozenset)
