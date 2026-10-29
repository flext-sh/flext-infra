"""Centralized constants for the deps subpackage.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, ClassVar

from flext_infra._constants.config import FlextInfraConstantsConfig

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraConstantsDeps(FlextInfraConstantsConfig):
    """Deps infrastructure constants."""

    # NOTE: Hardcoded base path constants removed.
    # All tool settings phases now use dynamic discovery via
    # u.Infra.discover_python_dirs() (SSOT in FlextInfraUtilitiesDiscovery).
    # SKIP_DIRS was removed with the declared exclusion registry
    # (config/codegen.yaml exclusions -> CodegenConfigSpec projection).
    DEP_NAME_RE: ClassVar[t.RegexPattern] = re.compile(r"^\s*([A-Za-z0-9_.-]+)")
    PYPROJECT_DOCUMENT_MAPPING_ERROR: ClassVar[str] = (
        "pyproject document is not a TOML mapping"
    )
    PEP621_NAME_RE: ClassVar[t.RegexPattern] = re.compile(
        r"^\s*(?P<name>[A-Za-z0-9_.-]+)",
    )
    PEP621_REQUIREMENT_HEAD_RE: ClassVar[t.RegexPattern] = re.compile(
        r"^\s*(?P<head>[A-Za-z0-9_.-]+(?:\[[^\]]+\])?)",
    )
    # An internal requirement declares its integration line; the commit it
    # resolves to is recorded only in uv.lock, written by `make upg`.
    BANNER: ClassVar[str] = (
        "# @flext-generated: continuous\n"
        "# @flext-owner: flext-infra/config/codegen.yaml"
        " + flext-infra/src/flext_infra/templates/project/base/pyproject.toml.j2\n"
        "# @flext-adjust: MANAGED=conflict_sections + overwrite_project_keys."
        " CUSTOM=preserve_project_keys and [tool.*] outside conflict_sections."
        " Never edit this projection.\n"
        "# @flext-regenerate: make gen\n"
    )
    # Render provenance: the composition owner appends the running generator's
    # identity so every emitted artifact names the motor that rendered it.
    # A skew between this stamp and the consumed motor is drift the fixed-point
    # verbs detect (conform --mode check); the stamp makes the drift report
    # name both sides instead of a bare byte diff.
    RENDERED_BY_MARKER: ClassVar[str] = "# @flext-rendered-by: flext-infra "
    DEV_OPTIONAL_DEPS_MARKER: ClassVar[str] = (
        "# [MANAGED] consolidated development dependencies"
    )
    LEGACY_AUTO_MARKER: ClassVar[str] = (
        "# [AUTO] merged from dev/docs/security/test/typings"
    )
    LEGACY_AUTO_BANNER_LINE: ClassVar[str] = (
        "# Sections with [AUTO] are derived from workspace layout and dependencies."
    )
    DEPTRY_UNUSED_DEPENDENCY_CODE: ClassVar[str] = "DEP002"
    """Deptry rule code for a declared dependency the code never imports."""
    CONSOLE_SCRIPTS_ENTRY_POINT_GROUP: ClassVar[str] = "console_scripts"
    """Entry-point group naming the executables an installed distribution ships."""
    PYTEST_PLUGIN_ENTRY_POINT_GROUP: ClassVar[str] = "pytest11"
    """Entry-point group through which pytest autoloads an installed plugin."""
    DEPTRY_SCAN_COVERAGE_RE: ClassVar[t.RegexPattern] = re.compile(
        r"^Scanning (?P<count>[0-9]+) files?\.\.\.$",
    )
    """Native deptry import extraction's executed file count."""
    DEPENDENCY_GROUPS: ClassVar[str] = "dependency-groups"
    """PEP 735 dependency-groups table key."""
    MEMBER_DEV_PROVENANCE: ClassVar[str] = "flext: derived member environment"
    """Inline TOML comment tagging generated additions to a member's dev group."""


__all__: list[str] = ["FlextInfraConstantsDeps"]
