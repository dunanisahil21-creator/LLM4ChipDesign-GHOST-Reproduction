"""Entrypoint: run the GHOST agent on a set of benchmarks and HT types,
then collate the Eval0/1/2 results.

  python -m src.run_ghost --benchmark sram uart_tx --ht-type HT1 HT2 HT3
"""
from __future__ import annotations
import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

from .agent import GhostAgent
from .evaluator import evaluate

ROOT = Path(__file__).resolve().parent.parent

BENCH = {
    "sram": {
        "rtl":          ROOT / "benchmarks/sram/sram.v",
        "tb":           ROOT / "benchmarks/sram/sram_tb.v",
        "tb_top":       "sram_tb",
        "act_tb":       ROOT / "benchmarks/sram/activation/sram_activation_tb.v",
        "act_tb_top":   "sram_activation_tb",
        "top":          "sram",
    },
    "uart_tx": {
        "rtl":          ROOT / "benchmarks/uart_tx/uart_tx.v",
        "tb":           ROOT / "benchmarks/uart_tx/uart_tx_tb.v",
        "tb_top":       "uart_tx_tb",
        "act_tb":       ROOT / "benchmarks/uart_tx/activation/uart_tx_activation_tb.v",
        "act_tb_top":   "uart_tx_activation_tb",
        "top":          "uart_tx",
    },
}


@dataclass
class RunRow:
    benchmark: str
    ht_type: str
    model: str
    eval0: int
    eval1: int
    eval2: int
    taxonomy: str
    notes: str


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark", nargs="+", default=["sram", "uart_tx"],
                    choices=sorted(BENCH.keys()))
    ap.add_argument("--ht-type", nargs="+", default=["HT1", "HT2", "HT3"],
                    choices=["HT1", "HT2", "HT3"])
    ap.add_argument("--model", default="gpt-4o-mini")
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--out", default=str(ROOT / "results"))
    args = ap.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    log_dir = ROOT / "agent_logs"

    agent = GhostAgent(model=args.model, temperature=args.temperature)

    rows: list[RunRow] = []
    for bench in args.benchmark:
        cfg = BENCH[bench]
        clean_rtl = cfg["rtl"].read_text()
        for ht in args.ht_type:
            print(f"\n=== {bench} / {ht} / {args.model} ===", flush=True)
            parsed, call = agent.generate(ht, bench, clean_rtl, log_dir=log_dir)
            notes = ""
            if parsed.rtl is None:
                print(f"  format failure: {parsed.missing}", flush=True)
                rows.append(RunRow(bench, ht, args.model, 0, 0, 0,
                                   parsed.taxonomy or "", f"format_failure"))
                continue

            run_dir = out_dir / f"{bench}_{ht}"
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "infected.v").write_text(parsed.rtl)
            (run_dir / "taxonomy.txt").write_text(parsed.taxonomy or "")
            (run_dir / "explanation.txt").write_text(parsed.explanation or "")

            res = evaluate(
                infected_rtl=parsed.rtl,
                original_tb=cfg["tb"],
                activation_tb=cfg["act_tb"],
                top_module=cfg["top"],
                original_tb_top=cfg["tb_top"],
                activation_tb_top=cfg["act_tb_top"],
            )
            (run_dir / "eval_compile.log").write_text(res.log_compile)
            (run_dir / "eval1_functional.log").write_text(res.log_eval1)
            (run_dir / "eval2_trigger.log").write_text(res.log_eval2)

            print(f"  Eval0 compile={res.eval0_compile}  "
                  f"Eval1 func={res.eval1_functional}  "
                  f"Eval2 trig={res.eval2_triggered}", flush=True)

            rows.append(RunRow(
                benchmark=bench, ht_type=ht, model=args.model,
                eval0=int(res.eval0_compile),
                eval1=int(res.eval1_functional),
                eval2=int(res.eval2_triggered),
                taxonomy=(parsed.taxonomy or "").replace("\n", " "),
                notes=notes,
            ))

    _write_csv(out_dir / "eval_table.csv", rows)
    _write_summary(out_dir / "summary.md", rows)
    print(f"\nWrote {out_dir/'eval_table.csv'} and {out_dir/'summary.md'}")
    return 0


def _write_csv(path: Path, rows: list[RunRow]) -> None:
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["benchmark", "ht_type", "model",
                    "eval0_compile", "eval1_functional", "eval2_triggered",
                    "taxonomy", "notes"])
        for r in rows:
            w.writerow([r.benchmark, r.ht_type, r.model,
                        r.eval0, r.eval1, r.eval2, r.taxonomy, r.notes])


def _write_summary(path: Path, rows: list[RunRow]) -> None:
    lines = [
        "# GHOST reproduction — Eval summary",
        "",
        "Each row is one LLM call (RBP + CTP + RVP, with up to one RVP revision).",
        "",
        "| Benchmark | HT | Model | Eval0 compile | Eval1 dormant | Eval2 triggered | Taxonomy |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r.benchmark} | {r.ht_type} | {r.model} | "
            f"{'✓' if r.eval0 else '✗'} | "
            f"{'✓' if r.eval1 else '✗'} | "
            f"{'✓' if r.eval2 else '✗'} | "
            f"{r.taxonomy or '—'} |"
        )
    # Aggregate rates like the paper's Table 2.
    n = len(rows)
    if n:
        c = sum(r.eval0 for r in rows)
        f = sum(r.eval1 for r in rows if r.eval0)
        t = sum(r.eval2 for r in rows if r.eval1)
        denom_c = n
        denom_f = sum(1 for r in rows if r.eval0) or 1
        denom_t = sum(1 for r in rows if r.eval1) or 1
        lines += [
            "",
            "## Aggregate",
            "",
            f"- **Eval0 (compile)**: {c}/{denom_c} = {100*c/denom_c:.1f} %",
            f"- **Eval1 (functional | compiled)**: {f}/{denom_f} = {100*f/denom_f:.1f} %",
            f"- **Eval2 (triggered | functional)**: {t}/{denom_t} = {100*t/denom_t:.1f} %",
        ]
    path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())
