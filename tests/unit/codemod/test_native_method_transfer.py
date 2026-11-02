"""Public native method-transfer contracts over real source projects.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import runpy
from pathlib import Path

import pytest

from tests import c, m, p, tm, u


class TestsFlextInfraNativeMethodTransfer:
    """Preserve actual method behavior and reject unproven ownership changes."""

    @staticmethod
    def test_nested_same_module_transfer_preserves_local_payload_binding(
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
    ) -> None:
        """A transfer cannot synthesize an import from its own source module."""
        workspace, path = rope_contract_consumer
        source = (
            "class Payload:\n"
            "    def __init__(self, value):\n"
            "        self.value = value\n"
            "class Owner:\n"
            "    class Helpers:\n"
            "        @staticmethod\n"
            "        def build(value):\n"
            "            return Payload(value)\n"
            "evidence = Owner.Helpers.build('retained').value\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        before = runpy.run_path(str(path))["evidence"]
        module = f"{path.parent.name}.{path.stem}"
        transfer = m.Infra.RopeMethodTransfer(
            id="same-module-payload-owner",
            destination=(module, "Owner"),
            methods=((module, "Owner.Helpers.build"),),
        )
        planned = tm.ok(
            u.Infra.plan_contract_rules(
                workspace,
                {path: source},
                (),
                options=m.Infra.ContractAdmissionOptions(method_transfers=(transfer,)),
            )
        )
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
        updated = {edit.file_path: edit.updated_source for edit in planned}
        path.write_text(updated[path], encoding=c.DEFAULT_ENCODING)
        namespace = runpy.run_path(str(path))
        tm.that(namespace["evidence"], eq=before)
        tm.that(
            tm.ok(
                u.Infra.plan_contract_rules(
                    workspace,
                    updated,
                    (),
                    options=m.Infra.ContractAdmissionOptions(
                        method_transfers=(transfer,)
                    ),
                )
            ),
            empty=True,
        )

    @staticmethod
    @pytest.mark.parametrize(
        ("destination", "method", "failure"),
        [
            (
                "    @staticmethod\n    def build(value): return value\n",
                "        @staticmethod\n        def build(value): return value\n",
                "occupied method destination",
            ),
            (
                "",
                (
                    "        @classmethod\n        def build(cls, value):\n"
                    "            return cls, value\n"
                ),
                "dependency on its original class",
            ),
        ],
        ids=["occupied-destination", "receiver-value"],
    )
    def test_rejected_transfer_leaves_every_source_unchanged(
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
        destination: str,
        method: str,
        failure: str,
    ) -> None:
        """Native ambiguity and receiver rules reject the complete read-only plan."""
        workspace, path = rope_contract_consumer
        source = f"class Owner:\n{destination}    class Helpers:\n{method}"
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        module = f"{path.parent.name}.{path.stem}"
        with pytest.raises(
            u.Infra.exception_type("rope.base.exceptions", "RefactoringError"),
            match=failure,
        ):
            u.Infra.plan_contract_rules(
                workspace,
                {path: source},
                (),
                options=m.Infra.ContractAdmissionOptions(
                    method_transfers=(
                        m.Infra.RopeMethodTransfer(
                            id="rejected-method-owner",
                            destination=(module, "Owner"),
                            methods=((module, "Owner.Helpers.build"),),
                        ),
                    )
                ),
            )
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    @staticmethod
    def test_different_module_binding_cannot_change_a_transferred_method(
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
    ) -> None:
        """A conflicting global must fail before either source is modified."""
        workspace, path = rope_contract_consumer
        target = path.with_name("destination.py")
        source = (
            "TOKEN = 'source'\n"
            "class Owner:\n"
            "    @staticmethod\n"
            "    def build(): return TOKEN\n"
        )
        destination = "TOKEN = 'destination'\nclass Target:\n    pass\n"
        sources = {path: source, target: destination}
        for file, content in sources.items():
            file.write_text(content, encoding=c.DEFAULT_ENCODING)
        module = path.parent.name
        with pytest.raises(
            u.Infra.exception_type("rope.base.exceptions", "RefactoringError"),
            match=r"conflicts|changes binding",
        ):
            u.Infra.plan_contract_rules(
                workspace,
                sources,
                (),
                options=m.Infra.ContractAdmissionOptions(
                    method_transfers=(
                        m.Infra.RopeMethodTransfer(
                            id="conflicting-global-owner",
                            destination=(f"{module}.{target.stem}", "Target"),
                            methods=((f"{module}.{path.stem}", "Owner.build"),),
                        ),
                    )
                ),
            )
        for file, content in sources.items():
            tm.that(file.read_text(encoding=c.DEFAULT_ENCODING), eq=content)
