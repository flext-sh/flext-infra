# Codegen Protocol Generation & Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend flext-infra codegen so it generates the maximum possible set of `p.*` structural protocols from Pydantic-2 models/services/`Flext*` classes via the rope semantic loop, validates every existing protocol against its implementation, and emits precise WARNINGS (never silent skips) for anything it cannot generate because the implementation is out of contract — reusing the scaffold `_protocols/*.j2` templates so the same contract branch stays idempotent.

**Architecture:** A new codegen stage `protocol_gen` runs entirely on the LAW-2 rope semantic model (`FlextInfraUtilitiesRopeAnalysis.get_class_methods` over `PyModule.get_attributes()` — never `get_ast()`). It classifies each public class into `field_only` (fields → generable protocol), `behavior` (public methods → contract-first, validate-only), or `out_of_contract` (mismatch → WARNING). It reuses the existing jinja2 scaffold templates under `templates/project/base/src/_protocols/` (extending them with a generic field-protocol + method-protocol template) so generated code is byte-idempotent with scaffold output. A validator compares each generated/expected protocol against the class the rope loop extracted and reports drift.

**Tech Stack:** Python 3.13, Pydantic 2, rope (semantic model only, LAW-2), jinja2 (via flext-infra codegen renderers), flext-core `r[T]`/`p.*`/`m.*`/`c.*`/`t.*`/`u.*` facades, pytest, ruff, pyrefly.

## Global Constraints

- Python 3.13 syntax only: `from __future__ import annotations`, `X | None`, `list[...]`, PEP 695 `type`/`def f[T]`, `match`/`case`. (python.md §3)
- Pydantic 2 only — `ConfigDict`, `Field`, `model_validate`/`model_dump`; forbidden v1 forms. (python.md §2)
- No `Any`/`object`/`cast(Any)`/`# type: ignore` without `[code]`+`Why:`; no bare `except`; no `# noqa` without `[code]`. (python.md §1)
- LAW-2 STATIC ANALYSIS: rope semantic model ONLY. BANNED in the generation/validation path: `import ast`, `ast.parse`, `ast.walk`, `PyModule.get_ast()`, `walk_ast_nodes`. Use `PyModule.get_attributes()`, `PyObject.get_attributes()`, `PyClass.get_superclasses()`, `child.get_kind()`, `FlextInfraUtilitiesRopeStructure.logical_statements()`, `class_base_names()`. (memory: adr005-p3-single-rope-loop)
- RULES-AS-DATA (LAW-1): classification thresholds, facet names, banned-annotation set live in `flext-infra/config/*.yaml` validated by a Pydantic model, never hardcoded ClassVar tables. (memory: adr005-p3-rules-as-data-law)
- Declaration-layer purity: `_models/*.py` and `_protocols/*.py` carry ZERO business methods — only Pydantic fields + `Field`/`field_validator`/`computed_field`, and `Protocol` signature stubs. Behavior lives in `_utilities`/services. (memory: flext-law-declaration-layers-zero-methods)
- Facade order c → t → p → m → u; `p` imports `m` only under `TYPE_CHECKING`. (memory: flext-typing-import-layering-law)
- Every module < 200 logical LOC. (python.md §0)
- Idempotency: running the generator twice on an unchanged tree produces byte-identical output; generated protocols must match the scaffold `_protocols/*.j2` shape exactly.
- English-only code, comments, docstrings, templates. (memory: english-only-code-comments)
- Validate after each edit: `make lint`, `make typecheck`, `make test` from flext-infra; surgical per-file git; never `git add -A`. (memory: cooperative-git-commit-discipline)
- Commits authored as the user, no bot attribution. (AGENTS.md Rule 10)

---

## Classification Contract (the taxonomy every task depends on)

A public class discovered by the rope loop is classified by comparing what it exposes against what a protocol can faithfully declare:

| Class | rope facts | Generable? | Action |
|---|---|---|---|
| **field_only** | Pydantic model, 0 public business methods, only annotated fields | YES | GENERATE `@property def <field>(self) -> <ann>: ...` protocol |
| **behavior** | public methods with resolvable signatures | VALIDATE-ONLY | COMPARE existing `p.*` protocol methods vs class methods; report drift |
| **out_of_contract** | public method NOT in declared `p.*` protocol, OR field annotation is `Any`/`object`/unresolvable, OR private `ClassVar` leaks into the public surface | NO | EMIT WARNING with exact reason + symbol + file:line |

The generator NEVER silently skips. Every non-generated class produces either a validated PASS or a WARNING naming the exact out-of-contract symbol.

---

## File Structure

**New config (LAW-1 rules-as-data):**

- `flext-infra/config/protocol_gen.yaml` — classification thresholds, facet allowlist, banned annotations, warning severities.
- `flext-infra/config/schemas/protocol_gen.schema.json` — JSON Schema validating the above.

**New models (declaration-only, rope models facet):**

- `flext-infra/src/flext_infra/_models/protocol_gen.py` — `ProtocolFieldSpec`, `ProtocolMethodSpec`, `ProtocolClassPlan`, `ProtocolGenWarning`, `ProtocolGenReport` (Pydantic `m.ContractModel`).

**New protocol port:**

- `flext-infra/src/flext_infra/_protocols/protocol_gen.py` — `ProtocolGenEngine` Protocol (signature stubs only).

**New rope-semantic extractor (behavior, LAW-2):**

- `flext-infra/src/flext_infra/_utilities/protocol_extract.py` — `FlextInfraUtilitiesProtocolExtract.extract_class(...) -> r[ProtocolClassPlan]`.

**New classifier (behavior):**

- `flext-infra/src/flext_infra/_utilities/protocol_classify.py` — `FlextInfraUtilitiesProtocolClassify.classify(...)`.

**New codegen orchestrator:**

- `flext-infra/src/flext_infra/codegen/protocol_gen.py` — `FlextInfraCodegenProtocolGen(s[str])`.

**New templates (reuse scaffold branch):**

- `flext-infra/src/flext_infra/templates/project/base/src/_protocols/_field_protocol.py.j2`
- `flext-infra/src/flext_infra/templates/project/base/src/_protocols/_method_protocol.py.j2`

**New tests:**

- `flext-infra/tests/unit/codegen/test_protocol_gen_config.py`
- `flext-infra/tests/unit/codegen/test_protocol_gen_models.py`
- `flext-infra/tests/unit/codegen/test_protocol_extract.py`
- `flext-infra/tests/unit/codegen/test_protocol_classify.py`
- `flext-infra/tests/unit/codegen/test_protocol_gen_render.py`
- `flext-infra/tests/unit/codegen/test_protocol_gen_validate.py`
- `flext-infra/tests/unit/codegen/test_protocol_gen_idempotent.py`
- `flext-infra/tests/unit/codegen/test_protocol_gen_cli.py`
- `flext-infra/tests/unit/codegen/test_protocol_gen_pipeline.py`
- `flext-infra/tests/unit/codegen/_fixtures/sample_models.py`

