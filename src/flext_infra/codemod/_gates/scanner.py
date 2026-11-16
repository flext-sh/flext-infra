"""Cached and bounded-parallel ast-grep batch scanning for codemod gates.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import concurrent.futures
import os
import sys
import tempfile
from collections.abc import Mapping, MutableMapping, Sequence
from contextlib import closing
from itertools import islice
from pathlib import Path

from flext_infra import c, config, p, r, u
from flext_infra._codemod.scan_cache import FlextInfraCodemodScanCache
from flext_infra.codemod._gates.findings import FlextInfraModGateFindings
from flext_infra.codemod._gates.fixtures import FlextInfraModGateFixtures


class FlextInfraModGateScanner(FlextInfraModGateFixtures, FlextInfraModGateFindings):
    """Run per-source cached ast-grep batch scans across governed targets."""

    @staticmethod
    def _report_evidence(receipt: p.Infra.ModScanEvidenceReceipt) -> None:
        """Print bounded totals and the authenticated full-evidence identity."""
        evidence = receipt.evidence
        sys.stderr.write(f"mod: findings total={evidence.findings}\n")
        for finding_class, count in evidence.totals_by_class.items():
            sys.stderr.write(
                f"mod: findings class={finding_class} count={count}\n",
            )
        for repository, count in evidence.totals_by_repository.items():
            sys.stderr.write(f"mod: findings repository={repository} count={count}\n")
        for rule_id, count in evidence.totals_by_rule.items():
            sys.stderr.write(f"mod: findings rule={rule_id} count={count}\n")
        sys.stderr.write(
            f"mod: findings report={receipt.path} sha256={receipt.sha256}\n",
        )
        sys.stderr.flush()

    @classmethod
    def _ruleset_report(
        cls,
        root: Path,
        ruleset: p.Infra.CodemodRuleset,
        rules_by_id: Mapping[str, p.Infra.CodemodRule],
        selection: tuple[Sequence[str], p.Infra.ModScanSourceContext],
        *,
        artifact_root: Path,
    ) -> p.Result[p.Infra.ModScanReport]:
        """Collect one provider's complete native findings before shared admission.

        Returns:
            The resulting ``p.Result[p.Infra.ModScanReport]``.

        """
        context = selection[1]
        ruleset_files = {
            rule_id: rules_by_id[rule_id].resource for rule_id in ruleset.rule_ids
        }
        fragments = cls._ruleset_fragments(
            root, ruleset, selection, artifact_root=artifact_root
        )
        if fragments.failure:
            return r[p.Infra.ModScanReport].from_failure(fragments)
        artifact, _, runs = fragments.value
        report = cls._parse_findings(
            artifact.path,
            root,
            (ruleset_files, frozenset(ruleset.fixable_rule_ids)),
            context,
            artifact,
        ).unwrap()
        sys.stderr.write(f"mod: native findings={report.findings}\n")
        sys.stderr.flush()
        for stderr, outcome, batch in runs:
            if outcome.failure:
                return r[p.Infra.ModScanReport].ok(
                    report.model_copy(
                        update={"native_failures": (outcome.error or "",)}
                    )
                )
            if outcome.value.raw_return_code != 0:
                error_findings = sum(
                    entry.severity == "error"
                    and u.Infra.codemod_source_path(root, entry.file) in batch
                    for entry in report.entries
                )
                if not error_findings:
                    return r[p.Infra.ModScanReport].fail(
                        "ast-grep finding exit has no error-severity occurrence"
                    )
                cls._validate_finding_receipt(stderr, error_findings).unwrap()
        return r[p.Infra.ModScanReport].ok(
            cls.recounted(
                report.entries,
                native_artifacts=(
                    *report.native_artifacts,
                    *(stderr for stderr, _, _ in runs),
                ),
            )
        )

    @classmethod
    def _scan_batch_workers(cls, batch_count: int) -> int:
        """Bound concurrent batch subprocesses to available CPU headroom.

        Returns:
            Number of concurrent batch workers.

        """
        if batch_count <= 1:
            return 1
        cpu_budget = (
            os.process_cpu_count() or config.Infra.codegen.lint_snapshot_workers
        )
        sg_threads = max(1, u.Infra.ast_grep_scan_threads())
        return max(
            1,
            min(
                batch_count,
                config.Infra.codegen.lint_snapshot_workers,
                max(2, cpu_budget // sg_threads),
            ),
        )

    @classmethod
    def _record_batch_outcome(
        cls,
        batch: frozenset[Path],
        scanned: p.Result[
            tuple[
                p.Cli.AtomicFileReceipt,
                p.Result[p.Cli.ProcessOutcome],
                Mapping[Path, str],
            ]
        ],
        keys: Mapping[Path, str],
        fragments: MutableMapping[Path, Path | str | None],
    ) -> tuple[
        p.Cli.AtomicFileReceipt,
        p.Result[p.Cli.ProcessOutcome],
        frozenset[Path],
    ]:
        """Persist completed batch fragments to cache and record run outcome.

        Returns:
            Tuple of stderr receipt, process outcome, and batch paths.

        """
        stderr, outcome, records = scanned.value
        for path in batch:
            fragments[path] = (
                records.get(path, "")
                if outcome.failure
                else FlextInfraCodemodScanCache.store(keys[path], records.get(path, ""))
            )
        return (stderr, outcome, batch)

    @classmethod
    def _execute_batches_sequential(
        cls,
        scan_target: tuple[
            Path,
            p.Infra.CodemodRuleset,
            p.Infra.ModScanSourceContext,
            Path,
        ],
        batch_state: tuple[
            Sequence[tuple[int, frozenset[Path]]],
            Path,
            Mapping[Path, str],
            MutableMapping[Path, Path | str | None],
        ],
    ) -> p.Result[
        tuple[
            tuple[
                p.Cli.AtomicFileReceipt,
                p.Result[p.Cli.ProcessOutcome],
                frozenset[Path],
            ],
            ...,
        ]
    ]:
        """Execute scan batches sequentially, stopping early on outcome failure.

        Returns:
            Recorded batch outcomes or the first scan failure.

        """
        root, ruleset, context, artifact_root = scan_target
        indexed_batches, directory, keys, fragments = batch_state
        runs: list[
            tuple[
                p.Cli.AtomicFileReceipt,
                p.Result[p.Cli.ProcessOutcome],
                frozenset[Path],
            ]
        ] = []
        for start, batch in indexed_batches:
            scanned = cls._scan_batch(
                root,
                ruleset,
                (batch, context),
                directory / str(start),
                artifact_root=artifact_root,
            )
            if scanned.failure:
                return r[
                    tuple[
                        tuple[
                            p.Cli.AtomicFileReceipt,
                            p.Result[p.Cli.ProcessOutcome],
                            frozenset[Path],
                        ],
                        ...,
                    ]
                ].from_failure(scanned)
            run = cls._record_batch_outcome(batch, scanned, keys, fragments)
            runs.append(run)
            if run[1].failure:
                break
        return r[
            tuple[
                tuple[
                    p.Cli.AtomicFileReceipt,
                    p.Result[p.Cli.ProcessOutcome],
                    frozenset[Path],
                ],
                ...,
            ]
        ].ok(tuple(runs))

    @classmethod
    def _execute_batches_parallel(
        cls,
        scan_target: tuple[
            Path,
            p.Infra.CodemodRuleset,
            p.Infra.ModScanSourceContext,
            Path,
        ],
        batch_state: tuple[
            Sequence[tuple[int, frozenset[Path]]],
            Path,
            Mapping[Path, str],
            MutableMapping[Path, Path | str | None],
        ],
    ) -> p.Result[
        tuple[
            tuple[
                p.Cli.AtomicFileReceipt,
                p.Result[p.Cli.ProcessOutcome],
                frozenset[Path],
            ],
            ...,
        ]
    ]:
        """Execute scan batches in bounded parallel waves.

        Returns:
            Recorded batch outcomes or the first scan failure.

        """
        root, ruleset, context, artifact_root = scan_target
        indexed_batches, directory, keys, fragments = batch_state
        runs: list[
            tuple[
                p.Cli.AtomicFileReceipt,
                p.Result[p.Cli.ProcessOutcome],
                frozenset[Path],
            ]
        ] = []
        workers = cls._scan_batch_workers(len(indexed_batches))
        pending = iter(indexed_batches)
        stopped = False
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            while not stopped and (wave := tuple(islice(pending, workers))):
                futures = tuple(
                    (
                        batch,
                        pool.submit(
                            cls._scan_batch,
                            root,
                            ruleset,
                            (batch, context),
                            directory / str(start),
                            artifact_root=artifact_root,
                        ),
                    )
                    for start, batch in wave
                )
                for batch, future in futures:
                    scanned = future.result()
                    if scanned.failure:
                        return r[
                            tuple[
                                tuple[
                                    p.Cli.AtomicFileReceipt,
                                    p.Result[p.Cli.ProcessOutcome],
                                    frozenset[Path],
                                ],
                                ...,
                            ]
                        ].from_failure(scanned)
                    run = cls._record_batch_outcome(batch, scanned, keys, fragments)
                    runs.append(run)
                    if run[1].failure:
                        stopped = True
                        break
        return r[
            tuple[
                tuple[
                    p.Cli.AtomicFileReceipt,
                    p.Result[p.Cli.ProcessOutcome],
                    frozenset[Path],
                ],
                ...,
            ]
        ].ok(tuple(runs))

    @classmethod
    def _ruleset_fragments(
        cls,
        root: Path,
        ruleset: p.Infra.CodemodRuleset,
        selection: tuple[Sequence[str], p.Infra.ModScanSourceContext],
        *,
        artifact_root: Path,
    ) -> p.Result[
        tuple[
            p.Cli.AtomicFileReceipt,
            frozenset[Path],
            tuple[
                tuple[
                    p.Cli.AtomicFileReceipt,
                    p.Result[p.Cli.ProcessOutcome],
                    frozenset[Path],
                ],
                ...,
            ],
        ]
    ]:
        """Publish one ruleset's native records from per-source fragments.

        Returns:
            The published records, the freshly scanned sources and each
            batch's native stderr receipt, outcome and sources.

        """
        result_type = r[
            tuple[
                p.Cli.AtomicFileReceipt,
                frozenset[Path],
                tuple[
                    tuple[
                        p.Cli.AtomicFileReceipt,
                        p.Result[p.Cli.ProcessOutcome],
                        frozenset[Path],
                    ],
                    ...,
                ],
            ]
        ]
        context = selection[1]
        keys, cached = cls._cached_fragments(root, ruleset, selection)
        fragments: MutableMapping[Path, Path | str | None] = dict(cached)
        missing = frozenset(
            path for path, fragment in fragments.items() if fragment is None
        )
        sys.stderr.write(
            f"mod: ast-grep cache hit={len(keys) - len(missing)} miss={len(missing)}\n"
        )
        sys.stderr.flush()
        ordered = sorted(missing)
        batch_size = (
            context.scan_batch_files or config.Infra.codegen.make.scan_batch_files
        )
        indexed_batches = tuple(
            (start, frozenset(ordered[start : start + batch_size]))
            for start in range(0, len(ordered), batch_size)
        )
        executor = (
            cls._execute_batches_parallel
            if context.runner is None and len(indexed_batches) > 1
            else cls._execute_batches_sequential
        )
        with tempfile.TemporaryDirectory(prefix="mod-native-") as directory:
            executed = executor(
                (root, ruleset, context, artifact_root),
                (indexed_batches, Path(directory), keys, fragments),
            )
            if executed.failure:
                return result_type.from_failure(executed)
            stdout_file = Path(directory) / "stdout"
            u.Cli.atomic_write_text_file(
                stdout_file,
                "".join(
                    fragment
                    if isinstance(fragment, str)
                    else fragment.read_text(encoding=c.DEFAULT_ENCODING)
                    for fragment in fragments.values()
                    if fragment is not None
                ),
            ).unwrap()
            artifact = u.Infra.publish_mod_native_artifact(artifact_root, stdout_file)
        return result_type.ok((artifact, missing, executed.value))

    @classmethod
    def _cached_fragments(
        cls,
        root: Path,
        ruleset: p.Infra.CodemodRuleset,
        selection: tuple[Sequence[str], p.Infra.ModScanSourceContext],
    ) -> tuple[dict[Path, str], dict[Path, Path | str | None]]:
        """Key every scanned source and look up its cached fragment.

        Returns:
            Each source's cache key and its cached fragment, or ``None``.

        """
        targets, context = selection
        digest = FlextInfraCodemodScanCache.ruleset_digest(
            ruleset.config, u.Infra.managed_mise_binary(c.Infra.SG, root).unwrap()
        )
        keys = {
            path: FlextInfraCodemodScanCache.source_key(
                digest, path.relative_to(root), state
            )
            for path in sorted(cls._scan_source_paths(root, targets))
            if (state := context.inventory[path]) is not None
        }
        fragments: dict[Path, Path | str | None] = {
            path: FlextInfraCodemodScanCache.lookup(key) for path, key in keys.items()
        }
        return keys, fragments

    @classmethod
    def _scan_batch(
        cls,
        root: Path,
        ruleset: p.Infra.CodemodRuleset,
        selection: tuple[frozenset[Path], p.Infra.ModScanSourceContext],
        scratch: Path,
        *,
        artifact_root: Path,
    ) -> p.Result[
        tuple[
            p.Cli.AtomicFileReceipt,
            p.Result[p.Cli.ProcessOutcome],
            Mapping[Path, str],
        ]
    ]:
        """Scan one batch of uncached sources in one native invocation.

        Returns:
            The batch's native stderr receipt, outcome and per-source records.

        """
        batch, context = selection
        scanned_file, stderr_file = (
            scratch.with_name(f"{scratch.name}-{name}")
            for name in ("scanned", "stderr")
        )
        outcome = cls._run_tool(
            root,
            u.Infra.ast_grep_scan_command(
                ruleset.config,
                rule_ids=ruleset.rule_ids,
                targets=tuple(
                    path.relative_to(root).as_posix() for path in sorted(batch)
                ),
                json_stream=True,
            ),
            outputs=(scanned_file, stderr_file, artifact_root),
            finding_exit_code=1,
            runner=u.Cli if context.runner is None else context.runner,
        )
        records = cls._source_records(
            scanned_file, root, batch, stopped=outcome.failure
        )
        if records.failure:
            return r[
                tuple[
                    p.Cli.AtomicFileReceipt,
                    p.Result[p.Cli.ProcessOutcome],
                    Mapping[Path, str],
                ]
            ].from_failure(records)
        return r[
            tuple[
                p.Cli.AtomicFileReceipt,
                p.Result[p.Cli.ProcessOutcome],
                Mapping[Path, str],
            ]
        ].ok((
            u.Infra.publish_mod_native_artifact(artifact_root, stderr_file),
            outcome,
            records.value,
        ))

    @classmethod
    def _source_records(
        cls,
        stdout: Path,
        root: Path,
        scanned: frozenset[Path],
        *,
        stopped: bool = False,
    ) -> p.Result[Mapping[Path, str]]:
        """Group one scan's native records by the scanned source they name.

        Returns:
            Each scanned source's exact JSONL records, or the first invalid record.

        """
        grouped: MutableMapping[Path, list[str]] = {}
        with closing(cls._native_records(stdout)) as lines:
            for _offset, raw_line in lines:
                line = raw_line.strip()
                if not line:
                    continue
                parsed = u.Cli.json_loads(line)
                if parsed.failure and stopped:
                    break
                if parsed.failure:
                    return r[Mapping[Path, str]].from_failure(parsed)
                if not isinstance(parsed.value, Mapping) or not isinstance(
                    file := parsed.value.get("file"), str
                ):
                    return r[Mapping[Path, str]].fail(
                        f"ast-grep JSONL record names no file: {line!r}"
                    )
                source = u.Infra.codemod_source_path(root, Path(file))
                if source not in scanned:
                    return r[Mapping[Path, str]].fail(
                        f"ast-grep JSONL record names an unscanned source: {file}"
                    )
                grouped.setdefault(source, []).append(line.decode("utf-8") + "\n")
        return r[Mapping[Path, str]].ok({
            source: "".join(records) for source, records in grouped.items()
        })

    @staticmethod
    def _scan_source_paths(root: Path, targets: Sequence[str]) -> frozenset[Path]:
        """Enumerate the native selection through its canonical Python file owner.

        Returns:
            Resolved Python paths, retaining prohibited lexical stub leaves.

        """
        return frozenset(
            path.absolute() if path.suffix == ".pyi" else path.resolve()
            for target in targets
            for path in (
                u.Infra.iter_directory_python_files(root / target, repository_root=root)
                if (root / target).suffix != ".pyi" and (root / target).is_dir()
                else (root / target,)
            )
        )


__all__: list[str] = ["FlextInfraModGateScanner"]
