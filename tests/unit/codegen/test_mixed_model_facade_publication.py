"""Native model publication keeps composed namespaces separate from whole models.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

from tests import c, m, p, tm, u


@c.Tests.MARK.parametrize("stale_model_base", [False, True])
@c.Tests.MARK.parametrize("annotated", [False, True])
def test_mixed_model_publication_preserves_identity_and_cold_fixed_point(
    tmp_path: Path,
    native_consumer: p.Tests.NativeConsumer,
    *,
    stale_model_base: bool,
    annotated: bool,
) -> None:
    """Compose plain owners while publishing a complete model without inheriting it."""
    root, package = u.Tests.create_lazy_init_workspace(tmp_path)
    family = u.Infra.facade_families()["m"]
    directory = package / family.directory
    directory.mkdir()
    owners = (
        ("commands", "Actions", "Operation"),
        ("connection", "Connections", "Health"),
        ("queries", "Queries", "Row"),
        ("schema", "Catalog", "Column"),
    )
    imports = ""
    aliases = ""
    for module, owner, nested in owners:
        (directory / f"{module}.py").write_text(
            "from pydantic import BaseModel\n"
            f"class {owner}:\n"
            f"    class {nested}(BaseModel):\n"
            "        value: str\n"
            f"__all__ = [{owner!r}]\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        imports += f"from {package.name}.{family.directory}.{module} import {owner}\n"
        annotation = f": ClassVar[type[{owner}.{nested}]]" if annotated else ""
        aliases += f"        {nested}{annotation} = {owner}.{nested}\n"
    (directory / "credential.py").write_text(
        "from pydantic import ConfigDict, RootModel\n"
        "class Credential(RootModel[str]):\n"
        "    model_config = ConfigDict(frozen=True)\n"
        "    def __str__(self):\n"
        "        return self.root\n"
        "    def reveal(self):\n"
        "        return self.root\n"
        "    def __hash__(self):\n"
        "        return hash(self.reveal())\n"
        "__all__ = ['Credential']\n",
        encoding=c.Infra.ENCODING_DEFAULT,
    )
    (directory / "containers.py").write_text(
        "class FrozenList(list[str]): pass\n"
        "class FrozenMapping(dict[str, str]): pass\n"
        "__all__ = ['FrozenList', 'FrozenMapping']\n",
        encoding=c.Infra.ENCODING_DEFAULT,
    )
    (directory / c.Infra.INIT_PY).write_text("", encoding=c.Infra.ENCODING_DEFAULT)
    imports += f"from {package.name}.{family.directory}.credential import Credential\n"
    password_annotation = ": ClassVar[type[Credential]]" if annotated else ""
    facade = package / f"{family.module}.py"
    facade.write_text(
        c.Infra.AUTOGEN_HEADER
        + "\nfrom typing import ClassVar\n"
        + imports
        + "class Public:\n"
        + (
            "    class Sample(Credential):\n"
            if stale_model_base
            else "    class Sample:\n"
        )
        + f"        Password{password_annotation} = Credential\n"
        + aliases
        + "m = Public\n__all__ = ['Public', 'm']\n",
        encoding=c.Infra.ENCODING_DEFAULT,
    )
    tm.that(u.Tests.run_lazy_init(root), eq=0)
    first = tm.ok(tm.not_none(u.Infra.render_utility_facade(package, family="m")))
    facade.write_text(first, encoding=c.Infra.ENCODING_DEFAULT)
    tm.that(u.Tests.run_lazy_init(root), eq=0)
    native_consumer(
        f"sys.path.insert(0, {str(package.parent)!r})\n"
        "from pydantic import BaseModel\n"
        f"from {package.name}.models import m\n"
        f"from {package.name}.{family.directory}.containers import FrozenList, "
        f"FrozenMapping\n"
        + imports
        + "owners = (Actions, Connections, Queries, Catalog)\n"
        "assert set(m.Sample.__bases__) == set(owners), m.Sample.__bases__\n"
        "assert m.Sample.__mro__ == (m.Sample, *m.Sample.__bases__, object)\n"
        "assert not issubclass(m.Sample, BaseModel)\n"
        "assert Credential not in m.Sample.__mro__\n"
        "assert m.Sample.FrozenList is FrozenList\n"
        "assert m.Sample.FrozenMapping is FrozenMapping\n"
        "assert m.Sample.FrozenList(['item']) == ['item']\n"
        "assert m.Sample.FrozenMapping(key='value') == {'key': 'value'}\n"
        "assert m.Sample.Password is Credential\n"
        "assert m.Sample.Operation is Actions.Operation\n"
        "assert m.Sample.Health is Connections.Health\n"
        "assert m.Sample.Row is Queries.Row\n"
        "assert m.Sample.Column is Catalog.Column\n"
        "assert {'Operation', 'Health', 'Row', 'Column'}.isdisjoint(vars(m.Sample)), "
        + repr(first)
        + "\n"
        "assert not hasattr(m.Sample, 'model_fields')\n"
        "password = m.Sample.Password('native-secret')\n"
        "original = Credential('native-secret')\n"
        "assert str(password) == str(original)\n"
        "assert password.reveal() == original.reveal()\n"
        "assert hash(password) == hash(original)\n"
        "assert password.model_json_schema() == Credential.model_json_schema()\n"
        "assert password.model_dump_json() == original.model_dump_json()\n"
        "class Envelope(BaseModel):\n"
        "    password: m.Sample.Password\n"
        "    column: m.Sample.Column\n"
        "column = Catalog.Column(value='native-column')\n"
        "envelope = Envelope(password=password, column=column)\n"
        "assert envelope.password is password\n"
        "assert envelope.column is column\n"
        "assert Envelope.model_fields['column'].annotation is Catalog.Column\n"
        "restored = Envelope.model_validate_json(envelope.model_dump_json())\n"
        "assert restored.column == column\n"
        "assert restored.password == Credential.model_validate_json(\n"
        "    original.model_dump_json())\n"
        "assert restored.model_dump_json() == envelope.model_dump_json()\n",
        cwd=root,
    )
    second = tm.ok(tm.not_none(u.Infra.render_utility_facade(package, family="m")))
    tm.that(second, eq=first)
    tm.ok(
        tm.not_none(
            u.Infra.render_utility_facade(package, family=c.Infra.FacadeFamily.M)
        ),
        eq=second,
    )


def test_models_infra_inherited_members_keep_native_static_types(
    tmp_path: Path,
    native_consumer: p.Tests.NativeConsumer,
    session_runtime: p.Tests.SessionRuntime,
) -> None:
    """Inherited model members preserve their static types and native identities."""
    root, package = u.Tests.create_lazy_init_workspace(tmp_path)
    directory = package / u.Infra.facade_families()["m"].directory
    directory.mkdir()
    (directory / "actions.py").write_text(
        "from pydantic import BaseModel\n"
        "class Actions:\n"
        "    class Operation(BaseModel):\n"
        "        value: str\n"
        "__all__ = ['Actions']\n",
        encoding=c.Infra.ENCODING_DEFAULT,
    )
    (directory / "health.py").write_text(
        "from pydantic import BaseModel\n"
        "class Healths:\n"
        "    class Health(BaseModel):\n"
        "        value: str\n"
        "__all__ = ['Healths']\n",
        encoding=c.Infra.ENCODING_DEFAULT,
    )
    (directory / c.Infra.INIT_PY).write_text("", encoding=c.Infra.ENCODING_DEFAULT)
    facade = package / "models.py"
    facade.write_text(
        "from flext_test_project._models.actions import Actions\n"
        "from flext_test_project._models.health import Healths\n"
        "class FlextTestProjectModels:\n"
        "    class Infra(Actions, Healths):\n"
        "        pass\n"
        "m = FlextTestProjectModels\n"
        "__all__ = ['FlextTestProjectModels', 'm']\n",
        encoding=c.Infra.ENCODING_DEFAULT,
    )

    tm.that(u.Tests.run_lazy_init(root), eq=0)
    rendered = tm.ok(tm.not_none(u.Infra.render_utility_facade(package, family="m")))

    facade.write_text(rendered, encoding=c.Infra.ENCODING_DEFAULT)
    tm.that(u.Tests.run_lazy_init(root), eq=0)
    tm.ok(
        u.Tests.create_python_environment(
            root,
            dependency_projects=u.Tests.python_dependency_projects(root),
            session_runtime=session_runtime,
        )
    )
    u.Tests.provision_checkout(root)
    reports = tm.ok(u.Cli.ensure_dir(root / c.Infra.REPORTS_DIR_NAME))
    report = reports / "inherited-model-static.json"
    consumer = package / "consumer.py"
    consumer.write_text(
        tm.ok(
            u.Infra.normalize_python_text(
                consumer,
                '"""Native inherited model constructor contracts.\n\n'
                f'{u.Infra.copyright_notice(package, module=consumer)}\n"""\n'
                "from typing import assert_type\n"
                "from flext_test_project._models.actions import Actions\n"
                "from flext_test_project._models.health import Healths\n"
                "from flext_test_project.models import m\n"
                "operation = m.Infra.Operation(value='native-operation')\n"
                "health = m.Infra.Health(value='native-health')\n"
                "assert_type(operation, Actions.Operation)\n"
                "assert_type(health, Healths.Health)\n",
            )
        ),
        encoding=c.Infra.ENCODING_DEFAULT,
    )
    checked = tm.ok(
        u.Cli.run_raw(
            (
                sys.executable,
                "-m",
                "flext_infra",
                "check",
                "run",
                "--repository-root",
                str(root),
                "--scope",
                "self",
                "--gates",
                "lint,pyrefly,pyright,mypy",
                "--file",
                consumer.relative_to(root).as_posix(),
                "--report-output",
                str(report),
            ),
            cwd=root,
        )
    )
    u.Cli.emit_raw(checked.stdout)
    u.Cli.emit_raw(checked.stderr)
    evidence = m.Infra.CheckReportSummary.model_validate_json(report.read_bytes())
    tm.that(
        u.Cli.process_succeeded(checked.outcome),
        eq=True,
        msg=checked.stdout
        + checked.stderr
        + "\n".join(
            error
            for project in evidence.results
            for gate in project.gates.values()
            for error in gate.result.errors
        ),
    )
    native_consumer(
        f"sys.path.insert(0, {str(package.parent)!r})\n"
        "from flext_test_project.models import m\n"
        "from flext_test_project._models.actions import Actions\n"
        "from flext_test_project._models.health import Healths\n"
        "assert m.Infra.Operation is Actions.Operation\n"
        "assert m.Infra.Health is Healths.Health\n"
        "from flext_test_project.consumer import health, operation\n"
        "assert operation.value == 'native-operation'\n"
        "assert health.value == 'native-health'\n",
        cwd=root,
    )
    tm.ok(tm.not_none(u.Infra.render_utility_facade(package, family="m")), eq=rendered)
