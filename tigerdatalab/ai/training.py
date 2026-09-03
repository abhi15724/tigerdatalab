"""Universal, adapter-based LLM training interfaces.

TigerDataLab provides a stable training contract, a production Hugging Face/TRL
backend for compatible local/open models, optional PEFT/LoRA support, and a custom
backend escape hatch for vendor-specific training APIs or proprietary models.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping


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
        quantization=True,
        peft=True,
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
        try:
            from peft import LoraConfig
        except ImportError:
            LoraConfig = None
        return (
            HFDataset,
            load_dataset,
            AutoModelForCausalLM,
            AutoTokenizer,
            SFTConfig,
            SFTTrainer,
            LoraConfig,
        )

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
        if isinstance(dataset, list):
            return hf_dataset_type.from_list(dataset)
        return dataset

    def train(self, request: TrainingRequest) -> Any:
        if request.task.lower() not in {"sft", "supervised", "supervised_fine_tuning"}:
            raise TrainingError(
                f"Transformers backend currently supports SFT only, not {request.task!r}"
            )
        if not isinstance(request.model, str) or not request.model.strip():
            raise TrainingError(
                "Transformers backend requires a Hugging Face model id or local model path"
            )

        (
            HFDataset,
            load_dataset,
            AutoModelForCausalLM,
            AutoTokenizer,
            SFTConfig,
            SFTTrainer,
            LoraConfig,
        ) = self._dependencies()
        hf_dataset = self._load_dataset(request.dataset, load_dataset, HFDataset)
        options = dict(request.options)

        tokenizer = AutoTokenizer.from_pretrained(request.model)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model_kwargs: dict[str, Any] = {}
        if options.pop("load_in_4bit", False):
            model_kwargs["load_in_4bit"] = True
        if options.pop("load_in_8bit", False):
            model_kwargs["load_in_8bit"] = True
        model = AutoModelForCausalLM.from_pretrained(request.model, **model_kwargs)

        use_lora = bool(options.pop("use_lora", False))
        if use_lora:
            if LoraConfig is None:
                raise TrainingDependencyError(
                    "LoRA training requires PEFT. Install with `pip install 'tigerdatalab[train]'`."
                )
            peft_config = LoraConfig(
                r=int(options.pop("lora_r", 16)),
                lora_alpha=int(options.pop("lora_alpha", 32)),
                lora_dropout=float(options.pop("lora_dropout", 0.05)),
                bias=str(options.pop("lora_bias", "none")),
                task_type="CAUSAL_LM",
                target_modules=options.pop("target_modules", None),
            )
        else:
            peft_config = None

        config_kwargs = dict(
            output_dir=request.output_dir,
            num_train_epochs=request.epochs,
            per_device_train_batch_size=request.batch_size,
            learning_rate=request.learning_rate,
            gradient_accumulation_steps=request.gradient_accumulation_steps,
            report_to="none",
            **options,
        )
        if request.max_seq_length is not None:
            config_kwargs["max_length"] = request.max_seq_length

        args = SFTConfig(**config_kwargs)
        trainer_args = {
            "model": model,
            "args": args,
            "train_dataset": hf_dataset,
        }
        if peft_config is not None:
            trainer_args["peft_config"] = peft_config
        try:
            trainer = SFTTrainer(processing_class=tokenizer, **trainer_args)
        except TypeError:
            trainer = SFTTrainer(tokenizer=tokenizer, **trainer_args)
        trainer.train()
        trainer.save_model(request.output_dir)
        tokenizer.save_pretrained(request.output_dir)
        return trainer


class CallableTrainingBackend(TrainingBackend):
    """Adapter for vendor SDKs, proprietary models, or custom training systems."""

    name = "custom"

    def __init__(
        self,
        function: Callable[[TrainingRequest], Any],
        *,
        name: str = "custom",
        capabilities: TrainingCapabilities | None = None,
    ):
        self.function = function
        self.name = name
        if capabilities is not None:
            self.capabilities = capabilities

    def train(self, request: TrainingRequest) -> Any:
        return self.function(request)


class UniversalTrainer:
    """Model-agnostic training facade with pluggable backends."""

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
    """Return a callable decorated/registered as a custom backend."""
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
