"""Real consumer qualification of native parameter replacement and retirement.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import runpy
from pathlib import Path

from tests import c, m, p, tm, u


class TestsFlextInfraNativeSignatureRemoval:
    """Native plans retain actual calls, annotations and repeatability."""

    @staticmethod
    @c.Tests.MARK.parametrize(
        ("source", "target", "replacement"),
        [
            u.Tests.param(
                "import inspect\n"
                "def build(value: str, index: str, suffix: str = '!') -> str:\n"
                "    return value + index + suffix\n"
                "evidence = (build('a', 'b'), "
                "build(value='a', index='b', suffix='?'))\n"
                "annotations = tuple((name, value) for name, value in "
                "build.__annotations__.items() if name != 'index')\n"
                "parameter_names = tuple(inspect.signature(build).parameters)\n",
                "build",
                "'b'",
                id="middle-positional-and-keyword-callers",
            ),
            u.Tests.param(
                "import inspect\n"
                "from rope.base.pyobjectsdef import PyModule\n"
                "class Owner:\n"
                "    @staticmethod\n"
                "    def build(module: PyModule, index: object, *, "
                "directory: str, declared_names: frozenset[str]) -> bool:\n"
                "        return index is module.get_source_binding_index() "
                "and directory in declared_names\n"
                "evidence = (\n"
                "    Owner.build(module, module.get_source_binding_index(), "
                "directory='member', declared_names=frozenset({'member'})),\n"
                "    Owner.build(module=module, "
                "index=module.get_source_binding_index(), "
                "directory='member', declared_names=frozenset({'member'})),\n"
                ")\n"
                "annotations = tuple((name, value) for name, value in "
                "Owner.build.__annotations__.items() if name != 'index')\n"
                "parameter_names = tuple(inspect.signature(Owner.build).parameters)\n",
                "Owner.build",
                "module.get_source_binding_index()",
                id="native-module-and-required-keyword-only-parameters",
            ),
        ],
    )
    def test_used_parameter_retirement_preserves_real_consumer(
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
        source: str,
        target: str,
        replacement: str,
    ) -> None:
        """Retiring the middle parameter preserves both native caller forms."""
        workspace, path = rope_contract_consumer
        module = workspace.rope_project.get_pymodule(
            u.Infra.file_resource_at(
                workspace.rope_project, path.parent / "__init__.py"
            )
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        before = runpy.run_path(str(path), init_globals={"module": module})
        removal = m.Infra.RopeSignatureRemoval(
            id="native-middle-parameter-retirement",
            target=f"{path.parent.name}.{path.stem}.{target}",
            parameter="index",
            replacement=replacement,
        )
        options = m.Infra.ContractAdmissionOptions(signature_removals=(removal,))
        planned = tm.ok(
            u.Infra.plan_contract_rules(workspace, {path: source}, (), options=options)
        )
        tm.that(len(planned), eq=1)
        updated = planned[0].updated_source
        path.write_text(updated, encoding=c.DEFAULT_ENCODING)
        after = runpy.run_path(str(path), init_globals={"module": module})
        tm.that(after["evidence"], eq=before["evidence"])
        tm.that(after["annotations"], eq=before["annotations"])
        tm.fail(removal.parameter in after["parameter_names"])
        tm.that(
            tm.ok(
                u.Infra.plan_contract_rules(
                    workspace, {path: updated}, (), options=options
                )
            ),
            empty=True,
        )
