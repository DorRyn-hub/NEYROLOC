from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "NEYROLOCK_5"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication
except (ImportError, ModuleNotFoundError):
    PYSIDE_AVAILABLE = False
else:
    from backends.base import Message
    from ui.main_window import GenerateWorker

    PYSIDE_AVAILABLE = True


@unittest.skipUnless(PYSIDE_AVAILABLE, "PySide6 is required for worker tests")
class GenerateWorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_empty_backend_stream_emits_failure_not_success(self) -> None:
        class EmptyBackend:
            def generate(self, messages, temperature):
                return iter(())

            def cancel(self) -> None:
                pass

        worker = GenerateWorker(
            EmptyBackend(),
            [Message("user", "Привет")],
            0.7,
        )
        failures: list[str] = []
        successes: list[bool] = []
        worker.failed.connect(failures.append)
        worker.finishedOk.connect(lambda: successes.append(True))

        worker.run()

        self.assertEqual(successes, [])
        self.assertEqual(len(failures), 1)
        self.assertIn("без ответа", failures[0])

    def test_real_stream_records_generation_timing(self) -> None:
        class MeasuredBackend:
            def __init__(self) -> None:
                self.recorded: tuple[str, float] | None = None

            def generate(self, messages, temperature):
                yield "Настоящий "
                yield "ответ"

            def record_generation(self, text: str, elapsed: float) -> None:
                self.recorded = (text, elapsed)

            def cancel(self) -> None:
                pass

        backend = MeasuredBackend()
        worker = GenerateWorker(
            backend,
            [Message("user", "Привет")],
            0.7,
        )
        successes: list[bool] = []
        worker.finishedOk.connect(lambda: successes.append(True))

        worker.run()

        self.assertEqual(successes, [True])
        self.assertIsNotNone(backend.recorded)
        self.assertEqual(backend.recorded[0], "Настоящий ответ")
        self.assertGreater(backend.recorded[1], 0)


if __name__ == "__main__":
    unittest.main()
