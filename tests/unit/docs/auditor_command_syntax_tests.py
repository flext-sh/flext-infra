"""Behavior tests for documented command syntax accepted by the audit.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import pytest

from flext_infra import config
from tests import m, tm, u


class TestsFlextInfraAuditorCommandSyntax:
    """Prove which documented command forms the audit accepts or rejects."""

    @staticmethod
    @pytest.mark.parametrize("tool", ["uv", "mkdocs", "ruff", "pyright", "pre-commit"])
    def test_tool_filename_is_not_a_command(tool: str) -> None:
        """Filename prefixes remain prose; actual tool invocations are rejected."""
        for content, expected in (
            (f"Configuration is stored in `{tool}.toml`.", 0),
            (f"The documentation uses `{tool}`.", 0),
            (f"```bash\n{tool}\n```", 1),
            (f"```bash\n{tool} --help\n```", 1),
        ):
            issues = u.Infra.docs_command_contract_content_issues(
                content,
                relative_path="docs/guides/commands.md",
                effective_verbs=config.Infra.codegen.make.verbs,
            )
            tm.that(len(issues), eq=expected)

    @staticmethod
    def test_accepts_every_declared_verb_rendered_from_the_ssot() -> None:
        """Each declared verb passes without the exterminated apply token."""
        lines = "\n".join(
            f"make {spec.name}" for spec in config.Infra.codegen.make.verbs
        )
        content = f"# Commands\n\n```bash\n{lines}\n```\n"

        issues = u.Infra.docs_command_contract_content_issues(
            content,
            relative_path="docs/guides/testing.md",
            effective_verbs=config.Infra.codegen.make.verbs,
        )

        tm.that(issues, eq=[])

    @staticmethod
    def test_accepts_declared_named_inputs_from_each_verb() -> None:
        """The same typed verb declaration owns its documented named inputs."""
        verbs = config.Infra.codegen.make.verbs
        commands = "\n".join(
            f"make {verb.name} {argument}=tests/unit/consumer.py"
            for verb in verbs
            for argument in verb.arguments
        )
        issues = u.Infra.docs_command_contract_content_issues(
            f"```bash\n{commands}\n```\n",
            relative_path="docs/guides/testing.md",
            effective_verbs=verbs,
        )
        tm.that(issues, empty=True)

    @staticmethod
    def test_accepts_common_controls_from_the_make_contract() -> None:
        """Shared controls and the configured CI name belong to every verb."""
        policy = config.Infra.codegen.make
        commands = "\n".join(
            f"make {verb.name} {argument}=Y"
            for verb in policy.verbs
            for argument in (*policy.common_arguments, policy.ci.variable)
        )
        issues = u.Infra.docs_command_contract_content_issues(
            f"```bash\n{commands}\n```\n",
            relative_path="docs/guides/testing.md",
            effective_verbs=policy.verbs,
        )
        tm.that(issues, empty=True)

    @staticmethod
    def test_named_input_is_not_borrowed_from_another_verb() -> None:
        """A declared file input cannot authorize a different operation."""
        owner = m.Infra.MakeVerbSpec(
            name="with-input",
            description="An operation with a named file input.",
            arguments=("FILE",),
        )
        independent = m.Infra.MakeVerbSpec(
            name="without-input",
            description="An operation without a named file input.",
        )
        issues = u.Infra.docs_command_contract_content_issues(
            "```bash\nmake without-input FILE=tests/unit/consumer.py\n```\n",
            relative_path="docs/guides/testing.md",
            effective_verbs=(owner, independent),
        )
        tm.that(issues, len=1)
        tm.that(issues[0].message, has="invented Make selector `FILE`")

    @staticmethod
    def test_malformed_named_input_retains_the_shell_parse_failure() -> None:
        """An unterminated input never becomes an accepted documentation command."""
        verb = m.Infra.MakeVerbSpec(
            name="with-input",
            description="An operation with a named file input.",
            arguments=("FILE",),
        )
        with pytest.raises(ValueError, match="No closing quotation"):
            u.Infra.docs_command_contract_content_issues(
                "```bash\nmake with-input FILE='unterminated\n```\n",
                relative_path="docs/guides/testing.md",
                effective_verbs=(verb,),
            )

    @staticmethod
    @pytest.mark.parametrize("name", ["MATCH", "UNDECLARED_ARGUMENT"])
    def test_allowed_input_does_not_hide_a_later_forbidden_selector(name: str) -> None:
        """All documented assignments are checked after an accepted input."""
        verb = m.Infra.MakeVerbSpec(
            name="with-input",
            description="An operation with a named file input.",
            arguments=("FILE",),
        )
        issues = u.Infra.docs_command_contract_content_issues(
            f"```bash\nmake with-input FILE='tests/unit/my consumer.py' "
            f"{name}=unit\n```\n",
            relative_path="docs/guides/testing.md",
            effective_verbs=(verb,),
        )
        tm.that(issues, len=1)
        tm.that(issues[0].message, has=f"invented Make selector `{name}`")

    @staticmethod
    def test_ignores_prose_that_begins_with_make() -> None:
        """Test ignores prose that begins with make."""
        content = """# Scope

