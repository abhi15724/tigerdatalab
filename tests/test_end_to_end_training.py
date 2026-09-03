from pathlib import Path

from tigerdatalab import create_project
from tigerdatalab.ai import CallableTrainingBackend, TrainingCapabilities


def test_end_to_end_project_prepares_validates_splits_and_exports(tmp_path: Path):
    source = [
        {"instruction": "What is the return policy?", "response": "30 days"},
        {"instruction": "How do I reset my password?", "response": "Use Settings."},
        {"instruction": "How do I reset my password?", "response": "Use Settings."},
        {"instruction": "", "response": "invalid"},
    ]

    project = create_project("demo")
    ai = project.ai_training(
        "support",
        source=source,
        output_dir=tmp_path,
    )

    ai.clean_data()
    validation = ai.validate_data()
    assert validation is not None
    assert len(ai.dataset.prepared) == 2

    splits = ai.split_dataset()
    assert set(splits) == {"train", "validation", "test"}
    assert sum(map(len, splits.values())) == 2

    out = ai.export_dataset()
    assert (out / "train.jsonl").exists()
    assert (out / "validation.jsonl").exists()
    assert (out / "test.jsonl").exists()
    assert (out / "quality_report.json").exists()
    assert (out / "lineage.json").exists()
    assert (out / "dataset_card.md").exists()


def test_end_to_end_project_uses_custom_training_backend(tmp_path: Path):
    source = [
        {"instruction": "Hello", "response": "Hi"},
        {"instruction": "Bye", "response": "Goodbye"},
    ]
    captured = {}

    def train(request):
        captured["model"] = request.model
        captured["task"] = request.task
        captured["records"] = len(request.dataset)
        return "submitted"

    backend = CallableTrainingBackend(
        train,
        name="test-backend",
        capabilities=TrainingCapabilities(local=False),
    )

    project = create_project("demo")
    ai = project.ai_training(
        "support",
        source=source,
        output_dir=tmp_path,
    )
    result = ai.train_model(
        model="company-model",
        backend=backend,
    )

    assert result == "submitted"
    assert captured == {"model": "company-model", "task": "sft", "records": 1}
