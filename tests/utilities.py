"""Test utilities for flext-infra."""

from __future__ import annotations

from pathlib import Path

from flext_infra import u as flext_infra_u
from flext_tests import FlextTestsUtilities, tm
from tests import c, m, t
from tests.utilities_codegen import TestsFlextInfraUtilitiesCodegenMixin
from tests.utilities_deps import TestsFlextInfraUtilitiesDepsMixin
from tests.utilities_fixture_docs import TestsFlextInfraUtilitiesDocsFixtureMixin
from tests.utilities_fixture_project import TestsFlextInfraUtilitiesProjectFixtureMixin
from tests.utilities_fixture_tooling import TestsFlextInfraUtilitiesToolingFixtureMixin
from tests.utilities_fixture_workspace import (
    TestsFlextInfraUtilitiesWorkspaceFixtureMixin,
)
from tests.utilities_gates import TestsFlextInfraUtilitiesGatesMixin
from tests.utilities_git import TestsFlextInfraUtilitiesGitMixin
from tests.utilities_release import TestsFlextInfraUtilitiesReleaseMixin
from tests.utilities_replay import TestsFlextInfraUtilitiesReplayRunnerMixin
from tests.utilities_replay_sequence import TestsFlextInfraUtilitiesReplaySequenceMixin
from tests.utilities_toml import TestsFlextInfraUtilitiesTomlMixin
from tests.utilities_workspace_env import TestsFlextInfraUtilitiesWorkspaceEnvMixin


class TestsFlextInfraUtilities(FlextTestsUtilities, flext_infra_u):
    """Typed test utilities for flext-infra."""

    class Tests(
        TestsFlextInfraUtilitiesTomlMixin,
        TestsFlextInfraUtilitiesReplayRunnerMixin,
        TestsFlextInfraUtilitiesReplaySequenceMixin,
        TestsFlextInfraUtilitiesProjectFixtureMixin,
        TestsFlextInfraUtilitiesWorkspaceFixtureMixin,
        TestsFlextInfraUtilitiesToolingFixtureMixin,
        TestsFlextInfraUtilitiesDocsFixtureMixin,
        TestsFlextInfraUtilitiesReleaseMixin,
        TestsFlextInfraUtilitiesGitMixin,
        TestsFlextInfraUtilitiesGatesMixin,
        TestsFlextInfraUtilitiesCodegenMixin,
        TestsFlextInfraUtilitiesDepsMixin,
        TestsFlextInfraUtilitiesWorkspaceEnvMixin,
        FlextTestsUtilities.Tests,
    ):
        """Canonical test helper namespace."""

        @staticmethod
        def enforcement_rule(rule_id: str) -> m.EnforcementRuleSpec:
            """Resolve one enabled rule from the canonical enforcement catalog."""
            catalog = u.build_canonical_catalog()
            rule: m.EnforcementRuleSpec = next(
                rule for rule in catalog.enabled_rules() if rule.id == rule_id
            )
            return rule

        @staticmethod
        def number(value: t.JsonValue) -> float:
            """Narrow one parsed payload value to a real number."""
            tm.that(isinstance(value, (int, float)), eq=True)
            if not isinstance(value, (int, float)):
                msg = "payload value is not a number"
                raise TypeError(msg)
            return float(value)

        @staticmethod
        def mapping(value: t.JsonPayload | None) -> t.JsonMapping:
            """Provide the pre-rename alias call sites still resolve to.

            Why: `toml_mapping` (`tests/utilities_toml.py`) is the canonical
            narrowing owner; this keeps the older `mapping` name working for
            call sites this merge did not also rename.
            """
            return TestsFlextInfraUtilitiesTomlMixin.toml_mapping(value)

        @staticmethod
        def json_payload(content: str) -> t.JsonMapping:
            """Parse JSON text through the canonical reader and narrow it."""
            return TestsFlextInfraUtilitiesTomlMixin.toml_mapping(
                tm.ok(u.Cli.json_loads(content))
            )

        @staticmethod
        def toml_payload(content: str) -> t.JsonMapping:
            """Parse TOML text through the canonical reader, never `tomllib`.

            The facade returns an absent mapping for unparseable text; a test
            that asked for a payload has already decided the text is one, so
            the absence is a defect rather than a value to carry forward.
            """
            parsed = u.Cli.toml_mapping_from_text(content)
            if parsed is None:
                msg = "TOML payload is not parseable"
                raise ValueError(msg)
            return parsed

        @staticmethod
        def write_canonical_package_layout(package_dir: Path) -> None:
            """Materialize the complete facade layout a governed package declares.

            The namespace validator grades a project, not a file: every missing
            facade, private-family base and composition tree is a violation of
            its own. A fixture that writes one module and expects a clean report
            is asserting that the layout law does not exist.
            """
            stem = u.derive_class_stem(package_dir.name)
            namespace = stem.removeprefix("Flext")
            families = (
                ("c", "constants", "_constants", "Constants"),
                ("t", "typings", "_typings", "Types"),
                ("p", "protocols", "_protocols", "Protocols"),
                ("m", "models", "_models", "Models"),
                ("u", "utilities", "_utilities", "Utilities"),
            )
            for alias, public_name, private_dir, suffix in families:
                private_root = package_dir / private_dir
                private_root.mkdir(parents=True, exist_ok=True)
                (private_root / c.Infra.INIT_PY).write_text("", encoding="utf-8")
                for module_name, class_suffix in (
                    ("base", "Base"),
                    ("domain", "Domain"),
                ):
                    (private_root / f"{module_name}.py").write_text(
                        "from __future__ import annotations\n\n\n"
                        f"class {stem}{suffix}{class_suffix}:\n    pass\n",
                        encoding="utf-8",
                    )
                (package_dir / f"{public_name}.py").write_text(
                    "from __future__ import annotations\n\n"
                    f"from flext_core import {alias}\n\n"
                    f"from {package_dir.name}.{private_dir}.base import "
                    f"{stem}{suffix}Base\n"
                    f"from {package_dir.name}.{private_dir}.domain import "
                    f"{stem}{suffix}Domain\n\n\n"
                    f"class {stem}{suffix}({alias}):\n"
                    f"    class {namespace}({stem}{suffix}Base, {stem}{suffix}Domain):\n"
                    "        pass\n",
                    encoding="utf-8",
                )
            for simple_name, class_suffix in (
                ("settings", "Settings"),
                ("config", "Config"),
                ("base", "Base"),
                ("api", "Api"),
                ("cli", "Cli"),
            ):
                (package_dir / f"{simple_name}.py").write_text(
                    "from __future__ import annotations\n\n\n"
                    f"class {stem}{class_suffix}:\n    pass\n",
                    encoding="utf-8",
                )
            services = package_dir / "services"
            services.mkdir(parents=True, exist_ok=True)
            (services / c.Infra.INIT_PY).write_text("", encoding="utf-8")

        @staticmethod
        def write_package_init(directory: Path, content: str) -> Path:
            """Materialize one importable package initializer under a test root."""
            directory.mkdir(parents=True, exist_ok=True)
            init_file = directory / c.Infra.INIT_PY
            init_file.write_text(content, encoding=c.Infra.ENCODING_DEFAULT)
            return init_file


u = TestsFlextInfraUtilities

__all__: list[str] = ["TestsFlextInfraUtilities", "u"]
