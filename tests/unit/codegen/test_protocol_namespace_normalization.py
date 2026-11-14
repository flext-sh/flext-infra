"""Preserve the protocol facade contract for non-Infra projects.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from collections.abc import Mapping
from pathlib import Path

import pytest

from flext_infra.protocols_bootstrap import normalize_protocol_source
from tests import p, tm, u


def test_project_model_annotations_become_protocols_idempotently() -> None:
    """Normalize a project's structural annotation exactly once."""
    source = (
        "from __future__ import annotations\n"
        "from typing import Protocol\n"
        "class DemoAppProtocolsSettings:\n"
        "    class Settings(Protocol):\n"
        "        DemoApp: m.DemoApp.SettingsNamespace\n"
        "        external: m.Foreign.Record\n"
    )
    result = normalize_protocol_source(source, package_name="demo_app")
    tm.that(result, has="DemoApp: p.DemoApp.SettingsNamespace")
    tm.that(result, has="from demo_app import p")
    tm.that(result, has="external: m.Foreign.Record")
    tm.that(normalize_protocol_source(result, package_name="demo_app"), eq=result)


def test_projected_protocol_keeps_pydantic_annotation_import(
    tmp_path: Path, native_consumer: p.Tests.NativeConsumer
) -> None:
    """A source type alias used by a field stays bound in the projected contract."""
    root, package = u.Tests.create_lazy_init_workspace(tmp_path)
    sources = {
        package / "models.py": (
            f"from {package.name}._models.payload import ModelsPayload\n"
            "class Models(ModelsPayload): pass\nm = Models\n__all__ = ['Models', 'm']\n"
        ),
        package / "protocols.py": (
            "class Protocols: pass\np = Protocols\n__all__ = ['Protocols', 'p']\n"
        ),
        package / "_models/payload.py": (
            "from pydantic import BaseModel, StrictStr\n"
            "class ModelsPayload:\n"
            "    class Item(BaseModel):\n"
            "        name: StrictStr\n"
        ),
    }
    for path, source in sources.items():
        tm.ok(u.Cli.ensure_dir(path.parent))
        tm.ok(u.Cli.atomic_write_text_file(path, source))
    with u.Infra.facade_source_project(root) as binding:
        sources = tm.ok(u.Infra.protocol_model_sources_from_source(root, binding[0]))
    generated = sources[(package / "_protocols/payload.py").relative_to(root)]
    tm.that(generated, has="from pydantic import StrictStr")
    for relative, content in sources.items():
        tm.ok(u.Cli.ensure_dir((root / relative).parent))
        tm.ok(u.Cli.atomic_write_text_file(root / relative, content))
    native_consumer(
        f"import sys\nsys.path.insert(0, {str(package.parent)!r})\n"
        "from typing import get_type_hints\n"
        f"from {package.name}._protocols.payload import ProtocolsPayload\n"
        "from flext_tests import tm\n"
        "tm.that(get_type_hints(ProtocolsPayload.Item)['name'], eq=str)\n",
        cwd=root,
    )


