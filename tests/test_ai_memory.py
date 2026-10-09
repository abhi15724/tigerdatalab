import json

import pytest

from tigerdatalab.ai.memory import MemoryError, ProjectMemory, SkillLoader


def test_skill_loader_loads_only_requested_skills(tmp_path):
    root = tmp_path / ".agents" / "skills"
    (root / "data-engineering").mkdir(parents=True)
    (root / "data-engineering" / "SKILL.md").write_text("Use deterministic transforms.", encoding="utf-8")
    (root / "agent-development").mkdir()
    (root / "agent-development" / "SKILL.md").write_text("Build small agents.", encoding="utf-8")

    loader = SkillLoader(root)
    assert loader.list_skills() == ["agent-development", "data-engineering"]
    assert loader.load(["data-engineering"]) == {
        "data-engineering": "Use deterministic transforms."
    }
    assert "agent-development" not in loader.context(["data-engineering"])


def test_skill_loader_rejects_traversal_and_missing_skills(tmp_path):
    loader = SkillLoader(tmp_path / "skills")
    with pytest.raises(MemoryError, match="Invalid skill name"):
        loader.load(["../secrets"])
    with pytest.raises(MemoryError, match="Skill not found"):
        loader.load(["missing"])


def test_skill_loader_enforces_size_limit(tmp_path):
    root = tmp_path / "skills"
    skill = root / "large"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("x" * 20, encoding="utf-8")
    with pytest.raises(MemoryError, match="exceeds"):
        SkillLoader(root, max_skill_bytes=10).load(["large"])


def test_project_memory_round_trip_and_evidence(tmp_path):
    memory = ProjectMemory(tmp_path / "memory")
    memory.write_project({"goal": "unified data and agent platform", "decisions": ["load skills selectively"]})
    project = memory.read_project()
    assert project["goal"] == "unified data and agent platform"
    assert project["updated_at"]

    memory.save_task("run-01", {"status": "running", "completed_steps": ["inspect"]})
    result = memory.record_evidence("run-01", {"kind": "test", "status": "passed", "source": "pytest"})
    assert result["completed_steps"] == ["inspect"]
    assert result["evidence"][0]["status"] == "passed"
    assert memory.load_task("run-01")["task_id"] == "run-01"


def test_memory_rejects_secrets_non_json_and_unsafe_task_ids(tmp_path):
    memory = ProjectMemory(tmp_path / "memory")
    with pytest.raises(MemoryError, match="sensitive field"):
        memory.write_project({"api_key": "do-not-store"})
    with pytest.raises(MemoryError, match="Unsupported JSON value"):
        memory.write_project({"object": object()})
    with pytest.raises(MemoryError, match="Invalid task id"):
        memory.save_task("../outside", {"status": "running"})


def test_memory_documents_are_bounded_and_corruption_is_reported(tmp_path):
    memory = ProjectMemory(tmp_path / "memory", max_document_bytes=80)
    with pytest.raises(MemoryError, match="exceeds"):
        memory.write_project({"note": "x" * 200})

    memory.root.mkdir(parents=True, exist_ok=True)
    (memory.root / "project.json").write_text("{broken", encoding="utf-8")
    with pytest.raises(MemoryError, match="Cannot read"):
        memory.read_project()


def test_task_state_is_valid_json_and_atomically_written(tmp_path):
    memory = ProjectMemory(tmp_path / "memory")
    memory.save_task("task-2", {"status": "completed"})
    payload = json.loads((memory.root / "tasks" / "task-2.json").read_text(encoding="utf-8"))
    assert payload["status"] == "completed"
    assert not (memory.root / "tasks" / "task-2.json.tmp").exists()
