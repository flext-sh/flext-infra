"""Runtime proof that bootstrap paths belong to the Makefile checkout."""

from __future__ import annotations

from pathlib import Path

from flext_infra import u as infra_u
from flext_infra.basemk.renderer import FlextInfraBaseMkTemplateRenderer
from flext_tests import tm
from tests import u


class TestsBootstrapForeignCwd:
    """Invoke an absolute Makefile without consulting the caller directory."""

    def test_parent_workspace_markers_do_not_classify_child_checkout(
        self, tmp_path: Path
    ) -> None:
        """Classify a nested checkout only from its own repository markers."""
        workspace = tmp_path / "workspace"
        repository = workspace / "repository"
        infra = workspace / "flext-infra"
        repository.mkdir(parents=True)
        infra.mkdir()
        u.Tests.initialize_git_repo(repository)
        (workspace / ".gitmodules").write_text("", encoding="utf-8")
        (infra / "base.mk").write_text(
            "$(error parent workspace base.mk must not be loaded)\n", encoding="utf-8"
        )
        (repository / "Makefile").write_text(
            "\n".join((
                tm.ok(FlextInfraBaseMkTemplateRenderer.render_bootstrap_include()),
                ".PHONY: topology-proof",
                "topology-proof:",
                '\t@printf "%s|%s\\n" "$(FLEXT_WORKSPACE_ROOT)" "$(SETUP_ROOT)"',
            )),
            encoding="utf-8",
        )

        output = tm.ok(infra_u.Cli.capture(["make", "topology-proof"], cwd=repository))

        tm.that(output.strip(), eq=f"|{repository}")

    def test_absolute_makefile_uses_checkout_base_mk(self, tmp_path: Path) -> None:
        repository = tmp_path / "repository"
        caller = tmp_path / "caller"
        repository.mkdir()
        caller.mkdir()
        u.Tests.initialize_git_repo(repository)
        (repository / "Makefile").write_text(
            tm.ok(FlextInfraBaseMkTemplateRenderer.render_bootstrap_include()),
            encoding="utf-8",
        )
        (repository / "base.mk").write_text(
            '.PHONY: cwd-proof\ncwd-proof:\n\t@printf "%s\\n" "$(SETUP_ROOT)"\n',
            encoding="utf-8",
        )
        foreign = caller / "base.mk"
        foreign.write_text(
            "$(error caller base.mk must not be loaded)\n", encoding="utf-8"
        )
        before = foreign.read_bytes()

        output = tm.ok(
            infra_u.Cli.capture(
                ["make", "-f", str(repository / "Makefile"), "cwd-proof"], cwd=caller
            )
        )

        tm.that(output.strip(), eq=str(repository))
        tm.that(foreign.read_bytes(), eq=before)


__all__: tuple[str, ...] = ()
