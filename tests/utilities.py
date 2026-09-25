"""Test utilities for flext-infra."""

from __future__ import annotations

from pathlib import Path

from flext_tests import FlextTestsUtilities, tm

from flext_core import r
from flext_infra import FlextInfraUtilities
from tests import c, m, p, t
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
from tests.utilities_namespace import TestsFlextInfraUtilitiesNamespaceMixin
from tests.utilities_promoted import TestsFlextInfraUtilitiesPromotedMixin
from tests.utilities_release import TestsFlextInfraUtilitiesReleaseMixin
from tests.utilities_replay import TestsFlextInfraUtilitiesReplayRunnerMixin
from tests.utilities_replay_sequence import TestsFlextInfraUtilitiesReplaySequenceMixin
from tests.utilities_toml import TestsFlextInfraUtilitiesTomlMixin
from tests.utilities_workspace_env import TestsFlextInfraUtilitiesWorkspaceEnvMixin


class TestsFlextInfraUtilities(FlextTestsUtilities, FlextInfraUtilities):
    """Typed test utilities for flext-infra."""

    class Tests(
        TestsFlextInfraUtilitiesTomlMixin,
        TestsFlextInfraUtilitiesReplayRunnerMixin,
        TestsFlextInfraUtilitiesReplaySequenceMixin,
        TestsFlextInfraUtilitiesProjectFixtureMixin,
        TestsFlextInfraUtilitiesWorkspaceFixtureMixin,
        TestsFlextInfraUtilitiesToolingFixtureMixin,
        TestsFlextInfraUtilitiesDocsFixtureMixin,
        TestsFlextInfraUtilitiesPromotedMixin,
        TestsFlextInfraUtilitiesReleaseMixin,
        TestsFlextInfraUtilitiesGitMixin,
        TestsFlextInfraUtilitiesNamespaceMixin,
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
        def json_payload(content: str) -> t.JsonMapping:
            """Parse JSON text through the canonical reader and narrow it."""
            return TestsFlextInfraUtilitiesTomlMixin.toml_mapping(
                tm.ok(u.Cli.json_loads(content))
            )

        @staticmethod
        def toml_payload(content: str) -> t.JsonMapping:
            """Parse TOML text through the canonical reader, never ``tomllib``.

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
        def materialize_docs_bundle(
            bundle: m.Infra.DocsGenerationBundle,
        ) -> p.Result[bool]:
            """Publish one immutable docs bundle through atomic file primitives."""
            required = u.Infra.docs_required_directories(bundle)
            if required.failure:
                return r[bool].from_failure(required)
            for directory in required.value:
                directory_plan = u.Cli.atomic_plan_directory_chain(directory)
                if directory_plan.failure:
                    return r[bool].from_failure(directory_plan)
                if directory_plan.value.directories:
                    created = u.Cli.atomic_create_directory_chain_guarded(
                        directory_plan.value, permission_mode=0o755
                    )
                    if created.failure:
                        return r[bool].from_failure(created)
            return TestsFlextInfraUtilities.Tests.materialize_codegen_plans(
                u.Infra.docs_file_plans(bundle)
            )

        @staticmethod
        def namespace_fixture(name: str) -> str:
            """Read a non-importable source fixture for namespace validation."""
            fixture = (
                Path(name).with_suffix(".pysrc") if name.endswith(".py") else Path(name)
            )
            return (
                Path(__file__).parent / "fixtures" / "namespace_validator" / fixture
            ).read_text(encoding="utf-8")

        @staticmethod
        def namespace_project(
            tmp_path: Path, *, module_source: str, module_name: str
        ) -> Path:
            """Create a tracked canonical project with one overridden module."""
            root, _ = TestsFlextInfraUtilities.Tests.namespace_project_path(
                tmp_path, module_source=module_source, module_path=module_name
            )
            return root

        @staticmethod
        def namespace_project_path(
            tmp_path: Path, *, module_source: str, module_path: str
        ) -> t.Pair[Path, Path]:
            """Create canonical facades and track the source or test module."""
            project_root = tmp_path / "project"
            package_dir = project_root / "src" / "flext_test"
            package_dir.mkdir(parents=True)
            _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")
            TestsFlextInfraUtilities.Tests.write_canonical_package_layout(package_dir)
            relative = Path(module_path)
            target = (
                project_root if relative.parts[0] == c.Infra.DIR_TESTS else package_dir
            ) / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if relative.parts[0] == c.Infra.DIR_TESTS:
                tests_initializer = project_root / c.Infra.DIR_TESTS / c.Infra.INIT_PY
                if not tests_initializer.exists():
                    _ = tests_initializer.write_text("", encoding="utf-8")
            _ = target.write_text(module_source, encoding="utf-8")
            TestsFlextInfraUtilities.Tests.initialize_git_repo(project_root)
            return project_root, target

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
                # The facade class extends its own private bases and rebinds
                # the letter locally — never the parent letter itself, whose
                # import shadows the local alias binding and breaks the
                # owner election.
                (package_dir / f"{public_name}.py").write_text(
                    "from __future__ import annotations\n\n"
                    f"from {package_dir.name}.{private_dir}.base import "
                    f"{stem}{suffix}Base\n"
                    f"from {package_dir.name}.{private_dir}.domain import "
                    f"{stem}{suffix}Domain\n\n\n"
                    f"class {stem}{suffix}({stem}{suffix}Base, {stem}{suffix}Domain):\n"
                    f"    class {namespace}({stem}{suffix}Base, {stem}{suffix}Domain):\n"
                    "        pass\n\n\n"
                    f"{alias} = {stem}{suffix}\n\n"
                    f'__all__: list[str] = ["{stem}{suffix}", "{alias}"]\n',
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
