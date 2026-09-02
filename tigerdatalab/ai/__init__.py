"""TigerDataLab AI training-data layer.

All public APIs are local-first and provider-agnostic. Optional model-training
frameworks can consume the exported JSONL artifacts without being required by
TigerDataLab itself.
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

__all__ = [
    "AIDataset", "prepare", "PIIScanner", "PIIFinding", "mask_record",
    "to_sft", "to_instruction", "to_dpo", "to_classification", "to_text",
    "split_records", "deterministic_split_records", "deduplicate", "fingerprint",
    "ValidationIssue", "ValidationReport", "validate_record", "validate_records",
    "quality_metrics", "label_distribution",
]
