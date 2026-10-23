"""Repository-bounded rule authentication through native scan and publication.

A rule's binding witnesses end at the repository being scanned: in-repo
drift rejects publication, while supplier and dependency sources are read
for inference and never authenticated, so their drift never blocks.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import c, codemod, m
from tests import tm, u


class TestsFlextInfraRuleBindingInputs:
    """Reject in-repo drift; never authenticate dependency or unrelated owners."""

    @staticmethod
    @pytest.mark.parametrize("changed", ["unrelated", "owner", "transitive"])
    def test_rejected_owner_does_not_authenticate_another_rewrite(
        mod_workspace: Path,
        tmp_path: Path,
        installed_dependency_path: Path,
        changed: str,
    ) -> None:
        """Only the in-repository owner authenticates the rewrite it admitted.

        The transitive base lives in an installed dependency outside the
        repository: it informs inference, is never a binding witness, and its
        drift publishes. A rejected candidate contributes no witness either.
        """
        owner = mod_workspace / "rewrite_owner.py"
        transitive = installed_dependency_path / "binding_base.py"
        unrelated = installed_dependency_path / "rejected_owner.py"
        transitive.write_text("class Base:\n    pass\n", encoding="utf-8")
        owner.write_text(
            "from binding_base import Base\nclass Value(Base):\n    pass\n",
            encoding="utf-8",
        )
        unrelated.write_text("class Value:\n    pass\n", encoding="utf-8")
        source = mod_workspace / "consumer.py"
        source.write_text(
            "from rewrite_owner import Value\n"
            "wrap = str\nunwrap = repr\nresult = wrap(Value)\n",
            encoding="utf-8",
        )
        rules_dir = tmp_path / "catalog" / c.Infra.CODEMOD_RULE_DIRS_KEY
        rules_dir.mkdir(parents=True)
        configuration = rules_dir.parent / c.Infra.CODEMOD_CONFIG_FILENAME
        tm.ok(
            u.Cli.yaml_dump(
                configuration,
                {c.Infra.CODEMOD_RULE_DIRS_KEY: [rules_dir.name]},
            )
        )
        for name in ("rewrite_owner", "rejected_owner"):
            tm.ok(
                u.Cli.yaml_dump(
                    rules_dir / f"{name}.yml",
                    {
                        "id": name,
                        "language": "Python",
                        "severity": "error",
                        "rule": {"pattern": "wrap($VALUE)"},
                        "fix": "unwrap($VALUE)",
                        "metadata": {
                            "context": {
                                "VALUE": {
                                    "is": "resolved-symbol",
                                    "arg": f"{name} Value",
                                }
                            }
                        },
                    },
                )
            )
        rules = tm.ok(u.Infra.codemod_catalog_rules("dependency-proof", configuration))
        plan = m.Infra.CodemodRulePlan(
            provider_order=("dependency-proof",),
            rules=tuple(rules),
            rulesets=(
                m.Infra.CodemodRuleset(
                    provider="dependency-proof",
                    config=configuration,
                    rule_ids=tuple(rule.id for rule in rules),
                    fixable_rule_ids=tuple(rule.id for rule in rules),
                ),
            ),
            project_rule_ids={
                mod_workspace.resolve(): tuple(rule.id for rule in rules)
            },
        )
        report = tm.ok(
            codemod.FlextInfraModGateEngine.scan(
                mod_workspace, fix=False, selection=plan, source_files=(source,)
            )
        )
        tm.that(tuple(entry.rule_id for entry in report.entries), eq=("rewrite_owner",))
        captured = {state.path for state in report.entries[0].binding_states}
        tm.that(owner in captured)
        tm.fail(transitive in captured)
        tm.fail(unrelated in captured)
        target = {
            "unrelated": unrelated,
            "owner": owner,
            "transitive": transitive,
        }[changed]
        before = source.read_bytes()
        target.write_text("changed = True\n", encoding="utf-8")
        published = codemod.FlextInfraModGateEngine.apply_report(
            mod_workspace, report, exact_replacements=True
        )
        if changed == "owner":
            tm.fail(published, has=str(target))
            tm.that(source.read_bytes(), eq=before)
        else:
            tm.ok(published)
            tm.that("unwrap(Value)" in source.read_text(encoding="utf-8"))
