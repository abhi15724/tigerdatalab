"""Unified company-agent lifecycle: prepare, teach, remember, act and deploy."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping
from .evaluation import EvaluationResult, Evaluator
from .pipeline import AIDataset
from .providers import Provider
from .rag import Document, KnowledgeBase
from .router import ModelRouter
from .system import AIResult, CompanyAI
from .tools import Tool, ToolRegistry
from .training import UniversalTrainer
from .workflows import Workflow, WorkflowResult
from .permissions import PermissionPolicy
from .approvals import ApprovalRequest, ApprovalStore

@dataclass
class CompanyAgent:
    """High-level facade for building, integrating and deploying a company AI agent."""
    name: str
    knowledge_base: KnowledgeBase = field(default_factory=KnowledgeBase)
    tools: ToolRegistry = field(default_factory=ToolRegistry)
    workflow: Workflow | None = None
    evaluator: Evaluator = field(default_factory=Evaluator)
    permissions: PermissionPolicy = field(default_factory=PermissionPolicy)
    approvals: ApprovalStore = field(default_factory=ApprovalStore)
    ai: CompanyAI | None = field(default=None, init=False, repr=False)
    training_dataset: AIDataset | None = field(default=None, init=False, repr=False)
    training_result: Any = field(default=None, init=False, repr=False)
    _system: str | None = field(default=None, init=False, repr=False)

    def prepare_training(self, source: Any, *, task: str = "sft", output_dir: str | Path | None = None, min_chars: int = 1, max_chars: int | None = None) -> AIDataset:
        dataset = AIDataset(source, task=task).run(min_chars=min_chars, max_chars=max_chars)
        if output_dir is not None:
            dataset.export(output_dir)
        self.training_dataset = dataset
        return dataset

    def train(self, model: str, *, output_dir: str | Path, dataset: Any | None = None, backend: Any = "auto", task: str = "sft", **kwargs: Any) -> Any:
        training_data = dataset if dataset is not None else self.training_dataset
        if training_data is None:
            raise ValueError("Prepare training data first or pass dataset explicitly")
        trainer = UniversalTrainer(model=model, output_dir=output_dir, backend=backend)
        self.training_result = trainer.train(training_data, task=task, **kwargs)
        return self.training_result

    def add_knowledge(self, source: str, text: str, **metadata: Any) -> "CompanyAgent":
        if not text or not text.strip():
            raise ValueError("knowledge text cannot be empty")
        self.knowledge_base.add(Document(source, text, {key: str(value) for key, value in metadata.items()}))
        if self.ai is not None:
            self.ai.knowledge_base = self.knowledge_base
        return self

    def add_tool(self, tool: Tool) -> "CompanyAgent":
        self.tools.register(tool)
        if self.ai is not None:
            self.ai.tools = self.tools
        return self

    def connect(self, provider: Provider, model: str, *, system: str | None = None) -> "CompanyAgent":
        router = ModelRouter()
        router.add(provider, model)
        self.ai = CompanyAI(router, knowledge_base=self.knowledge_base, tools=self.tools, workflow=self.workflow, evaluator=self.evaluator)
        self._system = system
        return self

    def attach(self, ai: CompanyAI) -> "CompanyAgent":
        self.ai = ai
        self.ai.knowledge_base = self.knowledge_base
        self.ai.tools = self.tools
        self.ai.workflow = self.workflow
        self.ai.evaluator = self.evaluator
        return self

    def set_workflow(self, workflow: Workflow) -> "CompanyAgent":
        self.workflow = workflow
        if self.ai is not None:
            self.ai.workflow = workflow
        return self

    def allow_tool(self, role: str, *tool_names: str) -> "CompanyAgent":
        self.permissions.allow(role, *tool_names)
        return self

    def check_tool_permission(self, role: str, tool_name: str) -> None:
        self.permissions.check(role, tool_name)

    def request_approval(self, action: str, arguments: Mapping[str, Any], *, requester: str | None = None) -> ApprovalRequest:
        return self.approvals.request(action, dict(arguments), requester)

    def decide_approval(self, request_id: str, approved: bool) -> None:
        self.approvals.decide(request_id, approved)

    def ask(self, prompt: str, **kwargs: Any) -> AIResult:
        if self.ai is None:
            raise ValueError("Connect or attach a CompanyAI before asking questions")
        if self._system is not None and "system" not in kwargs:
            kwargs["system"] = self._system
        return self.ai.ask(prompt, **kwargs)

    def run(self, inputs: Mapping[str, Any] | None = None) -> WorkflowResult:
        if self.ai is None:
            raise ValueError("Connect or attach a CompanyAI before running the workflow")
        return self.ai.run(inputs)

    def evaluate(self, records: list[Mapping[str, Any]]) -> EvaluationResult:
        if self.ai is None:
            raise ValueError("Connect or attach a CompanyAI before evaluation")
        return self.ai.evaluate(records)

    def deploy(self, *, host: str = "0.0.0.0", port: int = 8000, version: str = "1.0.0", **kwargs: Any) -> None:
        """Serve this ready agent as a real-time HTTP API."""
        from .deployment import serve
        serve(self, host=host, port=port, version=version, name=self.name, **kwargs)

    def app(self, *, version: str = "1.0.0") -> Any:
        """Return the ASGI application for container/cloud deployment."""
        from .deployment import create_app
        return create_app(self, name=self.name, version=version)

    @property
    def ready(self) -> bool:
        return self.ai is not None

CompanyAgentProject = CompanyAgent
