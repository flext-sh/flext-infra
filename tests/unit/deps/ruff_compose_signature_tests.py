"""Canonical Ruff modernization retires suppression tables without narrowing rules.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra import c, config, m, t
from flext_infra.check.gate_registry import FlextInfraGateRegistry
from flext_infra.deps import FlextInfraEnsureRuffConfigPhase
from flext_infra.gates import FlextInfraRuffFormatGate, FlextInfraRuffLintGate
from tests import tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRuffProjectPolicy:
    """One native policy replaces both fresh and formerly suppressed inputs."""

    @staticmethod
    @pytest.mark.parametrize("missing_contract", ["check", "repair"])
    def test_delegation_rejects_a_missing_owner_election(missing_contract: str) -> None:
        """A declared owner cannot disappear from either canonical contract."""
        make = config.Infra.codegen.make
        owners = config.Infra.tooling.tools.ruff.lint.rule_owners
        for owner in set(owners.values()):
            checks = tuple(gate for gate in make.check_gates_default if gate != owner)
            repairs = tuple(
                gate
                for gate in (*make.check_gates_fixable, *make.fmt_gates)
                if gate != owner
            )
            with pytest.raises(ValueError, match="elected native check/repair owner"):
                FlextInfraGateRegistry.default().delegated_lint_rules(
                    owners,
                    check_gates=(
                        checks
                        if missing_contract == "check"
                        else make.check_gates_default
                    ),
                    repair_gates=(
                        repairs
                        if missing_contract == "repair"
                        else (*make.check_gates_fixable, *make.fmt_gates)
                    ),
                )

    @staticmethod
    def test_delegation_is_derived_from_arbitrary_declared_order() -> None:
        """Projection depends on the typed mapping, not an independent rule roster."""
        owners = config.Infra.tooling.tools.ruff.lint.rule_owners
        make = config.Infra.codegen.make
        reversed_owners = dict(reversed(tuple(owners.items())))
        tm.that(
            FlextInfraGateRegistry.default().delegated_lint_rules(
                reversed_owners,
                check_gates=make.check_gates_default,
                repair_gates=(*make.check_gates_fixable, *make.fmt_gates),
            ),
            eq=tuple(sorted(owners)),
        )

    @staticmethod
    def test_delegation_rejects_an_owner_without_native_file_repair() -> None:
        """Registration alone cannot turn a non-repairing checker into an owner."""
        registry = FlextInfraGateRegistry.default()
        for owner in c.Infra.ALLOWED_GATES:
            gate = registry.get(owner)
            if (
                owner == c.Infra.LINT
                or owner not in c.Infra.CANONICAL_FILE_GATE_IDS
                or gate is None
                or not gate.can_fix
            ):
                with pytest.raises(
                    ValueError, match="elected native check/repair owner"
                ):
                    registry.delegated_lint_rules(
                        {"unused-import": owner},
                        check_gates=c.Infra.CANONICAL_GATE_IDS,
                        repair_gates=c.Infra.CANONICAL_GATE_IDS,
                    )

    @staticmethod
    @pytest.mark.parametrize("delegate", [False, True])
    def test_modernization_uses_the_supplied_validated_owner_policy(
        tmp_path: Path,
        *,
        delegate: bool,
    ) -> None:
        """Changing explicit policy changes only delegation, never rule selection."""
        tooling = config.Infra.tooling
        declared = tooling.tools.ruff.lint
        lint_payload = declared.model_dump(
            mode="json",
            by_alias=True,
            exclude_computed_fields=True,
        )
        owners = dict(declared.rule_owners) if delegate else {}
        lint_payload["rule-owners"] = owners
        lint = m.Infra.RuffLintConfig.model_validate_json(
            tm.ok(u.Cli.json_dumps(lint_payload)),
        )
        policy = tooling.model_copy(
            update={
                "tools": tooling.tools.model_copy(
                    update={
                        "ruff": tooling.tools.ruff.model_copy(update={"lint": lint}),
                    }
                ),
            }
        )
        payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(
            u.Tests.toml_payload('[project]\nname = "changed-owner-policy"\n'),
        )
        phase = FlextInfraEnsureRuffConfigPhase(policy)
        phase.apply_payload(
            payload,
            path=tmp_path / c.PYPROJECT_FILENAME,
            analysis_exclusions=(),
        )
        actual = tm.not_none(u.Cli.toml_mapping_path(payload, ("tool", "ruff", "lint")))
        tm.that(actual["ignore"], eq=sorted(owners))
        tm.that(actual["select"], eq=sorted(lint.select))
        tm.that(actual["unfixable"], eq=sorted(lint.unfixable))
        tm.that(
            phase.apply_payload(
                payload,
                path=tmp_path / c.PYPROJECT_FILENAME,
                analysis_exclusions=(),
            ),
            empty=True,
        )

    @staticmethod
    def test_modernization_retires_all_rule_suppression_tables(tmp_path: Path) -> None:
        """Retirement preserves full declared rules and converges without exemptions."""
        payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(
            u.Tests.toml_payload(
                '[project]\nname = "retired-exemptions"\n'
                '[tool.ruff.lint]\nignore = ["F401"]\nextend-ignore = ["F821"]\n'
                '[tool.ruff.lint.per-file-ignores]\n"tests/**" = ["ALL"]\n'
                '[tool.ruff.lint.extend-per-file-ignores]\n"scripts/**" = ["ALL"]\n',
            ),
        )
        phase = FlextInfraEnsureRuffConfigPhase(config.Infra.tooling)
        phase.apply_payload(
            payload,
            path=tmp_path / c.PYPROJECT_FILENAME,
            analysis_exclusions=(),
        )
        lint = tm.not_none(u.Cli.toml_mapping_path(payload, ("tool", "ruff", "lint")))
        for retired in (
            "extend-ignore",
            "per-file-ignores",
            "extend-per-file-ignores",
        ):
            tm.that(lint, lacks=retired)
        tm.that(
            lint["ignore"], eq=sorted(config.Infra.tooling.tools.ruff.lint.rule_owners)
        )
        tm.that(lint["select"], eq=sorted(config.Infra.tooling.tools.ruff.lint.select))
        tm.that(
            phase.apply_payload(
                payload,
                path=tmp_path / c.PYPROJECT_FILENAME,
                analysis_exclusions=(),
            ),
            empty=True,
        )

    @staticmethod
    @pytest.mark.parametrize("surface", config.Infra.tooling.tools.ruff.src)
    def test_native_selected_scope_has_no_hidden_findings(
        tmp_path: Path,
        surface: str,
    ) -> None:
        """The native owner sees formerly masked findings on every code root."""
        project = u.Tests.mk_project(tmp_path, "native-policy")
        selected = project / surface / "selected.py"
        selected.parent.mkdir(parents=True, exist_ok=True)
        selected.write_text("import os\n", encoding="utf-8")
        payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(
            u.Tests.toml_payload(
                (project / c.PYPROJECT_FILENAME).read_text(encoding="utf-8"),
            ),
        )
        FlextInfraEnsureRuffConfigPhase(config.Infra.tooling).apply_payload(
            payload,
            path=project / c.PYPROJECT_FILENAME,
            analysis_exclusions=(),
        )
        (project / c.PYPROJECT_FILENAME).write_text(
            u.Cli.toml_dumps(u.Cli.toml_document_from_mapping(payload)),
            encoding="utf-8",
        )
        gate = FlextInfraRuffLintGate(tmp_path)
        context = m.Infra.GateContext(
            repository_root=tmp_path,
            reports_dir=tmp_path / "reports",
        )
        execution = gate.check_files((selected,), project, context)
        tm.that(execution.result.passed, eq=False)
        tm.that(execution.outcome, eq=c.Infra.ToolOutcome.FINDINGS)
        tm.that([issue.code for issue in execution.issues], has="unused-import")
        tm.that(
            all(
                issue.severity == c.Infra.GateSeverity.ERROR.value
                for issue in execution.issues
            ),
            eq=True,
        )
        tm.that(selected.read_text(encoding="utf-8"), eq="import os\n")

    @staticmethod
    def test_native_lint_and_format_owners_reach_a_checked_fixed_point(
        tmp_path: Path,
    ) -> None:
        """Layout is still checked by its owner and unrelated findings still fail."""
        project = u.Tests.mk_project(
            tmp_path,
            "paired-native-policy",
            pyproject=(
                "[project]\n"
                'name = "paired-native-policy"\n'
                'version = "0.0.0"\n'
                "authors = [{ name = 'Test Holder' }]\n"
                "license = 'MIT'\n"
            ),
        )
        package = project / "pkg"
        package.mkdir()
        (package / "__init__.py").write_text("", encoding="utf-8")
        source = package / "values.py"
        source.write_text(
            '"""Values."""\n\nVALUES = [\n    0,\n    1\n]\n', encoding="utf-8"
        )
        payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(
            u.Tests.toml_payload(
                (project / c.PYPROJECT_FILENAME).read_text(encoding="utf-8"),
            ),
        )
        FlextInfraEnsureRuffConfigPhase(config.Infra.tooling).apply_payload(
            payload,
            path=project / c.PYPROJECT_FILENAME,
            analysis_exclusions=(),
        )
        (project / c.PYPROJECT_FILENAME).write_text(
            u.Cli.toml_dumps(u.Cli.toml_document_from_mapping(payload)),
            encoding="utf-8",
        )
        context = m.Infra.GateContext(
            repository_root=tmp_path,
            reports_dir=tmp_path / "reports",
            apply_fixes=True,
            selected_files=(source,),
        )
        lint = FlextInfraRuffLintGate(tmp_path)
        formatter = FlextInfraRuffFormatGate(tmp_path)
        before = formatter.check_files((source,), project, context)
        tm.that(before.result.passed, eq=False)
        tm.that(before.outcome, eq=c.Infra.ToolOutcome.FINDINGS)
        tm.that(lint.fix(project, context).result.passed, eq=True)
        tm.that(formatter.fix(project, context).result.passed, eq=True)
        stable = source.read_text(encoding="utf-8")
        for gate in (lint, formatter):
            tm.that(
                gate.check_files((source,), project, context).result.passed, eq=True
            )
            tm.that(gate.fix(project, context).result.passed, eq=True)
        tm.that(source.read_text(encoding="utf-8"), eq=stable)
        source.write_text(stable + "\nUNRESOLVED = missing_name\n", encoding="utf-8")
        unresolved = lint.check_files((source,), project, context)
        tm.that(unresolved.result.passed, eq=False)
        tm.that([issue.code for issue in unresolved.issues], has="undefined-name")
