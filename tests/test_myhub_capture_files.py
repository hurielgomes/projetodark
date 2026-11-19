import json
import tempfile
import unittest
from pathlib import Path

from myhub_llm import (
    _read_artifact_files, _valid_svg_fragment, _sidecar_json,
    criar_llm_myhub, MyHubArtifactMissingError,
)


class MyHubCaptureFileTests(unittest.TestCase):
    def test_truncated_inline_svg_is_rejected(self):
        self.assertIsNone(_valid_svg_fragment('<svg xmlns="http://www.w3.org/2000/svg"><g>'))

    def test_valid_inline_svg_is_extracted(self):
        svg = '<svg xmlns="http://www.w3.org/2000/svg"><circle cx="2" cy="2" r="1"/></svg>'
        self.assertEqual(_valid_svg_fragment('prefix\n' + svg + '\nsuffix'), svg)

    def test_downloaded_svg_is_prioritized_over_inline_block(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'artifacts').mkdir()
            (root / 'artifacts' / 'bad.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"><g>', encoding='utf-8')
            good = '<svg xmlns="http://www.w3.org/2000/svg"><circle cx="2" cy="2" r="1"/></svg>'
            (root / 'artifacts' / 'file.svg').write_text(good, encoding='utf-8')
            svg, side = _read_artifact_files(root, [
                {"path":"artifacts/bad.svg", "valid":False, "source":"code_block"},
                {"path":"artifacts/file.svg", "valid":True, "source":"download"},
            ])
            self.assertEqual(svg, good)
            self.assertIsNone(side)

    def test_sidecar_needs_valid_json_and_sidecar_keys(self):
        self.assertIsNone(_sidecar_json('{"partes":'))
        parsed = _sidecar_json('{"partes": {}, "animacoes": {}}')
        self.assertEqual(json.loads(parsed), {"partes": {}, "animacoes": {}})

    def test_adapter_prefers_file_svg_valid_when_inline_is_truncated(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bridge = root / "bridge"
            bridge.mkdir()
            (bridge / "config.json").write_text("{}", encoding="utf-8")
            fake = r'''import json, sys
from pathlib import Path
args = sys.argv
request = Path(args[args.index("--job") + 1])
job = json.loads(request.read_text(encoding="utf-8"))
out = Path("results") / job["id"]
(out / "artifacts").mkdir(parents=True, exist_ok=True)
(out / "response.txt").write_text('<svg xmlns="http://www.w3.org/2000/svg"><g>', encoding="utf-8")
(out / "artifacts" / "file.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><circle cx="2" cy="2" r="1"/></svg>', encoding="utf-8")
metadata = {"success": True, "code_blocks": [{"language":"svg", "content":"<svg xmlns=\\\"http://www.w3.org/2000/svg\\\"><g>"}], "artifacts": [{"filename":"file.svg", "path":"artifacts/file.svg", "source":"download", "valid":True}], "rejected_artifacts": [{"filename":"artefato_01.svg", "valid":False}], "attachment_diagnostics": []}
(out / "response.json").write_text(json.dumps(metadata), encoding="utf-8")
'''
            (bridge / "main.py").write_text(fake, encoding="utf-8")
            logs = []
            llm = criar_llm_myhub({"myhub_bridge_dir": str(bridge)}, root, logs.append)
            result = llm("Desenhe o SVG", False)
            self.assertEqual(result, '<svg xmlns="http://www.w3.org/2000/svg"><circle cx="2" cy="2" r="1"/></svg>')
            self.assertTrue(any("anexo" in message.lower() for message in logs))

    def test_adapter_no_retry_when_no_complete_svg_exists(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bridge = root / "bridge"
            bridge.mkdir()
            (bridge / "config.json").write_text("{}", encoding="utf-8")
            fake = r'''import json, sys
from pathlib import Path
args = sys.argv
request = Path(args[args.index("--job") + 1])
job = json.loads(request.read_text(encoding="utf-8"))
out = Path("results") / job["id"]
out.mkdir(parents=True, exist_ok=True)
(out / "response.txt").write_text('<svg xmlns="http://www.w3.org/2000/svg"><g>', encoding="utf-8")
metadata = {"success":True,"artifacts":[],"code_blocks":[{"language":"svg","content":"<svg xmlns=\\\"http://www.w3.org/2000/svg\\\"><g>"}]}
(out / "response.json").write_text(json.dumps(metadata), encoding="utf-8")
'''
            (bridge / "main.py").write_text(fake, encoding="utf-8")
            llm = criar_llm_myhub({"myhub_bridge_dir": str(bridge)}, root, lambda _: None)
            with self.assertRaises(MyHubArtifactMissingError) as caught:
                llm("Desenhe o SVG", False)
            self.assertTrue(caught.exception.no_retry)


if __name__ == '__main__':
    unittest.main()
