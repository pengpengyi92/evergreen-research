import json
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
                summary = run_citations(
                    Path(tmp), "LLM Reasoning / Test-time Compute", top_n=10, quiet=True, source="s2"
                )
            self.assertEqual(summary["ok"], 2)
            self.assertEqual(summary["rate_limited"], 1)
            self.assertEqual(summary["stored"], 2)
            self.assertEqual(CitationStore(Path(tmp)).stats()["tracked"], 2)


class NoveltyTest(unittest.TestCase):
    def test_jaccard_and_score(self) -> None:
        from evergreen.novelty import jaccard, novelty_score

        self.assertEqual(jaccard(frozenset("ab"), frozenset("bc")), 1 / 3)
        records = [
            {"id": "a", "methods": ["RLVR / GRPO", "Verifier / PRM"]},
            {"id": "b", "methods": ["RLVR / GRPO", "Verifier / PRM", "Search / MCTS"]},
            {"id": "c", "methods": ["RLVR / GRPO", "Verifier / PRM"]},
        ]
        score = novelty_score(records[0], records)
        # overlapping cohort of 2 with jaccards 2/3 and 1 -> novelty 1 - mean
        self.assertAlmostEqual(score["mean_jaccard"], (2 / 3 + 1.0) / 2, places=3)
        self.assertAlmostEqual(score["novelty"], 1 - (2 / 3 + 1.0) / 2, places=3)
        lone = novelty_score({"id": "d", "methods": ["Speculative Decoding"]}, records)
        self.assertEqual(lone["novelty"], 1.0)

    def test_md_to_latex_subset(self) -> None:
        from evergreen.latex import md_to_latex

        markdown = "## Heading\n\n- item **bold** and `code`\n- [link](https://x)\n\n> quote\n\n| A | B |\n|---|---|\n| 1 | 2 |\n"
        tex = md_to_latex(markdown)
        self.assertIn(r"\section{Heading}", tex)
        self.assertIn(r"\textbf{bold}", tex)
        self.assertIn(r"\texttt{code}", tex)
        self.assertIn(r"\href{https://x}{link}", tex)
        self.assertIn(r"\begin{itemize}", tex)
        self.assertIn(r"\begin{quote}", tex)
        self.assertIn(r"\begin{tabular}{ll}", tex)
        self.assertIn("A & B", tex)


class AuditTest(unittest.TestCase):
    def test_audit_catches_missing_and_unverified(self) -> None:
        from evergreen.audit import run_audit

        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data"
            survey_root = data_root / "survey"
            sections = survey_root / "sections"
            sections.mkdir(parents=True)
            db = PaperDatabase(data_root)
            db.upsert_many(
                [
                    {
                        "id": "evg-0123456789abcdef",
                        "title": "Real Paper",
                        "arxiv_id": "http://arxiv.org/abs/2501.02497",
                        "pillar": "LLM Reasoning / Test-time Compute",
                        "verified": False,
                        "methods": ["RLVR / GRPO"],
                        "benchmarks": [],
                        "year": 2025,
                        "published": "2025-01-01T00:00:00Z",
                        "authors": ["A"],
                        "url": "",
                        "categories": [],
                        "key_results": [],
                        "abstract": "",
                        "code_available": False,
                        "confidence": 0.5,
                        "swept_on": "2026-01-01T00:00:00Z",
                    }
                ]
            )
            (sections / "01-test.md").write_text(
                "Citing evg-0123456789abcdef and evg-deadbeefdeadbeef. "
                "arXiv:2501.02497 external. total 503 papers.",
                encoding="utf-8",
            )
            summary = run_audit(survey_root, data_root, quiet=True)
            self.assertGreaterEqual(summary["fail"], 1)  # missing id
            self.assertGreaterEqual(summary["warn"], 1)  # unverified + external


class RssTest(unittest.TestCase):
    def test_feed_generation(self) -> None:
        import xml.etree.ElementTree as ET

        from evergreen.rss import write_feed

        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp)
            weekly = data_root / "weekly"
            weekly.mkdir(parents=True)
            (weekly / "2026-W34.md").write_text(
                "# Frontier AI Weekly\n\n- **Paper One** ([arXiv](https://arxiv.org/abs/x)) — conf 0.80\n",
                encoding="utf-8",
            )
            path = write_feed(data_root, quiet=True)
            root = ET.parse(path).getroot()
            items = root.findall(".//item")
            self.assertEqual(len(items), 1)
            self.assertIn("2026-W34", items[0].findtext("title"))


