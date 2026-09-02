"""TigerDataLab AI training-data and optional LLM training layer.

Data preparation is local-first and has no model dependency. Install the
optional ``train`` extra to fine-tune Hugging Face causal language models with
TRL.
"""
from .datasets import (
    deterministic_split_records,
    split_records,
    to_classification,
    to_dpo,
    to_instruction,
    to_sft,
    to_text,
)
from .dedup import deduplicate, fingerprint
from .pipeline import AIDataset, prepare
from .privacy import PIIFinding, PIIScanner, mask_record
from .quality import label_distribution, quality_metrics
from .schema import ValidationIssue, ValidationReport, validate_record, validate_records
from .training import LLMTrainer, TrainingDependencyError, train_sft

__all__ = [
    "AIDataset", "prepare", "LLMTrainer", "train_sft", "TrainingDependencyError",
    "PIIScanner", "PIIFinding", "mask_record",
    "to_sft", "to_instruction", "to_dpo", "to_classification", "to_text",
    "split_records", "deterministic_split_records", "deduplicate", "fingerprint",
    "ValidationIssue", "ValidationReport", "validate_record", "validate_records",
    "quality_metrics", "label_distribution",
]
