import pandas as pd
import pytest

from tigerdatalab import TigerDataLab, create_project
from tigerdatalab.ai import AIResponse, Provider


class FakeProvider(Provider):
    name = "fake"

    def chat(self, messages, model, **kwargs):
        return AIResponse(text="company answer", model=model)


def test_unified_project_profiles_and_engineers_data():
    tdl = create_project("demo")
    frame = pd.DataFrame({"sales": [10, 20, None], "region": ["A", "B", "B"]})
    profile = tdl.profile(frame)
    assert profile.rows == 3
    assert profile.columns == 2
    assert profile.missing_cells == 1

    result = tdl.engineering.add("fill", lambda df: df.fillna({"sales": 0})).run(frame)
    assert result["sales"].tolist() == [10, 20, 0]


def test_data_science_split_is_reproducible():
    tdl = TigerDataLab("science")
    frame = pd.DataFrame({"x": range(10)})
    train_a, test_a = tdl.data_science.train_test_split(frame, seed=7)
    train_b, test_b = tdl.data_science.train_test_split(frame, seed=7)
    assert train_a.equals(train_b)
    assert test_a.equals(test_b)
    assert len(train_a) + len(test_a) == 10


def test_company_ai_project_connects_knowledge_and_provider():
    project = TigerDataLab("company").company_ai("support")
    project.add_knowledge("returns", "Unused products may be returned within 30 days.", department="support")
    project.connect(FakeProvider(), "fake-model", system="Follow company policy.")
    result = project.ask("What is the return policy?")
    assert result.output == "company answer"
    assert "30 days" in result.context


def test_pipeline_rejects_invalid_transform():
    with pytest.raises(TypeError):
        TigerDataLab().engineering.add("bad", lambda _: 123).run(pd.DataFrame({"x": [1]}))
