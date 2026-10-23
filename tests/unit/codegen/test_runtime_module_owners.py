"""Public contracts for project-scoped runtime module ownership.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from itertools import permutations
from pathlib import Path

import pytest

from flext_infra import config, infra
from tests import c, t, tm, u
from tests.unit.codegen.test_codegen_ci_matrix import TestsFlextInfraCodegenCiMatrix


class TestsFlextInfraRuntimeModuleOwners:
    """Resolve declarations through the same strict layers as generation."""

    @staticmethod
    @pytest.mark.parametrize(
        "roles",
        [
            {"unknown": "configuration"},
            {"config": "config"},
            {"settings": "settings"},
            {"config": "settings"},
            {"settings": "config"},
            {"config": "m"},
            {"config": "_configuration"},
            {"config": "class"},
            {"config": "not-a-module"},
            {"config": "nested.module"},
            {"config": ""},
            {"config": "shared", "settings": "shared"},
        ],
    )
    def test_invalid_declarations_fail_before_planning(
        tmp_path: Path, roles: t.JsonDict
    ) -> None:
        """Invalid roles, aliases and physical stems never reach rendering."""
        directory = tmp_path / "config"
        directory.mkdir()
        tm.ok(
            u.Cli.yaml_dump(
                directory / "codegen.yaml",
                {
                    "Infra": {
                        "codegen": {"runtime_module_overrides": {"ai-hub": roles}}
                    },
                },
            )
        )
        result = u.Infra.load_codegen_inputs(tmp_path)
        tm.ok(result.failure)
        tm.ok(result.exception is not None)
        tm.fail((tmp_path / "src").exists())

    @staticmethod
    def test_project_override_does_not_change_other_fleet_owners(
        tmp_path: Path,
    ) -> None:
        """One composed declaration changes only its canonical distribution."""
        directory = tmp_path / "config"
        directory.mkdir()
        tm.ok(
            u.Cli.yaml_dump(
                directory / "codegen.yaml",
                {
                    "Infra": {
                        "codegen": {
                            "runtime_module_overrides": {
                                "ai-hub": {
                                    "config": "configuration",
                                    "settings": "runtime_settings",
                                },
                            }
                        }
                    },
                },
            )
        )
        declared = tm.ok(u.Infra.load_codegen_inputs(tmp_path)).spec
        expected = declared.runtime_module_overrides["ai-hub"]
        for project_name in ("ai-hub", "flext-core", "flext-infra", "flext-demo"):
            names = u.Infra.runtime_module_names(
                project_name=project_name, codegen=declared
            )
            defaults = {
                Path(filename).stem.removeprefix("_"): Path(filename).stem
                for filename, *_ in c.Infra.RUNTIME_MODULES
            }
            tm.that(names, eq=expected if project_name == "ai-hub" else defaults)
            for role, stem in names.items():
                tm.that(
                    u.Infra.runtime_singleton_export(
                        f"{stem}.py", project_name=project_name, codegen=declared
                    ),
                    eq=role,
                )
            if project_name == "ai-hub":
                for stem in defaults.values():
                    tm.that(
                        u.Infra.runtime_singleton_export(
                            f"{stem}.py", project_name=project_name, codegen=declared
                        ),
                        eq=None,
                    )

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("override", [False, True])
    def test_generated_owners_keep_lazy_singletons_for_every_import_order(
        tmp_path: Path, *, override: bool
    ) -> None:
        """Real scaffold output keeps one destination and singleton identity."""
        root = tmp_path / "consumer"
        if override:
            directory = root / "config"
            directory.mkdir(parents=True)
            tm.ok(
                u.Cli.yaml_dump(
                    directory / "codegen.yaml",
                    {
                        "Infra": {
                            "codegen": {
                                "runtime_module_overrides": {
                                    "flext-demo": {
                                        "config": "configuration",
                                        "settings": "runtime_settings",
                                    },
                                }
                            }
                        },
                    },
                )
            )
        TestsFlextInfraCodegenCiMatrix.render_project(root)
        declared = tm.ok(u.Infra.load_codegen_inputs(root)).spec
        names = u.Infra.runtime_module_names(
            project_name="flext-demo", codegen=declared
        )
        package = root / "src" / "flext_demo"
        for role, stem in names.items():
            tm.ok((package / f"{stem}.py").is_file())
            if override:
                legacy = u.Infra.runtime_module_names(
                    project_name="flext-demo", codegen=config.Infra.codegen
                )[role]
                tm.fail((package / f"{legacy}.py").exists())
        request = u.Tests.conform_request(
            root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        before = tuple(sorted(path.name for path in package.glob("*.py")))
        for _ in range(2):
            result = tm.ok(infra.codegen_conform(request))
            tm.that(result.written_files, eq=())
            tm.that(
                tuple(sorted(path.name for path in package.glob("*.py"))), eq=before
            )
        script = """
import importlib
import sys
from pydantic import ValidationError
from flext_tests import tm

sys.path.insert(0, sys.argv[1])
package = importlib.import_module("flext_demo")
modules = ["flext_demo." + stem for stem in sys.argv[2:4]]
assert all(name not in sys.modules for name in modules)
for action in sys.argv[4:]:
    if action == "classes":
        from flext_demo import FlextDemoConfig
        assert FlextDemoConfig.__module__ == modules[0]
    elif action == "submodules":
        for name in modules:
            importlib.import_module(name)
    else:
        from flext_demo import config, settings
from flext_demo import FlextDemoConfig, config, settings
assert package.config is config is importlib.import_module(modules[0]).config
assert package.settings is settings is importlib.import_module(modules[1]).settings
assert FlextDemoConfig.fetch_global() is config
assert type(settings).fetch_global() is settings
original_config = config.model_dump()
original_settings = settings.model_dump()
for singleton in (config, settings):
    type(singleton).reset_for_testing()
    assert type(singleton).fetch_global() is singleton
assert package.config is config
assert package.settings is settings
assert config.model_dump() == original_config
assert settings.model_dump() == original_settings
adjusted = settings.clone(Demo={"enabled": not settings.Demo.enabled})
assert adjusted.Demo.enabled != settings.Demo.enabled
assert config.model_dump() == original_config
for namespace in (config.Demo, settings.Demo):
    try:
        type(namespace).model_validate(
            {**namespace.model_dump(), "__unexpected__": True}
        )
    except ValidationError as error:
        assert all(item["type"] == "extra_forbidden" for item in error.errors())
    else:
        tm.reject("Generated namespace accepts undeclared fields")
for singleton in (config, settings):
    try:
        singleton.Demo = singleton.Demo
    except ValidationError as error:
        assert all(item["type"] == "frozen_instance" for item in error.errors())
    else:
        tm.reject("Generated runtime singleton is mutable")
"""
        for order in permutations(("classes", "submodules", "aliases")):
            process = tm.ok(
                u.Cli.run_raw(
                    [
                        sys.executable,
                        "-c",
                        script,
                        str(root / "src"),
                        names["config"],
                        names["settings"],
                        *order,
                    ],
                    cwd=root,
                )
            )
            tm.that(
                u.Cli.process_succeeded(process.outcome),
                eq=True,
                msg=process.stdout + process.stderr,
            )
