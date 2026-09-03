"""End-to-end data-to-model training orchestration.

This module composes TigerDataLab's existing dataset preparation, deterministic
splitting, training backends, and evaluation primitives into one explicit API.
It does not hide the fact that model training requires a compatible backend and
hardware; instead it records each stage so runs are reproducible and auditable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping
import json

from .datasets import deterministic_split_records
from .evaluation import EvaluationResult, evaluate
from .pipeline import AIDataset
from .training import TrainingBackend, UniversalTrainer


@dataclass
class AITrainingRun:
    """Artifacts and state produced by :class:`AITrainingProject`."""

    name: str
    task: str
    output_dir: Path
    dataset: AIDataset | None = None
    splits: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    training_result: Any = None
    evaluation_result: EvaluationResult | None = None

    def summary(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "task": self.task,
            "output_dir": str(self.output_dir),
            "prepared_records": len(self.dataset.prepared) if self.dataset else 0,
            "splits": {key: len(value) for key, value in self.splits.items()},
            "trained": self.training_result is not None,
            "evaluated": self.evaluation_result is not None,
            "evaluation_score": (
                self.evaluation_result.score if self.evaluation_result else None
            ),
        }


class AITrainingProject:
    """Single-project facade for the complete data-to-model lifecycle.

    Typical lifecycle::

        project.clean_data()
        project.validate_data()
        project.convert_to_sft()
        project.split_dataset()
        project.train_model(model="Qwen/...", method="lora")
        project.evaluate_model(callable_model, evaluation_records)

    The methods are intentionally explicit. A project can stop after dataset
    preparation, use a custom training backend, or evaluate a model hosted by
    another service. No API key is required for local open-model training.
    """

    def __init__(
        self,
        name: str,
        source: str | Path | Iterable[Mapping[str, Any]],
        *,
        output_dir: str | Path = "./tigerdatalab-run",
        task: str = "sft",
    ) -> None:
        if not name.strip():
            raise ValueError("name cannot be empty")
        self.name = name
        self.source = source
        self.output_dir = Path(output_dir)
        self.task = task.lower()
        self.dataset: AIDataset | None = None
        self.splits: dict[str, list[dict[str, Any]]] = {}
        self.training_result: Any = None
        self.evaluation_result: EvaluationResult | None = None

    @property
    def run(self) -> AITrainingRun:
        return AITrainingRun(
            name=self.name,
            task=self.task,
            output_dir=self.output_dir,
            dataset=self.dataset,
            splits=self.splits,
            training_result=self.training_result,
            evaluation_result=self.evaluation_result,
        )

    def clean_data(
        self,
        *,
        min_chars: int = 1,
        max_chars: int | None = None,
    ) -> "AITrainingProject":
        """Prepare safe records: PII masking, formatting and deduplication."""
        self.dataset = AIDataset(self.source, task=self.task).run(
            min_chars=min_chars,
            max_chars=max_chars,
        )
        return self

    def validate_data(self):
        """Validate the prepared dataset and return its validation report."""
        if self.dataset is None:
            self.clean_data()
        assert self.dataset is not None
        if self.dataset.validation is None:
            self.dataset.run()
        return self.dataset.validation

    def convert_to_sft(self) -> "AITrainingProject":
        """Re-run preparation using the SFT adapter."""
        self.task = "sft"
        return self.clean_data()

    def split_dataset(
        self,
        *,
        train_ratio: float = 0.8,
        validation_ratio: float = 0.1,
        strategy: str = "hash",
    ) -> dict[str, list[dict[str, Any]]]:
        """Create reproducible train/validation/test splits."""
        if self.dataset is None:
            self.clean_data()
        assert self.dataset is not None
        if not 0 < train_ratio < 1 or not 0 <= validation_ratio < 1:
            raise ValueError("train_ratio must be > 0 and < 1; validation_ratio must be >= 0 and < 1")
        if train_ratio + validation_ratio >= 1:
            raise ValueError("train_ratio + validation_ratio must be < 1")
        if strategy == "hash":
            self.splits = deterministic_split_records(
                self.dataset.prepared, train_ratio, validation_ratio
            )
        elif strategy == "positional":
            from .datasets import split_records
            self.splits = split_records(
                self.dataset.prepared, train_ratio, validation_ratio
            )
        else:
            raise ValueError("strategy must be 'hash' or 'positional'")
        return self.splits

    def export_dataset(self) -> Path:
        """Export the prepared dataset and audit artifacts."""
        if self.dataset is None:
            self.clean_data()
        assert self.dataset is not None
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.dataset.export(self.output_dir)
        return self.output_dir

    def train_model(
        self,
        *,
        model: Any,
        method: str = "sft",
        backend: TrainingBackend | str = "auto",
        output_dir: str | Path | None = None,
        epochs: float = 1.0,
        batch_size: int = 2,
        learning_rate: float = 2e-5,
        max_seq_length: int | None = None,
        gradient_accumulation_steps: int = 1,
        **options: Any,
    ) -> Any:
        """Train using a compatible TigerDataLab training backend.

        ``method='lora'`` enables PEFT/LoRA in the built-in Transformers backend.
        Other methods/backends can be supplied through ``backend`` and options.
        """
        if self.dataset is None:
            self.clean_data()
        if not self.splits:
            self.split_dataset()
        train_records = self.splits.get("train", [])
        if not train_records:
            raise ValueError("training split is empty")
        target = Path(output_dir) if output_dir is not None else self.output_dir / "model"
        trainer = UniversalTrainer(model=model, output_dir=str(target), backend=backend)
        train_options = dict(options)
        if method.lower() in {"lora", "qlora"}:
            train_options["use_lora"] = True
            if method.lower() == "qlora":
                train_options["load_in_4bit"] = True
        self.training_result = trainer.train(
            train_records,
            task="sft" if method.lower() in {"sft", "lora", "qlora"} else method,
            epochs=epochs,
            batch_size=batch_size,
            learning_rate=learning_rate,
            max_seq_length=max_seq_length,
            gradient_accumulation_steps=gradient_accumulation_steps,
            **train_options,
        )
        return self.training_result

    def evaluate_model(
        self,
        model: Callable[[str], str],
        records: Iterable[Mapping[str, Any]] | None = None,
        *,
        scorer: Callable[[str, Mapping[str, Any]], bool] | None = None,
    ) -> EvaluationResult:
        """Evaluate a callable model against explicit evaluation records.

        Records should contain ``prompt`` (or ``input``) and optionally
        ``expected``. The callable can wrap a local fine-tuned model, OpenRouter,
        another provider, or any application endpoint.
        """
        if records is None:
            if not self.splits:
                self.split_dataset()
            records = self.splits.get("test", [])
        self.evaluation_result = evaluate(model, records, scorer=scorer)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "evaluation_report.json").write_text(
            json.dumps(
                {
                    "total": self.evaluation_result.total,
                    "passed": self.evaluation_result.passed,
                    "failed": self.evaluation_result.failed,
                    "score": self.evaluation_result.score,
                    "average_latency_ms": self.evaluation_result.average_latency_ms,
                    "failures": self.evaluation_result.failures,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return self.evaluation_result

    def export_run_manifest(self) -> Path:
        """Write a compact machine-readable run manifest."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / "run_manifest.json"
        path.write_text(
            json.dumps(self.run.summary(), indent=2, default=str),
            encoding="utf-8",
        )
        return path
