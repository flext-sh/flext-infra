"""Tests for flext_infra.constants — core namespace constants.

Tests cover Paths, Files, Gates, Status, and Excluded namespaces.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import config
from flext_infra.check.gate_registry import FlextInfraGateRegistry
from tests import c, tm


class TestsFlextInfraInfraConstantsCore:
    """Tests for Paths namespace constants."""

    @staticmethod
    def test_paths_constants_are_strings() -> None:
        """Test paths constants are strings."""
        tm.that(c.Infra.DEFAULT_SRC_DIR, is_=str)

    @staticmethod
    def test_files_constants_are_strings() -> None:
        """Test files constants are strings."""
        tm.that(c.PYPROJECT_FILENAME, is_=str)
        tm.that(c.Infra.MAKEFILE_FILENAME, is_=str)

    @staticmethod
    def test_gate_constants_resolve_config_check_gates() -> None:
        """Every config-declared default check gate resolves to a live gate.

        The gate vocabulary is config-owned (P0): instead of pinning the
        constant strings to today's literals, the constants must keep
        resolving the exact gate ids the generated Make surface will run.
        """
        registry = FlextInfraGateRegistry()
        for gate_id in config.Infra.codegen.make.check_gates_default:
            tm.that(registry.get(gate_id), none=False)

    @staticmethod
    def test_status_constants_are_result_status_members() -> None:
        """Test status constants are result status members."""
        tm.that(c.Infra.ResultStatus.PASSED, is_=c.Infra.ResultStatus)
        tm.that(c.Infra.ResultStatus.FAIL, is_=c.Infra.ResultStatus)
        tm.that(c.Infra.ResultStatus.OK, is_=c.Infra.ResultStatus)
        tm.that(c.Infra.ResultStatus.WARN, is_=c.Infra.ResultStatus)

    @staticmethod
    def test_analysis_excluded_dirs_derive_declared_registry() -> None:
        """Base walker exclusions derive the declared registry composition.

        The base set is config-owned (P0): it must equal exactly the union
        of the declared ``analysis_exclude`` artifacts, the declared
        tool-state roots, and the VCS-derived names, whatever valid values
        the config holds.
        """
        derived = frozenset(config.Infra.codegen.analysis_excluded_dirs)
        declared = (
            frozenset(
                artifact.name
                for artifact in config.Infra.codegen.artifacts
                if artifact.analysis_exclude
            )
            | frozenset(config.Infra.codegen.exclusions.tool_state)
            | frozenset((c.Infra.GIT_DIR, c.Infra.WORKTREES_DIRNAME))
        )
        tm.that(derived, is_=frozenset)
        tm.that(derived, eq=declared)

    @staticmethod
    def test_doc_excluded_dirs_compose_declared_sections() -> None:
        """Docs exclusions compose base, archive roots, and docs delta."""
        spec = config.Infra.codegen
        derived = frozenset(spec.docs_excluded_dirs)
        expected = (
            frozenset(spec.analysis_excluded_dirs)
            | frozenset(spec.exclusions.archive_roots)
            | frozenset(spec.exclusions.docs)
        )
        tm.that(derived, is_=frozenset)
        tm.that(derived, eq=expected)

    @staticmethod
    def test_pyproject_scan_excluded_dirs_compose_declared_sections() -> None:
        """Pyproject discovery composes base, archive roots, scan delta."""
        spec = config.Infra.codegen
        derived = frozenset(spec.pyproject_scan_excluded_dirs)
        expected = (
            frozenset(spec.analysis_excluded_dirs)
            | frozenset(spec.exclusions.archive_roots)
            | frozenset(spec.exclusions.pyproject_scan)
        )
        tm.that(derived, is_=frozenset)
        tm.that(derived, eq=expected)

    @staticmethod
    def test_check_excluded_dirs_compose_declared_sections() -> None:
        """Check exclusions compose base, archive roots, check delta."""
        spec = config.Infra.codegen
        derived = frozenset(spec.check_excluded_dirs)
        expected = (
            frozenset(spec.analysis_excluded_dirs)
            | frozenset(spec.exclusions.archive_roots)
            | frozenset(spec.exclusions.check)
        )
        tm.that(derived, is_=frozenset)
        tm.that(derived, eq=expected)

    @staticmethod
    def test_excluded_dirs_are_strings() -> None:
        """Derived exclusion projections are string sequences."""
        spec = config.Infra.codegen
        tm.that(spec.analysis_excluded_dirs, is_=tuple)
        tm.that(spec.docs_excluded_dirs, is_=tuple)
        tm.that(spec.pyproject_scan_excluded_dirs, is_=tuple)
        tm.that(spec.check_excluded_dirs, is_=tuple)
