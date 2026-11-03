"""Memory probing must remain optional on platforms without Unix resource."""

import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / "NEYROLOCK_5/core/runtime_metrics.py"


class RuntimeMetricsTests(unittest.TestCase):
    def load_metrics(self):
        spec = importlib.util.spec_from_file_location("runtime_metrics_fixture", PATH)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {spec.name: module}):
            spec.loader.exec_module(module)
        return module

    def test_windows_without_optional_probes_can_import_and_render(self):
        with patch.dict(sys.modules, {"resource": None, "psutil": None}):
            module = self.load_metrics()
            usage = module.process_memory_usage()
        self.assertIsNone(usage.bytes)
        self.assertEqual(module.format_memory_size(usage.bytes), "—")

    def test_psutil_reports_current_rss_without_resource(self):
        process = SimpleNamespace(memory_info=lambda: SimpleNamespace(rss=64 * 1024**2))
        probe = SimpleNamespace(Process=lambda pid: process)
        with patch.dict(sys.modules, {"resource": None, "psutil": probe}):
            usage = self.load_metrics().process_memory_usage()
        self.assertEqual(usage.bytes, 64 * 1024**2)
        self.assertFalse(usage.is_peak)


if __name__ == "__main__":
    unittest.main()
