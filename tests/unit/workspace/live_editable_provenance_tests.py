"""Real editable imports retain their physical origin while member HEAD advances.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from flext_infra import FlextInfraCli
from flext_infra.workspace import FlextInfraBindingService
from tests import c, m, p, t, tm, u
from tests.unit.codegen.test_make_bootstrap_publication import (
    TestsMakeBootstrapPublication as _BootstrapWorkspace,
)


class TestsLiveEditableProvenance:
    """Local editable provenance authenticates the live checkout independently."""

    @staticmethod
    def _workspace(root: Path) -> tuple[Path, tuple[Path, ...]]:
        workspace, members = _BootstrapWorkspace.workspace(root)
        u.Tests.git_run(workspace, "submodule", "absorbgitdirs")
        manifest = workspace / c.PYPROJECT_FILENAME
        document = u.Tests.toml_doc(manifest.read_text(encoding=c.DEFAULT_ENCODING))
        document["build-system"] = {
            "requires": ["setuptools"],
            "build-backend": "setuptools.build_meta",
        }
        tool = u.Cli.toml_ensure_table(document, "tool")
        setuptools = u.Cli.toml_ensure_table(tool, "setuptools")
        packages = u.Cli.toml_ensure_table(setuptools, "packages")
        find = u.Cli.toml_ensure_table(packages, "find")
        find["where"] = ["src"]
        uv_workspace = u.Cli.toml_ensure_table(
            u.Cli.toml_ensure_table(tool, "uv"), "workspace"
        )
        uv_workspace["members"] = [
            member.relative_to(workspace).as_posix() for member in members
        ]
        tm.ok(u.Cli.atomic_write_text_file(manifest, u.Cli.toml_dumps(document)))
        u.Tests.git_run(workspace, "add", c.PYPROJECT_FILENAME)
        u.Tests.git_run(
            workspace,
            "commit",
            "-qm",
            "declare real editable workspace build",
        )
        uv = u.Tests.managed_uv()
        tm.ok(
            u.Cli.run_checked(
                (uv, "sync", "--all-packages"),
                cwd=workspace,
                options=m.Cli.ProcessOptions(
                    remove_env_keys=c.Tests.MAKE_ISOLATION_ENV_KEYS,
                ),
            ),
        )
        return workspace, members

    @staticmethod
    def _verify(root: Path) -> p.Cli.CommandOutput:
        outcome = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-m",
                    "flext_infra",
                    c.Infra.CLI_GROUP_WORKSPACE,
                    "verify-environment",
                    "--repository-root",
                    str(root),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env={c.Infra.ENV_VAR_GITHUB_ACTIONS: ""},
                    remove_env_keys=c.Tests.MAKE_ISOLATION_ENV_KEYS,
                ),
            ),
        )
        u.Cli.emit_raw(outcome.stdout)
        u.Cli.emit_raw(outcome.stderr)
        return outcome

    @staticmethod
    def _import(root: Path, member: Path, expected: str) -> None:
        package = f"{u.Infra.project_package_name(member)}.live_probe"
        observation = tm.ok(
            u.Cli.run_raw(
                (
                    str(u.Infra.runtime_python(root)),
                    "-I",
                    "-c",
                    (
                        "import importlib,pathlib,sys; "
                        "module=importlib.import_module(sys.argv[1]); "
                        "print(module.LIVE_VALUE); "
                        "print(pathlib.Path(module.__file__).resolve())"
                    ),
                    package,
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(
                    remove_env_keys=c.Tests.MAKE_ISOLATION_ENV_KEYS,
                ),
            ),
        )
        tm.that(
            u.Cli.process_succeeded(observation.outcome),
            eq=True,
            msg=observation.stdout + observation.stderr,
        )
        lines = observation.stdout.splitlines()
        tm.that(lines[0], eq=expected)
        tm.ok(Path(lines[1]).is_relative_to(member.resolve()))

    def test_live_member_commit_does_not_invalidate_correct_editable_origin(
        self,
        tmp_path: Path,
    ) -> None:
        """The installed editable imports new committed code.

        The import succeeds before the superproject promotes the member gitlink.
        """
        root, members = self._workspace(tmp_path)
        member = members[0]
        package = u.Infra.project_package_name(member)
        module = member / "src" / package / "live_probe.py"
        before = self._verify(root)
        tm.that(u.Cli.process_succeeded(before.outcome), eq=True, msg=before.stderr)
        gitlink_before = u.Tests.git_capture(
            root,
            "rev-parse",
            f"{c.Infra.GIT_HEAD}:{member.relative_to(root).as_posix()}",
        ).strip()
        index_before = u.Tests.git_capture(
            root,
            "ls-files",
            "--stage",
            "--",
            member.relative_to(root).as_posix(),
        )
        value = "live-member-next-commit"
        module.write_text(f"LIVE_VALUE = {value!r}\n", encoding=c.DEFAULT_ENCODING)
        u.Tests.commit_git_changes(member, "advance live editable code")
        member_head = u.Tests.git_capture(member, "rev-parse", c.Infra.GIT_HEAD).strip()
        tm.fail(member_head == gitlink_before)
        self._import(root, member, value)
        tm.that(
            u.Tests.git_capture(
                root,
                "rev-parse",
                f"{c.Infra.GIT_HEAD}:{member.relative_to(root).as_posix()}",
            ).strip(),
            eq=gitlink_before,
        )
        tm.that(
            u.Tests.git_capture(
                root,
                "ls-files",
                "--stage",
                "--",
                member.relative_to(root).as_posix(),
            ),
            eq=index_before,
        )
        after = self._verify(root)
        tm.that(
            u.Cli.process_succeeded(after.outcome),
            eq=True,
            msg=after.stdout + after.stderr,
        )

    @staticmethod
    def _select(root: Path) -> int:
        """Run the public editable selection against the real workspace.

        Returns:
            The unchanged exit code from the public selection command.

        """
        return FlextInfraCli.infra_main([
            "workspace",
            c.Infra.FLEXT_EDITABLE_ROUTE_NAME,
            "--repository-root",
            str(root),
            "--flext-root",
            str(root),
        ])

    def test_strict_selection_refreshes_membership_without_preuninstall(
        self,
        tmp_path: Path,
    ) -> None:
        """Native selection rebuilds links and retains the prior install on failure."""
        root, members = self._workspace(tmp_path)
        member = members[0]
        package = u.Infra.project_package_name(member)
        tm.that(self._select(root), eq=0)
        module = member / "src" / package / "live_probe.py"
        value = "strict-membership-source"
        module.write_text(f"LIVE_VALUE = {value!r}\n", encoding=c.DEFAULT_ENCODING)
        excluded = member / "excluded_source"
        excluded.mkdir()
        (excluded / "__init__.py").write_text("", encoding=c.DEFAULT_ENCODING)
        tm.that(self._select(root), eq=0)
        self._import(root, member, value)
        receipt = root / c.Infra.FLEXT_EDITABLE_SELECTION_RELATIVE_PATH
        admitted = receipt.read_bytes()
        setup = member / "setup.py"
        tm.that(setup.exists(), eq=False)
        setup.write_text(
            "raise RuntimeError('native editable build refused')\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(self._select(root), ne=0)
        tm.that(receipt.read_bytes(), eq=admitted)
        self._import(root, member, value)
        setup.unlink()
        module.unlink()
        tm.that(self._select(root), eq=0)
        observation = tm.ok(
            u.Cli.run_raw(
                (
                    str(u.Infra.runtime_python(root)),
                    "-I",
                    "-c",
                    (
                        "import importlib.util,sys; "
                        "assert importlib.util.find_spec(sys.argv[1]) is None; "
                        "assert importlib.util.find_spec('excluded_source') is None; "
                        "assert importlib.util.find_spec('setuptools') is None"
                    ),
                    f"{package}.live_probe",
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(
                    remove_env_keys=c.Tests.MAKE_ISOLATION_ENV_KEYS,
                ),
            )
        )
        tm.that(
            u.Cli.process_succeeded(observation.outcome),
            eq=True,
            msg=observation.stdout + observation.stderr,
        )

    def test_selected_distribution_missing_dependency_blocks_receipt_publication(
        self,
        tmp_path: Path,
        capfd: t.Tests.CaptureFixture[str],
    ) -> None:
        """A receipt-bound requirement owner cannot excuse a missing dependency."""
        root, members = self._workspace(tmp_path)
        tm.that(self._select(root), eq=0)
        receipt = root / c.Infra.FLEXT_EDITABLE_SELECTION_RELATIVE_PATH
        admitted = receipt.read_bytes()
        manifest = members[0] / c.PYPROJECT_FILENAME
        document = u.Tests.toml_doc(manifest.read_text(encoding=c.DEFAULT_ENCODING))
        project = u.Cli.toml_ensure_table(document, "project")
        missing = f"{members[0].name}-missing-dependency"
        project[c.Infra.DEPENDENCIES] = [missing]
        tm.ok(u.Cli.atomic_write_text_file(manifest, u.Cli.toml_dumps(document)))
        tm.that(self._select(root), ne=0)
        capture = capfd.readouterr()
        tm.that(
            capture.out + capture.err,
            has=f"requires `{missing}`, but it's not installed",
        )
        tm.that(receipt.read_bytes(), eq=admitted)

    def test_selection_rejects_duplicate_native_metadata_without_rebinding(
        self,
        tmp_path: Path,
    ) -> None:
        """Two real installed metadata records never authorize source replacement."""
        root, members = self._workspace(tmp_path)
        tm.that(self._select(root), eq=0)
        observed = tm.ok(
            FlextInfraBindingService.consumer_package_environment(
                consumer_root=root,
                python=u.Infra.runtime_python(root),
                packages=(),
            )
        )
        paths = tuple(str(path) for path in observed.metadata_paths)
        installed = u.installed_distributions(name=members[0].name, path=paths)
        tm.that(len(installed), eq=1)
        metadata = next(
            Path(str(installed[0].locate_file(file)))
            for file in tm.not_none(installed[0].files)
            if file.name == "METADATA"
        )
        duplicate = metadata.parent.with_name(
            metadata.parent.name.removesuffix(c.Infra.DIST_INFO_SUFFIX)
            + "-duplicate"
            + c.Infra.DIST_INFO_SUFFIX
        )
        states = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in (
                metadata,
                root / c.Infra.FLEXT_EDITABLE_SELECTION_RELATIVE_PATH,
            )
        )
        u.Tests.reflink_copy_tree(metadata.parent, duplicate)
        try:
            tm.that(
                len(u.installed_distributions(name=members[0].name, path=paths)),
                eq=2,
            )
            tm.that(self._select(root), ne=0)
            tm.ok(u.Cli.atomic_verify_binary_file_states(states))
        finally:
            shutil.rmtree(duplicate)

    @c.Tests.MARK.parametrize("defect", ["origin", "backpointer", "foreign_editable"])
    def test_live_editable_origin_still_rejects_foreign_identity(
        self,
        tmp_path: Path,
        defect: str,
    ) -> None:
        """A valid baseline cannot authorize a foreign URL, Git store or install."""
        root, members = self._workspace(tmp_path)
        member = members[0]
        baseline = self._verify(root)
        tm.that(u.Cli.process_succeeded(baseline.outcome), eq=True, msg=baseline.stderr)
        if defect == "origin":
            u.Tests.git_run(
                member,
                "remote",
                "set-url",
                c.Infra.GIT_ORIGIN,
                u.Tests.repository_ref("foreign-origin").url,
            )
        elif defect == "backpointer":
            marker = member / c.Infra.GIT_DIR
            tm.ok(marker.is_file())
            marker.write_text(
                f"gitdir: {tmp_path / 'missing-git-metadata'}\n",
                encoding=c.DEFAULT_ENCODING,
            )
        else:
            foreign = tmp_path / "foreign-member"
            tm.ok(
                u.Cli.run_checked(
                    (c.Infra.GIT, "clone", str(member), str(foreign)),
                    cwd=root,
                ),
            )
            uv = u.Tests.managed_uv()
            tm.ok(
                u.Cli.run_checked(
                    (
                        uv,
                        "pip",
                        "install",
                        "--no-deps",
                        "--reinstall",
                        "--python",
                        str(u.Infra.runtime_python(root)),
                        "--editable",
                        str(foreign),
                    ),
                    cwd=root,
                ),
            )
        result = self._verify(root)
        tm.ok(result.outcome.raw_return_code != 0)
        tm.ok(bool(result.stderr.strip() or result.stdout.strip()))
