"""Comment injection phase tests for deps modernizer."""

from __future__ import annotations

from flext_tests import tm

from flext_infra.deps.phases.inject_comments import FlextInfraInjectCommentsPhase


class TestsFlextInfraDepsModernizerComments:
    """Tests comment injection behavior."""

    def test_inject_comments_adds_banner(self) -> None:
        """Inject the canonical managed banner."""
        rendered = "[project]\nname = 'test'"
        result, changes = FlextInfraInjectCommentsPhase().apply(rendered)
        tm.that(result, has="[MANAGED] FLEXT pyproject standardization")
        tm.that(any("banner" in change for change in changes), eq=True)

    def test_inject_comments_injects_markers(self) -> None:
        """Report managed section marker injection."""
        rendered = "[project]\nname = 'test'\n[tool.pytest]"
        _, changes = FlextInfraInjectCommentsPhase().apply(rendered)
        tm.that(any("marker" in change for change in changes), eq=True)

    def test_inject_comments_removes_broken_group_section(self) -> None:
        """Remove unsupported dependency-group sections."""
        rendered = "[group.dev.dependencies]\npytest = '^7.0'"
        result, changes = FlextInfraInjectCommentsPhase().apply(rendered)
        tm.that("[group.dev.dependencies]" not in result, eq=True)
        tm.that(any("broken" in change for change in changes), eq=True)

    def test_inject_comments_handles_optional_dependencies_dev(self) -> None:
        """Preserve or canonically annotate development dependencies."""
        rendered = "[project.optional-dependencies]\ndev = ['pytest']"
        result, changes = FlextInfraInjectCommentsPhase().apply(rendered)
        tm.that(("dev" in result) or (changes), eq=True)

    def test_inject_comments_preserves_existing_markers(self) -> None:
        """Preserve an already canonical section marker."""
        rendered = "# [MANAGED] build system\n[build-system]"
        result, _ = FlextInfraInjectCommentsPhase().apply(rendered)
        tm.that(result, has="# [MANAGED] build system")

    def test_inject_comments_phase_apply_banner(self) -> None:
        """Return a change record when injecting the banner."""
        rendered = '[project]\nname = "test"\n'
        result, changes = FlextInfraInjectCommentsPhase().apply(rendered)
        tm.that(result, has="[MANAGED] FLEXT pyproject standardization")
        tm.that(changes, has="managed banner injected")

    def test_inject_comments_phase_apply_markers(self) -> None:
        """Annotate governed tool sections with managed markers."""
        rendered = '[project]\nname = "test"\n[tool.pytest]\n'
        result, _ = FlextInfraInjectCommentsPhase().apply(rendered)
        tm.that(result, has="[MANAGED]")

    def test_inject_comments_phase_apply_broken_group_section(self) -> None:
        """Report removal of an invalid dependency-group section."""
        rendered = '[group.dev.dependencies]\nrequests = "*"\n[project]\n'
        result, changes = FlextInfraInjectCommentsPhase().apply(rendered)
        tm.that("[group.dev.dependencies]" not in result, eq=True)
        tm.that(changes, has="broken [group.dev.dependencies] section removed")

    def test_inject_comments_phase_apply_with_optional_dependencies_dev(self) -> None:
        """Handle dotted development dependency declarations."""
        rendered = "[project.optional-dependencies]\noptional-dependencies.dev = ['pytest', 'coverage']\n"
        result, changes = FlextInfraInjectCommentsPhase().apply(rendered)
        tm.that(("optional-dependencies.dev" in result) or (changes), eq=True)

    def test_inject_comments_phase_repositions_marker_before_section(self) -> None:
        """Position a managed marker immediately before its section."""
        rendered = '[tool.coverage.report]\nfail_under = 45\n# [MANAGED] pyrefly\n[tool.pyrefly]\npython-version = "3.13"'
        result, _changes = FlextInfraInjectCommentsPhase().apply(rendered)
        lines = result.splitlines()
        pyrefly_idx = lines.index("[tool.pyrefly]")
        tm.that(lines[pyrefly_idx - 1], eq="# [MANAGED] pyrefly")

    def test_inject_comments_phase_removes_auto_banner_and_auto_marker(self) -> None:
        """Replace superseded automatic banner and marker variants."""
        rendered = "# [MANAGED] FLEXT pyproject standardization\n# Sections with [MANAGED] are enforced by flext_infra.deps.modernizer.\n# Sections with [AUTO] are derived from workspace layout and dependencies.\n# [AUTO] merged from dev/docs/security/test/typings\n[project.optional-dependencies]\ndev = ['pytest']"
        result, _changes = FlextInfraInjectCommentsPhase().apply(rendered)
        tm.that(
            result, has="# Run `make mod` to regenerate all managed pyproject sections."
        )
        tm.that("[AUTO]" in result, eq=False)

    def test_inject_comments_phase_marks_pytest_and_coverage_subtables(self) -> None:
        """Annotate governed pytest and coverage subtables."""
        rendered = '[tool.pytest.ini_options]\nminversion = "8.0"\n[tool.coverage.report]\nfail_under = 45'
        result, _changes = FlextInfraInjectCommentsPhase().apply(rendered)
        tm.that(result, has="# [MANAGED] pytest")
        tm.that(result, has="# [MANAGED] coverage")

    def test_inject_comments_phase_deduplicates_family_markers(self) -> None:
        """Emit one marker for multiple tables in the same tool family."""
        rendered = "[tool.coverage.run]\nbranch = true\n[tool.coverage.report]\nfail_under = 45"
        result, _changes = FlextInfraInjectCommentsPhase().apply(rendered)
        tm.that(result.count("# [MANAGED] coverage"), eq=1)

    def test_inject_comments_phase_is_idempotent_on_managed_content(self) -> None:
        """Produce byte-identical output and no changes on a second pass."""
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

    def test_inject_comments_normalizes_leading_parse_trivia(self) -> None:
        """Keep the managed banner byte-identical after TOML parse/render."""
        # NOTE (multi-agent, mro-wkii.17.9.2.1): the banner owns exactly one
        # separator regardless of leading whitespace supplied by the parser.
        phase = FlextInfraInjectCommentsPhase()
        with_trivia, _changes = phase.apply('\n[project]\nname = "test"\n')
        without_trivia, _changes = phase.apply('[project]\nname = "test"\n')
        tm.that(with_trivia, eq=without_trivia)
