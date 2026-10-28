"""Public lazy-init behavior for nested private ``_<facade>/`` directories.

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

from tests import c, tm, u


class TestsFlextInfraCodegenLazyInitPrivateFacade:
    """Private facade directories publish into their importing package."""

    @staticmethod
    def test_nested_private_facade_directory_publishes_into_its_parent(
        tmp_path: Path,
    ) -> None:
        """A ``_<facade>/`` owner is re-exported by its importing package.

        Consumers declare ``from <pkg>.services import Owner`` for an owner
        declared under ``services/_acl/``. The services initializer must carry
        that re-export so planned base resolution follows it to the declaring
        module instead of failing as an unresolved planned base.
        """
        repository_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        services_root = package_root / "services"
        facade_dir = services_root / "_acl"
        facade_dir.mkdir(parents=True)
        services_root.joinpath(c.Infra.INIT_PY).write_text(
            "",
            encoding=c.DEFAULT_ENCODING,
        )
        facade_dir.joinpath(c.Infra.INIT_PY).write_text(
            "",
            encoding=c.DEFAULT_ENCODING,
        )
        facade_dir.joinpath("convert.py").write_text(
            'class FlextTestsAclConvertService:\n    """ACL conversion owner."""\n\n'
            '__all__ = ["FlextTestsAclConvertService"]\n',
            encoding=c.DEFAULT_ENCODING,
        )
        service = u.Tests.create_lazy_init_service(repository_root)
        service.apply_changes = True

        result = u.Tests.materialize_lazy_init(service)
        generated_services = services_root.joinpath(c.Infra.INIT_PY).read_text(
            encoding=c.DEFAULT_ENCODING,
        )

        tm.ok(result.success)
        tm.that(generated_services, contains='"FlextTestsAclConvertService"')
        tm.that(generated_services, contains="._acl.convert")

    @staticmethod
    def test_nested_package_with_own_modules_still_propagates_private_children(
        tmp_path: Path,
    ) -> None:
        """Direct exports never make a nested package drop ``_x`` child exports.

        Regression for the defect where a nested package with its own exporting
        modules dropped every private child (``owns_export_surface``). Only the
        public facade root withholds private children; no package publishes a
        child package object itself.
        """
        repository_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        services_root = package_root / "services"
        facade_dir = services_root / "_codegen"
        facade_dir.mkdir(parents=True)
        services_root.joinpath("runner.py").write_text(
            'class FlextTestsRunner:\n    """Direct services export."""\n\n'
            '__all__ = ["FlextTestsRunner"]\n',
            encoding=c.DEFAULT_ENCODING,
        )
        facade_dir.joinpath("planner.py").write_text(
            'class FlextTestsPlanner:\n    """Private child export."""\n\n'
            '__all__ = ["FlextTestsPlanner"]\n',
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)

        generated_services = u.Tests.generated_init(services_root)
        generated_root = u.Tests.generated_init(package_root)

        tm.that(
            generated_services,
            has=[
                '"FlextTestsRunner": ".runner"',
                '"FlextTestsPlanner": "._codegen.planner"',
            ],
        )
        tm.that(generated_services, lacks='"_codegen": "._codegen"')
        tm.that(
            generated_root,
            lacks=['"services"', "FlextTestsPlanner", "FlextTestsRunner"],
        )
        tm.that(u.Tests.run_lazy_init(repository_root, check_only=True), eq=0)
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"from {package_root.name}.services import FlextTestsPlanner\n"
                f"from {package_root.name}.services._codegen.planner import "
                "FlextTestsPlanner as declared\n"
                "print(FlextTestsPlanner is declared)\n",
                python_paths=(str(package_root.parent),),
                cwd=repository_root,
            ),
            eq=["True"],
        )
