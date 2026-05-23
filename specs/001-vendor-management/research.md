# Research: Vendor Management

## Decision: Use Python 3.14 with FastAPI and SQLAlchemy 2.x

**Rationale**: The implementation environment is using Python 3.14, along with FastAPI,
SQLAlchemy 2.x, and SQLite.
FastAPI provides strong request/response typing for machine-readable contracts, while
SQLAlchemy 2.x keeps the domain and persistence layers explicit without adding
unnecessary abstraction.

**Alternatives considered**:

- Flask: lighter weight, but requires more manual contract and validation wiring.
- TypeScript/Express: viable for the broader prompt, but outside the chosen stack.

## Decision: Use SQLite with startup seeding for vendor master data

**Rationale**: This is a PoC feature with pre-seeded vendors and no vendor CRUD.
SQLite minimizes operational complexity and aligns with the constitution's simplicity
rule, while startup seeding guarantees deterministic vendor availability scenarios for
agents and tests.

**Alternatives considered**:

- PostgreSQL: better production realism, but unnecessary infrastructure for this PoC.
- In-memory structures: too weak for integration-first testing and persistence realism.

## Decision: Expose two read contracts and a shared error catalog

**Rationale**: The feature scope is vendor eligibility and vendor exposure, not vendor
maintenance. A read-only contract keeps the feature bounded while still defining the
stable business error codes that downstream write flows must reuse when rejecting
inactive vendors.

**Alternatives considered**:

- Fold eligibility into future purchase-order creation only: would hide a key planning
  decision from agents and reduce autonomous completion.
- Add vendor CRUD endpoints: violates the explicit feature constraint that vendors are
  pre-seeded only.

## Decision: Compute exposure summaries server-side from unpaid invoices

**Rationale**: The caller must not do arithmetic. The API therefore computes the total
outstanding amount and supporting derived context, including the count of open invoices
and the statuses included in the calculation, using only invoices that remain unpaid at
request time.

**Alternatives considered**:

- Return raw invoice rows only: would force arithmetic into the agent and weaken the
  machine-first contract.
- Materialize a separate exposure table first: premature complexity for a PoC.

## Decision: Require correlation IDs and real-database tests

**Rationale**: The constitution requires traceability and integration-first testing.
Every contract must carry correlation data, and testing must exercise real SQLite
persistence rather than mocks so exposure calculations and error semantics are validated
end to end.

**Alternatives considered**:

- Mock the repository layer: faster, but prohibited by the constitution.
- Defer correlation IDs until implementation: would leave observability unspecified.
