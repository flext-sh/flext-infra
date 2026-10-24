"""Real public semantic file-plan publication, identity and rejection contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from functools import partial
from pathlib import Path

import pytest

from flext_infra import codemod, config, transformers
from tests import c, m, p, r, t, tm, u


class TestsFlextInfraSemanticPublicationPlans:
    """Admit complete semantic file plans and refuse stale or foreign identity."""

    def test_same_byte_foreign_replacement_of_unchanged_destination_is_rejected(
        self,
        mod_workspace: Path,
    ) -> None:
        """An unchanged plan rejects a foreign replacement with identical bytes."""
        u.Tests.run_native_callable(self._scenario_foreign_destination, mod_workspace)

    @staticmethod
    def _scenario_foreign_destination(mod_workspace: Path) -> None:
        """An unchanged plan never authorizes a foreign inode with equal bytes."""
        first, second = TestsFlextInfraSemanticPublicationPlans._plans(mod_workspace)
        unchanged = second.model_copy(
            update={"desired_content": second.before.content},
        )
        foreign = second.path.with_suffix(".foreign")
        foreign.write_bytes(tm.not_none(second.before.content))
        foreign.chmod(tm.not_none(second.before.mode))
        foreign.replace(second.path)
        foreign_state = tm.ok(
            u.Cli.atomic_read_binary_file_state(second.path, required=True),
        )
        tm.fail(
            transformers.FlextInfraSemanticPublication.publish_semantic_file_plans(
                (first, unchanged),
                repository_root=mod_workspace,
            ),
        )
        tm.that(first.path.read_bytes(), eq=first.before.content)
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(second.path, required=True)),
            eq=foreign_state,
        )

    @staticmethod
    def _plans(
        root: Path,
        names: t.StrTuple = ("first.py", "second.py"),
    ) -> t.VariadicTuple[m.Infra.SemanticFilePlan]:
        plans: list[m.Infra.SemanticFilePlan] = []
        for name in names:
            path = root / name
            u.Cli.atomic_write_text_file(path, 'value = "before"\n').unwrap()
            before = u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            plans.append(
                m.Infra.SemanticFilePlan(
                    project=root,
                    path=path,
                    before=before,
                    desired_content=b'value = "after"\n',
                    desired_mode=before.mode,
                    changes=("publication contract",),
                ),
            )
        return tuple(plans)

    @pytest.mark.parametrize("linked", [False, True])
    def test_changed_middle_identity_rejects_before_other_publications(
        self,
        mod_workspace: Path,
        *,
        linked: bool,
    ) -> None:
        """A changed middle-plan identity rejects the batch before any publication.

        The identity change is either a replaced file or a link.

        """
        u.Tests.run_native_callable(
            self._scenario_middle_identity,
            mod_workspace,
            linked=linked,
        )

    @staticmethod
    def _scenario_middle_identity(mod_workspace: Path, *, linked: bool) -> None:
        """Complete admission rejects stale identity before any file is changed."""
        first, second, third = TestsFlextInfraSemanticPublicationPlans._plans(
            mod_workspace,
            ("first.py", "second.py", "third.py"),
        )
        if linked:
            actual = second.path.with_suffix(".actual")
            second.path.rename(actual)
            second.path.symlink_to(actual)
        else:
            u.Cli.atomic_write_text_file(second.path, 'value = "concurrent"\n').unwrap()
        observed = second.path.read_bytes()
        tm.fail(
            transformers.FlextInfraSemanticPublication.publish_semantic_file_plans(
                (first, second, third),
                repository_root=mod_workspace,
            ),
        )
        tm.that(first.path.read_bytes(), eq=first.before.content)
        tm.that(third.path.read_bytes(), eq=third.before.content)
        tm.that(second.path.read_bytes(), eq=observed)

    def test_semantic_publication_changes_authored_initializer(
        self,
        mod_workspace: Path,
    ) -> None:
        """An explicit semantic plan changes an authored initializer."""
        u.Tests.run_native_callable(self._scenario_authored_initializer, mod_workspace)

    @staticmethod
    def _scenario_authored_initializer(mod_workspace: Path) -> None:
        """An explicit semantic plan owns its authored initializer transformation."""
        package = mod_workspace / c.Infra.DEFAULT_SRC_DIR / mod_workspace.name
        initializer = package / c.Infra.INIT_PY
        source = 'VALUE = "before"\n__all__ = ("VALUE",)\n'
        initializer.write_text(source, encoding="utf-8")
        before = tm.ok(
            u.Cli.atomic_read_binary_file_state(initializer, required=True),
        )
        plan = m.Infra.SemanticFilePlan(
            project=mod_workspace,
            path=initializer,
            before=before,
            desired_content=source.replace('"before"', '"after"').encode(),
            desired_mode=before.mode,
        )
        published = tm.ok(
            transformers.FlextInfraSemanticPublication.publish_semantic_file_plans(
                (plan,),
                repository_root=mod_workspace,
            ),
        )
        tm.that(published, eq=(initializer,))
        consumer = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    f"from {mod_workspace.name} import VALUE; assert VALUE == 'after'",
                ),
                cwd=mod_workspace,
                options=m.Cli.ProcessOptions(
                    env={
                        c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(package.parent),
                    },
                ),
            ),
        )
        tm.ok(u.Cli.process_succeeded(consumer.outcome))

    def test_generated_later_plan_rejects_authored_earlier_plan(
        self,
        mod_workspace: Path,
    ) -> None:
        """A generated later plan rejects an authored earlier plan."""
        u.Tests.run_native_callable(self._scenario_generated_plan, mod_workspace)

    @staticmethod
    def _scenario_generated_plan(mod_workspace: Path) -> None:
        """Test generated later plan rejects authored earlier plan."""
        first, second = TestsFlextInfraSemanticPublicationPlans._plans(mod_workspace)
        u.Cli.atomic_write_text_file(
            second.path,
            f'{c.Infra.AUTOGEN_HEADERS[0]}\nvalue = "before"\n',
        ).unwrap()
        generated = second.model_copy(
            update={
                "before": u.Cli.atomic_read_binary_file_state(
                    second.path,
                    required=True,
                ).unwrap(),
            },
        )
        tm.fail(
            transformers.FlextInfraSemanticPublication.publish_semantic_file_plans(
                (first, generated),
                repository_root=mod_workspace,
            ),
            has="canonical generator repair",
        )
        tm.that(first.path.read_bytes(), eq=first.before.content)

    def test_none_content_preserves_the_file(self, mod_workspace: Path) -> None:
        """A plan with no desired content or mode preserves the file."""
        u.Tests.run_native_callable(self._scenario_none_content, mod_workspace)

    @staticmethod
    def _scenario_none_content(mod_workspace: Path) -> None:
        """Test none content preserves the file."""
        first, _ = TestsFlextInfraSemanticPublicationPlans._plans(mod_workspace)
        noop = first.model_copy(update={"desired_content": None, "desired_mode": None})
        tm.that(
            tm.ok(
                transformers.FlextInfraSemanticPublication.publish_semantic_file_plans(
                    (noop,),
                    repository_root=mod_workspace,
                ),
            ),
            eq=(),
        )
        tm.that(first.path.read_bytes(), eq=first.before.content)

    def test_declared_template_input_is_not_its_generated_projection(
        self,
        mod_workspace: Path,
    ) -> None:
        """A declared template input is not its generated projection.

        An arbitrary template is never treated as a projection input.

        """
        u.Tests.run_native_callable(self._scenario_template_input, mod_workspace)

    @staticmethod
    def _scenario_template_input(mod_workspace: Path) -> None:
        """Test declared template input is not its generated projection."""
        template_root = mod_workspace / "templates"
        template_root.mkdir()
        declared = template_root / "declared.j2"
        arbitrary = template_root / "arbitrary.j2"
        projection = mod_workspace / "projection.py"
        content = f"{c.Infra.AUTOGEN_HEADERS[0]}\nbefore\n"
        for path in (declared, arbitrary, projection):
            path.write_text(content, encoding="utf-8")
        entry = next(
            item
            for item in config.Infra.codegen.templates.entries
            if item.source is not None
        )
        policy = config.Infra.codegen.model_copy(
            update={
                "templates": config.Infra.codegen.templates.model_copy(
                    update={
                        "root": template_root,
                        "entries": (
                            entry.model_copy(update={"source": Path(declared.name)}),
                        ),
                    },
                ),
            },
        )
        plans = tuple(
            m.Infra.SemanticFilePlan(
                project=mod_workspace,
                path=path,
                before=tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True)),
                desired_content=content.replace("before", "after").encode(),
                desired_mode=path.stat().st_mode & 0o7777,
            )
            for path in (declared, arbitrary, projection)
        )
        for denied in plans[1:]:
            tm.fail(
                transformers.FlextInfraSemanticPublication.publish_semantic_file_plans(
                    (plans[0], denied),
                    repository_root=mod_workspace,
                    codegen=policy,
                ),
                has="canonical generator repair",
            )
            tm.that(declared.read_text(), eq=content)
            tm.that(denied.path.read_text(), eq=content)
        tm.ok(
            transformers.FlextInfraSemanticPublication.publish_semantic_file_plans(
                (plans[0],),
                repository_root=mod_workspace,
                codegen=policy,
            ),
        )
        rendered = tm.ok(
            u.Cli.template_render(declared, m.Infra.StaticTextRenderSpec()),
        )
        tm.that(rendered, has="after")
        tm.that(arbitrary.read_text(), eq=content)
        tm.that(projection.read_text(), eq=content)

    def test_real_formatter_rejects_later_source_before_any_publication(
        self,
        mod_workspace: Path,
    ) -> None:
        """A later source rejected by the real formatter stops the whole batch.

        No file is published.

        """
        u.Tests.run_native_callable(self._scenario_formatter_rejection, mod_workspace)

    @staticmethod
    def _scenario_formatter_rejection(mod_workspace: Path) -> None:
        """Test real formatter rejects later source before any publication."""
        plans = TestsFlextInfraSemanticPublicationPlans._plans(mod_workspace)
        edits = tuple(
            m.Infra.SemanticMigrationEdit(
                file_path=plan.path,
                original_source=plan.path.read_text(),
                updated_source='value="after"\n' if index == 0 else "value = (\n",
                changes=("formatter preflight",),
            )
            for index, plan in enumerate(plans)
        )
        tm.fail(
            codemod.FlextInfraCodemodSemanticApply.publish_planned_edits(
                mod_workspace, edits
            )
        )
        for plan in plans:
            tm.that(plan.path.read_bytes(), eq=plan.before.content)

    def test_real_semantic_caller_commits_normalized_source_idempotently(
        self,
        mod_workspace: Path,
    ) -> None:
        """The real semantic caller commits normalized source idempotently.

        A repeat changes nothing further.

        """
        u.Tests.run_native_callable(self._scenario_normalized_caller, mod_workspace)

    @staticmethod
    def _scenario_normalized_caller(mod_workspace: Path) -> None:
        """Test real semantic caller commits normalized source idempotently."""
        first, _ = TestsFlextInfraSemanticPublicationPlans._plans(mod_workspace)
        edit = m.Infra.SemanticMigrationEdit(
            file_path=first.path,
            original_source=first.path.read_text(),
            updated_source='value="after"\n',
            changes=("semantic normalization",),
        )
        tm.ok(
            codemod.FlextInfraCodemodSemanticApply.publish_planned_edits(
                mod_workspace,
                (edit,),
            )
        )
        published = first.path.read_text()
        tm.that(published, has="after")
        tm.that(published, lacks="before")
        repeated = edit.model_copy(
            update={"original_source": published, "updated_source": published},
        )
        tm.ok(
            codemod.FlextInfraCodemodSemanticApply.publish_planned_edits(
                mod_workspace,
                (repeated,),
            )
        )
        tm.that(first.path.read_text(), eq=published)

    @staticmethod
    def _creation(mod_workspace: Path) -> m.Infra.SemanticMigrationEdit:
        """Declare one new module beside the fixture plans (absent before).

        Returns:
            The creation edit whose original source is ``None``.

        """
        first, _ = TestsFlextInfraSemanticPublicationPlans._plans(mod_workspace)
        return m.Infra.SemanticMigrationEdit(
            file_path=first.path.with_name("created_family.py"),
            original_source=None,
            updated_source='value = "created"\n',
            changes=("semantic creation",),
        )

    def test_creation_publishes_an_absent_destination(
        self,
        mod_workspace: Path,
    ) -> None:
        """A ``None`` original creates the module when its destination is absent."""
        edit = self._creation(mod_workspace)
        tm.ok(
            codemod.FlextInfraCodemodSemanticApply.publish_planned_edits(
                mod_workspace, (edit,)
            )
        )
        tm.that(edit.file_path.read_text(), has='value = "created"')

    def test_creation_refuses_an_existing_destination(
        self,
        mod_workspace: Path,
    ) -> None:
        """A destination that already exists at publish fails and stays intact."""
        edit = self._creation(mod_workspace)
        edit.file_path.write_text('value = "foreign"\n', encoding=c.DEFAULT_ENCODING)
        tm.fail(
            codemod.FlextInfraCodemodSemanticApply.publish_planned_edits(
                mod_workspace, (edit,)
            ),
            has=str(edit.file_path),
        )
        tm.that(edit.file_path.read_text(), eq='value = "foreign"\n')

    def test_creation_refuses_a_destination_created_concurrently(
        self,
        mod_workspace: Path,
    ) -> None:
        """A destination created after the absent snapshot never gets overwritten."""
        edit = self._creation(mod_workspace)
        tm.fail(
            codemod.FlextInfraCodemodSemanticApply.publish_planned_edits(
                mod_workspace,
                (edit,),
                validator=partial(self._concurrent_creator, edit.file_path),
            ),
            has=edit.file_path.name,
        )
        tm.that(edit.file_path.read_text(), eq='value = "concurrent"\n')

    @staticmethod
    def _concurrent_creator(destination: Path, _candidate_root: Path) -> p.Result[bool]:
        """Create the live destination while the candidate is being accepted.

        Returns:
            Acceptance of the candidate, after the concurrent creation.

        """
        destination.write_text('value = "concurrent"\n', encoding=c.DEFAULT_ENCODING)
        return r[bool].ok(value=True)
