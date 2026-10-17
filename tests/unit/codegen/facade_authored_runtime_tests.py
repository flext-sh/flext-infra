"""Generation preserves authored runtime outside declared family composition.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import c
from tests import p, tm, u


class TestsFlextInfraFacadeAuthoredRuntime:
    """Exercise preservation through generation and a fresh public consumer."""

    @staticmethod
    @pytest.mark.parametrize("consumer_fails", [False, True])
    def test_source_epoch_failure_preserves_consumer_exception(
        tmp_path: Path,
        *,
        consumer_fails: bool,
    ) -> None:
        """Changed inputs reject success but never replace a consumer's exception."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / c.Infra.INIT_PY
        tm.ok(u.Cli.atomic_write_text_file(path, ""))
        failure = RuntimeError("consumer failed before source verification")
        with (
            pytest.raises(
                RuntimeError if consumer_fails else ValueError,
                match="consumer failed|atomic source changed",
            ) as caught,
            u.Infra.facade_source_project(root) as (project, _, _),
        ):
            project.get_pymodule(project.get_resource(path.relative_to(root).as_posix()))
            tm.ok(u.Cli.atomic_write_text_file(path, "# Changed source epoch\n"))
            if consumer_fails:
                raise failure
        if consumer_fails:
            tm.that(caught.value is failure)
        else:
            tm.that(caught.value is not failure)

    @staticmethod
    def test_declared_projection_preserves_authored_bindings(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """Unrelated authored bindings keep working after the family is published."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY)
        facade = package / c.Infra.UTILITIES_PY
        sources = {
            package / c.Infra.INIT_PY: "",
            package / family.directory / "owner.py": (
                "class Owner:\n    marker = 'owner'\n__all__ = ['Owner']\n"
            ),
            package / family.directory / "support.py": (
                "class AuthoredSupport:\n"
                "    @staticmethod\n"
                "    def render(value):\n"
                "        return value.upper()\n"
                "__all__ = []\n"
            ),
            facade: (
                f"from {package.name}.{family.directory}.owner import Owner\n"
                f"from {package.name}.{family.directory}.support "
                "import AuthoredSupport\n"
                "def authored_value(value):\n"
                "    return AuthoredSupport.render(value)\n"
                "class Utilities(Owner):\n"
                "    @classmethod\n"
                "    def read(cls, value):\n"
                "        return authored_value(value) + ':' + cls.marker\n"
                "u = Utilities\n"
                "__all__ = ['Utilities', 'u']\n"
            ),
        }
        for path, source in sources.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        rendered = tm.not_none(u.Infra.render_utility_facade(package))
        tm.ok(u.Cli.atomic_write_text_file(facade, rendered))
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        tm.that(u.Infra.render_utility_facade(package), eq=rendered)
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name} import u\n"
            "assert u.read('value') == 'VALUE:owner'\n"
            "class Receiver(u):\n"
            "    marker = 'receiver'\n"
            "assert Receiver.read('value') == 'VALUE:receiver'\n",
            cwd=root,
        )

    @staticmethod
    def test_checkout_environment_is_never_a_planning_source(tmp_path: Path) -> None:
        """Dependency modules read from the checkout environment stay inputs only.

        Premise (70dc29f1b9 regression): the lazy-init plans carry every state
        their native reads consumed, including dependency modules installed in
        the checkout-local environment. Those states entered the planned-source
        map, so the facade planner treated the installed dependency as a
        project package and republished its facade inside the environment
        (cosmos-charts lost an importable flext_cli this way).
        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        installed = (
            root
            / c.Infra.ENVIRONMENT_DIRECTORY
            / "lib"
            / "site-packages"
            / "flext_dependency"
        )
        files = {
            package / c.Infra.INIT_PY: "",
            installed / c.Infra.INIT_PY: "",
            installed / c.Infra.UTILITIES_PY: "class Dependency:\n    pass\n",
        }
        for path, source in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        states = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in files
        )
        with u.Infra.facade_source_project(root, source_states=states) as binding:
            project, consumed, sources = binding
            project.get_pymodule(
                project.get_resource(
                    (installed / c.Infra.UTILITIES_PY).relative_to(root).as_posix()
                )
            )
            tm.that(
                {path.resolve() for path in sources},
                eq={(package / c.Infra.INIT_PY).resolve()},
            )
            tm.that(
                {state.path.resolve() for state in consumed()[0]},
                has=(installed / c.Infra.UTILITIES_PY).resolve(),
            )
