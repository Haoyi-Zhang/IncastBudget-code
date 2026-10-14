"""One regression method over the existing six sparse-control sizes."""
import json,sys,unittest
from pathlib import Path
from collections import defaultdict
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import queues as q


class ReplayStorageTests(unittest.TestCase):
    def test_sparse_arrival_storage(self):
        rows=json.loads((ROOT/'results/controls.json').read_text())['storage_scaling']['rows']
        for row in rows:
            n=row['n']
            with self.subTest(n=n):
                maps=[]
                def capture(factory):
                    value=defaultdict(factory);maps.append(value);return value
                with patch.object(q,'defaultdict',capture):
                    result=q.simulate([q.Burst(i,2*i,2*i,1) for i in range(n)],[q.F(1)]*n,list(range(0,2*n,2)))
                self.assertEqual(result['pool'],1);self.assertEqual(result['private'],[q.F(1)]*n)
                self.assertEqual(sum(len(v) for d in maps for v in d.values()),n)
if __name__=='__main__':unittest.main()
