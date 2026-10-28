"""Observe inherited dispatch after the public own-method source transformation.

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

from pathlib import Path

import pytest

from tests import c, tm, u


class TestsFlextInfraOwnMethodMro:
    """Preserve lexical identity while making subclass behavior observable."""

    @staticmethod
    def test_subclass_override_and_shadowed_binding_are_preserved(
        tmp_path: Path,
    ) -> None:
        """Dispatch inherited helpers through the receiver and preserve local names."""
        source = (
            "class Owner:\n"
            "    @staticmethod\n"
            "    def helper(): return 'base'\n"
            "    @staticmethod\n"
            "    def deliver(): return Owner.helper()\n"
            "    @staticmethod\n"
            "    def shadow(Owner): return Owner.helper()\n"
            "class Derived(Owner):\n"
            "    @staticmethod\n"
            "    def helper(): return 'derived'\n"
            "class Local:\n"
            "    @staticmethod\n"
            "    def helper(): return 'local'\n"
        )
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        module = package / "mro_consumer.py"
        module.write_text(source, encoding=c.DEFAULT_ENCODING)
        with u.Infra.facade_source_project(root) as (project, _sources):
            rewritten, changes = u.Infra.rewrite_own_method_mro_calls(
                source, source_project=project, file_path=module
            )
            with u.Infra.facade_source_project(
                root,
                planned_sources={module: rewritten},
                source_project=project,
            ) as (candidate, _candidate_sources):
                second, further_changes = u.Infra.rewrite_own_method_mro_calls(
                    rewritten, source_project=candidate, file_path=module
                )
        tm.that(changes, eq=("own-method-mro:Owner.deliver",))
        module.write_text(rewritten, encoding=c.DEFAULT_ENCODING)
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"from {package.name}.mro_consumer import Derived, Local\n"
                "print(Derived.deliver())\n"
                "print(Derived.shadow(Local))\n",
                python_paths=(str(package.parent),),
            ),
            eq=["derived", "local"],
        )
        tm.that(further_changes, eq=())
        tm.that(second.encode(c.DEFAULT_ENCODING), eq=module.read_bytes())

    @staticmethod
    def test_native_dispatch_preserves_signature_annotations_and_nested_receiver(
        tmp_path: Path,
    ) -> None:
        """Native rewrites retain argument kinds, hints and nested class dispatch."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        module = package / "annotated_consumer.py"
        source = (
            "from __future__ import annotations\n"
            "class Owner:\n"
            "    @staticmethod\n"
            "    def helper(value: int) -> str: return f'base:{value}'\n"
            "    @staticmethod\n"
            "    def deliver(value: int, /, *, suffix: str = '!') -> str:\n"
            "        return Owner.helper(value) + suffix\n"
            "    @classmethod\n"
            "    def relay(receiver, value: int) -> str:\n"
            "        return Owner.helper(value)\n"
            "    class Nested:\n"
            "        @classmethod\n"
            "        def helper(klass) -> str: return klass.__name__\n"
            "        @classmethod\n"
            "        def deliver(klass) -> str: return klass.helper()\n"
            "class Derived(Owner):\n"
            "    @staticmethod\n"
            "    def helper(value: int) -> str: return f'derived:{value}'\n"
        )
        module.write_text(source, encoding=c.DEFAULT_ENCODING)
        with u.Infra.facade_source_project(root) as (project, _sources):
            rewritten, _changes = u.Infra.rewrite_own_method_mro_calls(
                source, source_project=project, file_path=module
            )
        module.write_text(rewritten, encoding=c.DEFAULT_ENCODING)
        tm.that(
            u.Tests.run_lazy_init_probe(
                "import inspect\n"
                "from typing import get_type_hints\n"
                f"from {package.name}.annotated_consumer import Derived\n"
                "print(Derived.deliver(7))\n"
                "print(Derived.relay(7))\n"
                "print(Derived.Nested.deliver())\n"
                "parameters = inspect.signature(Derived.deliver).parameters\n"
                "print(parameters['value'].kind "
                "is inspect.Parameter.POSITIONAL_ONLY)\n"
                "print(parameters['suffix'].kind "
                "is inspect.Parameter.KEYWORD_ONLY)\n"
                "print(get_type_hints(Derived.deliver)['value'] is int)\n"
                "print(get_type_hints(Derived.deliver)['return'] is str)\n",
                python_paths=(str(package.parent),),
            ),
            eq=["derived:7!", "derived:7", "Nested", "True", "True", "True", "True"],
        )

    @staticmethod
    @pytest.mark.parametrize(
        ("source", "reason"),
        [
            (
                (
                    "class Owner:\n"
                    "    def helper(self): return 'instance'\n"
                    "    @staticmethod\n"
                    "    def deliver(): return Owner.helper\n"
                ),
                "unbound reference",
            ),
            (
                (
                    "class Owner:\n"
                    "    @staticmethod\n"
                    "    def helper(): return 'static'\n"
                    "    @staticmethod\n"
                    "    def deliver(cls): return Owner.helper()\n"
                ),
                "capture a parameter",
            ),
        ],
    )
    def test_invalid_receiver_semantics_fail_before_edit(
        tmp_path: Path, source: str, reason: str
    ) -> None:
        """Reject transformations that would change call signatures or capture names."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        module = package / "invalid_consumer.py"
        module.write_text(source, encoding=c.DEFAULT_ENCODING)
        with (
            u.Infra.facade_source_project(root) as (project, _sources),
            pytest.raises(ValueError, match=reason),
        ):
            u.Infra.rewrite_own_method_mro_calls(
                source, source_project=project, file_path=module
            )
        tm.that(module.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
