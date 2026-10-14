"""The public check path must replay its advertised attaining release vector."""
from contextlib import redirect_stderr, redirect_stdout
from fractions import Fraction
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import queue_certificate


class CheckWitnessTests(TestCase):
    def test_check_replays_attaining_witness(self):
        argv = ["queue_certificate.py", "check", str(ROOT / "inputs" / "example.json")]
        with patch.object(sys, "argv", argv), redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            self.assertEqual(queue_certificate.main(), 0)

    def test_check_rejects_failed_replay(self):
        argv = ["queue_certificate.py", "check", str(ROOT / "inputs" / "example.json")]
        with (patch.object(sys, "argv", argv),
              patch.object(queue_certificate, "simulate", return_value={"pool": Fraction(-1)}),
              redirect_stdout(StringIO()), redirect_stderr(StringIO())):
            self.assertEqual(queue_certificate.main(), 2)

    def test_failed_replay_does_not_publish_rows(self):
        with TemporaryDirectory() as tmp:
            rows = Path(tmp) / "rows.jsonl"
            argv = ["queue_certificate.py", "check", str(ROOT / "inputs" / "example.json"),
                    "--rows-output", str(rows)]
            with (patch.object(sys, "argv", argv),
                  patch.object(queue_certificate, "simulate", return_value={"pool": Fraction(-1)}),
                  redirect_stdout(StringIO()), redirect_stderr(StringIO())):
                self.assertEqual(queue_certificate.main(), 2)
            self.assertFalse(rows.exists())
