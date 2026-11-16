# How RBP + CTP + RVP map onto this reproduction

The paper calls out three prompt-engineering strategies and runs them as
a single concatenated prompt. This repo keeps each strategy in its own
text file under `prompts/` so a reviewer can read them without touching
Python, and `src/prompts.py` glues them in the fixed order
`RBP → CTP(HT type) → target design → RVP`.

## Role-Based Prompting (RBP)

File: `prompts/rbp.txt`. The model is asked to act as a hardware-security
researcher that already knows the Trust-Hub taxonomy, the usual
trigger/payload split, and common synthesis gotchas. The role is written
to encourage the model to pick *rare internal* triggers rather than
cheap top-level enables.

## Contextual Trojan Prompting (CTP)

Files: `prompts/ctp_ht1.txt`, `prompts/ctp_ht2.txt`,
`prompts/ctp_ht3.txt`. Each one defines the HT category for this call —
what the trigger should look like, what the payload must do, and the
dormancy requirement that keeps Eval1 passing.

* **HT1 — change function.** A bit-flip or value override on an output,
  fired by an internal rare condition.
* **HT2 — information leak.** An internal value is multiplexed onto an
  existing output when a rare condition is met.
* **HT3 — denial of service.** A rare condition latches the design into
  a broken state until reset.

## Reflexive Validation Prompting (RVP)

File: `prompts/rvp.txt`. A six-item checklist the model is told to
mentally run before answering. It also pins the output format:

```
```verilog
<full infected module>
```
TAXONOMY: HTx | trigger=... | payload=...
EXPLANATION: ...
```

`src/response_parser.py` enforces that format. If any part is missing,
`src/agent.py` calls the model once more with
`prompts.build_revision_prompt`, which quotes the previous answer and
the exact list of missing parts.

## Evaluation

`src/evaluator.py` runs iverilog three times per infected design:

* **Eval0 — compile.** `iverilog -g2001 infected.v original_tb.v`. The
  success of this stage is the paper's Eval0.
* **Eval1 — dormant functionality.** Run the original self-checking
  testbench against the infected RTL. Any `FAIL` line, or the absence of
  `All tests passed!`, fails Eval1 (the trojan is not dormant on normal
  inputs).
* **Eval2 — trigger activation.** Each benchmark ships a stress
  testbench in `benchmarks/<name>/activation/`. That testbench drives
  many random operations, tracks a shadow of the expected behaviour, and
  prints `TROJAN TRIGGERED` the moment the infected RTL deviates. The
  clean designs have been verified to produce **0 mismatches** on the
  activation testbenches, so a `TROJAN TRIGGERED` line is unambiguous
  evidence that the payload fired.

Eval3 (post-synthesis survival via Yosys + Sky130) is **not** run in
this reproduction; the paper's Eval3 only reports the fraction of
Eval2-passing HTs that survive synthesis, and setting up a PDK was not
feasible in the 32-hour assignment window.