def test_authored_protocol_projection_is_stable_on_first_publication(
    tmp_path: Path,
) -> None:
    """A newly projected sibling and its authored consumer converge in one pass."""
    root, package = u.Tests.create_lazy_init_workspace(
        tmp_path, project_name="demo-app", package_name="demo_app"
    )
    files = {
        package / "models.py": (
            "from demo_app._models.config import DemoAppConfigModels\n"
            "class DemoAppModels:\n"
            "    class DemoApp(DemoAppConfigModels): pass\n"
            "m = DemoAppModels\n__all__ = ['DemoAppModels', 'm']\n"
        ),
        package / "protocols.py": (
            "from demo_app._protocols.config import DemoAppProtocolsConfig\n"
            "class DemoAppProtocols:\n"
            "    class DemoApp(DemoAppProtocolsConfig): pass\n"
            "p = DemoAppProtocols\n__all__ = ['DemoAppProtocols', 'p']\n"
        ),
        package / "_models/config.py": (
            "from pydantic import BaseModel, StrictStr\n"
            "class DemoAppConfigModels:\n"
            "    class ConfigNamespace(BaseModel):\n"
            "        name: StrictStr\n"
        ),
        package / "_protocols/config.py": (
            "from __future__ import annotations\n"
            "from typing import Protocol\n"
            "class DemoAppProtocolsConfig:\n"
            "    class Config(Protocol):\n"
            "        DemoApp: m.DemoApp.ConfigNamespace\n"
            "__all__ = ['DemoAppProtocolsConfig']\n"
        ),
        package / "_protocols/__init__.py": (
            "from .config import DemoAppProtocolsConfig\n"
            "__all__ = ['DemoAppProtocolsConfig']\n"
        ),
    }
    for path, content in files.items():
        tm.ok(u.Cli.ensure_dir(path.parent))
        tm.ok(u.Cli.atomic_write_text_file(path, content))
    with u.Infra.facade_source_project(root) as binding:
        first = tm.ok(u.Infra.protocol_model_sources_from_source(root, binding[0]))
    for path, content in first.items():
        tm.ok(u.Cli.ensure_dir((root / path).parent))
        tm.ok(u.Cli.atomic_write_text_file(root / path, content))
    with u.Infra.facade_source_project(root) as binding:
        second = tm.ok(u.Infra.protocol_model_sources_from_source(root, binding[0]))
    destination = (package / "_protocols/config.py").relative_to(root)
    tm.that(second[destination], eq=first[destination])


def _project_sources(
    tmp_path: Path, models: str, *, published: tuple[str, ...] = ("ModelsPayload",)
) -> p.Result[Mapping[Path, str]]:
    """Project one ``_models/payload.py`` source through the public generator API.

    Returns:
        The generator's protocol sources, or its original failure.

    """
    root, package = u.Tests.create_lazy_init_workspace(tmp_path)
    exports = ", ".join(published)
    sources = {
        package / "models.py": (
            f"from {package.name}._models.payload import ModelsPayload\n"
            "class Models(ModelsPayload): pass\nm = Models\n__all__ = ['Models', 'm']\n"
        ),
        package / "protocols.py": (
            "class Protocols: pass\np = Protocols\n__all__ = ['Protocols', 'p']\n"
        ),
        package / "_models/payload.py": models + f"__all__ = [{exports!r}]\n",
    }
    for path, source in sources.items():
        tm.ok(u.Cli.ensure_dir(path.parent))
        tm.ok(u.Cli.atomic_write_text_file(path, source))
    with u.Infra.facade_source_project(root) as binding:
        return u.Infra.protocol_model_sources_from_source(root, binding[0]).map(
            lambda rendered: {
                path: text
                for path, text in rendered.items()
                if path == (package / "_protocols/payload.py").relative_to(root)
            }
        )


def test_republished_module_model_is_not_a_self_alias(tmp_path: Path) -> None:
    """``X = X`` republishes the model whose contract already owns its route."""
    sources = tm.ok(
        _project_sources(
            tmp_path,
            "from pydantic import BaseModel, StrictStr\n"
            "class Item(BaseModel):\n"
            "    name: StrictStr\n"
            "class ModelsPayload:\n"
            "    Item = Item\n",
        )
    )
    (generated,) = sources.values()
    tm.that(generated, has="class Item(")
    tm.that(generated, lacks="type Item =")


def test_unpublished_source_declaration_fails_loud(tmp_path: Path) -> None:
    """A field typed by a plain module class has no bindable Protocol name."""
    with pytest.raises(ValueError, match="neither a model nor an import") as raised:
        _project_sources(
            tmp_path,
            "from __future__ import annotations\n"
            "from dataclasses import dataclass\n"
            "from pydantic import BaseModel\n"
            "@dataclass(frozen=True)\n"
            "class Column:\n"
            "    end: int\n"
            "class Account(BaseModel):\n"
            "    code: str\n"
            "class ModelsPayload:\n"
            "    Account = Account\n"
            "    class Layout(BaseModel):\n"
            "        account: Account | None\n"
            "        columns: list[Column] | None\n",
        )
    tm.that(str(raised.value), has="payload.Column;")
    tm.that(str(raised.value), lacks="Account")
