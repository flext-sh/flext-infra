"""Reject dead governance skill paths and conflicting authority sequences.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import flext_infra
from flext_infra import config
from tests import c, tm, u


class TestsFlextInfraGovernanceAuthority:
    """Test suite for governance skill-path and authority-sequence integrity."""

    ROOT = Path(flext_infra.__file__).resolve().parents[2]

    def _common_dir(self) -> Path:
        return Path(
            tm.ok(
                u.Cli.capture(
                    ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
                    cwd=self.ROOT,
                ),
            ),
        )

    def _repository_root(self) -> Path:
        # When flext-infra is a submodule, the git common-dir resolves to the
        # superproject's <superproject>/.git/modules/<name> and --show-toplevel
        # returns the submodule checkout. Governance assets (docs/, AGENTS.md,
        # .agents/skills) live in the superproject, so resolve its root instead.
        common_dir = self._common_dir()
        super_modules = [
            p
            for p in common_dir.parents
            if p.name == "modules" and p.parent.name == c.GIT_DIR_NAME
        ]
        resolve_root = super_modules[0].parent.parent if super_modules else self.ROOT
        return Path(
            tm.ok(
                u.Cli.capture(
                    ["git", "rev-parse", "--path-format=absolute", "--show-toplevel"],
                    cwd=resolve_root,
                ),
            ),
        )

    def test_markdownlint_does_not_suppress_strict_rules(self) -> None:
        """Test markdownlint does not suppress strict rules."""
        markdown_config = u.Tests.json_payload(
            (self.ROOT / ".markdownlint.json").read_text(encoding="utf-8"),
        )
        tm.ok(markdown_config.get("MD012") is not False)
        tm.ok(markdown_config.get("MD050") is not False)
        tm.ok(markdown_config.get("MD064") is not False)
        tm.ok(markdown_config.get("MD075") is not False)
        line_length = u.Tests.toml_mapping(markdown_config["MD013"])["line_length"]
        tm.that(line_length, eq=u.Infra.docs_markdown_line_length(config.Infra.tooling))

    def test_markdown_projections_follow_the_same_typed_policy(self) -> None:
        """Generated JSON stays common while native tables preserve every override."""
        policy = u.Infra.load_tooling_inputs(self.ROOT).unwrap().document.tools.markdown
        common = u.Infra.configuration_pairs(policy.rules)
        overrides = u.Infra.configuration_pairs(policy.native_rules)
        compatible = u.Tests.json_payload(
            (self.ROOT / c.Infra.MARKDOWNLINT_CONFIG_FILENAME).read_text(
                encoding="utf-8"
            )
        )
        native = u.Tests.toml_payload(
            (self.ROOT / c.Infra.MARKDOWN_CONFIG_FILENAME).read_text(encoding="utf-8")
        )
        tm.that(compatible, eq=common)
        global_options = u.Tests.toml_mapping(native["global"])
        disabled = u.Tests.toml_strings(global_options["disable"])
        codegen = u.Infra.load_codegen_inputs(self.ROOT).unwrap().spec
        tm.that(global_options["exclude"], eq=list(codegen.markdown_exclude_globs))
        for name in overrides.keys() - common.keys():
            tm.that(name not in compatible, eq=True)
        elected = {**common, **overrides}
        for name, value in elected.items():
            if name == "default":
                continue
            if isinstance(value, bool):
                tm.that(name in disabled, eq=not value)
            else:
                expected = u.Tests.toml_mapping(value)
                if name in common and u.mapping(common[name]):
                    expected = {**u.Tests.toml_mapping(common[name]), **expected}
                tm.that(native[name], eq=expected)
        for name, options in policy.native_settings:
            for key, value in u.Tests.toml_mapping(options).items():
                tm.that(u.Tests.toml_mapping(native[name])[key], eq=value)

    def test_flext_law_requires_automated_structural_rewires(self) -> None:
        # Markdown reflows a clause across lines at whatever column the
        # formatter chooses, so a literal match answers about the wrap and not
        # about the law. Collapse runs of whitespace and assert the sentence
        # itself.
        """Test flext law requires automated structural rewires."""
        law = " ".join(
            (self._repository_root() / ".agents/skills/flext-law/SKILL.md")
            .read_text(encoding="utf-8")
            .split(),
        )

        for required in (
            "`make mod`",
            "`ast-grep` rewrites",
            "Rope semantic refactors",
            "GitHub and CRG belong to ai-hub",
            "never imports ai-hub or CRG as a library",
            "Repetitive manual call-site editing is prohibited",
        ):
            tm.that(law, has=required)
