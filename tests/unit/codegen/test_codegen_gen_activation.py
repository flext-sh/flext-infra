"""Real Make generation repairs activation before consuming its own output."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import config
from tests import c, u

# These cases provision their own environment from the candidate's committed
# locks. Make test-full owns the native installer and complete conform boundary.
pytestmark = [pytest.mark.slow, pytest.mark.remote]


class TestsFlextInfraCodegenGenActivation:
    """Exercise the generated dispatcher with its real producer and activation."""

    @staticmethod
    def _project_inputs(tmp_path: Path) -> Path:
        """Copy Git-visible source inputs, never a runtime or another Git store."""
        source = Path(__file__).resolve().parents[3]
        root = tmp_path / config.Infra.name
        paths = tm.not_none(u.Infra.git_tracked_scope_paths(source))
        tm.that(bool(paths), eq=True)
        for path in paths:
            destination = root / path.relative_to(source)
            destination.parent.mkdir(parents=True, exist_ok=True)
            _ = shutil.copy2(path, destination, follow_symlinks=False)
        tm.that((root / ".venv").exists(), eq=False)
        tm.that((root / ".git").exists(), eq=False)
        u.Tests.initialize_git_repo(
            root, origin_url=u.Tests.repository_ref(config.Infra.name).url
        )
        return root

    @pytest.mark.parametrize(
        "scenario",
        [
            "builtin",
            "custom",
            "producer-failure",
            "activation-failure",
            "missing-environment",
        ],
    )
    def test_gen_recovers_activation_and_orders_hooks(
        self, tmp_path: Path, scenario: str
    ) -> None:
        """Native failures stop post hooks; a valid producer activates only once."""
        root = self._project_inputs(tmp_path)
        if scenario != "missing-environment":
            setup = tm.ok(
                u.Tests.run_isolated_make(["--no-print-directory", "setup"], cwd=root)
            )
            tm.that(
                u.Cli.process_succeeded(setup.outcome),
                eq=True,
                msg=setup.stdout + setup.stderr,
            )
            tm.that((root / ".venv" / "pyvenv.cfg").is_file(), eq=True)

        receipt = root / "gen-lifecycle.log"
        envrc = root / c.Infra.ENVRC_FILENAME
        broken_activation = envrc.read_text(encoding="utf-8") + "\nreturn 73\n"
        envrc.write_text(broken_activation, encoding="utf-8")
        (root / c.Infra.ENVRC_LOCAL_RELPATH).write_text(
            "printf 'activated\\n' >> gen-lifecycle.log\n"
            'export MAKE_GEN_ACTIVATION_PROOF="$PROJECT_ROOT"\n'
            + ("return 43\n" if scenario == "activation-failure" else ""),
            encoding="utf-8",
        )
        (root / c.Infra.CUSTOM_MAKE_FILENAME).write_text(
            ".PHONY: pre-gen post-gen\n"
            "pre-gen:\n"
            '\t@test -x "$(RUNTIME_PYTHON)"\n'
            '\t@test -z "$$MAKE_GEN_ACTIVATION_PROOF"\n'
            "\t@printf 'pre\\n' >> gen-lifecycle.log\n"
            "post-gen:\n"
            '\t@test "$$MAKE_GEN_ACTIVATION_PROOF" = "$(PROJECT_ROOT)"\n'
            "\t@printf 'post\\n' >> gen-lifecycle.log\n"
            + (
                ".PHONY: _custom-gen\n"
                "_custom-gen:\n"
                "\t@printf 'custom\\n' >> gen-lifecycle.log\n"
                "\t+@$(SELF_MAKE) _builtin-gen\n"
                if scenario == "custom"
                else ""
            ),
            encoding="utf-8",
        )
        if scenario == "producer-failure":
            # Corrupt the real producer's package input. Python must preserve
            # its native SyntaxError before conform or activation can complete.
            initializer = (
                root
                / c.Infra.DEFAULT_SRC_DIR
                / config.Infra.name.replace("-", "_")
                / "__init__.py"
            )
            with initializer.open("a", encoding="utf-8") as stream:
                _ = stream.write("\ndef (\n")

        bootstrap = u.Infra.mise_bootstrap_environment()
        sidecars = root / ".mise" / "locks"
        locks = (
            root / c.Infra.UV_LOCK_FILENAME,
            root / bootstrap.version_pin_file,
            root / bootstrap.lock_file,
            *(path for path in sidecars.rglob("*") if path.is_file()),
        )
        before = {path: path.read_bytes() for path in locks}
        process = tm.ok(
            u.Tests.run_isolated_make(
                ["--no-print-directory", "gen"],
                cwd=root,
                env={"MAKE_GEN_ACTIVATION_PROOF": ""},
            )
        )

        tm.that({path: path.read_bytes() for path in locks}, eq=before)
        tm.that(
            {path for path in sidecars.rglob("*") if path.is_file()},
            eq={path for path in locks if path.is_relative_to(sidecars)},
        )
        succeeded = scenario in {"builtin", "custom"}
        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=succeeded,
            msg=process.stdout + process.stderr,
        )
        if scenario == "missing-environment":
            tm.that(process.stderr, has="missing environment interpreter")
            tm.that(receipt.exists(), eq=False)
            tm.that((root / ".venv").exists(), eq=False)
            tm.that(envrc.read_text(encoding="utf-8"), eq=broken_activation)
            return
        if scenario == "producer-failure":
            tm.that(receipt.read_text().splitlines(), eq=["pre"])
            tm.that(process.stderr, has="SyntaxError")
            tm.that(envrc.read_text(encoding="utf-8"), eq=broken_activation)
            return
        tm.that(envrc.read_text(encoding="utf-8") == broken_activation, eq=False)
        expected = ["pre"]
        if scenario == "custom":
            expected.append("custom")
        expected.append("activated")
        if succeeded:
            expected.append("post")
            tm.that(process.stderr, lacks="mise WARN")
        else:
            tm.that(process.stderr, has="exit status 43")
        tm.that(receipt.read_text().splitlines(), eq=expected)
