"""Generated import-boundary rules reach the import-law verdict natively.

Every scanned source is scenario data under ``tests/fixtures/import-boundary``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from tests import c, p, tm, u


class TestsFlextInfraCodemodGeneratedBoundaryRules:
    """Layer-zero, facade and typings boundaries fail only where the law says."""

    SCENARIO = "import-boundary"
    FACADE = "ban-settings-config-own-facade-import"
    MODULE = "ban-settings-config-own-module-import"
    EXTERNAL = "ban-external-import-outside-facade-family"
    LIBRARY = "ban-library-type-reference-outside-typings"

    @staticmethod
    @pytest.mark.parametrize("selector_length", [1023, 1024, 1025, 4096])
    def test_generated_scope_manifest_preserves_long_selector_keys(
        tmp_path: Path, selector_length: int
    ) -> None:
        """JSON scope keys survive both sides of YAML's implicit-key limit."""
        selector = "s" * selector_length
        paths = ("src/consumer.py",)
        u.Infra.codemod_write_native_documents(
            tmp_path / c.Infra.CODEMOD_SCOPES_FILENAME,
            ({selector: list(paths)},),
        )
        scopes = u.Infra.codemod_stage_scopes(
            tmp_path / c.Infra.CODEMOD_CONFIG_FILENAME
        )
        tm.that(tuple(scopes), eq=(selector,))
        tm.that(scopes[selector], eq=paths)

    @staticmethod
    def scenario_source(
        fixture_tree: p.Tests.FixtureTree, tmp_path: Path, case: str
    ) -> str:
        """Return one scenario source, materialized beside the scanned project.

        Returns:
            The source text of ``<case>.py`` in the import-boundary scenario.

        """
        scenarios = fixture_tree(
            TestsFlextInfraCodemodGeneratedBoundaryRules.SCENARIO,
            destination=tmp_path / "scenarios",
        )
        return (scenarios / f"{case}.py").read_text(encoding=c.DEFAULT_ENCODING)

    @staticmethod
    def scan_sources(tmp_path: Path, sources: Mapping[str, str]) -> Sequence[str]:
        """Write ``sources`` into a real project and scan every generated rule.

        Returns:
            ``<file>:<rule shape>`` for every finding, sorted.

        """
        repository, package = u.Tests.create_lazy_init_workspace(tmp_path)
        for name, source in sources.items():
            target = package / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source, encoding=c.DEFAULT_ENCODING)
        catalog = tmp_path / "catalog"
        (catalog / "rules").mkdir(parents=True)
        (catalog / "utils").mkdir(parents=True)
        with u.Infra.codemod_workspace_snapshot(repository) as snapshot:
            utilities = {
                **u.Infra.codemod_own_package_utilities(snapshot, repository),
                **u.Infra.codemod_stdlib_module_utilities(snapshot, repository),
                **u.Infra.codemod_facade_package_utilities(snapshot, repository),
            }
            documents = {
                **u.Infra.codemod_layer_zero_rules(snapshot, repository),
                **u.Infra.codemod_external_import_rules(snapshot, repository),
                **u.Infra.codemod_library_type_rules(snapshot, repository),
            }
        for util_id, rule in utilities.items():
            tm.ok(
                u.Cli.yaml_dump(
                    catalog / "utils" / f"{util_id}.yml",
                    u.Infra.codemod_native_utility_document(util_id, rule),
                )
            )
        for rule_id, document in documents.items():
            tm.ok(u.Cli.yaml_dump(catalog / "rules" / f"{rule_id}.yml", document))
        tm.ok(
            u.Cli.yaml_dump(
                catalog / "sgconfig.yml",
                {"ruleDirs": ["rules"], "utilDirs": ["utils"]},
            )
        )
        output = u.Cli.capture([
            c.Infra.SG,
            "scan",
            "-c",
            str(catalog / "sgconfig.yml"),
            "--info",
            "--json=compact",
            str(repository),
        ]).unwrap()
        return sorted(
            f"{Path(finding['file']).name}:{finding['ruleId'].partition('--')[0]}"
            for finding in json.loads(output)
        )

    @staticmethod
    @pytest.mark.parametrize(
        ("case", "shape"),
        [
            ("layer-zero/facade_settings", FACADE),
            ("layer-zero/facade_guarded_typings", FACADE),
            ("layer-zero/facade_config", FACADE),
            ("layer-zero/facade_letters", FACADE),
            ("layer-zero/module_settings", MODULE),
            ("layer-zero/module_models_config", MODULE),
            ("layer-zero/module_package", MODULE),
            ("layer-zero/module_settings_alias", MODULE),
            ("layer-zero/module_guarded_models", MODULE),
        ],
    )
    def test_own_namespace_import_fails_only_in_layer_zero(
        fixture_tree: p.Tests.FixtureTree, tmp_path: Path, case: str, shape: str
    ) -> None:
        """The layer-zero module fails; a consumer with the same import does not."""
        owner = TestsFlextInfraCodemodGeneratedBoundaryRules
        source = owner.scenario_source(fixture_tree, tmp_path, case)
        findings = owner.scan_sources(
            tmp_path, {"_settings.py": source, "consumer.py": source}
        )
        tm.that(findings, has=f"_settings.py:{shape}")
        tm.that([item for item in findings if item.startswith("consumer.py")], eq=[])

    @staticmethod
    @pytest.mark.parametrize(
        "case",
        [
            "library-import/griffe_import",
            "library-import/griffe_from",
            "library-import/rope_import",
        ],
    )
    def test_library_import_fails_outside_the_facade_families(
        fixture_tree: p.Tests.FixtureTree, tmp_path: Path, case: str
    ) -> None:
        """A consumer library import fails; the same import in a family passes."""
        owner = TestsFlextInfraCodemodGeneratedBoundaryRules
        source = owner.scenario_source(fixture_tree, tmp_path, case)
        findings = owner.scan_sources(
            tmp_path,
            {"consumer.py": source, "_utilities/library_owner.py": source},
        )
        tm.that(findings, eq=[f"consumer.py:{owner.EXTERNAL}"])

    @staticmethod
    @pytest.mark.parametrize(
        "case",
        [
            "allowed-import/pathlib_stdlib",
            "allowed-import/typing_extensions_backport",
            "allowed-import/own_facade",
            "allowed-import/flext_core_facade",
            "allowed-import/guarded_library",
        ],
    )
    def test_stdlib_own_facade_and_guarded_imports_stay_allowed(
        fixture_tree: p.Tests.FixtureTree, tmp_path: Path, case: str
    ) -> None:
        """Stdlib (with backports), own, facade and typing-only imports pass."""
        owner = TestsFlextInfraCodemodGeneratedBoundaryRules
        source = owner.scenario_source(fixture_tree, tmp_path, case)
        tm.that(owner.scan_sources(tmp_path, {"consumer.py": source}), eq=[])

    @staticmethod
    @pytest.mark.parametrize(
        "case",
        [
            "library-type-inline/annotation",
            "library-type-inline/isinstance_single",
            "library-type-inline/isinstance_union",
        ],
    )
    def test_library_type_named_inline_fails_outside_typings(
        fixture_tree: p.Tests.FixtureTree, tmp_path: Path, case: str
    ) -> None:
        """An inline library type fails in a utility and passes in typings."""
        owner = TestsFlextInfraCodemodGeneratedBoundaryRules
        source = owner.scenario_source(fixture_tree, tmp_path, case)
        findings = owner.scan_sources(
            tmp_path,
            {"_utilities/model_owner.py": source, "_typings/library_types.py": source},
        )
        tm.that(findings, eq=[f"model_owner.py:{owner.LIBRARY}"])

    @staticmethod
    def test_protocols_family_names_library_protocols_only(
        fixture_tree: p.Tests.FixtureTree, tmp_path: Path
    ) -> None:
        """The protocols family re-exposes a library protocol, never another type."""
        owner = TestsFlextInfraCodemodGeneratedBoundaryRules
        source = owner.scenario_source(
            fixture_tree, tmp_path, "protocols/library_protocols"
        )
        findings = owner.scan_sources(
            tmp_path, {"_protocols/library_protocols.py": source}
        )
        tm.that(findings, eq=[f"library_protocols.py:{owner.LIBRARY}"])

    @staticmethod
    def test_library_call_in_its_owning_utility_stays_allowed(
        fixture_tree: p.Tests.FixtureTree, tmp_path: Path
    ) -> None:
        """Calling the library's functions in its owning utility is not a type use."""
        owner = TestsFlextInfraCodemodGeneratedBoundaryRules
        source = owner.scenario_source(
            fixture_tree, tmp_path, "library-call/model_owner"
        )
        tm.that(
            owner.scan_sources(tmp_path, {"_utilities/model_owner.py": source}), eq=[]
        )
