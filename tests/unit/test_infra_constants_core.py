"""Tests for flext_infra.constants — core namespace constants.

Tests cover Paths, Files, Gates, Status, and Excluded namespaces.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_tests import tm
from tests import c


class TestsFlextInfraInfraConstantsCore:
    """Tests for Paths namespace constants."""

    def test_venv_bin_rel_constant(self) -> None:
        """Expose the virtual-environment binary path contract."""
        tm.that(c.Infra.VENV_BIN_REL, eq=".venv/bin")

    def test_default_src_dir_constant(self) -> None:
        """Expose the default source-directory contract."""
        tm.that(c.Infra.DEFAULT_SRC_DIR, eq="src")

    def test_paths_constants_are_strings(self) -> None:
        """Represent public path constants as strings."""
        tm.that(c.Infra.VENV_BIN_REL, is_=str)
        tm.that(c.Infra.DEFAULT_SRC_DIR, is_=str)

    def test_pyproject_filename_constant(self) -> None:
        """Expose the canonical Python project filename."""
        tm.that(c.Infra.PYPROJECT_FILENAME, eq="pyproject.toml")

    def test_makefile_filename_constant(self) -> None:
        """Expose the canonical Make entrypoint filename."""
        tm.that(c.Infra.MAKEFILE_FILENAME, eq="Makefile")

    def test_base_mk_constant(self) -> None:
        """Expose the canonical generated Make include filename."""
        tm.that(c.Infra.BASE_MK, eq="base.mk")

    def test_files_constants_are_strings(self) -> None:
        """Represent public filename constants as strings."""
        tm.that(c.Infra.PYPROJECT_FILENAME, is_=str)
        tm.that(c.Infra.MAKEFILE_FILENAME, is_=str)
        tm.that(c.Infra.BASE_MK, is_=str)

    def test_gate_constants_exist(self) -> None:
        """Expose every supported validation gate identifier."""
        tm.that(c.Infra.LINT, eq="lint")
        tm.that(c.Infra.FORMAT, eq="format")
        tm.that(c.Infra.PYREFLY, eq="pyrefly")
        tm.that(c.Infra.MYPY, eq="mypy")
        tm.that(c.Infra.PYRIGHT, eq="pyright")
        tm.that(c.Infra.SECURITY, eq="security")
        tm.that(c.Infra.MARKDOWN, eq="markdown")

    def test_default_csv_contains_gates(self) -> None:
        """Include the required validation gates in the default gate sequence."""
        csv = c.Infra.DEFAULT_CSV
        tm.that(csv, contains="lint")
        tm.that(csv, contains="format")
        tm.that(csv, contains="mypy")
        tm.that(csv, contains="pyright")

    def test_default_csv_is_comma_separated(self) -> None:
        """Encode the default gate sequence as comma-separated strings."""
        csv = c.Infra.DEFAULT_CSV
        gates = csv.split(",")
        tm.that(gates, length_gt=0)
        for g in gates:
            tm.that(g, is_=str)

    def test_pass_status_constant(self) -> None:
        """Expose the successful check result status."""
        tm.that(c.Infra.ResultStatus.PASSED, eq="PASS")

    def test_fail_status_constant(self) -> None:
        """Expose the failed check result status."""
        tm.that(c.Infra.ResultStatus.FAIL, eq="FAIL")

    def test_ok_status_constant(self) -> None:
        """Expose the generic successful operation status."""
        tm.that(c.Infra.ResultStatus.OK, eq="OK")

    def test_warn_status_constant(self) -> None:
        """Expose the warning result status."""
        tm.that(c.Infra.ResultStatus.WARN, eq="WARN")

    def test_status_constants_are_result_status_members(self) -> None:
        """Type every public result status as a ResultStatus member."""
        tm.that(c.Infra.ResultStatus.PASSED, is_=c.Infra.ResultStatus)
        tm.that(c.Infra.ResultStatus.FAIL, is_=c.Infra.ResultStatus)
        tm.that(c.Infra.ResultStatus.OK, is_=c.Infra.ResultStatus)
        tm.that(c.Infra.ResultStatus.WARN, is_=c.Infra.ResultStatus)

    def test_common_excluded_dirs_is_string(self) -> None:
        """Expose common excluded directories as an immutable set."""
        excluded = c.Infra.COMMON_EXCLUDED_DIRS
        tm.that(excluded, is_=frozenset)

    def test_common_excluded_dirs_contains_standard_dirs(self) -> None:
        """Exclude standard repository, environment, cache, and build directories."""
        excluded = c.Infra.COMMON_EXCLUDED_DIRS
        tm.that(excluded, has=".git")
        tm.that(excluded, has=".venv")
        tm.that(excluded, has="__pycache__")
        tm.that(excluded, has="dist")
        tm.that(excluded, has="build")
        tm.that(excluded, has="venv")

    def test_doc_excluded_dirs_includes_common(self) -> None:
        """Apply every common directory exclusion to documentation scans."""
        doc_excluded = c.Infra.DOC_EXCLUDED_DIRS
        common = c.Infra.COMMON_EXCLUDED_DIRS
        tm.that(doc_excluded.issuperset(common), eq=True)

    def test_doc_excluded_dirs_includes_site(self) -> None:
        """Exclude generated documentation sites from source documentation scans."""
        tm.that(c.Infra.DOC_EXCLUDED_DIRS, has="site")

    def test_pyproject_skip_dirs_includes_common(self) -> None:
        """Apply every common exclusion while discovering Python projects."""
        skip_dirs = c.Infra.PYPROJECT_SKIP_DIRS
        common = c.Infra.COMMON_EXCLUDED_DIRS
        tm.that(skip_dirs.issuperset(common), eq=True)

    def test_pyproject_skip_dirs_includes_flext_dirs(self) -> None:
        """Exclude FLEXT temporary and disabled workspaces from project discovery."""
        skip_dirs = c.Infra.PYPROJECT_SKIP_DIRS
        tm.that(skip_dirs, has=".claude.disabled")
        tm.that(skip_dirs, has="context_test")
        tm.that(skip_dirs, has="rope_ws")
        tm.that(skip_dirs, has="tmp_flow_test")

    def test_check_excluded_dirs_includes_common(self) -> None:
        """Apply every common directory exclusion to validation checks."""
        check_excluded = c.Infra.CHECK_EXCLUDED_DIRS
        common = c.Infra.COMMON_EXCLUDED_DIRS
        tm.that(check_excluded.issuperset(common), eq=True)

    def test_excluded_dirs_are_strings(self) -> None:
        """Expose all specialized exclusion collections as immutable sets."""
        tm.that(c.Infra.DOC_EXCLUDED_DIRS, is_=frozenset)
        tm.that(c.Infra.PYPROJECT_SKIP_DIRS, is_=frozenset)
        tm.that(c.Infra.CHECK_EXCLUDED_DIRS, is_=frozenset)