Make surfaces and documentation are changed at their canonical owner.
"""

        issues = u.Infra.docs_command_contract_content_issues(
            content,
            relative_path="docs/guides/make-commands.md",
            effective_verbs=config.Infra.codegen.make.verbs,
        )

        tm.that(issues, eq=[])

    @staticmethod
    def test_rejects_invented_make_selectors() -> None:
        """Test rejects invented make selectors."""
        content = """```bash
make test PROJECT=flext-demo MATCH=unit
```
"""

        issues = u.Infra.docs_command_contract_content_issues(
            content,
            relative_path="docs/guides/testing.md",
            effective_verbs=config.Infra.codegen.make.verbs,
        )

        tm.that(len(issues), eq=1)
        tm.that(issues[0].issue_type, eq="command_contract")
        tm.that(issues[0].message, has="invented Make selector")

    @staticmethod
    @pytest.mark.parametrize("value", ["Y", "N", "", "invalid"])
    def test_rejects_legacy_apply_flag_on_a_declared_verb(value: str) -> None:
        """The exterminated `APPLY` flag is rejected in documented commands."""
        verb = next(spec.name for spec in config.Infra.codegen.make.verbs)
        content = f"```bash\nmake {verb} APPLY={value}\n```\n"

        issues = u.Infra.docs_command_contract_content_issues(
            content,
            relative_path="docs/guides/getting-started.md",
            effective_verbs=config.Infra.codegen.make.verbs,
        )

        tm.that(len(issues), eq=1)
        tm.that(issues[0].message, has="legacy `APPLY` flag is exterminated")

    @staticmethod
    def test_accepts_plain_declared_verbs() -> None:
        """Every declared verb documented without variables passes."""
        plain = "\n".join(
            f"make {spec.name}" for spec in config.Infra.codegen.make.verbs
        )

        ok = u.Infra.docs_command_contract_content_issues(
            f"```bash\n{plain}\n```\n",
            relative_path="docs/guides/getting-started.md",
            effective_verbs=config.Infra.codegen.make.verbs,
        )
        tm.that(ok, eq=[])

        legacy = "\n".join(
            f"make {spec.name} APPLY=Y" for spec in config.Infra.codegen.make.verbs
        )
        bad = u.Infra.docs_command_contract_content_issues(
            f"```bash\n{legacy}\n```\n",
            relative_path="docs/guides/getting-started.md",
            effective_verbs=config.Infra.codegen.make.verbs,
        )
        tm.that(len(bad), eq=len(config.Infra.codegen.make.verbs))

    @staticmethod
    def test_rejects_raw_pytest_execution() -> None:
        """Test rejects raw pytest execution."""
        content = """```bash
PYTHONPATH=src python -m pytest tests/unit
```
"""

        issues = u.Infra.docs_command_contract_content_issues(
            content,
            relative_path="docs/guides/testing.md",
            effective_verbs=config.Infra.codegen.make.verbs,
        )

        tm.that(len(issues), eq=1)
        tm.that(issues[0].message, has="bypasses `make test`")

    @staticmethod
    def test_rejects_direct_tool_execution() -> None:
        """Test rejects direct tool execution."""
        content = """```bash
ruff check src
```
"""

        issues = u.Infra.docs_command_contract_content_issues(
            content,
            relative_path="docs/standards/development.md",
            effective_verbs=config.Infra.codegen.make.verbs,
        )

        tm.that(len(issues), eq=1)
        tm.that(issues[0].message, has="bypasses the root Make dispatcher")

    @staticmethod
    def test_inline_command_requires_an_execution_directive() -> None:
        """Describe a tool invocation without treating it as user guidance."""
        content = (
            "The fix pass runs `ruff check --fix` internally.\n"
            "Run `ruff check --fix` to invoke the tool directly.\n"
        )

        issues = u.Infra.docs_command_contract_content_issues(
            content,
            relative_path="docs/guides/commands.md",
            effective_verbs=config.Infra.codegen.make.verbs,
        )

        tm.that(len(issues), eq=1)
        tm.that(issues[0].message, has="line 2: direct tool command")

    @staticmethod
    def test_rejects_test_double_examples() -> None:
        """Test rejects test double examples."""
        content = """```python
from unittest.mock import patch

result = patch("package.owner")
```
"""

        issues = u.Infra.docs_command_contract_content_issues(
            content,
            relative_path="docs/standards/testing.md",
            effective_verbs=config.Infra.codegen.make.verbs,
        )

        tm.that(len(issues), eq=2)
        tm.that(issues[0].message, has="test-double code")
