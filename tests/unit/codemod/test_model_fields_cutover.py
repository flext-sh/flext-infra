"""Execute migrated public model-validation boundaries with real Pydantic types.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from flext_infra import infra
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraModelFieldsCutover:
    """Migration preserves rejection semantics and reaches a stable source."""

    @staticmethod
    @c.Tests.MARK.parametrize(
        "access",
        [
            'getattr(candidate, "model_fields", None)',
            'getattr(candidate, "model_fields", {})',
            'getattr(candidate, "model_fields")',
            "candidate.model_fields",
        ],
    )
    def test_public_boundary_rejects_non_models_without_attribute_access(
        tmp_path: Path,
        access: str,
    ) -> None:
        """Test public boundary rejects non models without attribute access."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "validation.py"
        source = (
            "from flext_core import m\n"
            "from flext_tests import tm\n"
            "def inspect_definition(candidate: object, *, label: str) -> None:\n"
            f"    fields = {access}\n"
            "    if not isinstance(fields, dict) or not fields:\n"
            "        raise ValueError(label)\n"
            "class Populated(m.BaseModel):\n"
            "    value: str\n"
            "class Empty(m.BaseModel):\n"
            "    pass\n"
            "class Pretender:\n"
            "    model_fields = {'value': None}\n"
            "class Poison:\n"
            "    def __getattr__(self, name: str) -> None:\n"
            "        raise RuntimeError('unexpected attribute access')\n"
            "inspect_definition(Populated, label='valid')\n"
            "for invalid in (None, object(), 1, str, Empty, Pretender, Poison(),"
            " Populated(value='x')):\n"
            "    try:\n"
            "        inspect_definition(invalid, label='original boundary error')\n"
            "    except ValueError as error:\n"
            "        assert str(error) == 'original boundary error'\n"
            "    else:\n"
            "        tm.reject('invalid model was accepted')\n"
        )
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.MODEL_FIELDS,
                    rope_workspace=rope,
                    sources={path: source},
                ),
            )
            tm.that(len(edits), eq=1)
            remaining = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.MODEL_FIELDS,
                    rope_workspace=rope,
                    sources={path: edits[0].updated_source},
                ),
            )
        tm.that(remaining, empty=True)
        path.write_text(edits[0].updated_source, encoding="utf-8")
        outcome = tm.ok(u.Cli.run_raw((sys.executable, "-I", str(path))))
        tm.that(outcome.exit_code, eq=0)
        tm.that(outcome.stderr, eq="")

    @staticmethod
    def test_ambiguous_rejection_keeps_the_source_untouched(
        tmp_path: Path,
    ) -> None:
        """Test ambiguous rejection keeps the source untouched."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "validation.py"
        source = (
            "def validate(candidate: object) -> None:\n"
            "    fields = candidate.model_fields\n"
            "    print(fields)\n"
        )
        path.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            result = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.MODEL_FIELDS,
                rope_workspace=rope,
                sources={path: source},
            )
        tm.fail(result, has="lacks a rejecting guard")
        tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    def test_conflicting_guard_binding_is_not_overwritten(tmp_path: Path) -> None:
        """Test conflicting guard binding is not overwritten."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "validation.py"
        source = (
            "u = 1\n"
            "def validate(candidate: object) -> None:\n"
            "    fields = candidate.model_fields\n"
            "    if not isinstance(fields, dict) or not fields:\n"
            "        raise ValueError('invalid')\n"
        )
        with infra.rope_workspace(root) as rope:
            result = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.MODEL_FIELDS,
                rope_workspace=rope,
                sources={path: source},
            )
        tm.fail(result, has="conflicts with a local binding")

    @staticmethod
    @c.Tests.MARK.parametrize(
        "declaration",
        [
            "from another import type\n",
            "def isinstance(*args):\n    return True\n",
            "class object:\n    pass\n",
            "getattr = lambda *args: {}\n",
            "try:\n    pass\nexcept Exception as dict:\n    pass\n",
            "match None:\n    case type:\n        pass\n",
        ],
    )
    def test_shadowed_contract_is_rejected(
        tmp_path: Path,
        declaration: str,
    ) -> None:
        """Test shadowed contract is rejected."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "validation.py"
        source = declaration + (
            "def validate(candidate: object) -> None:\n"
            "    fields = candidate.model_fields\n"
            "    if not isinstance(fields, dict) or not fields:\n"
            "        raise ValueError('invalid')\n"
        )
        with infra.rope_workspace(root) as rope:
            result = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.MODEL_FIELDS,
                rope_workspace=rope,
                sources={path: source},
            )
        tm.fail(result)

    @staticmethod
    @c.Tests.MARK.parametrize(
        "body",
        [
            (
                "    candidate = object()\n"
                "    fields = candidate.model_fields\n"
                "    if not isinstance(fields, dict) or not fields:\n"
                "        raise ValueError('invalid')\n"
            ),
            (
                "    fields = candidate.model_fields\n"
                "    if not isinstance(fields, dict) or not fields:"
                " raise ValueError('invalid')\n"
            ),
        ],
    )
    def test_unsafe_statement_layout_or_receiver_rebinding_fails(
        tmp_path: Path,
        body: str,
    ) -> None:
        """Test unsafe statement layout or receiver rebinding fails."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "validation.py"
        source = "def validate(candidate: object) -> None:\n" + body
        with infra.rope_workspace(root) as rope:
            result = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.MODEL_FIELDS,
                rope_workspace=rope,
                sources={path: source},
            )
        tm.fail(result)

    @staticmethod
    def test_runtime_protocol_fields_are_port_wrapped_and_validate(
        tmp_path: Path,
    ) -> None:
        """Pydantic fields validate direct public protocols through ``t.Port``."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "models.py"
        source = (
            "from pathlib import Path\n"
            "from typing import Protocol\n"
            "from flext_infra import m, p\n"
            "class Payload(m.BaseModel):\n"
            "    state: p.Cli.AtomicFileState\n"
            "    states: tuple[p.Cli.AtomicFileState, ...]\n"
            "    optional: p.Cli.AtomicFileState | None = None\n"
            "class Contract(Protocol):\n"
            "    state: p.Cli.AtomicFileState\n"
            "def consume(state: p.Cli.AtomicFileState) -> p.Cli.AtomicFileState:\n"
            "    return state\n"
            "class State:\n"
            "    path = Path('.')\n"
            "    content = None\n"
            "    device = None\n"
            "    inode = None\n"
            "value = State()\n"
            "payload = Payload(state=value, states=(value,), optional=value)\n"
            "assert payload.state is value and payload.states == (value,)\n"
        )
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.MODEL_FIELDS,
                    rope_workspace=rope,
                    sources={path: source},
                ),
            )
            tm.that(len(edits), eq=1)
            updated = edits[0].updated_source
            repeated = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.MODEL_FIELDS,
                    rope_workspace=rope,
                    sources={path: updated},
                ),
            )
        tm.that(repeated, empty=True)
        tm.ok("from flext_core import t" in updated)
        tm.ok("state: t.Port[p.Cli.AtomicFileState]" in updated)
        tm.ok("states: tuple[t.Port[p.Cli.AtomicFileState], ...]" in updated)
        tm.ok("optional: t.Port[p.Cli.AtomicFileState] | None" in updated)
        tm.ok("class Contract(Protocol):\n    state: p.Cli.AtomicFileState" in updated)
        tm.ok(
            "def consume(state: p.Cli.AtomicFileState) -> p.Cli.AtomicFileState"
            in updated
        )
        path.write_text(updated, encoding="utf-8")
        outcome = tm.ok(u.Cli.run_raw((sys.executable, "-I", str(path))))
        tm.that(outcome.exit_code, eq=0)
        tm.that(outcome.stderr, eq="")

    @staticmethod
    def test_inherited_local_model_fields_are_port_wrapped(tmp_path: Path) -> None:
        """The source classifier follows imported local bases through mixins."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        base = package / "base.py"
        path = package / "models.py"
        sources = {
            base: ("from flext_infra import m\nclass Shared(m.BaseModel):\n    pass\n"),
            path: (
                "from flext_infra import p\n"
                "from .base import Shared\n"
                "class Mixin:\n"
                "    pass\n"
                "class Payload(Mixin, Shared):\n"
                "    state: p.Cli.AtomicFileState\n"
            ),
        }
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.MODEL_FIELDS,
                    rope_workspace=rope,
                    sources=sources,
                ),
            )
            updated = next(
                edit.updated_source for edit in edits if edit.file_path == path
            )
            repeated = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.MODEL_FIELDS,
                    rope_workspace=rope,
                    sources={base: sources[base], path: updated},
                ),
            )
        tm.ok("from flext_core import t" in updated)
        tm.ok("state: t.Port[p.Cli.AtomicFileState]" in updated)
        tm.that(repeated, empty=True)

    @staticmethod
    def test_annotated_value_model_protocol_fields_are_port_wrapped(
        tmp_path: Path,
    ) -> None:
        """The native MRO classifier reaches ``m.Value`` through its preset base."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "models.py"
        source = (
            "from typing import Annotated, Protocol\n"
            "from flext_infra import m, p\n"
            "class Payload(m.Value):\n"
            "    source: Annotated[\n"
            "        tuple[p.Cli.AtomicPhysicalTreeManifest, ...],\n"
            "        m.Field(min_length=1),\n"
            "    ]\n"
            "class Contract(Protocol):\n"
            "    source: tuple[p.Cli.AtomicPhysicalTreeManifest, ...]\n"
            "def consume(source: p.Cli.AtomicPhysicalTreeManifest) -> None:\n"
            "    pass\n"
        )
        tm.ok(u.Cli.atomic_write_text_file(path, source))
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.MODEL_FIELDS,
                    rope_workspace=rope,
                    sources={path: source},
                ),
            )
            tm.that(len(edits), eq=1)
            updated = edits[0].updated_source
        tm.ok(u.Cli.atomic_write_text_file(path, updated))
        with infra.rope_workspace(root) as rope:
            repeated = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.MODEL_FIELDS,
                    rope_workspace=rope,
                    sources={path: updated},
                ),
            )
        tm.ok("from flext_core import t" in updated)
        tm.ok(
            "source: Annotated[tuple[t.Port[p.Cli.AtomicPhysicalTreeManifest], ...], "
            "m.Field(min_length=1)]" in updated
        )
        tm.ok(
            "class Contract(Protocol):\n"
            "    source: tuple[p.Cli.AtomicPhysicalTreeManifest, ...]" in updated
        )
        tm.ok(
            "def consume(source: p.Cli.AtomicPhysicalTreeManifest) -> None" in updated
        )
        tm.that(repeated, empty=True)

    @staticmethod
    def test_runtime_model_outside_models_tree_is_port_wrapped(
        tmp_path: Path,
    ) -> None:
        """The native model classifier is not limited to the ``_models`` tree."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "gates.py"
        source = (
            "from typing import Annotated, Protocol\n"
            "from flext_infra import m, p\n"
            "class DeptryScan(m.Value):\n"
            "    inputs: tuple[p.Cli.AtomicFileReceipt, ...]\n"
            "    source: Annotated[\n"
            "        tuple[p.Cli.AtomicPhysicalTreeManifest, ...] | None,\n"
            "        m.Field(default=None),\n"
            "    ]\n"
            "    @m.computed_field\n"
            "    @property\n"
            "    def sources(self) -> tuple[p.Cli.AtomicFileState, ...]:\n"
            "        return ()\n"
            "class ScanContract(Protocol):\n"
            "    source: tuple[p.Cli.AtomicPhysicalTreeManifest, ...] | None\n"
            "def consume(source: p.Cli.AtomicPhysicalTreeManifest) -> None:\n"
            "    pass\n"
        )
        tm.ok(u.Cli.atomic_write_text_file(path, source))
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.MODEL_FIELDS,
                    rope_workspace=rope,
                    sources={path: source},
                ),
            )
            tm.that(len(edits), eq=1)
            updated = edits[0].updated_source
        tm.ok(u.Cli.atomic_write_text_file(path, updated))
        with infra.rope_workspace(root) as rope:
            repeated = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.MODEL_FIELDS,
                    rope_workspace=rope,
                    sources={path: updated},
                ),
            )
        tm.ok("inputs: tuple[t.Port[p.Cli.AtomicFileReceipt], ...]" in updated)
        tm.ok(
            "source: Annotated[tuple[t.Port[p.Cli.AtomicPhysicalTreeManifest], ...] | "
            "None, "
            "m.Field(default=None)]" in updated
        )
        tm.ok(
            "def sources(self) -> tuple[t.Port[p.Cli.AtomicFileState], ...]:" in updated
        )
        tm.ok(
            "class ScanContract(Protocol):\n"
            "    source: tuple[p.Cli.AtomicPhysicalTreeManifest, ...] | None" in updated
        )
        tm.ok(
            "def consume(source: p.Cli.AtomicPhysicalTreeManifest) -> None" in updated
        )
        tm.that(repeated, empty=True)
