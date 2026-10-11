"""Fixed-point validation for staged ast-grep rule cascades.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from flext_infra import c, infra, m, main
from flext_infra.check import FlextInfraWorkspaceChecker
from flext_infra.codemod import (
    FlextInfraApplyRenames,
    FlextInfraCodemodBatchApply,
    FlextInfraCodemodSemanticApply,
    FlextInfraModGateEngine,
)
from tests import tm, u


class TestsFlextInfraCodemodBatchApplyValidation:
    """Keep staged rules distinct from a rewrite that recreates its own finding."""

    class RuntimeProgress:
        """Execute the real consumer at the first post-syntax public phase."""

        def __init__(self, sample: Path) -> None:
            """Bind the consumer whose imports must already converge."""
            self.sample = sample
            self.validated = False

        def emit(self, message: str) -> None:
            """Validate before either consumer text rewrites or the census run."""
            if message == "mod: apply declared consumer text cutovers":
                tm.ok(u.Cli.run((sys.executable, str(self.sample))))
                self.validated = True

        def emit_rename(self, report: m.Infra.ApplyRenamesReport) -> None:
            """Accept the public campaign progress contract."""
            _ = report

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize(
        ("entry", "broken"),
        [("census", True), ("pipeline", False), ("noop", False)],
    )
    def test_census_publishes_joint_factory_and_constants_candidate(
        tmp_path: Path,
        entry: str,
        broken: bool,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Real census gates see both cutovers and retain unrelated failures."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.provision_checkout(root)
        notice = u.Infra.copyright_notice(root)
        family = u.Infra.facade_family_declared_by(c.Infra.CONSTANTS_PY)
        owner = f"{u.derive_class_stem(root.name)}{family.suffix}"
        parts = package / "_constants"
        tm.ok(u.Cli.ensure_dir(parts))
        consumer = package / "consumer.py"
        sources = {
            parts / c.Infra.INIT_PY: (
                f'"""Candidate constant family.\n\n{notice}\n"""\n\n'
                "from __future__ import annotations\n"
            ),
            parts / "base.py": (
                f'"""Candidate constant declaration.\n\n{notice}\n"""\n\n'
                "from __future__ import annotations\n\n"
                "from typing import ClassVar\n\n\n"
                f"class {owner}Base:\n"
                '    """Own the fixture protocol value."""\n\n'
                '    JOINT_VALUE: ClassVar[str] = "joint-candidate"\n\n\n'
                f'__all__ = ["{owner}Base"]\n'
            ),
            package / c.Infra.CONSTANTS_PY: (
                f'"""Candidate constants.\n\n{notice}\n"""\n\n'
                "from __future__ import annotations\n\n"
                f"from ._constants.base import {owner}Base\n\n\n"
                f"class {owner}({owner}Base):\n"
                '    """Inherit the public constant contract."""\n\n\n'
                f"c = {owner}\n"
                f'__all__ = ["{owner}", "c"]\n'
            ),
            package / c.Infra.INIT_PY: (
                f'"""Candidate public facade.\n\n{notice}\n"""\n\n'
                "from __future__ import annotations\n\n"
                "from .constants import c\n\n"
                '__all__ = ["c"]\n'
            ),
            consumer: (
                (
                    f'"""Real joint cutover consumer.\n\n{notice}\n"""\n\n'
                    "from __future__ import annotations\n\n"
                    "from flext_core import t\n"
                    f"from {package.name} import c\n\n"
                    f"from {package.name}._constants.base import "
                    f"{owner}Base as upstream_c\n"
                    "value = t.scalar_mapping_adapter().validate_python("
                    "{'name': 'value'})\n"
                    "constant = upstream_c.JOINT_VALUE\n"
                    "local = c.JOINT_VALUE\n"
                )
                + ("broken: str = 1\n" if broken else "")
            ),
        }
        for path, source in sources.items():
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        if entry == "pipeline":
            tm.fail(
                FlextInfraWorkspaceChecker(repository_root=root).execute_payload(
                    m.Infra.RunCommand(
                        repository_root=root,
                        projects=(".",),
                        gates=(c.Infra.LINT, c.Infra.PYREFLY, c.Infra.FRESH_IMPORT),
                    ),
                ),
                has="quality",
            )
            before = capsys.readouterr().out
            tm.that(before, has=f"[FAIL] {c.Infra.PYREFLY}")
            tm.that(before, has="scalar_mapping_adapter")
            for path, source in sources.items():
                tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
            tm.that(
                main(["refactor", "mod", "--repository-root", str(root), "--apply"]),
                eq=0,
            )
        else:
            with infra.rope_workspace(root) as rope:
                result = FlextInfraCodemodSemanticApply.census_constants(
                    root,
                    rope,
                    apply=True,
                )
            if broken:
                tm.fail(result, has="quality")
            else:
                tm.ok(result)
        console = capsys.readouterr().out
        for gate in (c.Infra.LINT, c.Infra.PYREFLY, c.Infra.FRESH_IMPORT):
            verdict = "FAIL" if broken and gate == c.Infra.PYREFLY else "OK"
            tm.that(console, has=f"[{verdict}] {gate}")
        if broken:
            tm.that(console, has="bad-assignment")
            for path, source in sources.items():
                tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
        else:
            published = consumer.read_text(encoding=c.DEFAULT_ENCODING)
            tm.that(published, has="u.scalar_mapping_adapter()")
            tm.that(published, has="constant = c.JOINT_VALUE")
            output = tm.ok(
                u.Cli.run_raw(
                    (
                        sys.executable,
                        "-I",
                        "-c",
                        (
                            "import sys; sys.path.insert(0, sys.argv[1]); "
                            "from flext_test_project.consumer import "
                            "value, constant, local; "
                            "assert value == {'name': 'value'}; "
                            "assert constant == local"
                        ),
                        str(package.parent),
                    ),
                ),
            )
            tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)
        if entry == "noop":
            published = consumer.read_text(encoding=c.DEFAULT_ENCODING)
            with infra.rope_workspace(root) as rope:
                tm.ok(
                    FlextInfraCodemodSemanticApply.census_constants(
                        root,
                        rope,
                        apply=True,
                    ),
                )
            tm.that(consumer.read_text(encoding=c.DEFAULT_ENCODING), eq=published)
            invalid = published + "broken: str = 1\n"
            tm.ok(u.Cli.atomic_write_text_file(consumer, invalid))
            with infra.rope_workspace(root) as rope:
                tm.fail(
                    FlextInfraCodemodSemanticApply.census_constants(
                        root,
                        rope,
                        apply=True,
                    ),
                    has="quality",
                )
            tm.that(consumer.read_text(encoding=c.DEFAULT_ENCODING), eq=invalid)
            tm.that(capsys.readouterr().out, has=f"[FAIL] {c.Infra.PYREFLY}")

    @pytest.mark.slow
    @pytest.mark.parametrize(
        "contract",
        ["t.JsonMapping", "Annotated[t.JsonMapping, None]"],
    )
    def test_typeform_syntax_cascade_converges_before_consumer_publication(
        self,
        mod_workspace: Path,
        contract: str,
    ) -> None:
        """The native pipeline supplies companion imports before leaving syntax."""
        u.Tests.provision_checkout(mod_workspace)
        sample = mod_workspace / "sample.py"
        tm.ok(
            u.Cli.atomic_write_text_file(
                sample,
                '"""Adapter runtime contract."""\n'
                "from __future__ import annotations\n\n"
                "from typing import Annotated\n"
                "from pydantic import TypeAdapter\n"
                "from flext_core import t\n\n"
                f"adapter = TypeAdapter({contract})\n"
                'assert adapter.validate_python({"name": "value"}) '
                '== {"name": "value"}\n',
            ),
        )
        before = tm.ok(FlextInfraModGateEngine.scan(mod_workspace, fix=False))
        tm.that(
            any(
                item.rule_id.startswith("pydantic-adapter-typeform")
                for item in before.entries
            ),
            eq=True,
        )
        tm.that(
            any(item.rule_id == "pydantic-typeform-import" for item in before.entries),
            eq=False,
        )
        progress = self.RuntimeProgress(sample)
        with infra.rope_workspace(mod_workspace) as rope:
            service = FlextInfraCodemodBatchApply(
                repository_root=mod_workspace,
                apply_changes=True,
                rename_runner=FlextInfraApplyRenames(),
                progress=progress,
                rope=rope,
            )
            tm.ok(service.execute())
            first = sample.read_bytes()
            tm.that(progress.validated, eq=True)
            after = tm.ok(FlextInfraModGateEngine.scan(mod_workspace, fix=False))
            tm.that(after.actionable, eq=0)
            tm.ok(service.execute())
            tm.that(sample.read_bytes(), eq=first)

    @staticmethod
    def _report(path: Path, rule_id: str) -> m.Infra.ModScanReport:
        """Build one actionable ast-grep finding report.

        Returns:
            The resulting ``m.Infra.ModScanReport``.

        """
        finding = m.Infra.ModScanFinding(
            rule_file="fixture.yml",
            rule_id=rule_id,
            repository="fixture",
            file=path,
            source_owner="authored",
            source_state=None,
            range={},
            text="before",
            replacement="after",
            actionable=True,
            classification=c.Infra.ModScanFindingClass.ACTIONABLE,
            payload={},
        )
        return m.Infra.ModScanReport(
            findings=1,
            actionable=1,
            detection_only=0,
            non_actionable_with_fix=0,
            files=frozenset({path}),
            entries=(finding,),
        )

    def test_allows_a_later_rule_enabled_by_a_prior_rewrite(
        self,
        tmp_path: Path,
    ) -> None:
        """A staged rule becomes work for the next fixed-point iteration."""
        before = self._report(tmp_path / "subject.py", "bind-test-utility-alias")
        after = self._report(tmp_path / "subject.py", "rewire-test-utility-receiver")

        FlextInfraCodemodBatchApply.validate_fix_match(before, after)

    def test_rejects_a_rewrite_that_introduces_its_own_rule_again(
        self,
        tmp_path: Path,
    ) -> None:
        """A still-active rule proves that its own fix did not converge."""
        before = self._report(tmp_path / "subject.py", "rewrite-test-utility-receiver")
        after = self._report(tmp_path / "other.py", "rewrite-test-utility-receiver")

        with pytest.raises(RuntimeError, match="introduced 1 new actionable"):
            FlextInfraCodemodBatchApply.validate_fix_match(before, after)
