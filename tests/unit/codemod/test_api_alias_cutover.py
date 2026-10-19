"""Public utility evidence for semantic API-alias cutovers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from flext_infra import c, infra, m, t
from tests import tm, u


class TestsFlextInfraApiAliasCutover:
    """Exercise owner-first alias removal only through ``u.Infra``."""

    @staticmethod
    def _service_workspace(
        tmp_path: Path,
        consumer: str,
    ) -> t.Pair[Path, t.MappingKV[Path, str]]:
        """Build a real local foundation with the existing lazy root publisher."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        sources = {
            package / "foundation.py": (
                "from flext_core import p, s\nfrom flext_infra import m\n\n"
                "class FlextSampleService[T: p.Base](s[T], m.Infra.CommandContext):\n"
                "    @staticmethod\n    def delayed():\n        return s\n\n"
                "s = FlextSampleService\n"
                '__all__ = ["FlextSampleService", "s"]\n'
            ),
            package / "__init__.py": (
                "from types import MappingProxyType\n"
                "from typing import TYPE_CHECKING\n"
                "if TYPE_CHECKING:\n"
                "    from .foundation import FlextSampleService, s\n"
                "from flext_core.lazy import install_lazy_exports\n"
                "install_lazy_exports(__name__, globals(), MappingProxyType({\n"
                '    "FlextSampleService": ".foundation", "s": ".foundation",\n'
                "}))\n"
                '__all__ = ["FlextSampleService", "s"]\n'
            ),
            package / "consumer.py": consumer.replace("sample_pkg", package.name),
            package
            / "kernel.py": "from flext_core import s\nclass Kernel(s[str]):\n    pass\n",
        }
        for path, source in sources.items():
            path.write_text(source, encoding=c.DEFAULT_ENCODING)
        return root, sources

    @staticmethod
    @pytest.mark.parametrize(
        ("statement", "base", "expected"),
        [
            ("from sample_pkg import s", "s", "FlextSampleService"),
            ("from sample_pkg.foundation import s", "s", "FlextSampleService"),
            ("import sample_pkg as own", "own.s", "own.FlextSampleService"),
            (
                "import sample_pkg.foundation",
                "sample_pkg.foundation.s",
                "sample_pkg.foundation.FlextSampleService",
            ),
        ],
    )
    def test_service_retirement_preserves_kernel_context_and_shadowing(
        tmp_path: Path,
        statement: str,
        base: str,
        expected: str,
    ) -> None:
        """No scanner finding or filename convention substitutes for real identity."""
        root, sources = TestsFlextInfraApiAliasCutover._service_workspace(
            tmp_path,
            f"{statement}\nclass Consumer({base}[str]):\n    pass\n"
            'def shadowed(s):\n    return s\nliteral = "s"\n',
        )
        with infra.rope_workspace(root) as workspace:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.COMPAT_ALIAS,
                    rope_workspace=workspace,
                    sources=sources,
                )
            )
            updated = {
                **sources,
                **{edit.file_path: edit.updated_source for edit in edits},
            }
            owner = next(path for path in sources if path.name == "foundation.py")
            consumer = owner.with_name("consumer.py")
            tm.that(updated[owner], has="class FlextSampleService[T: p.Base](s[T],")
            tm.that(updated[owner], has="from flext_core import p, s")
            tm.that(updated[owner], has="return FlextSampleService")
            tm.that(updated[owner], lacks="s = FlextSampleService")
            tm.that(updated[owner], lacks='"s"')
            destination = expected.replace("sample_pkg", owner.parent.name)
            tm.that(updated[consumer], has=f"class Consumer({destination}[str]):")
            if base == "s":
                tm.that(
                    updated[consumer],
                    has=f"from {owner.parent.name} import FlextSampleService",
                )
            tm.that(updated[consumer], has="def shadowed(s):\n    return s")
            tm.that(updated[consumer], has='literal = "s"')
            tm.that(
                updated[owner.with_name("kernel.py")],
                eq=sources[owner.with_name("kernel.py")],
            )
            tm.that(
                tm.ok(
                    u.Infra.plan_semantic_cutover(
                        c.Infra.SemanticCutoverPhase.COMPAT_ALIAS,
                        rope_workspace=workspace,
                        sources=updated,
                    )
                ),
                eq=(),
            )
        for path, source in updated.items():
            path.write_text(source, encoding=c.DEFAULT_ENCODING)
        outcome = tm.ok(
            u.Cli.run((
                sys.executable,
                "-c",
                (
                    f"import sys; sys.path.insert(0, {str(owner.parent.parent)!r}); "
                    f"from {owner.parent.name} import FlextSampleService; "
                    f"from {owner.parent.name}.consumer import Consumer; "
                    f"from pathlib import Path; service = Consumer(repository_root={str(root)!r}); "
                    f"assert service.repository_root == Path({str(root)!r}); "
                    "assert service.delayed() is FlextSampleService"
                ),
            ))
        )
        tm.that(u.Cli.process_succeeded(outcome.outcome), eq=True)

    @staticmethod
    @pytest.mark.parametrize(
        ("consumer", "reason"),
        [
            (
                "from sample_pkg import s\ndef capture(FlextSampleService):\n    return s\n",
                "shadowed",
            ),
            ('import sample_pkg\nvalue = getattr(sample_pkg, "s")\n', "reflective"),
        ],
    )
    def test_service_retirement_refuses_uncovered_bindings(
        tmp_path: Path,
        consumer: str,
        reason: str,
    ) -> None:
        """A captured destination or reflective access prevents owner retirement."""
        root, sources = TestsFlextInfraApiAliasCutover._service_workspace(
            tmp_path, consumer
        )
        with (
            infra.rope_workspace(root) as workspace,
            pytest.raises(ValueError, match=reason),
        ):
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.COMPAT_ALIAS,
                rope_workspace=workspace,
                sources=sources,
            )
        tm.that(
            {path: path.read_text(encoding=c.DEFAULT_ENCODING) for path in sources},
            eq=sources,
        )

    @staticmethod
    @pytest.mark.parametrize(
        "consumer_source",
        [
            "from flext_sample.api import sample\n\nfacade = sample\n",
            (
                "if condition:\n"
                "    from flext_sample.api import sample\n"
                "else:\n"
                "    from flext_sample import sample\n"
                "facade = sample\n"
            ),
        ],
    )
    def test_rewires_consumer_before_removing_owner(
        tmp_path: Path,
        consumer_source: str,
    ) -> None:
        """Plan the complete owner/export/import/reference cutover together."""
        owner = tmp_path / "flext-sample/src/flext_sample/api.py"
        consumer = tmp_path / "flext-sample/tests/test_api.py"
        sources = {
            owner: (
                "class FlextSample:\n"
                "    pass\n\n"
                "sample = FlextSample\n"
                "facade = sample\n"
                '__all__ = ["FlextSample", "sample"]\n'
            ),
            consumer: consumer_source,
        }
        finding = m.Infra.ModOccurrence(
            rule_file="ban-compat-alias.yml",
            rule_id="ban-compat-alias",
            repository="flext-sample",
            file=owner.relative_to(tmp_path),
            range={},
            text="sample = FlextSample",
            actionable=False,
            classification=c.Infra.ModScanFindingClass.DETECTION_ONLY,
        )

        with infra.rope_workspace(tmp_path) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.COMPAT_ALIAS,
                rope_workspace=rope,
                sources=sources,
                findings=(finding,),
            )
        tm.ok(planned)
        edits = planned.value
        by_path = {edit.file_path: edit.updated_source for edit in edits}

        tm.that(len(edits), eq=2)
        tm.that(by_path[owner], lacks="sample = FlextSample")
        tm.that(by_path[owner], lacks='"sample"')
        tm.that(by_path[owner], has="facade = FlextSample")
        tm.that(by_path[consumer], has="from flext_sample.api import FlextSample")
        tm.that(by_path[consumer], has="facade = FlextSample")
        tm.that(by_path[consumer], lacks="import sample")

    @staticmethod
    @pytest.mark.parametrize(
        ("module", "receiver"),
        [
            ("flext_sample.api as sample_api", "sample_api"),
            ("flext_sample as sample_api", "sample_api"),
            ("flext_sample.api", "flext_sample.api"),
        ],
    )
    def test_module_attributes_require_import_identity(
        tmp_path: Path,
        module: str,
        receiver: str,
    ) -> None:
        """Rewrite proven module reads without changing shadowed or literal uses."""
        owner = tmp_path / "flext-sample/src/flext_sample/api.py"
        consumer = tmp_path / "flext-sample/tests/test_api.py"
        binding = receiver.split(".", maxsplit=1)[0]
        unchanged = (
            f"def shadowed({binding}):\n"
            f"    return {receiver}.sample\n\n"
            "def rebound(values):\n"
            f"    {binding} = values\n"
            f"    return {receiver}.sample\n\n"
            "def homonym():\n"
            f"    import unrelated as {binding}\n"
            f"    return {receiver}.sample\n\n"
            "def comprehension(values):\n"
            f"    return [{receiver}.sample for {binding} in values]\n\n"
            'payload = "sample_api.sample"\n'
            'literal = Literal["sample_api.sample"]\n'
            'metadata = Annotated[str, "sample_api.sample"]\n'
            'reflection_name = "sample"\n'
            f'reflected_target = getattr({receiver}, "FlextSample")\n'
            f'other_attribute = getattr({receiver}, "__name__")\n'
            f"def reflective_shadowed({binding}):\n"
            f'    return getattr({receiver}, "sample")\n\n'
            "def getter_shadowed(getattr, value):\n"
            '    return getattr(value, "sample")\n\n'
            "def local_getter(value):\n"
            "    def getattr(value, name):\n"
            "        return name\n"
            '    return getattr(value, "sample")\n\n'
            "def reflective_homonym():\n"
            f"    import unrelated as {binding}\n"
            f'    return getattr({receiver}, "sample")\n\n'
            f"def reflective_dynamic_shadowed({binding}, attribute):\n"
            f"    return getattr({receiver}, attribute)\n"
        )
        sources = {
            owner: (
                "class FlextSample:\n"
                "    pass\n\n"
                "sample = FlextSample\n"
                '__all__ = ["FlextSample", "sample"]\n'
            ),
            consumer: (
                f"import {module}\n"
                "from typing import Annotated, Literal\n\n"
                f"facade = {receiver}.sample\n\n"
                "def local_import():\n"
                f"    import {module}\n"
                f"    return {receiver}.sample\n\n" + unchanged
            ),
        }
        finding = m.Infra.ModOccurrence(
            rule_file="ban-compat-alias.yml",
            rule_id="ban-compat-alias",
            repository="flext-sample",
            file=owner.relative_to(tmp_path),
            range={},
            text="sample = FlextSample",
            actionable=False,
            classification=c.Infra.ModScanFindingClass.DETECTION_ONLY,
        )

        with infra.rope_workspace(tmp_path) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.COMPAT_ALIAS,
                rope_workspace=rope,
                sources=sources,
                findings=(finding,),
            )
            tm.ok(planned)
            rewritten = {edit.file_path: edit.updated_source for edit in planned.value}
            tm.that(len(rewritten), eq=2)
            tm.that(rewritten[consumer], has=f"facade = {receiver}.FlextSample")
            tm.that(
                rewritten[consumer],
                has=f"    import {module}\n    return {receiver}.FlextSample",
            )
            tm.that(rewritten[consumer], has=unchanged)
            tm.that(rewritten[owner], lacks="sample = FlextSample")
            converged = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.COMPAT_ALIAS,
                rope_workspace=rope,
                sources=rewritten,
                findings=(finding,),
            )
        tm.ok(converged)
        tm.that(converged.value, eq=())

    @staticmethod
    @pytest.mark.parametrize(
        ("consumer_source", "diagnostic"),
        [
            (
                (
                    "if condition:\n    from flext_sample.api import sample\n"
                    "else:\n    from unrelated.api import sample\nfacade = sample\n"
                ),
                "ambiguous qualified alias",
            ),
            (
                (
                    "from flext_sample.api import sample\n"
                    "if condition:\n    sample = value\nfacade = sample\n"
                ),
                "ambiguous qualified alias",
            ),
            (
                "from flext_sample.api import sample as selected\nfacade = selected\n",
                "ambiguous compatibility import alias",
            ),
            (
                "from flext_sample.api import sample as sample\nfacade = sample\n",
                "ambiguous compatibility import alias",
            ),
            ("import flext_sample.api as api\nmodule = api\n", "module escape"),
            ("import flext_sample.api\nmodule = flext_sample.api\n", "module escape"),
            (
                "import flext_sample.api as api\ndef expose():\n    return api\n",
                "module escape",
            ),
            ("import flext_sample.api as api\nconsume(api)\n", "module escape"),
            ("import flext_sample.api as api\nmodules = [api]\n", "module escape"),
            (
                (
                    "import flext_sample.api as api\n"
                    'def opaque(getattr):\n    return getattr(api, "sample")\n'
                ),
                "module escape",
            ),
            (
                (
                    "def ambiguous(condition):\n"
                    "    if condition:\n        import flext_sample.api as sample_api\n"
                    "    else:\n        import unrelated.api as sample_api\n"
                    "    return sample_api.sample\n"
                ),
                "ambiguous qualified alias",
            ),
            (
                (
                    "import flext_sample.api\n"
                    "if condition:\n    flext_sample = value\n"
                    "facade = flext_sample.api.sample\n"
                ),
                "ambiguous qualified alias",
            ),
            (
                (
                    "import flext_sample.api\n"
                    "if condition:\n    import unrelated as flext_sample\n"
                    'facade = getattr(flext_sample.api, "sample")\n'
                ),
                "ambiguous qualified alias",
            ),
            (
                (
                    "import flext_sample.api as api\nimport builtins\n"
                    "def opaque(builtins):\n"
                    '    return builtins.getattr(api, "FlextSample")\n'
                ),
                "module escape",
            ),
        ],
    )
    def test_unproven_consumers_reject_complete_plan(
        tmp_path: Path,
        consumer_source: str,
        diagnostic: str,
    ) -> None:
        """Refuse mixed bindings, import-as bindings and opaque module escapes."""
        owner = tmp_path / "flext-sample/src/flext_sample/api.py"
        consumer = tmp_path / "flext-sample/tests/test_api.py"
        sources = {
            owner: (
                "class FlextSample:\n"
                "    pass\n\n"
                "sample = FlextSample\n"
                '__all__ = ["FlextSample", "sample"]\n'
            ),
            consumer: consumer_source,
        }
        finding = m.Infra.ModOccurrence(
            rule_file="ban-compat-alias.yml",
            rule_id="ban-compat-alias",
            repository="flext-sample",
            file=owner.relative_to(tmp_path),
            range={},
            text="sample = FlextSample",
            actionable=False,
            classification=c.Infra.ModScanFindingClass.DETECTION_ONLY,
        )

        with infra.rope_workspace(tmp_path) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.COMPAT_ALIAS,
                rope_workspace=rope,
                sources=sources,
                findings=(finding,),
            )
        tm.fail(planned, has=diagnostic)

    @staticmethod
    @pytest.mark.parametrize(
        ("module_import", "receiver"),
        [
            ("import flext_sample.api as sample_api", "sample_api"),
            ("import flext_sample as sample_api", "sample_api"),
            ("from flext_sample import api as sample_api", "sample_api"),
            ("import flext_sample.api", "flext_sample.api"),
        ],
    )
    @pytest.mark.parametrize(
        "reflection",
        [
            'getattr(sample_api, "sample")',
            'getattr(sample_api, "sample", None)',
            'getattr(sample_api, "sam" "ple")',
            "getattr(sample_api, attribute)",
            "getattr(sample_api, *attributes)",
            'hasattr(sample_api, "sample")',
            'setattr(sample_api, "sample", None)',
            'delattr(sample_api, "sample")',
            'builtins.getattr(sample_api, "sample")',
            'lookup(sample_api, "sample")',
        ],
    )
    def test_reflective_alias_access_rejects_complete_plan(
        tmp_path: Path,
        module_import: str,
        receiver: str,
        reflection: str,
    ) -> None:
        """Retain the complete owner when a proven reflective consumer is unsafe."""
        owner = tmp_path / "flext-sample/src/flext_sample/api.py"
        consumer = tmp_path / "flext-sample/tests/test_api.py"
        sources = {
            owner: (
                "class FlextSample:\n"
                "    pass\n\n"
                "sample = FlextSample\n"
                '__all__ = ["FlextSample", "sample"]\n'
            ),
            consumer: (
                "import builtins\n"
                "from builtins import getattr as lookup\n"
                f"{module_import}\n\n"
                "def reflective(attribute, attributes):\n"
                f"    return {reflection.replace('sample_api', receiver)}\n"
            ),
        }
        finding = m.Infra.ModOccurrence(
            rule_file="ban-compat-alias.yml",
            rule_id="ban-compat-alias",
            repository="flext-sample",
            file=owner.relative_to(tmp_path),
            range={},
            text="sample = FlextSample",
            actionable=False,
            classification=c.Infra.ModScanFindingClass.DETECTION_ONLY,
        )

        with infra.rope_workspace(tmp_path) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.COMPAT_ALIAS,
                rope_workspace=rope,
                sources=sources,
                findings=(finding,),
            )
        tm.fail(planned, has="reflective")
