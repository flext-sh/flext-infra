# Plan collection

<!-- TOC START -->

- [Authorization](#authorization)
- [Source revisions](#source-revisions)
- [Publication and verification](#publication-and-verification)

<!-- TOC END -->

## Authorization

The documentation collector prepares authenticated file plans; the existing
documentation transaction alone publishes them. It neither executes an LLM nor decides
implementation status, supersession, deletion, or Bead closure.

The repository owns source associations in `config/plan-collection.yaml`.
`canonical_dir` is repository-relative; `projection_root` is a separately authorized
absolute output owner. Each source declares its provider, stable ID, root, adapter,
driver/version, plan globs, optional exclusions, timestamp fields, companion-directory
policy, and publication classification.

`enabled` is mandatory. The disabled state requires zero sources and no projection root;
it transactionally deletes only paths authenticated by the existing generated manifest,
then removes the resulting owned empty directories. A repository may enable collection
only with an explicitly approved, versioned source inventory. Ignored `.kilo` session
plans are not a publication source by default; they become one only when the operator
explicitly authorizes them and the repository lists that exact root and glob inventory.

## Source revisions

The `files` adapter accepts explicitly associated plan artifacts, snapshots each plan
and its same-basename companion directory, and includes attachments in the revision
digest. Stable identities separate incoming source revisions from the canonical plan:
existing reconciled text is never overwritten by collection. The companion directory
retains incoming revisions and provenance receipts. Receipt locators are relative to the
configured source and canonical owners; moving a collected corpus between checkouts does
not change its identities or embed the former checkout or personal home path in
versioned provenance.

`private-inventory` automatically inventories declared session sources for agent
reading. It never publishes session contents. Its coverage is explicitly incomplete for
extraction and reconciliation, not equivalent to collected plans. An unavailable source
fails; an empty source is reported distinctly.

The generated manifest records artifact ownership and exact content digests, not
workflow state. Unchanged projected outputs do not become fresh inputs. An edited
projected plan or companion retains its original identity and is collected as a new
incoming revision. Changes to projected ownership metadata fail closed. Recursive source
globs treat same-name companions as attachments, not independent plans.

Explicit source timestamps retain their declared value separately from ISO 8601 UTC
normalization, which is populated only for timezone-aware timestamps. Date-only and
local-datetime precision is preserved; absent timestamps remain unknown. UTF-8 BOM and
CRLF frontmatter are accepted without rewriting archived source bytes. Filesystem
timestamps are not treated as substantive source updates.

## Publication and verification

The publisher authenticates inputs and source topology before effects. It must register
the projection as an explicit transaction participant and account for declared
read/write aliases; it must not relax path-escape validation.

Immutable revisions live below each canonical plan's `incoming/` directory. The
documentation renderer excludes every `incoming` subtree so formatting, TOC generation,
and link rewriting cannot mutate digest-attested evidence. If an unintegrated collection
is interrupted after publication, rebuilding its generated manifest and incoming
artifacts requires explicit operator approval; never repair those files manually or
accept a changed digest.

The post-publication verifier checks every declared output against its planned bytes and
mode, while retaining exact snapshots for unrelated inputs. Manifest, receipt and
canonical text reads, including absence, are bound on first read so a concurrent edit
cannot be adopted as a newer precondition for stale output. Collection reports are not
evidence that semantic reconciliation is complete.

## Verification without provider homes

The existing collection command's `--check` mode verifies an enabled collection's
published canonical manifest and artifacts without visiting source providers or the
optional home projection. It performs no publication, directory creation, pruning or
retirement. Disabled collection is an explicit verification error; ordinary disabled
generation retains its existing removal-only contract.

A successful check requires the current typed source associations and complete source
coverage recorded by a real collection. A legacy manifest without that evidence,
private inventory, configuration drift, unsafe locators, absent artifacts or changed
content/provenance fails. A changed manifest schema requires producer regeneration
before CI; verification never upgrades or repairs evidence. A cold CI checkout verifies
committed evidence without claiming that it collected a provider it cannot access.
Local collection still requires every configured source and never silently skips an
unavailable provider.

Verification binds the original configuration, manifest and published artifact reads
and rechecks those observations before success. Collection binds the original
configuration and source observations to the existing publication guards. The manifest
stores a digest of the typed associations and their collection coverage, not private
provider roots or execution status. Semantic reconciliation and Beads closure remain
separate operations.

Coverage records each source-relative plan locator and the content revision digest
actually observed in that run. Its count, uniqueness and selector confinement must
agree with those references, and each locator/digest must resolve to one authenticated
revision and its incoming content. Historical revisions of removed plans remain
evidence; their presence or order alone never establishes current coverage. An empty
source carries an explicit empty reference sequence and zero count. Reobserving A
after B selects A as current without changing A's original provenance timestamp,
reordering history or duplicating its immutable evidence.

The local collection owner may admit a typed legacy manifest only as the original
ownership before-image. All configured sources must still be collected and every
publication must emit the current association and coverage proof. Malformed or partly
upgraded manifests are rejected. Verification never admits this before-image;
migration neither patches evidence by hand nor exposes a second successful format.

## Failure boundary

The collector preserves failed Results from configuration reads/parsing, publication,
locking and pruning through `from_failure`. The exception, error code and structured
data remain available to the existing CLI failure renderer; a failed prerequisite
blocks its dependent effects. Already published independent effects are not reverted.

Native configuration decoding and evidence validation retain their exception contract.
`config_decode` adds the document source to the original validation exception and
rethrows it. Collection helpers use the selected Result owner's causal `unwrap`
contract: a stored exception is rethrown with its Result context, while a logical
failure without an exception raises explicitly. The collector does not introduce a
catch-all conversion, default, retry or successful empty collection. Its CLI boundary
owns rendering and the nonzero exit; migration never changes invalid input into
qualified evidence.
