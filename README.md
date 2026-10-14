# incast-safe-queue-budget

This standalone repository accompanies the internal manuscript **Exact
Queue-Budget Certificates for Reserved-Service Incast: Release Windows,
Correlated Phases, and Tractability**. It contains exact-rational reference
implementations, bounded independent oracles, written proofs, deterministic
inputs, tests, raw results, and claim/resource ledgers.

The artifact supports an internal research draft. It is not a claim of
peer review, switch deployment, transport performance, or external submission
readiness. General theorems are written mathematical arguments, not
proof-assistant developments; finite checks validate implementations only on
the declared domains.

## Reproduce all shipped scientific results

Use Python 3.10 or later. Default Linux execution enforces POSIX limits; Windows
requires explicit `--portable` mode. Only the standard library is required. No
package installation, network access, model API, GPU, private data, or paper
directory is used.

```sh
python3 reproduce.py --part first  --output /tmp/incast-reproduction
python3 reproduce.py --part second --output /tmp/incast-reproduction
```

The second command verifies the retained first part before resuming. The first
part runs 11 validation jobs; the second runs the remaining 6, then an explicitly
partitioned test contract of 19 core methods plus 15 additional exactness and
adversarial methods (34 total), eight separately counted regression methods
(three snapshot, four workflow, one sparse replay), three example-certificate actions, and three
derived-file comparisons. Every scientific JSON field and every derived CSV
must equal the shipped result; only timing and RSS measurements are excluded. A
count mismatch, import failure, result mismatch, timeout, or failed test exits
nonzero. Each direct child's command, stdout, and stderr are retained in the
chosen output directory, including failed attempts. The scientific workflow
uses the flat repository root, Ubuntu 24.04, and a 600-second whole-run wall
deadline; raw output is uploaded even if a gate fails.

Validation and test workers enforce a 40-second CPU limit and a 3,584 MiB
address-space limit. The parent imposes a 40-second wall timeout on every direct
child, including certificate actions and export, and runs one worker at a time.
A slower host may time out rather than silently reducing coverage. The historical
clean-archive two-part run, before the added phase regression, used 33 tests and
recorded 18.096426 parent-plus-child CPU seconds,
18.712093 seconds of active wall time, and 40,504 KiB as the largest child peak
RSS; these are original-host feasibility measurements, not measurements of the
revised suite or performance results. The historical test summary records a
Windows finite check separately.

On Windows run `python -B reproduce.py --portable --output PATH`, where PATH is
a fresh directory outside `results/`. This explicitly omits POSIX CPU/address-
space guards and affinity pinning; every direct child still has a 40-second wall
timeout. Unavailable child-total CPU and process RSS are JSON null, never zero or
inferred from another host. Worker process CPU and wall time, OS/interpreter and
guard mode are recorded. `-O` propagates to direct children; explicit scientific
failures cannot be optimized away. The two modes are not new input populations.

Reproduction refuses retained output names and any subdirectory of shipped
`results/`. Resume requires unchanged consumed source/input bytes and the same
interpreter, optimization and guard mode. Preserve failed attempts and choose a
new directory. CPU/address-space guards apply to validation and `tests/run.py`;
separate regressions, CLI actions and export have wall timeout only. The default
POSIX branch was not executed on the current Windows host. Current local records
are in `results/reproduction/`; root and `results/current/` bytes remain historical.

## Inspect one independent-window certificate

