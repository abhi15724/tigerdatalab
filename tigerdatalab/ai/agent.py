"""Unified company-agent lifecycle: prepare, teach, remember, act and evaluate."""
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


@dataclass
class CompanyAgent:
    """High-level facade for building a company-specific AI agent.

    Combines five controlled layers: training-data preparation and optional
    model fine-tuning, company knowledge retrieval, explicitly allow-listed
    tools, deterministic workflows, and evaluation.
    """

    name: str
    knowledge_base: KnowledgeBase = field(default_factory=KnowledgeBase)
    tools: ToolRegistry = field(default_factory=ToolRegistry)
    workflow: Workflow | None = None
    evaluator: Evaluator = field(default_factory=Evaluator)
    ai: CompanyAI | None = field(default=None, init=False, repr=False)
    training_dataset: AIDataset | None = field(default=None, init=False, repr=False)
    training_result: Any = field(default=None, init=False, repr=False)
    _system: str | None = field(default=None, init=False, repr=False)

    def prepare_training(
        self,
        source: Any,
        *,
        task: str = "sft",
        output_dir: str | Path | None = None,
        min_chars: int = 1,
        max_chars: int | None = None,
    ) -> AIDataset:
        """Prepare privacy-aware, validated and deduplicated company data."""
        dataset = AIDataset(source, task=task).run(
            min_chars=min_chars,
            max_chars=max_chars,
        )
        if output_dir is not None:
            dataset.export(output_dir)
        self.training_dataset = dataset
        return dataset

    def train(
        self,
        model: str,
        *,
        output_dir: str | Path,
        dataset: Any | None = None,
        backend: Any = "auto",
        task: str = "sft",
        **kwargs: Any,
    ) -> Any:
        """Train a compatible model using prepared company examples."""
        training_data = dataset if dataset is not None else self.training_dataset
        if training_data is None:
            raise ValueError("Prepare training data first or pass dataset explicitly")
        trainer = UniversalTrainer(model=model, output_dir=output_dir, backend=backend)
        self.training_result = trainer.train(training_data, task=task, **kwargs)
        return self.training_result

    def add_knowledge(self, source: str, text: str, **metadata: Any) -> "CompanyAgent":
        """Add current company knowledge for retrieval without retraining."""
        if not text or not text.strip():
            raise ValueError("knowledge text cannot be empty")
        self.knowledge_base.add(
            Document(source, text, {key: str(value) for key, value in metadata.items()})
        )
        if self.ai is not None:
            self.ai.knowledge_base = self.knowledge_base
        return self

    def add_tool(self, tool: Tool) -> "CompanyAgent":
        """Register an explicitly allow-listed company action."""
        self.tools.register(tool)
        if self.ai is not None:
            self.ai.tools = self.tools
        return self

    def connect(
        self,
        provider: Provider,
        model: str,
        *,
        system: str | None = None,
    ) -> "CompanyAgent":
        """Connect the runtime model used by the agent."""
        router = ModelRouter()
        router.add(provider, model)
        self.ai = CompanyAI(
            router,
            knowledge_base=self.knowledge_base,
            tools=self.tools,
            workflow=self.workflow,
            evaluator=self.evaluator,
        )
        self._system = system
        return self

    def attach(self, ai: CompanyAI) -> "CompanyAgent":
        """Attach an already configured CompanyAI runtime."""
        self.ai = ai
        self.ai.knowledge_base = self.knowledge_base
        self.ai.tools = self.tools
        self.ai.workflow = self.workflow
        self.ai.evaluator = self.evaluator
        return self

    def set_workflow(self, workflow: Workflow) -> "CompanyAgent":
        """Attach a controlled business workflow."""
        self.workflow = workflow
        if self.ai is not None:
            self.ai.workflow = workflow
        return self

    def ask(self, prompt: str, **kwargs: Any) -> AIResult:
        """Ask the connected company AI using company context and tools."""
        if self.ai is None:
            raise ValueError("Connect or attach a CompanyAI before asking questions")
        if self._system is not None and "system" not in kwargs:
            kwargs["system"] = self._system
        return self.ai.ask(prompt, **kwargs)

    def run(self, inputs: Mapping[str, Any] | None = None) -> WorkflowResult:
        """Execute the configured business workflow."""
        if self.ai is None:
            raise ValueError("Connect or attach a CompanyAI before running the workflow")
        return self.ai.run(inputs)

    def evaluate(self, records: list[Mapping[str, Any]]) -> EvaluationResult:
        """Evaluate the connected runtime against representative test cases."""
        if self.ai is None:
            raise ValueError("Connect or attach a CompanyAI before evaluation")
        return self.ai.evaluate(records)

    @property
    def ready(self) -> bool:
        """Whether a runtime model is connected."""
        return self.ai is not None


CompanyAgentProject = CompanyAgent
