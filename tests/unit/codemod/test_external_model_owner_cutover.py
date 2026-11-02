"""Focused native cutover evidence for external model-holder ownership.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import infra
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraExternalModelOwnerCutover:
    """Only eligible external holders receive a path-derived native rename."""

    @staticmethod
    def test_external_model_holder_renames_consumers_and_lazy_export(
        tmp_path: Path,
    ) -> None:
        """Rope rewires imports and the lazy export while preserving a fixed point."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="ai-hub", package_name="ai_hub"
        )
        protocols = package / "protocols"
        tm.ok(u.Cli.ensure_dir(protocols))
        module = protocols / "model_pipeline.py"
        consumer = package / "consumer.py"
        initializer = protocols / c.Infra.INIT_PY
        sources = {
            module: "class AiHubModelPipeline:\n    pass\n",
            consumer: (
                "from ai_hub.protocols.model_pipeline import AiHubModelPipeline\n"
                "value = AiHubModelPipeline()\n"
            ),
            initializer: (
                "from types import MappingProxyType\n"
                "from flext_core.lazy import install_lazy_exports\n"
                "install_lazy_exports(\n"
                "    __name__, globals(),\n"
                "    MappingProxyType({'AiHubModelPipeline': '.model_pipeline'}),\n"
                "    public_exports=('AiHubModelPipeline',),\n"
                ")\n"
            ),
        }
        invalid = {
            package / "_models" / "model_pipeline.py": (
                "class AiHubModelPipeline:\n    pass\n"
            ),
            package / "models.py": "class AiHubModelPipeline:\n    pass\n",
            package / "collision.py": (
                "class AiHubModelCollision:\n    pass\n"
                "class AiHubCollision:\n    pass\n"
            ),
        }
        for path, source in {**sources, **invalid}.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))

        phase = c.Infra.SemanticCutoverPhase.EXTERNAL_MODEL_OWNER
        with infra.rope_workspace(root) as rope:
            planned = tm.ok(
                u.Infra.plan_semantic_cutover(
                    phase, rope_workspace=rope, sources={**sources, **invalid}
                )
            )
            updated = {
                **sources,
                **invalid,
                **{edit.file_path: edit.updated_source for edit in planned},
            }
            fixed = tm.ok(
                u.Infra.plan_semantic_cutover(
                    phase, rope_workspace=rope, sources=updated
                )
            )

        tm.that(
            {edit.file_path for edit in planned}, eq={module, consumer, initializer}
        )
        tm.that(updated[module], has="class AiHubProtocolsModelPipeline:")
        tm.that(updated[consumer], has="AiHubProtocolsModelPipeline")
        tm.that(updated[initializer], has="AiHubProtocolsModelPipeline")
        for path, source in invalid.items():
            tm.that(updated[path], eq=source)
        tm.that(fixed, empty=True)
