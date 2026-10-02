# Targeted reference identity record

This record checks only bibliographic identity against the supplied primary author/publisher sources. It does not reproduce or redistribute the papers and does not turn citation identity into evidence for this project’s theorems.

| Citation key | Formal title | Complete author list | Venue / stable record |
|---|---|---|---|
| `expresspass` | Credit-Scheduled Delay-Bounded Congestion Control for Datacenters | Inho Cho; Keon Jang; Dongsu Han | ACM SIGCOMM 2017; DOI 10.1145/3098822.3098840 |
| `phost` | pHost: Distributed Near-Optimal Datacenter Transport Over Commodity Network Fabric | Peter X. Gao; Akshay Narayan; Gautam Kumar; Rachit Agarwal; Sylvia Ratnasamy; Scott Shenker | ACM CoNEXT 2015; DOI 10.1145/2716281.2836086 |
| `presto` | Presto: Edge-based Load Balancing for Fast Datacenter Networks | Keqiang He; Eric Rozner; Kanak Agarwal; Wes Felter; John Carter; Aditya Akella | ACM SIGCOMM 2015; DOI 10.1145/2785956.2787507 |
| `letflow` | Let It Flow: Resilient Asymmetric Load Balancing with Flowlet Switching | Erico Vanini; Rong Pan; Mohammad Alizadeh; Parvin Taheri; Tom Edsall | USENIX NSDI 2017, pp. 407–420; Official USENIX paper record |
| `sincronia` | Sincronia: Near-Optimal Network Design for Coflows | Saksham Agarwal; Shijin Rajakrishnan; Akshay Narayan; Rachit Agarwal; David Shmoys; Amin Vahdat | ACM SIGCOMM 2018; DOI 10.1145/3230543.3230569 |

The manuscript uses the keys above in its transport, load-balancing, and coflow context paragraphs. No entry uses `and others`; the complete author lists are retained in `paper/references.bib`.

## Compiled consistency check

The clean BibTeX build contains 61 bibliography records and `main.tex` cites all
61 unique keys (80 citation occurrences). There are no missing or uncited keys,
duplicate keys, duplicate DOI strings, or placeholder author markers. The
compiled numbering is `expresspass` [14], `phost` [16], `presto` [21],
`letflow` [22], and `sincronia` [33]. The generated `main.bbl` retains every
author listed above and the formal titles above.
