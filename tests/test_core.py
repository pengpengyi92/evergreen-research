import unittest
from datetime import UTC, datetime

from evergreen.arxiv_client import parse_atom, parse_atom_lenient
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


if __name__ == "__main__":
    unittest.main()
