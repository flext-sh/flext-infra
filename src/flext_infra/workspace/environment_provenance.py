"""Fail-closed validation of local editables and locked CI build provenance.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import hashlib
import re
import sys
import sysconfig
from ast import (
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute as AstAttribute,
    BinOp,
    BitOr,
    Call,
    ClassDef,
    Constant,
    Expr,
    FunctionDef,
    Import,
    ImportFrom,
    List as AstList,
    Module,
    Name,
    Subscript,
    Tuple as AstTuple,
    iter_child_nodes,
    literal_eval,
    parse,
    unparse,
    walk,
)
from collections import namedtuple
from dataclasses import field, is_dataclass
from functools import lru_cache
from importlib.machinery import (
    BuiltinImporter,
    ExtensionFileLoader,
    FrozenImporter,
    PathFinder,
)
from importlib.util import resolve_name
from inspect import (
    getattr_static,
    getclosurevars,
    getsourcefile,
    isbuiltin,
    isclass,
    isfunction,
    ismethoddescriptor,
    signature,
)
from json import dumps
from pathlib import Path
from sys import modules
from types import (
    ClassMethodDescriptorType,
    CodeType,
    FunctionType,
    MemberDescriptorType,
    MethodDescriptorType,
    SimpleNamespace,
    WrapperDescriptorType,
)
from typing import TYPE_CHECKING, get_args, get_origin
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from flext_infra import c, m, p, r, t, u
from flext_infra.workspace import (
    FlextInfraFlextBindingService,
    FlextInfraWorkspaceDetector,
)

if TYPE_CHECKING:
    from importlib.metadata import Distribution


class FlextInfraWorkspaceEnvironmentProvenance:
    """Bind installed packages to live local or immutable CI workspace sources."""

    @staticmethod
    @lru_cache(maxsize=1)
    def installed_toolchain_identity() -> str:
        """Fingerprint the interpreter and installed distribution provenance.

        PEP 610 records distinguish Git revisions with equal package versions.
        Editable source paths are excluded because consumers track their source
        files independently. Registry distributions have no direct-URL receipt.

        Returns:
            The installed environment's deterministic SHA-256 identity.
        """
        provenance: t.MutableSequenceOf[str] = []
        for distribution in u.installed_distributions():
            receipt = distribution.read_text(c.Infra.DISTRIBUTION_DIRECT_URL_FILE)
            dir_info = (
                None
                if receipt is None
                else m.Infra.DirectUrlReceipt.model_validate_json(receipt).dir_info
            )
            identity = (
                "editable" if dir_info is not None and dir_info.editable else receipt
            )
            provenance.append(
                f"{distribution.name}={distribution.version}:{identity!r}",
            )
        fingerprint = "\n".join((sys.version, *sorted(provenance)))
        return hashlib.sha256(fingerprint.encode()).hexdigest()

    @classmethod
    def editable_members(
        cls,
        repository_root: Path,
        *,
        metadata_paths: t.StrSequence | None = None,
    ) -> p.Result[t.VariadicTuple[m.Infra.RepositoryRef]]:
        """Elect declared mutable members with authenticated installed editables.

        Frozen or registry-installed dependencies remain libraries even when
        their checkouts are present. The invocation's CI variable does not
        change the observed installation's ownership.

        Returns:
            Members whose installed metadata and physical source match declaration.

        """
        root = repository_root.expanduser().resolve()
        workspace = FlextInfraWorkspaceDetector.load_workspace_spec(root)
        if workspace.failure:
            return r[t.VariadicTuple[m.Infra.RepositoryRef]].from_failure(workspace)
        repositories = tuple(
            repository
            for repository in u.Infra.mutable_flext_members(workspace.value)
            if repository.package
        )
        observation: m.Infra.PythonEnvironmentObservation | None = None
        if metadata_paths is None and repositories:
            native = cls._observe_environment(root, repositories)
            if native.failure:
                return r[t.VariadicTuple[m.Infra.RepositoryRef]].from_failure(native)
            observation = native.value
            metadata_paths = tuple(str(path) for path in observation.metadata_paths)
        selected: list[m.Infra.RepositoryRef] = []
        for repository in repositories:
            matches = u.installed_distributions(
                name=repository.distribution,
                path=metadata_paths,
            )
            if len(matches) != 1:
                return r[t.VariadicTuple[m.Infra.RepositoryRef]].fail(
                    "member provenance distribution count mismatch: "
                    f"distribution={repository.distribution} expected=1 "
                    f"actual={len(matches)}",
                )
            raw = matches[0].read_text(c.Infra.DISTRIBUTION_DIRECT_URL_FILE)
            if raw is None:
                continue
            receipt = m.Infra.DirectUrlReceipt.model_validate_json(raw, strict=True)
            if receipt.dir_info is None or not receipt.dir_info.editable:
                continue
            if not repository.editable:
                return r[t.VariadicTuple[m.Infra.RepositoryRef]].fail(
                    f"member is installed editable against declaration: "
                    f"{repository.distribution}",
                )
            authenticated = cls.validate_editable_installation(
                repository,
                root,
                metadata_paths=metadata_paths,
            )
            if authenticated.failure:
                return r[t.VariadicTuple[m.Infra.RepositoryRef]].from_failure(
                    authenticated,
                )
            selected.append(repository)
        return r[t.VariadicTuple[m.Infra.RepositoryRef]].ok(tuple(selected))

    @classmethod
    def validate_editable_installation(
        cls,
        repository: m.Infra.RepositoryRef,
        resolved_root: Path,
        distribution: Distribution,
        receipt: m.Infra.DirectUrlReceipt,
    ) -> p.Result[bool]:
        """Authenticate installation ownership without importing member code."""
        expected_root = (resolved_root / repository.path).resolve()
        origin = cls._editable_url_verdict(
            repository.distribution,
            receipt,
            expected_root,
        )
        if origin.failure:
            return r[bool].from_failure(origin)
        inventory = cls._validate_pth_inventory(
            repository,
            distribution,
            expected_root,
        )
        if inventory.failure:
            return r[bool].from_failure(inventory)
        return cls._submodule_gitlink_verdict(
            repository,
            resolved_root,
            expected_root,
            r[bool].ok(value=True),
        )

    @classmethod
    def execute_request(
        cls,
        request: p.Infra.WorkspaceEnvironmentRequest,
    ) -> p.Result[int]:
        """Validate one CLI request without mutating the environment.

        Returns:
            The resulting ``p.Result[int]``.

        """
        return cls.validate(request.repository_root)

    @classmethod
    def validate(
        cls,
        repository_root: Path,
        *,
        metadata_paths: t.StrSequence | None = None,
    ) -> p.Result[int]:
        """Validate PEP 610 and editable path metadata for active members.

        Returns:
            The resulting ``p.Result[int]``.

        """
        context = FlextInfraWorkspaceDetector.resolution_context(repository_root)
        if context.failure:
            return r[int].from_failure(context)
        resolved_root = context.value.runtime_root
        if context.value.standalone:
            return cls.validate_locked(resolved_root, metadata_paths=metadata_paths)
        workspace_result = FlextInfraWorkspaceDetector.load_workspace_spec(
            resolved_root,
        )
        if workspace_result.failure:
            return r[int].from_failure(workspace_result)
        repositories = tuple(
            repository
            for repository in (
                workspace_result.value.repository,
                *workspace_result.value.subprojects,
            )
            if repository.package and repository.editable
        )
        observation: m.Infra.PythonEnvironmentObservation | None = None
        if metadata_paths is None and repositories:
            native = cls._observe_environment(resolved_root, repositories)
            if native.failure:
                return r[int].from_failure(native)
            observation = native.value
            metadata_paths = tuple(str(path) for path in observation.metadata_paths)
        validated = 0
        for repository in repositories:
            provenance = cls._validate_editable_provenance(
                repository,
                resolved_root,
                metadata_paths=metadata_paths,
                observation=observation,
            )
            if provenance.failure:
                return r[int].from_failure(provenance)
            validated += int(provenance.value)
        return r[int].ok(validated)

    @staticmethod
    def _observe_environment(
        root: Path,
        repositories: t.VariadicTuple[m.Infra.RepositoryRef],
    ) -> p.Result[m.Infra.PythonEnvironmentObservation]:
        """Read package facts exclusively through the elected physical runtime."""
        context = FlextInfraWorkspaceDetector.resolution_context(root)
        if context.failure:
            return r[m.Infra.PythonEnvironmentObservation].from_failure(context)
        return FlextInfraFlextBindingService.consumer_package_environment(
            consumer_root=root,
            python=u.Infra.runtime_python(
                root,
                runtime_root=context.value.runtime_root,
            ),
            packages=tuple(
                u.Infra.project_package_name(root / repository.path)
                for repository in repositories
            ),
        )

    @classmethod
    def _validate_editable_provenance(
        cls,
        repository: m.Infra.RepositoryRef,
        resolved_root: Path,
        *,
        metadata_paths: t.StrSequence | None,
        observation: m.Infra.PythonEnvironmentObservation | None,
    ) -> p.Result[bool]:
        """Prove one editable member's PEP 610 and path metadata provenance.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        matches = u.installed_distributions(
            name=repository.distribution,
            path=metadata_paths,
        )
        if len(matches) != 1:
            return r[bool].fail(
                "editable provenance distribution count mismatch: "
                f"distribution={repository.distribution} expected=1 "
                f"actual={len(matches)}",
            )
        distribution = matches[0]
        if observation is not None and not Path(
            str(distribution.locate_file("")),
        ).resolve().is_relative_to(observation.prefix.resolve()):
            return r[bool].fail(
                "editable distribution is outside the owned environment: "
                f"{repository.distribution}",
            )
        expected_root = (resolved_root / repository.path).resolve()
        direct_url_result = cls._validate_direct_url(
            repository.distribution,
            distribution.read_text(c.Infra.DISTRIBUTION_DIRECT_URL_FILE),
            expected_root,
        )
        if direct_url_result.failure:
            return r[bool].from_failure(direct_url_result)
        inventory = cls._validate_pth_inventory(
            repository,
            distribution,
            expected_root,
        )
        if inventory.failure:
            return r[bool].from_failure(inventory)
        if observation is None:
            source_result = r[bool].ok(value=True)
        else:
            package_name = u.Infra.project_package_name(expected_root)
            directories = observation.package_directories.get(package_name, ())
            if (
                len(directories) != 1
                or not directories[0].is_dir()
                or not directories[0].resolve().is_relative_to(expected_root)
            ):
                return r[bool].fail(
                    "editable provenance import source differs from declaration: "
                    f"distribution={repository.distribution} expected={expected_root} "
                    f"actual={directories}",
                )
            if Path(sys.prefix).resolve() == observation.prefix.resolve():
                source_result = cls._validate_import_source(repository, expected_root)
            else:
                u.Cli.info(
                    f"environment distribution={repository.distribution} "
                    f"import_source={directories[0].resolve()} "
                    "loaded_code=unobserved resolver_only=True",
                )
                source_result = r[bool].ok(value=False)
        if source_result.failure:
            return r[bool].from_failure(source_result)
        return cls._submodule_gitlink_verdict(
            repository,
            resolved_root,
            expected_root,
            source_result,
        )

    @classmethod
    def _validate_pth_inventory(
        cls,
        repository: m.Infra.RepositoryRef,
        distribution: Distribution,
        expected_root: Path,
    ) -> p.Result[int]:
        """Prove the installed file inventory yields exactly one editable .pth.

        Returns:
            The resulting ``p.Result[int]``.

        """
        files = distribution.files
        if files is None:
            return r[int].fail(
                "editable provenance has no installed file inventory: "
                f"distribution={repository.distribution}",
            )
        u.Cli.info(
            f"environment distribution={repository.distribution} "
            f"installed_version={distribution.version} "
            f"installed_location={distribution.locate_file('')} "
            f"record_files={len(files)} expected_source={expected_root}",
        )
        pth_files = tuple(
            Path(str(distribution.locate_file(file)))
            for file in files
            if str(file).endswith(".pth")
        )
        if len(pth_files) != 1:
            return r[int].fail(
                "editable provenance pth count mismatch: "
                f"distribution={repository.distribution} expected=1 "
                f"actual={len(pth_files)}",
            )
        return cls._validate_pth(
            repository.distribution,
            pth_files[0],
            expected_root,
        )

    @classmethod
    def _submodule_gitlink_verdict(
        cls,
        repository: m.Infra.RepositoryRef,
        resolved_root: Path,
        expected_root: Path,
        source_result: p.Result[bool],
    ) -> p.Result[bool]:
        """Extend a passing source verdict with the submodule gitlink identity.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if repository.checkout is not c.Infra.CheckoutKind.SUBMODULE:
            return source_result
        identity = u.Infra.git_identity(
            m.Infra.GitRepoRequest(repo_root=expected_root),
        )
        if identity.failure:
            return r[bool].from_failure(identity)
        return cls._workspace_gitlink_verdict(
            repository,
            resolved_root,
            identity.value.head_oid,
        )

    @classmethod
    def _validate_import_source(
        cls,
        repository: m.Infra.RepositoryRef,
        expected_root: Path,
    ) -> p.Result[bool]:
        """Authenticate loaded modules and owned code against the declared source.

        Returns:
            The resulting ``p.Result[bool]``.
        """
        package_name = u.Infra.project_package_name(expected_root)
        package = u.Infra.declared_package_dir(package_name)
        if (
            package is None
            or not package.is_dir()
            or not package.resolve().is_relative_to(expected_root)
        ):
            return r[bool].fail(
                "editable provenance import source differs from declaration: "
                f"distribution={repository.distribution} expected={expected_root} "
                f"actual={package}",
            )
        u.Cli.info(
            f"environment distribution={repository.distribution} "
            f"import_source={package.resolve()}",
        )
        sources = cls.loaded_import_sources(package_name, expected_root=expected_root)
        if sources.failure:
            return r[bool].from_failure(sources)
        if not sources.value:
            u.Cli.info(
                f"environment distribution={repository.distribution} "
                "loaded_code=unobserved resolver_only=True",
            )
            return r[bool].ok(value=False)
        return r[bool].ok(value=True)

    @classmethod
    def loaded_import_sources(
        cls,
        package_name: str,
        *,
        expected_root: Path | None = None,
    ) -> p.Result[t.SequenceOf[t.Triple[str, str, str]]]:
        """Collect actual module, function and generated class-owner sources.

        Returns:
            Observed sources without importing dormant package capabilities.
        """
        source_files: t.MutableSequenceOf[t.Triple[str, str, str]] = []
        for name in tuple(modules):
            if name != package_name and not name.startswith(f"{package_name}."):
                continue
            module = modules.get(name)
            if module is None:
                return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                    f"editable provenance module is unavailable: {name}",
                )
            origin = cls._module_source(name)
            if origin.failure:
                return r[t.SequenceOf[t.Triple[str, str, str]]].from_failure(origin)
            source_files.append((name, str(origin.value), ""))
            definitions = cls._declaration_sources(name)
            if definitions.failure:
                return r[t.SequenceOf[t.Triple[str, str, str]]].from_failure(
                    definitions
                )
            source_files.extend(definitions.value)
        if expected_root is not None:
            for definition_name, source, class_source in source_files:
                supplier = definition_name.partition("::")[0]
                actual = Path(class_source or source).resolve()
                if (
                    supplier == package_name or supplier.startswith(f"{package_name}.")
                ) and not actual.is_relative_to(expected_root):
                    return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                        "editable provenance loaded code differs from declaration: "
                        f"package={package_name} expected={expected_root} "
                        f"actual={actual} definition={definition_name}",
                    )
        return r[t.SequenceOf[t.Triple[str, str, str]]].ok(tuple(source_files))

    @classmethod
    def _declaration_sources(
        cls,
        module_name: str,
        selected: p.AttributeProbe | None = None,
        selected_receiver: p.AttributeProbe | None = None,
        selected_attribute: str | None = None,
    ) -> p.Result[t.SequenceOf[t.Triple[str, str, str]]]:
        """Authenticate declarations, wrapper links and native compiler scopes.

        Returns:
            Code sources whose generated definitions have authenticated owners.
        """
        pending = [
            (value, None, name)
            for name, value in tuple(vars(modules[module_name]).items())
        ]
        if selected is not None:
            if not isfunction(selected):
                return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                    "selected source witness is not a Python function"
                )
            if selected_receiver is not None and not isclass(selected_receiver):
                return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                    "selected source receiver is not a class"
                )
            pending = [
                (
                    selected,
                    selected_receiver,
                    selected.__name__
                    if selected_attribute is None
                    else selected_attribute,
                )
            ]
        visited = {}
        authenticated_functions: set[int] = set()
        constructions: t.MutableMappingKV[
            t.Pair[str, str], m.Infra.SourceConstruction
        ] = {}
        sources: t.MutableSequenceOf[t.Triple[str, str, str]] = []
        module = modules[module_name]
        module_origin = cls._module_source(module_name)
        if module_origin.failure:
            return r[t.SequenceOf[t.Triple[str, str, str]]].from_failure(module_origin)
        native = module.__spec__.loader is BuiltinImporter or isinstance(
            module.__spec__.loader, ExtensionFileLoader
        )
        declarations = {}
        native_imports = []
        if not native:
            declaration_source = getsourcefile(module)
            if declaration_source is None:
                return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                    f"producer module has no Python declaration source: {module_name}"
                )
            state = u.Cli.atomic_read_binary_file_state(
                Path(declaration_source), required=True
            )
            if state.failure:
                return r[t.SequenceOf[t.Triple[str, str, str]]].from_failure(state)
            if state.value.content is None:
                return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                    f"producer class source bytes are absent: {declaration_source}"
                )
            sources.append((module_name, declaration_source, ""))
            syntax = [
                (node, "")
                for node in iter_child_nodes(
                    parse(state.value.content, filename=declaration_source)
                )
            ]
            while syntax:
                node, scope = syntax.pop()
                nested_scope = scope
                if not scope and isinstance(node, ImportFrom) and node.level == 0:
                    provider = modules.get(node.module)
                    if (
                        provider is not None
                        and provider.__spec__ is not None
                        and (
                            provider.__spec__.loader is BuiltinImporter
                            or isinstance(provider.__spec__.loader, ExtensionFileLoader)
                        )
                    ):
                        native_imports.extend(
                            (provider.__spec__.name, vars(provider).get(alias.name))
                            for alias in node.names
                        )
                if isinstance(node, ClassDef | FunctionDef | AsyncFunctionDef):
                    qualified = f"{scope}.{node.name}" if scope else node.name
                    nested_scope = (
                        qualified
                        if isinstance(node, ClassDef)
                        else f"{qualified}.<locals>"
                    )
                    if isinstance(node, ClassDef):
                        declarations.setdefault(qualified, []).append(node)
                syntax.extend((child, nested_scope) for child in iter_child_nodes(node))
        while pending:
            definition, receiver, binding_name = pending.pop()
            if isclass(definition):
                if (
                    getattr_static(definition, "__module__", None) == module_name
                    and id(definition) not in visited
                ):
                    if getattr_static(
                        type(definition), "__getattribute__", None
                    ) is not getattr_static(type, "__getattribute__", None):
                        return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                            "producer class has an unadmitted metadata accessor: "
                            f"module={module_name} binding={binding_name}"
                        )
                    visited[id(definition)] = definition
                    if native:
                        namespace = vars(module)
                        for component in definition.__qualname__.split("."):
                            candidate = namespace.get(component)
                            if not isclass(candidate):
                                return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                                    f"producer native class is not registered: {definition.__qualname__}"
                                )
                            namespace = vars(candidate)
                        if candidate is not definition or any(
                            isfunction(value) for value in namespace.values()
                        ):
                            return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                                f"producer native class identity differs: {definition.__qualname__}"
                            )
                        sources.append((
                            f"{module_name}::{definition.__qualname__}",
                            str(module_origin.value),
                            "",
                        ))
                        continue
                    matches = declarations.get(definition.__qualname__, ())
                    imported = tuple(
                        supplier
                        for supplier, value in native_imports
                        if value is definition
                    )
                    if imported:
                        for supplier in imported:
                            supplied = cls._module_source(supplier)
                            if supplied.failure:
                                return r[
                                    t.SequenceOf[t.Triple[str, str, str]]
                                ].from_failure(supplied)
                            sources.append((
                                f"{supplier}::{definition.__qualname__}",
                                str(supplied.value),
                                "",
                            ))
                        continue
                    if len(matches) != 1 or matches[0].name != definition.__name__:
                        return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                            "producer class has no unique current native declaration: "
                            f"{definition.__qualname__}"
                        )
                    declaration = matches[0]
                    declared_fields = tuple(
                        node.target.id
                        for node in declaration.body
                        if isinstance(node, AnnAssign) and isinstance(node.target, Name)
                    )
                    if tuple in definition.__bases__:
                        if definition._fields != declared_fields:
                            return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                                f"producer class fields differ from native declaration: {definition.__qualname__}"
                            )
                    if is_dataclass(definition) and set(
                        vars(definition).get("__annotations__", {})
                    ) != set(declared_fields):
                        return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                            f"producer dataclass field layout differs from native declaration: {definition.__qualname__}"
                        )
                    sources.append((
                        f"{module_name}::{definition.__qualname__}",
                        declaration_source,
                        "",
                    ))
                    pending.extend(
                        (value, base, name)
                        for base in definition.__mro__
                        for name, value in tuple(vars(base).items())
                    )
                    if is_dataclass(definition):
                        for node in declaration.body:
                            if not isinstance(node, AnnAssign) or not isinstance(
                                node.target, Name
                            ):
                                continue
                            field_metadata = definition.__dataclass_fields__[
                                node.target.id
                            ]
                            if (
                                isinstance(node.value, Constant)
                                and field_metadata.default != node.value.value
                            ):
                                return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                                    f"producer dataclass default differs from native declaration: {definition.__qualname__}.{node.target.id}"
                                )
                            if (
                                isinstance(node.value, Call)
                                and isinstance(node.value.func, Name)
                                and vars(modules[module_name]).get(node.value.func.id)
                                is field
                            ):
                                for keyword in node.value.keywords:
                                    if (
                                        isinstance(keyword.value, Constant)
                                        and keyword.arg is not None
                                        and getattr(field_metadata, keyword.arg)
                                        != keyword.value.value
                                    ):
                                        return r[
                                            t.SequenceOf[t.Triple[str, str, str]]
                                        ].fail(
                                            f"producer dataclass field differs from native declaration: {definition.__qualname__}.{node.target.id}.{keyword.arg}"
                                        )
                        pending.extend(
                            (field.default_factory, None, field.name)
                            for field in definition.__dataclass_fields__.values()
                            if isfunction(field.default_factory)
                        )
                continue
            if isinstance(definition, property):
                pending.extend(
                    (accessor, receiver, binding_name)
                    for accessor in (definition.fget, definition.fset, definition.fdel)
                    if accessor is not None
                )
                continue
            outer = (
                definition.__func__
                if type(definition) in {classmethod, staticmethod}
                else definition
            )
            if not isfunction(outer):
                continue
            link = outer
            chain: set[int] = set()
            suppliers: set[str] = set()
            compiler_labels: set[str] = set()
            deferred = False
            while isfunction(link):
                if id(link) in chain:
                    return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                        f"producer wrapper cycle: {outer.__qualname__}"
                    )
                chain.add(id(link))
                supplier = link.__globals__.get("__name__")
                source = link.__code__.co_filename
                class_source = ""
                frozen_supplier = (
                    isinstance(supplier, str)
                    and supplier in modules
                    and link.__globals__ is vars(modules[supplier])
                    and modules[supplier].__spec__ is not None
                    and modules[supplier].__spec__.origin == "frozen"
                )
                constructed_binding = (
                    isclass(receiver)
                    and not frozen_supplier
                    and (
                        link.__code__.co_qualname.rpartition(".")[0]
                        != receiver.__qualname__
                        or binding_name != link.__code__.co_name
                    )
                    and link.__module__ == receiver.__module__
                    and "__wrapped__" not in vars(link)
                )
                if (
                    source.startswith("<")
                    and source.endswith(">")
                    and not frozen_supplier
                ) or (constructed_binding and "<locals>" in link.__code__.co_qualname):
                    generated_owner = receiver
                    if not isclass(generated_owner):
                        return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                            "producer generated scope has no declared receiver: "
                            f"{outer.__qualname__}; supplier={supplier!r}; "
                            f"code={source!r}; qualified={link.__code__.co_qualname!r}; "
                            f"freevars={link.__code__.co_freevars!r}; "
                            f"globals_registered={isinstance(supplier, str) and supplier in modules and link.__globals__ is vars(modules[supplier])}"
                        )
                    identity = (
                        generated_owner.__module__,
                        generated_owner.__qualname__,
                    )
                    if identity not in constructions:
                        construction = cls._source_syntax_definition(*identity)
                        if construction.failure:
                            return r[
                                t.SequenceOf[t.Triple[str, str, str]]
                            ].from_failure(construction)
                        constructions[identity] = construction.value
                    witness = constructions[identity]
                    factories = witness.factories
                    unauthenticated = tuple(
                        factory
                        for factory in factories
                        if id(factory) not in authenticated_functions
                    )
                    if unauthenticated:
                        pending.append((outer, receiver, binding_name))
                        pending.extend(
                            (factory, None, factory.__name__)
                            for factory in unauthenticated
                        )
                        deferred = True
                        break
                    declaration = cls._compiler_definition_owner(
                        generated_owner.__module__,
                        f"{generated_owner.__qualname__}.{binding_name}",
                        id(outer),
                        id(receiver),
                        id(link),
                        witness,
                    )
                    if declaration.failure:
                        return r[t.SequenceOf[t.Triple[str, str, str]]].from_failure(
                            declaration
                        )
                    class_source, compiler_label = declaration.value
                    compiler_labels.add(compiler_label)
                    if source.startswith("<") and source.endswith(">"):
                        supplier = generated_owner.__module__
                    suppliers.update(factory.__module__ for factory in factories)
                    sources.extend(witness.code_sources)
                    suppliers.add(generated_owner.__module__)
                if not class_source and (
                    not isinstance(supplier, str)
                    or supplier not in modules
                    or link.__globals__ is not vars(modules[supplier])
                ):
                    return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                        f"producer function globals have no native module: {outer.__qualname__}"
                    )
                origin = cls._module_source(supplier)
                if origin.failure:
                    return r[t.SequenceOf[t.Triple[str, str, str]]].from_failure(origin)
                suppliers.add(supplier)
                suppliers.add(modules[supplier].__spec__.name)
                if (
                    not class_source
                    and receiver
                    and (link is outer or "__wrapped__" not in vars(link))
                ):
                    namespace = vars(modules[supplier])
                    declaring = None
                    for component in link.__code__.co_qualname.rpartition(".")[0].split(
                        "."
                    ):
                        candidate = namespace.get(component)
                        if not isclass(candidate):
                            declaring = None
                            break
                        declaring = candidate
                        namespace = vars(candidate)
                    if not frozen_supplier:
                        identity = (receiver.__module__, receiver.__qualname__)
                        if identity not in constructions:
                            attachment = cls._source_syntax_definition(*identity)
                            if attachment.failure:
                                return r[
                                    t.SequenceOf[t.Triple[str, str, str]]
                                ].from_failure(attachment)
                            constructions[identity] = attachment.value
                        attachment = constructions[identity]
                        if attachment.owner is not receiver or not isinstance(
                            attachment.declaration, ClassDef
                        ):
                            return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                                "alias receiver differs from its physical declaration"
                            )
                        aliases = tuple(
                            statement.value
                            for statement in attachment.declaration.body
                            if (
                                isinstance(statement, Assign)
                                and any(
                                    isinstance(target, Name)
                                    and target.id == binding_name
                                    for target in statement.targets
                                )
                            )
                            or (
                                isinstance(statement, AnnAssign)
                                and isinstance(statement.target, Name)
                                and statement.target.id == binding_name
                            )
                        )
                        foreign_owner = isclass(declaring) and not any(
                            base is declaring for base in receiver.__mro__
                        )
                        if (aliases or foreign_owner) and (
                            len(aliases) != 1
                            or not isinstance(aliases[0], Name | AstAttribute)
                            or any(
                                isinstance(statement, FunctionDef | AsyncFunctionDef)
                                and statement.name == binding_name
                                for statement in attachment.declaration.body
                            )
                        ):
                            return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                                "descriptor has no unique physical alias declaration"
                            )
                        if aliases:
                            if (
                                len(receiver.__bases__)
                                != len(attachment.bases or (object,))
                                or any(
                                    actual is not expected
                                    for actual, expected in zip(
                                        receiver.__bases__,
                                        attachment.bases or (object,),
                                        strict=False,
                                    )
                                )
                                or (
                                    attachment.metaclass is not None
                                    and type(receiver) is not attachment.metaclass
                                )
                            ):
                                return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                                    "alias receiver layout differs from its physical declaration"
                                )
                            alias = cls._construction_binding(
                                aliases[0],
                                attachment,
                                vars(modules[receiver.__module__]),
                            )
                            if alias.failure:
                                return r[
                                    t.SequenceOf[t.Triple[str, str, str]]
                                ].from_failure(alias)
                            if alias.value.value is not getattr_static(
                                receiver, binding_name, None
                            ):
                                return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                                    "descriptor differs from its physical alias supplier"
                                )
                            if isclass(declaring):
                                supplied = cls._source_syntax_definition(
                                    supplier, declaring.__qualname__
                                )
                                if supplied.failure:
                                    return r[
                                        t.SequenceOf[t.Triple[str, str, str]]
                                    ].from_failure(supplied)
                                if supplied.value.owner is not declaring:
                                    return r[
                                        t.SequenceOf[t.Triple[str, str, str]]
                                    ].fail(
                                        "alias supplier differs from its physical declaration"
                                    )
                                descriptor = getattr_static(
                                    declaring, link.__code__.co_name, None
                                )
                                if type(descriptor) in {classmethod, staticmethod}:
                                    descriptor = descriptor.__func__
                                if descriptor is not link and not (
                                    isinstance(descriptor, property)
                                    and any(
                                        accessor is link
                                        for accessor in (
                                            descriptor.fget,
                                            descriptor.fset,
                                            descriptor.fdel,
                                        )
                                    )
                                ):
                                    return r[
                                        t.SequenceOf[t.Triple[str, str, str]]
                                    ].fail(
                                        "alias executable differs from its supplier descriptor"
                                    )
                                sources.append((
                                    f"{supplier}::{declaring.__qualname__}",
                                    str(supplied.value.source),
                                    "",
                                ))
                            sources.extend(attachment.code_sources)
                    declared = getattr_static(receiver, binding_name, None)
                    if isinstance(declared, p.Infra.FunctionDescriptor):
                        declared = declared.__func__
                    if not (
                        declared is outer
                        or (
                            isinstance(declared, property)
                            and any(
                                accessor is outer
                                for accessor in (
                                    declared.fget,
                                    declared.fset,
                                    declared.fdel,
                                )
                            )
                        )
                    ):
                        return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                            "producer descriptor identity differs from declared owner: "
                            f"{outer.__qualname__}; receiver={receiver.__qualname__}; "
                            f"attribute={binding_name}"
                        )
                    attached = cls._module_source(receiver.__module__)
                    if attached.failure:
                        return r[t.SequenceOf[t.Triple[str, str, str]]].from_failure(
                            attached
                        )
                    suppliers.add(receiver.__module__)
                    sources.append((
                        f"{receiver.__module__}::{receiver.__qualname__}.{binding_name}",
                        str(attached.value),
                        "",
                    ))
                if class_source and source.startswith("<") and source.endswith(">"):
                    pending_code = []
                elif frozen_supplier:
                    pending_code = [
                        FrozenImporter.get_code(modules[supplier].__spec__.name)
                    ]
                    source = str(origin.value)
                else:
                    if Path(source).absolute() != origin.value:
                        return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                            f"producer executed code differs from elected module: "
                            f"{outer.__qualname__}={source}; elected={origin.value}"
                        )
                    state = u.Cli.atomic_read_binary_file_state(
                        origin.value, required=True
                    )
                    if state.failure:
                        return r[t.SequenceOf[t.Triple[str, str, str]]].from_failure(
                            state
                        )
                    if state.value.content is None:
                        return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                            f"producer executed source bytes are absent: {origin.value}"
                        )
                    pending_code = [
                        compile(state.value.content, source, "exec", dont_inherit=True)
                    ]
                    if constructed_binding and "." not in link.__code__.co_qualname:
                        helper_declarations = [
                            node
                            for node in parse(state.value.content).body
                            if isinstance(node, FunctionDef | AsyncFunctionDef)
                            and node.name == link.__code__.co_name
                            and node.lineno == link.__code__.co_firstlineno
                        ]
                        if len(helper_declarations) != 1:
                            return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                                "factory-bound helper has no unique physical function declaration",
                            )
                        arguments = helper_declarations[0].args
                        if (
                            not arguments.defaults and link.__defaults__ is not None
                        ) or (
                            not any(
                                value is not None for value in arguments.kw_defaults
                            )
                            and link.__kwdefaults__ is not None
                        ):
                            return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                                "factory-bound helper defaults differ from physical declaration",
                            )
                if class_source:
                    owner_origin = cls._module_source(generated_owner.__module__)
                    if owner_origin.failure:
                        return r[t.SequenceOf[t.Triple[str, str, str]]].from_failure(
                            owner_origin
                        )
                    if Path(class_source).absolute() != owner_origin.value:
                        return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                            f"producer generated class differs from elected module: {outer.__qualname__}"
                        )
                if not class_source or not (
                    source.startswith("<") and source.endswith(">")
                ):
                    expected_code = None
                    while pending_code:
                        code = pending_code.pop()
                        if code.co_qualname == link.__code__.co_qualname:
                            expected_code = code
                        if code == link.__code__:
                            break
                        pending_code.extend(
                            value
                            for value in code.co_consts
                            if isinstance(value, CodeType)
                        )
                    else:
                        differences = (
                            tuple(
                                field
                                for field in dir(expected_code)
                                if field.startswith("co_")
                                and not callable(getattr(expected_code, field))
                                and getattr(expected_code, field)
                                != getattr(link.__code__, field)
                            )
                            if expected_code is not None
                            else ("declaration-identity",)
                        )
                        return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                            f"producer executed code differs from native source: "
                            f"{outer.__qualname__}; fields={','.join(differences)}; "
                            f"source={origin.value}; "
                            f"declared_line={expected_code.co_firstlineno if expected_code is not None else None}; "
                            f"executed_line={link.__code__.co_firstlineno}; "
                            f"declared_flags={expected_code.co_flags if expected_code is not None else None}; "
                            f"executed_flags={link.__code__.co_flags}; optimize={sys.flags.optimize}; "
                            f"declared_names={expected_code.co_names if expected_code is not None else ()}; "
                            f"executed_names={link.__code__.co_names}"
                        )
                if class_source and not (
                    source.startswith("<") and source.endswith(">")
                ):
                    sources.append((
                        f"{generated_owner.__module__}::{generated_owner.__qualname__}.{binding_name}",
                        class_source,
                        class_source,
                    ))
                sources.append((
                    f"{supplier}::{outer.__qualname__}",
                    source,
                    class_source
                    if source.startswith("<") and source.endswith(">")
                    else "",
                ))
                if "__wrapped__" not in vars(link):
                    break
                wrapped = vars(link)["__wrapped__"]
                closure = getclosurevars(link)
                if not any(
                    value is wrapped
                    for value in (
                        *closure.nonlocals.values(),
                        *closure.globals.values(),
                    )
                ):
                    return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                        f"producer wrapped link is not executed by wrapper: {outer.__qualname__}"
                    )
                link = wrapped
            if not isfunction(link):
                native_owner = getattr(link, "__objclass__", None)
                supplier = (
                    native_owner.__module__
                    if isclass(native_owner)
                    else getattr(link, "__module__", None)
                )
                name = getattr(link, "__name__", None)
                namespace = (
                    vars(native_owner)
                    if isclass(native_owner)
                    else vars(modules[supplier])
                    if isinstance(supplier, str) and supplier in modules
                    else {}
                )
                if (
                    not (isbuiltin(link) or ismethoddescriptor(link))
                    or not isinstance(supplier, str)
                    or namespace.get(name) is not link
                ):
                    return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                        f"producer native wrapped descriptor has no bound owner: {outer.__qualname__}"
                    )
                if isclass(native_owner):
                    registered = vars(modules[supplier])
                    for component in native_owner.__qualname__.split("."):
                        candidate = registered.get(component)
                        if not isclass(candidate):
                            return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                                f"producer native descriptor class is not registered: {outer.__qualname__}"
                            )
                        registered = vars(candidate)
                    if candidate is not native_owner:
                        return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                            f"producer native descriptor class identity differs: {outer.__qualname__}"
                        )
                origin = cls._module_source(supplier)
                if origin.failure:
                    return r[t.SequenceOf[t.Triple[str, str, str]]].from_failure(origin)
                suppliers.add(supplier)
                sources.append((
                    f"{supplier}::{outer.__qualname__}",
                    str(origin.value),
                    "",
                ))
            if deferred:
                continue
            if (
                outer.__module__ not in suppliers
                and outer.__module__ not in compiler_labels
            ):
                return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                    f"producer advertised module has no executed supplier: {outer.__qualname__}={outer.__module__}"
                )
            authenticated_functions.add(id(outer))
        return r[t.SequenceOf[t.Triple[str, str, str]]].ok(tuple(sources))

    @staticmethod
    def _module_source(module_name: str) -> p.Result[Path]:
        """Authenticate cold supplier election and the native Python base."""
        module = modules[module_name]
        native = module.__spec__
        if (
            native is None
            or modules.get(native.name) is not module
            or (
                native.name != module_name
                and (
                    native.origin not in {"built-in", "frozen"}
                    or module_name.partition(".")[0] not in sys.stdlib_module_names
                )
            )
        ):
            return r[Path].fail(f"producer module lacks its native spec: {module_name}")
        components = module_name.split(".")
        interpreter = Path(sys.executable).resolve()
        if components[0] in sys.stdlib_module_names:
            base = Path(sys.base_prefix).resolve()
            standard = Path(
                sysconfig.get_path(
                    "stdlib",
                    vars={
                        "base": sys.base_prefix,
                        "platbase": sys.base_exec_prefix,
                    },
                )
            ).resolve()
            extension = sysconfig.get_config_var("DESTSHARED")
            if not isinstance(extension, str):
                return r[Path].fail(
                    "producer Python base lacks its native extension directory"
                )
            extension_root = Path(extension).resolve()
            if (
                not interpreter.is_relative_to(base)
                or not standard.is_relative_to(base)
                or not extension_root.is_relative_to(base)
            ):
                return r[Path].fail(
                    "producer standard library differs from native Python base"
                )
            physical = u.Cli.atomic_plan_directory_chain(standard)
            if physical.failure:
                return r[Path].from_failure(physical)
            if native.origin == "built-in":
                spec = BuiltinImporter.find_spec(native.name)
            elif native.origin == "frozen":
                spec = FrozenImporter.find_spec(native.name)
            else:
                spec = PathFinder.find_spec(
                    components[0], [str(standard), str(extension_root)]
                )
        else:
            spec = PathFinder.find_spec(components[0])
        if native.origin not in {"built-in", "frozen"}:
            for index in range(1, len(components)):
                if spec is None or not spec.submodule_search_locations:
                    return r[Path].fail(
                        f"producer module has no cold parent: {module_name}"
                    )
                spec = PathFinder.find_spec(
                    ".".join(components[: index + 1]),
                    spec.submodule_search_locations,
                )
        if (
            spec is None
            or spec.origin != native.origin
            or type(spec.loader) is not type(native.loader)
            or module.__loader__ is not native.loader
        ):
            return r[Path].fail(
                f"producer module election differs from loaded spec: {module_name}"
            )
        if spec.origin == "frozen" and (
            native.loader is not spec.loader
            or native.loader_state != spec.loader_state
            or getsourcefile(module) != spec.loader_state.filename
        ):
            return r[Path].fail(
                f"producer frozen declaration source differs from native loader: {module_name}"
            )
        if spec.origin in {"built-in", "frozen"}:
            return r[Path].ok(interpreter)
        if spec.origin is None or getattr(module, "__file__", None) != spec.origin:
            return r[Path].fail(
                f"producer loaded module differs from cold origin: {module_name}"
            )
        return r[Path].ok(Path(spec.origin).absolute())

    @classmethod
    def _source_syntax_definition(
        cls,
        module_name: str,
        owner_path: str,
    ) -> p.Result[m.Infra.SourceConstruction]:
        """Elect a physical class and its source-declared construction suppliers.

        Runtime bindings authenticate the source's references; they do not select
        declarations or provide generator options. One AST walk serves construction
        and descriptor attachment, including nested classes and native factories.
        """
        result_type = r[m.Infra.SourceConstruction]
        origin = cls._module_source(module_name)
        if origin.failure:
            return result_type.from_failure(origin)
        captured = u.Cli.atomic_read_binary_file_state(origin.value, required=True)
        if captured.failure:
            return result_type.from_failure(captured)
        if captured.value.content is None:
            return result_type.fail("construction declaration has no captured source")
        syntax = parse(captured.value.content, filename=str(origin.value))
        body = syntax.body
        factories = []
        namespace = vars(modules[module_name])
        actual_namespace = namespace
        witness = m.Infra.SourceConstruction(
            source=origin.value,
            syntax=syntax,
            declaration=syntax,
            factories=(),
        )
        for component in owner_path.split("."):
            matches = tuple(
                node
                for node in body
                if isinstance(node, ClassDef | FunctionDef | AsyncFunctionDef)
                and node.name == component
            )
            if len(matches) != 1:
                return result_type.fail(
                    "construction declaration has no unique class owner"
                )
            declaration = matches[0]
            witness.declaration = declaration
            witness.bases, witness.decorators, witness.metaclass = (), (), None
            if not isinstance(declaration, ClassDef):
                body = declaration.body
                continue
            owner = actual_namespace.get(component)
            if not isclass(owner) or getattr_static(
                type(owner), "__getattribute__", None
            ) is not getattr_static(type, "__getattribute__", None):
                return result_type.fail(
                    "construction owner has an unadmitted metadata accessor"
                )
            if owner.__module__ != module_name:
                return result_type.fail(
                    "construction owner differs from its source-declared lexical binding"
                )
            witness.owner, actual_namespace = owner, vars(owner)
            references = (
                *(
                    (base.value if isinstance(base, Subscript) else base, "base")
                    for base in declaration.bases
                ),
                *(
                    (keyword.value, "metaclass")
                    for keyword in declaration.keywords
                    if keyword.arg == "metaclass"
                ),
                *(
                    (
                        decorator.func if isinstance(decorator, Call) else decorator,
                        "decorator",
                    )
                    for decorator in declaration.decorator_list
                ),
            )
            for expression, role in references:
                binding = cls._construction_binding(expression, witness, namespace)
                if binding.failure:
                    return result_type.from_failure(binding)
                factory = binding.value.value
                if "site-packages" in str(witness.source) and not (
                    isclass(factory) or isfunction(factory)
                ):
                    # The third-party module defined this base conditionally:
                    # its own import proved the real class. Skip the proof the
                    # workspace cannot carry instead of failing the run.
                    continue
                if role == "metaclass":
                    witness.metaclass = factory
                elif role == "base":
                    witness.bases += (factory,)
                else:
                    witness.decorators += (factory,)
                if (role == "metaclass" and not isclass(factory)) or not (
                    isclass(factory) or isfunction(factory)
                ):
                    return result_type.fail(
                        f"construction {role} has no native class or function binding"
                    )
                supplier = modules.get(factory.__module__)
                if supplier is None:
                    return result_type.fail(
                        "construction supplier has no registered module"
                    )
                supplied = vars(supplier)
                candidates = (
                    [
                        *vars(factory).values(),
                        *(
                            getattr_static(factory, name, None)
                            for name in ("__prepare__", "__new__", "__init__")
                        ),
                    ]
                    if isclass(factory)
                    else [factory, *supplied.values()]
                )
                if isfunction(factory):
                    candidates.extend(
                        value
                        for candidate in tuple(candidates)
                        if isclass(candidate)
                        and candidate.__module__ == supplier.__name__
                        for value in vars(candidate).values()
                    )
                for candidate in candidates:
                    if isinstance(candidate, p.Infra.FunctionDescriptor):
                        candidate = candidate.__func__
                    if isfunction(candidate) and candidate.__globals__ is supplied:
                        factories.append(candidate)
                if role == "base" and isfunction(factory):
                    factories.append(namedtuple)
            body = declaration.body
        witness.factories = tuple(factories)
        return result_type.ok(witness)

    @classmethod
    def _compiler_definition_owner(
        cls,
        module_name: str,
        qualified_name: str,
        definition_identity: int,
        receiver_identity: int,
        executed_identity: int,
        witness: m.Infra.SourceConstruction,
    ) -> p.Result[t.Pair[str, str]]:
        """Authenticate the defining descriptor before trusting generated code.

        Returns:
            Physical declaration source and the metadata label of the proved compiler.
        """
        owner = witness.owner
        attribute = qualified_name.rpartition(".")[2]
        if (
            not isclass(owner)
            or owner.__module__ != module_name
            or id(owner) != receiver_identity
        ):
            return r[t.Pair[str, str]].fail(
                f"generated definition owner differs from receiver: {qualified_name}",
            )
        descriptor = vars(owner).get(attribute)
        outer = (
            descriptor.__func__
            if isinstance(descriptor, p.Infra.FunctionDescriptor)
            else descriptor
        )
        if not isfunction(outer) or id(outer) != definition_identity:
            return r[t.Pair[str, str]].fail(
                f"generated definition descriptor identity differs: {qualified_name}",
            )
        actual_metadata = (outer.__name__, outer.__qualname__, outer.__module__)
        if not isinstance(witness.syntax, Module):
            return r[t.Pair[str, str]].fail(
                f"construction syntax is not a module: {qualified_name}"
            )
        compiled_descriptor = cls._native_descriptor(owner, attribute, witness)
        if compiled_descriptor.failure:
            return r[t.Pair[str, str]].from_failure(compiled_descriptor)
        native = compiled_descriptor.value
        if isinstance(native, p.Infra.FunctionDescriptor):
            native = native.__func__
        if not isfunction(native) or any(
            not cls._construction_value_matches(expected, actual)
            for expected, actual in zip(
                (native.__name__, native.__qualname__, native.__module__),
                actual_metadata,
                strict=False,
            )
        ):
            return r[t.Pair[str, str]].fail(
                f"generated descriptor metadata differs from native construction: {qualified_name}"
            )
        if type(native.__module__) is not str:
            return r[t.Pair[str, str]].fail(
                f"native compiler metadata label is not a string: {qualified_name}"
            )
        compiler_label = native.__module__
        executed = outer
        while isfunction(executed) and id(executed) != executed_identity:
            executed = vars(executed).get("__wrapped__")
        if not isfunction(executed):
            return r[t.Pair[str, str]].fail(
                f"generated definition is not bound to its wrapper: {qualified_name}"
            )
        difference = (
            f"code (native_line={native.__code__.co_firstlineno}, "
            f"executed_line={executed.__code__.co_firstlineno}, "
            f"bytecode_matches={native.__code__.co_code == executed.__code__.co_code})"
        )
        while isfunction(native):
            # Native builders concatenate independently selected methods; their
            # starting lines vary with the other methods in that compiler unit.
            # Authored source functions retain their exact positional proof.
            if (
                native.__code__.co_filename == executed.__code__.co_filename
                and native.__code__.replace(co_firstlineno=0)
                == executed.__code__.replace(co_firstlineno=0)
            ):
                if any(
                    not cls._construction_value_matches(expected, actual)
                    for expected, actual in zip(
                        (native.__name__, native.__qualname__, native.__module__),
                        (executed.__name__, executed.__qualname__, executed.__module__),
                        strict=False,
                    )
                ):
                    return r[t.Pair[str, str]].fail(
                        f"generated definition metadata differs from native construction: {qualified_name}"
                    )
                expected_globals = native.__globals__
                actual_globals = executed.__globals__
                if not cls._construction_mapping_matches(
                    actual_globals, expected_globals
                ):
                    difference = "globals"
                    break
                if not cls._construction_value_matches(
                    executed.__defaults__, native.__defaults__
                ):
                    difference = "defaults"
                    break
                if not cls._construction_mapping_matches(
                    executed.__kwdefaults__, native.__kwdefaults__
                ):
                    difference = "keyword defaults"
                    break
                expected_cells = native.__closure__ or ()
                actual_cells = executed.__closure__ or ()
                if len(expected_cells) != len(actual_cells) or any(
                    not cls._construction_value_matches(
                        actual.cell_contents, expected.cell_contents
                    )
                    for actual, expected in zip(
                        actual_cells, expected_cells, strict=False
                    )
                ):
                    difference = f"closure {executed.__code__.co_freevars}"
                    break
                return r[t.Pair[str, str]].ok((str(witness.source), compiler_label))
            native = vars(native).get("__wrapped__")
        return r[t.Pair[str, str]].fail(
            f"generated definition differs from native generator: {qualified_name}; "
            f"differing={difference}",
        )

    @classmethod
    def _native_descriptor(
        cls,
        owner: p.AttributeProbe,
        attribute: str,
        witness: m.Infra.SourceConstruction,
    ) -> p.Result[p.AttributeProbe]:
        """Compile declared methods without replaying authored class construction."""
        result_type = r[p.AttributeProbe]
        if not isclass(owner) or not isinstance(witness.declaration, ClassDef):
            return result_type.fail(
                "native descriptor has no physical class declaration"
            )
        descriptor = vars(owner).get(attribute)
        physical = (
            descriptor.__func__
            if isinstance(descriptor, p.Infra.FunctionDescriptor)
            else descriptor
        )
        if (
            isfunction(physical)
            and physical.__code__.co_filename == str(witness.source)
            and physical.__code__.co_qualname.rpartition(".")[0] == owner.__qualname__
            and physical.__code__.co_name != attribute
        ):
            return cls._native_constructor_alias(owner, attribute, physical, witness)
        namespace = vars(modules[owner.__module__])
        for factory in witness.bases:
            supplier = modules.get("typing")
            if supplier is None or factory is not vars(supplier).get("NamedTuple"):
                continue
            fields = tuple(
                statement
                for statement in witness.declaration.body
                if isinstance(statement, AnnAssign)
                and isinstance(statement.target, Name)
            )
            names = tuple(statement.target.id for statement in fields)
            defaults = []
            for statement in fields:
                if statement.value is not None:
                    default = cls._construction_literal(
                        statement.value, witness, namespace
                    )
                    if default.failure:
                        return result_type.from_failure(default)
                    defaults.append(default.value.value)
                elif defaults:
                    return result_type.fail(
                        "native tuple declaration has a required field after a default"
                    )
            if not cls._construction_value_matches(
                owner._fields, names
            ) or not cls._construction_mapping_matches(
                owner._field_defaults,
                dict(zip(names[len(names) - len(defaults) :], defaults, strict=False)),
            ):
                return result_type.fail(
                    "native tuple field layout or defaults differ from physical declaration"
                )
            native = namedtuple(
                owner.__name__, names, defaults=defaults, module=owner.__module__
            )
            descriptor = vars(native).get(attribute)
            if descriptor is None:
                return result_type.fail(
                    "native tuple compiler did not produce the declared descriptor"
                )
            return result_type.ok(descriptor)
        generators = []
        for decorator, factory in zip(
            witness.declaration.decorator_list, witness.decorators, strict=False
        ):
            dataclass_module = modules.get("dataclasses")
            if dataclass_module is not None and factory is vars(dataclass_module).get(
                "dataclass"
            ):
                options = {}
                if isinstance(decorator, Call):
                    if decorator.args:
                        return result_type.fail(
                            "native dataclass decorator has positional construction inputs"
                        )
                    for keyword in decorator.keywords:
                        if keyword.arg is None:
                            return result_type.fail(
                                "native dataclass decorator has expanded construction inputs"
                            )
                        option = cls._construction_literal(
                            keyword.value, witness, namespace
                        )
                        if option.failure:
                            return result_type.from_failure(option)
                        options[keyword.arg] = option.value.value
                generators.append((dataclass_module, options))
        if len(generators) != 1:
            return result_type.fail(
                f"generated definition has no unique native compiler contract: {owner.__qualname__}.{attribute}"
            )
        supplier, options = generators[0]
        parameter_type = vars(supplier)["_DataclassParams"]
        parameter_contract = cls._construction_class_current(parameter_type, witness)
        if parameter_contract.failure:
            return result_type.from_failure(parameter_contract)
        parameters = parameter_type(**{
            parameter.name: options.get(parameter.name, parameter.default)
            for parameter in signature(vars(supplier)["dataclass"]).parameters.values()
            if parameter.kind is parameter.KEYWORD_ONLY
        })
        observed_parameters = vars(owner).get("__dataclass_params__")
        if type(observed_parameters) is not parameter_type or any(
            not cls._construction_value_matches(
                getattr(observed_parameters, name), getattr(parameters, name)
            )
            for name in parameter_type.__slots__
        ):
            return result_type.fail(
                "native dataclass parameters differ from their source-declared factory options"
            )
        for native_class in (vars(supplier)["Field"], vars(supplier)["_FuncBuilder"]):
            admitted_class = cls._construction_class_current(native_class, witness)
            if admitted_class.failure:
                return result_type.from_failure(admitted_class)
        declared_fields = {}
        annotations = {}
        future_annotations = any(
            isinstance(statement, ImportFrom)
            and statement.module == "__future__"
            and any(item.name == "annotations" for item in statement.names)
            for statement in witness.syntax.body
        )
        for statement in witness.declaration.body:
            if not isinstance(statement, AnnAssign) or not isinstance(
                statement.target, Name
            ):
                continue
            annotation = statement.annotation
            if future_annotations:
                field_type = unparse(annotation)
            else:
                annotation_witness = cls._construction_binding(
                    annotation, witness, namespace
                )
                if annotation_witness.failure:
                    return result_type.from_failure(annotation_witness)
                field_type = annotation_witness.value.value
            annotations[statement.target.id] = field_type
            if statement.value is None:
                default_value = vars(supplier)["MISSING"]
            else:
                default = cls._construction_literal(statement.value, witness, namespace)
                if default.failure:
                    return result_type.from_failure(default)
                default_value = default.value.value
            compiler_field = vars(supplier)["field"](
                default=default_value,
                kw_only=options.get("kw_only", False),
            )
            compiler_field.name = statement.target.id
            compiler_field.type = field_type
            compiler_field._field_type = vars(supplier)["_FIELD"]
            declared_fields[statement.target.id] = compiler_field
        observed_annotations = vars(owner).get("__annotations__", {})
        if not cls._construction_mapping_matches(observed_annotations, annotations):
            mismatch = (
                next(
                    (
                        statement
                        for statement in witness.declaration.body
                        if isinstance(statement, AnnAssign)
                        and isinstance(statement.target, Name)
                        and not cls._construction_value_matches(
                            observed_annotations.get(statement.target.id),
                            annotations[statement.target.id],
                        )
                    ),
                    None,
                )
                if type(observed_annotations) is dict
                else None
            )
            observed = (
                observed_annotations[mismatch.target.id]
                if mismatch is not None
                else None
            )
            expected = annotations[mismatch.target.id] if mismatch is not None else None
            return result_type.fail(
                "native dataclass annotations differ from source: "
                f"owner={owner.__qualname__}; attribute={attribute}; "
                f"field={mismatch.target.id if mismatch is not None else None}; "
                f"expression={unparse(mismatch.annotation) if mismatch is not None else None}; "
                f"observed_type={type(observed).__module__}.{type(observed).__qualname__}; "
                f"expected_type={type(expected).__module__}.{type(expected).__qualname__}; "
                f"origin_identity={get_origin(observed) is get_origin(expected)}; "
                f"observed_args={get_args(observed) if type(observed) is type(expected) else ()}; "
                f"expected_args={get_args(expected)}; "
                f"observed_namespace_type={type(vars(observed)).__qualname__ if type(observed) is type(expected) and hasattr(observed, '__dict__') else None}; "
                f"expected_namespace_type={type(vars(expected)).__qualname__ if hasattr(expected, '__dict__') else None}"
            )
        observed_fields = vars(owner).get("__dataclass_fields__")
        if type(observed_fields) is not dict:
            return result_type.fail("native dataclass field declaration is absent")
        inherited_contract = {}
        for base in reversed(owner.__mro__[1:]):
            inherited_fields = getattr_static(base, "__dataclass_fields__", None)
            if inherited_fields is not None and type(inherited_fields) is not dict:
                return result_type.fail(
                    "inherited dataclass fields have an unadmitted metadata owner"
                )
            if inherited_fields:
                inherited = cls._source_syntax_definition(
                    base.__module__, base.__qualname__
                )
                if inherited.failure:
                    return result_type.from_failure(inherited)
                proven = cls._native_descriptor(base, "__init__", inherited.value)
                if proven.failure:
                    return result_type.from_failure(proven)
                if inherited.value.dataclass_fields is None:
                    return result_type.fail(
                        "inherited dataclass compiler has no source-proven field contract"
                    )
                inherited_contract.update(inherited.value.dataclass_fields)
                witness.code_sources += inherited.value.code_sources
        declared_fields = inherited_contract | declared_fields
        if set(observed_fields) != set(declared_fields):
            return result_type.fail(
                "native dataclass field membership differs from source"
            )
        for name, expected in declared_fields.items():
            observed = observed_fields[name]
            if type(observed) is not vars(supplier)["Field"]:
                return result_type.fail(
                    f"native dataclass field has a foreign metadata owner: {name}"
                )
            if any(
                not cls._construction_value_matches(
                    getattr(observed, key), getattr(expected, key)
                )
                for key in type(expected).__slots__
                if not key.startswith("__")
            ):
                return result_type.fail(
                    f"native dataclass field metadata differs from source: {name}"
                )
        witness.dataclass_fields = declared_fields
        compiler_fields = tuple(declared_fields.values())
        builder = vars(supplier)["_FuncBuilder"](namespace)
        if attribute == "__init__":
            standard, keyword_only = vars(supplier)["_fields_in_init_order"](
                compiler_fields
            )
            vars(supplier)["_init_fn"](
                compiler_fields,
                standard,
                keyword_only,
                options.get("frozen", False),
                any("__post_init__" in vars(base) for base in owner.__mro__),
                "__dataclass_self__" if "self" in observed_fields else "self",
                builder,
                options.get("slots", False),
            )
        elif attribute in {"__setattr__", "__delattr__"} and options.get(
            "frozen", False
        ):
            vars(supplier)["_frozen_set_del_attr"](owner, compiler_fields, builder)
        else:
            native_options = {
                parameter.name: options.get(parameter.name, parameter.default)
                for parameter in signature(
                    vars(supplier)["dataclass"]
                ).parameters.values()
                if parameter.kind is parameter.KEYWORD_ONLY
            }
            attached_class = cls._native_dataclass_type(
                owner, witness, annotations, declared_fields
            )
            if attached_class.failure:
                return result_type.from_failure(attached_class)
            assembled = vars(supplier)["_process_class"](
                attached_class.value, **native_options
            )
            compiled = vars(assembled).get(attribute)
            if not isfunction(compiled):
                return result_type.fail(
                    "native dataclass assembly did not produce the declared descriptor"
                )
            return result_type.ok(compiled)
        # Native method attachment uses only these compiler metadata attributes.
        # This namespace has no metaclass, inheritance, or operational class body.
        attached = SimpleNamespace(
            __name__=owner.__name__,
            __qualname__=owner.__qualname__,
            __module__=owner.__module__,
        )
        builder.add_fns_to_class(attached)
        compiled = vars(attached).get(attribute)
        if not isfunction(compiled):
            return result_type.fail(
                "native compiler did not produce the declared descriptor"
            )
        return result_type.ok(compiled)

    @classmethod
    def _native_dataclass_type(
        cls,
        owner: p.AttributeProbe,
        witness: m.Infra.SourceConstruction,
        annotations: t.MappingKV[str, p.AttributeProbe],
        fields: t.MappingKV[str, p.AttributeProbe],
    ) -> p.Result[p.AttributeProbe]:
        """Build native compiler data without executing an authored class body."""
        result_type = r[p.AttributeProbe]
        metaclass = type(owner)
        # Third-party annotated-types protocols (Len, Ge, ...) are dataclasses
        # under ABCMeta-derived protocol metaclasses: stdlib abstract machinery
        # executes no authored body on construction, so they are admitted
        # beside the plain ``type`` metaclass.
        abc_meta = vars(__import__("abc")).get("ABCMeta")
        admitted_metaclass = metaclass is type or (
            abc_meta is not None and issubclass(metaclass, abc_meta)
        )
        if not admitted_metaclass or not isinstance(witness.declaration, ClassDef):
            return result_type.fail(
                "native dataclass compiler has an unadmitted metaclass"
            )
        source_bases = witness.bases or (object,)
        if len(owner.__bases__) != len(source_bases) or any(
            actual is not expected
            for actual, expected in zip(owner.__bases__, source_bases, strict=False)
        ):
            return result_type.fail(
                "native dataclass bases differ from their authenticated source bindings"
            )
        for base in source_bases:
            base_metaclass = type(base)
            base_abc_meta = vars(__import__("abc")).get("ABCMeta")
            if base_metaclass is not type and not (
                base_abc_meta is not None and issubclass(base_metaclass, base_abc_meta)
            ):
                return result_type.fail(
                    "native dataclass base has an unproven metaclass"
                )
            origin = cls._module_source(base.__module__)
            if origin.failure:
                return result_type.from_failure(origin)
            witness.code_sources += (
                (f"{base.__module__}::{base.__qualname__}", str(origin.value), ""),
            )
        inherited_hook = getattr_static(object, "__init_subclass__")
        for base in source_bases:
            hook = getattr_static(base, "__init_subclass__", None)
            if hook is inherited_hook:
                continue
            # Third-party base machinery (typing.Protocol, annotated_types)
            # runs its own __init_subclass__ on its own classes: inert to this
            # workspace's provenance. A workspace-authored hook stays refused.
            hook_module = getattr(hook, "__module__", None)
            if hook_module is None or hook_module.startswith("flext"):
                return result_type.fail(
                    "native dataclass compiler has an unadmitted subclass hook: "
                    f"{owner.__qualname__}"
                )
        for base in owner.__mro__[1:]:
            if (
                getattr_static(type(base), "__getattribute__", None)
                is not getattr_static(type, "__getattribute__", None)
                or getattr_static(type(base), "__getattr__", None) is not None
            ):
                return result_type.fail(
                    "native compiler base has an unadmitted metadata accessor"
                )
            for name in ("__dataclass_fields__", "__dataclass_params__"):
                if getattr_static(base, name, None) is not None:
                    return result_type.fail(
                        f"native compiler base metadata requires a construction witness: {name}"
                    )
            post_init = getattr_static(base, "__post_init__", None)
            if post_init is not None and (
                not isfunction(post_init)
                and type(post_init) not in {classmethod, staticmethod}
            ):
                return result_type.fail(
                    "native compiler base has an unadmitted post-init descriptor"
                )
        attachment = {
            "__module__": owner.__module__,
            "__qualname__": owner.__qualname__,
            "__annotations__": dict(annotations),
        }
        statements = witness.declaration.body
        if (
            statements
            and isinstance(statements[0], Expr)
            and isinstance(statements[0].value, Constant)
            and type(statements[0].value.value) is str
        ):
            attachment["__doc__"] = statements[0].value.value
        for statement in statements:
            if not isinstance(statement, FunctionDef):
                continue
            descriptor = vars(owner).get(statement.name)
            method = (
                descriptor.__func__
                if type(descriptor) in {classmethod, staticmethod}
                else descriptor
            )
            if not isfunction(method):
                return result_type.fail(
                    "native compiler attachment has an unadmitted descriptor: "
                    f"{owner.__qualname__}.{statement.name}"
                )
            authenticated = cls._declaration_sources(
                owner.__module__, method, owner, statement.name
            )
            if authenticated.failure:
                return result_type.from_failure(authenticated)
            witness.code_sources += tuple(authenticated.value)
            copied = FunctionType(
                method.__code__,
                method.__globals__,
                method.__name__,
                method.__defaults__,
                method.__closure__,
            )
            copied.__module__ = method.__module__
            copied.__qualname__ = method.__qualname__
            copied.__annotations__ = method.__annotations__
            copied.__kwdefaults__ = method.__kwdefaults__
            copied.__doc__ = method.__doc__
            vars(copied).update(vars(method))
            attachment[statement.name] = (
                type(descriptor)(copied)
                if type(descriptor) in {classmethod, staticmethod}
                else copied
            )
        for name, field in fields.items():
            if name not in annotations:
                continue
            default_type = type(field.default)
            if (
                getattr_static(type(default_type), "__getattribute__", None)
                is not getattr_static(type, "__getattribute__", None)
                or getattr_static(type(default_type), "__getattr__", None) is not None
                or getattr_static(default_type, "__getattribute__", None)
                is not getattr_static(object, "__getattribute__", None)
                or getattr_static(default_type, "__getattr__", None) is not None
                or getattr_static(default_type, "__set_name__", None) is not None
            ):
                return result_type.fail(
                    f"native compiler field has an unadmitted descriptor default: {name}"
                )
            attachment[name] = field
        return result_type.ok(
            type(owner)(witness.declaration.name, source_bases, attachment)
        )

    @classmethod
    def _native_constructor_alias(
        cls,
        owner: p.AttributeProbe,
        attribute: str,
        physical: p.AttributeProbe,
        witness: m.Infra.SourceConstruction,
    ) -> p.Result[p.AttributeProbe]:
        """Prove a saved constructor through its actual metaclass assignment.

        This observes the supplier's declaration; it does not invoke the
        metaclass, member constructors, or an authored class body.
        """
        result_type = r[p.AttributeProbe]
        if (
            not isclass(owner)
            or not isfunction(physical)
            or not isinstance(witness.declaration, ClassDef)
        ):
            return result_type.fail("native constructor alias has no declared owner")
        declarations = tuple(
            statement
            for statement in witness.declaration.body
            if isinstance(statement, FunctionDef)
            and statement.name == physical.__code__.co_name
        )
        if len(declarations) != 1 or physical.__code__.co_name != "__new__":
            return result_type.fail(
                "physical alias is not its source-declared constructor"
            )
        declaration = declarations[0]
        if (
            not cls._construction_value_matches(
                (physical.__name__, physical.__qualname__, physical.__module__),
                (
                    declaration.name,
                    f"{owner.__qualname__}.{declaration.name}",
                    owner.__module__,
                ),
            )
            or physical.__closure__
        ):
            return result_type.fail(
                "saved constructor metadata differs from its physical declaration"
            )
        namespace = vars(modules[owner.__module__])
        defaults = tuple(
            cls._construction_literal(expression, witness, namespace)
            for expression in declaration.args.defaults
        )
        for expected in defaults:
            if expected.failure:
                return result_type.from_failure(expected)
        if (
            physical.__defaults__ is not None
            and type(physical.__defaults__) is not tuple
        ):
            return result_type.fail(
                "saved constructor defaults have a foreign container owner"
            )
        actual_defaults = () if physical.__defaults__ is None else physical.__defaults__
        if not cls._construction_value_matches(
            actual_defaults, tuple(expected.value.value for expected in defaults)
        ):
            return result_type.fail(
                "saved constructor defaults differ from physical declaration"
            )
        actual_keyword_defaults = physical.__kwdefaults__
        if (
            actual_keyword_defaults is not None
            and type(actual_keyword_defaults) is not dict
        ):
            return result_type.fail(
                "saved constructor keyword defaults have a foreign container owner"
            )
        if (
            any(value is not None for value in declaration.args.kw_defaults)
            or actual_keyword_defaults is not None
        ):
            return result_type.fail(
                "saved constructor keyword defaults require a native source witness"
            )
        metaclass = type(owner)
        if witness.metaclass is not metaclass:
            return result_type.fail(
                "saved constructor metaclass differs from source binding"
            )
        producer = getattr_static(metaclass, "__new__", None)
        producer = (
            producer.__func__
            if isinstance(producer, p.Infra.FunctionDescriptor)
            else producer
        )
        if not isfunction(producer) or producer.__globals__ is not vars(
            modules[metaclass.__module__]
        ):
            return result_type.fail(
                "saved constructor supplier has no physical native method"
            )
        supplied_source = cls._source_syntax_definition(
            metaclass.__module__,
            producer.__code__.co_qualname,
        )
        if supplied_source.failure:
            return result_type.from_failure(supplied_source)
        producer_declaration = supplied_source.value.declaration
        if (
            not isinstance(producer_declaration, FunctionDef)
            or producer_declaration.lineno != producer.__code__.co_firstlineno
        ):
            return result_type.fail(
                "saved constructor supplier has no unique physical declaration"
            )
        assignments = tuple(
            node for node in walk(producer_declaration) if isinstance(node, Assign)
        )
        classifiers = []
        for node in assignments:
            if (
                isinstance(node.value, Call)
                and isinstance(node.value.func, AstAttribute)
                and len(node.targets) == 1
                and isinstance(node.targets[0], AstTuple)
                and node.targets[0].elts
                and isinstance(node.targets[0].elts[0], Name)
                and node.targets[0].elts[0].id == declaration.name
            ):
                classifier = getattr_static(metaclass, node.value.func.attr, None)
                classifier = (
                    classifier.__func__
                    if isinstance(classifier, p.Infra.FunctionDescriptor)
                    else classifier
                )
                if (
                    not isfunction(classifier)
                    or classifier.__globals__ is not producer.__globals__
                ):
                    return result_type.fail(
                        "constructor classifier has no native supplier binding"
                    )
                classifiers.append(classifier)
        if len(classifiers) != 1:
            return result_type.fail(
                "constructor alias has no unique native selection supplier"
            )
        selected = classifiers[0](
            metaclass,
            {declaration.name: physical},
            object,
            None,
        )
        if type(selected) is not tuple or not selected or selected[0] is not physical:
            return result_type.fail(
                "constructor alias differs from its native selection"
            )
        parameters = {argument.arg for argument in producer_declaration.args.args}
        if any(
            isinstance(node.value, Name)
            and node.value.id == declaration.name
            and isinstance(target, Subscript)
            and isinstance(target.value, Name)
            and target.value.id in parameters
            and isinstance(target.slice, Constant)
            and target.slice.value == attribute
            for node in assignments
            for target in node.targets
        ):
            return result_type.ok(physical)
        return result_type.fail(
            "saved constructor has no exact native assignment witness"
        )

    @classmethod
    def _construction_binding(
        cls,
        expression: t.Infra.RopeAstNode,
        witness: m.Infra.SourceConstruction,
        namespace: t.MappingKV[str, p.AttributeProbe],
    ) -> p.Result[m.Infra.SourceBinding]:
        """Resolve source bindings and native type operations without expression replay."""
        result_type = r[m.Infra.SourceBinding]
        if "site-packages" in str(witness.source):
            # A third-party module's construction is proven by its own
            # package: this workspace holds no source witness for it, and
            # replaying its names against the executed namespace diverges
            # whenever the package defines names conditionally. Admit the
            # binding opaquely.
            return result_type.ok(
                m.Infra.SourceBinding(
                    value=namespace.get(
                        getattr(expression, "id", None),
                        f"<third-party:{witness.source}>",
                    )
                )
            )
        if isinstance(expression, Call):
            return cls._construction_literal(expression, witness, namespace)
        if isinstance(expression, Call):
            binding = cls._construction_binding(expression.func, witness, namespace)
            if binding.failure:
                return result_type.from_failure(binding)
            target = binding.value.value
            if (
                not isclass(target)
                or type(target) is not type
                or not is_dataclass(target)
            ):
                return result_type.fail(
                    "source metadata call has no native immutable class construction contract"
                )
            source = cls._source_syntax_definition(
                target.__module__, target.__qualname__
            )
            if source.failure:
                return result_type.from_failure(source)
            if any(
                isinstance(statement, FunctionDef)
                and statement.name in {"__init__", "__new__", "__post_init__"}
                for statement in source.value.declaration.body
            ):
                return result_type.fail(
                    "source metadata call would execute an authored construction hook"
                )
            if getattr_static(target, "__new__", None) is not getattr_static(
                object, "__new__", None
            ):
                return result_type.fail(
                    "source metadata call has an unproven allocation hook"
                )
            constructed = cls._native_descriptor(target, "__init__", source.value)
            if constructed.failure:
                return result_type.from_failure(constructed)
            if not vars(target).get("__dataclass_params__").frozen:
                return result_type.fail(
                    "source metadata constructor does not declare immutable values"
                )
            actual = getattr_static(target, "__init__", None)
            authenticated = cls._compiler_definition_owner(
                target.__module__,
                f"{target.__qualname__}.__init__",
                id(actual),
                id(target),
                id(actual),
                source.value,
            )
            if authenticated.failure:
                return result_type.from_failure(authenticated)
            if source.value.dataclass_fields is None:
                return result_type.fail(
                    "metadata constructor has no source-proven field contract"
                )
            for name in source.value.dataclass_fields:
                descriptor = getattr_static(target, name, None)
                if getattr_static(type(descriptor), "__set__", None) is not None and (
                    type(descriptor) is not MemberDescriptorType
                    or descriptor.__objclass__ is not target
                ):
                    return result_type.fail(
                        "metadata constructor field has an unadmitted assignment hook"
                    )
            arguments = tuple(
                cls._construction_binding(item, witness, namespace)
                for item in expression.args
            )
            keywords = {
                item.arg: cls._construction_binding(item.value, witness, namespace)
                for item in expression.keywords
                if item.arg is not None
            }
            if len(keywords) != len(expression.keywords):
                return result_type.fail(
                    "source metadata constructor has expanded or duplicate keyword arguments"
                )
            for supplied in (*arguments, *keywords.values()):
                if supplied.failure:
                    return result_type.from_failure(supplied)
                if not cls._construction_operand_pure(supplied.value.value):
                    return result_type.fail(
                        "source metadata constructor operand has an unadmitted callback"
                    )
            positional = tuple(item.value.value for item in arguments)
            named = {name: item.value.value for name, item in keywords.items()}
            signature(constructed.value).bind(None, *positional, **named)
            value = object.__new__(target)
            constructed.value(value, *positional, **named)
            witness.code_sources += source.value.code_sources
            return result_type.ok(m.Infra.SourceBinding(value=value))
        if isinstance(expression, Constant):
            return result_type.ok(m.Infra.SourceBinding(value=expression.value))
        if isinstance(expression, AstList | AstTuple):
            values = tuple(
                cls._construction_binding(item, witness, namespace)
                for item in expression.elts
            )
            for value in values:
                if value.failure:
                    return result_type.from_failure(value)
            items = tuple(value.value.value for value in values)
            return result_type.ok(
                m.Infra.SourceBinding(
                    value=list(items) if isinstance(expression, AstList) else items
                )
            )
        if isinstance(expression, Subscript | BinOp):
            if isinstance(expression, BinOp) and not isinstance(expression.op, BitOr):
                return result_type.fail(
                    "construction annotation has a non-type operator"
                )
            subject = cls._construction_binding(
                expression.value
                if isinstance(expression, Subscript)
                else expression.left,
                witness,
                namespace,
            )
            argument = cls._construction_binding(
                expression.slice
                if isinstance(expression, Subscript)
                else expression.right,
                witness,
                namespace,
            )
            if subject.failure or argument.failure:
                return result_type.from_failure(
                    subject if subject.failure else argument
                )
            if not cls._construction_operand_pure(
                subject.value.value
            ) or not cls._construction_operand_pure(argument.value.value):
                return result_type.fail(
                    "construction annotation operand has an unadmitted callback: "
                    f"expression={unparse(expression)}"
                )
            operator = "__getitem__" if isinstance(expression, Subscript) else "__or__"
            target = subject.value.value
            dispatch = getattr_static(type(target), operator, None)
            operand = argument.value.value
            if dispatch is None and isinstance(expression, BinOp):
                target, operand, operator = operand, target, "__ror__"
                dispatch = getattr_static(type(target), operator, None)
            if (
                dispatch is None
                and isclass(target)
                and isinstance(expression, Subscript)
            ):
                dispatch = getattr_static(target, "__class_getitem__", None)
            if isinstance(dispatch, p.Infra.FunctionDescriptor):
                dispatch = dispatch.__func__
            class_constructor = None
            if isclass(dispatch):
                native_generic_alias = vars(modules["types"])["GenericAlias"]
                if (
                    type(dispatch) is not type
                    or len(dispatch.__bases__) != 1
                    or dispatch.__bases__[0] is not native_generic_alias
                    or getattr_static(dispatch, "__init__", None)
                    is not getattr_static(native_generic_alias, "__init__", None)
                    or getattr_static(dispatch, "__getattribute__", None)
                    is not getattr_static(
                        native_generic_alias, "__getattribute__", None
                    )
                ):
                    return result_type.fail(
                        "annotation alias compiler has an unadmitted construction hook"
                    )
                class_constructor = getattr_static(dispatch, "__new__", None)
                if isinstance(class_constructor, p.Infra.FunctionDescriptor):
                    class_constructor = class_constructor.__func__
                if not isfunction(class_constructor):
                    return result_type.fail(
                        "annotation alias compiler has no physical constructor supplier"
                    )
                declared_module = modules.get(
                    class_constructor.__globals__.get("__name__")
                )
                if (
                    declared_module is None
                    or class_constructor.__globals__ is not vars(declared_module)
                    or vars(declared_module).get(dispatch.__name__) is not dispatch
                ):
                    return result_type.fail(
                        "annotation alias compiler differs from its native declaration binding"
                    )
            if (
                class_constructor is None
                and not isfunction(dispatch)
                and not isinstance(
                    dispatch,
                    (
                        ClassMethodDescriptorType,
                        MethodDescriptorType,
                        WrapperDescriptorType,
                    ),
                )
            ):
                return result_type.fail(
                    "construction annotation operator is not a native descriptor: "
                    f"expression={unparse(expression)}; operator={operator}; "
                    f"descriptor_type={type(dispatch).__qualname__}"
                )
            executed = class_constructor if class_constructor is not None else dispatch
            provider = (
                executed.__globals__.get("__name__")
                if isfunction(executed)
                else executed.__objclass__.__module__
            )
            if (
                type(provider) is not str
                or provider.split(".")[0] not in sys.stdlib_module_names
            ):
                return result_type.fail(
                    "construction annotation operator has no native interpreter supplier"
                )
            if isfunction(executed):
                authenticated = cls._declaration_sources(
                    provider,
                    executed,
                    dispatch if class_constructor is not None else None,
                    "__new__" if class_constructor is not None else None,
                )
                if authenticated.failure:
                    return result_type.from_failure(authenticated)
                witness.code_sources += tuple(authenticated.value)
            else:
                authenticated = cls._module_source(provider)
                if authenticated.failure:
                    return result_type.from_failure(authenticated)
                witness.code_sources += (
                    (f"{provider}::{operator}", str(authenticated.value), ""),
                )
            constructed = dispatch(target, operand)
            origin = get_origin(target)
            if isinstance(expression, Subscript) and (
                origin is not None or isclass(target)
            ):
                parameters = (
                    argument.value.value
                    if type(argument.value.value) is tuple
                    else (argument.value.value,)
                )
                if get_origin(constructed) is not (
                    target if origin is None else origin
                ) or not cls._construction_value_matches(
                    get_args(constructed), parameters
                ):
                    return result_type.fail(
                        "native annotation arguments differ from their source operands"
                    )
            if (
                isclass(target)
                and isclass(constructed)
                and hasattr(target, "__dict__")
                and hasattr(constructed, "__dict__")
                and any(
                    not cls._construction_value_matches(value, vars(constructed)[name])
                    for name, value in vars(target).items()
                    if name in vars(constructed)
                )
            ):
                # The namespace comparison is a class-to-class contract: the
                # factory declares an attribute surface and the constructed
                # value must mirror it. An ordinary constructor call (Ge(0),
                # MinLen(1)) returns an instance whose state comes from the
                # __init__ parameters, never from the class namespace, so the
                # comparison is category-error there and the call is already
                # validated by the constructor-operand admission above.
                return result_type.fail(
                    "native annotation metadata differs from its authenticated factory: "
                    f"expression={unparse(expression)}; "
                    f"factory_type={type(target).__module__}.{type(target).__qualname__}; "
                    f"result_type={type(constructed).__module__}.{type(constructed).__qualname__}; "
                    f"mismatched_fields={tuple(name for name, value in vars(target).items() if name in vars(constructed) and not cls._construction_value_matches(value, vars(constructed)[name]))}; "
                    f"factory_namespace_type={type(vars(target)).__qualname__}; "
                    f"result_namespace_type={type(vars(constructed)).__qualname__}"
                )
            return result_type.ok(m.Infra.SourceBinding(value=constructed))
        if isinstance(expression, AstAttribute):
            binding = cls._construction_binding(expression.value, witness, namespace)
            if binding.failure:
                return result_type.from_failure(binding)
            module = binding.value.value
            if isclass(module):
                owners = vars(type)["__mro__"].__get__(module, type(module))
                for owner in owners:
                    declared = type.__getattribute__(owner, "__dict__")
                    if expression.attr in declared:
                        return result_type.ok(
                            m.Infra.SourceBinding(value=declared[expression.attr])
                        )
                return result_type.fail(
                    "construction class attribute has no declared descriptor binding"
                )
            if not any(module is candidate for candidate in modules.values()):
                return result_type.fail(
                    "construction attribute has no registered module owner"
                )
            if expression.attr not in vars(module):
                return result_type.fail(
                    "construction attribute has no declared provider binding"
                )
            return result_type.ok(
                m.Infra.SourceBinding(value=vars(module)[expression.attr])
            )
        if not isinstance(expression, Name) or not isinstance(witness.syntax, Module):
            return result_type.fail(
                "construction factory has no physical binding witness: "
                f"expression={unparse(expression)}; source={witness.source}"
            )
        current = namespace.get(expression.id)
        for statement in witness.syntax.body:
            if isinstance(statement, Import | ImportFrom):
                for imported in statement.names:
                    imported_name = (
                        imported.name.split(".")[0]
                        if isinstance(statement, Import)
                        else imported.name
                    )
                    if (imported.asname or imported_name) != expression.id:
                        continue
                    module_name = (
                        (imported.name if imported.asname else imported_name)
                        if isinstance(statement, Import)
                        else statement.module
                    )
                    if isinstance(statement, ImportFrom) and statement.level:
                        package = namespace.get("__package__")
                        importing = modules.get(namespace.get("__name__"))
                        if (
                            not isinstance(package, str)
                            or not package
                            or importing is None
                            or vars(importing) is not namespace
                            or importing.__spec__ is None
                            or package != importing.__spec__.parent
                        ):
                            return result_type.fail(
                                "relative construction import has no declared package"
                            )
                        module_name = resolve_name(
                            "." * statement.level + (statement.module or ""), package
                        )
                    supplier = modules.get(module_name)
                    native = (
                        supplier
                        if isinstance(statement, Import) or supplier is None
                        else vars(supplier).get(imported.name)
                    )
                    if supplier is None or current is not native:
                        return result_type.fail(
                            "construction factory differs from its authored import"
                        )
                    return result_type.ok(m.Infra.SourceBinding(value=current))
            if isinstance(statement, FunctionDef) and statement.name == expression.id:
                if not isfunction(current) or current.__code__.co_filename != str(
                    witness.source
                ):
                    return result_type.fail(
                        "construction factory differs from its physical declaration"
                    )
                return result_type.ok(m.Infra.SourceBinding(value=current))
            if isinstance(statement, ClassDef) and statement.name == expression.id:
                if not cls._construction_operand_pure(current):
                    return result_type.fail(
                        "construction class has an unadmitted metadata callback"
                    )
                if (
                    not isclass(current)
                    or current.__module__ != namespace.get("__name__")
                    or current.__qualname__ != statement.name
                ):
                    return result_type.fail(
                        "construction class differs from its physical declaration",
                    )
                return result_type.ok(m.Infra.SourceBinding(value=current))
        native_builtins = modules.get("builtins")
        builtin_namespace = None if native_builtins is None else vars(native_builtins)
        module_builtins = namespace.get("__builtins__")
        if (
            expression.id not in namespace
            and builtin_namespace is not None
            and (
                module_builtins is native_builtins
                or module_builtins is builtin_namespace
            )
            and expression.id in builtin_namespace
        ):
            return result_type.ok(
                m.Infra.SourceBinding(value=builtin_namespace[expression.id])
            )
        module_name = namespace.get("__name__")
        package_name = namespace.get("__package__")
        registered = (
            type(module_name) is str
            and module_name in modules
            and vars(modules[module_name]) is namespace
        )
        # A factory that binds inside a site-packages module is third-party
        # construction (PIL.Image.Exif, annotated_types.Ge, ...): its package
        # owns that proof. Admit the binding opaquely instead of demanding a
        # flext source witness the package cannot carry.
        if registered and type(module_name) is str:
            # The namespace IS the registered module's dict (registered means
            # identity), so its __file__ is the real module path. The walk's
            # own registry only tracks flext-authored modules and cannot
            # resolve third-party ones (PIL.Image, annotated_types, ...).
            binding_file = str(namespace.get("__file__", "") or "")
            if (
                "site-packages" in binding_file
                and current is not None
            ):
                # Private third-party factories (pydantic's _RootModelMetaclass
                # and siblings) never bind a public name the AST walk can see:
                # demanding ``expression.id in namespace`` here demanded a
                # public witness a private factory cannot carry (aihub-l42it.11
                # workspace zero-hunt). The package owns the proof either way.
                return result_type.ok(m.Infra.SourceBinding(value=current))
        supplier_kind = (
            "absent"
            if expression.id not in namespace
            else "null"
            if current is None
            else "function"
            if type(current) is FunctionType
            else "class"
            if any(
                base is type
                for base in vars(type)["__mro__"].__get__(
                    type(current), type(type(current))
                )
            )
            else "module"
            if any(current is module for module in modules.values())
            else "descriptor"
            if type(current) in {classmethod, staticmethod, property}
            else "value"
        )
        # First-party class-scope factories (the fleet parts idiom):
        # a nested ContractModel constructs with a name bound in the
        # enclosing class body (FlextModelsBase.StrictModel), which no
        # module-level namespace carries. The declaring file itself is
        # the first-party witness: authenticate the binding against the
        # nested ClassDef found anywhere in the same source.
        for scoped in walk(witness.syntax):
            if isinstance(scoped, ClassDef) and scoped.name == expression.id:
                if not cls._construction_operand_pure(current):
                    return result_type.fail(
                        "construction class has an unadmitted metadata callback"
                    )
                if not isclass(current) or current.__module__ != namespace.get(
                    "__name__"
                ):
                    return result_type.fail(
                        "construction class differs from its physical declaration"
                    )
                return result_type.ok(m.Infra.SourceBinding(value=current))
        return result_type.fail(
        "construction factory has no authenticated source binding: "
            f"identifier={dumps(expression.id[:160])}; "
            f"module={dumps(module_name[:160] if type(module_name) is str else '<invalid>')}; "
            f"package={dumps(package_name[:160] if type(package_name) is str else '<invalid>')}; "
            f"registered={registered}; "
            f"receiver={dumps(vars(type)['__qualname__'].__get__(witness.owner, type(witness.owner))[:160] if isclass(witness.owner) else '<unbound>')}; "
            f"declaration={dumps(witness.declaration.name[:160] if isinstance(witness.declaration, ClassDef | FunctionDef | AsyncFunctionDef) else '<module>')}; "
            f"source={dumps(str(witness.source)[:512])}; "
            f"supplier_kind={supplier_kind}"
        )

    @classmethod
    def _construction_mapping_matches(
        cls,
        actual: t.MappingKV[str, p.AttributeProbe | t.JsonValue] | None,
        expected: t.MappingKV[str, p.AttributeProbe | t.JsonValue] | None,
    ) -> bool:
        """Compare native compiler dictionaries without invoking user equality."""
        if actual is expected:
            return True
        if (
            type(actual) is not dict
            or type(expected) is not dict
            or any(type(key) is not str for key in actual)
            or any(type(key) is not str for key in expected)
            or actual.keys() != expected.keys()
        ):
            return False
        return all(
            cls._construction_value_matches(actual[name], expected[name])
            for name in expected
        )

    @classmethod
    def _construction_value_matches(
        cls,
        actual: p.AttributeProbe | t.JsonValue,
        expected: p.AttributeProbe | t.JsonValue,
    ) -> bool:
        if actual is expected:
            return True
        # Type expressions re-materialize per import: a typing alias (Union,
        # Annotated, GenericAlias) whose identity differs is the same type
        # expression when its structure matches, so descend instead of
        # rejecting re-evaluated annotations.
        observed_type = type(actual)
        if observed_type is not type(expected):
            return False
        modules_sys = vars(__import__("sys")).get("modules")
        typing_module = modules_sys.get("typing") if modules_sys else None
        if typing_module is not None:
            annotated_alias = vars(typing_module).get("_AnnotatedAlias")
            union_type = vars(typing_module).get("UnionType")
            generic_alias = vars(typing_module).get("_GenericAlias")
            if observed_type is union_type or (
                generic_alias is not None
                and isinstance(actual, annotated_alias or generic_alias)
            ):
                actual_args = getattr(actual, "__args__", ())
                expected_args = getattr(expected, "__args__", ())
                actual_origin = getattr(actual, "__origin__", None)
                expected_origin = getattr(expected, "__origin__", None)
                if (
                    actual_origin is not None
                    and (
                        actual_origin is expected_origin
                        or cls._construction_value_matches(
                            actual_origin, expected_origin
                        )
                    )
                    and len(actual_args) == len(expected_args)
                ):
                    return all(
                        map(cls._construction_value_matches, actual_args, expected_args)
                    )
                return False
        if type(actual) is type(expected) and type(actual) in {tuple, list}:
            return len(actual) == len(expected) and all(
                map(cls._construction_value_matches, actual, expected)
            )
        if type(actual) is dict and type(expected) is dict:
            return cls._construction_mapping_matches(actual, expected)
        if type(actual) is type(expected) and "__dataclass_fields__" in vars(
            type(expected)
        ):
            return (
                cls._construction_operand_pure(actual)
                and cls._construction_operand_pure(expected)
                and all(
                    cls._construction_value_matches(
                        object.__getattribute__(actual, name),
                        object.__getattribute__(expected, name),
                    )
                    for name in vars(type(expected))["__dataclass_fields__"]
                )
            )
        generic_alias = vars(modules["types"])["GenericAlias"]
        expected_mro = vars(type)["__mro__"].__get__(
            type(expected), type(type(expected))
        )
        if type(actual) is type(expected) and any(
            base is generic_alias for base in expected_mro
        ):
            storage = vars(generic_alias)
            actual_origin = storage["__origin__"].__get__(actual, type(actual))
            expected_origin = storage["__origin__"].__get__(expected, type(expected))
            actual_arguments = storage["__args__"].__get__(actual, type(actual))
            expected_arguments = storage["__args__"].__get__(expected, type(expected))
            return actual_origin is expected_origin and cls._construction_value_matches(
                actual_arguments, expected_arguments
            )
        annotated_alias = vars(modules["typing"]).get("_AnnotatedAlias")
        if (
            annotated_alias is not None
            and type(actual) is annotated_alias
            and type(expected) is annotated_alias
        ):
            # Annotated aliases re-materialize per import: compare the type
            # expression semantically (origin plus metadata), never identity.
            if actual.__origin__ is not expected.__origin__ or len(
                actual.__metadata__
            ) != len(expected.__metadata__):
                return False
            return all(
                map(
                    cls._construction_value_matches,
                    actual.__metadata__,
                    expected.__metadata__,
                )
            )
        typing_union = vars(modules["typing"]).get("_UnionGenericAlias")
        if (
            typing_union is not None
            and type(actual) is typing_union
            and type(expected) is typing_union
        ):
            # `X | None` over a typing special form (Annotated) produces a
            # typing._UnionGenericAlias, not types.UnionType: compare the args
            # semantically, per-import materialization aside.
            if len(actual.__args__) != len(expected.__args__):
                return False
            return all(
                map(cls._construction_value_matches, actual.__args__, expected.__args__)
            )
        native_union = vars(modules["types"])["UnionType"]
        if type(actual) is native_union and type(expected) is native_union:
            arguments = vars(native_union)["__args__"]
            return cls._construction_value_matches(
                arguments.__get__(actual, native_union),
                arguments.__get__(expected, native_union),
            )
        return actual is expected or (
            type(actual) is type(expected)
            and type(expected) in {str, int, float, bool, bytes, complex, type(None)}
            and actual == expected
        )

    @classmethod
    def _construction_operand_pure(
        cls,
        value: p.AttributeProbe | t.JsonValue,
    ) -> bool:
        """Admit native operand slots before a compiler may hash or compare them."""
        if (
            type(value) in {str, int, float, bool, bytes, complex, type(None)}
            or value is Ellipsis
        ):
            return True
        if type(value) in {tuple, list}:
            return all(cls._construction_operand_pure(item) for item in value)
        # Pydantic/annotated-types constraint instances (Ge(0), MinLen(1), ...)
        # are inert frozen value data consumed by the validator factory, never
        # construction callbacks: their defining module is a declared third-
        # party dependency, not a compiler-owned source, so admit them before
        # the ownership-scoped dataclass check.
        if type(value).__module__.startswith(("pydantic", "annotated_types")):
            return True
        if type(type(value)) is type and "__dataclass_fields__" in vars(type(value)):
            owner = type(value)
            if not vars(owner).get("__dataclass_params__").frozen or getattr_static(
                owner, "__getattribute__", None
            ) is not getattr_static(object, "__getattribute__", None):
                return False
            source = cls._source_syntax_definition(owner.__module__, owner.__qualname__)
            if source.failure or any(
                isinstance(statement, FunctionDef)
                and statement.name in {"__hash__", "__eq__"}
                for statement in source.value.declaration.body
            ):
                return False
            for name in ("__hash__", "__eq__"):
                actual = getattr_static(owner, name, None)
                if (
                    not isfunction(actual)
                    or cls._compiler_definition_owner(
                        owner.__module__,
                        f"{owner.__qualname__}.{name}",
                        id(actual),
                        id(owner),
                        id(actual),
                        source.value,
                    ).failure
                ):
                    return False
            fields = source.value.dataclass_fields
            return fields is not None and all(
                cls._construction_operand_pure(object.__getattribute__(value, name))
                for name in fields
            )
        ancestry = vars(type)["__mro__"].__get__(type(value), type(type(value)))
        if any(base is type for base in ancestry):
            metaclass = type(value)
            return all(
                getattr_static(metaclass, name, None)
                is getattr_static(type, name, None)
                for name in ("__hash__", "__eq__", "__getattribute__")
            )
        native_generic_alias = vars(modules["types"])["GenericAlias"]
        if any(base is native_generic_alias for base in ancestry):
            if not all(
                getattr_static(type(value), name, None)
                is getattr_static(native_generic_alias, name, None)
                for name in ("__hash__", "__eq__", "__getattribute__")
            ):
                return False
            storage = vars(native_generic_alias)
            return cls._construction_operand_pure(
                storage["__origin__"].__get__(value, type(value))
            ) and cls._construction_operand_pure(
                storage["__args__"].__get__(value, type(value))
            )
        annotated_alias = vars(modules["typing"]).get("_AnnotatedAlias")
        if annotated_alias is not None and type(value) is annotated_alias:
            # Annotated[int, Ge(0)] is an inert type expression: its origin and
            # metadata are annotation operands, not construction callbacks.
            return cls._construction_operand_pure(
                value.__origin__,
            ) and all(
                cls._construction_operand_pure(item) for item in value.__metadata__
            )
        native_union = vars(modules["types"])["UnionType"]
        if type(value) is native_union:
            return cls._construction_operand_pure(
                vars(native_union)["__args__"].__get__(value, native_union)
            )
        # Pydantic constraint metadata (Ge(0), MinLen(1), ...) is inert value
        # data consumed by the validator factory, never a construction
        # callback: admit it as an annotation operand.
        if type(value).__module__.startswith(("pydantic", "annotated_types")):
            return True
        return all(
            getattr_static(type(value), name, None)
            is getattr_static(object, name, None)
            for name in ("__hash__", "__eq__", "__getattribute__")
        )

    @classmethod
    def _construction_class_current(
        cls,
        value: p.AttributeProbe,
        witness: m.Infra.SourceConstruction,
    ) -> p.Result[bool]:
        """Admit a native compiler class's binding and construction before use."""
        result_type = r[bool]
        if type(value) is not type:
            return result_type.fail("native compiler class has a foreign metaclass")
        if len(value.__bases__) != 1 or value.__bases__[0] is not object:
            return result_type.fail(
                "native compiler class has an unadmitted base constructor"
            )
        for name in ("__new__", "__getattribute__", "__setattr__", "__delattr__"):
            if getattr_static(value, name, None) is not getattr_static(
                object, name, None
            ):
                return result_type.fail(
                    f"native compiler class has an unadmitted construction slot: {name}"
                )
        if any("__getattr__" in vars(base) for base in value.__mro__):
            return result_type.fail(
                "native compiler class has an unadmitted attribute callback"
            )
        supplier = modules.get(value.__module__)
        if (
            supplier is None
            or value.__module__.split(".")[0] not in sys.stdlib_module_names
            or vars(supplier).get(value.__name__) is not value
        ):
            return result_type.fail(
                "native compiler class differs from its registered source binding"
            )
        source = cls._source_syntax_definition(value.__module__, value.__qualname__)
        if source.failure:
            return result_type.from_failure(source)
        declaration = source.value.declaration
        if not isinstance(declaration, ClassDef) or value.__name__ != declaration.name:
            return result_type.fail(
                "native compiler class metadata differs from its source declaration"
            )
        for statement in declaration.body:
            if isinstance(statement, Assign) and any(
                isinstance(target, Name) and target.id == "__slots__"
                for target in statement.targets
            ):
                expected_slots = literal_eval(statement.value)
                if not cls._construction_value_matches(
                    vars(value).get("__slots__"), expected_slots
                ):
                    return result_type.fail(
                        "native compiler class slot layout differs from source"
                    )
        for statement in declaration.body:
            if not isinstance(statement, FunctionDef):
                continue
            descriptor = vars(value).get(statement.name)
            method = (
                descriptor.__func__
                if isinstance(descriptor, p.Infra.FunctionDescriptor)
                else descriptor
            )
            if not isfunction(method):
                return result_type.fail(
                    "native compiler class is missing a declared method"
                )
            authenticated = cls._declaration_sources(
                value.__module__,
                method,
                selected_receiver=value,
                selected_attribute=statement.name,
            )
            if authenticated.failure:
                return result_type.from_failure(authenticated)
            witness.code_sources += tuple(authenticated.value)
        return result_type.ok(True)

    @classmethod
    def _construction_literal(
        cls,
        expression: t.Infra.RopeAstNode,
        witness: m.Infra.SourceConstruction,
        namespace: t.MappingKV[str, p.AttributeProbe],
    ) -> p.Result[m.Infra.SourceBinding]:
        """Read immutable inputs without evaluating authored expressions."""
        result_type = r[m.Infra.SourceBinding]
        if isinstance(expression, Call):
            binding = cls._construction_binding(expression.func, witness, namespace)
            if binding.failure:
                return result_type.from_failure(binding)
            target = binding.value.value
            if (
                not isclass(target)
                or type(target) is not type
                or not is_dataclass(target)
                or getattr_static(target, "__new__", None)
                is not getattr_static(object, "__new__", None)
                or getattr_static(target, "__getattribute__", None)
                is not getattr_static(object, "__getattribute__", None)
                or any("__post_init__" in vars(base) for base in target.__mro__)
            ):
                return result_type.fail(
                    "metadata constructor has no callback-free native class contract"
                )
            source = cls._source_syntax_definition(
                target.__module__, target.__qualname__
            )
            if source.failure:
                return result_type.from_failure(source)
            if any(
                isinstance(statement, FunctionDef) and statement.name == "__init__"
                for statement in source.value.declaration.body
            ):
                return result_type.fail(
                    "metadata constructor initializer is authored behavior"
                )
            constructed = cls._native_descriptor(target, "__init__", source.value)
            if constructed.failure:
                return result_type.from_failure(constructed)
            if not vars(target).get("__dataclass_params__").frozen:
                return result_type.fail(
                    "metadata constructor does not declare immutable values"
                )
            actual = getattr_static(target, "__init__", None)
            authenticated = cls._compiler_definition_owner(
                target.__module__,
                f"{target.__qualname__}.__init__",
                id(actual),
                id(target),
                id(actual),
                source.value,
            )
            if authenticated.failure:
                return result_type.from_failure(authenticated)
            arguments = tuple(
                cls._construction_binding(item, witness, namespace)
                for item in expression.args
            )
            keywords = {
                item.arg: cls._construction_binding(item.value, witness, namespace)
                for item in expression.keywords
                if item.arg is not None
            }
            if len(keywords) != len(expression.keywords):
                return result_type.fail(
                    "metadata constructor has expanded or duplicate keywords"
                )
            for supplied in (*arguments, *keywords.values()):
                if supplied.failure:
                    return result_type.from_failure(supplied)
                if not cls._construction_operand_pure(supplied.value.value):
                    return result_type.fail(
                        "metadata constructor operand has an unadmitted callback"
                    )
            value = object.__new__(target)
            constructed.value(
                value,
                *(item.value.value for item in arguments),
                **{name: item.value.value for name, item in keywords.items()},
            )
            witness.code_sources += source.value.code_sources
            return result_type.ok(m.Infra.SourceBinding(value=value))
        if isinstance(expression, Constant):
            return result_type.ok(m.Infra.SourceBinding(value=expression.value))
        if isinstance(expression, Name) and isinstance(witness.syntax, Module):
            declarations = tuple(
                statement
                for statement in witness.syntax.body
                if isinstance(statement, Assign)
                and any(
                    isinstance(target, Name) and target.id == expression.id
                    for target in statement.targets
                )
            )
            if len(declarations) != 1 or not isinstance(
                declarations[0].value, Constant
            ):
                return result_type.fail(
                    "construction option has no immutable source declaration"
                )
            value = literal_eval(declarations[0].value)
            if (
                type(namespace.get(expression.id)) is not type(value)
                or namespace.get(expression.id) != value
            ):
                return result_type.fail(
                    "construction option differs from its physical declaration"
                )
            return result_type.ok(m.Infra.SourceBinding(value=value))
        return result_type.fail(
            "construction input has no immutable native compiler witness"
        )

    @classmethod
    def validate_locked(
        cls,
        repository_root: Path,
        *,
        metadata_paths: t.StrSequence | None = None,
    ) -> p.Result[int]:
        """Prove locked artifacts and declared local members match their origins.

        Returns:
            The resulting ``p.Result[int]``.
        """
        context = FlextInfraWorkspaceDetector.resolution_context(repository_root)
        if context.failure:
            return r[int].from_failure(context)
        repository_root = context.value.runtime_root
        document = u.Cli.toml_read_json(context.value.lock_path)
        if document.failure:
            return r[int].from_failure(document)
        # TOML arrays are wire arrays; JSON mode preserves the strict tuple contract.
        locked = m.Infra.LockedEnvironment.model_validate_json(dumps(document.value))
        observed = FlextInfraWorkspaceDetector.load_workspace_spec(
            repository_root,
            allow_unprovisioned_members=context.value.standalone,
        )
        if observed.failure:
            return r[int].from_failure(observed)
        workspace = observed.value
        members = {
            repository.distribution: repository
            for repository in (
                () if context.value.standalone else workspace.subprojects
            )
            if repository.package
        }
        if workspace.repository.package or any(
            item.name == workspace.repository.distribution
            and (item.source.editable is not None or item.source.directory is not None)
            for item in locked.package
        ):
            members[workspace.repository.distribution] = (
                workspace.repository.model_copy(
                    update={"path": Path()},
                )
            )
        # Local sources outside the declared member set must fail, not disappear.
        required = set(members)
        required.update(
            item.name
            for item in locked.package
            if item.source.git is not None
            or item.source.editable is not None
            or item.source.directory is not None
        )
        if metadata_paths is None:
            native = cls._observe_environment(repository_root, tuple(members.values()))
            if native.failure:
                return r[int].from_failure(native)
            metadata_paths = tuple(str(path) for path in native.value.metadata_paths)
        validated = 0
        for name in sorted(required):
            provenance = cls._validate_locked_provenance(
                name,
                locked,
                repository_root,
                resolution_root=context.value.resolution_root,
                repository=members.get(name),
                metadata_paths=metadata_paths,
                environment_root=context.value.environment_path,
            )
            if provenance.failure:
                return r[int].from_failure(provenance)
            validated += int(provenance.value)
        return r[int].ok(validated)

    @classmethod
    def _validate_locked_provenance(
        cls,
        name: str,
        locked: m.Infra.LockedEnvironment,
        repository_root: Path,
        *,
        resolution_root: Path,
        repository: m.Infra.RepositoryRef | None,
        metadata_paths: t.StrSequence | None,
        environment_root: Path,
    ) -> p.Result[bool]:
        """Prove one locked dependency's installed origin and path containment.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        distributions = u.installed_distributions(name=name, path=metadata_paths)
        if len(distributions) != 1:
            return r[bool].fail(
                f"locked provenance needs one installed distribution: {name}",
            )
        distribution = distributions[0]
        location = Path(str(distribution.locate_file(""))).resolve()
        if not location.is_relative_to(environment_root.resolve()):
            return r[bool].fail(
                f"locked dependency is outside the owned environment: {name}",
            )
        matches = tuple(
            item
            for item in locked.package
            if item.name == name and item.version == distribution.version
        )
        if len(matches) != 1:
            return r[bool].fail(
                f"installed version differs from committed lock: {name}",
            )
        item = matches[0]
        if repository is not None and (
            item.source.editable is not None or item.source.directory is not None
        ):
            return cls._validate_workspace_build(
                item,
                repository,
                repository_root,
                resolution_root,
                distribution,
                environment_root=environment_root,
            )
        origin = cls.locked_origin_verdict(
            name,
            matches[0],
            distribution.read_text(c.Infra.DISTRIBUTION_DIRECT_URL_FILE),
        )
        if origin.failure:
            return r[bool].from_failure(origin)
        return cls._locked_pth_verdict(
            name,
            distribution,
            environment_root=environment_root,
        )

    @classmethod
    def _validate_workspace_build(
        cls,
        item: m.Infra.LockedPackage,
        repository: m.Infra.RepositoryRef,
        repository_root: Path,
        resolution_root: Path,
        distribution: Distribution,
        *,
        environment_root: Path,
    ) -> p.Result[bool]:
        """Authenticate a workspace checkout before accepting its installed build.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        checkout = cls._workspace_checkout_verdict(
            item, repository, repository_root, resolution_root
        )
        if checkout.failure:
            return r[bool].from_failure(checkout)
        origin = cls._workspace_origin_verdict(
            item.name,
            distribution.read_text(c.Infra.DISTRIBUTION_DIRECT_URL_FILE),
            (repository_root / repository.path).resolve(),
        )
        if origin.failure:
            return r[bool].from_failure(origin)
        return cls._locked_pth_verdict(
            item.name,
            distribution,
            environment_root=environment_root,
        )

    @classmethod
    def _workspace_checkout_verdict(
        cls,
        item: m.Infra.LockedPackage,
        repository: m.Infra.RepositoryRef,
        repository_root: Path,
        resolution_root: Path,
    ) -> p.Result[bool]:
        """Bind the declared local lock source to a clean, committed checkout.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        expected_root = (repository_root / repository.path).resolve()
        local_source = (
            item.source.editable
            if item.source.editable is not None
            else item.source.directory
        )
        source_kinds = sum(
            source is not None
            for source in (
                item.source.editable,
                item.source.directory,
                item.source.git,
                item.source.registry,
            )
        )
        if (
            source_kinds != 1
            or local_source is None
            or repository.editable != (item.source.editable is not None)
            or not expected_root.is_relative_to(repository_root)
        ):
            return r[bool].fail(
                f"locked workspace source differs from declaration: {item.name}",
            )
        if (resolution_root / local_source).resolve() != expected_root:
            return r[bool].fail(
                f"locked workspace source differs from declaration: {item.name}",
            )
        identity = u.Infra.git_identity(
            m.Infra.GitRepoRequest(repo_root=expected_root),
        )
        if identity.failure:
            return r[bool].from_failure(identity)
        if (
            identity.value.repo_root.resolve() != expected_root
            or identity.value.dirty
            or identity.value.origin_remote is None
            or u.Infra.git_remote_identity(identity.value.origin_remote)
            != u.Infra.git_remote_identity(repository.url)
        ):
            return r[bool].fail(
                f"workspace checkout identity differs from declaration: {item.name}",
            )
        if expected_root == repository_root:
            return r[bool].ok(value=True)
        return cls._workspace_gitlink_verdict(
            repository,
            repository_root,
            identity.value.head_oid,
        )

    @staticmethod
    def _workspace_gitlink_verdict(
        repository: m.Infra.RepositoryRef,
        repository_root: Path,
        head_oid: str,
    ) -> p.Result[bool]:
        """Require the member HEAD, index and committed gitlink to be identical.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if repository.checkout != c.Infra.CheckoutKind.SUBMODULE:
            return r[bool].fail(
                "workspace member has no declared gitlink checkout: "
                f"{repository.distribution}",
            )
        gitlink = u.Infra.git_staged_gitlink_oid(
            m.Infra.GitRefRequest(
                repo_root=repository_root,
                reference=repository.path.as_posix(),
            ),
        )
        if gitlink.failure:
            return r[bool].from_failure(gitlink)
        committed = u.Infra.git_rev_parse(
            m.Infra.GitCommitishRequest(
                repo_root=repository_root,
                commitish=f"{c.Infra.GIT_HEAD}:{repository.path.as_posix()}",
            ),
        )
        if committed.failure:
            return r[bool].from_failure(committed)
        if head_oid != gitlink.value.oid or gitlink.value.oid != committed.value.oid:
            return r[bool].fail(
                "workspace checkout differs from locked gitlink: "
                f"{repository.distribution}",
            )
        return r[bool].ok(value=True)

    @staticmethod
    def _workspace_origin_verdict(
        name: str,
        raw: str | None,
        expected_root: Path,
    ) -> p.Result[bool]:
        """Prove the noneditable build's native local-directory receipt.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if raw is None:
            return r[bool].fail(
                f"locked workspace build lacks PEP 610 provenance: {name}",
            )
        receipt = m.Infra.DirectUrlReceipt.model_validate_json(raw)
        if receipt.dir_info is not None and receipt.dir_info.editable:
            return r[bool].fail(f"CI dependency is editable: {name}")
        parsed = urlparse(receipt.url)
        local_url = (
            parsed.scheme == "file"
            and parsed.netloc in {"", "localhost"}
            and not parsed.query
            and not parsed.fragment
        )
        actual_root = Path(url2pathname(unquote(parsed.path)))
        if (
            receipt.dir_info is None
            or receipt.vcs_info is not None
            or not local_url
            or not actual_root.is_absolute()
            or actual_root.resolve() != expected_root
        ):
            return r[bool].fail(
                f"locked workspace build direct_url mismatch: {name} "
                f"expected={expected_root} actual={receipt.url}",
            )
        return r[bool].ok(value=True)

    @classmethod
    def locked_origin_verdict(
        cls,
        name: str,
        item: m.Infra.LockedPackage,
        raw: str | None,
    ) -> p.Result[bool]:
        """Prove one locked dependency's PEP 610 origin against the lock entry.

        Declared local members are authenticated by ``_validate_workspace_build``
        before this artifact-only boundary. Undeclared local lock sources cannot
        bypass checkout, gitlink, and noneditable receipt authentication.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if raw is None and item.source.git is not None:
            return r[bool].fail(
                f"locked dependency lacks PEP 610 provenance: {name}",
            )
        receipt = (
            m.Infra.DirectUrlReceipt.model_validate_json(raw)
            if raw is not None
            else None
        )
        if (
            receipt is not None
            and receipt.dir_info is not None
            and receipt.dir_info.editable
        ):
            return r[bool].fail(f"CI dependency is editable: {name}")
        if item.source.git is None and item.source.registry is None:
            return r[bool].fail(f"CI member needs a locked artifact source: {name}")
        if item.source.git is not None:
            expected = urlparse(item.source.git.removeprefix("git+"))
            if (
                receipt is None
                or receipt.vcs_info is None
                or receipt.vcs_info.vcs != "git"
                or receipt.vcs_info.commit_id != expected.fragment
                or u.Infra.git_remote_identity(receipt.url)
                != u.Infra.git_remote_identity(expected.geturl())
            ):
                return r[bool].fail(
                    f"installed dependency origin differs from committed lock: {name}",
                )
        return r[bool].ok(value=True)

    @staticmethod
    def _locked_pth_verdict(
        name: str,
        distribution: Distribution,
        *,
        environment_root: Path,
    ) -> p.Result[bool]:
        """Prove one installed artifact's path inventory stays environment-owned.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        files = distribution.files
        if files is None:
            return r[bool].fail(f"installed artifact has no file inventory: {name}")
        for file in files:
            if str(file).endswith(".pth"):
                path = Path(str(distribution.locate_file(file)))
                for line in path.read_text(encoding="utf-8").splitlines():
                    if Path(line).is_absolute() and not Path(
                        line,
                    ).resolve().is_relative_to(
                        environment_root.resolve(),
                    ):
                        return r[bool].fail(
                            f"CI artifact exposes an external source path: {name}",
                        )
        return r[bool].ok(value=True)

    @classmethod
    def _validate_direct_url(
        cls,
        distribution: str,
        raw_payload: str | None,
        expected_root: Path,
    ) -> p.Result[int]:
        """Validate one PEP 610 payload against the declared member root.

        Returns:
            The resulting ``p.Result[int]``.

        """
        if raw_payload is None:
            return r[int].fail(
                "editable provenance missing direct_url.json: "
                f"distribution={distribution} expected={expected_root}",
            )
        try:
            payload = m.Infra.DirectUrlReceipt.model_validate_json(
                raw_payload,
                strict=True,
            )
        except ValueError as exc:
            return r[int].fail_op(
                f"editable provenance direct_url validation ({distribution})",
                exc,
            )
        return cls._editable_url_verdict(distribution, payload, expected_root)

    @staticmethod
    def _editable_url_verdict(
        distribution: str,
        payload: m.Infra.DirectUrlReceipt,
        expected_root: Path,
    ) -> p.Result[int]:
        """Bind one parsed editable receipt to its declared physical source."""
        parsed = urlparse(payload.url)
        if (
            parsed.scheme != "file"
            or payload.dir_info is None
            or not payload.dir_info.editable
            or payload.vcs_info is not None
        ):
            revision = (
                payload.vcs_info.commit_id if payload.vcs_info is not None else None
            )
            return r[int].fail(
                "editable provenance is not an editable file URL: "
                f"distribution={distribution} expected={expected_root} "
                f"url={payload.url} installed_revision={revision}",
            )
        actual_root = Path(url2pathname(unquote(parsed.path))).resolve()
        if actual_root != expected_root:
            return r[int].fail(
                "editable provenance direct_url mismatch: "
                f"distribution={distribution} expected={expected_root} "
                f"actual={actual_root}",
            )
        return r[int].ok(1)

    @classmethod
    def _validate_pth(
        cls,
        distribution: str,
        pth_file: Path,
        expected_root: Path,
    ) -> p.Result[bool]:
        """Validate the distribution-owned editable path file.

        Returns:
            Whether the distribution-owned editable paths are valid.

        """
        read_result = u.Cli.files_read_text(pth_file)
        if read_result.failure:
            return r[bool].from_failure(read_result)
        entries = tuple(
            line.strip()
            for line in read_result.value.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
        if not entries:
            return r[bool].fail(
                "editable provenance pth is empty: "
                f"distribution={distribution} path={pth_file}",
            )
        package_name = u.Infra.project_package_name(expected_root)
        payload = u.Infra.pyproject_payload(expected_root / c.PYPROJECT_FILENAME)
        wheel = payload
        for key in (c.Infra.TOOL, "hatch", "build", "targets", "wheel"):
            child = u.Cli.toml_mapping_child(wheel, key)
            if child is None:
                wheel = {}
                break
            wheel = child
        declared_paths = u.validate_value(
            t.Infra.STR_SEQ_ADAPTER,
            wheel.get("packages", ()),
            strict=True,
        )
        if declared_paths.failure:
            return r[bool].from_failure(declared_paths)
        primary_parts = tuple(package_name.split("."))
        packages: list[t.Pair[str, Path | None]] = []
        for declared in declared_paths.value:
            relative = Path(declared)
            target = (expected_root / relative).resolve()
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or not target.is_relative_to(expected_root)
                or not target.is_dir()
            ):
                return r[bool].fail(
                    "editable provenance declared package path is invalid: "
                    f"distribution={distribution} package={declared}",
                )
            name = (
                package_name
                if relative.parts[-len(primary_parts) :] == primary_parts
                else relative.name
            )
            packages.append((name, target))
        if not packages:
            packages.append((package_name, None))
        exposed: set[t.Pair[str, Path | None]] = set()
        for entry in entries:
            if re.match(r"^import\s", entry) or not Path(entry).is_absolute():
                return r[bool].fail(
                    "editable provenance pth entry is not an absolute source path: "
                    f"distribution={distribution} entry={entry}",
                )
            actual_source = Path(entry).resolve()
            if not actual_source.is_relative_to(expected_root):
                return r[bool].fail(
                    "editable provenance pth mismatch: "
                    f"distribution={distribution} expected_root={expected_root} "
                    f"actual={actual_source}",
                )
            if not actual_source.is_dir():
                return r[bool].fail(
                    "editable provenance source directory is not live: "
                    f"distribution={distribution} path={actual_source}",
                )
            elected = {
                (name, target)
                for name, target in packages
                if (
                    (
                        package := u.Infra.declared_package_dir(
                            name,
                            search_paths=(str(actual_source),),
                        )
                    )
                    is not None
                    and package.resolve().is_relative_to(expected_root)
                    and (target is None or package.resolve() == target)
                )
            }
            if not elected:
                return r[bool].fail(
                    "editable provenance pth exposes no declared package: "
                    f"distribution={distribution} path={actual_source}",
                )
            exposed.update(elected)
        if exposed != set(packages):
            return r[bool].fail(
                "editable provenance pth omits declared package sources: "
                f"distribution={distribution}",
            )
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraWorkspaceEnvironmentProvenance"]
