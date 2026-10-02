# Literature calibration and contribution boundary

Access date for this record: 2026-09-15. No scholarly PDF is bundled. Full-paper
calibration here means a cover-to-cover structural pass over the complete paper
and focused reading of the abstract, introduction, model/mechanism, central
argument, evaluation, limitations/conclusion, figures/tables, and references.
It is a writing and novelty-calibration activity, not an independent replication
of every theorem or experiment. Exact technical premises used by this project
received a narrower equation/proof-level check, identified below. Metadata-only
search results were not counted.

The completed calibration set contains **12 TPDS full papers, 5 influential full
papers, and 5 adjacent-venue full papers**, with no overlap between the three
sets. No award or distinguished-paper status is asserted. The set is relevance
first: TPDS samples calibrate journal narrative and evidence; influential papers
calibrate datacenter-systems exposition; adjacent papers pressure-test the
closest buffer-management boundary.

## Targeted primary-source bibliography check

A separate identity pass on 2026-09-25 checked the formal title and complete
author list for `expresspass`, `phost`, `presto`, `letflow`, and `sincronia`
against the supplied author/publisher sources. The exact records are retained in
`reference-identity.md`; `references.bib` contains no abbreviated `and others`
author list for these entries. This pass validates citation identity, not the
project's mathematical claims.

## Closest technical premises and negative novelty findings

- **DCTCP** supplies the historical reactive ancestor. Its threshold marking,
  proportional response, analysis, and experiments address persistent queues and
  congestion reaction; they do not provide the finite-schedule robust capacity
  theorem here. The paper's discussion of first-burst limitations is context,
  not a proof of this work.
- **Network calculus** supplies standard cumulative-arrival/service and
  busy-interval identities. Those identities are attributed. The contribution
  claimed here is the common attaining release vector for a finite Cartesian
  window set, its exact checker/producer, and the timing-language complexity
  boundary—not the underlying min-plus calculus.
- **ABM, Traffic-Aware Buffer Management, PayDebt, P-PFC, TOP, Reverie,
  Credence, and Occamy** already establish broad proactive, predictive,
  preemptive, or traffic-aware queue/buffer control. Therefore the manuscript
  does not claim to be the first proactive incast or predictable-buffer scheme.
- **Incast-Free MoE Rate-Based Scheduling** already gives a recent proactive
  rate-scheduling treatment of collective traffic. Its traffic-matrix scheduler
  and simulation evidence differ from a proof-carrying robust memory admission
  rule, but they preclude novelty based merely on “rate allocation before an
  incast.”
- **Bouillard and Thierry** establish worst-case backlog hardness in feed-forward
  networks. The present reduction instead keeps per-tenant service exogenous and
  encodes coupling only through binary release phases. This is a precise model
  distinction, not a claim that hardness of deterministic queue bounds is new.
- **Garey, Johnson, and Stockmeyer** provide the external premise that simple
  unweighted MAX-CUT is NP-complete. The four-epoch queue construction and its
  global-peak identity are proved in this project.

The surviving, deliberately narrow delta is: for a declared finite timing
uncertainty set and release-oblivious reserved service, compute an exact minimum
memory threshold plus a checkable attaining witness; characterize when this is
near-linear (independent windows), width-parameterized (binary phase factors),
or NP/coNP-hard (unrestricted phase interaction). The calibration did not reveal
this exact theorem/algorithm/complexity combination. That is a reasoned research
position, not a guarantee of novelty or acceptance.

## Twelve TPDS full-paper calibrations

