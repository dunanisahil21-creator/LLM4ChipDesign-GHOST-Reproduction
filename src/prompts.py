"""Loader for the three prompt-engineering strategies used by GHOST.

The prompt text itself lives in the top-level ``prompts/`` folder so it
can be read, cited, and audited without having to touch Python. This
module just concatenates the parts in the order the paper describes:
Role-Based Prompting (RBP), Contextual Trojan Prompting (CTP) for the
chosen HT category, and Reflexive Validation Prompting (RVP).
"""
from pathlib import Path

_PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _read(name: str) -> str:
    return (_PROMPT_DIR / name).read_text().strip()


def rbp() -> str:
    return _read("rbp.txt")


def ctp(ht_type: str) -> str:
    ht_type = ht_type.upper()
    if ht_type not in {"HT1", "HT2", "HT3"}:
        raise ValueError(f"Unknown HT type {ht_type!r} (expected HT1/HT2/HT3)")
    return _read(f"ctp_{ht_type.lower()}.txt")


def rvp() -> str:
    return _read("rvp.txt")


def build_prompt(ht_type: str, benchmark_name: str, rtl_source: str) -> str:
    """Assemble the combined RBP + CTP + RVP prompt for a single call."""
    return (
        f"{rbp()}\n\n"
        f"{ctp(ht_type)}\n\n"
        f"Target design: `{benchmark_name}`.\n"
        f"Clean Verilog source:\n```verilog\n{rtl_source}\n```\n\n"
        f"{rvp()}\n"
    )


def build_revision_prompt(previous_response: str, issues: list[str]) -> str:
    """Prompt used when the Reflexive Validation self-check flags an issue."""
    bullet = "\n".join(f"  - {i}" for i in issues)
    return (
        "Your previous answer did not pass the Reflexive Validation "
        "checklist. Issues:\n"
        f"{bullet}\n\n"
        "Please revise and resend your answer in the EXACT required "
        "format (```verilog``` block, then TAXONOMY and EXPLANATION lines). "
        "Do not apologise or add commentary.\n\n"
        "For reference, your previous answer was:\n"
        f"{previous_response}\n"
    )
