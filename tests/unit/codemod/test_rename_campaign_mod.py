"""Configured CSV campaigns through the real public mod command.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from flext_infra import FlextInfraConfig, c, infra, m
from tests import tm, u


class TestsFlextInfraRenameCampaignMod:
    """Use separate processes and real config files, never patched owner state."""

    @staticmethod
    def _declare(config_dir: Path) -> None:
        config_dir.mkdir(exist_ok=True)
        (config_dir / "renames.csv").write_text(
            "old,new\ncampaign_token,campaign_renamed_token\n",
            encoding="utf-8",
        )
        (config_dir / c.Infra.INFRA_CONFIG_FILENAME).write_text(
            "Infra:\n  refactor_csv_campaigns:\n    campaigns:\n"
            "      - csv: renames.csv\n"
            "        text_globs: ['**/*.md']\n"
            "        python_documentation: true\n",
            encoding="utf-8",
        )

    @pytest.mark.slow
    @pytest.mark.parametrize("apply", [False, True])
    def test_public_mod_consumes_declared_text_campaign(
        self,
        mod_workspace: Path,
        *,
        apply: bool,
    ) -> None:
        """Test public mod consumes declared text campaign."""
        config_dir = mod_workspace / "config"
        self._declare(config_dir)
        (mod_workspace / "sample.py").write_text(
            '"""Document campaign_token without changing the runtime payload."""\n'
            "\nfrom __future__ import annotations\n"
            "\nclass ModWorkspaceSample:\n"
            '    PAYLOAD: str = "campaign_token"\n\n'
            '__all__ = ["ModWorkspaceSample"]\n',
            encoding="utf-8",
        )
        guide = mod_workspace / "guide.md"
        guide.write_text("A campaign_token paragraph.\n", encoding="utf-8")
        result = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-m",
                    "flext_infra",
                    "refactor",
                    "mod",
                    "--repository-root",
                    str(mod_workspace),
                    *(("--apply",) if apply else ()),
                ),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=apply, msg=result.stderr)
        if apply:
            tm.that(result.stdout, has="published file(s)")
        tm.that(
            guide.read_text(),
            eq="A campaign_renamed_token paragraph.\n"
            if apply
            else "A campaign_token paragraph.\n",
        )
        consumer = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        "from sample import ModWorkspaceSample; "
                        "print(ModWorkspaceSample.PAYLOAD)"
                    ),
                ),
                cwd=mod_workspace,
            ),
        )
        tm.that(consumer.stdout, eq="campaign_token\n")

    @staticmethod
    @pytest.mark.slow
    def test_public_mod_renames_only_declared_field_binding(
        mod_workspace: Path,
    ) -> None:
        """A field campaign preserves unrelated members with the same spelling."""
        config_dir = mod_workspace / "config"
        config_dir.mkdir(exist_ok=True)
        (config_dir / "renames.csv").write_text(
            "old,new\nldif,Ldif\n", encoding="utf-8"
        )
        (config_dir / c.Infra.INFRA_CONFIG_FILENAME).write_text(
            "Infra:\n  refactor_csv_campaigns:\n    campaigns:\n"
            "      - csv: renames.csv\n"
            "        rename_definitions: true\n"
            "        bindings: {'': ['sample.ModWorkspaceSample.Settings']}\n",
            encoding="utf-8",
        )
        source = mod_workspace / "sample.py"
        source.write_text(
            "from __future__ import annotations\n\n"
            "class ModWorkspaceSample:\n"
            "    class Settings:\n        ldif: str = 'configured'\n\n"
            "    class Client:\n        ldif: str = 'service'\n\n"
            "    @classmethod\n"
            "    def values(cls) -> tuple[str, str]:\n"
            "        settings = cls.Settings()\n"
            "        client = cls.Client()\n"
            "        return settings.ldif, client.ldif\n\n"
            "__all__ = ['ModWorkspaceSample']\n",
            encoding="utf-8",
        )
        original = source.read_bytes()
        preview = tm.ok(
            infra.apply_renames(
                m.Infra.ApplyRenamesInput(
                    repository_root=mod_workspace,
                    csv=str(config_dir / "renames.csv"),
                    roots=(str(mod_workspace),),
                    bindings={"": ("sample.ModWorkspaceSample.Settings",)},
                    rename_definitions=True,
                )
            )
        )
        tm.that(preview.preview_diff, has=f"--- {source}")
        tm.that(preview.preview_diff, has="settings.Ldif, client.ldif")
        tm.that(preview.preview_diff, lacks="client.Ldif")
        tm.that(source.read_bytes(), eq=original)
        result = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-m",
                    "flext_infra",
                    "refactor",
                    "mod",
                    "--repository-root",
                    str(mod_workspace),
                    "--apply",
                ),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True, msg=result.stderr)
        updated = source.read_text(encoding="utf-8")
        tm.that(updated, has="Ldif: str")
        tm.that(updated, has="settings.Ldif")
        tm.that(updated, has="client.ldif")
        consumer = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        "from sample import ModWorkspaceSample; "
                        "print(ModWorkspaceSample.values())"
                    ),
                ),
                cwd=mod_workspace,
            ),
        )
        tm.that(consumer.stdout, eq="('configured', 'service')\n")

    @staticmethod
    def test_packaged_campaigns_preserve_prose_and_converge(
        tmp_path: Path,
    ) -> None:
        """Test packaged campaigns preserve prose and converge."""
        mod_workspace, _package = u.Tests.create_lazy_init_workspace(tmp_path)
        config_dir = FlextInfraConfig.ssot_config_dir()
        campaigns = (
            FlextInfraConfig.fetch_global().Infra.refactor_csv_campaigns.campaigns
        )
        tm.that(campaigns, empty=False)
        for index, campaign in enumerate(campaigns):
            rows = tm.ok(
                u.Cli.csv_loads(
                    (config_dir / campaign.csv).read_text(encoding="utf-8"),
                ),
            )
            pairs = tuple((row[0], row[1]) for row in rows[1:])
            mentions = "".join(f"- {old}\n" for old, _new in pairs)
            guide = mod_workspace / f"campaign_{index}.md"
            guide.write_text(
                "# Guide\n\nSurrounding prose remains.\n" + mentions,
                encoding="utf-8",
            )
            consumer = mod_workspace / f"consumer_{index}.py"
            consumer.write_text(f'"""{mentions}"""\n', encoding="utf-8")
            params = m.Infra.ApplyRenamesInput(
                csv=str(config_dir / campaign.csv),
                roots=(str(mod_workspace),),
                apply=True,
                bindings=campaign.bindings,
                text_globs=campaign.text_globs,
                python_documentation=campaign.python_documentation,
                exclude_globs=campaign.exclude_globs,
            )
            tm.ok(infra.apply_renames(params))
            for old, new in pairs:
                tm.that(guide.read_text(), has=f"- {new}\n")
                tm.that(guide.read_text(), lacks=f"- {old}\n")
            tm.that(guide.read_text(), has="Surrounding prose remains.\n")
            first = guide.read_bytes()
            second = tm.ok(infra.apply_renames(params))
            tm.that(second.files_changed, eq=0)
            tm.that(second.occurrences, eq=0)
            tm.that(guide.read_bytes(), eq=first)

    @pytest.mark.slow
    @pytest.mark.parametrize(
        ("csv", "roots"),
        [
            ("../outside.csv", ()),
            ("/outside.csv", ()),
            ("renames.csv", ("../outside",)),
            ("renames.csv", ("/outside",)),
            ("renames.csv", (r"C:\\outside",)),
        ],
    )
    def test_public_config_rejects_escaping_campaign_paths(
        self,
        mod_workspace: Path,
        csv: str,
        roots: tuple[str, ...],
    ) -> None:
        """A malformed campaign fails at config validation before source edits."""
        config_dir = mod_workspace / "config"
        self._declare(config_dir)
        (config_dir / c.Infra.INFRA_CONFIG_FILENAME).write_text(
            "Infra:\n  refactor_csv_campaigns:\n    campaigns:\n"
            f"      - csv: {csv!r}\n"
            f"        roots: {list(roots)!r}\n"
            "        text_globs: ['**/*.md']\n",
            encoding="utf-8",
        )
        guide = mod_workspace / "guide.md"
        guide.write_text("A campaign_token paragraph.\n", encoding="utf-8")
        result = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-m",
                    "flext_infra",
                    "refactor",
                    "mod",
                    "--repository-root",
                    str(mod_workspace),
                    "--apply",
                ),
            ),
        )
        tm.fail(u.Cli.process_succeeded(result.outcome))
        tm.that(
            result.stderr + result.stdout,
            has="CSV campaign path must be relative and non-escaping",
        )
        tm.that(guide.read_text(encoding="utf-8"), eq="A campaign_token paragraph.\n")

    @pytest.mark.slow
    @pytest.mark.parametrize("escape", ["driver", "root"])
    def test_public_mod_rejects_symlink_escape_before_publication(
        self,
        mod_workspace: Path,
        tmp_path: Path,
        escape: str,
    ) -> None:
        """A relative declaration cannot follow a link outside its owner."""
        config_dir = mod_workspace / "config"
        self._declare(config_dir)
        outside = tmp_path / "outside"
        outside.mkdir()
        guide = outside / "guide.md"
        guide.write_text("A campaign_token paragraph.\n", encoding="utf-8")
        if escape == "driver":
            source = outside / "renames.csv"
            source.write_bytes((config_dir / "renames.csv").read_bytes())
            (config_dir / "renames.csv").unlink()
            (config_dir / "renames.csv").symlink_to(source)
            expected = "CSV campaign driver escapes config directory"
        else:
            (mod_workspace / "outside").symlink_to(outside, target_is_directory=True)
            (config_dir / c.Infra.INFRA_CONFIG_FILENAME).write_text(
                "Infra:\n  refactor_csv_campaigns:\n    campaigns:\n"
                "      - csv: renames.csv\n"
                "        roots: [outside]\n"
                "        text_globs: ['**/*.md']\n",
                encoding="utf-8",
            )
            expected = "CSV campaign scan root escapes repository"
        result = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-m",
                    "flext_infra",
                    "refactor",
                    "mod",
                    "--repository-root",
                    str(mod_workspace),
                    "--apply",
                ),
            ),
        )
        tm.fail(u.Cli.process_succeeded(result.outcome))
        tm.that(result.stdout + result.stderr, has=expected)
        tm.that(guide.read_text(encoding="utf-8"), eq="A campaign_token paragraph.\n")
        tm.that(guide.read_text(encoding="utf-8"), eq="A campaign_token paragraph.\n")
