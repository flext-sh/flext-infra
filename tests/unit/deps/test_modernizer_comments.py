"""Comment injection phase tests for deps modernizer.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pytest
from flext_tests import tm

from flext_infra import c, u
from flext_infra.deps.phases.inject_comments import FlextInfraInjectCommentsPhase


class TestsFlextInfraDepsModernizerComments:
    """Tests comment injection behavior."""

    @pytest.mark.parametrize("rendered", ["", " \n", "# custom only\n"])
    def test_inject_comments_rejects_semantically_empty_toml(
        self, rendered: str
    ) -> None:
        """Fail loud when valid TOML carries no semantic configuration data."""
        with pytest.raises(ValueError, match="non-empty TOML"):
            FlextInfraInjectCommentsPhase().apply(rendered)

    def test_inject_comments_preserves_lookup_after_managed_table_trivia(self) -> None:
        """Preserve nested optional-dependency lookups after removing trivia."""
        rendered = (
            "[project.optional-dependencies]\n"
            f"{c.Infra.DEV_OPTIONAL_DEPS_MARKER}\n"
            "dev = ['pytest']\n"
        )

        result, _changes = FlextInfraInjectCommentsPhase().apply(rendered)
        document = u.Cli.toml_parse_text(result)
        if document is None:
            pytest.fail("comment injection must emit valid TOML")
        project = u.Cli.toml_table_child(document, "project")
        if project is None:
            pytest.fail("project table must remain addressable")
        optional = u.Cli.toml_table_child(project, "optional-dependencies")
        if optional is None:
            pytest.fail("optional-dependencies table must remain addressable")

        tm.that(u.Cli.toml_item_child(optional, "dev"), none=False)

    def test_inject_comments_adds_banner(self) -> None:
        """Add the canonical managed banner to unmarked content."""
        rendered = "[project]\nname = 'test'"
        result, changes = FlextInfraInjectCommentsPhase().apply(rendered)
        tm.that(result, has="[MANAGED] FLEXT pyproject standardization")
        tm.that(any("banner" in change for change in changes), eq=True)

    def test_inject_comments_injects_markers(self) -> None:
        """Inject the configured marker before a managed section."""
        rendered = "[project]\nname = 'test'\n[tool.pytest]"
        _, changes = FlextInfraInjectCommentsPhase().apply(rendered)
        tm.that(any("marker" in change for change in changes), eq=True)

    def test_inject_comments_removes_broken_group_section(self) -> None:
        """Remove the invalid Poetry dependency-group section."""
        rendered = "[group.dev.dependencies]\npytest = '^7.0'\n[project]\nname = 'test'"
        result, changes = FlextInfraInjectCommentsPhase().apply(rendered)
        tm.that("[group.dev.dependencies]" not in result, eq=True)
        tm.that(any("broken" in change for change in changes), eq=True)

    def test_inject_comments_handles_optional_dependencies_dev(self) -> None:
        """Preserve development optional dependencies while marking them."""
        rendered = "[project.optional-dependencies]\ndev = ['pytest']"
        result, changes = FlextInfraInjectCommentsPhase().apply(rendered)
        tm.that(("dev" in result) or (changes), eq=True)

    def test_inject_comments_preserves_existing_markers(self) -> None:
        """Preserve one canonical marker for an already managed section."""
        rendered = "# [MANAGED] build system\n[build-system]"
        result, _ = FlextInfraInjectCommentsPhase().apply(rendered)
        tm.that(result, has="# [MANAGED] build system")

    def test_inject_comments_phase_apply_banner(self) -> None:
        """Report the managed banner introduced by the phase."""
        rendered = '[project]\nname = "test"\n'
        result, changes = FlextInfraInjectCommentsPhase().apply(rendered)
        tm.that(result, has="[MANAGED] FLEXT pyproject standardization")
        tm.that(changes, has="managed banner injected")

    def test_inject_comments_phase_apply_markers(self) -> None:
        """Apply managed markers to supported tool sections."""
        rendered = '[project]\nname = "test"\n[tool.pytest]\n'
        result, _ = FlextInfraInjectCommentsPhase().apply(rendered)
        tm.that(result, has="[MANAGED]")

    def test_inject_comments_phase_apply_broken_group_section(self) -> None:
        """Report removal of an invalid dependency-group section."""
        """Report removal of an invalid dependency-group section."""
        rendered = '[group.dev.dependencies]\nrequests = "*"\n[project]\n'
        result, changes = FlextInfraInjectCommentsPhase().apply(rendered)
        tm.that("[group.dev.dependencies]" not in result, eq=True)
        tm.that(changes, has="broken [group.dev.dependencies] section removed")

    def test_inject_comments_phase_apply_with_optional_dependencies_dev(self) -> None:
        """Mark the development optional-dependency declaration."""
        rendered = "[project.optional-dependencies]\noptional-dependencies.dev = ['pytest', 'coverage']\n"
        result, changes = FlextInfraInjectCommentsPhase().apply(rendered)
        tm.that(("optional-dependencies.dev" in result) or (changes), eq=True)

    def test_inject_comments_phase_repositions_marker_before_section(self) -> None:
        """Reposition a managed marker immediately before its section."""
        rendered = '[tool.coverage.report]\nfail_under = 45\n# [MANAGED] pyrefly\n[tool.pyrefly]\npython-version = "3.13"'
        result, _changes = FlextInfraInjectCommentsPhase().apply(rendered)
        lines = result.splitlines()
        pyrefly_idx = lines.index("[tool.pyrefly]")
        tm.that(lines[pyrefly_idx - 1], eq="# [MANAGED] pyrefly")

    def test_inject_comments_phase_removes_auto_banner_and_auto_marker(self) -> None:
        """Replace legacy automatic annotations with canonical content."""
        rendered = "# [MANAGED] FLEXT pyproject standardization\n# Sections with [MANAGED] are enforced by flext_infra.deps.modernizer.\n# Sections with [AUTO] are derived from workspace layout and dependencies.\n# [AUTO] merged from dev/docs/security/test/typings\n[project.optional-dependencies]\ndev = ['pytest']"
        result, _changes = FlextInfraInjectCommentsPhase().apply(rendered)
        tm.that(
            result, has="# Run `make mod` to regenerate all managed pyproject sections."
        )
        tm.that("[AUTO]" in result, eq=False)

    def test_inject_comments_phase_marks_pytest_and_coverage_subtables(self) -> None:
        """Mark pytest and coverage subtables by their configured families."""
        rendered = '[tool.pytest.ini_options]\nminversion = "8.0"\n[tool.coverage.report]\nfail_under = 45'
        result, _changes = FlextInfraInjectCommentsPhase().apply(rendered)
        tm.that(result, has="# [MANAGED] pytest")
        tm.that(result, has="# [MANAGED] coverage")

    def test_inject_comments_phase_deduplicates_family_markers(self) -> None:
        """Emit one marker for multiple sections in the same family."""
        rendered = "[tool.coverage.run]\nbranch = true\n[tool.coverage.report]\nfail_under = 45"
        result, _changes = FlextInfraInjectCommentsPhase().apply(rendered)
        tm.that(result.count("# [MANAGED] coverage"), eq=1)

    def test_inject_comments_phase_is_idempotent_on_managed_content(self) -> None:
        """Keep managed content byte-stable on immediate reapplication."""
        rendered = (
            '[project]\nname = "test"\n[tool.pytest.ini_options]\nminversion = "8.0"\n'
        )
        first_result, first_changes = FlextInfraInjectCommentsPhase().apply(rendered)
        second_result, second_changes = FlextInfraInjectCommentsPhase().apply(
            first_result
        )
        tm.that(first_changes, len=(1, 20))
        tm.that(second_result, eq=first_result)
        tm.that(second_changes, empty=True)

    def test_inject_comments_discards_orphan_blank_after_banner(self) -> None:
        """Discard stripped banner trivia and preserve the immediate fixed point."""
        rendered = (
            f'{c.Infra.BANNER}\n\n[build-system]\nbuild-backend = "hatchling.build"\n'
        )

        first_result, _first_changes = FlextInfraInjectCommentsPhase().apply(rendered)
        second_result, second_changes = FlextInfraInjectCommentsPhase().apply(
            first_result
        )

        banner_length = len(c.Infra.BANNER.splitlines())
        tm.that(first_result.splitlines()[banner_length], eq="# [MANAGED] build system")
        tm.that(second_result, eq=first_result)
        tm.that(second_changes, empty=True)

    @pytest.mark.parametrize(
        "description",
        [
            "alpha\n# [MANAGED] ruff\nomega",
            "alpha\n\n\nomega",
            "alpha\n[tool.ruff]\nomega",
        ],
    )
    def test_inject_comments_treats_multiline_values_as_opaque(
        self, description: str
    ) -> None:
        """Preserve TOML-looking markers, headers, and blank lines inside values."""
        rendered = f'''[project]
name = "test"
description = """{description}"""
[tool.pytest.ini_options]
minversion = "8.0"
'''
        expected_mapping = u.Cli.toml_mapping_from_text(rendered)

        first_result, _first_changes = FlextInfraInjectCommentsPhase().apply(rendered)
        second_result, second_changes = FlextInfraInjectCommentsPhase().apply(
            first_result
        )

        tm.that(expected_mapping is not None, eq=True)
        tm.that(u.Cli.toml_mapping_from_text(first_result), eq=expected_mapping)
        tm.that(first_result, has=description)
        tm.that(second_result, eq=first_result)
        tm.that(second_changes, empty=True)

    def test_inject_comments_normalizes_leading_parse_trivia(self) -> None:
        """Keep the managed banner byte-identical after TOML parse/render."""
        # NOTE (multi-agent, mro-wkii.17.9.2.1): the banner owns exactly one
        # separator regardless of leading whitespace supplied by the parser.
        phase = FlextInfraInjectCommentsPhase()
        with_trivia, _changes = phase.apply('\n[project]\nname = "test"\n')
        without_trivia, _changes = phase.apply('[project]\nname = "test"\n')
        tm.that(with_trivia, eq=without_trivia)
