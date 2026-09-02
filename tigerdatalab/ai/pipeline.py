"""End-to-end local-first AI training-data preparation pipeline.

The pipeline is deliberately model-provider agnostic: it produces validated,
privacy-aware JSONL datasets that can be consumed by fine-tuning frameworks.
"""
from __future__ import annotations

from pathlib import Path
import csv
import json
from typing import Any, Iterable, Mapping

from .datasets import (
    deterministic_split_records,
    split_records,
    to_classification,
    to_dpo,
    to_instruction,
    to_sft,
    to_text,
)
from .dedup import deduplicate
from .privacy import mask_record
from .quality import quality_metrics
from .schema import validate_records


def _read(source: str | Path | Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(source, (str, Path)):
        return [dict(row) for row in source]
    path = Path(source)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as f:
            return [dict(x) for x in csv.DictReader(f)]
    if suffix == ".jsonl":
        return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    if suffix == ".json":
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, list) else [value]
    raise ValueError("Supported formats: CSV, JSON and JSONL")


_ADAPTERS = {
    "sft": to_sft,
    "instruction": to_instruction,
    "dpo": to_dpo,
    "classification": to_classification,
    "text": to_text,
}


class AIDataset:
    """Prepare a source dataset for LLM/ML training while retaining audit lineage."""

    def __init__(self, source: str | Path | Iterable[Mapping[str, Any]], task: str = "sft"):
        self.source = str(source) if isinstance(source, (str, Path)) else "<in-memory>"
        self.task = task.lower()
        self.rows = _read(source)
        self.prepared: list[dict[str, Any]] = []
        self.stats: dict[str, Any] = {}
        self.validation = None

    def run(self, min_chars: int = 1, max_chars: int | None = None) -> "AIDataset":
        if self.task not in _ADAPTERS:
            raise ValueError("Supported tasks: sft, instruction, dpo, classification, text")
        records: list[dict[str, Any]] = []
        rejected = 0
        pii: dict[str, int] = {}
        too_short = too_long = 0
        adapter = _ADAPTERS[self.task]
        for row in self.rows:
            item = adapter(row)
            if not item:
                rejected += 1
                continue
            text_size = sum(len(v) for v in _string_values(item))
            if text_size < min_chars:
                too_short += 1
                continue
            if max_chars is not None and text_size > max_chars:
                too_long += 1
                continue
            records.append(item)

        # Deduplicate before masking so repeated source examples do not inflate
        # privacy statistics and so the fingerprint remains based on source data.
        records, duplicates = deduplicate(records)
        masked_records: list[dict[str, Any]] = []
        for item in records:
            masked, found = mask_record(item)
            masked_records.append(masked)
            for kind, count in found.items():
                pii[kind] = pii.get(kind, 0) + count
        records = masked_records

        self.validation = validate_records(records, self.task)
        invalid = {issue.index for issue in self.validation.issues}
        if invalid:
            records = [record for i, record in enumerate(records) if i not in invalid]
        self.prepared = records
        self.stats = {
            "input_records": len(self.rows),
            "output_records": len(records),
            "duplicates_removed": duplicates,
            "rejected_records": rejected + len(invalid),
            "too_short": too_short,
            "too_long": too_long,
            "pii_masked": pii,
            "task": self.task,
            "validation": {
                "valid": self.validation.valid,
                "invalid": self.validation.invalid,
                "validity_rate": self.validation.validity_rate,
            },
        }
        return self

    def summary(self) -> dict[str, Any]:
        return dict(self.stats)

    def quality(self) -> dict[str, Any]:
        total = max(len(self.rows), 1)
        retained = len(self.prepared)
        retention = retained / total * 100
        metrics = quality_metrics(self.prepared, self.stats.get("validation", {}).get("validity_rate", 0.0))
        metrics.update({
            "overall": round(min(100.0, metrics["validation_rate"] * .7 + retention * .3), 2),
            "retention": round(retention, 2),
        })
        return metrics

    def export(
        self,
        directory: str | Path,
        train_ratio: float = .8,
        validation_ratio: float = .1,
        split_strategy: str = "hash",
    ) -> Path:
        if not self.prepared:
            self.run()
        out = Path(directory)
        out.mkdir(parents=True, exist_ok=True)
        if split_strategy == "hash":
            splits = deterministic_split_records(self.prepared, train_ratio, validation_ratio)
        elif split_strategy == "positional":
            splits = split_records(self.prepared, train_ratio, validation_ratio)
        else:
            raise ValueError("split_strategy must be 'hash' or 'positional'")
        for name, records in splits.items():
            with (out / f"{name}.jsonl").open("w", encoding="utf-8") as f:
                for record in records:
                    f.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
        quality = self.quality()
        (out / "quality_report.json").write_text(json.dumps(quality, indent=2), encoding="utf-8")
        lineage = {
            "source": self.source,
            "task": self.task,
            "pipeline": ["ingest", "format", "deduplicate", "pii_mask", "validate", "quality", "split", "export"],
            "split_strategy": split_strategy,
            "stats": self.stats,
        }
        (out / "lineage.json").write_text(json.dumps(lineage, indent=2), encoding="utf-8")
        card = [
            "# TigerDataLab Dataset",
            "",
            f"- Source: `{self.source}`",
            f"- Task: `{self.task}`",
            f"- Records: {len(self.prepared)}",
            f"- Quality score: {quality['overall']}",
            f"- Split strategy: `{split_strategy}`",
            "- Privacy: deterministic PII masking enabled",
            "- Deduplication: deterministic SHA-256 fingerprinting enabled",
        ]
        (out / "dataset_card.md").write_text("\n".join(card) + "\n", encoding="utf-8")
        return out


def _string_values(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _string_values(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _string_values(item)


def prepare(source: str | Path | Iterable[Mapping[str, Any]], task: str = "sft") -> AIDataset:
    """Backward-compatible factory for :class:`AIDataset`."""
    return AIDataset(source, task)
