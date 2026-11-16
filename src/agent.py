"""The GHOST agent: wrap one or two LLM calls around the RBP+CTP+RVP
prompt and return the parsed infected RTL.

The agent applies one revision round: if the first response is missing
parts of the required format, the model is asked to fix just that
issue. Any further failure is returned to the caller so the run can be
marked as a format failure rather than silently looping.
"""
from __future__ import annotations
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path

from openai import OpenAI

from . import prompts
from . import response_parser as rp


@dataclass
class AgentCall:
    model: str
    ht_type: str
    benchmark: str
    prompt: str
    response: str
    parsed: dict
    revision_prompt: str | None
    revision_response: str | None
    revision_parsed: dict | None
    elapsed_s: float


class GhostAgent:
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 1.0):
        self.model = model
        self.temperature = temperature
        self.client = OpenAI()  # reads OPENAI_API_KEY from env

    # ------------------------------------------------------------------
    # low level LLM call
    # ------------------------------------------------------------------
    def _chat(self, prompt: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content or ""

    # ------------------------------------------------------------------
    # one full RBP + CTP + RVP round, with up to one revision pass
    # ------------------------------------------------------------------
    def generate(
        self, ht_type: str, benchmark: str, rtl: str, log_dir: Path | None = None
    ) -> tuple[rp.ParsedResponse, AgentCall]:
        prompt = prompts.build_prompt(ht_type, benchmark, rtl)
        t0 = time.time()
        response = self._chat(prompt)
        parsed = rp.parse(response)

        rev_prompt = rev_response = None
        rev_parsed_obj: rp.ParsedResponse | None = None
        if parsed.missing:
            rev_prompt = prompts.build_revision_prompt(response, parsed.missing)
            rev_response = self._chat(rev_prompt)
            rev_parsed_obj = rp.parse(rev_response)
            if not rev_parsed_obj.missing:
                parsed = rev_parsed_obj

        elapsed = time.time() - t0

        call = AgentCall(
            model=self.model,
            ht_type=ht_type,
            benchmark=benchmark,
            prompt=prompt,
            response=response,
            parsed=_parsed_to_dict(rp.parse(response)),
            revision_prompt=rev_prompt,
            revision_response=rev_response,
            revision_parsed=_parsed_to_dict(rev_parsed_obj) if rev_parsed_obj else None,
            elapsed_s=round(elapsed, 2),
        )

        if log_dir is not None:
            log_dir.mkdir(parents=True, exist_ok=True)
            stamp = time.strftime("%Y%m%d-%H%M%S")
            fname = f"{stamp}_{benchmark}_{ht_type}.json"
            (log_dir / fname).write_text(json.dumps(asdict(call), indent=2))

        return parsed, call


def _parsed_to_dict(p: rp.ParsedResponse) -> dict:
    return {
        "rtl": p.rtl,
        "taxonomy": p.taxonomy,
        "explanation": p.explanation,
        "missing": list(p.missing),
    }