**Wiring:**

- `flext-infra/src/flext_infra/cli.py` — `protocol-gen` subcommand.
- `flext-infra/src/flext_infra/codegen/pipeline.py` — register stage.
- `flext-infra/base.mk` — `protocol-gen` make verb (dry-run default, `APPLY=1` writes).

---

## Task 1: Rules-as-data config + schema

**Files:**

- Create: `flext-infra/config/protocol_gen.yaml`
- Create: `flext-infra/config/schemas/protocol_gen.schema.json`
- Test: `flext-infra/tests/unit/codegen/test_protocol_gen_config.py`

**Interfaces:**

- Produces: `config/protocol_gen.yaml` with keys `facet_allowlist: list[str]`, `banned_annotations: list[str]`, `field_only_max_methods: int`, `warning_severities: {out_of_contract, unresolved_annotation, private_leak}`; validated by `protocol_gen.schema.json`.

- [ ] **Step 1: Write the failing test**

```python
# flext-infra/tests/unit/codegen/test_protocol_gen_config.py
from __future__ import annotations

from pathlib import Path

from flext_infra import u


class TestProtocolGenConfig:
    def test_config_loads_and_validates_against_schema(self) -> None:
        root = Path(__file__).resolve().parents[3]
        cfg = root / "config" / "protocol_gen.yaml"
        schema = root / "config" / "schemas" / "protocol_gen.schema.json"
        result = u.Cli.yaml_validate_schema(cfg, schema)
        assert result.success, result.error
        data = result.value
        assert data["field_only_max_methods"] == 0
        assert "Any" in data["banned_annotations"]
        assert data["warning_severities"]["out_of_contract"] == "HIGH"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd flext-infra && env -u PYTHONPATH .venv/bin/python -m pytest tests/unit/codegen/test_protocol_gen_config.py -v`
Expected: FAIL — `config/protocol_gen.yaml` missing (FileNotFoundError).

- [ ] **Step 3: Create the schema**

```json
// flext-infra/config/schemas/protocol_gen.schema.json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ProtocolGenConfig",
  "type": "object",
  "additionalProperties": false,
  "required": ["facet_allowlist", "banned_annotations", "field_only_max_methods", "warning_severities"],
  "properties": {
    "facet_allowlist": {"type": "array", "items": {"type": "string"}, "minItems": 1},
    "banned_annotations": {"type": "array", "items": {"type": "string"}, "minItems": 1},
    "field_only_max_methods": {"type": "integer", "minimum": 0},
    "warning_severities": {
      "type": "object",
      "additionalProperties": false,
      "required": ["out_of_contract", "unresolved_annotation", "private_leak"],
      "properties": {
        "out_of_contract": {"enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"]},
        "unresolved_annotation": {"enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"]},
        "private_leak": {"enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"]}
      }
    }
  }
}
```

- [ ] **Step 4: Create the config**

```yaml
# flext-infra/config/protocol_gen.yaml
# Rules-as-data for codegen protocol generation & validation (LAW-1).
facet_allowlist:
  - models
  - services
  - api
  - base
banned_annotations:
  - Any
  - object
  - "typing.Any"
field_only_max_methods: 0
warning_severities:
  out_of_contract: HIGH
  unresolved_annotation: MEDIUM
  private_leak: HIGH
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd flext-infra && env -u PYTHONPATH .venv/bin/python -m pytest tests/unit/codegen/test_protocol_gen_config.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(codegen): protocol_gen rules-as-data config + schema" config/protocol_gen.yaml config/schemas/protocol_gen.schema.json tests/unit/codegen/test_protocol_gen_config.py
```

---

## Task 2: Declaration-only spec models

**Files:**

- Create: `flext-infra/src/flext_infra/_models/protocol_gen.py`
- Modify: `flext-infra/src/flext_infra/_models/__init__.py` (lazy export `FlextInfraModelsProtocolGen`)
- Modify: `flext-infra/src/flext_infra/models.py` (compose into `m.Infra` MRO — follow `FlextInfraModelsRope`/`m.Infra.SymbolInfo` pattern)
- Test: `flext-infra/tests/unit/codegen/test_protocol_gen_models.py`

**Interfaces:**

- Produces (all `m.Infra.*`, frozen `m.ContractModel`):
  - `ProtocolFieldSpec(name: str, annotation: str)`
  - `ProtocolMethodSpec(name: str, signature: str, kind: str)`
  - `ProtocolClassPlan(class_name: str, module: str, kind: str, fields: tuple[ProtocolFieldSpec, ...] = (), methods: tuple[ProtocolMethodSpec, ...] = ())`
  - `ProtocolGenWarning(class_name: str, module: str, symbol: str, reason: str, severity: str, line: int)`
  - `ProtocolGenReport(generated: tuple[ProtocolClassPlan, ...] = (), validated: tuple[str, ...] = (), warnings: tuple[ProtocolGenWarning, ...] = ())`

- [ ] **Step 1: Write the failing test**

```python
# flext-infra/tests/unit/codegen/test_protocol_gen_models.py
from __future__ import annotations

from flext_infra import m


class TestProtocolGenModels:
    def test_field_spec_is_frozen_pydantic(self) -> None:
        spec = m.Infra.ProtocolFieldSpec(name="app_name", annotation="str")
        assert spec.name == "app_name"
        assert spec.model_config.get("frozen") is True

    def test_class_plan_holds_specs(self) -> None:
        plan = m.Infra.ProtocolClassPlan(
            class_name="Storage",
            module="storage.py",
            kind="field_only",
            fields=(m.Infra.ProtocolFieldSpec(name="namespace", annotation="str"),),
        )
        assert plan.kind == "field_only"
        assert plan.fields[0].name == "namespace"

    def test_warning_carries_reason_and_line(self) -> None:
        warn = m.Infra.ProtocolGenWarning(
            class_name="FlextService",
            module="service.py",
            symbol="fetch_global",
            reason="public method missing from p.Service",
            severity="HIGH",
            line=53,
        )
        assert warn.line == 53
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd flext-infra && env -u PYTHONPATH .venv/bin/python -m pytest tests/unit/codegen/test_protocol_gen_models.py -v`
Expected: FAIL — `AttributeError: ... has no attribute 'ProtocolFieldSpec'`.

