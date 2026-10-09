"""Provider-specific native tool-calling adapters for AgentRuntime."""
from __future__ import annotations

import json
from typing import Any

from .agent_runtime import AgentRuntimeError, AgentToolCall, AgentTurn


def _anthropic_history(messages):
    system = "\n\n".join(str(m.get("content", "")) for m in messages if m.get("role") == "system") or None
    history = []
    for m in messages:
        role, content = m.get("role"), m.get("content")
        if role == "system":
            continue
        if role == "tool":
            try:
                result = json.loads(content or "null")
            except (TypeError, ValueError):
                result = content
            history.append({"role": "user", "content": [{
                "type": "tool_result", "tool_use_id": m.get("tool_call_id", ""),
                "content": json.dumps(result, ensure_ascii=False, default=str),
            }]})
            continue
        blocks = [{"type": "text", "text": str(content)}] if content else []
        if role == "assistant":
            for call in m.get("tool_calls", []) or []:
                try:
                    args = json.loads(call["function"].get("arguments") or "{}")
                except (KeyError, TypeError, ValueError):
                    args = {}
                blocks.append({"type": "tool_use", "id": call.get("id", call["function"]["name"]),
                               "name": call["function"]["name"], "input": args})
        history.append({"role": "assistant" if role == "assistant" else "user",
                        "content": blocks or [{"type": "text", "text": ""}]})
    return system, history


def anthropic_agent_model(provider, model: str, **options):
    """Adapt Anthropic Messages tool_use/tool_result to normalized AgentTurn."""
    if not model or not model.strip():
        raise ValueError("model cannot be empty")
    def call(messages, schemas):
        system, history = _anthropic_history(messages)
        kwargs = dict(options)
        kwargs["system"] = system or ""
        if schemas:
            kwargs["tools"] = [{
                "name": s["function"]["name"],
                "description": s["function"].get("description", ""),
                "input_schema": s["function"].get("parameters") or {"type": "object", "properties": {}},
            } for s in schemas]
        response = provider.chat(history, model=model, **kwargs)
        calls = []
        for block in response.raw.get("content", []) or []:
            if block.get("type") == "tool_use":
                calls.append(AgentToolCall(str(block.get("id", block["name"])),
                                           str(block["name"]), block.get("input") or {}))
        raw_usage = response.usage or {}
        usage = {"input_tokens": int(raw_usage.get("input_tokens", 0) or 0),
                 "output_tokens": int(raw_usage.get("output_tokens", 0) or 0)}
        usage["total_tokens"] = usage["input_tokens"] + usage["output_tokens"]
        return AgentTurn(response.text, tuple(calls), usage, response.model)
    return call


def _gemini_history(messages):
    system = "\n\n".join(str(m.get("content", "")) for m in messages if m.get("role") == "system") or None
    history = []
    for m in messages:
        role, content = m.get("role"), m.get("content")
        if role == "system":
            continue
        if role == "tool":
            try:
                result = json.loads(content or "null")
            except (TypeError, ValueError):
                result = content
            history.append({"role": "user", "parts": [{"functionResponse": {
                "name": m.get("name", "tool"), "response": {"result": result},
            }}]})
            continue
        parts = [{"text": str(content)}] if content else []
        if role == "assistant":
            for tool_call in m.get("tool_calls", []) or []:
                try:
                    args = json.loads(tool_call["function"].get("arguments") or "{}")
                except (KeyError, TypeError, ValueError):
                    args = {}
                parts.append({"functionCall": {"name": tool_call["function"]["name"], "args": args}})
        history.append({"role": "model" if role == "assistant" else "user", "parts": parts or [{"text": ""}]})
    return system, history


def gemini_agent_model(provider, model: str, **options):
    """Adapt Gemini functionCall/functionResponse to AgentRuntime.

    Requires a provider exposing generate_content(contents, model, system_instruction,
    **options); TigerDataLab's GeminiProvider implements this native method.
    """
    if not model or not model.strip():
        raise ValueError("model cannot be empty")
    if not callable(getattr(provider, "generate_content", None)):
        raise TypeError("Gemini provider must implement generate_content()")
    def call(messages, schemas):
        system, history = _gemini_history(messages)
        kwargs = dict(options)
        if schemas:
            kwargs["tools"] = [{"functionDeclarations": [{
                "name": s["function"]["name"],
                "description": s["function"].get("description", ""),
                "parameters": s["function"].get("parameters") or {"type": "object", "properties": {}},
            } for s in schemas]}]
        response = provider.generate_content(history, model=model, system_instruction=system, **kwargs)
        calls = []
        for i, part in enumerate(response.raw.get("candidates", [{}])[0].get("content", {}).get("parts", []) or []):
            function_call = part.get("functionCall")
            if function_call:
                calls.append(AgentToolCall(f"gemini-{i}", function_call["name"], function_call.get("args") or {}))
        raw_usage = response.usage or {}
        input_tokens = int(raw_usage.get("promptTokenCount", 0) or 0)
        output_tokens = int(raw_usage.get("candidatesTokenCount", 0) or 0)
        usage = {"input_tokens": input_tokens, "output_tokens": output_tokens,
                 "total_tokens": int(raw_usage.get("totalTokenCount", input_tokens + output_tokens) or 0)}
        return AgentTurn(response.text, tuple(calls), usage, response.model)
    return call
