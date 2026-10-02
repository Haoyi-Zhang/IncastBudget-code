from __future__ import annotations
import unittest
from fractions import Fraction as F
from itertools import product

from independent_oracles.affine_minimax import AffinePiece, MinimaxCertificate, solve_exact_minimax, verify_minimax_certificate
from independent_oracles.finite_domain_ve import Factor, brute_force_max, variable_elimination_max, verify_assignment


class AdversarialExactnessTests(unittest.TestCase):
    def test_large_denominators_remain_exact(self):
        q=104729
        pieces=[AffinePiece.make(F(11,q),[F(-7,q),F(13,q)]),
                AffinePiece.make(F(17,q),[F(5,q),F(-19,q)]),
                AffinePiece.make(F(-3,q),[F(23,q),F(2,q)])]
        cert=solve_exact_minimax(pieces,[F(-2,q),F(-1,q)],[F(5,q),F(4,q)],F(3,q))
        ok,err=verify_minimax_certificate(pieces,[F(-2,q),F(-1,q)],[F(5,q),F(4,q)],F(3,q),cert)
        self.assertTrue(ok,err)
        self.assertIsInstance(cert.value,F)

    def test_boundary_only_optimum(self):
        pieces=[AffinePiece.make(0,[1,0]),AffinePiece.make(100,[0,-1])]
        cert=solve_exact_minimax(pieces,[0,0],[1,9],9)
        self.assertEqual(sum(cert.rates),F(9))
        self.assertTrue(verify_minimax_certificate(pieces,[0,0],[1,9],9,cert)[0])

    def test_wrong_bound_multiplier_rejected(self):
        pieces=[AffinePiece.make(5,[-1,0]),AffinePiece.make(5,[0,-1])]
        c=solve_exact_minimax(pieces,[0,0],[3,3],3)
        bad=MinimaxCertificate(c.rates,c.value,c.piece_multipliers,(F(1),F(0)),c.upper_multipliers,c.equality_multiplier)
        self.assertFalse(verify_minimax_certificate(pieces,[0,0],[3,3],3,bad)[0])

    def test_disconnected_and_isolated_phase_variables(self):
        domains={'a':(0,1),'b':(0,1,2),'c':('x','y')}
        f=Factor(('a','b'),{(a,b):F(2*a-b) for a in domains['a'] for b in domains['b']})
        brute=brute_force_max(domains,[f])
        trace=variable_elimination_max(domains,[f],('c','a','b'))
        self.assertEqual(brute[0],trace.objective)
        self.assertTrue(verify_assignment(domains,[f],trace.assignment,trace.objective))

    def test_incomplete_factor_table_rejected(self):
        domains={'x':(0,1),'y':(0,1)}
        bad=Factor(('x','y'),{(0,0):F(0)})
        with self.assertRaises(ValueError): brute_force_max(domains,[bad])
        with self.assertRaises(ValueError): variable_elimination_max(domains,[bad],('x','y'))

    def test_order_validation(self):
        domains={'x':(0,1),'y':(0,1)}
        f=Factor(('x',),{(0,):F(0),(1,):F(1)})
        for order in [('x',),('x','x'),('x','z')]:
            with self.assertRaises(ValueError): variable_elimination_max(domains,[f],order)

    def test_negative_factor_scores(self):
        domains={i:(0,1,2) for i in range(4)}
        fs=[]
        for i in range(3):
            fs.append(Factor((i,i+1),{(x,y):F(-abs(x-y)-i,3) for x in domains[i] for y in domains[i+1]}))
        b,a=brute_force_max(domains,fs); t=variable_elimination_max(domains,fs,(0,1,2,3))
        self.assertEqual(b,t.objective)
        self.assertTrue(verify_assignment(domains,fs,t.assignment,b))

if __name__=='__main__': unittest.main()
