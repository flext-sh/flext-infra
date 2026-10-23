"""Module rename publication and its consumer rewire are one atomic effect.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import codemod
from tests import c, tm, u


class TestsFlextInfraSemanticRenameAtomicity:
    """A rename never publishes without the consumer rewire planned with it."""

    @staticmethod
    def test_rewire_failure_publishes_no_module_rename(tmp_path: Path) -> None:
        """A stale rewire target aborts the whole candidate before any effect.

        The naming wave plans the module move and the cross-root consumer
        rewire as one candidate. A concurrent writer changing the consumer after
        planning is the failure injected between rename and rewire: publication
        must reject the candidate and leave the original module, the consumer
        reference and the absent destination exactly as they were, so the tree
        still imports through its original path.
        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        receiver, receiver_package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="atomic-receiver",
            package_name="atomic_receiver",
        )
        for checkout in (root, receiver):
            u.Tests.provision_checkout(checkout)
            u.Tests.provision_runtime_environment(checkout)
        facade = package / "_facade"
        facade.mkdir()
        (facade / "__init__.py").write_text("", encoding=c.DEFAULT_ENCODING)
        source = facade / "_module.py"
        source.write_text("VALUE = 1\n", encoding=c.DEFAULT_ENCODING)
        consumer = receiver_package / "consumer.py"
        original = f"from {package.name}._facade._module import VALUE\n"
        consumer.write_text(original, encoding=c.DEFAULT_ENCODING)
        seed = tm.ok(
            codemod.FlextInfraCodemodSemanticApply.build_source_plan(root, (receiver,))
        )
        planned = tm.ok(
            codemod.FlextInfraCodemodSemanticApply.plan_module_names(root, seed)
        )
        tm.that(planned.candidate.updates[source], eq=None)
        tm.ok(consumer in planned.candidate.updates)
        injected = original + "# concurrent writer\n"
        consumer.write_text(injected, encoding=c.DEFAULT_ENCODING)

        published = codemod.FlextInfraCodemodSemanticApply.publish_candidate(
            root, planned, publish=True
        )

        tm.fail(published)
        tm.that(str(published.error), contains=f"atomic source changed: {consumer}")
        tm.ok(source.is_file())
        tm.that(source.read_text(encoding=c.DEFAULT_ENCODING), eq="VALUE = 1\n")
        tm.ok(not (facade / "module.py").exists())
        tm.that(consumer.read_text(encoding=c.DEFAULT_ENCODING), eq=injected)
