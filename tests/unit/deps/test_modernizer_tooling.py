"""Tooling phase tests for deps modernizer.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

import pytest

from flext_infra import config
from flext_infra.check import FlextInfraGateRegistry
from flext_infra.deps import FlextInfraEnsureRuffConfigPhase
from tests import m, t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraDepsModernizerTooling:
    """Declarative tests for the Ruff phase and analyzer surface policy."""

    @staticmethod
    def _yaml_settings_payload(
        document: m.Infra.ToolConfigDocument,
    ) -> dict[str, t.JsonPayload]:
        """Recreate YAML settings lists while retaining unrelated validated fields.

        Returns:
            A document payload exercising only the native settings ingress.

        """
        return {
            "settings": {
                table: [[key, value] for key, value in pairs]
                for table, pairs in document.settings.items()
            },
            "derived-tool-roots": document.derived_tool_roots,
            "derived-settings": document.derived_settings,
            "raw-check-receipt-suffix": document.raw_check_receipt_suffix,
            "tools": document.tools,
            "lazy-init": document.lazy_init,
            "mod": document.mod,
        }

    @staticmethod
    def test_native_settings_yaml_pairs_validate_as_tuples(
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """YAML-shaped lists become tuples without changing native option values."""
        payload = TestsFlextInfraDepsModernizerTooling._yaml_settings_payload(
            tool_config_document,
        )
        validated = m.Infra.ToolConfigDocument.model_validate(payload)
        tm.that(validated.settings, eq=tool_config_document.settings)
        for pairs in validated.settings.values():
            tm.that(type(pairs), eq=tuple)
            for pair in pairs:
                tm.that(type(pair), eq=tuple)

    @staticmethod
    @pytest.mark.parametrize(
        "pair",
        [[], ["option"], ["option", True, False], [1, True], ["", True], "ab"],
    )
    def test_native_settings_reject_invalid_pair_shapes(
        tool_config_document: m.Infra.ToolConfigDocument,
        pair: t.JsonValue,
    ) -> None:
        """Sequence normalization never repairs malformed native declarations."""
        payload = TestsFlextInfraDepsModernizerTooling._yaml_settings_payload(
            tool_config_document,
        )
        payload["settings"] = {"invalid_table": [pair]}
        with pytest.raises(m.ValidationError, match=r"settings\.invalid_table"):
            _ = m.Infra.ToolConfigDocument.model_validate(payload)

    @staticmethod
    def test_native_tool_configurations_round_trip_without_mutating_policy(
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """Every configured root remains valid native TOML with detached values."""
        original = deepcopy(tool_config_document.settings)
        roots = {table.partition(".")[0] for table in original}
        for root in sorted(roots):
            native = u.Infra.native_tool_configuration(tool_config_document, root)
            rendered = u.Cli.toml_dumps(u.Cli.toml_document_from_mapping(native))
            tm.that(u.Tests.toml_payload(rendered), eq=native)
            mutable_options: list[t.MutableJsonMapping] = []
            for table, entries in original.items():
                owner, separator, nested = table.partition(".")
                if owner != root:
                    continue
                observed = u.Cli.toml_mapping_ensure_path(
                    native, nested.split(".") if separator else ()
                )
                for key, value in u.Infra.configuration_pairs(entries).items():
                    tm.that(observed[key], eq=value)
                    if u.mapping(observed[key]):
                        mutable_options.append(
                            u.Cli.toml_mapping_ensure_table(observed, key)
                        )
            for option in mutable_options:
                option.clear()
        tm.that(tool_config_document.settings, eq=original)

    @staticmethod
    def test_native_tool_configuration_rejects_an_undeclared_root(
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """An unavailable native root cannot become an empty successful policy."""
        roots = {table.partition(".")[0] for table in tool_config_document.settings}
        missing = "undeclared_tool"
        while missing in roots:
            missing = f"_{missing}"
        with pytest.raises(KeyError) as rejected:
            u.Infra.native_tool_configuration(tool_config_document, missing)
        tm.that(rejected.value.args, eq=(missing,))

    @staticmethod
    def _applied(
        tool_config_document: m.Infra.ToolConfigDocument,
        project_dir: Path,
        source: str = "",
    ) -> t.Pair[t.MutableJsonMapping, t.JsonMapping]:
        """Apply the Ruff phase twice to one named payload; return payload and ruff.

        Returns:
            The resulting ``t.Pair[t.MutableJsonMapping, t.JsonMapping]``.

        """
        payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(
            u.Tests.toml_payload(f'[project]\nname = "{project_dir.name}"\n{source}'),
        )
        phase = FlextInfraEnsureRuffConfigPhase(
            tool_config_document,
        )
        path = project_dir / "pyproject.toml"
        _ = phase.apply_payload(payload, path=path)
        tm.that(phase.apply_payload(payload, path=path), empty=True)
        return payload, u.Tests.toml_mapping(
            u.Tests.toml_mapping(payload["tool"])["ruff"],
        )

    @staticmethod
    def test_typecheck_policy_keeps_tracked_surfaces_visible(
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """Keep every tracked Python surface visible to all four analyzers."""
        tools = tool_config_document.tools
        tracked_surfaces = frozenset({"examples", "scripts", "src", "tests"})
        hidden_globs = frozenset({
            "**/examples",
            "**/examples/**",
            "**/tests",
            "**/tests/**",
        })

        tm.that(
            frozenset(
                u.Infra.native_tool_setting(
                    tool_config_document, "ruff", "src", list[str]
                )
            ),
            eq=tracked_surfaces,
        )
        tm.that(
            frozenset(
                u.Infra.native_tool_setting(
                    tool_config_document, "ruff", "namespace-packages", list[str]
                )
            ),
            eq=frozenset({"examples", "scripts", "tests"}),
        )
        tm.that(frozenset(tools.pyright.path_rules.env_dirs), eq=tracked_surfaces)
        tm.that(
            hidden_globs.isdisjoint(tools.pyright.path_rules.default_excludes),
            eq=True,
        )
        tm.that(frozenset(tools.pyrefly.path_rules.env_dirs), eq=tracked_surfaces)
        tm.that(
            hidden_globs.isdisjoint(
                u.Infra.native_tool_setting(
                    tool_config_document,
                    "pyrefly",
                    "project-excludes",
                    t.StrSequence,
                )
            ),
            eq=True,
        )

    def test_ruff_phase_sets_expected_state(
        self,
        tmp_path: Path,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """Render Ruff policy, drop stale sections, and converge on second apply."""
        ruff_policy = tool_config_document.tools.ruff
        project_dir = tmp_path / "flext-sample"
        (project_dir / "src" / "flext_sample").mkdir(parents=True)
        (project_dir / "src" / "flext_sample" / "__init__.py").write_text(
            "",
            encoding="utf-8",
        )
        stale_pattern = "stale-pattern.py"

        payload, ruff = self._applied(
            tool_config_document,
            project_dir,
            '[lint]\nselect = ["E501"]\n'
            '[tool.ruff.lint.pylint]\nallow-dunder-method-names = ["__basse__"]\n'
            f'[tool.ruff.lint.per-file-ignores]\n"{stale_pattern}" = ["E402"]\n',
        )

        tm.that(payload, lacks="lint")
        # Shared artifact exclusions remain declared independently of workspace
        # topology; Ruff keeps its own native defaults alongside them.
        tm.that(
            ruff["extend-exclude"],
            eq=sorted(
                u.Infra.native_tool_setting(
                    tool_config_document, "ruff", "extend-exclude", list[str]
                )
            ),
        )
        tm.that(ruff, lacks="exclude")
        tm.that(
            ruff["line-length"],
            eq=u.Infra.native_tool_setting(
                tool_config_document, "ruff", "line-length", int
            ),
        )
        tm.that(
            ruff["target-version"],
            eq="py" + config.Infra.codegen.toolchain.python_version.replace(".", ""),
        )
        # The declared src list stays the SSOT; the projection filters it to
        # roots that exist (a retired tree must not name analyzer entries),
        # with roots the active plan is materializing accepted as present.
        tm.that(
            frozenset(u.Tests.toml_strings(ruff["src"])),
            eq=frozenset(
                root
                for root in u.Infra.native_tool_setting(
                    tool_config_document, "ruff", "src", list[str]
                )
                if (project_dir / root).is_dir()
            ),
        )
        tm.that(
            u.Tests.toml_mapping(ruff["format"])["docstring-code-format"],
            eq=u.Infra.native_tool_setting(
                tool_config_document, "ruff.format", "docstring-code-format", bool
            ),
        )
        lint = u.Tests.toml_mapping(ruff["lint"])
        tm.that(
            list(
                u.Tests.toml_strings(
                    u.Tests.toml_mapping(lint["pylint"])["allow-dunder-method-names"],
                ),
            ),
            eq=u.Infra.native_tool_setting(
                config.Infra.tooling,
                "ruff.lint.pylint",
                "allow-dunder-method-names",
                list[str],
            ),
        )
        tm.that(
            list(u.Tests.toml_strings(lint["unfixable"])),
            eq=u.Infra.native_tool_setting(
                config.Infra.tooling, "ruff.lint", "unfixable", list[str]
            ),
        )
        tm.that(
            list(u.Tests.toml_strings(lint["extend-safe-fixes"])),
            eq=u.Infra.native_tool_setting(
                config.Infra.tooling, "ruff.lint", "extend-safe-fixes", list[str]
            ),
        )
        delegated = FlextInfraGateRegistry.default().delegated_lint_rules(
            ruff_policy.lint.rule_owners,
            check_gates=config.Infra.codegen.make.check_gates_default,
            repair_gates=(
                *config.Infra.codegen.make.check_gates_fixable,
                *config.Infra.codegen.make.fmt_gates,
            ),
        )
        tm.that(
            lint["ignore"],
            eq=sorted({
                *delegated,
                *ruff_policy.lint.ruling_disabled_rules,
                *u.Infra.native_tool_setting(
                    tool_config_document, "ruff.lint", "ignore", t.StrSequence
                ),
            }),
        )
        tm.that(
            list(
                u.Tests.toml_strings(
                    u.Tests.toml_mapping(lint["isort"])["known-first-party"],
                ),
            ),
            eq=sorted({
                "flext_sample",
            }),
        )
        tm.that(lint, lacks="per-file-ignores")

    @staticmethod
    def test_project_cannot_declare_its_own_ruff_exemption(
        tmp_path: Path,
    ) -> None:
        """A project cannot reintroduce retired exemption configuration."""
        project_dir = tmp_path / "flext-sample"
        config_dir = project_dir / "config"
        config_dir.mkdir(parents=True)
        (config_dir / "sample.yaml").write_text(
            "ManagedArtifacts:\n"
            "  Ruff:\n"
            "    per_file_ignores:\n"
            "      src/flext_sample/_config.py: [N802]\n",
            encoding="utf-8",
        )

        tm.fail(u.Infra.load_project_managed_artifacts(project_dir), has="Ruff")

    def test_ruff_phase_skips_nonmember_workspace_namespaces(
        self,
        tmp_path: Path,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """Exclude nonmember consumer namespaces from FLEXT first-party names."""
        repository_root = tmp_path / "workspace"
        project_dir = repository_root / "demo-migration-tool"
        _ = u.Tests.WorktreeFixture.governed_workspace_with_member(
            repository_root,
            workspace="workspace",
            member="flext-core",
        )
        (project_dir / "src" / "demo_migration_tool").mkdir(parents=True)
        (project_dir / "src" / "demo_migration_tool" / "__init__.py").write_text(
            "",
            encoding="utf-8",
        )
        (project_dir / "pyproject.toml").write_text(
            '[project]\nname = "demo-migration-tool"\nversion = "0.1.0"\n'
            'dependencies = ["flext-core>=0.1.0"]\n',
            encoding="utf-8",
        )
        _, ruff = self._applied(
            tool_config_document,
            repository_root,
            'dependencies = ["flext-core>=0.1.0"]\n',
        )

        known_first_party = u.Tests.toml_strings(
            u.Tests.toml_mapping(u.Tests.toml_mapping(ruff["lint"])["isort"])[
                "known-first-party"
            ],
        )
        tm.that(known_first_party, has="flext_core")
        tm.that(known_first_party, lacks="demo_migration_tool")
