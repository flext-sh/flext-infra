"""Public consumer contracts for lawful external declaration imports.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from flext_infra import codemod, infra
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraDeclarationImportConsumers:
    """Keep real external utility behavior, aliases and lexical shadows."""

    @staticmethod
    @pytest.mark.parametrize("entrypoint", ["value", "forwarded"])
    def test_ordinary_static_calls_do_not_elect_delegation_descriptors(
        tmp_path: Path,
        entrypoint: str,
    ) -> None:
        """A normal static return chain is not a descriptor argument contract."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "service.py"
        source = (
            "class Service:\n"
            "    @staticmethod\n"
            "    def value() -> str:\n"
            "        return str('before')\n"
            "    @staticmethod\n"
            "    def second() -> str:\n"
            "        return Service.value()\n"
            "    @staticmethod\n"
            "    def forwarded() -> str:\n"
            "        return Service.second()\n\n"
            "class Consumer:\n"
            f"    VALUE = Service.{entrypoint}()\n"
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        original = tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
        with infra.rope_workspace(root) as rope:
            tm.that(
                tm.ok(
                    u.Infra.plan_semantic_cutover(
                        c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                        rope_workspace=rope,
                        sources={path: source},
                    )
                ),
                empty=True,
            )
        tm.ok(u.Cli.atomic_verify_binary_file_states((original,)))

    @staticmethod
    @pytest.mark.parametrize("binding", ["Service", "c"])
    def test_constants_phase_elects_native_roles_without_inventing_facades(
        tmp_path: Path,
        binding: str,
    ) -> None:
        """Service-only imports are lawful; an unresolved declared c still fails."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        service = package / "service.py"
        service.write_text("class Service:\n    pass\n", encoding=c.DEFAULT_ENCODING)
        consumer = package / "consumer.py"
        source = (
            f"from {package.name}.service import Service\n"
            if binding == "Service"
            else f"from {package.name} import c as constants\n"
        )
        consumer.write_text(source, encoding=c.DEFAULT_ENCODING)
        sources = {
            service: service.read_text(encoding=c.DEFAULT_ENCODING),
            consumer: source,
        }
        with infra.rope_workspace(root) as rope:
            if binding == "c":
                with pytest.raises(
                    ValueError, match="unresolved constant import chain"
                ):
                    u.Infra.plan_semantic_cutover(
                        c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS,
                        rope_workspace=rope,
                        sources=sources,
                    )
            else:
                tm.that(
                    tm.ok(
                        u.Infra.plan_semantic_cutover(
                            c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS,
                            rope_workspace=rope,
                            sources=sources,
                        )
                    ),
                    empty=True,
                )
        tm.that(consumer.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
        tm.that((package / c.Infra.CONSTANTS_PY).exists(), eq=False)

    @staticmethod
    def test_explicit_external_source_owner_keeps_consumer_intact(
        tmp_path: Path,
    ) -> None:
        """A sibling consumer retains its manifest owner without becoming a producer."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        receiver, receiver_package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="explicit-receiver",
            package_name="explicit_receiver",
        )
        source = package / "service.py"
        consumer = receiver_package / "consumer.py"
        source.write_text("class Service:\n    pass\n", encoding=c.DEFAULT_ENCODING)
        consumer.write_text(
            f"from {package.name}.service import Service\n",
            encoding=c.DEFAULT_ENCODING,
        )
        seed = tm.ok(
            codemod.FlextInfraCodemodSemanticApply.build_source_plan(root, (receiver,))
        )
        sources = {
            path: path.read_text(encoding=c.DEFAULT_ENCODING)
            for path in (source, consumer)
        }
        with codemod.FlextInfraCodemodSemanticApply.planning_workspace(
            root, seed, sources
        ) as rope:
            tm.that(rope.repository_root, eq=root)
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                    rope_workspace=rope,
                    sources=sources,
                )
            )
            tm.that(edits, empty=True)
        tm.that(consumer.read_text(encoding=c.DEFAULT_ENCODING), eq=sources[consumer])

    @staticmethod
    @pytest.mark.parametrize(
        "declaration",
        [
            "from flext_cli import u as first, u as second\n",
            (
                "from flext_cli import u as first\n"
                "from flext_cli import u as second\n"
                "from flext_cli import u as first\n"
            ),
        ],
    )
    def test_external_aliases_preserve_the_real_public_consumer(
        tmp_path: Path,
        declaration: str,
    ) -> None:
        """Lawful external imports remain usable through public cutover planning."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = package / "_utilities"
        family.mkdir()
        path = family / "consumer.py"
        source = declaration + (
            "class Consumer:\n"
            "    @staticmethod\n"
            "    def digest() -> str:\n"
            "        '''Documented public operation.'''\n"
            "        return first.Cli.sha256_bytes(b'payload')\n"
            "def unrelated(first: str) -> str:\n"
            "    return first\n"
            "assert Consumer.digest() == second.Cli.sha256_bytes(b'payload')\n"
            "assert Consumer.digest() == "
            "__import__('hashlib').sha256(b'payload').hexdigest()\n"
            "assert Consumer.digest.__doc__ == 'Documented public operation.'\n"
            "assert unrelated('local') == 'local'\n"
        )
        path.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                    rope_workspace=rope,
                    sources={path: source},
                ),
            )
            proposed = {path: source}
            proposed.update({edit.file_path: edit.updated_source for edit in edits})
            tm.that(u.Infra.declaration_relocation_findings(rope, proposed), empty=True)
        path.write_text(proposed[path], encoding="utf-8")
        output = tm.ok(u.Cli.run_raw((sys.executable, "-I", str(path))))
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)
