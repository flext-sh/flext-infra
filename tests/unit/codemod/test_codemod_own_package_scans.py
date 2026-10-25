"""Own-package scans span the project's internal tiers and declared roles.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra.codemod import FlextInfraModGateEngine
from tests import c, t, tm, u


class TestsFlextInfraCodemodOwnPackageScans:
    """An import between a project's own namespaces never crosses an owner."""

    class TestDeclaredNamespace:
        """Declared packages and source roles keep strict scan boundaries."""

        @staticmethod
        @pytest.mark.parametrize("namespace", ["infra", "deployment_support"])
        @pytest.mark.parametrize(
            ("consumer", "target", "expected"),
            [
                ("contracts/models.py", "contracts._models.entity", (True, True)),
                ("contracts/_models/part.py", "contracts._models.entity", (True, True)),
                (
                    "contracts/_typings/part.py",
                    "contracts._models.entity",
                    (True, False),
                ),
                ("other/models.py", "contracts._models.entity", (True, False)),
                (
                    "contracts/models.py",
                    "foreign.contracts._models.entity",
                    (False, False),
                ),
            ],
        )
        def test_declared_namespace_preserves_private_family_boundaries(
            tmp_path: Path,
            namespace: str,
            consumer: str,
            target: str,
            expected: tuple[bool, bool],
        ) -> None:
            """Independent implicit packages allow assembly, not foreign families."""
            own, member = expected
            root = u.Tests.mk_project(
                tmp_path,
                c.ContextScope.APPLICATION,
                with_src=True,
                pyproject=(
                    f'[project]\nname = "{c.ContextScope.APPLICATION}"\n'
                    'version = "1.0.0"\n'
                ),
            )
            declaration = u.Tests.project_spec(c.ContextScope.APPLICATION).model_copy(
                update={"repository_namespace_packages": (namespace,)}
            )
            tm.ok(
                u.Cli.yaml_dump(
                    root / "config" / "codegen.yaml",
                    {
                        "Infra": {
                            "codegen": {
                                "repository": {
                                    "project": declaration.model_dump(mode="json"),
                                }
                            }
                        }
                    },
                )
            )
            source = root / namespace / consumer
            source.parent.mkdir(parents=True, exist_ok=True)
            imported = (
                target if target.startswith("foreign.") else f"{namespace}.{target}"
            )
            content = f"from {imported} import Entity\n"
            source.write_text(content, encoding="utf-8")
            stem = "".join(part.title() for part in namespace.split("_"))
            tm.that(u.Infra.project_prefix(source), eq=stem)
            tm.that(
                u.Infra.import_namespace(root, source),
                eq=(root / namespace, f"{namespace}.{consumer[:-3].replace('/', '.')}"),
            )
            report = tm.ok(
                FlextInfraModGateEngine.scan(
                    root,
                    fix=False,
                    selection=("ban-private-import", "ban-own-family-internal-import"),
                    source_files=(source,),
                )
            )
            separator = c.Infra.CODEMOD_GENERATED_ID_SEPARATOR
            tm.that(
                {row.rule_id.partition(separator)[0] for row in report.entries},
                eq=(
                    {"ban-private-import"}
                    if not own
                    else {"ban-own-family-internal-import"}
                    if not member
                    else set()
                ),
            )
            tm.that(source.read_text(encoding="utf-8"), eq=content)

        @staticmethod
        @pytest.mark.parametrize("with_utilities", [False, True])
        @pytest.mark.parametrize("constructor", ["native", "m", "t"])
        def test_adapter_construction_excludes_only_native_layer_zero_calls(
            mod_workspace: Path, *, with_utilities: bool, constructor: str
        ) -> None:
            """Keep consumers, ancestor roles and facade aliases visible."""
            namespace = u.Infra.project_package_name(mod_workspace)
            package = mod_workspace / c.Infra.DEFAULT_SRC_DIR / namespace
            imports = "from pydantic import TypeAdapter\n"
            if constructor != "native":
                imports += f"from flext_core import {constructor}\n"
            if with_utilities:
                imports += "from flext_core import u\n"
            receiver = "" if constructor == "native" else f"{constructor}."
            source = f"{imports}\nADAPTER = {receiver}TypeAdapter(int)\n"
            paths = tuple(
                package / relative
                for relative in (
                    "_settings.py",
                    "_config.py",
                    "consumer.py",
                    "_models/_settings.py",
                    "_utilities/_config.py",
                )
            )
            # The native graph authenticates the real package initializer.
            original = {
                path: (
                    f"import {namespace}\nimport {namespace}._models\n"
                    f"import {namespace}._utilities\n\n{source}"
                    if path.name == "consumer.py"
                    else source
                )
                for path in paths
            }
            for path, content in original.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.parent != package:
                    (path.parent / c.Infra.INIT_PY).write_text(
                        "", encoding=c.DEFAULT_ENCODING
                    )
                path.write_text(content, encoding=c.DEFAULT_ENCODING)
            rule_ids = (
                "rewire-type-adapter-construction",
                "rewire-type-adapter-construction-missing-u-import",
            )
            selected = tuple(
                dict.fromkeys((
                    *(path.parent / c.Infra.INIT_PY for path in paths),
                    *paths,
                ))
            )
            report = tm.ok(
                FlextInfraModGateEngine.scan(
                    mod_workspace,
                    fix=False,
                    selection=rule_ids,
                    source_files=selected,
                )
            )
            expected = set(paths if constructor != "native" else paths[2:])
            expected_id = rule_ids[0] if with_utilities else rule_ids[1]
            tm.that(
                {
                    (u.Infra.codemod_source_path(mod_workspace, row.file), row.rule_id)
                    for row in report.entries
                },
                eq={(path.resolve(), expected_id) for path in expected},
            )
            tm.that(report.findings, eq=len(expected))
            for path in paths:
                tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=original[path])

    class TestSourceRoles:
        """Native declarations distinguish configuration from consumer helpers."""

        @staticmethod
        @pytest.mark.parametrize(
            "filename",
            [
                "configuration.py",
                "runtime_settings.py",
                "consumer.py",
                "helpers/settings.py",
                "helpers/config.py",
                "pulumi/lib/settings.py",
            ],
        )
        @pytest.mark.parametrize("declares", [False, True])
        @pytest.mark.parametrize(
            ("provider", "base"),
            [("flext_core", "FlextConfig"), ("flext_ldap", "FlextLdapSettings")],
        )
        def test_source_layer_zero_requires_native_configuration_ancestry(
            mod_workspace: Path,
            filename: str,
            provider: str,
            base: str,
            *,
            declares: bool,
        ) -> None:
            """Importing a settings base alone never grants its consumer Layer0."""
            namespace = u.Infra.project_package_name(mod_workspace)
            source = mod_workspace / "src" / namespace / filename
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text(
                f"from {provider} import {base}, m, t\n"
                + (
                    f"class LocalSettings({base}):\n    pass\n"
                    if declares
                    else "class Consumer:\n    pass\n"
                ),
                encoding="utf-8",
            )
            with (
                u.Infra.open_project(mod_workspace) as project,
                u.Infra.semantic_matching_context(),
            ):
                resource = u.Infra.require_file_resource(
                    project.get_resource(source.relative_to(mod_workspace).as_posix()),
                    source,
                )
                module = u.Infra.resolve_pymodule(project, resource)
                tm.that(
                    u.Infra.import_source_role(project, module, source),
                    eq="layer0" if declares else "consumer",
                )

    @staticmethod
    @pytest.mark.parametrize(
        "case",
        [
            "publisher",
            "assigned-installer",
            "static-consumer",
            "runtime-root",
            "wrong-module",
            "wrong-attribute",
            "absent-export",
            "shadow-guard",
            "shadow-installer",
            "authored",
            "competing-write",
            "foreign-provider",
            "non-alias",
        ],
    )
    def test_only_canonical_static_publication_is_not_a_consumer(
        tmp_path: Path,
        *,
        case: str,
    ) -> None:
        """Real generated publication is allowed; consumer lookalikes stay banned."""
        mod_workspace, _package = u.Tests.create_lazy_init_workspace(tmp_path)
        layout = tm.not_none(u.Infra.layout(mod_workspace))
        namespace = layout.package_name
        class_name = f"{layout.class_stem}Models"
        u.Tests.write_lazy_init_namespace_module(
            layout.package_dir / "models.py", class_name=class_name, alias="m"
        )
        tm.ok(u.Cli.atomic_write_text_file(layout.init_path, ""))
        tm.that(u.Tests.run_lazy_init(mod_workspace), eq=0)
        generated = layout.init_path.read_text(encoding=c.DEFAULT_ENCODING)
        original_import = f"from {namespace}.models import"
        tm.that(generated, has=original_import)
        target = layout.init_path
        candidate = generated
        edits = {
            "assigned-installer": (
                generated,
                generated.replace(
                    "\ninstall_lazy_exports(", "\n__getattr__ = install_lazy_exports("
                ).rstrip()
                + "[0]\n",
            ),
            "runtime-root": ("if TYPE_CHECKING:", "if True:"),
            "wrong-attribute": ('"m": ".models"', '"m": (".models", "Different")'),
            "shadow-guard": (
                "if TYPE_CHECKING:",
                "TYPE_CHECKING = True\n\nif TYPE_CHECKING:",
            ),
            "shadow-installer": (
                "\ninstall_lazy_exports(",
                "\ninstall_lazy_exports = print\n\ninstall_lazy_exports(",
            ),
        }
        edit = edits.get(case)
        if edit is not None:
            candidate = candidate.replace(*edit)
        match case:
            case "static-consumer":
                target = layout.package_dir / "consumer.py"
            case "non-alias":
                target = layout.package_dir / "consumer.py"
                candidate = f"from {namespace}.models import {class_name}\n"
            case "wrong-module":
                u.Tests.write_lazy_init_namespace_module(
                    layout.package_dir / "other.py", class_name="OtherModels", alias="m"
                )
                candidate = candidate.replace(
                    original_import, f"from {namespace}.other import"
                )
            case "absent-export":
                declaration = next(
                    row
                    for row in u.Infra.logical_statements(candidate)
                    if row.text.startswith("__all__")
                )
                candidate = candidate.replace(declaration.text, "__all__ = ()", 1)
            case "authored":
                candidate = candidate.partition("\n")[2]
            case "competing-write":
                candidate += f"\nm = {class_name}\n"
            case "foreign-provider":
                candidate = candidate.replace(
                    original_import,
                    f"from {c.Infra.LAZY_BOOTSTRAP_ROOT_PACKAGE}.models import",
                )
                document = mod_workspace / c.PYPROJECT_FILENAME
                document.write_text(
                    document.read_text(encoding=c.DEFAULT_ENCODING).replace(
                        f"{c.Infra.DEPENDENCIES} = []",
                        f'{c.Infra.DEPENDENCIES} = ["flext-core"]',
                    ),
                    encoding=c.DEFAULT_ENCODING,
                )
            case _:
                pass
        if case not in {"publisher", "static-consumer"}:
            tm.ok(candidate != generated)
        tm.ok(u.Cli.atomic_write_text_file(target, candidate))
        report = tm.ok(
            FlextInfraModGateEngine.scan(
                mod_workspace,
                fix=False,
                selection=("ban-noncanonical-alias-import",),
                source_files=(target,),
            )
        )
        violations = tuple(
            row
            for row in report.entries
            if u.Infra.codemod_source_path(mod_workspace, row.file) == target
        )
        tm.that(
            len(violations),
            eq=0 if case in {"publisher", "assigned-installer", "non-alias"} else 1,
        )
        tm.that(target.read_text(encoding=c.DEFAULT_ENCODING), eq=candidate)

    @staticmethod
    def test_namespace_alias_and_adapter_rules_pass_native_fixtures(
        mod_workspace: Path,
    ) -> None:
        """The real catalog's publication and adapter rules pass their fixtures."""
        with u.Infra.codemod_workspace_snapshot(mod_workspace) as snapshot:
            plan = tm.ok(
                u.Infra.codemod_rule_plan(
                    snapshot,
                    rule_ids=(
                        "ban-noncanonical-alias-import",
                        "rewire-type-adapter-construction",
                        "rewire-type-adapter-construction-missing-u-import",
                    ),
                )
            )
        tm.ok(
            FlextInfraModGateEngine.validate_rule_fixtures(
                mod_workspace,
                tuple(dict.fromkeys(item.resource for item in plan.rules)),
            )
        )

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("producer", [False, True])
    @pytest.mark.parametrize("module_import", [False, True])
    def test_own_utility_import_requires_the_declared_producer_family(
        mod_workspace: Path,
        *,
        producer: bool,
        module_import: bool,
    ) -> None:
        """Consumer categories never borrow a real facade producer's role."""
        family = u.Infra.facade_families()["u"]
        tests_root = mod_workspace / c.Infra.DIR_TESTS
        tm.ok(u.Cli.ensure_dir(tests_root))
        tm.ok(
            u.Cli.atomic_write_text_file(
                tests_root / c.Infra.INIT_PY,
                f"from .{family.module} import u\n",
            )
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                tests_root / f"{family.module}.py",
                "from flext_core import u\n__all__ = ['u']\n",
            )
        )
        source = (
            (tests_root if producer else tests_root / "unit")
            / f"_{family.module}"
            / "probe.py"
        )
        tm.ok(u.Cli.ensure_dir(source.parent))
        tm.ok(
            u.Cli.atomic_write_text_file(
                source,
                f"import {tests_root.name}.{family.module}\n"
                if module_import
                else f"from {tests_root.name} import u\n",
            )
        )
        report = tm.ok(
            FlextInfraModGateEngine.scan(
                mod_workspace,
                fix=False,
                selection=("ban-utilities-own-letter-import",),
                source_files=(source,),
            )
        )
        tm.that(bool(report.entries), eq=producer)

    @staticmethod
    @pytest.mark.parametrize(
        "dependencies",
        [None, (), ("pydantic; python_version < '0'",)],
    )
    def test_empty_declared_runtime_rejects_installed_external_packages(
        tmp_path: Path,
        dependencies: t.StrSequence | None,
    ) -> None:
        """Omitted, empty and inapplicable requirements declare no providers."""
        project = u.Tests.mk_project(
            tmp_path,
            "runtime-probe",
            pyproject='[project]\nname = "runtime-probe"\nversion = "0.1.0"\n',
            with_src=True,
        )
        declaration: t.JsonDict = {
            "project": {"name": "runtime-probe", "version": "0.1.0"},
        }
        if dependencies is not None:
            declaration["project"] = {
                "name": "runtime-probe",
                "version": "0.1.0",
                "dependencies": list(dependencies),
            }
        tm.ok(u.Cli.toml_write_mapping(project / c.PYPROJECT_FILENAME, declaration))
        tm.that(u.Infra.codemod_runtime_modules(project), empty=True)
        tm.that(u.Infra.codemod_facade_packages(project), lacks="pydantic")

    @staticmethod
    def test_declared_installed_runtime_package_is_a_runtime_module(
        tmp_path: Path,
    ) -> None:
        """A nonempty real requirement reaches the runtime-package fact."""
        project = u.Tests.mk_project(
            tmp_path,
            "runtime-probe",
            pyproject=(
                '[project]\nname = "runtime-probe"\nversion = "0.1.0"\n'
                'dependencies = ["pydantic"]\n'
            ),
            with_src=True,
        )
        tm.that(u.Infra.codemod_runtime_modules(project), has="pydantic")


__all__: list[str] = ["TestsFlextInfraCodemodOwnPackageScans"]
