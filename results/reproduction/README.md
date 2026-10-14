# Current local finite evidence

These are measurements of the exact Python queue models, not traffic from a
network adapter, switch, remote CPU or production collective. Inputs remain the
authored configurations in `inputs/`; no artificial sample is labeled native.
`host.json` records the actual local CIM/Python observations.

`normal/` and `optimized/` are complete serial invocations of `reproduce.py
--portable --output NEW_PATH`, with and without `-O`. Each executes the same 17
validation jobs, original 19+15 test contract, separate 3+4+1 regressions, three
certificate actions and three derived comparisons. `resumed/` records the same
work in first/second parts, not another scientific population. All scientific
fields equal the shipped root records after removing only `measurement`; the
three derived files match byte-for-byte. Run logs and failed attempts are
private audit material, not scientific inputs.

Only explicit portable execution was tested on this Windows host. The default
POSIX guard branch remains unexecuted here. Wall timeout is 40 seconds per direct
child. CPU/address-space limits and affinity are omitted explicitly, and missing
child-total CPU/RSS are null. Worker process CPU is measured, not inferred from
the historical Linux runs. One serial ordinary run takes 20.5580654 seconds and
the optimized run takes 27.0831074 seconds; do not interpret these as a controlled
cross-mode speed comparison. Input counts and unique test methods are not doubled.

`path-costs-{normal,optimized}.json` measure one serial paired pass per mode on
the existing four input files, after code repair and after the campaign processes
finished. Intermediate measurements and one failed measurement-code attempt
remain in the private audit. Selection of these records is by final code state
and serial execution, not by favorable ratios. Both identifiers receive the same
original instance; no certificate is supplied to either. Production pays its
internal and serialized-consumer certificate checks. A candidate-verifier total
is separate and excludes candidate preparation, so it is not identification.
Timed scope includes parsing, object conversion, arithmetic/replay, and output
encoding, but excludes interpreter startup and disk I/O. CPU ticks can be coarse;
a reported zero process-CPU tick is not zero elapsed work. Numerical outputs and
serialized digests agree. Window costs and the two-burst allocation costs are
negative for the checked path; only the four-burst allocation pilot favors it.

`replay-storage-before.json`, `replay-storage-after.json` and
`replay-storage-after-optimized.json` use the six existing sparse-control sizes,
not a new matrix. The before measurement preceded the `queues.simulate` repair;
source-byte bindings are in `provenance.json`. Each size is one traced replay,
with inputs constructed before tracing. Entry counts and Python traced-byte
peaks are different metrics. At n=256 the arrival entries drop 65,536 to 256 and
traced peak drops 593,912 to 112,512 bytes; n=8 and16 have higher dictionary-byte
cost after repair. All original root and `results/current/` bytes are preserved.
These finite records neither establish novelty nor satisfy deployment/acceptance
obligations.
