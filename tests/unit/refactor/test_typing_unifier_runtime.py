"""Public runtime checks for lexical typing rewrites and preserved data."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest
from flext_tests import tm

from flext_infra import c, infra, u
from flext_infra.transformers.typing_unifier import FlextInfraRefactorTypingUnifier

if TYPE_CHECKING:
    from pathlib import Path


class TestsTypingUnifierRuntime:
    """Validate transformed consumers through imports and get_type_hints."""

    def test_aliased_typing_preserves_metadata_and_broad_types(
        self, tmp_path: Path
    ) -> None:
        """Brackets, commas and Unicode in metadata remain data at runtime."""
        source = f"""from {c.Infra.PKG_CORE_UNDERSCORE} import t
from typing import Annotated as A, Literal as L, Any as Payload
import typing as typing_module

TEXT = "str | int | float | bool; object; typing.Any; ] café, ☃"

def consume(entrée: A[list[object], "] object, café ☃"], kind: L["] object, café ☃"], payload: Payload) -> object:
    return payload

def quoted(value: 'A[list[object], "] object, café ☃"]') -> typing_module.Any:
    return value
"""
        transformer = FlextInfraRefactorTypingUnifier(
            canonical_map=c.Infra.TYPING_INLINE_UNION_CANONICAL_MAP
        )
        updated, changes = transformer.apply_to_source(source)
        tm.that(bool(changes), eq=True)
        (tmp_path / "typing_consumer.py").write_text(updated, encoding="utf-8")
        probe = f"""from typing import Any, get_args, get_type_hints
from flext_core import cli
from {c.Infra.PKG_CORE_UNDERSCORE} import t
from typing_consumer import TEXT, consume, quoted
hints = get_type_hints(consume, include_extras=True)
quoted_hints = get_type_hints(quoted, include_extras=True)
cli.print(get_args(hints["entrée"])[0] == t.SequenceOf[object])
cli.print(get_args(hints["entrée"])[1])
cli.print(get_args(hints["kind"])[0])
cli.print(hints["payload"] is Any, hints["return"] is object, quoted_hints["return"] is Any)
cli.print(get_args(quoted_hints["value"])[1])
cli.print(TEXT)
"""
        outcome = tm.ok(u.Cli.run([sys.executable, "-c", probe], cwd=tmp_path))
        tm.that(
            outcome.stdout.splitlines(),
            eq=[
                "True",
                "] object, café ☃",
                "] object, café ☃",
                "True True True",
                "] object, café ☃",
                "str | int | float | bool; object; typing.Any; ] café, ☃",
            ],
        )
        stable, repeat_changes = transformer.apply_to_source(updated)
        tm.that(stable, eq=updated)
        tm.that(repeat_changes, eq=[])

    def test_shadowed_builtin_keeps_its_runtime_identity(self, tmp_path: Path) -> None:
        """A local class named list is not the builtin container."""
        source = """from typing import Any

class list[T]:
    pass

def consume(value: list[object], payload: Any) -> object:
    return payload
"""
        transformer = FlextInfraRefactorTypingUnifier(
            canonical_map=c.Infra.TYPING_INLINE_UNION_CANONICAL_MAP
        )
        updated, changes = transformer.apply_to_source(source)
        tm.that(updated, eq=source)
        tm.that(changes, eq=[])
        (tmp_path / "typing_homonym.py").write_text(updated, encoding="utf-8")
        probe = """from typing import Any, get_origin, get_type_hints
from flext_core import cli
from typing_homonym import consume, list
hints = get_type_hints(consume)
cli.print(get_origin(hints["value"]) is list, hints["payload"] is Any, hints["return"] is object)
"""
        outcome = tm.ok(u.Cli.run([sys.executable, "-c", probe], cwd=tmp_path))
        tm.that(outcome.stdout.strip(), eq="True True True")

    @pytest.mark.parametrize(
        ("declaration", "probe"),
        [
            (
                "type Number = int | float\n",
                "from pydantic import TypeAdapter\nfrom deferred_consumer import Number\nprint(TypeAdapter(Number).validate_json('1.25'))\n",
            ),
            (
                f"from {c.Infra.PKG_CORE_UNDERSCORE} import m\nclass Number(m.BaseModel):\n    value: int | float\n",
                "from deferred_consumer import Number\nprint(Number.model_validate_json('{\"value\": 1.25}').value)\n",
            ),
        ],
    )
    def test_deferred_import_cannot_replace_a_runtime_union(
        self, tmp_path: Path, declaration: str, probe: str
    ) -> None:
        """PEP 695 and Pydantic consumers keep their valid contract on refusal."""
        source = (
            "from __future__ import annotations\nfrom typing import TYPE_CHECKING\n"
            f"if TYPE_CHECKING:\n    from {c.Infra.PKG_CORE_UNDERSCORE} import t\n"
            + declaration
        )
        path = tmp_path / "deferred_consumer.py"
        path.write_text(source, encoding="utf-8")
        transformer = FlextInfraRefactorTypingUnifier(
            canonical_map=c.Infra.TYPING_INLINE_UNION_CANONICAL_MAP
        )
        with infra.rope_workspace(tmp_path) as rope:
            resource = rope.resource(path)
            assert resource is not None
            project = rope.rope_project
            with pytest.raises(ValueError, match="requires a runtime binding"):
                transformer.transform(project, resource)
        tm.that(path.read_text(encoding="utf-8"), eq=source)
        outcome = tm.ok(u.Cli.run([sys.executable, "-c", probe], cwd=tmp_path))
        tm.that(outcome.stdout.strip(), eq="1.25")
