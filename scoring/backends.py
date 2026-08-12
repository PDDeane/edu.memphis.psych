"""Inference backends for the scorer.

Two interchangeable paths, both returning a validated dict:

  ClaudeCliBackend  — drives the locally authenticated `claude` CLI with
                      --json-schema. Works with no API key, which is the
                      situation on this machine (no ANTHROPIC_API_KEY, no
                      `ant` profile). This is the default.

  AnthropicApiBackend — official Anthropic Python SDK, claude-opus-5,
                      structured outputs via output_config.format. Use this
                      in production: it is faster per call, supports prompt
                      caching of the shared rubric prefix, and does not carry
                      the CLI's own system prompt on every request.
"""

from __future__ import annotations

import json
import random
import re
import subprocess
import time

DEFAULT_MODEL_CLI = "opus"
DEFAULT_MODEL_API = "claude-opus-5"


class BackendError(RuntimeError):
    pass


def _extract_json(text: str) -> dict:
    """Parse a JSON object out of model output, tolerating code fences."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            raise BackendError(f"no JSON object in output: {text[:300]!r}")
        return json.loads(m.group(0))


class ClaudeCliBackend:
    def __init__(
        self,
        model: str = DEFAULT_MODEL_CLI,
        timeout: int = 300,
        max_budget_usd: float | None = None,
    ):
        self.model = model
        self.timeout = timeout
        self.max_budget_usd = max_budget_usd
        self.total_cost_usd = 0.0
        self.calls = 0

    def complete(
        self,
        system: str,
        prompt: str,
        schema: dict,
        retries: int = 3,
        allow_tools: list[str] | None = None,
        max_turns: int = 2,
    ) -> dict:
        """Retry with exponential backoff.

        Concurrency above ~6 workers makes the CLI exit non-zero with an empty
        stderr — transient, and almost certainly rate limiting. A single
        immediate retry was not enough: a 240-call run lost 118 items that way.
        """
        last: Exception | None = None
        for attempt in range(retries + 1):
            try:
                return self._once(system, prompt, schema, allow_tools, max_turns)
            except BackendError as e:
                last = e
                if attempt < retries:
                    time.sleep(min(2 ** attempt * 3 + random.uniform(0, 2), 45))
        raise last  # type: ignore[misc]

    def _once(
        self,
        system: str,
        prompt: str,
        schema: dict,
        allow_tools: list[str] | None = None,
        max_turns: int = 2,
    ) -> dict:
        cmd = [
            "claude",
            "-p",
            "--model",
            self.model,
            # The grading task is pure text-in/JSON-out, but the CLI ships a
            # tool-using agent by default. Left enabled, it reaches for a tool,
            # burns the single turn, and the call dies with error_max_turns.
            # Deny the tools and keep a spare turn as a safety net.
        ]
        if allow_tools:
            # Handout 3 item 1c needs to look at a graph image, so Read is
            # enabled for that item only and given extra turns to use it.
            cmd += ["--allowedTools", ",".join(allow_tools)]
        else:
            cmd += [
                "--disallowed-tools",
                "Bash,Read,Write,Edit,Glob,Grep,WebSearch,WebFetch,Task,TodoWrite,NotebookEdit",
            ]
        cmd += [
            "--max-turns",
            str(max_turns),
            "--exclude-dynamic-system-prompt-sections",
            "--system-prompt",
            system,
            "--json-schema",
            json.dumps(schema),
            "--output-format",
            "json",
        ]
        if self.max_budget_usd is not None:
            cmd += ["--max-budget-usd", str(self.max_budget_usd)]
        cmd.append(prompt)

        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=self.timeout, cwd="/tmp"
        )
        if proc.returncode != 0:
            # stderr is usually empty on the transient rate-limit exit, so keep
            # stdout too — otherwise the failure is undiagnosable after the fact.
            detail = (proc.stderr or "").strip() or (proc.stdout or "").strip()[:300]
            raise BackendError(f"claude exited {proc.returncode}: {detail or '(no output)'}")
        try:
            env = json.loads(proc.stdout)
        except json.JSONDecodeError:
            raise BackendError(f"non-JSON envelope: {proc.stdout[:300]!r}")
        if env.get("is_error"):
            detail = env.get("errors") or env.get("terminal_reason") or env.get("result")
            raise BackendError(f"claude reported error: {str(detail)[:300]}")

        self.calls += 1
        self.total_cost_usd += float(env.get("total_cost_usd") or 0.0)
        return _extract_json(env["result"])


class AnthropicApiBackend:
    """Official SDK path. Requires credentials (ANTHROPIC_API_KEY or an
    `ant auth login` profile — a bare Anthropic() client picks up either)."""

    def __init__(self, model: str = DEFAULT_MODEL_API, effort: str = "high"):
        import anthropic  # imported lazily so the CLI path needs no install

        self.client = anthropic.Anthropic()
        self.model = model
        self.effort = effort
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0

    def complete(
        self,
        system: str,
        prompt: str,
        schema: dict,
        allow_tools: list[str] | None = None,
        max_turns: int = 2,
    ) -> dict:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=16000,
            thinking={"type": "adaptive"},
            output_config={
                "effort": self.effort,
                "format": {"type": "json_schema", "schema": schema},
            },
            # Cache the rubric-bearing system prompt: it is byte-identical
            # across every call for a given item.
            system=[
                {
                    "type": "text",
                    "text": system,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": prompt}],
        )
        if resp.stop_reason == "refusal":
            raise BackendError("model refused the request")
        self.calls += 1
        self.input_tokens += resp.usage.input_tokens
        self.output_tokens += resp.usage.output_tokens
        text = next(b.text for b in resp.content if b.type == "text")
        return _extract_json(text)


class LoBlocksBackend:
    """score.py's prompt, sent down the SHIPPED route.

    Exists to separate two variables that were confounded for the whole project.
    score.py defaults to `cli`, i.e. Opus; the web and agreement.py post to
    lo-blocks' /api/llm/chat/completions, which answers as gpt-5-mini. So "the
    paper scorer scores higher than the shipped prompt" compared a different
    PROMPT *and* a different MODEL at once, and several prompt-wording
    experiments were run against a gap that may be neither.

    With this backend the prompt is score.py's and the model is the shipped one,
    so the difference against `--backend cli` is the model alone and the
    difference against agreement.py is the prompt alone.

    No profile is sent, so routes/llm.ts resolves `interactive` and injects its
    own max_completion_tokens — exactly what agreement.py relies on.
    """

    ENDPOINT = "http://localhost:8888/api/llm/chat/completions"

    def __init__(self, endpoint: str | None = None, timeout: int = 600,
                 retries: int = 6):
        self.endpoint = endpoint or self.ENDPOINT
        self.timeout = timeout
        self.retries = retries
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0

    def complete(
        self,
        system: str,
        prompt: str,
        schema: dict,
        allow_tools: list[str] | None = None,
        max_turns: int = 2,
    ) -> dict:
        import time
        import urllib.error
        import urllib.request

        payload = json.dumps({
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": prompt}],
            "tools": [],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "scoring", "strict": True,
                                "schema": schema},
            },
        }).encode()
        last: Exception | None = None
        # Same patience as agreement.py: the endpoint intermittently returns an
        # empty body, and a lost cell biases the item's rate.
        for attempt in range(self.retries + 1):
            req = urllib.request.Request(
                self.endpoint, data=payload,
                headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    env = json.loads(resp.read())
                self.calls += 1
                u = env.get("usage") or {}
                self.input_tokens += u.get("prompt_tokens") or 0
                self.output_tokens += u.get("completion_tokens") or 0
                return _extract_json(env["choices"][0]["message"]["content"])
            except (urllib.error.HTTPError, urllib.error.URLError,
                    ValueError, KeyError) as e:
                last = e
                if attempt < self.retries:
                    time.sleep(min(2 ** attempt * 5 + 2, 45))
        raise BackendError(f"lo-blocks endpoint failed: {last}")


def make_backend(kind: str, **kw):
    if kind == "cli":
        return ClaudeCliBackend(**kw)
    if kind == "api":
        return AnthropicApiBackend(**kw)
    if kind == "lo":
        return LoBlocksBackend(**kw)
    raise ValueError(f"unknown backend {kind!r}")