class OpenAlexTest(unittest.TestCase):
    def test_paper_by_title_match(self) -> None:
        from evergreen import openalex

        record = {"title": "DeepSeek-R1: Incentivizing Reasoning", "authors": ["DeepSeek-AI"]}
        payload = {
            "results": [
                {
                    "id": "W1",
                    "title": "DeepSeek-R1: Incentivizing Reasoning",
                    "cited_by_count": 853,
                    "publication_date": "2025-01-22",
                    "authorships": [{"author": {"display_name": "DeepSeek-AI"}}],
                    "primary_location": None,
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict("os.environ", {"EVERGREEN_OPENALEX_CACHE": tmp}):
                with mock.patch.object(openalex, "_rate_limit"):

                    def fake_urlopen(request, timeout=30):
                        response = mock.MagicMock()
                        response.read.return_value = json.dumps(payload).encode("utf-8")
                        response.__enter__ = lambda self: self
                        response.__exit__ = lambda *a: None
                        return response

                    with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
                        result = openalex.paper_by_title(record)
                    self.assertEqual(result["citationCount"], 853)
                    self.assertEqual(result["source"], "openalex")
                    # cached: second call must not hit the network again
                    with mock.patch("urllib.request.urlopen", side_effect=AssertionError("network used")):
                        again = openalex.paper_by_title(record)
                    self.assertEqual(again["citationCount"], 853)


class MatrixTest(unittest.TestCase):
    def test_build_query_cluster(self) -> None:
        from evergreen.matrix import build_matrix, cluster_report, kmeans, query

        records = [
            {"id": "a", "title": "Reinforcement learning for reasoning models", "abstract": "we train reasoning models with reinforcement learning and verifiable rewards", "pillar": "LLM Reasoning / Test-time Compute", "year": 2025, "arxiv_id": "arXiv:1"},
            {"id": "b", "title": "Reinforcement learning trading agents", "abstract": "we train trading agents with reinforcement learning and market rewards", "pillar": "Quant × AI", "year": 2025, "arxiv_id": "arXiv:2"},
            {"id": "c", "title": "Video generation with diffusion models", "abstract": "we generate videos using diffusion and world models", "pillar": "Multimodal / World Models", "year": 2026, "arxiv_id": "arXiv:3"},
            {"id": "d", "title": "Diffusion for image synthesis", "abstract": "image synthesis with diffusion models and text conditioning", "pillar": "Multimodal / World Models", "year": 2026, "arxiv_id": "arXiv:4"},
        ]
        matrix = build_matrix(records)
        self.assertGreater(len(matrix["vocabulary"]), 5)
        results = query(matrix, records, "reinforcement learning", k=2)
        top_ids = {item["id"] for item in results}
        self.assertEqual(top_ids, {"a", "b"})  # both RL papers; shorter doc ranks higher
        assignment = kmeans(matrix, k=2)
        report = cluster_report(matrix, records, assignment, 2)
        self.assertEqual(len(report["clusters"]), 2)
        self.assertGreater(sum(c["size"] for c in report["clusters"]), 0)


class GroupsTest(unittest.TestCase):
    def test_group_classification_and_report(self) -> None:
        from evergreen.groups import is_ai_quant, run_groups

        self.assertTrue(is_ai_quant("We train a transformer for stock prediction"))
        self.assertFalse(is_ai_quant("A study of medieval poetry in translation"))

        works = [
            {
                "openalex_id": "W1",
                "title": "LLM Agents for Portfolio Optimization",
                "abstract": "We build trading agents with reinforcement learning and memory",
                "authorships": [{"author": "A. Chan", "institutions": ["Hong Kong University of Science and Technology"]}],
                "institutions": ["Hong Kong University of Science and Technology"],
                "affiliations_raw": ["Department of Computer Science, Hong Kong University of Science and Technology"],
                "cited_by_count": 12,
                "publication_date": "2026-01-05",
                "doi": "10.1/x",
            },
            {
                "openalex_id": "W2",
                "title": "Poetry in the Tang Dynasty",
                "abstract": "A historical analysis of poetry",
                "authorships": [{"author": "B. Lee", "institutions": ["Hong Kong University of Science and Technology"]}],
                "institutions": ["Hong Kong University of Science and Technology"],
                "affiliations_raw": ["Department of Computer Science, Hong Kong University of Science and Technology"],
                "cited_by_count": 3,
                "publication_date": "2026-02-01",
                "doi": "10.1/y",
            },
            {
                "openalex_id": "W3",
                "title": "Graph Neural Networks for Equity Forecasting",
                "abstract": "forecasting equities with graph neural networks",
                "authorships": [{"author": "C. Wong", "institutions": ["University of Hong Kong"]}],
                "institutions": ["University of Hong Kong"],
                "affiliations_raw": ["Department of Statistics and Actuarial Science, University of Hong Kong"],
                "cited_by_count": 8,
                "publication_date": "2026-03-01",
                "doi": "10.1/z",
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp)
            with mock.patch(
                "evergreen.openalex.works_by_institution", return_value=works
            ):
                aggregate = run_groups(data_root, per_group=10, quiet=True)
            hkust = aggregate["groups"].get("hkust", {})
            self.assertEqual(hkust.get("papers"), 1)  # only the AI/quant work
            self.assertTrue((data_root / "groups" / "hkust.md").exists())
            self.assertIn("Portfolio Optimization", (data_root / "groups" / "hkust.md").read_text())
            # hku-ds requires department-level raw affiliation strings
            hku_ds = aggregate["groups"].get("hku-ds", {})
            self.assertEqual(hku_ds.get("papers"), 1)
            self.assertIn("Equity Forecasting", (data_root / "groups" / "hku-ds.md").read_text())


class GithubRadarTest(unittest.TestCase):
    def test_org_repos_radar(self) -> None:
        from evergreen import github

        payload = [
            {
                "name": "LightRAG",
                "full_name": "HKUDS/LightRAG",
                "description": "Simple and Fast RAG",
                "language": "Python",
                "stargazers_count": 38951,
                "forks_count": 1200,
                "topics": ["rag", "llm"],
                "pushed_at": "2026-08-19T00:00:00Z",
                "html_url": "https://github.com/HKUDS/LightRAG",
            },
            {
                "name": "OldRepo",
                "full_name": "HKUDS/OldRepo",
                "description": "dormant",
                "language": "Roff",
                "stargazers_count": 2,
                "forks_count": 0,
                "topics": [],
                "pushed_at": "2023-01-01T00:00:00Z",
                "html_url": "https://github.com/HKUDS/OldRepo",
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict("os.environ", {"EVERGREEN_GH_CACHE": tmp, "GITHUB_TOKEN": "fake"}):
                captured = {}

                def fake_urlopen(request, timeout=30):
                    captured["auth"] = request.headers.get("Authorization")
                    response = mock.MagicMock()
                    response.read.return_value = json.dumps(payload).encode("utf-8")
                    response.__enter__ = lambda self: self
                    response.__exit__ = lambda *a: None
                    return response

                with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
                    repos = github.org_repos("HKUDS")
                self.assertEqual(len(repos), 2)
                self.assertEqual(captured["auth"], "Bearer fake")
                report = github.repos_report(repos, "HKUDS")
                self.assertEqual(report["active_repos"], 1)
                self.assertEqual(report["total_stars"], 38953)
                self.assertEqual(report["top"][0]["name"], "LightRAG")


class PillarsPluginTest(unittest.TestCase):
    def test_load_pillars_merges_manifest(self) -> None:
        from evergreen.pillars import PILLARS, load_pillars

        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "evergreen_pillars.json"
            manifest.write_text(
                json.dumps(
                    {
                        "Crypto / DeFi × AI": {
                            "categories": ["q-fin.TR"],
                            "terms": 'all:"crypto" OR all:"defi"',
                            "max": 10,
                            "days_back": 21,
                        }
                    }
                ),
                encoding="utf-8",
            )
            merged = load_pillars(manifest)
            self.assertEqual(len(merged), len(PILLARS) + 1)
            self.assertIn("Crypto / DeFi × AI", merged)
            # missing manifest -> built-ins only
            self.assertEqual(len(load_pillars(Path(tmp) / "nope.json")), len(PILLARS))


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
