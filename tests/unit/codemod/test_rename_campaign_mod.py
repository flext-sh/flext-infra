"""Configured CSV campaigns through the real public mod command.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from flext_infra import FlextInfraConfig, c, infra, m
from tests import tm, u

if TYPE_CHECKING:
    from tests import p


class TestsFlextInfraRenameCampaignMod:
    """Use separate processes and real config files, never patched owner state."""

    @staticmethod
    @pytest.mark.parametrize(
        ("apply", "check", "dry_run"),
        [(False, False, False), (True, True, False), (True, False, True)],
    )
    def test_public_mod_readonly_keeps_declared_artifact_and_parent_absent(
        tmp_path: Path,
        mod_progress: p.Infra.ModProgress,
        *,
        apply: bool,
        check: bool,
        dry_run: bool,
    ) -> None:
        """Pending-work verdicts never publish declared artifacts or rename consumers."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        receiver, receiver_package = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="readonly-receiver", package_name="readonly_receiver"
        )
        for checkout in (root, receiver):
            u.Tests.provision_checkout(checkout)
            u.Tests.provision_runtime_environment(checkout)
        source = package / "service.py"
        consumer = receiver_package / "consumer.py"
        source.write_text(
            "class Original:\n    VALUE = 'preserved'\n\n__all__ = ['Original']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        consumer.write_text(
            f"from {package.name}.service import Original\nVALUE = Original.VALUE\n",
            encoding=c.DEFAULT_ENCODING,
        )
        config_dir = root / c.CONFIG_DIR_NAME
        config_dir.mkdir(exist_ok=True)
        manifest = config_dir / "decisions.json"
        manifest.write_text(
            m.Infra.SemanticRenameSelections(
                decisions=(
                    m.Infra.SemanticRenameSelection(
                        qualified_name=f"{package.name}.service.Original",
                        replacement_name="Renamed",
                        reason="Explicit project domain name",
                    ),
                ),
                consumer_roots=(receiver,),
            ).model_dump_json(),
            encoding=c.DEFAULT_ENCODING,
        )
        output = Path("semantic-artifacts") / "nested" / "plan.artifact"
        declaration = config_dir / c.Infra.INFRA_CONFIG_FILENAME
        declaration.write_text(
            "Infra:\n  refactor_csv_campaigns:\n"
            "    semantic_decisions: config/decisions.json\n"
            f"    semantic_plan: {output.as_posix()}\n",
            encoding=c.DEFAULT_ENCODING,
        )
        snapshots = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in (source, consumer, manifest, declaration)
        )
        tm.fail((root / output.parts[0]).exists())
        infra.mod(
            m.Infra.ModCommand(
                repository_root=root,
                apply=apply,
                check=check,
                dry_run_mode=dry_run,
            ),
            mod_progress,
        )
        tm.ok(u.Cli.atomic_verify_binary_file_states(snapshots))
        tm.fail((root / output).exists())
        tm.fail((root / output.parts[0]).exists())
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"from {package.name}.service import Original\n"
                "from readonly_receiver.consumer import VALUE\n"
                "print(Original.VALUE == VALUE == 'preserved')\n",
                python_paths=(str(package.parent), str(receiver_package.parent)),
            ),
            eq=["True"],
        )

    @staticmethod
    @pytest.mark.parametrize("kind", ["class", "module", "package"])
    def test_public_mod_consumes_declared_semantic_decisions_and_converges(
        tmp_path: Path,
        mod_progress: p.Infra.ModProgress,
        kind: str,
    ) -> None:
        """A real cutover converges after its one-time driver is explicitly retired."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        receiver, receiver_package = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="decision-receiver", package_name="decision_receiver"
        )
        for checkout in (root, receiver):
            u.Tests.provision_checkout(checkout)
            u.Tests.provision_runtime_environment(checkout)
        source_dir = package
        original_module = f"{package.name}.service"
        qualified_name = f"{original_module}.Original"
        replacement_name = "Renamed"
        renamed_identity = f"{original_module} import Renamed"
        if kind == "module":
            qualified_name = original_module
            replacement_name = "domain"
            renamed_identity = f"{package.name}.domain import Original as Renamed"
        elif kind == "package":
            source_dir = package / "parts"
            source_dir.mkdir()
            (source_dir / "__init__.py").write_text("", encoding=c.DEFAULT_ENCODING)
            original_module = f"{package.name}.parts.service"
            qualified_name = f"{package.name}.parts"
            replacement_name = "_domain"
            renamed_identity = (
                f"{package.name}._domain.service import Original as Renamed"
            )
        (source_dir / "service.py").write_text(
            "class Original:\n    VALUE = 'preserved'\n\n__all__ = ['Original']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (receiver_package / "consumer.py").write_text(
            f"from {original_module} import Original\nVALUE = Original.VALUE\n",
            encoding=c.DEFAULT_ENCODING,
        )
        config_dir = root / c.CONFIG_DIR_NAME
        config_dir.mkdir(exist_ok=True)
        manifest = config_dir / "decisions.json"
        selections = m.Infra.SemanticRenameSelections(
            decisions=(
                m.Infra.SemanticRenameSelection(
                    qualified_name=qualified_name,
                    replacement_name=replacement_name,
                    reason="Explicit project domain name",
                ),
            ),
            consumer_roots=(receiver,),
        )
        manifest.write_text(selections.model_dump_json(), encoding=c.DEFAULT_ENCODING)
        (config_dir / c.Infra.INFRA_CONFIG_FILENAME).write_text(
            "Infra:\n  refactor_csv_campaigns:\n"
            "    semantic_decisions: config/decisions.json\n"
            f"    semantic_plan: {c.Infra.REPORTS_DIR_NAME}/decisions.artifact\n",
            encoding=c.DEFAULT_ENCODING,
        )
        request = m.Infra.ModCommand(repository_root=root, apply=True)
        tm.fail((root / c.Infra.REPORTS_DIR_NAME).exists())
        tm.ok(infra.mod(request, mod_progress))
        artifact_path = root / c.Infra.REPORTS_DIR_NAME / "decisions.artifact"
        tm.ok(artifact_path.is_file())
        artifact = m.Infra.SemanticRenamePlan.model_validate_json(
            artifact_path.read_bytes()
        )
        tm.that(artifact.consumer_roots, eq=(receiver,))
        python_paths = (str(package.parent), str(receiver_package.parent))
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"from {renamed_identity}\n"
                "from decision_receiver.consumer import VALUE\n"
                "print(Renamed.VALUE == VALUE == 'preserved')\n",
                python_paths=python_paths,
            ),
            eq=["True"],
        )
        tm.that(
            m.Infra.SemanticRenameSelections.model_validate_json(manifest.read_bytes()),
            eq=selections,
        )
        with pytest.raises(ValueError, match="semantic rename"):
            infra.mod(request, mod_progress)
        (config_dir / c.Infra.INFRA_CONFIG_FILENAME).write_text(
            "Infra:\n  refactor_csv_campaigns:\n    campaigns: []\n",
            encoding=c.DEFAULT_ENCODING,
        )
        manifest.unlink()
        snapshots = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for checkout in (root, receiver)
            for path in u.Infra.discover_python_files(
                checkout, workspace_excluded_top_dirs=frozenset()
            )
        )
        tm.ok(infra.mod(request, mod_progress))
        tm.ok(u.Cli.atomic_verify_binary_file_states(snapshots))

    @staticmethod
    def test_public_rename_plan_materializes_missing_parent_then_mod_consumes_it(
        tmp_path: Path,
        mod_progress: p.Infra.ModProgress,
    ) -> None:
        """Explicit artifact publication creates its parent without changing sources."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.provision_checkout(root)
        u.Tests.provision_runtime_environment(root)
        source = package / "service.py"
        consumer = package / "consumer.py"
        source.write_text(
            "class Original:\n    VALUE = 'preserved'\n\n__all__ = ['Original']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        consumer.write_text(
            f"from {package.name}.service import Original\nVALUE = Original.VALUE\n",
            encoding=c.DEFAULT_ENCODING,
        )
        states = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in (source, consumer)
        )
        output = Path(c.Infra.REPORTS_DIR_NAME) / "nested" / "plan.artifact"
        tm.fail((root / c.Infra.REPORTS_DIR_NAME).exists())
        selections = m.Infra.SemanticRenameSelections(
            decisions=(
                m.Infra.SemanticRenameSelection(
                    qualified_name=f"{package.name}.service.Original",
                    replacement_name="Renamed",
                    reason="Explicit project domain name",
                ),
            ),
        )
        result = tm.ok(
            u.Cli.run_raw((
                sys.executable,
                "-m",
                "flext_infra",
                "refactor",
                "rename-plan",
                "--repository-root",
                str(root),
                "--decisions",
                selections.model_dump_json(),
                "--output",
                str(output),
            )),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True, msg=result.stderr)
        tm.ok((root / output).is_file())
        tm.ok(u.Cli.atomic_verify_binary_file_states(states))
        tm.ok(
            infra.mod(
                m.Infra.ModCommand(
                    repository_root=root, rename_plan=output, apply=True
                ),
                mod_progress,
            )
        )
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"from {package.name}.service import Renamed\n"
                f"from {package.name}.consumer import VALUE\n"
                "print(Renamed.VALUE == VALUE == 'preserved')\n",
                python_paths=(str(package.parent),),
            ),
            eq=["True"],
        )

    @staticmethod
    @pytest.mark.parametrize("unsafe", ["parent_symlink", "leaf_symlink", "escape"])
    def test_public_rename_plan_rejects_aliased_or_escaping_outputs(
        tmp_path: Path,
        unsafe: str,
    ) -> None:
        """Rejected artifact paths preserve physical targets and original inputs."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "service.py"
        source.write_text(
            "class Original:\n    VALUE = 'preserved'\n",
            encoding=c.DEFAULT_ENCODING,
        )
        destination = root / "physical"
        if unsafe == "escape":
            destination = tmp_path / "outside"
        destination.mkdir()
        protected = destination / "protected.artifact"
        protected.write_text("protected payload\n", encoding=c.DEFAULT_ENCODING)
        reports = root / c.Infra.REPORTS_DIR_NAME
        output = reports / "plan.artifact"
        if unsafe == "parent_symlink":
            reports.symlink_to(destination, target_is_directory=True)
        elif unsafe == "leaf_symlink":
            reports.mkdir()
            output.symlink_to(protected)
        else:
            output = protected
        snapshots = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in (source, protected)
        )
        selections = m.Infra.SemanticRenameSelections(
            decisions=(
                m.Infra.SemanticRenameSelection(
                    qualified_name=f"{package.name}.service.Original",
                    replacement_name="Renamed",
                    reason="Explicit project domain name",
                ),
            ),
        )
        result = tm.ok(
            u.Cli.run_raw((
                sys.executable,
                "-m",
                "flext_infra",
                "refactor",
                "rename-plan",
                "--repository-root",
                str(root),
                "--decisions",
                selections.model_dump_json(),
                "--output",
                str(output),
            )),
        )
        tm.fail(u.Cli.process_succeeded(result.outcome))
        tm.ok(u.Cli.atomic_verify_binary_file_states(snapshots))
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"from {package.name}.service import Original\n"
                "print(Original.VALUE)\n",
                python_paths=(str(package.parent),),
            ),
            eq=["preserved"],
        )
        if unsafe == "parent_symlink":
            tm.that(reports.readlink(), eq=destination)
        elif unsafe == "leaf_symlink":
            tm.that(output.readlink(), eq=protected)

    @staticmethod
    @pytest.mark.parametrize("apply", [False, True])
    @pytest.mark.parametrize("content", ["{", "{}", '{"decisions": []}'])
    def test_public_mod_rejects_invalid_declared_semantic_manifest(
        tmp_path: Path,
        mod_progress: p.Infra.ModProgress,
        content: str,
        *,
        apply: bool,
    ) -> None:
        """Malformed or empty declared decisions never become ordinary mod."""
        root, _package = u.Tests.create_lazy_init_workspace(tmp_path)
        config_dir = root / c.CONFIG_DIR_NAME
        config_dir.mkdir(exist_ok=True)
        (config_dir / "decisions.json").write_text(
            content, encoding=c.DEFAULT_ENCODING
        )
        (config_dir / c.Infra.INFRA_CONFIG_FILENAME).write_text(
            "Infra:\n  refactor_csv_campaigns:\n"
            "    semantic_decisions: config/decisions.json\n"
            f"    semantic_plan: {c.Infra.REPORTS_DIR_NAME}/decisions.artifact\n",
            encoding=c.DEFAULT_ENCODING,
        )
        with pytest.raises(ValueError):
            infra.mod(m.Infra.ModCommand(repository_root=root, apply=apply), mod_progress)
        tm.fail((root / c.Infra.REPORTS_DIR_NAME / "decisions.artifact").exists())

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
