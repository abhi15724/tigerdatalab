"""Compose model, retrieval, tools, workflows and evaluation into one API."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .evaluation import Evaluator, EvaluationResult
from .rag import KnowledgeBase
from .router import ModelRouter
from .tools import ToolRegistry
from .workflows import Workflow, WorkflowResult


@dataclass
class AIResult:
    output: str
    model: str | None = None
    context: str = ""
    tool_results: dict[str, Any] | None = None


class CompanyAI:
    """Production composition root for a company-specific AI application.

    TigerDataLab does not train proprietary hosted models itself; it prepares
    data, retrieval context, tools and evaluation around the model a customer chooses.
    """

    def __init__(self, router: ModelRouter, *, knowledge_base: KnowledgeBase | None = None,
                 tools: ToolRegistry | None = None, workflow: Workflow | None = None,
                 evaluator: Evaluator | None = None):
        self.router = router
        self.knowledge_base = knowledge_base
        self.tools = tools or ToolRegistry()
        self.workflow = workflow
        self.evaluator = evaluator or Evaluator()

    def ask(self, prompt: str, *, system: str | None = None, top_k: int = 5, **kwargs: Any) -> AIResult:
        if not prompt or not prompt.strip():
            raise ValueError("prompt cannot be empty")
        context = self.knowledge_base.context(prompt, top_k=top_k) if self.knowledge_base else ""
        messages: list[Mapping[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        if context:
            messages.append({"role": "system", "content": "Relevant company context:\n" + context})
        messages.append({"role": "user", "content": prompt})
        response = self.router.chat(messages, tools=self.tools.schemas(), **kwargs) if len(self.tools) else self.router.chat(messages, **kwargs)
        return AIResult(response.content, response.model, context)

    def run(self, inputs: Mapping[str, Any] | None = None) -> WorkflowResult:
        if self.workflow is None:
            raise ValueError("No workflow configured")
        return self.workflow.run(inputs)

    def evaluate(self, records: list[Mapping[str, Any]]) -> EvaluationResult:
        return self.evaluator.evaluate(lambda messages: self.router.chat(messages).content, records)