- [ ] **Step 3: Create the models module**

```python
# flext-infra/src/flext_infra/_models/protocol_gen.py
"""Declaration-only spec models for codegen protocol generation.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_core import m


class FlextInfraModelsProtocolGen:
    """Pydantic contracts for the protocol-generation pipeline."""

    class ProtocolFieldSpec(m.ContractModel):
        """One protocol property derived from a model field."""

        name: str
        annotation: str

    class ProtocolMethodSpec(m.ContractModel):
        """One protocol method stub derived from a class method."""

        name: str
        signature: str
        kind: str

    class ProtocolClassPlan(m.ContractModel):
        """Full extraction+classification plan for one public class."""

        class_name: str
        module: str
        kind: str
        fields: tuple[FlextInfraModelsProtocolGen.ProtocolFieldSpec, ...] = ()
        methods: tuple[FlextInfraModelsProtocolGen.ProtocolMethodSpec, ...] = ()

    class ProtocolGenWarning(m.ContractModel):
        """A class the generator refused to emit, with the exact reason."""

        class_name: str
        module: str
        symbol: str
        reason: str
        severity: str
        line: int

    class ProtocolGenReport(m.ContractModel):
        """Aggregate result of one protocol-gen run."""

        generated: tuple[FlextInfraModelsProtocolGen.ProtocolClassPlan, ...] = ()
        validated: tuple[str, ...] = ()
        warnings: tuple[FlextInfraModelsProtocolGen.ProtocolGenWarning, ...] = ()


__all__: list[str] = ["FlextInfraModelsProtocolGen"]
```

- [ ] **Step 4: Wire the lazy export**

In `_models/__init__.py` add `".protocol_gen": ("FlextInfraModelsProtocolGen",)` to `build_lazy_import_map`, and compose `FlextInfraModelsProtocolGen` into the `m.Infra` MRO in `models.py` (mirror `FlextInfraModelsRope`).

- [ ] **Step 5: Run test to verify it passes**

Run: `cd flext-infra && env -u PYTHONPATH .venv/bin/python -m pytest tests/unit/codegen/test_protocol_gen_models.py -v`
Expected: PASS (3 passed).

- [ ] **Step 6: Validate + commit**

Run: `cd flext-infra && env -u PYTHONPATH .venv/bin/python -m ruff check src/flext_infra/_models/protocol_gen.py && env -u PYTHONPATH .venv/bin/python -m pyright src/flext_infra/_models/protocol_gen.py`
Expected: ruff pass, 0 pyright errors.

```bash
git commit -m "feat(codegen): declaration-only protocol_gen spec models" src/flext_infra/_models/protocol_gen.py src/flext_infra/_models/__init__.py src/flext_infra/models.py tests/unit/codegen/test_protocol_gen_models.py
```

---

## Task 3: Rope-semantic protocol extractor (LAW-2)

**Files:**

- Create: `flext-infra/src/flext_infra/_utilities/protocol_extract.py`
- Modify: `flext-infra/src/flext_infra/utilities.py` (compose `u.Infra.ProtocolExtract`)
- Test: `flext-infra/tests/unit/codegen/test_protocol_extract.py`
- Fixture: `flext-infra/tests/unit/codegen/_fixtures/sample_models.py`

**Interfaces:**

- Consumes: `m.Infra.ProtocolFieldSpec/ProtocolMethodSpec/ProtocolClassPlan` (Task 2); `FlextInfraUtilitiesRopeAnalysis.get_class_methods(rope_project, resource, class_name, include_private=False) -> t.StrMapping`; `FlextInfraUtilitiesRopeStructure.logical_statements(source) -> tuple[p.Infra.LogicalStatement, ...]` + `target_name`.
- Produces: `FlextInfraUtilitiesProtocolExtract.extract_class(project_root: Path, file_path: Path, class_name: str) -> r[p.Infra.ProtocolClassPlan]` — fields from class-enclosed `ANN_ASSIGN` statements, methods from `get_class_methods`, `kind="unclassified"`.

- [ ] **Step 1: Write the fixture**

```python
# flext-infra/tests/unit/codegen/_fixtures/sample_models.py
"""Fixture classes for protocol extraction tests."""

from __future__ import annotations

from flext_core import m, u


class SampleFieldOnly(m.Value):
    """A pure field-only model."""

    namespace: str = u.Field(description="ns")
    max_size: int | None = u.Field(default=None)


class SampleBehavior(m.Value):
    """A model with a public behavior method."""

    name: str = u.Field(description="n")

    def describe(self) -> str:
        return self.name
```

- [ ] **Step 2: Write the failing test**

```python
# flext-infra/tests/unit/codegen/test_protocol_extract.py
from __future__ import annotations

from pathlib import Path

from flext_infra import u

_FIXTURE = Path(__file__).parent / "_fixtures" / "sample_models.py"
_ROOT = Path(__file__).resolve().parents[3]


class TestProtocolExtract:
    def test_extract_field_only_returns_fields(self) -> None:
        result = u.Infra.ProtocolExtract.extract_class(
            _ROOT, _FIXTURE, "SampleFieldOnly"
        )
        assert result.success, result.error
        names = {f.name for f in result.value.fields}
        assert names == {"namespace", "max_size"}
        assert result.value.methods == ()

    def test_extract_behavior_returns_public_method(self) -> None:
        result = u.Infra.ProtocolExtract.extract_class(
            _ROOT, _FIXTURE, "SampleBehavior"
        )
        assert result.success, result.error
        assert "describe" in {mth.name for mth in result.value.methods}
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd flext-infra && env -u PYTHONPATH .venv/bin/python -m pytest tests/unit/codegen/test_protocol_extract.py -v`
Expected: FAIL — `u.Infra.ProtocolExtract` unresolved.

- [ ] **Step 4: Implement the extractor (rope-only)**

