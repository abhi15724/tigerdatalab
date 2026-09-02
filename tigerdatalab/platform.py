"""Unified production-oriented Data-to-AI platform facade."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable
import json

import numpy as np
import pandas as pd

from .core import analyze
from .ai import AIDataset, CompanyAI, Document, KnowledgeBase, ModelRouter, UniversalTrainer
from .ai.providers import Provider


@dataclass(frozen=True)
class DatasetProfile:
    rows: int
    columns: int
    missing_cells: int
    duplicate_rows: int
    numeric_columns: tuple[str, ...]
    categorical_columns: tuple[str, ...]


@dataclass
class DataPipeline:
    """Deterministic ETL pipeline suitable for local or CI execution."""
    steps: list[tuple[str, Callable[[pd.DataFrame], pd.DataFrame]]] = field(default_factory=list)

    def add(self, name: str, transform: Callable[[pd.DataFrame], pd.DataFrame]) -> "DataPipeline":
        if not name.strip():
            raise ValueError("step name cannot be empty")
        if not callable(transform):
            raise TypeError("transform must be callable")
        self.steps.append((name, transform))
        return self

    def run(self, frame: pd.DataFrame) -> pd.DataFrame:
        current = frame.copy()
        for name, transform in self.steps:
            result = transform(current)
            if not isinstance(result, pd.DataFrame):
                raise TypeError(f"Data pipeline step {name!r} must return a pandas DataFrame")
            current = result
        return current

    def save_manifest(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps({"steps": [name for name, _ in self.steps]}, indent=2), encoding="utf-8")


class DataScience:
    """Dependency-light data-science helpers with reproducible behavior."""

    @staticmethod
    def profile(frame: pd.DataFrame) -> DatasetProfile:
        numeric = tuple(frame.select_dtypes(include=[np.number]).columns.astype(str))
        categorical = tuple(c for c in frame.columns.astype(str) if c not in numeric)
        return DatasetProfile(len(frame), len(frame.columns), int(frame.isna().sum().sum()), int(frame.duplicated().sum()), numeric, categorical)

    @staticmethod
    def train_test_split(frame: pd.DataFrame, test_size: float = 0.2, seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
        if not 0 < test_size < 1:
            raise ValueError("test_size must be between 0 and 1")
        rng = np.random.default_rng(seed)
        indices = np.arange(len(frame))
        rng.shuffle(indices)
        cut = int(round(len(frame) * (1 - test_size)))
        return frame.iloc[indices[:cut]].reset_index(drop=True), frame.iloc[indices[cut:]].reset_index(drop=True)

    @staticmethod
    def correlation(frame: pd.DataFrame) -> pd.DataFrame:
        return frame.select_dtypes(include=[np.number]).corr()


@dataclass
class AIProject:
    """General AI training project backed by TigerDataLab's training layer."""
    name: str
    task: str = "sft"

    def prepare(self, source: Any, output_dir: str | Path | None = None) -> AIDataset:
        dataset = AIDataset(source, task=self.task).run()
        if output_dir is not None:
            dataset.export(output_dir)
        return dataset

    def trainer(self, model: str, output_dir: str | Path, **kwargs: Any) -> UniversalTrainer:
        return UniversalTrainer(model=model, output_dir=str(output_dir), **kwargs)


@dataclass
class CompanyAIProject:
    """Company AI project combining knowledge, provider model and workflow."""
    name: str
    ai: CompanyAI | None = None
    knowledge_base: KnowledgeBase = field(default_factory=KnowledgeBase)
    workflow: Any = None
    _system: str | None = field(default=None, repr=False)

    def add_knowledge(self, source: str, text: str, **metadata: Any) -> "CompanyAIProject":
        self.knowledge_base.add(Document(source, text, {k: str(v) for k, v in metadata.items()}))
        if self.ai is not None:
            self.ai.knowledge_base = self.knowledge_base
        return self

    def connect(self, provider: Provider, model: str, *, system: str | None = None) -> "CompanyAIProject":
        router = ModelRouter()
        router.add(provider, model)
        self.ai = CompanyAI(router, knowledge_base=self.knowledge_base, workflow=self.workflow)
        self._system = system
        return self

    def attach(self, ai: CompanyAI) -> "CompanyAIProject":
        self.ai = ai
        self.ai.knowledge_base = self.knowledge_base
        return self

    def ask(self, prompt: str, **kwargs: Any):
        if self.ai is None:
            raise ValueError("Connect or attach a CompanyAI before asking questions")
        if self._system is not None and "system" not in kwargs:
            kwargs["system"] = self._system
        return self.ai.ask(prompt, **kwargs)

    def run(self, inputs: dict[str, Any] | None = None):
        if self.ai is None:
            raise ValueError("Connect or attach a CompanyAI before running the workflow")
        return self.ai.run(inputs)


class TigerDataLab:
    """Single entry point for data analytics, engineering, data science and AI."""
    def __init__(self, project: str = "default") -> None:
        if not project.strip():
            raise ValueError("project cannot be empty")
        self.project = project
        self.engineering = DataPipeline()
        self.data_science = DataScience()

    def load(self, source: str | Path) -> pd.DataFrame:
        path = Path(source)
        suffix = path.suffix.lower()
        if suffix == ".csv": return pd.read_csv(path)
        if suffix in {".json", ".jsonl"}: return pd.read_json(path, lines=suffix == ".jsonl")
        if suffix in {".xlsx", ".xls"}: return pd.read_excel(path)
        if suffix == ".parquet": return pd.read_parquet(path)
        raise ValueError(f"Unsupported data source: {suffix or 'no extension'}")

    def profile(self, frame: pd.DataFrame) -> DatasetProfile: return self.data_science.profile(frame)
    def analyze(self, source: str | Path): return analyze(source)
    def ai_training(self, name: str, task: str = "sft") -> AIProject: return AIProject(name=name, task=task)
    def company_ai(self, name: str) -> CompanyAIProject: return CompanyAIProject(name=name)


def create_project(name: str = "default") -> TigerDataLab:
    """Create the unified TigerDataLab platform object."""
    return TigerDataLab(name)
