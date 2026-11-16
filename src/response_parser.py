"""Parse the LLM response into its three expected parts.

The GHOST RVP template asks the model to produce:

  * a ```verilog ... ``` fenced block with the infected RTL,
  * a ``TAXONOMY:`` line summarising HT category / trigger / payload,
  * an ``EXPLANATION:`` block.

This module extracts those three parts and reports what, if anything, is
missing so the caller can decide whether to ask the model to revise.
"""
import re
from dataclasses import dataclass


@dataclass
class ParsedResponse:
    rtl: str | None
    taxonomy: str | None
    explanation: str | None
    missing: list[str]


_CODE_RE = re.compile(r"```(?:verilog|systemverilog|v|rtl)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
_TAX_RE = re.compile(r"^\s*TAXONOMY\s*:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
_EXP_RE = re.compile(r"^\s*EXPLANATION\s*:\s*(.*?)(?:\Z|\n\s*\n)", re.IGNORECASE | re.DOTALL | re.MULTILINE)


def parse(response: str) -> ParsedResponse:
    missing: list[str] = []

    code_m = _CODE_RE.search(response)
    rtl = code_m.group(1).strip() if code_m else None
    if rtl is None:
        # Fallback: some models skip the fence when the file is large.
        if "module " in response and "endmodule" in response:
            start = response.index("module ")
            end = response.rindex("endmodule") + len("endmodule")
            rtl = response[start:end].strip()
        else:
            missing.append("no ```verilog``` block and no module/endmodule found")

    tax_m = _TAX_RE.search(response)
    taxonomy = tax_m.group(1).strip() if tax_m else None
    if taxonomy is None:
        missing.append("missing TAXONOMY: line")

    exp_m = _EXP_RE.search(response)
    explanation = exp_m.group(1).strip() if exp_m else None
    if explanation is None:
        missing.append("missing EXPLANATION: block")

    return ParsedResponse(rtl=rtl, taxonomy=taxonomy, explanation=explanation, missing=missing)
