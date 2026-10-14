"""Soundness contracts for the rendered Makefile bootstrap recipes.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

import pytest

from tests import c, m, tm, u

_TEMPLATES = Path(__file__).parents[3] / "src" / "flext_infra" / "templates"
_ASSIGNMENT = re.compile(r"(?<![-=!<>])\b([a-z_][a-z0-9_]*)=(?!=)")
_USE = re.compile(r"\$\$([a-z_][a-z0-9_]*)")
_TRAP_BODY = re.compile(r"trap '.*?' EXIT", re.DOTALL)
_FUNCTION_BODY = re.compile(r"\b[a-z_][a-z0-9_]*\(\) \{.*?\n\t?\};", re.DOTALL)


class TestsFlextInfraMakefileBootstrapSoundness:
    """Every emitted bootstrap variable is assigned before it is read."""

    @pytest.mark.parametrize("associated_clone", [False, True])
    def test_help_observes_native_workspace_owner_without_member_environment(
        self,
        tmp_path: Path,
        *,
        associated_clone: bool,
    ) -> None:
        """Make reports UV membership before a member environment exists.

        This proves owner election only. It does not qualify cold bootstrap,
        dependency provisioning or setup/upgrade delegation.
        """
        root, _ = u.Tests.render_make_environment(
            tmp_path / "container",
            c.Infra.MakeProfile.WORKSPACE,
            bootstrap=True,
            shape=u.Tests.MakeEnvironmentShape(project_name="native-owner-root"),
        )
        seed, _ = u.Tests.render_make_environment(
            tmp_path / "member-seed",
            c.Infra.MakeProfile.STANDALONE,
            bootstrap=True,
            shape=u.Tests.MakeEnvironmentShape(project_name="native-owner-member"),
        )
        member = root / "packages" / seed.name
        shutil.copytree(
            seed,
            member,
            symlinks=True,
            ignore=shutil.ignore_patterns(".git", c.Infra.ENVIRONMENT_DIRECTORY),
        )
        if associated_clone:
            u.Tests.initialize_git_repo(
                member,
                origin_url=u.Tests.repository_ref(member.name).url,
            )
        document = u.Tests.toml_doc(
            (root / c.PYPROJECT_FILENAME).read_text(encoding=c.DEFAULT_ENCODING),
        )
        tool = u.Cli.toml_ensure_table(document, "tool")
        uv = u.Cli.toml_ensure_table(tool, "uv")
        uv["workspace"] = {"members": [member.relative_to(root).as_posix()]}
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / c.PYPROJECT_FILENAME,
                u.Cli.toml_dumps(document),
            ),
        )
        binary = tm.ok(u.Infra.managed_mise_binary(c.Infra.UV, root))
        native_options = m.Cli.ProcessOptions(
            remove_env_keys=c.Tests.MAKE_ISOLATION_ENV_KEYS,
        )
        owner = Path(
            tm.ok(
                u.Cli.capture(
                    [str(binary), "workspace", "dir", "--project", str(member)],
                    cwd=member,
                    options=native_options,
                ),
            ).strip(),
        ).resolve()
        tm.that(owner, eq=root.resolve())
        environment = root / c.Infra.ENVIRONMENT_DIRECTORY
        created = tm.ok(
            u.Cli.run_raw(
                [
                    str(binary),
                    "venv",
                    "--python",
                    sys.executable,
                    str(environment),
                ],
                cwd=root,
                options=native_options,
            ),
        )
        tm.that(
            u.Cli.process_succeeded(created.outcome),
            eq=True,
            msg=created.stdout + created.stderr,
        )
        tm.that(environment.is_symlink(), eq=False)
        tm.that((environment / "pyvenv.cfg").is_file(), eq=True)
        member_environment = member / c.Infra.ENVIRONMENT_DIRECTORY
        tm.that(member_environment.exists(), eq=False)
        (member / c.Infra.CUSTOM_MAKE_FILENAME).write_text(
            ".PHONY: post-help\npost-help:\n"
            "\t@printf 'native-runtime-root=%s\\n' '$(RUNTIME_ROOT)'\n"
            "\t@printf 'native-runtime-environment=%s\\n' '$(RUNTIME_VENV)'\n",
            encoding=c.DEFAULT_ENCODING,
        )
        parent_lock = root / c.Infra.MISE_LOCK_FILENAME
        member_lock = member / c.Infra.MISE_LOCK_FILENAME
        locks_before = (parent_lock.read_bytes(), member_lock.read_bytes())
        metadata_before = tuple(
            (project / c.PYPROJECT_FILENAME).read_bytes()
            for project in (root, member)
        )
        process = tm.ok(u.Tests.run_isolated_make(["help"], cwd=member))
        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=True,
            msg=process.stdout + process.stderr,
        )
        tm.that(process.stdout, has=f"native-runtime-root={owner}\n")
        tm.that(
            process.stdout,
            has=f"native-runtime-environment={environment.resolve()}\n",
        )
        tm.that(member_environment.exists(), eq=False)
        tm.that(
            (parent_lock.read_bytes(), member_lock.read_bytes()),
            eq=locks_before,
        )
        tm.that(
            tuple(
                (project / c.PYPROJECT_FILENAME).read_bytes()
                for project in (root, member)
            ),
            eq=metadata_before,
        )

    def test_bootstrap_recipe_initializes_every_variable_it_reads(self) -> None:
        """The tool bootstrap recipe never reads an unassigned shell variable.

        Raises:
            AssertionError: If bootstrap recipe reads shell variables before assigning
                them.
        """
        recipe = (
            _TEMPLATES / "project" / "base" / ("tool_bootstrap_recipe.j2")
        ).read_text(encoding="utf-8")
        # Traps and function bodies read only when invoked, not when declared.
        text = _FUNCTION_BODY.sub(
            "function ... { };", _TRAP_BODY.sub("trap '...' EXIT", recipe)
        )
        bound: set[str] = set()
        violations: list[str] = []
        for line in text.splitlines():
            bound.update(assigned.group(1) for assigned in _ASSIGNMENT.finditer(line))
            violations.extend(
                f"{name} (line: {line.strip()[:80]})"
                for name in _USE.findall(line)
                if name not in bound
            )
        tm.that(violations, eq=[], msg=f"unassigned bootstrap reads: {violations}")
        tm.that(bool(recipe), eq=True)

    @pytest.mark.parametrize("verb", ["setup", "upg"])
    @pytest.mark.parametrize("profile", list(c.Infra.MakeProfile))
    @pytest.mark.parametrize("broken", [False, True])
    def test_borrowed_environment_blocks_bootstrap_before_effects(
        self,
        tmp_path: Path,
        verb: str,
        profile: c.Infra.MakeProfile,
        *,
        broken: bool,
    ) -> None:
        """Public provisioning rejects borrowed runtimes before bootstrap or hooks."""
        project, _ = u.Tests.render_make_environment(tmp_path, profile)
        environment = u.Infra.runtime_environment_dir(project)
        foreign = tmp_path / "foreign"
        if not broken:
            foreign.mkdir()
            (foreign / "owner.txt").write_bytes(b"foreign-owned bytes")
        environment.symlink_to(foreign, target_is_directory=True)
        (project / "custom.mk").write_text(
            "pre-setup pre-upg post-setup post-upg:\n\t@touch hook-effect\n",
            encoding=c.DEFAULT_ENCODING,
        )
        paths = set(project.rglob("*"))
        contents = {path: path.read_bytes() for path in paths if path.is_file()}
        process = tm.ok(u.Tests.run_isolated_make([verb], cwd=project))
        tm.that(process.outcome.raw_return_code, eq=2)
        tm.that(process.stderr, has=f"physical, not a symlink: {environment}")
        tm.that(process.stdout, lacks="github-auth")
        tm.that(set(project.rglob("*")), eq=paths)
        for path, content in contents.items():
            tm.that(path.read_bytes(), eq=content)
        tm.that(environment.is_symlink(), eq=True)
        tm.that(foreign.exists(), eq=not broken)
        if not broken:
            tm.that(tuple(foreign.iterdir()), eq=(foreign / "owner.txt",))
            tm.that((foreign / "owner.txt").read_bytes(), eq=b"foreign-owned bytes")
