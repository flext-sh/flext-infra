"""Native contract calls bind through declared family owners without self cycles.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from flext_infra import infra
from tests import c, m, p, t, tm, u


class TestsRopeContractFamilyRoutes:
    """Exercise real lazy publication, function identity and cold composition."""

    @staticmethod
    @pytest.mark.parametrize("helper_binding", ["absent", "alias", "module", "shadow"])
    def test_same_family_never_reenters_composing_facade(
        tmp_path: Path, helper_binding: str
    ) -> None:
        """A declaration-time call must import only the published helper owner."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = package / u.Infra.facade_families()["u"].directory
        family.mkdir(exist_ok=True)
        namespace = package.name
        provider = f"{namespace}.{family.name}.codec.Codec.normalize"
        helper_import = {
            "absent": "",
            "alias": f"from {namespace}.{family.name} import Codec as Encoder\n",
            "module": f"import {namespace}.{family.name} as helpers\n",
            "shadow": "Codec = str\n",
        }[helper_binding]
        path = family / "consumer.py"
        sources = {
            package / "__init__.py": (
                "from types import MappingProxyType\n"
                "from typing import TYPE_CHECKING\n"
                "if TYPE_CHECKING:\n    from .utilities import u\n"
                "from flext_core.lazy import install_lazy_exports\n"
                "install_lazy_exports(__name__, globals(), "
                "MappingProxyType({'u': '.utilities'}))\n"
                "__all__ = ['u']\n"
            ),
            family / "__init__.py": (
                "from types import MappingProxyType\n"
                "from typing import TYPE_CHECKING\n"
                "if TYPE_CHECKING:\n"
                "    from .codec import Codec\n"
                "    from .consumer import Consumer\n"
                "from flext_core.lazy import install_lazy_exports\n"
                "install_lazy_exports(__name__, globals(), "
                "MappingProxyType({'Codec': '.codec', 'Consumer': '.consumer'}))\n"
                "__all__ = ['Codec', 'Consumer']\n"
            ),
            family / "codec.py": (
                "from flext_core import u as sdk\n"
                "class Codec:\n"
                "    @staticmethod\n"
                "    def normalize(value):\n"
                "        return sdk.normalize_to_json_value(value)\n"
                "__all__ = ['Codec']\n"
            ),
            package / "legacy.py": (
                "from flext_core import u as sdk\n"
                "class Legacy:\n"
                "    @staticmethod\n"
                "    def normalize(val):\n"
                "        return sdk.normalize_to_json_value(val)\n"
                "__all__ = ['Legacy']\n"
            ),
            path: (
                f"from {namespace}.legacy import Legacy\n"
                f"{helper_import}"
                "class Consumer:\n"
                "    registered = Legacy.normalize(val={'ready': None})\n"
                "    @staticmethod\n"
                "    def emit(value):\n"
                "        return Legacy.normalize(value)\n"
                "__all__ = ['Consumer']\n"
            ),
            package / "utilities.py": (
                f"from {namespace}.{family.name} import Consumer, Codec\n"
                "class Utilities(Consumer, Codec):\n"
                "    marker = 'richer'\n"
                "u = Utilities\n__all__ = ['u']\n"
            ),
        }
        for source_path, source in sources.items():
            source_path.write_text(source, encoding=c.DEFAULT_ENCODING)
        rules: list[p.Infra.RopeContractRule] = [
            m.Infra.RopeContractRule(
                id=f"native-json-{index}",
                pattern=pattern,
                goal="u.normalize(${value})",
                arguments={"normalizer": f"name={namespace}.legacy.Legacy.normalize"},
                call_target="normalizer",
                imports={"u": f"from {namespace} import u"},
                bindings={"u.normalize": provider},
            )
            for index, pattern in enumerate((
                "${normalizer}(${value})",
                "${normalizer}(val=${value})",
            ))
        ]
        with infra.rope_workspace(root) as workspace:
            if helper_binding == "shadow":
                with pytest.raises(ValueError, match="shadowed"):
                    u.Infra.plan_contract_rules(workspace, sources, rules)
                tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=sources[path])
                return
            edits = tm.ok(u.Infra.plan_contract_rules(workspace, sources, rules))
            updated = {
                **sources,
                **{edit.file_path: edit.updated_source for edit in edits},
            }
            tm.that(updated[path], lacks=f"from {namespace} import u")
            tm.that(updated[path], lacks="Legacy.normalize(")
            if helper_binding == "alias":
                tm.that(updated[path], has="Encoder.normalize(")
            elif helper_binding == "module":
                tm.that(updated[path], has="helpers.Codec.normalize(")
            else:
                tm.that(
                    updated[path], has=f"from {namespace}.{family.name} import Codec"
                )
            tm.that(
                tm.ok(u.Infra.plan_contract_rules(workspace, updated, rules)),
                empty=True,
            )
        for source_path, source in updated.items():
            source_path.write_text(source, encoding=c.DEFAULT_ENCODING)
        outcome = tm.ok(
            u.Cli.run((
                sys.executable,
                "-c",
                (
                    f"import sys\nsys.path.insert(0, {str(package.parent)!r})\n"
                    f"from {namespace} import u\n"
                    "if u.registered != {'ready': None} or u.emit([None]) != [None]:\n"
                    "    raise RuntimeError('native JSON contract changed')\n"
                    "if u.marker != 'richer':\n"
                    "    raise RuntimeError('composed facade was replaced')\n"
                ),
            ))
        )
        tm.ok(u.Cli.process_succeeded(outcome.outcome))

    @staticmethod
    def test_richer_foreign_facade_binding_is_unchanged(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
    ) -> None:
        """Inherited native function identity already permits an upstream facade."""
        workspace, path = rope_contract_consumer
        source = (
            "from flext_cli import u\n"
            "class Legacy:\n"
            "    @staticmethod\n"
            "    def normalize(value):\n"
            "        return u.normalize_to_json_value(value)\n"
            "value = Legacy.normalize({'key': None})\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        rule = m.Infra.RopeContractRule(
            id="native-json-rich-facade",
            pattern="${normalizer}(${value})",
            goal="u.normalize_to_json_value(${value})",
            arguments={
                "normalizer": f"name={path.parent.name}.{path.stem}.Legacy.normalize"
            },
            call_target="normalizer",
            imports={"u": "from flext_core import u"},
            bindings={
                "u.normalize_to_json_value": (
                    "flext_core._utilities.pydantic."
                    "FlextUtilitiesPydantic.normalize_to_json_value"
                )
            },
        )
        edits = tm.ok(u.Infra.plan_contract_rules(workspace, {path: source}, (rule,)))
        tm.that(len(edits), eq=1)
        tm.that(edits[0].updated_source, has="from flext_cli import u")
        tm.that(edits[0].updated_source, lacks="from flext_core import u")
        tm.that(edits[0].updated_source, has="u.normalize_to_json_value(")

    @staticmethod
    @pytest.mark.parametrize("arguments", ["*args", "**kwargs"])
    def test_expanded_arguments_cannot_authorize_contract_normalization(
        rope_contract_consumer: t.Pair[p.Infra.RopeWorkspaceDsl, Path],
        arguments: str,
    ) -> None:
        """Unknown argument bindings cannot authorize val-to-value normalization."""
        workspace, path = rope_contract_consumer
        source = (
            "from flext_core import u\n"
            "class Legacy:\n"
            "    @staticmethod\n"
            "    def normalize(val):\n"
            "        return u.normalize_to_json_value(val)\n"
            "args = ({'key': None},)\nkwargs = {'val': {'key': None}}\n"
            f"value = Legacy.normalize({arguments})\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        rule = m.Infra.RopeContractRule(
            id="native-json-explicit-arguments",
            pattern="${normalizer}",
            goal="u.normalize_to_json_value",
            arguments={
                "normalizer": f"name={path.parent.name}.{path.stem}.Legacy.normalize"
            },
            call_target="normalizer",
            explicit_arguments=True,
            imports={"u": "from flext_core import u"},
            bindings={
                "u.normalize_to_json_value": (
                    "flext_core._utilities.pydantic."
                    "FlextUtilitiesPydantic.normalize_to_json_value"
                )
            },
        )
        with pytest.raises(ValueError, match="expanded arguments"):
            u.Infra.plan_contract_rules(workspace, {path: source}, (rule,))
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
