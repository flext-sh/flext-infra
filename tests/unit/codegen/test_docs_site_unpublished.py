"""Verify docs.yml publishes the site to Pages only for publishing distributions.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, tm, u


class TestsFlextInfraDocsSiteUnpublished:
    """A private distribution builds its docs site and never deploys it."""

    template = (
        Path(__file__).resolve().parents[3]
        / "src/flext_infra/templates/project/base/.github/workflows/docs.yml.j2"
    )

    @classmethod
    def _rendered(cls, *, docs_site_publish: bool) -> str:
        spec = u.CodegenTestSupport.Ci.workflow_spec(
            dist="fixture-docs-site",
            make_profile=c.Infra.MakeProfile.STANDALONE,
            repository_branch="develop",
            ci_trigger_branches=("develop", "main"),
            overrides=u.CodegenTestSupport.Ci.WorkflowRenderOverrides(
                docs_site_publish=docs_site_publish,
            ),
        )
        return tm.ok(u.Cli.template_render(cls.template, spec))

    @staticmethod
    def _jobs(rendered: str) -> tuple[str, ...]:
        adapter = u.Cli.JSON_MAPPING_ADAPTER
        document = adapter.validate_python(tm.ok(u.Cli.yaml_parse(rendered)))
        return tuple(adapter.validate_python(document["jobs"]))

    def test_publishing_distribution_deploys_site_to_pages(self) -> None:
        """The default distribution uploads the site and deploys it from main."""
        rendered = self._rendered(docs_site_publish=True)

        tm.that(self._jobs(rendered), eq=("docs-quality", "deploy"))
        for action in ("upload-pages-artifact", "configure-pages", "deploy-pages"):
            tm.that(rendered, has=action)
        tm.that(rendered, has="pages: write")

    def test_unpublished_distribution_never_touches_pages(self) -> None:
        """An unpublished distribution keeps only the build-and-check proof."""
        rendered = self._rendered(docs_site_publish=False)

        tm.that(self._jobs(rendered), eq=("docs-quality",))
        for marker in (
            "upload-pages-artifact",
            "configure-pages",
            "deploy-pages",
            "pages: write",
            "id-token: write",
        ):
            tm.that(rendered, lacks=marker)
