"""Public lazy-init behavior for nested private ``_<facade>/`` directories.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

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
