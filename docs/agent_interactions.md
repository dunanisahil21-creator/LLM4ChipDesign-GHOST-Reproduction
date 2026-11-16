# Agent interactions — walk-through

Every LLM call made during a `python -m src.run_ghost` run is dumped to
`agent_logs/<timestamp>_<benchmark>_<HT>.json`. Each file is a single
JSON object with these keys:

| Key | Meaning |
|---|---|
| `model` | The LLM id used (e.g. `gpt-4o-mini`). |
| `ht_type` | `HT1`, `HT2`, or `HT3`. |
| `benchmark` | `sram` or `uart_tx`. |
| `prompt` | The full concatenated prompt (RBP + CTP + clean RTL + RVP). |
| `response` | The LLM's first answer, verbatim. |
| `parsed` | `rtl`, `taxonomy`, `explanation`, `missing`. |
| `revision_prompt` | Only present if the first answer missed part of the required format. Shows exactly what we asked the model to fix. |
| `revision_response` | The second answer. |
| `revision_parsed` | Parsed form of the second answer. |
| `elapsed_s` | Wall-clock time for the whole call (first + optional revision). |

This directory is intentionally not `.gitignore`d. The assignment asks
for "Documentation of your agent interactions, including prompts,
errors, and refinements" and the JSON dump is that documentation.

## A representative run

The first infected SRAM (HT1 — change-function) produced by
`gpt-4o-mini` typically:

1. Adds an internal 7-bit counter `cnt_dbg`.
2. Picks a rare condition such as `cnt_dbg == 7'd97 && addr == 5'd13`.
3. Flips the top bit of `dout` when that condition fires.
4. Explains in the EXPLANATION block that `cnt_dbg` is initialised to
   zero on reset and advances every clock, which is why the clean
   testbench (which stops well before cycle 97) passes Eval1.

The matching `sram_activation_tb` eventually ticks past cycle 97 while
addressing location 13, observes a bit-flipped `dout`, and prints
`TROJAN TRIGGERED` — Eval2 passes.

## Common failure modes we saw

* **Fenced-block omitted.** `gpt-4o-mini` occasionally returns the RTL
  without the ```verilog fence; the parser's fallback (grab everything
  between the first `module` and the last `endmodule`) usually
  recovers.
* **Missing `TAXONOMY:` line.** The RVP revision pass fixes this ~95 %
  of the time; the remaining cases are logged as `format_failure`.
* **Trigger too aggressive.** Early prompt iterations let the model
  pick triggers that fired during Eval1 (the model broke dormancy). The
  current `prompts/ctp_*.txt` text explicitly forbids this.

See `agent_logs/` for the raw record.
