"""Optional LLM fine-tuning integration.

The training backend is intentionally optional. TigerDataLab remains lightweight
for users who only need data preparation, while users who install the ``train``
extra can fine-tune Hugging Face causal language models with TRL.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping


class TrainingDependencyError(ImportError):
    """Raised when optional LLM training dependencies are not installed."""


class LLMTrainer:
    """Train a causal language model from a prepared :class:`AIDataset`.

    This is a thin, provider-neutral wrapper around Hugging Face Transformers,
    Datasets and TRL. It does not send training data to TigerDataLab or any
    external service. Model downloads are handled by the Hugging Face stack.
    """

    def __init__(self, model: str, output_dir: str | Path = "./tigerdatalab-model"):
        self.model = model
        self.output_dir = str(output_dir)

    @staticmethod
    def _dependencies():
        try:
            from datasets import load_dataset
            from transformers import AutoModelForCausalLM, AutoTokenizer
            from trl import SFTConfig, SFTTrainer
        except ImportError as exc:
            raise TrainingDependencyError(
                "LLM training requires optional dependencies. Install with "
                "`pip install 'tigerdatalab[train]'`."
            ) from exc
        return load_dataset, AutoModelForCausalLM, AutoTokenizer, SFTConfig, SFTTrainer

    def train_sft(
        self,
        dataset: Any,
        *,
        epochs: float = 1.0,
        batch_size: int = 2,
        learning_rate: float = 2e-5,
        max_seq_length: int | None = None,
        gradient_accumulation_steps: int = 1,
        **trainer_kwargs: Any,
    ) -> Any:
        """Fine-tune a causal LM with supervised fine-tuning (SFT).

        ``dataset`` may be an ``AIDataset`` that has already been run/exported,
        a path to a JSONL file, or a Hugging Face Dataset object.
        """
        load_dataset, AutoModelForCausalLM, AutoTokenizer, SFTConfig, SFTTrainer = self._dependencies()

        if hasattr(dataset, "prepared"):
            records = list(dataset.prepared)
            if not records:
                dataset.run()
                records = list(dataset.prepared)
            hf_dataset = load_dataset("json", data_files=_records_to_temp_jsonl(records), split="train")
        elif isinstance(dataset, (str, Path)):
            hf_dataset = load_dataset("json", data_files=str(dataset), split="train")
        else:
            hf_dataset = dataset

        tokenizer = AutoTokenizer.from_pretrained(self.model)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        model = AutoModelForCausalLM.from_pretrained(self.model)

        config_kwargs = dict(
            output_dir=self.output_dir,
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            learning_rate=learning_rate,
            gradient_accumulation_steps=gradient_accumulation_steps,
            report_to="none",
            **trainer_kwargs,
        )
        if max_seq_length is not None:
            config_kwargs["max_length"] = max_seq_length

        args = SFTConfig(**config_kwargs)
        trainer_kwargs = {"model": model, "args": args, "train_dataset": hf_dataset}
        # TRL versions before/after the tokenizer->processing_class rename are
        # supported without making the core package depend on a specific TRL.
        try:
            trainer = SFTTrainer(processing_class=tokenizer, **trainer_kwargs)
        except TypeError:
            trainer = SFTTrainer(tokenizer=tokenizer, **trainer_kwargs)
        trainer.train()
        trainer.save_model(self.output_dir)
        tokenizer.save_pretrained(self.output_dir)
        return trainer


def _records_to_temp_jsonl(records: Iterable[Mapping[str, Any]]) -> str:
    """Write in-memory records to a temporary JSONL file for Datasets loading."""
    import json
    import tempfile

    handle = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", encoding="utf-8", delete=False)
    with handle:
        for record in records:
            handle.write(json.dumps(dict(record), ensure_ascii=False) + "\n")
    return handle.name


def train_sft(
    dataset: Any,
    model: str,
    output_dir: str | Path = "./tigerdatalab-model",
    **kwargs: Any,
) -> Any:
    """Convenience function for supervised fine-tuning."""
    return LLMTrainer(model, output_dir).train_sft(dataset, **kwargs)
