"""Public consumer contracts for lawful external declaration imports.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from flext_infra import infra
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraDeclarationImportConsumers:
    """Keep real external utility behavior, aliases and lexical shadows."""

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
