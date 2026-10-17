"""Verify lexical capture admission for valid multiline Python expressions.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests import c, m, tm, u

if TYPE_CHECKING:
    from pathlib import Path

    from tests import p


class TestsFlextInfraMultilineBindingCapture:
    """A captured expression retains its source grammar and ownership verdict."""

    @staticmethod
    @pytest.mark.parametrize("require_binding", [False, True])
    def test_native_multiline_receiver(
        mod_workspace: Path,
        binding_probe_rule: m.Infra.CodemodRule,
        native_consumer: p.Tests.NativeConsumer,
        *,
        require_binding: bool,
    ) -> None:
        """Real Python execution and native admission agree on the capture."""
        consumer = mod_workspace / "consumer.py"
        capture = 'f"old"\n    f"-tail".replace'
        source = f'value = (\n    {capture}("old", "native")\n)\n'
        consumer.write_text(source, encoding=c.DEFAULT_ENCODING)
        native_consumer(
            "from runpy import run_path\n"
            f"observed = run_path({str(consumer)!r})\n"
            "assert observed['value'] == 'native-tail'\n",
            cwd=mod_workspace,
        )
        rule = binding_probe_rule.model_copy(
            update={
                "context": (
                    m.Infra.CodemodContextCondition(
                        variable="OWNER",
                        predicate=(
                            c.Infra.CodemodContextPredicate.SAME_BINDING
                            if require_binding
                            else c.Infra.CodemodContextPredicate.EXECUTABLE_OCCURRENCE
                        ),
                        arg=("str.replace",) if require_binding else (),
                        holds=True,
                    ),
                ),
            },
        )
        snapshot = u.Infra.codemod_binding_snapshot(
            mod_workspace,
            (tm.ok(u.Cli.atomic_read_binary_file_state(consumer, required=True)),),
        )
        start = source.encode(c.DEFAULT_ENCODING).index(
            capture.encode(c.DEFAULT_ENCODING),
        )
        with u.Infra.codemod_binding_project(
            mod_workspace, u.Infra.codemod_source_epoch(snapshot)
        ) as (project, sources):
            tm.that(
                u.Infra.codemod_context_admits(
                    m.Infra.CodemodAdmission(
                        root=mod_workspace,
                        rule=rule,
                        file_path=consumer,
                        captures={
                            "OWNER": {
                                "text": capture,
                                "range": {
                                    "byteOffset": {
                                        "start": start,
                                        "end": start
                                        + len(capture.encode(c.DEFAULT_ENCODING)),
                                    }
                                },
                            }
                        },
                        facts=u.Infra.codemod_project_facts(mod_workspace, (rule,)),
                        snapshot=snapshot,
                    ),
                    project=project,
                    sources=sources,
                ),
                eq=not require_binding,
            )