| TPDS paper | Problem and organizing principle | Central argument and evidence pattern | Implication for this manuscript |
|---|---|---|---|
| Wang et al., **Luopan: Sampling-Based Load Balancing in Data Center Networks**, TPDS 30(1), 2019, DOI 10.1109/TPDS.2018.2858815 | Make useful routing decisions with incomplete traffic state; sampling is the general principle | Model/design precede system realization and comparative evaluation; figures move from intuition to sensitivity and throughput | Calibrates a systems narrative but concerns path selection, not an exact memory threshold |
| Liu et al., **ScaleFlux: Efficient Stateful Scaling in NFV**, TPDS 33(12), 2022, DOI 10.1109/TPDS.2022.3204209 | Scale stateful functions without losing correctness or efficiency | Explicit design invariants, implementation, multi-workload evaluation, and limitations | Reinforces separating a checkable invariant from unimplemented deployment components |
| Feng, Xu, and Li, **An Alternating Direction Method Approach to Cloud Traffic Management**, TPDS 28(8), 2017, DOI 10.1109/TPDS.2017.2658620 | Decompose a coupled resource-allocation problem | Optimization formulation, convergence/algorithm argument, then trace/numerical evaluation | Calibrates the LP/KKT story; familiar optimization machinery is not itself the novelty |
| Wang et al., **Large-Scale Measurements and Prediction of DC-WAN Traffic**, TPDS 34(5), 2023, DOI 10.1109/TPDS.2023.3245092 | Establish empirical regularities before building prediction | Measurement methodology, dataset characterization, prediction, and validation | Shows what real workload evidence would require; this paper makes no workload-representativeness claim |
| Luo et al., **Towards Practical and Near-Optimal Coflow Scheduling for Data Center Networks**, TPDS 27(11), 2016, DOI 10.1109/TPDS.2016.2525767 | Make coflow scheduling implementable while retaining approximation quality | Scheduling formulation, algorithmic bound/heuristic, simulations and practical discussion | Collective completion scheduling is adjacent but does not answer robust per-queue memory admission |
| De Pellegrini et al., **Fair Coflow Scheduling via Controlled Slowdown**, TPDS 35(12), 2024, DOI 10.1109/TPDS.2024.3446188 | Express fairness by controlled slowdown rather than raw completion time | Formal objective, scheduling method, analytical properties, and comparative experiments | Motivates precise objective language; this manuscript claims neither fairness nor completion-time optimality |
| Brun and Prabhu, **Performance Bounds for Priority-Based Stochastic Coflow Scheduling**, TPDS early access, 2026, DOI 10.1109/TPDS.2026.3690856 | Schedule unknown random coflow sizes with a priority policy | Stochastic model, polyhedral relaxation, approximation bounds, and numerical study | Contrasts distributional expectation with worst-case finite release uncertainty |
| Liu et al., **PayDebt: Reduce Buffer Occupancy Under Bursty Traffic on Large Clusters**, TPDS 33(12), 2022, DOI 10.1109/TPDS.2022.3202504 | Actively repay congestion “debt” after bursts to reduce occupancy | Mechanism design, implementation path, cluster-scale evaluation, and parameter sensitivity | Closest operational buffer paper; it controls queue evolution but does not issue the exact offline capacity/witness certificate studied here |
| Tian et al., **P-PFC: Reducing Tail Latency with Predictive PFC in Lossless Data Center Networks**, TPDS 31(6), 2020, DOI 10.1109/TPDS.2020.2969182 | Predict impending congestion before conventional PFC reacts | Prediction/control mechanism plus lossless-network evaluation | Precludes a broad “predict before overflow” novelty claim; prediction error and protocol dynamics are outside this paper |
| Liu et al., **Exploring Token-Oriented In-Network Prioritization in Datacenter Networks**, TPDS 31(5), 2020, DOI 10.1109/TPDS.2019.2958899 | Coordinate packet prioritization with in-network tokens | Architecture/protocol, implementation, and workload evaluation | Demonstrates the evidence needed for an operational prioritization claim, which is not made here |
| Chen et al., **Swing: Providing Long-Range Lossless RDMA via PFC-Relay**, TPDS 34(1), 2023, DOI 10.1109/TPDS.2022.3215517 | Extend lossless behavior beyond one PFC domain | Protocol construction, correctness intuition, implementation and performance evidence | Shows that multi-hop losslessness needs protocol/topology evidence; single-pool certificates do not imply it |
| Ruan et al., **On the Synchronization Bottleneck of OpenStack Swift-Like Cloud Storage Systems**, TPDS 29(9), 2018, DOI 10.1109/TPDS.2018.2810179 | Explain synchronized distributed-stage bottlenecks | System diagnosis, model/measurements, design intervention, and evaluation | Supports the importance of correlated stage timing while not supplying the phase-factor queue theorem |

### TPDS pattern extracted

The strongest shared pattern is: motivate a concrete distributed-systems failure;
state a general principle; make the model, objective, and trust boundary explicit;
provide either a formal argument or an implementable mechanism; connect it to a
real operational setting; evaluate the evidence actually needed by the claim;
then delimit what remains. The final paper follows that sequence in eight sections.
Its figures have distinct roles: one counterexample/intuition diagram, one
optimization geometry plot, and one exhaustive negative-control plot. Tables
state model boundaries, a running certificate, and finite validation coverage.

## Five influential full-paper calibrations

These are selected for canonical datacenter design and exposition patterns; no
award status is asserted.

