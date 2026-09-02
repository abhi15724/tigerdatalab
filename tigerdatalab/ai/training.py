"""Universal, adapter-based LLM training interfaces.

TigerDataLab cannot modify the weights of literally every model in existence: each
model family exposes different training interfaces. Instead this module provides a
stable training contract, a production Hugging Face/TRL backend for local/open
models, and a custom-backend escape hatch for any model or vendor that exposes its
own training API or SDK. Credentials and provider-specific implementation details
stay outside prepared datasets.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping


class TrainingDependencyError(ImportError):
    """Raised when optional LLM training dependencies are not installed."""


class TrainingError(RuntimeError):
    """Raised when a training backend cannot execute a request."""


@dataclass(frozen=True)
class TrainingCapabilities:
    """Capabilities advertised by a training backend."""

    supervised_fine_tuning: bool = True
    preference_tuning: bool = False
    quantization: bool = False
    peft: bool = False
    local: bool = True


@dataclass(frozen=True)
class TrainingRequest:
    """Normalized training request passed to every backend."""

    model: Any
    dataset: Any
    output_dir: str
    task: str = "sft"
    epochs: float = 1.0
    batch_size: int = 2
    learning_rate: float = 2e-5
    max_seq_length: int | None = None
    gradient_accumulation_steps: int = 1
    options: Mapping[str, Any] = field(default_factory=dict)


class TrainingBackend(ABC):
    """Adapter contract for any model training system."""

    name = "backend"
    capabilities = TrainingCapabilities()

    @abstractmethod
    def train(self, request: TrainingRequest) -> Any:
        """Train a model and return the backend-specific training result."""


class TransformersSFTBackend(TrainingBackend):
    """Fine-tune compatible causal LMs with Transformers + Datasets + TRL."""

    name = "transformers"
    capabilities = TrainingCapabilities(
        supervised_fine_tuning=True,
        preference_tuning=False,
        quantization=False,
        peft=False,
        local=True,
    )

    @staticmethod
    def _dependencies():
        try:
            from datasets import Dataset as HFDataset
            from datasets import load_dataset
            from transformers import AutoModelForCausalLM, AutoTokenizer
            from trl import SFTConfig, SFTTrainer
        except ImportError as exc:
            raise TrainingDependencyError(
                "LLM training requires optional dependencies. Install with "
                "`pip install 'tigerdatalab[train]'`."
            ) from exc
        return HFDataset, load_dataset, AutoModelForCausalLM, AutoTokenizer, SFTConfig, SFTTrainer

    @staticmethod
    def _load_dataset(dataset: Any, load_dataset: Callable[..., Any], hf_dataset_type: Any) -> Any:
        if hasattr(dataset, "prepared"):
            records = list(dataset.prepared)
            if not records:
                dataset.run()
                records = list(dataset.prepared)
            return hf_dataset_type.from_list(records)
        if isinstance(dataset, (str, Path)):
            path = str(dataset)
            return load_dataset("json", data_files=path, split="train")
        return dataset

    def train(self, request: TrainingRequest) -> Any:
        if request.task.lower() not in {"sft", "supervised", "supervised_fine_tuning"}:
            raise TrainingError(
                f"Transformers backend currently supports SFT only, not {request.task!r}"
            )
        if not isinstance(request.model, str) or not request.model.strip():
            raise TrainingError("Transformers backend requires a Hugging Face model id or local model path")

        HFDataset, load_dataset, AutoModelForCausalLM, AutoTokenizer, SFTConfig, SFTTrainer = self._dependencies()
        hf_dataset = self._load_dataset(request.dataset, load_dataset, HFDataset)

        tokenizer = AutoTokenizer.from_pretrained(request.model)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        model = AutoModelForCausalLM.from_pretrained(request.model)

        config_kwargs = dict(
            output_dir=request.output_dir,
            num_train_epochs=request.epochs,
            per_device_train_batch_size=request.batch_size,
            learning_rate=request.learning_rate,
            gradient_accumulation_steps=request.gradient_accumulation_steps,
            report_to="none",
            **dict(request.options),
        )
        if request.max_seq_length is not None:
            # Newer TRL exposes this as max_length; older releases may reject it.
            config_kwargs["max_length"] = request.max_seq_length

        args = SFTConfig(**config_kwargs)
        trainer_args = {"model": model, "args": args, "train_dataset": hf_dataset}
        try:
            trainer = SFTTrainer(processing_class=tokenizer, **trainer_args)
        except TypeError:
            trainer = SFTTrainer(tokenizer=tokenizer, **trainer_args)
        trainer.train()
        trainer.save_model(request.output_dir)
        tokenizer.save_pretrained(request.output_dir)
        return trainer


class CallableTrainingBackend(TrainingBackend):
    """Adapter for vendor SDKs, proprietary models, or custom training systems.

    The callable receives a normalized :class:`TrainingRequest`, so TigerDataLab
    can support a new model family without changing the dataset pipeline.
    """

    name = "custom"

    def __init__(self, function: Callable[[TrainingRequest], Any], *, name: str = "custom", capabilities: TrainingCapabilities | None = None):
        self.function = function
        self.name = name
        if capabilities is not None:
            self.capabilities = capabilities

    def train(self, request: TrainingRequest) -> Any:
        return self.function(request)


class UniversalTrainer:
    """Model-agnostic training facade with pluggable backends.

    ``backend='auto'`` uses the built-in Transformers backend for a model id/path.
    For a vendor-specific training API, pass a :class:`TrainingBackend` instance.
    This makes the public API stable even when model vendors use different SDKs.
    """

    def __init__(
        self,
        model: Any,
        output_dir: str | Path = "./tigerdatalab-model",
        *,
        backend: TrainingBackend | str = "auto",
    ) -> None:
        self.model = model
        self.output_dir = str(output_dir)
        self.backend = TransformersSFTBackend() if backend == "auto" else backend
        if isinstance(self.backend, str):
            if self.backend in {"transformers", "huggingface", "hf"}:
                self.backend = TransformersSFTBackend()
            else:
                raise TrainingError(f"Unknown training backend: {self.backend!r}")

    def train(
        self,
        dataset: Any,
        *,
        task: str = "sft",
        epochs: float = 1.0,
        batch_size: int = 2,
        learning_rate: float = 2e-5,
        max_seq_length: int | None = None,
        gradient_accumulation_steps: int = 1,
        **options: Any,
    ) -> Any:
        request = TrainingRequest(
            model=self.model,
            dataset=dataset,
            output_dir=self.output_dir,
            task=task,
            epochs=epochs,
            batch_size=batch_size,
            learning_rate=learning_rate,
            max_seq_length=max_seq_length,
            gradient_accumulation_steps=gradient_accumulation_steps,
            options=options,
        )
        return self.backend.train(request)

    def train_sft(self, dataset: Any, **kwargs: Any) -> Any:
        """Convenience wrapper for supervised fine-tuning."""
        return self.train(dataset, task="sft", **kwargs)


class LLMTrainer(UniversalTrainer):
    """Backward-compatible alias for the previous TigerDataLab trainer."""


def register_training_backend(
    function: Callable[[TrainingRequest], Any],
    *,
    name: str = "custom",
    capabilities: TrainingCapabilities | None = None,
) -> Callable[[TrainingRequest], Any]:
    """Return a callable decorated/registered as a custom backend.

    This helper keeps integration simple for providers whose training API is not
    part of TigerDataLab's optional dependencies.
    """
    return CallableTrainingBackend(function, name=name, capabilities=capabilities).function


def train_sft(
    dataset: Any,
    model: Any,
    output_dir: str | Path = "./tigerdatalab-model",
    *,
    backend: TrainingBackend | str = "auto",
    **kwargs: Any,
) -> Any:
    """Fine-tune any model supported by the selected training adapter."""
    return UniversalTrainer(model, output_dir, backend=backend).train_sft(dataset, **kwargs)
