# incast-safe-queue-budget

This standalone repository accompanies the internal manuscript **Exact
Queue-Budget Certificates for Reserved-Service Incast: Release Windows,
Correlated Phases, and Tractability**. It contains exact-rational reference
implementations, bounded independent oracles, written proofs, deterministic
inputs, tests, raw results, and claim/resource ledgers.

The artifact supports a completed internal research draft. It is not a claim of
peer review, switch deployment, transport performance, or external submission
readiness. General theorems are written mathematical arguments, not
proof-assistant developments; finite checks validate implementations only on
the declared domains.

## Reproduce all shipped scientific results

Use Python 3.10 or later on Linux. Only the standard library is required. No
package installation, network access, model API, GPU, private data, or paper
directory is used.

```sh
python3 reproduce.py --part first  --output /tmp/incast-reproduction
python3 reproduce.py --part second --output /tmp/incast-reproduction
```

The second command verifies the retained first part before resuming. The first
part runs 11 validation jobs; the second runs the remaining 6, then an explicitly
partitioned test contract of 18 core methods plus 15 additional exactness and
adversarial methods (33 total), three example-certificate actions, and three
derived-file comparisons. Every scientific JSON field and every derived CSV
must equal the shipped result; only timing and RSS measurements are excluded. A
count mismatch, import failure, result mismatch, timeout, or failed test exits
nonzero.

Each validation child has a 40-second CPU limit and a 3,584 MiB address-space
limit; the parent imposes a 40-second wall limit per child. One worker is used.
A slower host may time out rather than silently reducing coverage. The frozen clean-archive two-part run recorded 18.096426 parent-plus-child CPU seconds,
18.712093 seconds of active wall time, and 40,504 KiB as the largest child peak
RSS; these are host-specific feasibility measurements, not performance results.

## Inspect one independent-window certificate

```sh
python3 src/queue_certificate.py check inputs/example.json
python3 src/queue_certificate.py check inputs/example.json \
  --rows-output /tmp/incast-envelope-rows.jsonl
python3 src/queue_certificate.py optimize inputs/example.json \
  --output /tmp/incast-certificate.json
python3 src/queue_certificate.py verify inputs/example.json \
  /tmp/incast-certificate.json
```

The example has exact rates `(1,1)`, minimum pooled occupancy 8, and two active
support lines `10-2x` and `6+2x`, combined with weights `1/2`. The verifier
reconstructs the claimed cuts and replays the envelope without invoking the
optimizer or hull builder. `check` reports private maxima `(4,5)`, a pooled
witness at time 4, and compact checker/storage metadata. Full `q/p` rows are not
materialized by default; `--rows-output` streams one JSON record per endpoint.
The private maxima need not occur together.

Burst tenant, lower endpoint, upper endpoint, and size fields are integers.
Rates, floors, and capacities accept integers or exact strings such as `1/2`.
Binary floating point, booleans, duplicate JSON keys, and non-finite constants
are rejected. Rational times and sizes must be converted by an exact common
integer scale; the CLI never rounds them. Input is limited to 2 MiB, checking to
10,000 bursts, and two-tenant optimization to 32 bursts. This is a bounded
research interface, not a hardened network service.

## Implemented mechanisms and written theorems

- `src/queues.py`: ordinary trace replay, a sparse-event transparent recurrence
  with optional row streaming, a heap-based constant-rate sweep, clipped
  witnesses, and fixed equal-cell calendars.
- `src/oracle.py`: exhaustive integer-release oracle and an independently
  organized actual-trace two-tenant allocation oracle.
- `src/allocation.py`: general-tenant private-cap admission and exact
  **two-tenant** pooled-rate optimization/checking.
- `src/phases.py`: construction and ordinary replay for binary shared phases.
- `src/phase_dp.py`: candidate-time reduction, factor construction, induced-width
  checking, exact max-sum elimination, and maximizing-assignment reconstruction.
- `proofs/core.md`: independent-window service-clock theorem, exact capacities,
  checking/sweep invariants, private-cap admission, general max-affine/LP design,
  a general active-cut optimum certificate, the implemented two-tenant
  specialization, calendar corollary, refinement monotonicity, and negative
  controls.
- `proofs/correlated-phases.md`: exact width-parameterized phase algorithm,
  reconstruction proof, and the four-epoch MAX-CUT reduction proving OVERLOAD
  NP-complete and SAFE coNP-complete.

The repository does **not** contain a general-tenant pooled LP solver or producer
for the general KKT multipliers. That result is a written characterization. The
phase solver is exact but exponential in supplied induced width; deterministic
min-fill is a heuristic for finding an order, not an optimal-treewidth solver.

## Frozen finite evidence

All consumed synthetic inputs are in `inputs/`; inclusion rules are frozen in
`inputs/validation-plan.json`. Counts describe mathematical configurations, not
independent production workloads.

| Evidence | Instances | Explicit checks |
|---|---:|---:|
| Four-burst independent-window pilot | 96 | 1,902 fluid + 1,902 calendar traces |
| Three-burst independent-window domain | 20,736 | 96,000 fluid + 288,000 calendar traces |
| Four-burst allocation pilot | 80 | 1,910 release assignments |
| Two-burst allocation domain | 432 | 1,200 release assignments |
| Private-cap combinations | 3,888 | 3,888 decisions |
| All labeled simple graphs on 1--4 vertices | 75 | 1,098 phase assignments |
| Width-one path stress case | 1 (64 vertices) | 2,020 factor entries, exact peak 316 |
| Test contract | 33 methods | 18 core + 15 additional; all pass |
| Sparse storage family | 6 sizes | `n=m=8,...,256`; exact values agree, `2m` event entries |

The bounded window producer, recurrence, busy-interval formula, integer-release
oracle, and replayed clipped witness agree. Calendar prefix clocks agree with a
slot loop. Allocation objective and smallest optimizer agree with the independent
actual-trace oracle. For phases, exhaustive optimization agrees with variable
elimination on every small graph; the reconstructed assignment replays to the
reported maximum. The observed deterministic min-fill width histogram is
`{0:4, 1:44, 2:26, 3:1}`.

`results/controls.json` retains five model-separating controls: endpoint corners
can understate by factor `m`; marginal independent windows can overstate a
correlated shift by factor `m`; sums of private peaks can overstate a pool by
factor `n`; equal average calendar quotas can require different buffers; and a
fixed reservation is not interchangeable with work-conserving aggregate
service. It also retains the separate sparse-storage audit. The reference
checker uses `O(n+m)` working entries and `O(nm)` arithmetic; choosing to retain
all full endpoint rows is explicitly a `Theta(nm)` output-space mode.

## Figure data and evidence traceability

```sh
python3 export_results.py --output /tmp/incast-figures
```

This regenerates `summary.json`, `corners.csv`, and `allocation.csv` without
rerunning validation. The CSVs contain exact terminating plot coordinates; all
algorithms use integer or rational arithmetic.

`claim_evidence_ledger.csv` maps each manuscript-level claim to its proof, code,
input, result, and maturity. `external_resources.csv` records scholarly and
workflow sources, access mode, licenses, and whether anything was integrated.
`literature.md` contains the completed 12 TPDS + 5 influential + 5 adjacent
full-paper calibration and the narrower closest-work comparison. No copyrighted
paper PDF, third-party code, model weight, hidden cache, or private input is
bundled or modified.

Original code, synthetic data, and proof documentation are covered by `LICENSE`; consulted-resource boundaries are in `licenses/NOTICE.md`.
