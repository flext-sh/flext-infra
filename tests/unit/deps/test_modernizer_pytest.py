"""Pytest phase tests for deps modernizer."""

from __future__ import annotations

from flext_infra import config
from flext_infra.deps.phases.ensure_pytest import FlextInfraEnsurePytestConfigPhase
from flext_tests import tm
from tests import t, u


class TestsFlextInfraDepsModernizerPytest:
    """Tests pytest settings phase behavior."""

    @staticmethod
    def _ini_options(doc: t.Cli.TomlDocument) -> t.JsonMapping:
        """Unwrap the canonical tool.pytest.ini_options table from one document."""
        return u.Tests.toml_mapping(
            u.Tests.toml_mapping(
                u.Tests.toml_mapping(u.Tests.toml_doc_mapping(doc)["tool"])["pytest"]
            )["ini_options"]
        )

    def test_tooling_policy_enforces_configured_case_timeout(self) -> None:
        policy = config.Infra.tooling.tools.pytest
        phase = FlextInfraEnsurePytestConfigPhase(config.Infra.tooling)
        doc = u.Cli.toml_document()

        _ = phase.apply(doc)

        ini = TestsFlextInfraDepsModernizerPytest._ini_options(doc)
        tm.that(
            set(u.Tests.strings(ini["addopts"])),
            has=[f"--timeout={policy.case_timeout_seconds}"],
        )

    def test_apply_sets_expected_ini_options(self) -> None:
        """Populate every canonical pytest option in an empty document."""
        tool_config = config.Infra.tooling
        doc = u.Cli.toml_document()

        _ = FlextInfraEnsurePytestConfigPhase(tool_config).apply(doc)

        ini = TestsFlextInfraDepsModernizerPytest._ini_options(doc)
        pytest_policy = tool_config.tools.pytest
        tm.that(ini["minversion"], eq=pytest_policy.min_version)
        tm.that(
            set(u.Tests.strings(ini["python_classes"])), eq=set(pytest_policy.python_classes)
        )
        tm.that(set(u.Tests.strings(ini["python_files"])), eq=set(pytest_policy.python_files))
        tm.that(
            set(u.Tests.strings(ini["addopts"])),
            eq={
                *tool_config.tools.pytest.standard_addopts,
                f"--timeout={tool_config.tools.pytest.case_timeout_seconds}",
            },
        )
        tm.that(
            set(u.Tests.strings(ini["markers"])),
            eq=set(tool_config.tools.pytest.standard_markers),
        )

    def test_apply_replaces_policy_and_merges_extension_entries(self) -> None:
        """Replace policy flags while retaining declared discovery extensions."""
        tool_config = config.Infra.tooling
        doc = u.Tests.toml_doc(
            """
[tool.pytest.ini_options]
minversion = "7.0"
flext_slow_timeout_seconds = "5"
python_classes = ["Spec*"]
python_files = ["spec_*.py"]
addopts = ["--maxfail=1"]
markers = ["custom: custom marker"]
"""
        )

        _ = FlextInfraEnsurePytestConfigPhase(tool_config).apply(doc)

        ini = TestsFlextInfraDepsModernizerPytest._ini_options(doc)
        pytest_policy = tool_config.tools.pytest
        tm.that(ini["minversion"], eq=pytest_policy.min_version)
        tm.that(
            ini["flext_slow_timeout_seconds"],
            eq=str(pytest_policy.slow_timeout_seconds),
        )
        tm.that(
            set(u.Tests.strings(ini["python_classes"])),
            eq={"Spec*", *pytest_policy.python_classes},
        )
        tm.that(
            set(u.Tests.strings(ini["python_files"])),
            eq={"spec_*.py", *pytest_policy.python_files},
        )
        tm.that(
            set(u.Tests.strings(ini["addopts"])),
            eq={
                *tool_config.tools.pytest.standard_addopts,
                f"--timeout={tool_config.tools.pytest.case_timeout_seconds}",
            },
        )
        tm.that(
            set(u.Tests.strings(ini["markers"])),
            eq={"custom: custom marker", *tool_config.tools.pytest.standard_markers},
        )

    def test_apply_is_idempotent(self) -> None:
        """Leave a document unchanged after the canonical policy is present."""
        tool_config = config.Infra.tooling
        phase = FlextInfraEnsurePytestConfigPhase(tool_config)
        doc = u.Cli.toml_document()

        _ = phase.apply(doc)
        second_changes = phase.apply(doc)

        tm.that(second_changes, empty=True)
