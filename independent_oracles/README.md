# Independent exact oracles

This package contains structurally separate small-instance validators used by
the additional 15-test suite.  `affine_minimax.py` enumerates exact rational
vertices and independently checks KKT certificates for finite affine-envelope
problems.  `finite_domain_ve.py` provides finite-domain max-sum elimination and
a complete-enumeration oracle with witness checking.  `linear_exact.py` contains
their exact rational linear algebra.

These modules are validation oracles rather than production-scale solvers.  The
standard `tests/run.py` entry point executes their eight exactness tests and
seven adversarial tests after the 19-method model suite (the original 18 methods
plus the rational-phase replay regression).

The ternary and four-valued tables in these tests stress the oracle software;
they do not expand the paper's correlated-arrival model, whose shared phase
variables remain binary.
