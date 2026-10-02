from __future__ import annotations
import random
import unittest
from fractions import Fraction as F
from itertools import product

from independent_oracles.affine_minimax import (
    AffinePiece, MinimaxCertificate, solve_exact_minimax,
    verify_minimax_certificate,
)
from independent_oracles.finite_domain_ve import (
    Factor, brute_force_max, variable_elimination_max, verify_assignment,
)


class ExactAffineMinimaxTests(unittest.TestCase):
    def test_three_tenant_fractional_certificate(self):
        pieces = [
            AffinePiece.make(7, [-1, 0, 0], "tenant-0"),
            AffinePiece.make(8, [0, -2, 0], "tenant-1"),
            AffinePiece.make(6, [0, 0, -1], "tenant-2"),
            AffinePiece.make(F(21,2), [-1,-1,-1], "pooled"),
        ]
        c = solve_exact_minimax(pieces, [F(1,3)]*3, [F(5)]*3, F(6))
        ok, errors = verify_minimax_certificate(pieces, [F(1,3)]*3, [F(5)]*3, F(6), c)
        self.assertTrue(ok, errors)

    def test_degenerate_duplicate_pieces(self):
        pieces = [AffinePiece.make(3, [-1,-1]), AffinePiece.make(3, [-1,-1]),
                  AffinePiece.make(5, [-2,0]), AffinePiece.make(5,[0,-2])]
        c = solve_exact_minimax(pieces, [0,0], [4,4], 4)
        self.assertTrue(verify_minimax_certificate(pieces,[0,0],[4,4],4,c)[0])

    def test_infeasible_capacity_rejected(self):
        with self.assertRaises(ValueError):
            solve_exact_minimax([AffinePiece.make(0,[1,1])], [2,2], [3,3], 1)

    def test_mutated_certificates_rejected(self):
        pieces = [AffinePiece.make(4,[-1,0]), AffinePiece.make(4,[0,-1])]
        c = solve_exact_minimax(pieces,[0,0],[4,4],4)
        variants = [
            MinimaxCertificate((c.rates[0]+F(1,7),c.rates[1]),c.value,c.piece_multipliers,c.lower_multipliers,c.upper_multipliers,c.equality_multiplier),
            MinimaxCertificate(c.rates,c.value+1,c.piece_multipliers,c.lower_multipliers,c.upper_multipliers,c.equality_multiplier),
            MinimaxCertificate(c.rates,c.value,tuple(-x for x in c.piece_multipliers),c.lower_multipliers,c.upper_multipliers,c.equality_multiplier),
            MinimaxCertificate(c.rates,c.value,c.piece_multipliers,c.lower_multipliers,c.upper_multipliers,c.equality_multiplier+1),
        ]
        for bad in variants:
            self.assertFalse(verify_minimax_certificate(pieces,[0,0],[4,4],4,bad)[0])

    def test_random_exact_kkt_and_dense_grid_lower_bound(self):
        rng = random.Random(8128)
        for n in (2,3,4):
            for _ in range(24):
                cap = F(n+2)
                pieces = []
                for k in range(n+3):
                    pieces.append(AffinePiece.make(rng.randint(0,9),
                        [F(rng.randint(-3,1), rng.choice((1,2,3))) for _ in range(n)], str(k)))
                cert = solve_exact_minimax(pieces,[F(0)]*n,[cap]*n,cap)
                self.assertTrue(verify_minimax_certificate(pieces,[0]*n,[cap]*n,cap,cert)[0])
                # A feasible grid can only upper-bound the exact minimum.
                if n == 2:
                    vals=[]
                    for j in range(49):
                        x=(cap*F(j,48),cap*(1-F(j,48)))
                        vals.append(max(p.intercept+sum(a*b for a,b in zip(p.slope,x)) for p in pieces))
                    self.assertLessEqual(cert.value,min(vals))


class FiniteDomainVETests(unittest.TestCase):
    def _random_instance(self, rng, n, domain_size):
        domains={f"x{i}":tuple(range(domain_size)) for i in range(n)}
        factors=[]
        for i in range(n):
            scope=(f"x{i}", f"x{(i+1)%n}") if n>1 else ("x0",)
            table={vals:F(rng.randint(-5,8),rng.choice((1,2,3)))
                   for vals in product(*(domains[v] for v in scope))}
            factors.append(Factor(scope,table,f"f{i}"))
        return domains,factors

    def test_binary_and_ternary_domains_against_bruteforce(self):
        rng=random.Random(1729)
        for domain_size in (2,3,4):
            for n in range(1,7):
                for _ in range(8):
                    domains,factors=self._random_instance(rng,n,domain_size)
                    bval,barg=brute_force_max(domains,factors)
                    trace=variable_elimination_max(domains,factors,tuple(domains))
                    self.assertEqual(bval,trace.objective)
                    self.assertTrue(verify_assignment(domains,factors,trace.assignment,bval))

    def test_maxcut_special_case(self):
        # Pairwise disagreement factors are exactly an unweighted MAX-CUT objective.
        domains={i:(0,1) for i in range(5)}
        edges=[(0,1),(1,2),(2,3),(3,4),(4,0),(0,2)]
        factors=[Factor((u,v),{(a,b):F(a!=b) for a in (0,1) for b in (0,1)},f"e{u}-{v}") for u,v in edges]
        val,a=brute_force_max(domains,factors)
        trace=variable_elimination_max(domains,factors,(0,1,2,3,4))
        self.assertEqual(val,trace.objective)
        self.assertEqual(val,sum(F(a[u]!=a[v]) for u,v in edges))

    def test_bad_witness_rejected(self):
        domains={'x':(0,1),'y':(0,1,2)}
        f=Factor(('x','y'),{(x,y):F(3*x-y) for x in domains['x'] for y in domains['y']})
        val,a=brute_force_max(domains,[f])
        self.assertTrue(verify_assignment(domains,[f],a,val))
        bad=dict(a); bad['x']=1-bad['x']
        self.assertFalse(verify_assignment(domains,[f],bad,val))
        self.assertFalse(verify_assignment(domains,[f],a,val+1))


if __name__ == '__main__':
    unittest.main()
