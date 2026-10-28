"""Constant-consumer evidence for staged semantic cutovers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import sys
from typing import TYPE_CHECKING

import pytest

from flext_infra import infra
from flext_infra.codemod import FlextInfraCodemodSemanticApply
from tests import c, m, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraSemanticConstantCutover:
    """Constant consumers resolve upstream bindings and cut over atomically."""

    @staticmethod
    @pytest.mark.parametrize("guarded", [False, True])
    @pytest.mark.parametrize(
        "upstream_import",
        [
            "from flext_core import c as core_c",
            "from flext_core.constants import FlextConstants as core_c",
        ],
    )
    def test_constant_consumers_resolve_upstream_binding_without_shadow_rewrites(
        tmp_path: Path,
        upstream_import: str,
        *,
        guarded: bool,
    ) -> None:
        """Inherited constants use the existing facade and reach a fixed point."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = u.Infra.facade_family_declared_by(c.Infra.CONSTANTS_PY)
        owner = f"{u.derive_class_stem(root.name)}{family.suffix}"
        path = package / "consumer.py"
        shadowed = "def local(core_c):\n    return c.PRIMITIVES_TYPES\n"
        sources = {
            package / c.Infra.CONSTANTS_PY: (
                "from flext_cli import c\n"
                f"class {owner}(c):\n    pass\n"
                f"c = {owner}\n"
                f'__all__ = ["{owner}", "c"]\n'
            ),
            package / c.Infra.INIT_PY: 'from .constants import c\n__all__ = ["c"]\n',
            path: (
                f"{upstream_import}\n"
                f"from {package.name} import c\n"
                "upstream = c.PRIMITIVES_TYPES\n"
                "downstream = c.PRIMITIVES_TYPES\n\n"
                f"{shadowed}"
            ),
        }
        if guarded:
            sources[path] = (
                "from __future__ import annotations\n"
                "from typing import TYPE_CHECKING\n"
                f"from {package.name} import c\n"
                "# Keep the provider documentation.\n"
                "if TYPE_CHECKING:  # Annotation boundary.\n"
                f"    {upstream_import}\n"
                "def annotated(value: core_c):\n"
                "    return c.PRIMITIVES_TYPES\n"
                "downstream = c.PRIMITIVES_TYPES\n\n"
                f"{shadowed}"
            )
        for source_path, source in sources.items():
            source_path.write_text(source, encoding="utf-8")
        phase = c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS
        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                phase,
                rope_workspace=rope,
                sources=sources,
            )
            tm.ok(planned)
            tm.that(tuple(edit.file_path for edit in planned.value), eq=(path,))
            updated = planned.value[0].updated_source
            if guarded:
                tm.that(updated, has="def annotated(value: c):")
                tm.that(updated, has="# Keep the provider documentation.")
                tm.that(updated, has="# Annotation boundary.")
                tm.that(updated, lacks="TYPE_CHECKING")
            else:
                tm.that(updated, has="upstream = c.PRIMITIVES_TYPES")
            tm.that(updated, has="downstream = c.PRIMITIVES_TYPES")
            tm.that(updated, has=shadowed)
            tm.that(updated.count(f"from {package.name} import c"), eq=1)
            tm.fail(upstream_import in updated)
            remaining = u.Infra.plan_semantic_cutover(
                phase,
                rope_workspace=rope,
                sources={**sources, path: updated},
            )
        tm.ok(remaining)
        tm.that(remaining.value, empty=True)
        for source_path, source in sources.items():
            tm.that(source_path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    @pytest.mark.parametrize("case", ["ambiguous", "cyclic"])
    def test_constant_consumers_reject_unproven_upstream_bindings(
        tmp_path: Path,
        case: str,
    ) -> None:
        """Competing terminal identities and export cycles never yield edits."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        upstream = package.parent / "flext_upstream"
        upstream.mkdir()
        family = u.Infra.facade_family_declared_by(c.Infra.CONSTANTS_PY)
        owner = f"{u.derive_class_stem(root.name)}{family.suffix}"
        sources = {
            package / c.Infra.CONSTANTS_PY: (
                f'class {owner}:\n    pass\nc = {owner}\n__all__ = ["{owner}", "c"]\n'
            ),
            package / "consumer.py": (
                "from flext_upstream import c as core_c\n"
                f"from {package.name} import c\n"
                "value = c.PRIMITIVES_TYPES\n"
            ),
            upstream / c.Infra.INIT_PY: (
                "from .left import Left as c\nfrom .right import Right as c\n"
                if case == "ambiguous"
                else "from .loop import c\n"
            ),
            upstream / "left.py": "class Left:\n    pass\n",
            upstream / "right.py": "class Right:\n    pass\n",
            upstream / "loop.py": "from . import c\n",
        }
        for path, source in sources.items():
            path.write_text(source, encoding="utf-8")
        with (
            infra.rope_workspace(root) as rope,
            pytest.raises(ValueError, match=case) as raised,
        ):
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS,
                rope_workspace=rope,
                sources=sources,
            )
        tm.that(str(raised.value), has="flext_upstream.c")
        for path, source in sources.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    @pytest.mark.parametrize("alias", ["c", "constants"])
    @pytest.mark.parametrize("guarded", [False, True])
    def test_nonprefixed_constants_qualify_public_owners_without_value_dedupe(
        tmp_path: Path, alias: str, *, guarded: bool
    ) -> None:
        """Published project owners preserve SDK ancestry, domains and lexical scope."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="signal-hub", package_name="signal_hub"
        )
        family = package / "_constants"
        family.mkdir()
        consumer = package / "consumer.py"
        private = package / "private_consumer.py"
        declaration = f"from {package.name} import c"
        if alias != "c":
            declaration += f" as {alias}"
        sources = {
            family / "base.py": (
                "from enum import StrEnum\n"
                "class SignalConstantsBase:\n"
                "    TOKEN = 'shared-domain-value'\n"
                "    EXISTING = 'nested-domain-value'\n"
                "    class Mode(StrEnum):\n"
                "        READY = 'ready'\n"
            ),
            family / "other.py": (
                "from enum import StrEnum\n"
                "class SignalConstantsOther:\n"
                "    OTHER_TOKEN = 'shared-domain-value'\n"
                "    class OtherMode(StrEnum):\n"
                "        READY = 'ready'\n"
            ),
            package / c.Infra.CONSTANTS_PY: (
                "from flext_infra import c as upstream\n"
                f"from {package.name}._constants.base import SignalConstantsBase\n"
                f"from {package.name}._constants.other import SignalConstantsOther\n"
                "class SignalHubConstants(upstream):\n"
                "    class SignalHub:\n"
                "        EXISTING = 'published-flat-value'\n"
                "        Base = SignalConstantsBase\n"
                "        Other = SignalConstantsOther\n"
                "c = SignalHubConstants\n"
                "__all__ = ['SignalHubConstants', 'c']\n"
            ),
            package / c.Infra.INIT_PY: "from .constants import c\n__all__ = ['c']\n",
            consumer: (
                '"""c.SignalHub.TOKEN remains documentation."""\n'
                "from __future__ import annotations\n"
                "from pathlib import Path\n"
                "from typing import TYPE_CHECKING\n"
                + (
                    f"if TYPE_CHECKING:\n    {declaration}\n"
                    if guarded
                    else f"{declaration}\n"
                )
                + f"def accept(value: {alias}.SignalHub.Mode):\n    return value\n"
                + (
                    ""
                    if guarded
                    else (
                        f"value = {alias}.SignalHub.Mode.READY\n"
                        f"published = {alias}.SignalHub.Base.Mode.READY\n"
                        f"flat = {alias}.SignalHub.EXISTING\n"
                        f"other = {alias}.SignalHub.OtherMode.READY\n"
                        f"token = {alias}.SignalHub.TOKEN\n"
                        f"other_token = {alias}.SignalHub.OTHER_TOKEN\n"
                        f"sdk = {alias}.Cli.FILE_FORMAT_JSON\n"
                        f"infra = {alias}.Infra.GIT_OID_HEX_LENGTH_SHA1\n"
                        f"core = {alias}.PRIMITIVES_TYPES\n"
                    )
                )
                + f"note = '{alias}.SignalHub.TOKEN'\n"
                + "location = Path(__file__).name\n"
                + f"# {alias}.SignalHub.TOKEN is not an executable reference.\n"
                + f"def shadow({alias}):\n    return {alias}.SignalHub.TOKEN\n"
            ),
            private: (
                "from __future__ import annotations\n"
                "from flext_infra import c\n"
                f"from {package.name}._constants.base import "
                "SignalConstantsBase as Internal\n"
                "value = Internal.Mode.READY\n"
                "def accept(value: Internal):\n    return value\n"
                "sdk = c.Cli.FILE_FORMAT_JSON\n"
            ),
        }
        for path, source in sources.items():
            path.write_text(source, encoding=c.DEFAULT_ENCODING)
        originals = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in sources
        )
        phase = c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    phase, rope_workspace=rope, sources=sources
                )
            )
        tm.that({edit.file_path for edit in edits}, eq={consumer, private})
        tm.ok(u.Cli.atomic_verify_binary_file_states(originals))
        proposed = {
            **sources,
            **{edit.file_path: edit.updated_source for edit in edits},
        }
        for edit in edits:
            tm.ok(u.Cli.atomic_write_text_file(edit.file_path, edit.updated_source))
        with infra.rope_workspace(root) as rope:
            tm.that(
                tm.ok(
                    u.Infra.plan_semantic_cutover(
                        phase, rope_workspace=rope, sources=proposed
                    )
                ),
                empty=True,
            )
        probe = (
            "from typing import get_type_hints\n"
            f"from {package.name} import c, consumer, private_consumer\n"
            "from flext_infra import c as sdk\n"
            "class Local:\n    class SignalHub:\n        TOKEN = 'local'\n"
            "assert consumer.shadow(Local) == 'local'\n"
            f"assert consumer.location == {consumer.name!r}\n"
            f"assert consumer.note == '{alias}.SignalHub.TOKEN'\n"
            "assert consumer.__doc__ == 'c.SignalHub.TOKEN remains documentation.'\n"
            f"namespace = {{**vars(consumer), '{alias}': c}}\n"
            "assert get_type_hints(consumer.accept, globalns=namespace)['value'] "
            "is c.SignalHub.Base.Mode\n"
            "assert private_consumer.value is c.SignalHub.Base.Mode.READY\n"
            "assert get_type_hints(private_consumer.accept)['value'] "
            "is c.SignalHub.Base\n"
            "assert private_consumer.sdk == sdk.Cli.FILE_FORMAT_JSON\n"
        )
        if not guarded:
            probe += (
                "assert consumer.value is c.SignalHub.Base.Mode.READY\n"
                "assert consumer.published is c.SignalHub.Base.Mode.READY\n"
                "assert consumer.flat == c.SignalHub.EXISTING\n"
                "assert consumer.flat != c.SignalHub.Base.EXISTING\n"
                "assert consumer.other is c.SignalHub.Other.OtherMode.READY\n"
                "assert consumer.value == consumer.other\n"
                "assert type(consumer.value) is not type(consumer.other)\n"
                "assert consumer.token == c.SignalHub.Base.TOKEN\n"
                "assert consumer.other_token == c.SignalHub.Other.OTHER_TOKEN\n"
                "assert consumer.sdk == sdk.Cli.FILE_FORMAT_JSON\n"
                "assert consumer.infra == sdk.Infra.GIT_OID_HEX_LENGTH_SHA1\n"
                "assert consumer.core is sdk.PRIMITIVES_TYPES\n"
            )
        output = tm.ok(
            u.Cli.run_raw(
                (sys.executable, "-c", probe),
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env={c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(package.parent)}
                ),
            )
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)
        tm.that(
            consumer.read_text(encoding=c.DEFAULT_ENCODING),
            has=f"# {alias}.SignalHub.TOKEN is not an executable reference.",
        )

    @staticmethod
    @pytest.mark.parametrize(
        "case", ["same-value", "different-value", "identity-depth"]
    )
    def test_nonprefixed_constants_reject_competing_publications_before_writes(
        tmp_path: Path, case: str
    ) -> None:
        """Neither equal values nor a shorter path elect a competing public owner."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="signal-hub", package_name="signal_hub"
        )
        family = package / "_constants"
        family.mkdir()
        sources = {
            family / "base.py": "class Chosen:\n    TOKEN = 'domain-value'\n",
            package / c.Infra.INIT_PY: "from .constants import c\n__all__ = ['c']\n",
            package / c.Infra.CONSTANTS_PY: (
                f"from {package.name}._constants.base import Chosen\n"
                "class SignalHubConstants:\n"
                "    class SignalHub:\n"
                "        Base = Chosen\n"
                + (
                    "        class Nested:\n            Published = Chosen\n"
                    if case == "identity-depth"
                    else (
                        "        class Other:\n"
                        "            TOKEN = "
                        + ("'domain-value'\n" if case == "same-value" else "'other'\n")
                    )
                )
                + "c = SignalHubConstants\n__all__ = ['SignalHubConstants', 'c']\n"
            ),
            package / "consumer.py": (
                f"from {package.name}._constants.base import Chosen\n"
                "value = Chosen.TOKEN\n"
                if case == "identity-depth"
                else f"from {package.name} import c\nvalue = c.SignalHub.TOKEN\n"
            ),
        }
        for path, source in sources.items():
            path.write_text(source, encoding=c.DEFAULT_ENCODING)
        originals = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in sources
        )
        with (
            infra.rope_workspace(root) as rope,
            pytest.raises(ValueError, match="ambiguous public owners"),
        ):
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS,
                rope_workspace=rope,
                sources=sources,
            )
        tm.ok(u.Cli.atomic_verify_binary_file_states(originals))

    @staticmethod
    def test_annotations_and_nesting_complete_in_one_atomic_cutover(
        tmp_path: Path,
    ) -> None:
        """Test annotations and nesting complete in one atomic cutover."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = u.Infra.facade_family_declared_by(c.Infra.CONSTANTS_PY)
        owner = f"{u.derive_class_stem(root.name)}{family.suffix}"
        path = package / "constants.py"
        u.Tests.write_lazy_init_namespace_module(
            path,
            class_name=owner,
            alias="c",
            extra_class_names=(f"{owner}Member",),
        )
        tm.ok(u.Tests.provision_python_project_environment(root))
        source = path.read_text(encoding="utf-8").replace(
            "from __future__ import annotations\n",
            "",
        )
        path.write_text(source, encoding="utf-8")
        finding = m.Infra.ModOccurrence(
            rule_file="require-future-annotations.yml",
            rule_id="require-future-annotations",
            repository=root.name,
            file=path.relative_to(root),
            range={},
            text=source,
            actionable=False,
            classification=c.Infra.ModScanFindingClass.DETECTION_ONLY,
        )
        report = m.Infra.ModOccurrenceReport(
            files=frozenset({path}),
            entries=(finding,),
        )
        with infra.rope_workspace(root) as rope:
            tm.ok(
                FlextInfraCodemodSemanticApply.apply(
                    root,
                    report,
                    rope,
                    workspace_factory=infra.rope_workspace,
                )
            )
        published = path.read_text(encoding="utf-8")
        tm.that(published, has="from __future__ import annotations")
        tm.that(published, has=f"    class {owner}Member")
        with infra.rope_workspace(root) as rope:
            tm.ok(
                FlextInfraCodemodSemanticApply.apply(
                    root,
                    report,
                    rope,
                    workspace_factory=infra.rope_workspace,
                )
            )
        tm.that(path.read_text(encoding="utf-8"), eq=published)

    @staticmethod
    def test_nesting_replans_proposed_sources_without_publishing(
        tmp_path: Path,
    ) -> None:
        """Test nesting replans proposed sources without publishing."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = u.Infra.facade_family_declared_by(c.Infra.CONSTANTS_PY)
        owner = f"{u.derive_class_stem(root.name)}{family.suffix}"
        path = package / "constants.py"
        u.Tests.write_lazy_init_namespace_module(
            path,
            class_name=owner,
            alias="c",
            extra_class_names=(f"{owner}Member",),
        )
        original = path.read_text(encoding="utf-8")
        nesting = c.Infra.SemanticCutoverPhase.CLASS_NESTING
        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                nesting,
                rope_workspace=rope,
                sources={path: original},
            )
            tm.ok(planned)
            tm.that(len(planned.value), eq=1)
            tm.that(
                planned.value[0].changes,
                eq=(f"nested {owner}Member under {owner}",),
            )
            remaining = u.Infra.plan_semantic_cutover(
                nesting,
                rope_workspace=rope,
                sources={path: planned.value[0].updated_source},
            )
        tm.ok(remaining)
        tm.that(remaining.value, empty=True)
        tm.that(path.read_text(encoding="utf-8"), eq=original)

    @staticmethod
    def test_nesting_reports_every_module_without_an_owner_as_a_failure(
        tmp_path: Path,
    ) -> None:
        """Rival stem-carrying classes leave the owner undecidable: the plan fails."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "models.py"
        stem = (
            f"{u.derive_class_stem(root.name)}"
            f"{u.Infra.facade_family_declared_by(c.Infra.MODELS_PY).suffix}"
        )
        source = (
            f"class {stem}FirstCandidate:\n    pass\n\n"
            f"class {stem}SecondCandidate:\n    pass\n\n"
            f'__all__ = ["{stem}FirstCandidate", "{stem}SecondCandidate"]\n'
        )
        path.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                rope_workspace=rope,
                sources={path: source},
            )
        tm.fail(planned, has="requires exactly one declared module owner")
