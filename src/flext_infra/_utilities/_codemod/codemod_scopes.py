"""File scopes a catalog rule names, resolved into native files and ignores.

ast-grep matches one file's syntax and sees no project fact about the file
itself. A catalog rule that holds only in some files of the project (outside
the layer-zero modules, inside one facade family) names those file sets under
``metadata.scope``; the project's generated provider publishes them, and the
native stage writes them into the rule's ``files`` and ``ignores``. A rule
whose captured letter must (or must not) be one of the file's facade families
is partitioned per file group into generated rules
``<rule id>--<package>[--<key>]``, each scoped to that group's files, so a
native scan of the stage reproduces the verdict with no admission after it.

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

import re
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath

from flext_cli import u

from flext_infra import c, m, t


class FlextInfraUtilitiesCodemodScopes:
    """Resolve ``metadata.scope`` into native rule documents."""

    @staticmethod
    def codemod_stage_scopes(
        generated: Path | None,
    ) -> Mapping[str, Sequence[str]]:
        """Read the file scopes the stage's generated provider published.

        Returns:
            Project-relative file sets keyed by selector; none without a
            generated provider.

        Raises:
            TypeError: If the published scopes are not selector lists.

        """
        if generated is None:
            return {}
        payload = u.Cli.json_read(
            generated.parent / c.Infra.CODEMOD_SCOPES_FILENAME
        ).unwrap()
        scopes: dict[str, Sequence[str]] = {}
        for selector, paths in payload.items():
            if not isinstance(paths, Sequence) or isinstance(paths, str):
                msg = f"generated file scope is not a list: {selector}"
                raise TypeError(msg)
            scopes[selector] = tuple(str(path) for path in paths)
        return scopes

    @classmethod
    def codemod_scoped_document(
        cls,
        document: t.JsonMapping,
        scopes: Mapping[str, Sequence[str]],
        rule_id: str,
    ) -> t.JsonMapping:
        """Resolve one staged rule's ``in``/``not-in`` scopes into files and ignores.

        ``in`` keeps only the scoped files the document's own ``files`` and
        ``ignores`` admit; ``not-in`` adds the scoped files to its ignores.

        Returns:
            The native document, or the document itself when it names no scope.

        Raises:
            ValueError: If the scope is malformed, names an unknown selector, or
                partitions the rule: a partitioned rule is rendered by the
                project's generated provider and never staged as authored.

        """
        scope = cls._declared_scope(document, rule_id)
        if scope is None:
            return document
        if c.Infra.CODEMOD_SCOPE_PARTITION_KEY in scope:
            msg = f"{rule_id}: a partitioned rule is rendered, never staged"
            raise ValueError(msg)
        return cls._bounded(document, scope, scopes, rule_id)[0]

    @classmethod
    def codemod_partitioned_documents(
        cls,
        document: t.JsonMapping,
        scopes: Mapping[str, Sequence[str]],
        rule_id: str,
        package: str,
    ) -> Mapping[str, t.JsonMapping]:
        """Render one partitioned catalog rule into the project's native documents.

        ``partition`` splits the rule per published file group (a facade
        letter's family, a private family package): each copy constrains the
        named variable to the group's key and keeps (``holds: true``) or
        ignores (``holds: false``) the group's files; with ``holds: false`` a
        last copy covers every value that names no group. Each copy is a
        generated rule ``<rule id>--<package>[--<key>]`` without the scope.

        Returns:
            The generated documents keyed by their rule id.

        Raises:
            ValueError: If the rule declares no partition.

        """
        scope = cls._declared_scope(document, rule_id)
        partition = (
            None if scope is None else scope.get(c.Infra.CODEMOD_SCOPE_PARTITION_KEY)
        )
        if scope is None or partition is None:
            msg = f"{rule_id}: only a partitioned rule is rendered per project"
            raise ValueError(msg)
        base, files, ignores = cls._bounded(document, scope, scopes, rule_id)
        metadata = base.get("metadata")
        unscoped = {
            **base,
            "metadata": {
                **{
                    key: value
                    for key, value in (
                        metadata.items() if isinstance(metadata, Mapping) else ()
                    )
                    if key != c.Infra.CODEMOD_SCOPE_METADATA_KEY
                },
                c.Infra.CODEMOD_PARTITION_OF_KEY: rule_id,
            },
        }
        separator = c.Infra.CODEMOD_GENERATED_ID_SEPARATOR
        rendered: dict[str, t.JsonMapping] = {}
        for key, native in cls._partition_documents(
            unscoped, partition, (scopes, files, ignores), rule_id
        ):
            identity = separator.join(
                (rule_id, package)
                if key is None
                else (rule_id, package, cls._key_identity(key))
            )
            rendered[identity] = {**native, "id": identity}
        return rendered

    @staticmethod
    def _key_identity(key: str) -> str:
        """Spell one partition key as a rule-id segment.

        A key that is a plain dotted or comma-separated name stays readable;
        any other key (a published regex) is identified by its digest.

        Returns:
            The rule-id segment of the key.

        """
        if re.fullmatch(c.Infra.CODEMOD_PARTITION_KEY_IDENTITY_PATTERN, key):
            return key
        return u.Cli.sha256_content(key)[: c.Infra.CODEMOD_PARTITION_KEY_DIGEST_LENGTH]

    @classmethod
    def codemod_embedded_utilities(
        cls,
        document: t.JsonMapping,
        catalog: Mapping[str, t.JsonMapping],
    ) -> t.JsonMapping:
        """Embed the catalog utilities a rendered document references as locals.

        A stage qualifies every catalog utility by its provider, so a
        generated document carries the catalog utilities it matches (and
        theirs, transitively) under its own ``utils``; the stable generated
        utilities stay global.

        Returns:
            The document with every referenced catalog utility embedded.

        """
        local = document.get("utils")
        utils: dict[str, t.JsonValue] = (
            dict(local) if isinstance(local, Mapping) else {}
        )
        pending = list(cls._matched(document))
        while pending:
            identity = pending.pop()
            if identity in utils or identity not in catalog:
                continue
            utils[identity] = dict(catalog[identity])
            pending.extend(cls._matched(catalog[identity]))
        return {**document, "utils": utils} if utils else document

    @classmethod
    def codemod_bound_document(
        cls,
        document: t.JsonMapping,
        utilities: Mapping[str, t.JsonMapping],
        sensitive: frozenset[str],
    ) -> t.JsonMapping:
        """Embed every binding-sensitive utility a staged rule references.

        ast-grep evaluates a global utility in its own metavariable scope,
        while a rule's local utilities share the rule's bindings. A referenced
        utility whose rule names a metavariable, directly or through the
        utilities it matches, is copied into the rule's ``utils`` under the
        same identity, so a backreference such as ``$NAME`` binds the rule's
        own capture. ``sensitive`` is ``codemod_binding_sensitive`` of the
        same utilities, computed once per stage.

        Returns:
            The document with every binding-sensitive utility embedded.

        """
        local = document.get("utils")
        utils: dict[str, t.JsonValue] = (
            dict(local) if isinstance(local, Mapping) else {}
        )
        pending = list(cls._matched(document))
        while pending:
            identity = pending.pop()
            if identity in utils or identity not in sensitive:
                continue
            utils[identity] = dict(utilities[identity])
            pending.extend(cls._matched(utilities[identity]))
        return {**document, "utils": utils} if utils else document

    @classmethod
    def codemod_binding_sensitive(
        cls, utilities: Mapping[str, t.JsonMapping]
    ) -> frozenset[str]:
        """Name the utilities whose verdict depends on the caller's bindings.

        Returns:
            Every utility naming a metavariable, closed over ``matches``.

        """
        pattern = re.compile(c.Infra.CODEMOD_METAVARIABLE_PATTERN)
        sensitive = {
            identity
            for identity, body in utilities.items()
            if pattern.search(u.Cli.json_dumps(dict(body)).unwrap())
        }
        grown = True
        while grown:
            reached = {
                identity
                for identity, body in utilities.items()
                if identity not in sensitive
                and sensitive.intersection(cls._matched(body))
            }
            sensitive.update(reached)
            grown = bool(reached)
        return frozenset(sensitive)

    @classmethod
    def _matched(cls, value: t.JsonValue | t.JsonMapping) -> Sequence[str]:
        """Collect every utility identity a rule fragment references.

        Returns:
            The ``matches`` identities in the fragment.

        """
        if isinstance(value, Mapping):
            return tuple(
                found
                for key, item in value.items()
                for found in (
                    (item,)
                    if key == "matches" and isinstance(item, str)
                    else (*item, *cls._matched(item))
                    if key == "matches" and isinstance(item, Mapping)
                    else cls._matched(item)
                )
            )
        if isinstance(value, list):
            return tuple(found for item in value for found in cls._matched(item))
        return ()

    @staticmethod
    def _declared_scope(document: t.JsonMapping, rule_id: str) -> t.JsonMapping | None:
        """Read and validate a rule's ``metadata.scope``.

        Returns:
            The scope mapping, or ``None`` when the rule declares none.

        Raises:
            ValueError: If the scope is not a mapping of the known keys.

        """
        metadata = document.get("metadata")
        scope = (
            metadata.get(c.Infra.CODEMOD_SCOPE_METADATA_KEY)
            if isinstance(metadata, Mapping)
            else None
        )
        if scope is None:
            return None
        keys = {
            c.Infra.CODEMOD_SCOPE_IN_KEY,
            c.Infra.CODEMOD_SCOPE_NOT_IN_KEY,
            c.Infra.CODEMOD_SCOPE_PARTITION_KEY,
        }
        if not isinstance(scope, Mapping) or not scope or set(scope) - keys:
            msg = f"{rule_id}: metadata.scope maps only {sorted(keys)}"
            raise ValueError(msg)
        return scope

    @classmethod
    def _bounded(
        cls,
        document: t.JsonMapping,
        scope: t.JsonMapping,
        scopes: Mapping[str, Sequence[str]],
        rule_id: str,
    ) -> tuple[t.JsonMapping, Sequence[str] | None, Sequence[str]]:
        """Apply the ``in`` and ``not-in`` scopes of one rule.

        ``files`` is ``None`` while nothing restricts the rule's files.

        Returns:
            The bounded document with its resulting ``files`` and ignores.

        """
        files: Sequence[str] | None = (
            cls._globs(document, "files", rule_id) if "files" in document else None
        )
        ignores = cls._globs(document, "ignores", rule_id)
        base = dict(document)
        if c.Infra.CODEMOD_SCOPE_IN_KEY in scope:
            files = tuple(
                cls._admitted(
                    cls._selected(scope, c.Infra.CODEMOD_SCOPE_IN_KEY, scopes, rule_id),
                    files,
                    ignores,
                )
            )
            base["files"] = list(files)
        if c.Infra.CODEMOD_SCOPE_NOT_IN_KEY in scope:
            ignores = (
                *ignores,
                *(
                    f"**/{path}"
                    for path in cls._selected(
                        scope, c.Infra.CODEMOD_SCOPE_NOT_IN_KEY, scopes, rule_id
                    )
                ),
            )
            base["ignores"] = list(ignores)
        return base, files, ignores

    @classmethod
    def _partition_documents(
        cls,
        base: t.JsonMapping,
        partition: t.JsonValue,
        context: tuple[
            Mapping[str, Sequence[str]], Sequence[str] | None, Sequence[str]
        ],
        rule_id: str,
    ) -> Sequence[tuple[str | None, t.JsonMapping]]:
        """Partition one document per published file group of a variable.

        Each key names one file group, published as ``<selectors><key>``; its
        copy constrains the variable to (``matching: false``: away from) the
        key's regex (the declared one, or ``pattern`` instantiated with the
        key) and keeps (``holds: true``) or ignores (``holds: false``) the
        group's files. With ``holds: false`` a last copy covers every value no
        key's regex matches.

        Returns:
            Each key with its native document, plus the keyless remainder when
            the group must not hold.

        Raises:
            TypeError: If the partition is not a mapping.

        """
        scopes, files, ignores = context
        if not isinstance(partition, Mapping):
            msg = f"{rule_id}: metadata.scope.partition must be a mapping"
            raise TypeError(msg)
        declared = m.Infra.CodemodScopePartition.model_validate({
            **partition,
            "rule_id": rule_id,
        })
        prefix = declared.selectors
        keys = dict(declared.keys) or {
            selector.removeprefix(prefix): cls._key_pattern(
                declared.pattern, selector.removeprefix(prefix)
            )
            for selector in sorted(scopes)
            if selector.startswith(prefix)
        }
        documents: list[tuple[str | None, t.JsonMapping]] = []
        for key, pattern in keys.items():
            members = scopes.get(f"{prefix}{key}", ())
            narrowed = cls._constrained(
                base,
                declared.variable,
                {"regex": pattern}
                if declared.matching
                else {"not": {"regex": pattern}},
            )
            if declared.holds:
                admitted = list[t.JsonValue](cls._admitted(members, files, ignores))
                if admitted:
                    documents.append((key, {**narrowed, "files": admitted}))
            else:
                documents.append((
                    key,
                    {
                        **narrowed,
                        "ignores": list[t.JsonValue]([
                            *ignores,
                            *(f"**/{path}" for path in members),
                        ]),
                    },
                ))
        if not declared.holds:
            remainder: t.JsonMapping = (
                {"not": {"any": [{"regex": pattern} for pattern in keys.values()]}}
                if keys
                else {}
            )
            documents.append((
                None,
                cls._constrained(base, declared.variable, remainder)
                if remainder
                else base,
            ))
        return tuple(documents)

    @staticmethod
    def _key_pattern(template: str, key: str) -> str:
        """Instantiate one partition key's regex from the rule's template.

        ``{key}`` is the escaped key; ``{alternatives}`` the escaped
        comma-separated parts of the key as one alternation; ``{raw}`` the key
        itself, for a group whose key the producer publishes as a regex.

        Returns:
            The key's native regex.

        """
        return (
            template
            .replace(c.Infra.CODEMOD_PARTITION_RAW_PLACEHOLDER, key)
            .replace(c.Infra.CODEMOD_PARTITION_KEY_PLACEHOLDER, re.escape(key))
            .replace(
                c.Infra.CODEMOD_PARTITION_ALTERNATIVES_PLACEHOLDER,
                "|".join(re.escape(part) for part in key.split(",")),
            )
        )

    @staticmethod
    def _constrained(
        document: t.JsonMapping, variable: str, rule: t.JsonMapping
    ) -> t.JsonMapping:
        """Add one native constraint to a metavariable, keeping any it has.

        Returns:
            The document with the variable's constraint narrowed.

        """
        constraints = document.get("constraints")
        current = dict(constraints) if isinstance(constraints, Mapping) else {}
        existing = current.get(variable)
        current[variable] = (
            dict(rule) if existing is None else {"all": [existing, dict(rule)]}
        )
        return {**document, "constraints": current}

    @staticmethod
    def _globs(document: t.JsonMapping, key: str, rule_id: str) -> Sequence[str]:
        """Read one native glob list of a rule document.

        Returns:
            The declared globs, empty when absent.

        Raises:
            TypeError: If the value is not a list.

        """
        value = document.get(key, [])
        if not isinstance(value, Sequence) or isinstance(value, str):
            msg = f"{rule_id}: {key} must be a list of globs"
            raise TypeError(msg)
        return tuple(str(glob) for glob in value)

    @staticmethod
    def _selected(
        scope: t.JsonMapping,
        key: str,
        scopes: Mapping[str, Sequence[str]],
        rule_id: str,
    ) -> Sequence[str]:
        """Union the file sets one scope key names.

        Returns:
            The sorted project-relative paths of every named selector.

        Raises:
            TypeError: If the key is not a selector list.
            ValueError: If the key names an unknown selector.

        """
        names = scope.get(key, [])
        if not isinstance(names, Sequence) or isinstance(names, str):
            msg = f"{rule_id}: metadata.scope.{key} must be a selector list"
            raise TypeError(msg)
        unknown = sorted(str(name) for name in names if str(name) not in scopes)
        if unknown:
            msg = (
                f"{rule_id}: unknown file scope selectors {unknown}; "
                f"available selectors are {sorted(scopes)}"
            )
            raise ValueError(msg)
        return tuple(sorted({path for name in names for path in scopes[str(name)]}))

    @staticmethod
    def _admitted(
        paths: Sequence[str], files: Sequence[str] | None, ignores: Sequence[str]
    ) -> list[str]:
        """Keep the paths a document's own ``files`` and ``ignores`` admit.

        Returns:
            The admitted paths as native ``files`` globs.

        """
        return [
            f"**/{path}"
            for path in paths
            if (files is None or any(PurePosixPath(path).full_match(g) for g in files))
            and not any(PurePosixPath(path).full_match(g) for g in ignores)
        ]


__all__: list[str] = ["FlextInfraUtilitiesCodemodScopes"]