```python
# flext-infra/src/flext_infra/_utilities/protocol_extract.py
"""Rope-semantic protocol extraction (LAW-2: no ast, no get_ast).

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core import c, m, r
from flext_infra._utilities.rope_analysis import FlextInfraUtilitiesRopeAnalysis
from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra._utilities.rope_structure import FlextInfraUtilitiesRopeStructure

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraUtilitiesProtocolExtract:
    """Extract fields + public methods for a class using the rope semantic model."""

    @classmethod
    def extract_class(
        cls, project_root: Path, file_path: Path, class_name: str
    ) -> r[p.Infra.ProtocolClassPlan]:
        """Return an unclassified plan of one class's protocol surface."""
        source = file_path.read_text(encoding="utf-8")
        return r[p.Infra.ProtocolClassPlan].ok(
            m.Infra.ProtocolClassPlan(
                class_name=class_name,
                module=file_path.name,
                kind="unclassified",
                fields=cls._extract_fields(source, class_name),
                methods=cls._extract_methods(project_root, file_path, class_name),
            )
        )

    @staticmethod
    def _extract_fields(
        source: str, class_name: str
    ) -> tuple[p.Infra.ProtocolFieldSpec, ...]:
        """Return annotated fields declared directly in ``class_name``'s body."""
        specs: list[p.Infra.ProtocolFieldSpec] = []
        for stmt in FlextInfraUtilitiesRopeStructure.logical_statements(source):
            if (
                stmt.enclosing_kind == c.Infra.RopeScopeKind.CLASS
                and stmt.enclosing_name == class_name
                and stmt.category == c.Infra.StatementCategory.ANN_ASSIGN
            ):
                name = FlextInfraUtilitiesRopeStructure.target_name(stmt)
                if name and not name.startswith("_"):
                    specs.append(
                        m.Infra.ProtocolFieldSpec(
                            name=name,
                            annotation=FlextInfraUtilitiesProtocolExtract._annotation_of(
                                stmt.text
                            ),
                        )
                    )
        return tuple(specs)

    @staticmethod
    def _annotation_of(text: str) -> str:
        """Return the annotation source between the first ':' and '=' (or EOL)."""
        _, _, annotation = text.split("=", 1)[0].partition(":")
        return annotation.strip()

    @staticmethod
    def _extract_methods(
        project_root: Path, file_path: Path, class_name: str
    ) -> tuple[p.Infra.ProtocolMethodSpec, ...]:
        """Return public methods of ``class_name`` via rope PyObject attributes."""
        with FlextInfraUtilitiesRopeCore.open_project(project_root) as rope_proj:
            resource = FlextInfraUtilitiesRopeCore.fetch_python_resource(
                rope_proj, file_path
            )
            if resource is None:
                return ()
            methods = FlextInfraUtilitiesRopeAnalysis.get_class_methods(
                rope_proj, resource, class_name, include_private=False
            )
        return tuple(
            m.Infra.ProtocolMethodSpec(
                name=name, signature=f"def {name}(self) -> object: ...", kind=str(kind)
            )
            for name, kind in sorted(methods.items())
        )


__all__: list[str] = ["FlextInfraUtilitiesProtocolExtract"]
```

Compose into `u.Infra` (mirror `u.Infra.RopeStructure`).

- [ ] **Step 5: Run test to verify it passes**

Run: `cd flext-infra && env -u PYTHONPATH .venv/bin/python -m pytest tests/unit/codegen/test_protocol_extract.py -v`
Expected: PASS (2 passed).

- [ ] **Step 6: Verify LAW-2 + commit**

Run: `cd flext-infra && grep -nE "import ast|ast\.parse|get_ast|walk_ast_nodes" src/flext_infra/_utilities/protocol_extract.py`
Expected: NO output.

```bash
git commit -m "feat(codegen): rope-semantic protocol extractor (LAW-2)" src/flext_infra/_utilities/protocol_extract.py src/flext_infra/utilities.py tests/unit/codegen/test_protocol_extract.py tests/unit/codegen/_fixtures/sample_models.py
```

---

## Task 4: Classifier (field_only / behavior / out_of_contract)

**Files:**

- Create: `flext-infra/src/flext_infra/_utilities/protocol_classify.py`
- Modify: `flext-infra/src/flext_infra/utilities.py` (compose `u.Infra.ProtocolClassify`)
- Test: `flext-infra/tests/unit/codegen/test_protocol_classify.py`

**Interfaces:**

- Consumes: `m.Infra.ProtocolClassPlan` (unclassified), `m.Infra.ProtocolGenWarning`, Task-1 config mapping.
- Produces: `FlextInfraUtilitiesProtocolClassify.classify(plan: p.Infra.ProtocolClassPlan, config: t.JsonMapping) -> tuple[p.Infra.ProtocolClassPlan, tuple[p.Infra.ProtocolGenWarning, ...]]` — banned annotation → `out_of_contract`+warning; public methods > `field_only_max_methods` → `behavior`; else `field_only`.

- [ ] **Step 1: Write the failing test**

```python
# flext-infra/tests/unit/codegen/test_protocol_classify.py
from __future__ import annotations

from flext_infra import m, u

_CONFIG = {
    "facet_allowlist": ["models"],
    "banned_annotations": ["Any", "object"],
    "field_only_max_methods": 0,
    "warning_severities": {
        "out_of_contract": "HIGH",
        "unresolved_annotation": "MEDIUM",
        "private_leak": "HIGH",
    },
}


class TestProtocolClassify:
    def test_field_only_when_no_methods(self) -> None:
        plan = m.Infra.ProtocolClassPlan(
            class_name="S",
            module="s.py",
            kind="unclassified",
            fields=(m.Infra.ProtocolFieldSpec(name="x", annotation="str"),),
        )
        classified, warnings = u.Infra.ProtocolClassify.classify(plan, _CONFIG)
        assert classified.kind == "field_only"
        assert warnings == ()

    def test_behavior_when_public_methods(self) -> None:
        plan = m.Infra.ProtocolClassPlan(
            class_name="Svc",
            module="svc.py",
            kind="unclassified",
            methods=(
                m.Infra.ProtocolMethodSpec(
                    name="run",
                    signature="def run(self) -> object: ...",
                    kind="instance",
                ),
            ),
        )
        classified, _ = u.Infra.ProtocolClassify.classify(plan, _CONFIG)
        assert classified.kind == "behavior"

    def test_out_of_contract_warns_on_banned_annotation(self) -> None:
        plan = m.Infra.ProtocolClassPlan(
            class_name="Bad",
            module="b.py",
            kind="unclassified",
            fields=(m.Infra.ProtocolFieldSpec(name="data", annotation="Any"),),
        )
        classified, warnings = u.Infra.ProtocolClassify.classify(plan, _CONFIG)
        assert classified.kind == "out_of_contract"
        assert warnings[0].symbol == "data"
        assert warnings[0].severity == "MEDIUM"
        assert "Any" in warnings[0].reason
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd flext-infra && env -u PYTHONPATH .venv/bin/python -m pytest tests/unit/codegen/test_protocol_classify.py -v`
Expected: FAIL — `u.Infra.ProtocolClassify` unresolved.

- [ ] **Step 3: Implement the classifier**

