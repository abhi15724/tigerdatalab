"""Contract tests for the AI training-data layer."""
from pathlib import Path

from tigerdatalab.ai import (
    AIDataset,
    deterministic_split_records,
    to_classification,
    to_dpo,
    to_instruction,
    to_sft,
    validate_records,
)


def test_adapters_cover_common_training_formats():
    assert to_sft({"prompt": "Hi", "response": "Hello"})["messages"][-1]["content"] == "Hello"
    assert to_instruction({"instruction": "Summarize", "output": "Done"})["output"] == "Done"
    assert to_dpo({"prompt": "Q", "chosen": "A", "rejected": "B"})["chosen"] == "A"
    assert to_classification({"text": "refund", "label": "billing"}) == {"text": "refund", "label": "billing"}


def test_sft_validation_rejects_malformed_records():
    report = validate_records([{"messages": [{"role": "user", "content": "hello"}]}], "sft")
    assert report.valid == 0
    assert report.invalid == 1
    assert report.issues[0].code == "missing_user_or_assistant"


def test_hash_split_is_stable_and_disjoint():
    records = [{"text": f"record-{i}"} for i in range(100)]
    first = deterministic_split_records(records)
    second = deterministic_split_records(list(reversed(records)))
    assert first == second
    assert set(map(str, first["train"])).isdisjoint(set(map(str, first["test"])))
    assert sum(len(v) for v in first.values()) == 100


def test_pipeline_masks_pii_deduplicates_and_exports(tmp_path: Path):
    rows = [
        {"prompt": "Email me at test@example.com", "response": "Sure"},
        {"prompt": "Email me at test@example.com", "response": "Sure"},
        {"prompt": "No email", "response": "Another answer"},
    ]
    dataset = AIDataset(rows, "sft").run()
    assert dataset.stats["input_records"] == 3
    assert dataset.stats["duplicates_removed"] == 1
    assert dataset.stats["pii_masked"]["email"] == 1
    assert "[EMAIL]" in dataset.prepared[0]["messages"][0]["content"]

    out = dataset.export(tmp_path)
    assert (out / "train.jsonl").exists()
    assert (out / "validation.jsonl").exists()
    assert (out / "test.jsonl").exists()
    assert (out / "quality_report.json").exists()
    assert (out / "lineage.json").exists()
    assert (out / "dataset_card.md").exists()


def test_backward_compatible_positional_export(tmp_path: Path):
    dataset = AIDataset([{"prompt": "a", "response": "b"}], "sft").run()
    out = dataset.export(tmp_path, split_strategy="positional")
    assert (out / "train.jsonl").exists()
