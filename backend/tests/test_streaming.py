import json
import types
import unittest
from unittest.mock import patch

class StreamingTests(unittest.TestCase):
    def test_sse_token_stream(self):
        from backend.app import app
        captured = {"load_called": []}
        def fake_load_pipeline(model_dir, device, config):
            captured["load_called"].append({"device": device, "config": dict(config or {})})
            return types.SimpleNamespace()
        def fake_generate_stream(pipe, prompt, config, streamer):
            streamer("hello ")
            streamer("world ")
            streamer("!")
            return "hello world !", {"ttft_ms": 10.0, "tpot_ms": 5.0, "throughput_tps": 50.0, "generate_ms": 100.0}
        with patch("backend.app.load_pipeline", fake_load_pipeline), patch("backend.services.inference.generate_stream", fake_generate_stream):
            client = app.test_client()
            resp = client.get("/api/infer/stream?model_id=unit&device=CPU&prompt=hi&config={}")
            data = b"".join(list(resp.response))
            s = data.decode("utf-8", errors="ignore")
            self.assertIn("event: token", s)
            self.assertIn("event: final", s)
            self.assertTrue(captured["load_called"] and captured["load_called"][0]["config"].get("auto_multi") is True)

    def test_perf_usage(self):
        from backend.app import app
        client = app.test_client()
        resp = client.get("/api/perf")
        self.assertEqual(resp.status_code, 200)
        j = json.loads(resp.get_data(as_text=True))
        self.assertIn("avg", j)
        self.assertIn("usage", j)

    def test_sources_event(self):
        from backend.app import app
        def fake_web_search(q, max_results=5):
            return [
                {"title": "A", "url": "http://a.com", "snippet": "sa"},
                {"title": "B", "url": "http://b.com", "snippet": "sb"},
            ]
        def fake_augment(prompt, src, lang="zh"):
            return prompt + "\n" + "\n".join([s["title"] for s in src])
        with patch("backend.services.inference.web_search", fake_web_search), patch("backend.services.inference.augment_with_sources", fake_augment), patch("backend.app.load_pipeline", lambda a,b,c: object()), patch("backend.services.inference.generate_stream", lambda p, q, c, s: ("ok", {})):
            client = app.test_client()
            resp = client.get("/api/infer/stream?model_id=unit&device=CPU&prompt=hi&config={\"web_search\":true,\"search_query\":\"hi\"}")
            data = b"".join(list(resp.response))
            s = data.decode("utf-8", errors="ignore")
            self.assertIn("event: sources", s)

if __name__ == "__main__":
    unittest.main()