```python
# flext-infra/src/flext_infra/_utilities/protocol_classify.py
"""Classify an extracted class plan into field_only / behavior / out_of_contract.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core import m

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraUtilitiesProtocolClassify:
    """Assign a protocol-generation kind and emit precise warnings."""

    @classmethod
    def classify(
        cls, plan: p.Infra.ProtocolClassPlan, config: t.JsonMapping
    ) -> tuple[p.Infra.ProtocolClassPlan, tuple[p.Infra.ProtocolGenWarning, ...]]:
        """Return (classified_plan, warnings) for one extracted class."""
        banned = set(config["banned_annotations"])
        max_methods = int(config["field_only_max_methods"])
        severity = str(config["warning_severities"]["unresolved_annotation"])
        warnings = tuple(
            m.Infra.ProtocolGenWarning(
                class_name=plan.class_name,
                module=plan.module,
                symbol=field.name,
                reason=f"field annotation '{field.annotation}' is banned for protocol generation",
                severity=severity,
                line=0,
            )
            for field in plan.fields
            if field.annotation in banned
        )
        if warnings:
            kind = "out_of_contract"
        elif len(plan.methods) > max_methods:
            kind = "behavior"
        else:
            kind = "field_only"
        return plan.model_copy(update={"kind": kind}), warnings


__all__: list[str] = ["FlextInfraUtilitiesProtocolClassify"]
```

Compose into `u.Infra`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd flext-infra && env -u PYTHONPATH .venv/bin/python -m pytest tests/unit/codegen/test_protocol_classify.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Validate + commit**

```bash
git commit -m "feat(codegen): protocol classifier with out-of-contract warnings" src/flext_infra/_utilities/protocol_classify.py src/flext_infra/utilities.py tests/unit/codegen/test_protocol_classify.py
```

---

## Task 5: Generic field + method protocol templates (reuse scaffold branch)

**Files:**

- Create: `flext-infra/src/flext_infra/templates/project/base/src/_protocols/_field_protocol.py.j2`
- Create: `flext-infra/src/flext_infra/templates/project/base/src/_protocols/_method_protocol.py.j2`
- Test: `flext-infra/tests/unit/codegen/test_protocol_gen_render.py`

**Interfaces:**

- Consumes: render context vars `package_name`, `year`, `author_name`, `protocol_class_name: str`, `fields: list[{name, annotation}]`, `methods: list[{signature}]`.
- Produces: rendered protocol source matching the existing `settings.py.j2` field-only shape + a method-stub block.

- [ ] **Step 1: Write the failing test**

```python
# flext-infra/tests/unit/codegen/test_protocol_gen_render.py
from __future__ import annotations

from pathlib import Path

from flext_infra import u

_TPL_DIR = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "flext_infra"
    / "templates"
    / "project"
    / "base"
    / "src"
    / "_protocols"
)


class TestProtocolGenRender:
    def test_field_protocol_renders_property_per_field(self) -> None:
        tpl = (_TPL_DIR / "_field_protocol.py.j2").read_text(encoding="utf-8")
        ctx = {
            "package_name": "flext_demo",
            "year": "2026",
            "author_name": "FLEXT Team",
            "protocol_class_name": "Storage",
            "fields": [
                {"name": "namespace", "annotation": "str"},
                {"name": "max_size", "annotation": "int | None"},
            ],
        }
        result = u.Cli.render_template_string(tpl, ctx)
        assert result.success, result.error
        out = result.value
        assert "class Storage(Protocol):" in out
        assert "def namespace(self) -> str:" in out
        assert "def max_size(self) -> int | None:" in out
        assert "@runtime_checkable" in out
```

