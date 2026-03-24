"""Tests for flext_infra.constants — core namespace constants.

Tests cover Paths, Files, Gates, Status, and Excluded namespaces.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_tests import tm

from flext_infra import c as infra_c


class TestFlextInfraConstantsPathsNamespace:
    """Tests for Paths namespace constants."""

    def test_venv_bin_rel_constant(self) -> None:
        tm.that(infra_c.Infra.Paths.VENV_BIN_REL, eq=".venv/bin")

    def test_default_src_dir_constant(self) -> None:
        tm.that(infra_c.Infra.Paths.DEFAULT_SRC_DIR, eq="src")

    def test_paths_constants_are_strings(self) -> None:
        tm.that(isinstance(infra_c.Infra.Paths.VENV_BIN_REL, str), eq=True)
        tm.that(isinstance(infra_c.Infra.Paths.DEFAULT_SRC_DIR, str), eq=True)


class TestFlextInfraConstantsFilesNamespace:
    """Tests for Files namespace constants."""

    def test_pyproject_filename_constant(self) -> None:
        tm.that(infra_c.Infra.Files.PYPROJECT_FILENAME, eq="pyproject.toml")

    def test_makefile_filename_constant(self) -> None:
        tm.that(infra_c.Infra.Files.MAKEFILE_FILENAME, eq="Makefile")

    def test_base_mk_constant(self) -> None:
        tm.that(infra_c.Infra.Files.BASE_MK, eq="base.mk")

    def test_go_mod_constant(self) -> None:
        tm.that(infra_c.Infra.Files.GO_MOD, eq="go.mod")

    def test_files_constants_are_strings(self) -> None:
        tm.that(isinstance(infra_c.Infra.Files.PYPROJECT_FILENAME, str), eq=True)
        tm.that(isinstance(infra_c.Infra.Files.MAKEFILE_FILENAME, str), eq=True)
        tm.that(isinstance(infra_c.Infra.Files.BASE_MK, str), eq=True)
        tm.that(isinstance(infra_c.Infra.Files.GO_MOD, str), eq=True)


class TestFlextInfraConstantsGatesNamespace:
    """Tests for Gates namespace constants."""

    def test_gate_constants_exist(self) -> None:
        tm.that(infra_c.Infra.Gates.LINT, eq="lint")
        tm.that(infra_c.Infra.Gates.FORMAT, eq="format")
        tm.that(infra_c.Infra.Gates.PYREFLY, eq="pyrefly")
        tm.that(infra_c.Infra.Gates.MYPY, eq="mypy")
        tm.that(infra_c.Infra.Gates.PYRIGHT, eq="pyright")
        tm.that(infra_c.Infra.Gates.SECURITY, eq="security")
        tm.that(infra_c.Infra.Gates.MARKDOWN, eq="markdown")
        tm.that(infra_c.Infra.Gates.GO, eq="go")

    def test_type_alias_gate(self) -> None:
        tm.that(infra_c.Infra.Gates.TYPE_ALIAS, eq="type")

    def test_default_csv_contains_gates(self) -> None:
        csv = infra_c.Infra.Gates.DEFAULT_CSV
        tm.that(csv, contains="lint")
        tm.that(csv, contains="format")
        tm.that(csv, contains="mypy")
        tm.that(csv, contains="pyright")

    def test_default_csv_is_comma_separated(self) -> None:
        csv = infra_c.Infra.Gates.DEFAULT_CSV
        gates = csv.split(",")
        tm.that(gates, length_gt=0)
        for g in gates:
            tm.that(isinstance(g, str), eq=True)


class TestFlextInfraConstantsStatusNamespace:
    """Tests for Status namespace constants."""

    def test_pass_status_constant(self) -> None:
        tm.that(infra_c.Infra.Status.PASS, eq="PASS")

    def test_fail_status_constant(self) -> None:
        tm.that(infra_c.Infra.Status.FAIL, eq="FAIL")

    def test_ok_status_constant(self) -> None:
        tm.that(infra_c.Infra.Status.OK, eq="OK")

    def test_warn_status_constant(self) -> None:
        tm.that(infra_c.Infra.Status.WARN, eq="WARN")

    def test_status_constants_are_strings(self) -> None:
        tm.that(isinstance(infra_c.Infra.Status.PASS, str), eq=True)
        tm.that(isinstance(infra_c.Infra.Status.FAIL, str), eq=True)
        tm.that(isinstance(infra_c.Infra.Status.OK, str), eq=True)
        tm.that(isinstance(infra_c.Infra.Status.WARN, str), eq=True)


class TestFlextInfraConstantsExcludedNamespace:
    """Tests for Excluded namespace constants."""

    def test_common_excluded_dirs_is_string(self) -> None:
        excluded = infra_c.Infra.Excluded.COMMON_EXCLUDED_DIRS
        tm.that(isinstance(excluded, frozenset), eq=True)

    def test_common_excluded_dirs_contains_standard_dirs(self) -> None:
        excluded = infra_c.Infra.Excluded.COMMON_EXCLUDED_DIRS
        assert ".git" in excluded
        assert ".venv" in excluded
        assert "__pycache__" in excluded
        assert "dist" in excluded
        assert "build" in excluded

    def test_doc_excluded_dirs_includes_common(self) -> None:
        doc_excluded = infra_c.Infra.Excluded.DOC_EXCLUDED_DIRS
        common = infra_c.Infra.Excluded.COMMON_EXCLUDED_DIRS
        tm.that(doc_excluded.issuperset(common), eq=True)

    def test_doc_excluded_dirs_includes_site(self) -> None:
        assert "site" in infra_c.Infra.Excluded.DOC_EXCLUDED_DIRS

    def test_pyproject_skip_dirs_includes_common(self) -> None:
        skip_dirs = infra_c.Infra.Excluded.PYPROJECT_SKIP_DIRS
        common = infra_c.Infra.Excluded.COMMON_EXCLUDED_DIRS
        tm.that(skip_dirs.issuperset(common), eq=True)

    def test_pyproject_skip_dirs_includes_flext_dirs(self) -> None:
        skip_dirs = infra_c.Infra.Excluded.PYPROJECT_SKIP_DIRS
        assert ".flext-deps" in skip_dirs
        assert ".sisyphus" in skip_dirs

    def test_check_excluded_dirs_includes_common(self) -> None:
        check_excluded = infra_c.Infra.Excluded.CHECK_EXCLUDED_DIRS
        common = infra_c.Infra.Excluded.COMMON_EXCLUDED_DIRS
        tm.that(check_excluded.issuperset(common), eq=True)

    def test_check_excluded_dirs_includes_flext_deps(self) -> None:
        assert ".flext-deps" in infra_c.Infra.Excluded.CHECK_EXCLUDED_DIRS

    def test_excluded_dirs_are_strings(self) -> None:
        tm.that(isinstance(infra_c.Infra.Excluded.DOC_EXCLUDED_DIRS, frozenset), eq=True)
        tm.that(isinstance(infra_c.Infra.Excluded.PYPROJECT_SKIP_DIRS, frozenset), eq=True)
        tm.that(isinstance(infra_c.Infra.Excluded.CHECK_EXCLUDED_DIRS, frozenset), eq=True)
