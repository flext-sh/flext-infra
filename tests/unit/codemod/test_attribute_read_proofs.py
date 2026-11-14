"""Native read-effect proofs for Rope's method transfer adapter.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

from tests import c, m, tm, u


class TestsFlextInfraAttributeReadProofs:
    """Proofs follow lazy exports and refuse custom getter behavior."""

    @staticmethod
    def _workspace(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        provider = package / "provider"
        provider.mkdir()
        (provider / "__init__.py").write_text(
            "from flext_core.lazy import install_lazy_exports\n"
            "__all__ = ('h', 'm')\n"
            "install_lazy_exports(__name__, globals(), {"
            "'h': '.handlers', 'm': '.models'}, public_exports=__all__)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (provider / "handlers.py").write_text(
            "from flext_core import h\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (provider / "models.py").write_text(
            "class Models:\n"
            "    class DemoApp:\n"
            "        class ResyncInput:\n"
            "            pass\n"
            "m = Models\n",
            encoding=c.DEFAULT_ENCODING,
        )
        destination = package / "destination.py"
        destination.write_text("class Target:\n    pass\n", encoding=c.DEFAULT_ENCODING)
        consumer = package / "consumer.py"
        consumer.write_text(
            "from flext_test_project.provider import h, m\n"
            "class Legacy:\n"
            "    @h.handler(command=m.DemoApp.ResyncInput)\n"
            "    def execute(self, request):\n"
            "        return request\n",
            encoding=c.DEFAULT_ENCODING,
        )
        return root, package, consumer, destination

    @staticmethod
    def _observe(root: Path, package: Path, module: str, owner: str) -> str:
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        "from flext_core import c; "
                        f"from {package.name}.{module} import {owner}; "
                        f"instance = {owner}(); "
                        "print(instance.execute('retained')); "
                        "print(getattr(instance.execute, "
                        "c.HANDLER_ATTR).command.__qualname__)"
                    ),
                ),
                cwd=root,
                timeout=c.Infra.TIMEOUT_SHORT,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        return result.stdout

    @staticmethod
    def test_native_transfer_preserves_real_handler_behavior(tmp_path: Path) -> None:
        """The moved method executes with its real handler and command metadata."""
        root, package, consumer, destination = (
            TestsFlextInfraAttributeReadProofs._workspace(tmp_path)
        )
        observed = TestsFlextInfraAttributeReadProofs._observe(
            root, package, "consumer", "Legacy"
        )
        with u.Infra.facade_source_project(root) as (project, _sources):
            changes = tm.not_none(
                u.Infra.method_transfer_changes(
                    project,
                    m.Infra.RopeMethodTransfer(
                        id="native-handler-attribute-behavior",
                        destination=(f"{package.name}.destination", "Target"),
                        methods=((f"{package.name}.consumer", "Legacy.execute"),),
                    ),
                    (consumer, destination),
                    u.Infra.source_member_resolver(project, sources={}),
                )
            )
            for change in tm.ok(
                u.Infra.change_set_members(changes.changes, "invalid native changes")
            ):
                Path(change.resource.real_path).write_text(
                    change.new_contents, encoding=c.DEFAULT_ENCODING
                )
        tm.that(
            TestsFlextInfraAttributeReadProofs._observe(
                root, package, "destination", "Target"
            ),
            eq=observed,
        )

    @staticmethod
    def test_custom_metaclass_getter_refuses_before_rope_changes(
        tmp_path: Path,
    ) -> None:
        """A class-level __getattribute__ that varies metadata is refused."""
        root, package, consumer, _destination = (
            TestsFlextInfraAttributeReadProofs._workspace(tmp_path)
        )
        (package / "provider" / "models.py").write_text(
            "import inspect\n"
            "class DynamicMeta(type):\n"
            "    def __getattribute__(cls, name):\n"
            "        if name == 'ResyncInput':\n"
            "            return int if inspect.currentframe().f_back.f_code.co_name == "
            "'<module>' else str\n"
            "        return super().__getattribute__(name)\n"
            "class Models(metaclass=DynamicMeta):\n"
            "    class DemoApp:\n"
            "        class ResyncInput:\n"
            "            pass\n"
            "m = Models\n",
            encoding=c.DEFAULT_ENCODING,
        )
        with u.Infra.facade_source_project(root) as (project, _sources):
            resolver = u.Infra.source_member_resolver(project, sources={})
            resource = project.get_resource(consumer.relative_to(root).as_posix())
            module = project.get_pymodule(resource)
            function = (
                module
                .get_attribute("Legacy")
                .get_object()
                .get_attribute("execute")
                .get_object()
            )
            with u.Tests.raises(ValueError, match="non-builtin getter"):
                u.Infra.attribute_read_proofs(project, resource, function, resolver)
