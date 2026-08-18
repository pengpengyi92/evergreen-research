from __future__ import annotations

PILLARS: dict[str, dict[str, object]] = {
    "LLM Reasoning / Test-time Compute": {
        "categories": ["cs.AI", "cs.CL", "cs.LG"],
        "terms": (
            'all:"reasoning" OR all:"chain-of-thought" OR all:"test-time compute" '
            'OR all:"inference-time" OR all:"process reward" OR all:"verifier" '
            'OR all:"RLVR" OR all:"GRPO" OR all:"reinforcement learning"'
        ),
        "max": 15,
        "days_back": 21,
    },
    "Agentic AI / Deep Research Systems": {
        "categories": ["cs.AI", "cs.MA", "cs.CL"],
        "terms": (
            'all:"agent" OR all:"tool use" OR all:"multi-agent" OR all:"deep research" '
            'OR all:"computer use" OR all:"web agent" OR all:"function calling"'
        ),
        "max": 15,
        "days_back": 21,
    },
    "Efficient Training & Inference": {
        "categories": ["cs.LG", "cs.CL", "cs.DC"],
        "terms": (
            'all:"mixture-of-experts" OR all:"distillation" OR all:"quantization" '
            'OR all:"KV cache" OR all:"long context" OR all:"speculative decoding" '
            'OR all:"scaling law" OR all:"training efficiency"'
        ),
        "max": 15,
        "days_back": 21,
    },
    "RL / Alignment / Safety": {
        "categories": ["cs.LG", "cs.CL", "cs.CR"],
        "terms": (
            'all:"reinforcement learning from human feedback" OR all:"preference optimization" '
            'OR all:"alignment" OR all:"interpretability" OR all:"jailbreak" '
            'OR all:"red team" OR all:"reward hacking"'
        ),
        "max": 15,
        "days_back": 21,
    },
    "Multimodal / World Models": {
        "categories": ["cs.CV", "cs.CL", "cs.LG"],
        "terms": (
            'all:"vision-language" OR all:"video generation" OR all:"world model" '
            'OR all:"multimodal" OR all:"image generation"'
        ),
        "max": 15,
        "days_back": 21,
    },
    "Quant × AI": {
        "categories": ["q-fin.TR", "q-fin.ST", "q-fin.CP", "cs.LG"],
        "terms": (
            'all:"trading" OR all:"stock" OR all:"financial" OR all:"market prediction" '
            'OR all:"portfolio" OR all:"factor model"'
        ),
        "max": 15,
        "days_back": 30,
    },
}
