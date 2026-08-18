import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest import mock

from evergreen.arxiv_client import parse_atom, parse_atom_lenient
from evergreen.database import PaperDatabase
from evergreen.structurer import detect_benchmarks, detect_methods, structure_entry

SAMPLE_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2501.12948v3</id>
    <title>DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning</title>
    <summary>We introduce first-generation reasoning models trained with large-scale
    reinforcement learning. They develop long chain-of-thought traces, self-verification
    and reflection. On AIME 2024 and MATH-500 the model attains performance comparable
    to OpenAI-o1 and outperforms prior open baselines. Code is available on GitHub.</summary>
    <published>2025-01-22T18:59:31Z</published>
    <updated>2025-01-22T18:59:31Z</updated>
    <author><name>DeepSeek-AI</name></author>
    <link href="http://arxiv.org/abs/2501.12948v3" rel="alternate" type="text/html"/>
    <arxiv:primary_category term="cs.CL"/>
    <category term="cs.CL"/>
    <category term="cs.AI"/>
  </entry>
</feed>
"""


class ParseTest(unittest.TestCase):
    def test_parse_atom(self) -> None:
        entries = parse_atom(SAMPLE_ATOM)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["primary_category"], "cs.CL")
        self.assertEqual(entries[0]["authors"], ["DeepSeek-AI"])

    def test_salvage_truncated(self) -> None:
        truncated = SAMPLE_ATOM[: SAMPLE_ATOM.rfind("</feed>")]
        entries = parse_atom_lenient(truncated)
        self.assertEqual(len(entries), 1)


class StructurerTest(unittest.TestCase):
    def test_method_benchmark_detection(self) -> None:
        text = (
            "We train with reinforcement learning and RLVR. The model uses "
            "chain-of-thought and a process reward model. Evaluated on AIME, "
            "MATH-500, and GPQA, it outperforms baselines."
        )
        methods = detect_methods(text)
        self.assertIn("RLVR / GRPO", methods)
        self.assertIn("Chain-of-Thought", methods)
        benchmarks = detect_benchmarks(text)
        self.assertIn("AIME", benchmarks)
        self.assertIn("GPQA", benchmarks)

    def test_arc_boundary_no_false_positive(self) -> None:
        text = "We study architecture and search for trajectory arcs in robotics."
        self.assertNotIn("ARC-AGI", detect_benchmarks(text))

    def test_structure_entry(self) -> None:
        entry = parse_atom(SAMPLE_ATOM)[0]
        record = structure_entry(
            entry,
            "LLM Reasoning / Test-time Compute",
            datetime.now(UTC).isoformat(),
        )
        self.assertEqual(record["pillar"], "LLM Reasoning / Test-time Compute")
        self.assertTrue(record["id"].startswith("evg-"))
        self.assertIn("AIME", record["benchmarks"])
        self.assertTrue(record["code_available"])
        self.assertGreater(record["confidence"], 0.6)


class FulltextTest(unittest.TestCase):
    def test_html_to_text_extracts_content(self) -> None:
        from evergreen.fulltext import html_to_text, normalize_arxiv_id

        html = (
            "<html><head><title>x</title><style>.a{}</style></head><body>"
            "<h1>Title</h1><p>We study <b>reasoning</b> models.</p>"
            "<p>Second paragraph with AIME benchmark.</p>"
            "<script>var x = 1;</script>"
            "</body></html>"
        )
        text = html_to_text(html)
        self.assertIn("reasoning", text)
        self.assertIn("AIME", text)
        self.assertNotIn("var x = 1", text)
        self.assertEqual(normalize_arxiv_id("http://arxiv.org/abs/2501.12948v3"), "2501.12948")
        self.assertEqual(normalize_arxiv_id("2501.12948"), "2501.12948")

    def test_verify_pipeline_mocked(self) -> None:
        from evergreen.pipeline import run_verification

        record = {
            "id": "evg-test-fulltext",
            "title": "Test-Time Scaling Paper",
            "authors": ["A. Researcher"],
            "year": 2026,
            "published": "2026-08-01T00:00:00Z",
            "arxiv_id": "http://arxiv.org/abs/2608.00002",
            "url": "https://arxiv.org/abs/2608.00002",
            "primary_category": "cs.AI",
            "categories": ["cs.AI"],
            "pillar": "LLM Reasoning / Test-time Compute",
            "methods": ["Verifier / PRM"],
            "benchmarks": ["AIME"],
            "models": [],
            "key_results": [],
            "abstract": "abstract",
            "code_available": False,
            "confidence": 0.7,
            "swept_on": "2026-08-18T00:00:00Z",
        }
        html = (
            "<html><body><p>"
            + ("We use a process reward model with chain-of-thought. " * 400)
            + "Evaluated on AIME and MATH.</p></body></html>"
        )
        with tempfile.TemporaryDirectory() as tmp:
            db = PaperDatabase(Path(tmp))
            db.upsert_many([record])
            with mock.patch(
                "evergreen.fulltext.fetch_fulltext", return_value=(html, "ar5iv")
            ):
                summary = run_verification(Path(tmp), "LLM Reasoning / Test-time Compute", top_n=5, quiet=True)
            self.assertEqual(summary["verified"], 1)
            updated = db.load()[0]
            self.assertTrue(updated["verified"])
            self.assertIn("fulltext-verified", updated["verification"]["status"])
            self.assertIn("Verifier / PRM", updated["verification"]["matched_methods"])

    def test_db_update_record_atomic(self) -> None:
        db = PaperDatabase(Path(tempfile.mkdtemp()))
        record = {"id": "r1", "title": "x"}
        db.upsert_many([record])
        self.assertTrue(db.update_record("r1", {"verified": True}))
        self.assertEqual(db.load()[0]["verified"], True)
        self.assertFalse(db.update_record("nope", {"verified": True}))


class CitationsTest(unittest.TestCase):
    def test_store_round_trip_and_stats(self) -> None:
        from evergreen.citations import CitationStore

        with tempfile.TemporaryDirectory() as tmp:
            store = CitationStore(Path(tmp))
            added = store.upsert(
                [
                    {
                        "arxiv_id": "arXiv:2501.12948",
                        "citationCount": 4200,
                        "influentialCitationCount": 310,
                    },
                    {
                        "arxiv_id": "arXiv:2501.02497",
                        "citationCount": 40,
                        "influentialCitationCount": 4,
                    },
                ]
            )
            self.assertEqual(added, 2)
            self.assertEqual(store.upsert([{"arxiv_id": "arXiv:2501.12948", "citationCount": 1}]), 0)
            stats = store.stats()
            self.assertEqual(stats["tracked"], 2)
            self.assertEqual(stats["median_citations"], 2120)
            self.assertEqual(stats["max_citations"], 4200)

    def test_paper_by_arxiv_id_mock(self) -> None:
        from evergreen.citations import paper_by_arxiv_id

        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict("os.environ", {"EVERGREEN_S2_CACHE": tmp}):
                with mock.patch("evergreen.citations._rate_limit"):
                    record = paper_by_arxiv_id(
                        "2501.12948",
                        fetch_func=lambda url: {
                            "citationCount": 42,
                            "influentialCitationCount": 3,
                        },
                    )
                    self.assertEqual(record["citationCount"], 42)
                    # cached: fetcher not called again
                    calls = []
                    again = paper_by_arxiv_id("2501.12948", fetch_func=lambda url: calls.append(url) or {})
                    self.assertEqual(again["citationCount"], 42)
                    self.assertEqual(calls, [])

    def test_run_citations_persists_only_successes(self) -> None:
        from evergreen.citations import CitationStore
        from evergreen.pipeline import run_citations

        papers = []
        for i in range(3):
            papers.append(
                {
                    "id": f"evg-c{i}",
                    "title": f"Paper {i}",
                    "published": f"2026-08-0{i + 1}T00:00:00Z",
                    "arxiv_id": f"http://arxiv.org/abs/2608.1000{i}",
                    "pillar": "LLM Reasoning / Test-time Compute",
                    "verified": True,
                }
            )
        with tempfile.TemporaryDirectory() as tmp:
            db = PaperDatabase(Path(tmp))
            db.upsert_many(papers)
            calls = {"n": 0}

            def fake_fetch(url):
                calls["n"] += 1
                if calls["n"] == 2:
                    return {"arxiv_id": "x", "citationCount": None, "error": "rate_limited"}
                return {"citationCount": 10 + calls["n"], "influentialCitationCount": 1}

            with mock.patch(
                "evergreen.citations.paper_by_arxiv_id", side_effect=lambda aid: fake_fetch(aid)
            ):
                summary = run_citations(Path(tmp), "LLM Reasoning / Test-time Compute", top_n=10, quiet=True)
            self.assertEqual(summary["ok"], 2)
            self.assertEqual(summary["rate_limited"], 1)
            self.assertEqual(summary["stored"], 2)
            self.assertEqual(CitationStore(Path(tmp)).stats()["tracked"], 2)


class PipelineTest(unittest.TestCase):
    def test_cluster_signals(self) -> None:
        from evergreen.pipeline import _cluster_signals

        records = [
            {"methods": ["RLVR / GRPO", "Verifier / PRM"], "pillar": "LLM Reasoning / Test-time Compute"},
            {"methods": ["RLVR / GRPO"], "pillar": "Agentic AI / Deep Research Systems"},
            {"methods": ["RLVR / GRPO"], "pillar": "Quant × AI"},
        ]
        signals = _cluster_signals(records)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0]["method"], "RLVR / GRPO")
        self.assertEqual(len(signals[0]["spanning_pillars"]), 3)

    def test_backfill_dedups(self) -> None:
        from evergreen.pipeline import run_backfill

        entry = {
            "arxiv_id": "http://arxiv.org/abs/2608.00001",
            "title": "Backfill Test Paper",
            "summary": "We study reinforcement learning with process reward models on AIME.",
            "published": "2026-01-01T00:00:00Z",
            "updated": "2026-01-01T00:00:00Z",
            "url": "https://arxiv.org/abs/2608.00001",
            "primary_category": "cs.AI",
            "categories": ["cs.AI"],
            "authors": ["A. Researcher"],
            "comment": "",
        }
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch("evergreen.pipeline.arxiv_client.search_recent", return_value=[entry]):
                first = run_backfill(Path(tmp), [(360, 0)], per_pillar=30, quiet=True)
                # same arXiv id across six pillars -> one record after dedup
                self.assertEqual(first["new_records"], 1)
                second = run_backfill(Path(tmp), [(360, 0)], per_pillar=30, quiet=True)
                self.assertEqual(second["new_records"], 0)  # already in DB


if __name__ == "__main__":
    unittest.main()
