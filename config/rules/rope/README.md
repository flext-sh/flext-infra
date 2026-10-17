# Repository Rope Rules

See the [packaged Rope phase documentation](../../../src/flext_infra/config/rules/rope/README.md)
for shared phase contracts and repository overlay ownership.

[Packaged accessor migrations](../../../src/flext_infra/config/rules/rope/accessor-migrations.yaml)
extend the existing accessor phase with typed expression
rules. Each rule binds a removed accessor to its qualified declaring class, backing
field, origin package, and public normalizer. The phase proves those member identities
through the live Rope graph before replacing a complete read expression. Actual fields
and overrides owned by other classes, and ordinary payload strings, remain outside the
selected contract. An unknown receiver, overridden owned backing field, write use, or
captured normalizer facade rejects the transformation before publication. The public
normalizers preserve scope token parsing and optional path resolution without adding
serialized computed fields. Consumer propagation runs through `make mod`; repeated
passes produce no accessor changes.
