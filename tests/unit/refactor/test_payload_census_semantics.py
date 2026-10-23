"""Native payload census candidates preserve validation and serialization inputs.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from flext_infra import c, p
from flext_infra.refactor import FlextInfraRefactorCensus
from tests import c, m, tm, u


class TestsFlextInfraPayloadCensusSemantics:
    """Exercise the existing inventory and duplicate grouping public boundaries."""

    @staticmethod
    def test_duplicate_definitions_retain_mutation_and_json_round_trip(
        tmp_path: Path,
    ) -> None:
        """Definition elements remain validated models in a mutable JSON array."""
        records = [
            m.Infra.Object(
                name="Published",
                kind="class",
                file_path=str(tmp_path / f"{module}.py"),
                line=1,
                project="demo",
            )
            for module in ("left", "right")
        ]
        group = m.Infra.DuplicateGroup(
            name=records[0].name,
            kind=records[0].kind,
            definitions=records,
        )
        tm.ok(group.definitions[0] is records[0])
        last = group.definitions.pop()
        group.definitions.insert(0, last)
        tm.ok(group.definitions[0] is records[-1])
        restored = m.Infra.DuplicateGroup.model_validate_json(group.model_dump_json())
        tm.that(restored, eq=group)
        tm.that(restored.definitions[0].file_path, eq=last.file_path)

    @staticmethod
    @pytest.mark.parametrize(
        ("change", "expected_candidate"),
        [
            ("alias", True),
            ("default", False),
            ("literal-space", False),
            ("config", False),
            ("validator", False),
            ("serializer", False),
            ("generic", False),
            ("base", False),
        ],
    )
    def test_payload_candidates_cross_names_without_claiming_equivalence(
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        change: str,
        *,
        expected_candidate: bool,
    ) -> None:
        """Different holders match only when every native declaration input matches."""
        root = Path(rope_workspace.rope_project.root.real_path)
        path = root / "payloads.py"
        default = "'a b'"
        second_default = (
            "'different'"
            if change == "default"
            else "'a  b'"
            if change == "literal-space"
            else default
        )
        validator = (
            "        @field_validator('value')\n"
            "        @classmethod\n"
            "        def normalize(cls, value: str) -> str:\n"
            "            return value.strip()\n"
            if change == "validator"
            else ""
        )
        second_validator = validator.replace("value.strip()", "value.upper()")
        serializer = (
            "        @field_serializer('value')\n"
            "        def serialize(self, value: str) -> str:\n"
            "            return value.lower()\n"
            if change == "serializer"
            else ""
        )
        second_serializer = serializer.replace("value.lower()", "value.upper()")
        base = (
            "AlternativeBase"
            if change == "base"
            else "AlternateModel"
            if change == "alias"
            else "Model"
        )
        field = "AlternateField" if change == "alias" else "Field"
        source = (
            "from __future__ import annotations\n"
            "from pydantic import BaseModel as Model, Field, ConfigDict\n"
            "from pydantic import BaseModel as AlternateModel, Field as "
            "AlternateField\n"
            "from pydantic import field_validator, field_serializer\n"
            "class AlternativeBase(Model):\n"
            "    model_config = ConfigDict(strict=True)\n"
            "class InputHolder:\n"
            f"    class Input{'[T]' if change == 'generic' else ''}(Model):\n"
            "        model_config = ConfigDict(frozen=True)\n"
            f"        value: str = Field(default={default})\n"
            + validator
            + serializer
            + "class OutputHolder:\n"
            f"    class Output{'[T: int]' if change == 'generic' else ''}({base}):\n"
            f"        model_config = ConfigDict(frozen={change != 'config'})\n"
            f"        value: str = {field}(default={second_default})\n"
            + second_validator
            + second_serializer
        )
        tm.ok(u.Cli.atomic_write_text_file(path, source))
        rope_workspace.refresh()
        objects = tuple(
            item
            for item in rope_workspace.objects(
                path,
                include_local_scopes=False,
                include_references=False,
            )
            if item.scope_path in {"InputHolder.Input", "OutputHolder.Output"}
        )
        tm.that(len(objects), eq=2)
        tm.ok(all(item.payload_fingerprint for item in objects))
        groups = FlextInfraRefactorCensus.duplicate_groups((objects,))
        candidates = tuple(group for group in groups if group.semantic_candidate)
        tm.that(bool(candidates), eq=expected_candidate)
        tm.ok(all(not group.value_identical for group in candidates))
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
        if expected_candidate:
            observed = tm.ok(
                u.Cli.run(
                    (
                        sys.executable,
                        "-B",
                        "-c",
                        (
                            "from payloads import InputHolder, OutputHolder; "
                            "left = InputHolder.Input; right = OutputHolder.Output; "
                            "assert left is not right; "
                            "assert left.model_json_schema()['title'] != "
                            "right.model_json_schema()['title']; "
                            "assert left().model_dump() == right().model_dump()"
                        ),
                    ),
                    cwd=root,
                    options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(root)}),
                ),
            )
            tm.ok(u.Cli.process_succeeded(observed.outcome))

    @staticmethod
    def test_non_pydantic_homonyms_have_no_payload_candidate(
        rope_workspace: p.Infra.RopeWorkspaceDsl,
    ) -> None:
        """A class named BaseModel cannot enter the native Pydantic candidate route."""
        path = Path(rope_workspace.rope_project.root.real_path) / "homonyms.py"
        tm.ok(
            u.Cli.atomic_write_text_file(
                path,
                "class BaseModel:\n    pass\n"
                "class InputHolder:\n"
                "    class Input(BaseModel):\n        value: str = 'same'\n"
                "class OutputHolder:\n"
                "    class Output(BaseModel):\n        value: str = 'same'\n",
            )
        )
        rope_workspace.refresh()
        objects = rope_workspace.objects(
            path,
            include_local_scopes=False,
            include_references=False,
        )
        tm.fail(any(item.payload_fingerprint for item in objects))
        tm.that(
            any(
                group.semantic_candidate
                for group in FlextInfraRefactorCensus.duplicate_groups((objects,))
            ),
            eq=False,
        )
