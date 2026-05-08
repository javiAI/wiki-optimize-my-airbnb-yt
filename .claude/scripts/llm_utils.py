"""
llm_utils.py — Shared `claude -p` wrapper.

Auto-switches to stdin when the prompt exceeds ARGV_PROMPT_MAX_BYTES, because
argv hits macOS ARG_MAX (~256 KB) with `OSError: Argument list too long` —
which is NOT a `subprocess.CalledProcessError`, so it would slip past handlers
that only catch `CalledProcessError`. Stdin sidesteps the limit entirely.
"""

from __future__ import annotations

import os
import re
import subprocess

CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "claude")
DEFAULT_TIMEOUT = 300
DEFAULT_MAX_TURNS = 3

# argv-mode prompt size limit. macOS ARG_MAX is 256 KB minus env+argv overhead;
# leave headroom. If a prompt exceeds this, fall through to stdin automatically.
ARGV_PROMPT_MAX_BYTES = 100_000


class LLMTimeout(RuntimeError):
    """Raised when the LLM call exceeds the timeout."""


class LLMFailure(RuntimeError):
    """Raised when the LLM exits non-zero. .stderr carries the captured stderr."""

    def __init__(self, message: str, stderr: str = ""):
        super().__init__(message)
        self.stderr = stderr


def call_claude(
    prompt: str,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    max_turns: int = DEFAULT_MAX_TURNS,
    via_stdin: bool | None = None,
) -> str:
    """Invoke `claude -p`; return raw stdout.

    via_stdin:
        - None (default): auto — argv if prompt fits, stdin otherwise.
        - True/False: force one mode.
    Raises LLMTimeout / LLMFailure on errors.
    """
    if via_stdin is None:
        via_stdin = len(prompt.encode("utf-8")) > ARGV_PROMPT_MAX_BYTES
    base = [CLAUDE_BIN, "-p"]
    if via_stdin:
        cmd = base + ["--max-turns", str(max_turns)]
        try:
            result = subprocess.run(
                cmd, input=prompt, capture_output=True, text=True,
                timeout=timeout, check=True,
            )
        except subprocess.TimeoutExpired:
            raise LLMTimeout(f"LLM call timed out after {timeout}s (stdin mode)")
        except subprocess.CalledProcessError as e:
            raise LLMFailure(f"LLM returned non-zero ({e.returncode})", e.stderr or "")
    else:
        cmd = base + [prompt, "--max-turns", str(max_turns)]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=timeout, check=True,
            )
        except subprocess.TimeoutExpired:
            raise LLMTimeout(f"LLM call timed out after {timeout}s")
        except subprocess.CalledProcessError as e:
            raise LLMFailure(f"LLM returned non-zero ({e.returncode})", e.stderr or "")
    return result.stdout


def strip_fences(text: str, *langs: str) -> str:
    """Strip leading/trailing ```lang ... ``` wrappers from LLM output.

    Pass the expected fence languages (`"markdown"`, `"md"`, `"json"`); without
    args, strips any fenced wrapper.
    """
    text = text.strip()
    if langs:
        pattern = "|".join(re.escape(l) for l in langs)
        text = re.sub(rf"^```(?:{pattern})?\s*\n?", "", text)
    else:
        text = re.sub(r"^```\w*\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()