| Paper | Principle and evidence | Narrative lesson used here |
|---|---|---|
| Alizadeh et al., **DCTCP**, SIGCOMM 2010, DOI 10.1145/1851182.1851192 | Shallow queues through ECN thresholding and proportional reaction; analysis, simulation, and commodity-switch experiments | Start from the concrete failure and distinguish control-loop behavior from the first unreacted burst |
| Alizadeh et al., **pFabric**, SIGCOMM 2013 | Minimal in-network prioritization can approximate ideal flow completion; idealized analysis plus simulation | Keep the core principle simple, but avoid transferring ideal-model results to an untested implementation |
| Chowdhury, Zhong, and Stoica, **Varys**, SIGCOMM 2014 | Coflow-aware scheduling improves collective completion; centralized algorithm and cluster evidence | Explain why individual-flow summaries lose application-level coordination; here, private peaks likewise lose cross-tenant phase |
| Perry et al., **Fastpass**, SIGCOMM 2014 | Centralized per-packet scheduling can suppress queues; architecture, implementation, and experiments | A planning-stage decision can be useful, but operational claims require scheduler and hardware evidence absent here |
| Montazeri et al., **Homa**, SIGCOMM 2018 | Receiver-driven scheduling and priorities target low tail latency; design plus implementation/evaluation | Separate the semantic contract from transport enforcement and do not infer FCT from queue safety |

## Five adjacent-venue full-paper calibrations

| Paper | Closest contribution | Boundary forced on this manuscript |
|---|---|---|
| Addanki et al., **ABM: Active Buffer Management in Datacenters**, SIGCOMM 2022, DOI 10.1145/3544216.3544252 | Active shared-buffer thresholds, isolation, drain-time and burst-absorption reasoning | “Predictable/active buffer management” is prior art; the distinct object here is an exact declaration-specific threshold and witness |
| Huang, Wang, and Cui, **Traffic-Aware Buffer Management in Shared Memory Switches**, IEEE/ACM TON 30(6), 2022, DOI 10.1109/TNET.2022.3173930 | Traffic-aware allocation of shared switch memory | Dynamic traffic classification/allocation is not the same as robust offline capacity under a fixed timing set |
| Addanki et al., **Reverie**, NSDI 2024 | Low-pass-filter buffer sharing for mixed RDMA/TCP traffic | Real mixed-transport behavior and filter tuning are not modeled by exogenous per-tenant service clocks |
| Addanki, Pacut, and Schmid, **Credence**, NSDI 2024 | ML predictions augment buffer sharing | Predictive accuracy and online adaptation are different evidence obligations; no model or API is used here |
| Shan et al., **Occamy**, EuroSys 2025, DOI 10.1145/3689031.3717495 | Preemptive on-chip shared-memory buffer management | Hardware preemption and switch implementation can reduce occupancy, but do not subsume the robust timing-certificate theorem |

## Other foundations and recent context

Le Boudec and Thiran, Chang, Cruz, and Parekh--Gallager provide deterministic
queue/service foundations. Bertsimas--Sim provides robust-optimization context.
Dechter, Koller--Friedman, Bodlaender, and Arnborg--Corneil--Proskurowski support
the factor-elimination/treewidth vocabulary and complexity boundary. The recent
Incast-Free MoE preprint is cited as current collective-scheduling context, not
as peer-reviewed deployment evidence. SIRD and BFC are cited to avoid presenting
sender/receiver scheduling or backpressure as new.

## Contribution and non-claim ledger from the comparison

Supported paper-level claim:

> Within the declared single-output reserved-service model, independent release
> windows admit an exact common fixed-time extremizer and checkable minimum
> capacity; binary shared phases admit exact width-parameterized elimination and
> become NP/coNP-hard at unrestricted interaction width.

Claims deliberately removed or rejected:

- first proactive incast prevention;
- first bounded-buffer or predictive queue mechanism;
- exactness for feedback-dependent or work-conserving service;
- production collective or switch performance;
- general multi-hop composition;
- general-tenant pooled solver implementation;
- polynomial safety certificates for unrestricted phases;
- proof that the work will be accepted or is independently novel.

## Venue and policy workflow status

The supplied `IEEEtran.cls` and `IEEEtran.bst` were inspected and kept unmodified.
The official TPDS author-information page returned a script shell rather than
usable static policy content, and the template selector did not resolve during
this run. Therefore the paper satisfies the user's internal exactly-12-page
contract, but live submission length, anonymity, supplement, and portal fields
remain an external-use recheck. IEEE's first-party AI-content guidance was
accessible; the manuscript accordingly discloses substantive system assistance
rather than describing it as grammar-only editing. No submission, account action,
repository URL, authorship approval, or policy exception is asserted.
