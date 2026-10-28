"""Real public module-naming waves over split packages and numbered fragments.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from pathlib import Path

import pytest

from flext_infra import codemod
from tests import c, tm, u


class TestsFlextInfraSemanticModuleNaming:
    """Derive split-module names from native evidence or fail closed."""

    @staticmethod
    @pytest.mark.parametrize("suffix", ["_parts", "_part"])
    def test_package_policy_precedes_modules_and_defers_descendants(
        tmp_path: Path, suffix: str
    ) -> None:
        """Only an owned shallowest package moves in a native naming wave."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.provision_checkout(root)
        u.Tests.provision_runtime_environment(root)
        family = next(iter(u.Infra.facade_families().values()))
        owner = package / family.directory
        owner.mkdir(exist_ok=True)
        (owner / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        (package / f"{family.module}.py").write_text(
            f"{family.letter} = 1\n__all__ = ['{family.letter}']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        outer = owner / f"_responsibility{suffix}"
        inner = outer / "_nested_parts"
        inner.mkdir(parents=True)
        for directory in (outer, inner):
            (directory / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        source = inner / "_behavior_part.py"
        source.write_text("VALUE = 1\n", encoding=c.DEFAULT_ENCODING)
        service = package / "services"
        service.mkdir(exist_ok=True)
        (service / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        seed = tm.ok(codemod.FlextInfraCodemodSemanticApply.build_source_plan(root))
        planned = tm.ok(
            codemod.FlextInfraCodemodSemanticApply.plan_module_names(root, seed)
        )
        destination = owner / "_responsibility" / inner.name / source.name
        tm.that(planned.candidate.updates[destination], eq=source.read_text())
        tm.ok(service / c.Infra.INIT_PY not in planned.candidate.updates)
        tm.ok(source.is_file())
        tm.ok(not destination.exists())

    @staticmethod
    @pytest.mark.parametrize("name", ["_parts", "_part", "_domain_part01", "_part_2"])
    def test_package_policy_reports_unresolved_semantic_grouping(
        tmp_path: Path, name: str
    ) -> None:
        """Bare and numbered fragments cannot invent a semantic responsibility."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.provision_checkout(root)
        u.Tests.provision_runtime_environment(root)
        directory = package / name
        directory.mkdir()
        source = directory / c.Infra.INIT_PY
        source.write_text("", encoding=c.DEFAULT_ENCODING)
        seed = tm.ok(codemod.FlextInfraCodemodSemanticApply.build_source_plan(root))
        with pytest.raises(ValueError, match="unresolved semantic grouping") as caught:
            codemod.FlextInfraCodemodSemanticApply.plan_module_names(root, seed)
        tm.ok(str(directory) in str(caught.value))
        tm.ok(source.is_file())

    @staticmethod
    @pytest.mark.parametrize("name", ["_behavior_part.py", "behavior_parts.py"])
    def test_module_policy_removes_unnumbered_split_suffix(
        tmp_path: Path, name: str
    ) -> None:
        """A meaningful remaining filename supplies the responsibility name."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.provision_checkout(root)
        u.Tests.provision_runtime_environment(root)
        source = package / name
        source.write_text("VALUE = 1\n", encoding=c.DEFAULT_ENCODING)
        seed = tm.ok(codemod.FlextInfraCodemodSemanticApply.build_source_plan(root))
        planned = tm.ok(
            codemod.FlextInfraCodemodSemanticApply.plan_module_names(root, seed)
        )
        tm.that(
            planned.candidate.updates[package / "behavior.py"], eq=source.read_text()
        )

    @staticmethod
    @pytest.mark.parametrize("name", ["_part01.py", "behavior_part_2.py", "_parts.py"])
    def test_module_policy_reports_unresolved_semantic_grouping(
        tmp_path: Path, name: str
    ) -> None:
        """Numbered or bare split filenames fail rather than publishing guesses."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.provision_checkout(root)
        u.Tests.provision_runtime_environment(root)
        source = package / name
        source.write_text("VALUE = 1\n", encoding=c.DEFAULT_ENCODING)
        seed = tm.ok(codemod.FlextInfraCodemodSemanticApply.build_source_plan(root))
        with pytest.raises(ValueError, match="unresolved semantic grouping") as caught:
            codemod.FlextInfraCodemodSemanticApply.plan_module_names(root, seed)
        tm.ok(str(source) in str(caught.value))
        tm.ok(source.is_file())

    @staticmethod
    @pytest.mark.parametrize(
        ("declaration", "replacement"),
        [
            ("Contract", "contract"),
            ("Fields", "fields"),
            ("Aggregates", "aggregates"),
            ("Document", "document"),
            ("PyprojectIngressContract", "pyproject_ingress_contract"),
        ],
    )
    def test_numbered_modules_derive_native_owner_relative_responsibility(
        tmp_path: Path, declaration: str, replacement: str
    ) -> None:
        """Native introducing identities select short names and rewrite callers."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.provision_checkout(root)
        u.Tests.provision_runtime_environment(root)
        owner = "ExampleModelsProjectMetadata"
        prefix = "ExampleModels" if declaration.startswith("Pyproject") else owner
        identity = prefix + declaration
        source = package / f"{owner.lower()}_part_01.py"
        original = f"class {identity}:\n    pass\n"
        source.write_text(original, encoding=c.DEFAULT_ENCODING)
        consumer = package / "consumer.py"
        imported = f"from {package.name}.{source.stem} import {identity}\n"
        consumer.write_text(imported, encoding=c.DEFAULT_ENCODING)
        seed = tm.ok(codemod.FlextInfraCodemodSemanticApply.build_source_plan(root))
        planned = tm.ok(
            codemod.FlextInfraCodemodSemanticApply.plan_module_names(root, seed)
        )
        tm.that(planned.candidate.updates[source], eq=None)
        tm.that(planned.candidate.updates[package / f"{replacement}.py"], eq=original)
        tm.that(
            planned.candidate.updates[consumer],
            eq=f"from {package.name}.{replacement} import {identity}\n",
        )
        tm.that(source.read_text(), eq=original)
        tm.that(consumer.read_text(), eq=imported)

    @staticmethod
    @pytest.mark.parametrize(
        "declarations",
        [
            "class ExampleContract:\n    pass\nclass ExampleFields:\n    pass\n",
            "class Example:\n    pass\n",
            "class UnrelatedContract:\n    pass\n",
        ],
    )
    def test_numbered_modules_reject_ambiguous_native_responsibility(
        tmp_path: Path, declarations: str
    ) -> None:
        """Multiple, owner-only and unrelated identities do not authorize a move."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.provision_checkout(root)
        u.Tests.provision_runtime_environment(root)
        source = package / "example_part_01.py"
        source.write_text(declarations, encoding=c.DEFAULT_ENCODING)
        seed = tm.ok(codemod.FlextInfraCodemodSemanticApply.build_source_plan(root))
        with pytest.raises(ValueError, match="unresolved semantic grouping"):
            codemod.FlextInfraCodemodSemanticApply.plan_module_names(root, seed)
        tm.that(source.read_text(), eq=declarations)

    @staticmethod
    @pytest.mark.parametrize(
        ("methods", "replacement"),
        [
            (("build_map", "normalize_map", "reset"), "map"),
            (("service_routes",), "service_routes"),
        ],
    )
    def test_split_class_modules_derive_responsibility_from_public_methods(
        tmp_path: Path, methods: tuple[str, ...], replacement: str
    ) -> None:
        """A mechanical split class is named by its own public methods."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.provision_checkout(root)
        u.Tests.provision_runtime_environment(root)
        source = package / "examplelazy_part_01.py"
        original = "class ExampleLazyPart01:\n" + "".join(
            f"    def {name}(self) -> None:\n        pass\n" for name in methods
        )
        source.write_text(original, encoding=c.DEFAULT_ENCODING)
        seed = tm.ok(codemod.FlextInfraCodemodSemanticApply.build_source_plan(root))
        planned = tm.ok(
            codemod.FlextInfraCodemodSemanticApply.plan_module_names(root, seed)
        )
        tm.that(planned.candidate.updates[source], eq=None)
        tm.that(planned.candidate.updates[package / f"{replacement}.py"], eq=original)
        tm.that(source.read_text(), eq=original)

    @staticmethod
    @pytest.mark.parametrize(
        "sources",
        [
            {"examplelazy_part_01.py": ("execute_app", "register_command", "exit")},
            {
                "examplelazy_part_01.py": ("build_map", "normalize_map"),
                "examplelazy_part_02.py": ("merge_map", "load_map"),
            },
        ],
    )
    def test_split_class_modules_reject_tied_or_colliding_method_evidence(
        tmp_path: Path, sources: dict[str, tuple[str, ...]]
    ) -> None:
        """Tied method words and sibling collisions do not authorize a move."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.provision_checkout(root)
        u.Tests.provision_runtime_environment(root)
        for index, (name, methods) in enumerate(sources.items(), start=1):
            (package / name).write_text(
                f"class ExampleLazyPart0{index}:\n"
                + "".join(
                    f"    def {method}(self) -> None:\n        pass\n"
                    for method in methods
                ),
                encoding=c.DEFAULT_ENCODING,
            )
        seed = tm.ok(codemod.FlextInfraCodemodSemanticApply.build_source_plan(root))
        with pytest.raises(ValueError, match="unresolved semantic grouping"):
            codemod.FlextInfraCodemodSemanticApply.plan_module_names(root, seed)
        tm.ok(all((package / name).is_file() for name in sources))
