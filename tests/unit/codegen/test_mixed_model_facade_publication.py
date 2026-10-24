"""Native model publication keeps composed namespaces separate from whole models.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import c, p, tm, u


@pytest.mark.parametrize("stale_model_base", [False, True])
@pytest.mark.parametrize("annotated", [False, True])
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
    (directory / c.Infra.INIT_PY).write_text("", encoding=c.Infra.ENCODING_DEFAULT)
    imports += f"from {package.name}.{family.directory}.credential import Credential\n"
    password_annotation = ": ClassVar[type[Credential]]" if annotated else ""
    facade = package / f"{family.module}.py"
    facade.write_text(
        c.Infra.AUTOGEN_HEADERS[0]
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
    first = tm.not_none(u.Infra.render_utility_facade(package, family="m"))
    facade.write_text(first, encoding=c.Infra.ENCODING_DEFAULT)
    native_consumer(
        f"sys.path.insert(0, {str(package.parent)!r})\n"
        "from pydantic import BaseModel\n"
        f"from {package.name}.models import m\n"
        + imports
        + "owners = (Actions, Connections, Queries, Catalog)\n"
        "assert m.Sample.__bases__ == owners\n"
        "assert m.Sample.__mro__ == (m.Sample, *owners, object)\n"
        "assert not issubclass(m.Sample, BaseModel)\n"
        "assert Credential not in m.Sample.__mro__\n"
        "assert m.Sample.Password is Credential\n"
        "assert m.Sample.Operation is Actions.Operation\n"
        "assert m.Sample.Health is Connections.Health\n"
        "assert m.Sample.Row is Queries.Row\n"
        "assert m.Sample.Column is Catalog.Column\n"
        "assert {'Operation', 'Health', 'Row', 'Column'}.isdisjoint(vars(m.Sample))\n"
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
    second = tm.not_none(u.Infra.render_utility_facade(package, family="m"))
    tm.that(second, eq=first)
    tm.that(
        u.Infra.render_utility_facade(package, family=c.Infra.FacadeFamily.M),
        eq=second,
    )
