"""Real Rope declaration-relocation cutovers of guarded and grouped payloads.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from flext_infra import infra, p, r
from flext_infra.codegen import (
    FlextInfraCodegenLazyInit,
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenTransaction,
)
from flext_infra.codemod import FlextInfraCodemodSemanticApply, FlextInfraModGateEngine
from flext_infra.transformers import FlextInfraSemanticPublication
from tests import c, m, t, tm, u
from tests.unit.codemod.declaration_relocation_support import (
    TestsFlextInfraDeclarationRelocationSupport,
)


class TestsFlextInfraDeclarationRelocationGroups:
    """Exercise guarded, grouped, and composed declaration relocation cutovers."""

    @staticmethod
    @pytest.mark.parametrize("guard", ["TYPE_CHECKING", "Checking"])
    def test_unrelated_type_checking_guard_refuses_without_mutation(
        tmp_path: Path,
        guard: str,
    ) -> None:
        """A same-spelled local flag is not the typing module's guard identity."""
        root, sources = TestsFlextInfraDeclarationRelocationSupport.seed(
            tmp_path,
            body="amount: 'Amount'",
        )
        origin = next(path for path in sources if path.parent.name == "_utilities")
        sources[origin] = (
            f"{guard} = False\nif {guard}:\n"
            "    from decimal import Decimal as Amount\n" + sources[origin]
        )
        origin.write_text(sources[origin], encoding="utf-8")
        with (
            infra.rope_workspace(root) as rope,
            pytest.raises(ValueError, match=r"unresolved/outer dependency.*Amount"),
        ):
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                rope_workspace=rope,
                sources=sources,
            )
        for path, source in sources.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    @pytest.mark.parametrize("refused", ["destination", "exposure"])
    @pytest.mark.parametrize("independent_group", [False, True])
    def test_failed_dependent_group_preserves_independent_public_runtime(
        tmp_path: Path,
        refused: str,
        *,
        independent_group: bool,
    ) -> None:
        """A destination refusal recovers only its invocation's dependent group."""
        root, sources = TestsFlextInfraDeclarationRelocationSupport.seed(
            tmp_path,
            body="count: int = Field(default=3)",
        )
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                    rope_workspace=rope,
                    sources=sources,
                )
            )
        target = next(path for path in sources if path.parent.name == "_models")
        package = target.parent.parent
        blocked = target if refused == "destination" else target.parent / "__init__.py"
        if refused == "exposure":
            blocked.write_text("", encoding="utf-8")
            sources[blocked] = ""
        independent = root / "independent.py"
        independent.write_text("VALUE = 'before'\n", encoding="utf-8")
        independent_before = tm.ok(
            u.Cli.atomic_read_binary_file_state(independent, required=True)
        )
        plans = [
            m.Infra.CodegenFilePlan(
                project=root,
                path=independent,
                before=independent_before,
                desired_content=b"VALUE = 'after'\n",
                desired_mode=independent_before.mode,
                dependency_group=independent.stem if independent_group else None,
            )
        ]
        for edit in edits:
            before = tm.ok(
                u.Cli.atomic_read_binary_file_state(edit.file_path, required=True)
            )
            plans.append(
                m.Infra.CodegenFilePlan(
                    project=root,
                    path=edit.file_path,
                    before=before,
                    desired_content=edit.updated_source.encode("utf-8"),
                    desired_mode=before.mode,
                    dependency_group=package.name,
                )
            )
        if refused == "exposure":
            exposure = tm.ok(
                FlextInfraCodegenLazyInit(repository_root=root).plan_files()
            )
            plans.extend(
                item.model_copy(update={"dependency_group": package.name})
                for item in exposure.files
                if item.path == blocked
            )
        transaction = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root)
        )
        receipts: list[m.Infra.CodegenStagedFile] = []

        def refuse_destination(
            session: m.Infra.CodegenTransactionSession,
            _staged: t.VariadicTuple[m.Infra.CodegenStagedFile],
        ) -> p.Result[m.Infra.CodegenTransactionSession]:
            before = tm.ok(u.Cli.atomic_read_binary_file_state(blocked, required=True))
            tm.ok(
                u.Cli.atomic_write_binary_file_guarded(
                    before,
                    sources[blocked].encode("utf-8")
                    + b"\n# authored destination change\n",
                    permission_mode=before.mode,
                )
            )
            return r[m.Infra.CodegenTransactionSession].ok(session)

        def publish(scope: Path) -> p.Result[t.VariadicTuple[Path]]:
            started = transaction.begin_files_locked(scope, {f"@{root.name}": root}, ())
            if started.failure:
                return r[t.VariadicTuple[Path]].from_failure(started)
            admitted = transaction.append_phase_locked(
                started.value,
                c.Infra.CodegenStagedFilePhase.SEMANTIC,
                tuple(plans),
                publication_policy=m.Infra.CodegenPhasePublicationPolicy(
                    directories=(), staged_validator=refuse_destination
                ),
            )
            if admitted.failure:
                return r[t.VariadicTuple[Path]].from_failure(admitted)
            return transaction.commit_locked(admitted.value, published_files=receipts)

        failed = transaction.run_files_locked({f"@{root.name}": root}, publish)
        tm.fail(failed)
        tm.that(independent.read_text(encoding="utf-8"), eq="VALUE = 'after'\n")
        tm.that(
            blocked.read_text(encoding="utf-8"),
            eq=sources[blocked] + "\n# authored destination change\n",
        )
        for path, source in sources.items():
            if path != blocked:
                tm.that(path.read_text(encoding="utf-8"), eq=source)
        tm.that(tuple(item.before.path for item in receipts), eq=(independent,))
        consumer = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-B",
                    "-c",
                    (
                        f"from {package.name}.consumer import build; "
                        f"from {package.name} import m; "
                        "from independent import VALUE; "
                        "assert not hasattr(m, 'Payload'); "
                        "assert build().count == 3; assert VALUE == 'after'"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env={"PYTHONPATH": str(package.parent) + ":" + str(root)}
                ),
            )
        )
        tm.that(u.Cli.process_succeeded(consumer.outcome), eq=True)

    @staticmethod
    @pytest.mark.parametrize("accepted", [False, True])
    def test_public_group_cutover_is_accepted_or_recovers_on_consumer_rejection(
        tmp_path: Path,
        *,
        accepted: bool,
    ) -> None:
        """A fresh consumer accepts the full cutover, never a partial runtime."""
        root, sources = TestsFlextInfraDeclarationRelocationSupport.seed(
            tmp_path,
            body="count: int = Field(default=3)",
        )
        before_sources = {path: path.read_bytes() for path in root.rglob("*.py")}
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                    rope_workspace=rope,
                    sources=sources,
                )
            )
        target = next(path for path in sources if path.parent.name == "_models")
        package = target.parent.parent
        plans: list[m.Infra.SemanticFilePlan] = []
        for edit in edits:
            before = tm.ok(
                u.Cli.atomic_read_binary_file_state(edit.file_path, required=True)
            )
            source = edit.updated_source
            if not accepted and edit.file_path == target:
                source = source.replace("Field(default=3)", "Field(default=7)")
            plans.append(
                m.Infra.SemanticFilePlan(
                    project=root,
                    path=edit.file_path,
                    before=before,
                    desired_content=source.encode("utf-8"),
                    desired_mode=before.mode,
                    changes=("declaration relocation",),
                )
            )

        def consume(candidate_root: Path) -> p.Result[bool]:
            result = u.Cli.run(
                (
                    sys.executable,
                    "-B",
                    "-c",
                    (
                        f"from {package.name} import m; "
                        f"from {package.name}.consumer import build; "
                        "assert build().__class__ is m.Payload; "
                        "assert build().count == 3; "
                        "assert m.Payload.model_validate({'count': 4}).model_dump() == "
                        "{'count': 4}"
                    ),
                ),
                cwd=candidate_root,
                options=m.Cli.ProcessOptions(
                    env={
                        "PYTHONPATH": str(
                            candidate_root / package.parent.relative_to(root)
                        ),
                    },
                ),
            )
            if result.failure:
                return r[bool].from_failure(result)
            return r[bool].ok(u.Cli.process_succeeded(result.value.outcome))

        result = FlextInfraSemanticPublication.publish_semantic_file_plans(
            plans,
            repository_root=root,
            options=m.Infra.SemanticPublicationOptions(
                projection_roots=(root,),
                dependency_group=package.name,
                validator=consume,
            ),
        )
        if accepted:
            tm.ok(result)
            tm.that(tm.ok(consume(root)), eq=True)
            with infra.rope_workspace(root) as rope:
                tm.that(
                    tm.ok(
                        u.Infra.plan_semantic_cutover(
                            c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                            rope_workspace=rope,
                            sources={
                                path: path.read_text(encoding="utf-8")
                                for path in sources
                            },
                        )
                    ),
                    eq=(),
                )
        else:
            tm.fail(result)
            for path, content in before_sources.items():
                tm.that(path.read_bytes(), eq=content)
            original = tm.ok(
                u.Cli.run(
                    (
                        sys.executable,
                        "-B",
                        "-c",
                        (
                            f"from {package.name}.consumer import build; "
                            "assert build().count == 3"
                        ),
                    ),
                    cwd=root,
                    options=m.Cli.ProcessOptions(
                        env={"PYTHONPATH": str(package.parent)}
                    ),
                )
            )
            tm.that(u.Cli.process_succeeded(original.outcome), eq=True)

    @staticmethod
    def test_real_scan_selects_the_immutable_declaration_phase(tmp_path: Path) -> None:
        """Test real scan selects the immutable declaration phase."""
        root, sources = TestsFlextInfraDeclarationRelocationSupport.seed(tmp_path)
        preflight = FlextInfraModGateEngine.scan(root, fix=False).unwrap()
        phase = c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION
        rule_id = c.Infra.SEMANTIC_CUTOVER_RULE_IDS[phase]
        tm.that(
            any(finding.rule_id == rule_id for finding in preflight.entries),
            eq=True,
        )
        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                phase,
                rope_workspace=rope,
                sources=sources,
                findings=preflight.entries,
            )
            tm.ok(planned)
            tm.that(len(planned.value), eq=3)
        for path, source in sources.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    @pytest.mark.parametrize("nested_local", [False, True])
    def test_validator_and_computed_field_runtime_preserved(
        tmp_path: Path,
        *,
        nested_local: bool,
    ) -> None:
        """Test validator and computed field runtime preserved.

        Raises:
            RuntimeError: If Published validator has no loader.

        """
        root, sources = TestsFlextInfraDeclarationRelocationSupport.seed(
            tmp_path,
            body=(
                "value: int = 1\n"
                "        @field_validator('value')\n"
                "        @classmethod\n"
                "        def normalize(cls, value: int) -> int:\n"
                + (
                    "            scratch = [item * 2 for item in (value,)]\n"
                    "            return scratch[0]\n"
                    if nested_local
                    else "            return value * 2\n"
                )
                + "        @computed_field\n"
                "        @property\n"
                "        def derived(self) -> int:\n"
                "            return self.value + 1"
            ),
        )
        origin = next(
            path
            for path in sources
            if path.parent.name
            == u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        )
        sources[origin] = (
            "from pydantic import field_validator, computed_field\n" + sources[origin]
        )
        origin.write_text(sources[origin], encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                rope_workspace=rope,
                sources=sources,
            )
            tm.ok(planned)
            target = next(
                edit
                for edit in planned.value
                if edit.file_path.parent.name
                == u.Infra.facade_family_declared_by(c.Infra.MODELS_PY).directory
            )
        published = tmp_path / "published_validator.py"
        published.write_text(target.updated_source, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("published_validator", published)
        if spec is None or spec.loader is None:
            msg = "Published validator has no loader"
            raise RuntimeError(msg)
        loaded = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(loaded)
        owner = f"{u.derive_class_stem(root.name)}ModelsPayload"
        tm.that(
            getattr(loaded, owner).Payload.model_validate({"value": 3}).model_dump(),
            eq={"value": 6, "derived": 7},
        )

    @staticmethod
    def test_generated_sources_refuse_the_whole_plan(tmp_path: Path) -> None:
        """Test unsafe sources refuse the whole plan."""
        root, sources = TestsFlextInfraDeclarationRelocationSupport.seed(tmp_path)
        path = next(path for path in sources if path.name == "consumer.py")
        sources[path] = c.Infra.AUTOGEN_HEADERS[0] + "\n" + sources[path]
        expected = "generated consumer"
        path.write_text(sources[path], encoding="utf-8")
        with (
            infra.rope_workspace(root) as rope,
            pytest.raises(ValueError, match=expected),
        ):
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                rope_workspace=rope,
                sources=sources,
            )
        for path, source in sources.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    def test_unresolved_source_owner_is_a_finding_not_a_crash(
        tmp_path: Path,
    ) -> None:
        """An unexpected outer owner is reported while resolvable moves apply."""
        root, sources = TestsFlextInfraDeclarationRelocationSupport.seed(
            tmp_path,
            variants=frozenset({"stray"}),
        )
        stem = u.derive_class_stem(root.name)
        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                rope_workspace=rope,
                sources=sources,
            )
            findings = u.Infra.declaration_relocation_findings(rope, sources)
        tm.ok(planned)
        tm.that(len(planned.value), eq=3)
        unresolved = tuple(
            finding
            for finding in findings
            if finding.declaration == f"{stem}StrayHolder.Stray"
        )
        tm.that(len(unresolved), eq=1)
        tm.that(unresolved[0].expected_owner, eq=f"{stem}UtilitiesPayload")
        tm.that(bool(unresolved[0].reason), eq=True)
        tm.that(
            all(
                finding.file_path in sources and finding.reason for finding in findings
            ),
            eq=True,
        )
        for path, source in sources.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    @pytest.mark.slow
    def test_uncomposed_model_owner_preserves_findings_and_failed_publication(
        tmp_path: Path,
    ) -> None:
        """An unresolved owner stays visible; failed candidate gates publish nothing."""
        root, sources = TestsFlextInfraDeclarationRelocationSupport.seed(
            tmp_path,
            variants=frozenset({"uncomposed"}),
        )
        stem = u.derive_class_stem(root.name)
        origin = next(
            path
            for path in sources
            if path.parent.name
            == u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        )
        tm.that(sources[origin], lacks="from __future__ import annotations")
        preflight = FlextInfraModGateEngine.authored(
            FlextInfraModGateEngine.scan(root, fix=False).unwrap(),
        )
        tm.that(
            any(
                finding.rule_id == "require-future-annotations"
                for finding in preflight.entries
            ),
            eq=True,
        )
        with infra.rope_workspace(root) as rope:
            findings = FlextInfraCodemodSemanticApply.relocation_findings(
                root,
                preflight,
                rope,
            )
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                rope_workspace=rope,
                sources=sources,
            )
            tm.ok(planned)
            tm.that(planned.value, empty=True)
            applied = FlextInfraCodemodSemanticApply.apply(
                root,
                preflight,
                rope,
                source_preview=infra.source_preview(root),
                workspace_factory=infra.rope_workspace,
            )
        tm.that(len(findings), eq=1)
        tm.that(findings[0].file_path, eq=origin.resolve())
        tm.that(findings[0].declaration, eq=f"{stem}UtilitiesPayload.Payload")
        tm.that(findings[0].expected_owner, has="one authored model owner")
        tm.that(findings[0].reason, has="found []")
        tm.fail(applied)
        tm.that(applied.error, has="quality checks failed")
        for path, source in sources.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    @pytest.mark.parametrize("split", [False, True])
    def test_public_preset_dependency_moves_without_self_facade_cycle(
        tmp_path: Path,
        *,
        split: bool,
    ) -> None:
        """The public model consumer loads the relocated payload and its preset."""
        root, sources = TestsFlextInfraDeclarationRelocationSupport.seed(tmp_path)
        stem = u.derive_class_stem(root.name)
        target = next(path for path in sources if path.parent.name == "_models")
        owner = f"{stem}ModelsPayload"
        sources[target] = (
            "from pydantic import BaseModel, Field\n"
            f"class {owner}:\n    Field = Field\n"
            "    class Preset(BaseModel):\n        pass\n"
            f"__all__ = ['{owner}']\n"
        )
        origin = next(path for path in sources if path.parent.name == "_utilities")
        sources[origin] = f"from {target.parent.parent.name} import m\n" + sources[
            origin
        ].replace("class Payload(PayloadBase)", "class Payload(m.Preset)").replace(
            "Field(default=", "m.Field(default="
        )
        sources[origin] = sources[origin].replace(
            "\ndef local():",
            "\n    @staticmethod\n    def consume(value: Payload) -> str:\n"
            "        return value.value\n\ndef local():",
        )
        if split:
            parts = origin.parent / "_payload_parts"
            parts.mkdir()
            (parts / "__init__.py").write_text("", encoding="utf-8")
            sources[parts / "payload_part.py"] = sources.pop(origin)
            sources[origin] = (
                f"from {target.parent.parent.name}._utilities."
                "_payload_parts.payload_part "
                f"import {stem}UtilitiesPayload\n"
                f"__all__ = ['{stem}UtilitiesPayload']\n"
            )
            sources[target.parent.parent / "utilities.py"] = (
                f"from {target.parent.parent.name}._utilities.payload "
                f"import {stem}UtilitiesPayload\n"
                f"class {stem}Utilities({stem}UtilitiesPayload):\n    pass\n"
                f"u = {stem}Utilities\n__all__ = ['u', '{stem}Utilities']\n"
            )
        for path, source in sources.items():
            path.write_text(source, encoding="utf-8")
        tm.that(u.Tests.run_lazy_init(root), eq=0)
        with infra.rope_workspace(root) as rope:
            planned = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                    rope_workspace=rope,
                    sources=sources,
                ),
            )
        for edit in planned:
            edit.file_path.write_text(edit.updated_source, encoding="utf-8")
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {target.parent.parent.name} import m; "
                        f"from {target.parent.parent.name}._utilities.payload "
                        f"import {stem}UtilitiesPayload; "
                        "from typing import get_type_hints; "
                        f"assert get_type_hints({stem}UtilitiesPayload.consume)"
                        "['value'] is m.Payload; "
                        "assert issubclass(m.Payload, m.Preset); "
                        "assert m.Payload.model_validate("
                        "{'value': 'consumer'}).value == 'consumer'"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env={"PYTHONPATH": str(target.parent.parent.parent)}
                ),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True)

    @staticmethod
    @pytest.mark.parametrize("competing", [False, True])
    def test_composed_preset_identity_resolves_local_model_owner(
        tmp_path: Path,
        *,
        competing: bool,
    ) -> None:
        """Unrelated composition parts do not compete with the preset owner."""
        root, sources = TestsFlextInfraDeclarationRelocationSupport.seed(tmp_path)
        stem = u.derive_class_stem(root.name)
        target = next(path for path in sources if path.parent.name == "_models")
        owner = f"{stem}ModelsPayload"
        sources[target] = (
            "from pydantic import BaseModel\n"
            f"class {owner}:\n    class Preset(BaseModel):\n        pass\n"
            f"__all__ = ['{owner}']\n"
        )
        origin = next(path for path in sources if path.parent.name == "_utilities")
        sources[origin] = (
            f"from {target.parent.parent.name}._models.payload import {owner}\n"
            + sources[origin].replace(
                "class Payload(PayloadBase)", f"class Payload({owner}.Preset)"
            )
        )
        other = target.with_name("other.py")
        other_owner = f"{stem}ModelsOther"
        sources[other] = (
            f"from {target.parent.parent.name}._models.payload import {owner}\n"
            f"class {other_owner}{f'({owner})' if competing else ''}:\n    pass\n"
            f"__all__ = ['{other_owner}']\n"
        )
        facade = target.parent.parent / "models.py"
        sources[facade] = (
            f"from {target.parent.parent.name}._models.other import {other_owner}\n"
            + sources[facade].replace(f"({owner})", f"({owner}, {other_owner})")
        )
        for path, source in sources.items():
            path.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            findings = u.Infra.declaration_relocation_findings(rope, sources)
            planned = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                    rope_workspace=rope,
                    sources=sources,
                )
            )
        payload_findings = tuple(
            finding
            for finding in findings
            if finding.declaration == f"{stem}UtilitiesPayload.Payload"
        )
        tm.that(bool(payload_findings), eq=competing)
        tm.that(
            all(
                finding.file_path in sources and finding.reason for finding in findings
            ),
            eq=True,
        )
        tm.that(bool(planned), eq=not competing)
        if competing:
            return
        proposed = dict(sources)
        proposed.update({edit.file_path: edit.updated_source for edit in planned})
        for path, source in proposed.items():
            path.write_text(source, encoding="utf-8")
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {target.parent.parent.name} import m; "
                        "from pydantic import ValidationError; "
                        "assert m.Payload.model_validate({'value': 'consumer'}).value "
                        "== 'consumer'\n"
                        "try:\n    m.Payload.model_validate({'value': []})\n"
                        "except ValidationError:\n    print('rejected')\n"
                        "else:\n    raise AssertionError('invalid payload accepted')\n"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env={"PYTHONPATH": str(target.parent.parent.parent)},
                ),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True, msg=result.stderr)
        tm.that(result.stdout.strip(), eq="rejected")
