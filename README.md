# GHOST-Reproduction

**Student:** Sahil Dunani (NetID: sd6429)  
**Course:** NYU LLM4ChipDesign (Prof. Ramesh Karri), Fall 2026  
**Assignment:** Agent-Based Hardware Trojan Paper Reproduction  
**Paper:** _Unleashing GHOST: An LLM-Powered Framework for Automated Hardware Trojan Design_, arXiv:2412.02816

A Python reproduction of the GHOST framework from

> **Unleashing GHOST: An LLM-Powered Framework for Automated Hardware Trojan Design**
> Sankara Sastry et al., arXiv:2412.02816 (2024)

GHOST uses a large language model (LLM) as an *agent* that reads a clean
Verilog design, chooses an insertion point, and modifies the RTL to embed a
stealthy hardware trojan (HT). The paper combines three prompt-engineering
strategies (RBP + CTP + RVP), runs the LLM on three benchmarks (SRAM, UART,
AES-128) and three HT categories (change-function, leak-info, denial-of-
service), and evaluates each generated HT across four stages
(compile → functional → trigger-activated → post-synthesis survival).

This repository is an **independent reproduction** of the methodology. The
original paper does not release the complete prompt set or the generator
source, so every prompt here is rebuilt from the description in the paper.

---

## What is reproduced

| Component | Paper | This repo |
|---|---|---|
| LLM agent | GPT-4, Gemini-1.5-pro, LLaMA3-70B | OpenAI `gpt-4o-mini` (default); any OpenAI-compatible model via `--model` |
| Prompt strategies | RBP + CTP + RVP combined | All three, rebuilt from the paper's description, in `src/prompts.py` |
| Benchmarks | SRAM (52 LoC), UART (430 LoC), AES-128 (768 LoC) | SRAM and UART-TX; AES-128 omitted (too large for a 32-hour budget) |
| HT categories | HT1 change-function, HT2 info-leak, HT3 DoS | All three |
| Eval0 — compilation | iverilog | iverilog ✓ |
| Eval1 — dormant functionality preserved | run original TB on infected RTL | iverilog + original TB ✓ |
| Eval2 — trigger activation | custom activation TB | iverilog + per-HT activation TB ✓ |
| Eval3 — post-synthesis survival | Yosys + Sky130 PDK | **Not reproduced** — Yosys + Sky130 PDK setup is out of scope for this submission |
| Agent interaction logs | implied | every LLM call saved to `agent_logs/*.json` |

The paper's main table reports GPT-4 at **88.9 / 100 / 100 / 100 %**. This
repo only reports the first three Eval stages.

---

## Repository layout

```
GHOST-Reproduction/
├── README.md
├── requirements.txt
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── agent.py            GHOST agent: builds the combined prompt, calls the
│   │                       LLM, applies Reflexive Validation (one revision
│   │                       pass if RVP self-check flags an issue).
│   ├── prompts.py          RBP, CTP (per HT type) and RVP templates.
│   ├── response_parser.py  Extracts the modified RTL, taxonomy label and
│   │                       explanation from the LLM response.
│   ├── evaluator.py        Eval0 + Eval1 + Eval2 iverilog harness.
│   └── run_ghost.py        Main entrypoint.
├── benchmarks/
│   ├── sram/
│   │   ├── sram.v          Clean 32×8 single-port sync SRAM.
│   │   └── sram_tb.v       Original self-checking testbench.
│   └── uart_tx/
│       ├── uart_tx.v       Clean 8-N-1 UART transmitter.
│       └── uart_tx_tb.v    Original self-checking testbench.
├── prompts/
│   ├── rbp.txt             Role-Based Prompt text, verbatim (for the report).
│   ├── ctp_ht1.txt         Contextual Trojan Prompt — change-function.
│   ├── ctp_ht2.txt         Contextual Trojan Prompt — information leak.
│   ├── ctp_ht3.txt         Contextual Trojan Prompt — denial of service.
│   └── rvp.txt             Reflexive Validation checklist.
├── agent_logs/             One JSON per LLM call, written at runtime.
├── results/
│   ├── eval_table.csv      Per-run Eval0/1/2 results.
│   └── summary.md          Human-readable rollup table.
└── docs/
    ├── methodology.md      How RBP+CTP+RVP map onto our Python code.
    └── agent_interactions.md
                            Walk-through of a representative run: the prompt
                            sent, the LLM's response, the Eval verdicts, and
                            any revision the RVP loop asked for.
```

---

## Setup

```bash
pip install -r requirements.txt
sudo apt-get install -y iverilog     # Ubuntu / WSL / Colab
# macOS:    brew install icarus-verilog
# Windows:  install iverilog from http://bleyer.org/icarus/
```

Set your OpenAI key before running:

```bash
export OPENAI_API_KEY=sk-...
```

---

## Run

Single HT, one benchmark:

```bash
python -m src.run_ghost --benchmark sram --ht-type HT1
```

All three HTs, both benchmarks, gpt-4o-mini:

```bash
python -m src.run_ghost --benchmark sram uart_tx --ht-type HT1 HT2 HT3
```

Each run writes:

* the infected RTL to `results/<benchmark>_<HT>/infected.v`
* the full prompt and the LLM response to `agent_logs/<timestamp>.json`
* an Eval0/1/2 row to `results/eval_table.csv`

A final rollup is printed at the end and written to `results/summary.md`.

---

## Documenting the AI-agent interactions

Every call to the LLM is saved verbatim to `agent_logs/`. Each JSON file
holds the model id, the three prompt parts (RBP, CTP, RVP), the raw
response, the parsed RTL, the Eval0/1/2 verdicts, and — if the Reflexive
Validation loop ran a revision — the follow-up prompt and the second
response. See `docs/agent_interactions.md` for a walk-through of one
representative run.

---

## Difference from the paper

* Only two of the three benchmarks (AES-128 omitted).
* One LLM family instead of three; replacing `--model` with any
  OpenAI-compatible endpoint is a one-line change.
* Eval3 (post-synthesis survival via Yosys + Sky130) is not run — Yosys
  installation and PDK configuration are beyond the 32-hour scope of this
  submission.
* The paper's `Hw2vec` detection-evasion study is not reproduced.
* The paper's full prompt text is not released by the authors; the prompts
  in this repo are independent reconstructions from the paper's description
  and are documented verbatim in `prompts/`.

---

## Acknowledgement

This reproduction was built with LLM-assisted development as part of the
NYU LLM4ChipDesign course assignment "Agent-Based Hardware Trojan Paper
Reproduction" (Prof. Ramesh Karri, Fall 2026).