```sh
python3 src/segment_certificate.py check inputs/example.json
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

For constant reservations, `segment_certificate.py` checks the heap producer
with separately constructed per-tenant queue segments and replays the clipped
witness through actual-arrival segments. All three stages take
`O((m+n) log(m+n))` exact arithmetic/comparison operations and `O(m+n)` working
entries. It emits the same scientific thresholds and observation, without
dense endpoint history. `queue_certificate.py` retains transparent recurrence
checking and row streaming. General service-clock and calendar results keep
their stated interfaces. The proof is `proofs/segment-verifier.md`; seven
separate segment regression methods compare the complete existing 96+20,736
window inputs in ordinary and optimized modes and do not change the frozen
34-method model suite.

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
- `src/segment_check.py`: independent fixed-rate queue segments and merged
  events for exact envelope verification and concrete witness replay.
- `src/oracle.py`: exhaustive integer-release oracle and an independently
  organized actual-trace two-tenant allocation oracle.
- `src/allocation.py`: general-tenant private-cap admission and exact
  **two-tenant** pooled-rate optimization/checking.
- `src/phases.py`: construction and ordinary exact-rational event replay for
  binary shared phases, on the same parsed input domain as the phase solver.
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
| Test contract | 34 methods | 19 core + 15 additional; all pass |
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
`selected_container_entries` counts the three state vectors, sparse masses,
event-map keys and sorted endpoint index. It excludes transient q/p row payloads,
scalar temporaries and Python object overhead; it is not a peak-memory bound.
`rows_materialized: false` means the full row history is not retained, not that
no temporary row is allocated.

When neither recording nor streaming is requested, the transparent recurrence
does not construct diagnostic q/p tuple snapshots. Its recurrence, returned
values and abstract storage/row counters are unchanged. The portable independent
regression `python -B tests/snapshot_regression.py` runs explicitly in CI before
the unchanged historical 19+15 test/reproduction contract. It is a separate
finite correctness check, not a new campaign or a measured performance result.

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
## Vector figure reproduction

The retained data can be rendered with `python scripts/plot_figures.py`.
Native PDFs go to `figures/`; `--paper-figures ../paper/figures` copies identical
assets into a full project's sibling paper. Figure-only dependencies, font
discovery and portable fallbacks are documented in `scripts/README.md`.
Historical raw files and scientific thresholds are unchanged. CLI outputs must
be new distinct paths and never alias inputs or certificates; diagnostic rows
use an independently named temporary file and exclusive publication.

## Complete paths and sparse replay

`python -B scripts/measure_paths.py --output PATH` measures the existing 96 and
20,736 window inputs and 80 and 432 allocation inputs, once per path. Both window
paths return exact pool/private values plus a replayed attaining release. The
production path includes transparent checking; the direct busy-interval formula
does not call it. Both allocation identifiers get only the same original input
and return the exact value, smallest optimizer and replayed witness. Production
also pays its internal certificate check and a serialized-consumer check; the
direct actual-release vertex oracle has no supplied certificate or production
cut/hull call. A supplied-candidate verifier is timed separately: its smaller
information task is not identification and not credited as a solver speedup.
Timers include JSON decoding, object construction and output encoding, but not
interpreter startup or disk I/O. All CPU/wall records are retained; one pass per
mode is feasibility evidence, not a statistical or deployment benchmark.

`python -B scripts/measure_replay_storage.py --output PATH` measures the same six
already-shipped sparse controls, not a new generated matrix. Actual-release
replay now coalesces only nonzero tenant arrivals. It preserves numerical values
and optional row history without calling the window-envelope recurrence. The
transparent checked path is O(nm+(n+m)log(n+m)) arithmetic; unrecorded
replay uses O(n+m) entries. Python dictionary bytes can be worse at small n even
though the entry count improves. Recorded full rows still cost Theta(nm) output.
Raw storage/cost records and current measurements are in `results/reproduction/`.
All inputs are authored mathematical configurations, never native network traces.

`scripts/measure_segments.py` compares the separate segment route with the
transparent checked route on the same 96 pilot and 20,736 bounded inputs and
the six existing sparse controls. The current source-bound record is
`results/segment-costs/samples.json`; `scripts/summarize_segments.py` regenerates
its summary and paper table. Three alternating, unfiltered passes retain 48
whole-group wall/CPU observations. JSON decoding, instance construction,
producer, independent verification, witness replay and scientific-output
serialization are charged; file acquisition and interpreter startup are not.
Outputs match byte-for-byte. Segment/transparent median wall ratios are 1.447
for the pilot, 1.456 for the bounded domain and 0.033 for the 256-tenant sparse
control. Those repetitions characterize these local inputs, not a transport
benchmark or additional independent workloads.
