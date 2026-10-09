import pytest

from tigerdatalab.ai import AgentFactory, AgentTemplate, Provider, AIResponse, Tool


class FakeProvider(Provider):
    name = "fake"

    def chat(self, messages, model, **kwargs):
        return AIResponse(text="factory works", model=model)


def test_factory_creates_agent_from_template():
    factory = AgentFactory("demo")
    factory.register_template(AgentTemplate(
        name="assistant", provider="openrouter", model="example/model",
        system_prompt="Be concise.",
    ))
    agent = factory.create("assistant", provider=FakeProvider())
    assert agent.name == "demo-assistant"
    assert agent.ready
    assert agent.ask("hello").output == "factory works"
    assert factory.get(agent.name) is agent
    assert factory.list_agents() == [{"name": "demo-assistant", "ready": True}]


def test_factory_registers_allow_listed_tools():
    factory = AgentFactory()
    factory.register_tool(Tool("lookup", "Lookup an item", lambda item_id: item_id))
    factory.register_template(AgentTemplate(
        name="lookup-agent", provider="openrouter", model="m",
        system_prompt="Use approved tools only.", tool_names=("lookup",),
    ))
    agent = factory.create("lookup-agent", provider=FakeProvider())
    assert len(agent.tools) == 1


def test_factory_rejects_unknown_tools_and_duplicate_templates():
    factory = AgentFactory()
    with pytest.raises(ValueError, match="unregistered tools"):
        factory.register_template(AgentTemplate(
            name="bad", provider="openrouter", model="m",
            system_prompt="test", tool_names=("shell",),
        ))
    template = AgentTemplate(name="ok", provider="openrouter", model="m", system_prompt="test")
    factory.register_template(template)
    with pytest.raises(ValueError, match="already registered"):
        factory.register_template(template)


def test_factory_rejects_duplicate_agent_names():
    factory = AgentFactory()
    factory.register_template(AgentTemplate(
        name="assistant", provider="openrouter", model="m", system_prompt="test"
    ))
    factory.create("assistant", provider=FakeProvider())
    with pytest.raises(ValueError, match="Agent already exists"):
        factory.create("assistant", provider=FakeProvider())


def test_factory_config_rejects_unknown_keys_and_missing_required_fields():
    factory = AgentFactory()
    with pytest.raises(ValueError, match="Unsupported"):
        factory.create_from_config({"name": "x", "model": "m", "system_prompt": "x", "api_key": "secret"})
    with pytest.raises(ValueError, match="model cannot be empty"):
        factory.create_from_config({"name": "x", "system_prompt": "x"}, provider=FakeProvider())


def test_factory_config_registers_and_creates():
    factory = AgentFactory("sample")
    agent = factory.create_from_config({
        "name": "helper", "provider": "openrouter", "model": "sample/model",
        "system_prompt": "Helpful assistant", "description": "Demo",
    }, provider=FakeProvider())
    assert agent.name == "sample-helper"
    assert factory.list_templates()[0]["description"] == "Demo"
