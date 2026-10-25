"""Real public semantic publication, identity and fix-forward contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import stat
from pathlib import Path

import pytest

from flext_infra import codemod, infra, services
from tests import c, m, t, tm, u


class TestsFlextInfraSemanticPublication:
    """Preserve successful effects and report each unsafe semantic target."""

    @staticmethod
    def test_module_policy_derives_native_moves_and_cross_root_consumers(
        tmp_path: Path,
    ) -> None:
        """Discover private module files without changing packages or live bytes."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        receiver, receiver_package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="module-receiver",
            package_name="module_receiver",
        )
        for checkout in (root, receiver):
            u.Tests.provision_checkout(checkout)
            u.Tests.provision_runtime_environment(checkout)
        facade = package / "_facade"
        facade.mkdir()
        (facade / "__init__.py").write_text("", encoding=c.DEFAULT_ENCODING)
        source = facade / "_module.py"
        source.write_text("VALUE = 1\n", encoding=c.DEFAULT_ENCODING)
        special = facade / "__main__.py"
        special.write_text("", encoding=c.DEFAULT_ENCODING)
        proper = facade / "proper.py"
        proper.write_text("", encoding=c.DEFAULT_ENCODING)
        consumer = receiver_package / "consumer.py"
        original = f"from {package.name}._facade._module import VALUE\n"
        consumer.write_text(original, encoding=c.DEFAULT_ENCODING)
        consumer_private = receiver_package / "_consumer.py"
        consumer_private.write_text("", encoding=c.DEFAULT_ENCODING)
        seed = tm.ok(
            codemod.FlextInfraCodemodSemanticApply.build_source_plan(root, (receiver,))
        )
        planned = tm.ok(
            codemod.FlextInfraCodemodSemanticApply.plan_module_names(root, seed)
        )
        updates = planned.candidate.updates
        tm.that(updates[source], eq=None)
        tm.that(updates[facade / "module.py"], eq=source.read_text())
        tm.that(
            updates[consumer],
            eq=f"from {package.name}._facade.module import VALUE\n",
        )
        for unchanged in (special, proper, facade / "__init__.py", consumer_private):
            tm.ok(unchanged not in updates)
        tm.that(consumer.read_text(), eq=original)
        tm.ok(source.is_file())
        tm.ok(not (facade / "module.py").exists())

    @staticmethod
    @pytest.mark.parametrize(
        "destination_kind",
        ["data-only", "module", "package", "namespace", "nested-namespace", "invalid"],
    )
    def test_native_module_rename_distinguishes_data_from_python_destinations(
        tmp_path: Path, destination_kind: str
    ) -> None:
        """Plan beside YAML data, but refuse occupied Python or invalid names."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.provision_checkout(root)
        u.Tests.provision_runtime_environment(root)
        source = package / "_config.py"
        original = b"VALUE = 1\n"
        source.write_bytes(original)
        target = package / "config.py"
        data = package / "config"
        nested = data / "nested"
        nested.mkdir(parents=True)
        payloads = {
            data / "rules.yaml": b"enabled: true\r\n",
            nested / "settings.yaml": b"value: preserved\n",
        }
        for path, content in payloads.items():
            path.write_bytes(content)
        consumer = package / "consumer.py"
        consumer.write_text(
            f"from {package.name}._config import VALUE\n",
            encoding=c.DEFAULT_ENCODING,
        )
        occupied = None
        if destination_kind == "module":
            occupied = target
        elif destination_kind == "package":
            occupied = data / c.Infra.INIT_PY
        elif destination_kind in {"namespace", "nested-namespace"}:
            occupied = (
                nested if destination_kind == "nested-namespace" else data
            ) / "provider.py"
        if occupied is not None:
            occupied.write_bytes(b"")
            payloads[occupied] = b""
        originals = {
            path: path.read_bytes()
            for path in (source, consumer, package / c.Infra.INIT_PY, *payloads)
        }
        selections = m.Infra.SemanticRenameSelections(
            decisions=(
                m.Infra.SemanticRenameSelection(
                    qualified_name=f"{package.name}.{source.stem}",
                    replacement_name=(
                        "not-valid" if destination_kind == "invalid" else "config"
                    ),
                    reason="Preserve configuration data beside the renamed module",
                ),
            ),
        )
        with infra.rope_workspace(root) as workspace:
            if destination_kind == "data-only":
                planned = tm.ok(
                    codemod.FlextInfraCodemodSemanticApply.build_rename_plan(
                        root, workspace, selections
                    )
                )
                tm.that(planned.moves, eq=((source, target),))
                tm.that(planned.candidate.updates[source], eq=None)
                tm.that(
                    planned.candidate.updates[target],
                    eq=original.decode(c.DEFAULT_ENCODING),
                )
                tm.that(
                    planned.candidate.updates[consumer],
                    eq=f"from {package.name}.config import VALUE\n",
                )
                tm.ok(
                    all(
                        not path.is_relative_to(data)
                        for path in planned.candidate.updates
                    )
                )
            else:
                with pytest.raises(ValueError, match=r"occupied|Python identifier"):
                    codemod.FlextInfraCodemodSemanticApply.build_rename_plan(
                        root, workspace, selections
                    )
        for path, content in originals.items():
            tm.that(path.read_bytes(), eq=content)
        tm.ok(data.is_dir())
        tm.ok(nested.is_dir())
        tm.that(target.exists(), eq=destination_kind == "module")

    @staticmethod
    @pytest.mark.parametrize("occupied", ["module.py", "__module.py", "module"])
    def test_module_policy_collision_has_no_live_effects(
        tmp_path: Path, occupied: str
    ) -> None:
        """Reject occupied or competing module destinations before publication."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.provision_checkout(root)
        u.Tests.provision_runtime_environment(root)
        source = package / "_module.py"
        original = "VALUE = 1\n"
        source.write_text(original, encoding=c.DEFAULT_ENCODING)
        destination = package / occupied
        if destination.suffix:
            destination.write_text("", encoding=c.DEFAULT_ENCODING)
        else:
            destination.mkdir()
            (destination / "__init__.py").write_text("", encoding=c.DEFAULT_ENCODING)
        seed = tm.ok(codemod.FlextInfraCodemodSemanticApply.build_source_plan(root))
        with pytest.raises(ValueError, match=r"conflict|occupied"):
            codemod.FlextInfraCodemodSemanticApply.plan_module_names(root, seed)
        tm.that(source.read_text(), eq=original)
        tm.ok(destination.exists())

    @staticmethod
    @pytest.mark.parametrize("name", ["_.py", "_class.py"])
    def test_module_policy_rejects_invalid_stripped_identifiers(
        tmp_path: Path, name: str
    ) -> None:
        """Do not turn a private module into an empty identifier or keyword."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.provision_checkout(root)
        u.Tests.provision_runtime_environment(root)
        source = package / name
        original = "VALUE = 1\n"
        source.write_text(original, encoding=c.DEFAULT_ENCODING)
        seed = tm.ok(codemod.FlextInfraCodemodSemanticApply.build_source_plan(root))
        with pytest.raises(ValueError, match="no valid public identifier"):
            codemod.FlextInfraCodemodSemanticApply.plan_module_names(root, seed)
        tm.that(source.read_text(), eq=original)

    @staticmethod
    def _rename_artifact(
        tmp_path: Path,
        *,
        kind: str = "callable",
        external_consumers: int = 0,
        executable: bool = False,
    ) -> t.Pair[m.Infra.SemanticRenamePlan, m.Cli.AtomicFileState]:
        """Build a native artifact against an independent physical runtime.

        Returns:
            The captured source candidate and its separate driver identity.

        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.provision_checkout(root)
        u.Tests.provision_runtime_environment(root)
        driver = root / c.Infra.REPORTS_DIR_NAME / "native" / "rename.artifact"
        driver.parent.mkdir(parents=True, exist_ok=True)
        notice = u.Infra.copyright_notice(root)
        source = package / "service.py"
        source.write_text(
            f'"""Public callable contract.\n\n{notice}\n"""\n\n'
            "from __future__ import annotations\n\n\n"
            "class FlextSemanticService:\n"
            '    """Preserve predicate behavior under an explicit domain rename."""\n\n'
            "    @staticmethod\n"
            "    def predicate(value: str) -> bool:\n"
            '        """Inspect a caller value.\n\n'
            "        Returns:\n"
            "            Whether the value is nonempty.\n"
            '        """\n'
            "        return bool(value)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        consumer = package / "consumer.py"
        consumer.write_text(
            f'"""Observed callable consumer.\n\n{notice}\n"""\n\n'
            "from __future__ import annotations\n\n"
            f"from {package.name}.service import FlextSemanticService\n\n"
            'VALUE = FlextSemanticService.predicate("domain")\n',
            encoding=c.DEFAULT_ENCODING,
        )
        if executable:
            source.chmod(stat.S_IMODE(source.stat().st_mode) | stat.S_IXUSR)
        consumer_roots: list[Path] = []
        for index in range(external_consumers):
            receiver, receiver_package = u.Tests.create_lazy_init_workspace(
                tmp_path,
                project_name=f"native-receiver-{index}",
                package_name=f"native_receiver_{index}",
            )
            u.Tests.provision_checkout(receiver)
            u.Tests.provision_runtime_environment(receiver)
            (receiver_package / "consumer.py").write_text(
                consumer.read_text(encoding=c.DEFAULT_ENCODING),
                encoding=c.DEFAULT_ENCODING,
            )
            consumer_roots.append(receiver)
        with infra.rope_workspace(root) as workspace:
            artifact = tm.ok(
                codemod.FlextInfraCodemodSemanticApply.build_rename_plan(
                    root,
                    workspace,
                    m.Infra.SemanticRenameSelections(
                        decisions=(
                            m.Infra.SemanticRenameSelection(
                                qualified_name=(
                                    f"{package.name}.service"
                                    + (
                                        ".FlextSemanticService"
                                        if kind != "module"
                                        else ""
                                    )
                                    + (".predicate" if kind == "callable" else "")
                                ),
                                replacement_name="FlextMeaningfulService"
                                if kind == "class"
                                else "meaningful",
                                reason="Reviewed callable domain contract",
                            ),
                        ),
                        consumer_roots=tuple(consumer_roots),
                    ),
                )
            )
        tm.ok(consumer in artifact.candidate.updates)
        tm.ok(u.Cli.atomic_write_text_file(driver, artifact.model_dump_json()))
        captured = tm.ok(u.Cli.atomic_read_binary_file_state(driver, required=True))
        hydrated = m.Infra.SemanticRenamePlan.model_validate_json(
            tm.not_none(captured.content)
        )
        tm.that(
            hydrated.model_dump(mode="python"),
            eq=artifact.model_dump(mode="python"),
        )
        return hydrated, captured

    @pytest.mark.parametrize("kind", ["class", "module"])
    def test_mod_composes_native_cross_root_effects_and_is_idempotent(
        self,
        tmp_path: Path,
        kind: str,
    ) -> None:
        """Public mod composes one native candidate across roots, idempotently."""
        u.Tests.run_native_callable(self._scenario_cross_root_mod, tmp_path, kind)

    @staticmethod
    def _scenario_cross_root_mod(tmp_path: Path, kind: str) -> None:
        """The normal public mod action consumes one coordinated native candidate."""
        mod_progress = services.FlextInfraCliModProgress()
        artifact, driver = TestsFlextInfraSemanticPublication._rename_artifact(
            tmp_path,
            kind=kind,
            external_consumers=2,
            executable=kind == "module",
        )
        root = (artifact.candidate.workspaces or (artifact.candidate.workspace,))[0]
        origin_mode = (
            stat.S_IMODE(artifact.moves[0][0].stat().st_mode)
            if artifact.moves
            else None
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / c.GIT_DIR_NAME / "persisted-plan-metadata", "metadata\n"
            )
        )
        with infra.rope_workspace(root) as workspace:
            rebuilt = tm.ok(
                codemod.FlextInfraCodemodSemanticApply.build_rename_plan(
                    root,
                    workspace,
                    codemod.FlextInfraCodemodSemanticApply.rename_selections(artifact),
                    source_plan=artifact,
                )
            )
        tm.that(
            rebuilt.model_dump(mode="python"), eq=artifact.model_dump(mode="python")
        )
        if kind == "class":
            tm.ok(root != artifact.candidate.workspace)
        tm.ok(
            infra.mod(
                m.Infra.ModCommand(
                    repository_root=root,
                    apply=True,
                    rename_plan=driver.path,
                    consumer_roots=artifact.consumer_roots,
                ),
                mod_progress,
            )
        )
        if kind == "module":
            origin, target = artifact.moves[0]
            tm.fail(origin.exists())
            tm.that(stat.S_IMODE(target.stat().st_mode), eq=origin_mode)
        for receiver in artifact.consumer_roots:
            package = next(
                layout.package_name
                for layout in artifact.candidate.layouts
                if layout.project_root == receiver
            )
            tm.that(
                u.Tests.run_lazy_init_probe(
                    f"from {package}.consumer import VALUE\nprint(VALUE)\n",
                    python_paths=tuple(
                        str(layout.src_dir) for layout in artifact.candidate.layouts
                    ),
                ),
                eq=["True"],
            )
        published = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for scope in (root, *artifact.consumer_roots)
            for path in u.Infra.discover_python_files(
                scope, workspace_excluded_top_dirs=frozenset()
            )
        )
        tm.ok(
            infra.mod(
                m.Infra.ModCommand(
                    repository_root=root,
                    apply=True,
                    consumer_roots=artifact.consumer_roots,
                ),
                mod_progress,
            )
        )
        tm.ok(u.Cli.atomic_verify_binary_file_states(published))
        tm.that(driver.path.read_bytes(), eq=driver.content)

    def test_mod_rejects_changed_persisted_rename_payload(self, tmp_path: Path) -> None:
        """A persisted rename payload whose edits drifted from its plan is rejected."""
        u.Tests.run_native_callable(self._scenario_payload_drift, tmp_path)

    @staticmethod
    def _scenario_payload_drift(tmp_path: Path) -> None:
        """A persisted edit plan that differs from the native plan is refused."""
        mod_progress = services.FlextInfraCliModProgress()
        artifact, driver = TestsFlextInfraSemanticPublication._rename_artifact(
            tmp_path, kind="class"
        )
        tm.that(artifact.edits, empty=False)
        changed = artifact.model_copy(update={"edits": ()})
        tm.ok(u.Cli.atomic_write_text_file(driver.path, changed.model_dump_json()))
        observed_driver = tm.ok(
            u.Cli.atomic_read_binary_file_state(driver.path, required=True)
        )
        root = (artifact.candidate.workspaces or (artifact.candidate.workspace,))[0]
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / c.GIT_DIR_NAME / "persisted-plan-metadata", "metadata\n"
            )
        )
        originals = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in u.Infra.discover_python_files(
                root, workspace_excluded_top_dirs=frozenset()
            )
        )
        tm.fail(
            infra.mod(
                m.Infra.ModCommand(
                    repository_root=root,
                    apply=True,
                    rename_plan=driver.path,
                    consumer_roots=artifact.consumer_roots,
                ),
                mod_progress,
            ),
            has="fields=edits",
        )
        tm.ok(u.Cli.atomic_verify_binary_file_states((*originals, observed_driver)))

    @pytest.mark.slow
    @pytest.mark.parametrize("needs_ast", [False, True])
    def test_source_campaign_applies_ast_without_a_rename_artifact(
        self,
        tmp_path: Path,
        *,
        needs_ast: bool,
    ) -> None:
        """A source campaign applies without a rename artifact, with or without AST.

        The repeat of the same campaign is a no-op.

        """
        u.Tests.run_native_callable(
            self._scenario_source_campaign,
            tmp_path,
            needs_ast=needs_ast,
        )

    @staticmethod
    def _scenario_source_campaign(tmp_path: Path, *, needs_ast: bool) -> None:
        """The public pipeline accepts real automatic work and its no-op repeat."""
        mod_progress = services.FlextInfraCliModProgress()
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.provision_checkout(root)
        u.Tests.provision_runtime_environment(root)
        u.Tests.declare_codemod_rules(
            root,
            {
                "source-campaign": (
                    "id: source-campaign\n"
                    "language: Python\n"
                    "rule:\n"
                    "  pattern: 'value: int = 1'\n"
                    "fix: 'value: int = 2'\n"
                    "severity: warning\n"
                )
            },
        )
        source = package / "service.py"
        notice = u.Infra.copyright_notice(root)
        source.write_text(
            f'"""Automatic source campaign.\n\n{notice}\n"""\n\n'
            "from __future__ import annotations\n\n"
            f"value: int = {1 if needs_ast else 2}\n",
            encoding=c.DEFAULT_ENCODING,
        )
        before = tm.ok(codemod.FlextInfraModGateEngine.scan(root, fix=False))
        tm.that(bool(before.actionable), eq=needs_ast)
        request = m.Infra.ModCommand(repository_root=root, apply=True)
        tm.ok(infra.mod(request, mod_progress))
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"from {package.name}.service import value\nprint(value)\n",
                python_paths=(str(package.parent),),
            ),
            eq=["2"],
        )
        tm.that(
            tm.ok(codemod.FlextInfraModGateEngine.scan(root, fix=False)).findings, eq=0
        )
        published = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
        tm.ok(infra.mod(request, mod_progress))
        tm.ok(u.Cli.atomic_verify_binary_file_states((published,)))

    @staticmethod
    @pytest.mark.parametrize("retire", [False, True])
    def test_source_effect_rejects_unpaired_content_and_mode(
        tmp_path: Path, *, retire: bool
    ) -> None:
        """A deletion clears mode; a write always declares its actual mode."""
        source = tmp_path / "source.py"
        source.write_text("value = 1\n", encoding=c.DEFAULT_ENCODING)
        original = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
        with pytest.raises(ValueError, match="bytes and mode must agree"):
            m.Infra.CodegenFilePlan(
                project=tmp_path,
                path=source,
                before=original,
                desired_content=None if retire else original.content,
                desired_mode=original.mode if retire else None,
            )
        tm.ok(u.Cli.atomic_verify_binary_file_states((original,)))

    @pytest.mark.parametrize("drift", ["none", "source", "same-byte"])
    def test_composed_module_rename_preserves_mode_and_refuses_drift(
        self, tmp_path: Path, drift: str
    ) -> None:
        """A composed module rename keeps executable mode.

        A drifted or same-byte replaced origin is refused.

        """
        u.Tests.run_native_callable(self._scenario_composed_rename, tmp_path, drift)

    @staticmethod
    def _scenario_composed_rename(tmp_path: Path, drift: str) -> None:
        """Composition preserves strict rename intent, executable mode and CAS."""
        artifact, driver = TestsFlextInfraSemanticPublication._rename_artifact(
            tmp_path, kind="module", executable=True
        )
        root = artifact.candidate.workspace
        origin, target = artifact.moves[0]
        originals = {
            path: tm.ok(u.Cli.atomic_read_binary_file_state(path))
            for path in (origin, target)
        }
        composed = tm.ok(
            codemod.FlextInfraCodemodSemanticApply.compose_candidate(
                artifact,
                (
                    m.Infra.CodegenFilePlan(
                        project=root,
                        path=target,
                        before=originals[target],
                        desired_content=tm.not_none(
                            artifact.candidate.updates[target]
                        ).encode(c.DEFAULT_ENCODING),
                        desired_mode=artifact.candidate.modes[target],
                    ),
                ),
            )
        )
        tm.that(composed, is_=m.Infra.SemanticSourcePlan)
        tm.that(composed.consumer_roots, eq=artifact.consumer_roots)
        tm.that(composed.candidate.modes[target], eq=originals[origin].mode)
        if drift == "source":
            origin.write_bytes(tm.not_none(originals[origin].content) + b"\n")
        elif drift == "same-byte":
            foreign = origin.with_suffix(".foreign")
            foreign.write_bytes(tm.not_none(originals[origin].content))
            foreign.chmod(tm.not_none(originals[origin].mode))
            foreign.replace(origin)
        observed = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path)) for path in originals
        )
        published = codemod.FlextInfraCodemodSemanticApply.publish_candidate(
            root, composed
        )
        if drift == "none":
            tm.ok(published)
            tm.fail(origin.exists())
            tm.that(stat.S_IMODE(target.stat().st_mode), eq=originals[origin].mode)
        else:
            tm.fail(published)
            tm.ok(u.Cli.atomic_verify_binary_file_states(observed))
        tm.that(driver.path.read_bytes(), eq=driver.content)

    def test_automatic_nesting_rewrites_declared_consumers_without_syntax_fanout(
        self,
        tmp_path: Path,
    ) -> None:
        """Automatic nesting rewrites declared consumers without syntax fan-out.

        The rule selects the owner while external read scope stays bounded.

        """
        u.Tests.run_native_callable(self._scenario_nesting, tmp_path)

    @staticmethod
    def _scenario_nesting(tmp_path: Path) -> None:
        """Rule authority selects the owner while external read scope stays bounded."""
        mod_progress = services.FlextInfraCliModProgress()
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        receiver, receiver_package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="native-receiver",
            package_name="native_receiver",
        )
        for checkout in (root, receiver):
            u.Tests.provision_checkout(checkout)
            u.Tests.provision_runtime_environment(checkout)
        alias = next(
            letter
            for letter, family in u.Infra.facade_families().items()
            if family.module == "models"
        )
        source = package / f"{u.Tests.family_public_module(alias)}.py"
        source.write_text("", encoding=c.DEFAULT_ENCODING)
        with infra.rope_workspace(root) as graph:
            owner = (
                graph.convention(source).module_policy.project_prefix
                + u.Infra.facade_family_declared_by(source.name).suffix
            )
        source.write_text(
            f'class {owner}:\n    """Native public family owner."""\n\n'
            'class Payload:\n    """Native introducing declaration."""\n'
            '    VALUE = "native"\n\n'
            f'__all__ = ({owner!r}, "Payload")\n',
            encoding=c.DEFAULT_ENCODING,
        )
        consumer = receiver_package / "consumer.py"
        consumer.write_text(
            f"from {package.name}.{source.stem} import Payload as Bound\n"
            "VALUE = Bound.VALUE\n",
            encoding=c.DEFAULT_ENCODING,
        )
        unrelated = receiver_package / "unrelated.py"
        unrelated.write_text(
            'class Payload:\n    VALUE = "local"\nVALUE = Payload.VALUE\n',
            encoding=c.DEFAULT_ENCODING,
        )
        original = tm.ok(u.Cli.atomic_read_binary_file_state(unrelated, required=True))
        tm.ok(
            infra.mod(
                m.Infra.ModCommand(
                    repository_root=root,
                    consumer_roots=(receiver,),
                    apply=True,
                ),
                mod_progress,
            )
        )
        tm.ok(u.Cli.atomic_verify_binary_file_states((original,)))
        tm.that(
            u.Tests.run_lazy_init_probe(
                "from native_receiver.consumer import VALUE\nprint(VALUE)\n",
                python_paths=(str(package.parent), str(receiver_package.parent)),
            ),
            eq=["native"],
        )
        tm.that(source.read_text(encoding=c.DEFAULT_ENCODING), has="    class Payload:")

    @pytest.mark.parametrize("failure", ["missing", "collision", "drift"])
    def test_mod_refuses_invalid_cross_root_campaign_before_source_publication(
        self,
        tmp_path: Path,
        failure: str,
    ) -> None:
        """An invalid cross-root campaign is refused before any source is published.

        Invalid means a missing scope, an occupied native name or stale epochs.

        """
        u.Tests.run_native_callable(self._scenario_invalid_campaign, tmp_path, failure)

    @staticmethod
    def _scenario_invalid_campaign(tmp_path: Path, failure: str) -> None:
        """Missing scope, occupied native name and stale epochs stay unpublished."""
        mod_progress = services.FlextInfraCliModProgress()
        artifact, driver = TestsFlextInfraSemanticPublication._rename_artifact(
            tmp_path,
            kind="class",
            external_consumers=1,
        )
        root = artifact.candidate.workspaces[0]
        roots = artifact.consumer_roots
        if failure == "missing":
            roots = (*roots, tmp_path / "missing-consumer")
        elif failure == "collision":
            declaration = next(
                path for path in artifact.candidate.updates if path.name == "service.py"
            )
            declaration.write_text(
                declaration.read_text(encoding=c.DEFAULT_ENCODING)
                + "\nclass FlextMeaningfulService:\n    pass\n",
                encoding=c.DEFAULT_ENCODING,
            )
        else:
            consumer = next(
                path
                for path in artifact.candidate.updates
                if path.name == "consumer.py" and path.is_relative_to(roots[0])
            )
            consumer.write_bytes(
                consumer.read_bytes() + b"# a different physical epoch\n"
            )
        originals = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for scope in (root, *artifact.consumer_roots)
            for path in u.Infra.discover_python_files(
                scope, workspace_excluded_top_dirs=frozenset()
            )
        )
        tm.fail(
            infra.mod(
                m.Infra.ModCommand(
                    repository_root=root,
                    consumer_roots=roots,
                    rename_plan=driver.path,
                    apply=True,
                ),
                mod_progress,
            )
        )
        tm.ok(u.Cli.atomic_verify_binary_file_states(originals))

    @pytest.mark.parametrize("kind", ["callable", "class", "module"])
    def test_authenticated_rename_apply_publishes_then_rejects_stale_repeat(
        self,
        tmp_path: Path,
        kind: str,
    ) -> None:
        """An authenticated rename applies once and rejects a stale repeat."""
        u.Tests.run_native_callable(self._scenario_stale_repeat, tmp_path, kind)

    @staticmethod
    def _scenario_stale_repeat(tmp_path: Path, kind: str) -> None:
        """The actual artifact consumer applies once and preserves its stale driver."""
        artifact, driver = TestsFlextInfraSemanticPublication._rename_artifact(
            tmp_path, kind=kind
        )
        root = artifact.candidate.workspace
        request = m.Infra.ModCommand(
            repository_root=root, rename_plan=driver.path, apply=True
        )
        with infra.rope_workspace(root) as workspace:
            tm.that(
                tm.ok(
                    codemod.FlextInfraCodemodSemanticApply.consume_rename_plan(
                        request, workspace
                    )
                ),
                eq=True,
            )
            published = {
                path: path.read_bytes() if path.exists() else None
                for path in artifact.candidate.updates
            }
            # The shared publisher normalizes every Python effect it writes.
            for path, desired in artifact.candidate.updates.items():
                tm.that(
                    published[path],
                    eq=None
                    if desired is None
                    else tm.ok(u.Infra.normalize_python_text(path, desired)).encode(
                        c.DEFAULT_ENCODING
                    ),
                )
            tm.fail(
                codemod.FlextInfraCodemodSemanticApply.consume_rename_plan(
                    request, workspace
                )
            )
        for path, content in published.items():
            tm.that(path.read_bytes() if path.exists() else None, eq=content)
        tm.that(driver.path.read_bytes(), eq=driver.content)
        consumer = next(
            path for path in artifact.candidate.updates if path.name == "consumer.py"
        )
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"from {consumer.parent.name}.consumer import VALUE\nprint(VALUE)\n",
                python_paths=(str(consumer.parent.parent),),
            ),
            eq=["True"],
        )

    @pytest.mark.parametrize("kind", ["class", "module"])
    def test_native_rename_artifact_preserves_originals_and_refuses_consumer_drift(
        self,
        tmp_path: Path,
        kind: str,
    ) -> None:
        """A rename artifact preserves originals and refuses consumer drift.

        A changed external consumer epoch rejects the cut before the producer
        changes.

        """
        u.Tests.run_native_callable(self._scenario_consumer_drift, tmp_path, kind)

    @staticmethod
    def _scenario_consumer_drift(tmp_path: Path, kind: str) -> None:
        """A changed external epoch rejects the cut before the producer changes."""
        producer, package = u.Tests.create_lazy_init_workspace(tmp_path)
        consumer_root, consumer_package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="native-consumer",
            package_name="native_consumer",
        )
        declaration = package / "original.py"
        declaration.write_text(
            "class Original:\n    pass\n", encoding=c.DEFAULT_ENCODING
        )
        consumer = consumer_package / "consumer.py"
        consumer.write_text(
            f"from {package.name}.original import Original\nVALUE = Original()\n",
            encoding=c.DEFAULT_ENCODING,
        )
        with infra.rope_workspace(producer) as workspace:
            artifact = tm.ok(
                codemod.FlextInfraCodemodSemanticApply.build_rename_plan(
                    producer,
                    workspace,
                    m.Infra.SemanticRenameSelections(
                        decisions=(
                            m.Infra.SemanticRenameSelection(
                                qualified_name=f"{package.name}.original"
                                + (".Original" if kind == "class" else ""),
                                replacement_name="Renamed"
                                if kind == "class"
                                else "renamed",
                                reason=(
                                    "Coordinated native producer and consumer "
                                    "identity cut"
                                ),
                            ),
                        ),
                        consumer_roots=(consumer_root,),
                    ),
                )
            )
            driver = producer / "native.artifact"
            tm.ok(u.Cli.atomic_write_text_file(driver, artifact.model_dump_json()))
            before = declaration.read_bytes()
            changed = consumer.read_bytes() + b"# independent source epoch\n"
            consumer.write_bytes(changed)
            tm.fail(
                codemod.FlextInfraCodemodSemanticApply.consume_rename_plan(
                    m.Infra.ModCommand(
                        repository_root=producer, rename_plan=driver, apply=True
                    ),
                    workspace,
                )
            )
        tm.that(declaration.read_bytes(), eq=before)
        tm.that(consumer.read_bytes(), eq=changed)
        tm.fail(declaration.with_name("renamed.py").exists())
