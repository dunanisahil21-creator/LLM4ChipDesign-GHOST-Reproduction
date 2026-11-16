"""iverilog harness implementing GHOST's Eval0, Eval1 and Eval2 stages.

  Eval0  — does the infected RTL compile?
  Eval1  — does the infected RTL still pass the ORIGINAL testbench
           (confirming the trojan is dormant on normal inputs)?
  Eval2  — does a trigger-activation testbench expose the payload
           (confirming the trojan actually fires)?

The success criterion for Eval1 and Eval2 is the presence of the
``All tests passed!`` marker in the simulation output (clean TB) and
``TROJAN TRIGGERED`` in the activation TB respectively. Any ``FAIL``
line in Eval1 also fails the stage.

Eval3 (post-synthesis survival via Yosys) is documented in the README
but intentionally not implemented.
"""
from __future__ import annotations
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class EvalResult:
    eval0_compile: bool
    eval1_functional: bool
    eval2_triggered: bool
    log_compile: str
    log_eval1: str
    log_eval2: str

    @property
    def row(self) -> dict:
        return {
            "eval0_compile": int(self.eval0_compile),
            "eval1_functional": int(self.eval1_functional),
            "eval2_triggered": int(self.eval2_triggered),
        }


def _run(cmd: list[str], cwd: Path, timeout: int = 60) -> tuple[int, str]:
    try:
        p = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return p.returncode, (p.stdout + p.stderr)
    except subprocess.TimeoutExpired as e:
        return 124, f"TIMEOUT after {timeout}s\n{e.stdout or ''}{e.stderr or ''}"


def evaluate(
    infected_rtl: str,
    original_tb: Path,
    activation_tb: Path | None,
    top_module: str,
    original_tb_top: str,
    activation_tb_top: str | None = None,
) -> EvalResult:
    """Run Eval0-2 on a single infected RTL string.

    * ``original_tb`` is the clean testbench shipped with the benchmark.
    * ``activation_tb`` is a per-HT testbench that asserts the trojan
      payload fires (prints the sentinel ``TROJAN TRIGGERED``). Pass
      ``None`` to skip Eval2 (e.g. when debugging).
    """
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "infected.v").write_text(infected_rtl)

        # Eval0 - compile against the ORIGINAL TB first.
        vvp1 = d / "eval1.vvp"
        rc, log0 = _run(
            ["iverilog", "-g2001", "-s", original_tb_top,
             "-o", str(vvp1), "infected.v", str(original_tb)],
            cwd=d,
        )
        eval0 = (rc == 0)
        eval1 = False
        log1 = ""
        if eval0:
            rc1, log1 = _run(["vvp", str(vvp1)], cwd=d)
            eval1 = (
                rc1 == 0
                and "All tests passed!" in log1
                and "FAIL" not in log1
            )

        # Eval2 - compile + run the activation TB.
        eval2 = False
        log2 = ""
        if eval0 and activation_tb is not None and activation_tb_top is not None:
            vvp2 = d / "eval2.vvp"
            rc2a, log2a = _run(
                ["iverilog", "-g2001", "-s", activation_tb_top,
                 "-o", str(vvp2), "infected.v", str(activation_tb)],
                cwd=d,
            )
            if rc2a == 0:
                rc2b, log2b = _run(["vvp", str(vvp2)], cwd=d)
                log2 = log2a + log2b
                eval2 = (rc2b == 0 and "TROJAN TRIGGERED" in log2b)
            else:
                log2 = log2a

    return EvalResult(
        eval0_compile=eval0,
        eval1_functional=eval1,
        eval2_triggered=eval2,
        log_compile=log0,
        log_eval1=log1,
        log_eval2=log2,
    )