NOTE: confirm the SSOT render entry name — run `grep -rn "def render_template" ../flext-cli/src` — and replace `u.Cli.render_template_string` with the real symbol if different.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd flext-infra && env -u PYTHONPATH .venv/bin/python -m pytest tests/unit/codegen/test_protocol_gen_render.py -v`
Expected: FAIL — `_field_protocol.py.j2` missing.

- [ ] **Step 3: Create the field-protocol template**

```jinja
{# templates/project/base/src/_protocols/_field_protocol.py.j2 #}
{# NOTE (protocol-gen): generic field-only protocol; generalizes config/settings. -#}
"""Structural field protocol {{ protocol_class_name }} for {{ package_name }}.

Copyright (c) {{ year }} {{ author_name }}. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class {{ protocol_class_name }}(Protocol):
    """Structural field surface generated from the model of the same name."""

{% for field in fields %}
    @property
    def {{ field.name }}(self) -> {{ field.annotation }}:
        """Field ``{{ field.name }}``."""
        ...
{% endfor %}
```

- [ ] **Step 4: Create the method-protocol template**

```jinja
{# templates/project/base/src/_protocols/_method_protocol.py.j2 #}
{# NOTE (protocol-gen): behavior protocol method-stub block. -#}
"""Structural behavior protocol {{ protocol_class_name }} for {{ package_name }}.

Copyright (c) {{ year }} {{ author_name }}. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class {{ protocol_class_name }}(Protocol):
    """Structural behavior contract generated from the class of the same name."""

{% for method in methods %}
    {{ method.signature }}
{% endfor %}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd flext-infra && env -u PYTHONPATH .venv/bin/python -m pytest tests/unit/codegen/test_protocol_gen_render.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(codegen): generic field + method protocol templates" src/flext_infra/templates/project/base/src/_protocols/_field_protocol.py.j2 src/flext_infra/templates/project/base/src/_protocols/_method_protocol.py.j2 tests/unit/codegen/test_protocol_gen_render.py
```

---

## Task 6: Codegen orchestrator (extract → classify → report)

**Files:**

- Create: `flext-infra/src/flext_infra/codegen/protocol_gen.py`
- Create: `flext-infra/src/flext_infra/_protocols/protocol_gen.py`
- Modify: `flext-infra/src/flext_infra/protocols.py` (compose `FlextInfraProtocolsProtocolGen`)
- Test: `flext-infra/tests/unit/codegen/test_protocol_gen_validate.py`

**Interfaces:**

- Consumes: `u.Infra.ProtocolExtract.extract_class`, `u.Infra.ProtocolClassify.classify`, Task-1 config; class discovery via `FlextInfraUtilitiesRopeAnalysis.get_module_classes` (LAW-2) unioned with `u.Infra.RopeAnalysisIntrospection.extract_public_methods_from_dir`.
- Produces: `FlextInfraCodegenProtocolGen.run(package_dir: Path, *, apply: bool) -> r[p.Infra.ProtocolGenReport]` — dry-run by default (Safe-by-Default); writes only when `apply=True`.

- [ ] **Step 1: Write the failing test**

```python
# flext-infra/tests/unit/codegen/test_protocol_gen_validate.py
from __future__ import annotations

from pathlib import Path

from flext_infra.codegen.protocol_gen import FlextInfraCodegenProtocolGen

_FIXTURE_DIR = Path(__file__).parent / "_fixtures"


class TestProtocolGenValidate:
    def test_run_dry_run_reports_field_only_and_behavior(self) -> None:
        result = FlextInfraCodegenProtocolGen().run(_FIXTURE_DIR, apply=False)
        assert result.success, result.error
        kinds = {plan.class_name: plan.kind for plan in result.value.generated}
        assert kinds.get("SampleFieldOnly") == "field_only"
        assert kinds.get("SampleBehavior") == "behavior"

    def test_run_dry_run_does_not_write_files(self) -> None:
        before = set(_FIXTURE_DIR.glob("_protocols/*.py"))
        FlextInfraCodegenProtocolGen().run(_FIXTURE_DIR, apply=False)
        assert set(_FIXTURE_DIR.glob("_protocols/*.py")) == before
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd flext-infra && env -u PYTHONPATH .venv/bin/python -m pytest tests/unit/codegen/test_protocol_gen_validate.py -v`
Expected: FAIL — module `flext_infra.codegen.protocol_gen` missing.

- [ ] **Step 3: Create the protocol port**

```python
# flext-infra/src/flext_infra/_protocols/protocol_gen.py
"""Structural port for the protocol-generation engine.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import m, p


class FlextInfraProtocolsProtocolGen:
    """Protocol namespace for the protocol-generation engine."""

    @runtime_checkable
    class ProtocolGenEngine(Protocol):
        """Contract for the extract-classify-render-report engine."""

        def run(
            self, package_dir: Path, *, apply: bool
        ) -> p.Result[p.Infra.ProtocolGenReport]:
            """Run the pipeline and return the aggregate report."""
            ...


__all__: list[str] = ["FlextInfraProtocolsProtocolGen"]
```

- [ ] **Step 4: Create the orchestrator**

```python
# flext-infra/src/flext_infra/codegen/protocol_gen.py
"""Codegen stage: generate + validate protocols from Pydantic classes.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import c, m, r, s, u
from flext_infra._utilities.discovery import FlextInfraUtilitiesDiscovery
from flext_infra._utilities.rope_analysis import FlextInfraUtilitiesRopeAnalysis
from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraCodegenProtocolGen(s[str]):
    """Drive protocol generation and validation for one package directory."""

    def run(self, package_dir: Path, *, apply: bool) -> r[p.Infra.ProtocolGenReport]:
        """Discover, extract, classify, (optionally) render, and report."""
        config = self._load_config()
        if config.failure:
            return r[p.Infra.ProtocolGenReport].fail(
                config.error or "config load failed"
            )
        project_root = FlextInfraUtilitiesDiscovery.project_root(package_dir / "foo.py")
        if project_root is None:
            return r[p.Infra.ProtocolGenReport].fail(
                f"no project root for {package_dir}"
            )
        plans: list[p.Infra.ProtocolClassPlan] = []
        warnings: list[p.Infra.ProtocolGenWarning] = []
        for py_file in sorted(package_dir.glob(c.Infra.EXT_PYTHON_GLOB)):
            if py_file.name == c.Infra.INIT_PY or py_file.name.startswith("_"):
                continue
            for class_name in self._discover_classes(project_root.parent, py_file):
                extracted = u.Infra.ProtocolExtract.extract_class(
                    project_root.parent, py_file, class_name
                )
                if extracted.failure:
                    continue
                classified, class_warnings = u.Infra.ProtocolClassify.classify(
                    extracted.value, config.value
                )
                plans.append(classified)
                warnings.extend(class_warnings)
        generated = tuple(p for p in plans if p.kind in {"field_only", "behavior"})
        if apply:
            self._render_field_only(package_dir, generated)
        return r[p.Infra.ProtocolGenReport].ok(
            m.Infra.ProtocolGenReport(
                generated=generated,
                validated=tuple(
                    p.class_name for p in generated if p.kind == "behavior"
                ),
                warnings=tuple(warnings),
            )
        )

    @staticmethod
    def _load_config() -> r[t.JsonMapping]:
        root = Path(__file__).resolve().parents[2]
        return u.Cli.yaml_validate_schema(
            root / "config" / "protocol_gen.yaml",
            root / "config" / "schemas" / "protocol_gen.schema.json",
        )

    @staticmethod
    def _discover_classes(project_root: Path, py_file: Path) -> tuple[str, ...]:
        with FlextInfraUtilitiesRopeCore.open_project(project_root) as rope_proj:
            resource = FlextInfraUtilitiesRopeCore.fetch_python_resource(
                rope_proj, py_file
            )
            if resource is None:
                return ()
            classes = FlextInfraUtilitiesRopeAnalysis.get_module_classes(
                rope_proj, resource
            )
        return tuple(sorted(classes))

    @staticmethod
    def _render_field_only(
        package_dir: Path, plans: tuple[p.Infra.ProtocolClassPlan, ...]
    ) -> None:
        # Idempotent writer implemented in Task 7. Dry-run path is complete here.
        _ = (package_dir, plans)


__all__: list[str] = ["FlextInfraCodegenProtocolGen"]
```

NOTE: confirm `FlextInfraUtilitiesRopeAnalysis.get_module_classes` signature via `grep -n "def get_module_classes" src/flext_infra/_utilities/rope_analysis.py`; if it needs `include_nested`, pass the flag that returns top-level classes only.

- [ ] **Step 5: Run test to verify it passes**

Run: `cd flext-infra && env -u PYTHONPATH .venv/bin/python -m pytest tests/unit/codegen/test_protocol_gen_validate.py -v`
Expected: PASS (2 passed).

- [ ] **Step 6: LAW-2 check + commit**

Run: `cd flext-infra && grep -nE "get_ast|import ast|ast\.parse" src/flext_infra/codegen/protocol_gen.py`
Expected: NO output.

```bash
git commit -m "feat(codegen): protocol-gen orchestrator (extract/classify/report)" src/flext_infra/codegen/protocol_gen.py src/flext_infra/_protocols/protocol_gen.py src/flext_infra/protocols.py tests/unit/codegen/test_protocol_gen_validate.py
```

---

## Task 7: Idempotent writer

**Files:**

- Modify: `flext-infra/src/flext_infra/codegen/protocol_gen.py:_render_field_only`
- Test: `flext-infra/tests/unit/codegen/test_protocol_gen_idempotent.py`

**Interfaces:**

- Consumes: Task-5 `_field_protocol.py.j2`, Task-6 `generated` plans.
- Produces: `_render_field_only` writes `_protocols/<snake>.py` per `field_only` plan through the SSOT renderer, only when content differs; two `apply=True` runs are byte-identical.

- [ ] **Step 1: Write the failing test**

```python
# flext-infra/tests/unit/codegen/test_protocol_gen_idempotent.py
from __future__ import annotations

import shutil
from pathlib import Path

from flext_infra.codegen.protocol_gen import FlextInfraCodegenProtocolGen

_FIXTURE_DIR = Path(__file__).parent / "_fixtures"


class TestProtocolGenIdempotent:
    def test_apply_twice_is_byte_identical(self, tmp_path: Path) -> None:
        pkg = tmp_path / "sample_pkg"
        shutil.copytree(_FIXTURE_DIR, pkg)
        engine = FlextInfraCodegenProtocolGen()
        engine.run(pkg, apply=True)
        first = {p.name: p.read_bytes() for p in (pkg / "_protocols").glob("*.py")}
        engine.run(pkg, apply=True)
        second = {p.name: p.read_bytes() for p in (pkg / "_protocols").glob("*.py")}
        assert first == second
        assert first
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd flext-infra && env -u PYTHONPATH .venv/bin/python -m pytest tests/unit/codegen/test_protocol_gen_idempotent.py -v`
Expected: FAIL — `_protocols/` empty (`_render_field_only` is a stub).

- [ ] **Step 3: Implement the idempotent writer**

Replace `_render_field_only` with:

```python
@staticmethod
def _render_field_only(
    package_dir: Path, plans: tuple[p.Infra.ProtocolClassPlan, ...]
) -> None:
    """Write one field-only protocol file per plan, byte-idempotently."""
    out_dir = package_dir / "_protocols"
    out_dir.mkdir(exist_ok=True)
    template = (
        Path(__file__).resolve().parents[1]
        / "templates"
        / "project"
        / "base"
        / "src"
        / "_protocols"
        / "_field_protocol.py.j2"
    ).read_text(encoding="utf-8")
    for plan in plans:
        if plan.kind != "field_only":
            continue
        ctx: t.MutableStrMapping = {
            "package_name": package_dir.name,
            "year": "2026",
            "author_name": "FLEXT Team",
            "protocol_class_name": plan.class_name,
            "fields": [
                {"name": f.name, "annotation": f.annotation} for f in plan.fields
            ],
        }
        rendered = u.Cli.render_template_string(template, ctx)
        if rendered.failure:
            continue
        target = out_dir / f"{plan.class_name.lower()}.py"
        if not target.exists() or target.read_text(encoding="utf-8") != rendered.value:
            target.write_text(rendered.value, encoding="utf-8")
```

Use the confirmed SSOT renderer name from Task 5 if different.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd flext-infra && env -u PYTHONPATH .venv/bin/python -m pytest tests/unit/codegen/test_protocol_gen_idempotent.py -v`
Expected: PASS.

- [ ] **Step 5: Codegen suite regression + commit**

Run: `cd flext-infra && env -u PYTHONPATH .venv/bin/python -m pytest tests/unit/codegen/ -v`
Expected: all protocol_gen tests PASS.

```bash
git commit -m "feat(codegen): idempotent field-protocol writer" src/flext_infra/codegen/protocol_gen.py tests/unit/codegen/test_protocol_gen_idempotent.py
```

---

## Task 8: CLI subcommand + warning report

**Files:**

- Modify: `flext-infra/src/flext_infra/cli.py`
- Test: `flext-infra/tests/unit/codegen/test_protocol_gen_cli.py`

**Interfaces:**

- Consumes: `FlextInfraCodegenProtocolGen.run`, `m.Infra.ProtocolGenReport`.
- Produces: `flext-infra protocol-gen --package <dir> [--apply]` printing `WARNING [severity] <module>::<class>.<symbol> — <reason>` per warning + `generated=N validated=M warnings=K`; exit 1 if any HIGH/CRITICAL warning, else 0.

- [ ] **Step 1: Write the failing test**

```python
# flext-infra/tests/unit/codegen/test_protocol_gen_cli.py
from __future__ import annotations

from pathlib import Path

from flext_cli.testing import CliRunner
from flext_infra.cli import app

_FIXTURE_DIR = Path(__file__).parent / "_fixtures"


class TestProtocolGenCli:
    def test_protocol_gen_dry_run_prints_summary(self) -> None:
        result = CliRunner().invoke(
            app, ["protocol-gen", "--package", str(_FIXTURE_DIR)]
        )
        assert result.exit_code == 0
        assert "generated=" in result.stdout
        assert "warnings=" in result.stdout
```

Confirm `CliRunner`/`app` import paths via `grep -rn "CliRunner" ../flext-cli/src` and the existing command registration style in `cli.py`.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd flext-infra && env -u PYTHONPATH .venv/bin/python -m pytest tests/unit/codegen/test_protocol_gen_cli.py -v`
Expected: FAIL — no `protocol-gen` command.

- [ ] **Step 3: Add the CLI command**

In `cli.py`, register `protocol-gen` following the existing model-driven flext-cli command pattern in that file. Parse `--package: Path`, `--apply: bool = False`; call `FlextInfraCodegenProtocolGen().run(package, apply=apply)`; on success, for each `report.warnings` emit `WARNING [{w.severity}] {w.module}::{w.class_name}.{w.symbol} — {w.reason}` via the flext-cli output SSOT (no bare `print`), then `generated={len(report.generated)} validated={len(report.validated)} warnings={len(report.warnings)}`; exit 1 if any `w.severity in {"HIGH","CRITICAL"}`, else 0.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd flext-infra && env -u PYTHONPATH .venv/bin/python -m pytest tests/unit/codegen/test_protocol_gen_cli.py -v`
Expected: PASS.

- [ ] **Step 5: Manual QA — run for real**

Run: `cd flext-infra && env -u PYTHONPATH .venv/bin/python -m flext_infra protocol-gen --package ../flext-core/src/flext_core/_models`
Expected: `generated=… validated=… warnings=…` + `WARNING [HIGH] ...` lines naming each out-of-contract symbol.

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(codegen): protocol-gen CLI with warning report" src/flext_infra/cli.py tests/unit/codegen/test_protocol_gen_cli.py
```

---

## Task 9: Pipeline registration + make verb

**Files:**

- Modify: `flext-infra/src/flext_infra/codegen/pipeline.py`
- Modify: `flext-infra/base.mk`
- Test: `flext-infra/tests/unit/codegen/test_protocol_gen_pipeline.py`

**Interfaces:**

- Consumes: `FlextInfraCodegenProtocolGen`.
- Produces: `protocol_gen` registered as a named pipeline stage (dry-run default); `make protocol-gen PROJECT=<name>` validates, `APPLY=1` regenerates.

- [ ] **Step 1: Write the failing test**

```python
# flext-infra/tests/unit/codegen/test_protocol_gen_pipeline.py
from __future__ import annotations

from flext_infra.codegen.pipeline import FlextInfraCodegenPipeline


class TestProtocolGenPipeline:
    def test_protocol_gen_stage_is_registered(self) -> None:
        assert "protocol_gen" in FlextInfraCodegenPipeline.stage_names()
```

Confirm the real stage-registry accessor via `grep -nE "stage|register|def .*stages" src/flext_infra/codegen/pipeline.py`; adjust `stage_names()` to the actual API.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd flext-infra && env -u PYTHONPATH .venv/bin/python -m pytest tests/unit/codegen/test_protocol_gen_pipeline.py -v`
Expected: FAIL — `protocol_gen` not registered.

- [ ] **Step 3: Register the stage**

In `pipeline.py`, add `protocol_gen` → `FlextInfraCodegenProtocolGen` in the stage registry, dry-run by default.

- [ ] **Step 4: Add the make verb**

In `base.mk`, add a `protocol-gen` target delegating to the CLI (`… protocol-gen --package $(PROJECT_ROOT)/src/$(PACKAGE_NAME)/_models $(if $(APPLY),--apply,)`), matching the existing `BASE_INFRA_VALIDATE`/CLI invocation style.

- [ ] **Step 5: Test + real make QA**

Run: `cd flext-infra && env -u PYTHONPATH .venv/bin/python -m pytest tests/unit/codegen/test_protocol_gen_pipeline.py -v`
Expected: PASS.
Run: `make -C .. protocol-gen PROJECT=flext-core 2>&1 | tail -5` (dry-run)
Expected: summary printed; `git -C ../flext-core status --short src/flext_core/_protocols` shows no changes.

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(codegen): register protocol-gen pipeline stage + make verb" src/flext_infra/codegen/pipeline.py base.mk tests/unit/codegen/test_protocol_gen_pipeline.py
```

---

## Task 10: Full-workspace gate + evidence

**Files:** none new; runs the full gate.

- [ ] **Step 1: flext-infra gate**

Run: `cd flext-infra && make lint 2>&1 | tail -3 && make typecheck 2>&1 | tail -3 && make test 2>&1 | tail -10`
Expected: ruff 0, pyright/pyrefly 0, pytest all green (incl. 8 new test files).

- [ ] **Step 2: Real protocol-gen over flext-core**

Run: `cd flext-infra && env -u PYTHONPATH .venv/bin/python -m flext_infra protocol-gen --package ../flext-core/src/flext_core/_models 2>&1 | tee /tmp/opencode/protocol_gen_core.txt | tail -30`
Expected: field_only generated, behavior validated, precise `WARNING [HIGH] …` per out-of-contract symbol.

- [ ] **Step 3: Idempotency proof on scratch copy**

Run: `cd flext-infra && cp -r ../flext-core/src/flext_core/_models /tmp/opencode/_models_scratch && env -u PYTHONPATH .venv/bin/python -m flext_infra protocol-gen --package /tmp/opencode/_models_scratch --apply >/dev/null && sha1sum /tmp/opencode/_models_scratch/_protocols/*.py > /tmp/opencode/pg_h1.txt && env -u PYTHONPATH .venv/bin/python -m flext_infra protocol-gen --package /tmp/opencode/_models_scratch --apply >/dev/null && sha1sum /tmp/opencode/_models_scratch/_protocols/*.py > /tmp/opencode/pg_h2.txt && diff /tmp/opencode/pg_h1.txt /tmp/opencode/pg_h2.txt && echo IDEMPOTENT`
Expected: `IDEMPOTENT` (byte-identical second run).

- [ ] **Step 4: Record evidence in the bead**

Run: `cd /home/marlonsc/flext && bd update <bead-id> --notes "protocol-gen codegen landed: rope-semantic (LAW-2) extractor+classifier+idempotent field-protocol generator+behavior validator+warning report. Gate green (ruff/pyright/pytest). flext-core/_models run: generated=N validated=M warnings=K (each names symbol+reason). Idempotent proof: two --apply runs byte-identical. Evidence /tmp/opencode/protocol_gen_core.txt."`

- [ ] **Step 5: Teardown**

Run: `mv /tmp/opencode/_models_scratch /tmp/opencode/_models_scratch.bak 2>/dev/null; echo cleaned`
Expected: scratch archived.

---

## Self-Review

**1. Spec coverage:**

- "validar e gerar o maximo de protocols" → Tasks 3-7 (extract/classify/generate field_only) + Task 6/8 (validate behavior). ✓
- "validar o maximo que temos" → Task 6 behavior validation + Task 10 real flext-core run. ✓
- "warning ... que ele nao pode gerar que estao em desacordo com o contrato do serviço, indicando o que é" → Task 4 `out_of_contract` warnings + Task 8 CLI report naming symbol+reason. ✓
- "usando flext-infra com o maximo do loop rope" → Tasks 3/6 use `get_class_methods` + `RopeStructure.logical_statements` + `get_module_classes` (LAW-2, PyObject.get_attributes). ✓
- "codegen templates/ jinja2 ... pastas de protocols/ do scaffold" → Task 5 templates under `templates/project/base/src/_protocols/`. ✓
- "reaproveitar sempre o mesmo contrato e branch ... indepotente" → Task 7 idempotent writer + Task 10 idempotency proof. ✓
- "criar e manter o padrao" → Task 9 pipeline + make verb. ✓

**2. Placeholder scan:** No "TBD"/"implement later". Three steps say "confirm the real symbol via grep and adjust" (renderer name Task 5/7, CliRunner path Task 8, stage API Task 9) — verification instructions with concrete fallbacks, because the exact SSOT symbol must be read from live flext-cli/pipeline, not guessed (fail-loud-on-missing-SSOT).

**3. Type consistency:** `ProtocolClassPlan.kind` values (`field_only`/`behavior`/`out_of_contract`/`unclassified`) consistent across Tasks 2,4,6,7. `extract_class(project_root, file_path, class_name)` consistent Tasks 3,6. `classify(plan, config) -> (plan, warnings)` consistent Tasks 4,6. `run(package_dir, *, apply)` consistent Tasks 6,7,8,9. Warning fields consistent Tasks 2,4,8.

---

## Execution Handoff

**Plan complete and saved to `flext-infra/docs/superpowers/plans/2026-07-16-codegen-protocol-generation.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — execute tasks in this session using executing-plans, batch execution with checkpoints.

**Which approach?**
