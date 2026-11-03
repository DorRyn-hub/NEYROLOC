"""Run the real Windows GUI with a local model without touching user state.

The image and report can contain synthetic model output; review before sharing.
This verifies CPU inference and native Qt rendering, not model answer quality.
"""

import argparse
import json
import tempfile
import os
import sys
import time
import traceback
from unittest.mock import patch
from pathlib import Path
parser = argparse.ArgumentParser(description='Verify native Windows GUI + CPU LocalGGUFBackend with an isolated temporary profile.')
parser.add_argument('--model', type=Path, required=True, help='Existing local GGUF file')
parser.add_argument('--output', type=Path, required=True, help='Private directory for JSON result and window screenshot')
args = parser.parse_args()
if sys.platform != 'win32':
    parser.error('This check must run on Windows in an interactive desktop session.')
model_path = args.model.expanduser().resolve()
if not model_path.is_file():
    parser.error('GGUF file does not exist.')
output = args.output.expanduser().resolve()
output.mkdir(parents=True, exist_ok=True)
root = Path(__file__).resolve().parents[1]
isolated_profile = tempfile.TemporaryDirectory(prefix='neyroloc-smoke-')
os.environ['QT_QPA_PLATFORM'] = 'windows'
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / 'NEYROLOCK_5'))
result = {'platform': sys.platform, 'scope': 'interactive Windows console, native Qt windows plugin, isolated profile, CPU GGUF'}
try:
    with patch.object(Path, "home", return_value=Path(isolated_profile.name)):
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication
        import main
        from core.runtime_metrics import process_memory_usage
        original = main.MainWindow
        start = time.monotonic()
        window = None
        sent = False

        def finish(error=None):
            if error:
                result['ok'] = False
                result['error'] = str(error)
            result['elapsed_seconds'] = round(time.monotonic() - start, 2)
            (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
            if window:
                window.close()
            QApplication.instance().quit()

        def poll():
            global sent
            try:
                if time.monotonic() - start > 90:
                    raise RuntimeError('Native GUI model/generation check timed out')
                if window._model_ready and not sent:
                    sent = True
                    window._navigate('chat')
                    window.chat._input.setPlainText('Reply with the single word READY.')
                    window.chat._on_submit()
                if sent and window._worker is None and window.session.messages and window.session.messages[-1].role == 'assistant':
                    answer = window.session.messages[-1].content
                    assert answer.strip(), 'Empty local response'
                    assert QApplication.instance().font().family() == 'Onest'
                    assert process_memory_usage().bytes > 0
                    result.update(ok=True, font='Onest', memory_probe='current RSS', answer=answer, model=model_path.name, backend='LocalGGUFBackend', gpu_layers=0)
                    assert window.grab().save(str(output / 'window.png')), 'Could not save window screenshot'
                    finish()
                    return
                QTimer.singleShot(100, poll)
            except BaseException:
                finish(traceback.format_exc())

        class NativeWindow(original):
            def show(self):
                global window
                super().show()
                window = self
                self._choose_backend('local_gguf')
                self.sidebar.set_config_values({'model_path': str(model_path), 'n_ctx': '1024', 'n_gpu_layers': '0'})
                self.config.set_last_model('local_gguf', model_path.name)
                QTimer.singleShot(200, self._on_apply_clicked)
                QTimer.singleShot(500, poll)

        main.MainWindow = NativeWindow
        try:
            main.main()
        except BaseException:
            result['error'] = traceback.format_exc()
            (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
            raise

        raise SystemExit(0 if result.get('ok') else 1)
finally:
    isolated_profile.cleanup()
