"""Reusable, model-agnostic factory for configured TigerDataLab agents."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .agent import CompanyAgent
from .providers import Provider, get_provider
from .rag import Document
from .tools import Tool, ToolError
from .workflows import Workflow


@dataclass(frozen=True)
class AgentTemplate:
    """Reusable configuration. Keep provider credentials in environment variables."""
    name: str
    provider: str
    model: str
    system_prompt: str
    description: str = ""
    tool_names: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for key in ("name", "provider", "model", "system_prompt"):
            if not getattr(self, key).strip():
                raise ValueError(f"{key} cannot be empty")
        if len(set(self.tool_names)) != len(self.tool_names):
            raise ValueError("tool_names cannot contain duplicates")


@dataclass
class AgentFactory:
    """Build agents from validated templates and explicitly registered tools."""
    project_name: str = "default"
    templates: dict[str, AgentTemplate] = field(default_factory=dict)
    _tools: dict[str, Tool] = field(default_factory=dict, repr=False)
    _agents: dict[str, CompanyAgent] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        if not self.project_name.strip():
            raise ValueError("project_name cannot be empty")

    def register_tool(self, item: Tool, *, replace: bool = False) -> "AgentFactory":
        if not isinstance(item, Tool):
            raise TypeError("item must be a tigerdatalab.ai.Tool")
        if item.name in self._tools and not replace:
            raise ToolError(f"Tool already registered in factory: {item.name}")
        self._tools[item.name] = item
        return self

    def register_template(self, template: AgentTemplate, *, replace: bool = False) -> "AgentFactory":
        if not isinstance(template, AgentTemplate):
            raise TypeError("template must be an AgentTemplate")
        if template.name in self.templates and not replace:
            raise ValueError(f"Template already registered: {template.name}")
        missing = [n for n in template.tool_names if n not in self._tools]
        if missing:
            raise ValueError(f"Template references unregistered tools: {', '.join(missing)}")
        self.templates[template.name] = template
        return self

    def create(
        self, template_name: str, *, name: str | None = None,
        provider: Provider | str | None = None, model: str | None = None,
        system_prompt: str | None = None, knowledge: Sequence[Document] = (),
        workflow: Workflow | None = None, tool_names: Sequence[str] | None = None,
    ) -> CompanyAgent:
        """Create a ready CompanyAgent from a registered template."""
        try:
            template = self.templates[template_name]
        except KeyError as exc:
            raise KeyError(f"Unknown agent template: {template_name}") from exc
        agent_name = name or f"{self.project_name}-{template.name}"
        if not agent_name.strip():
            raise ValueError("agent name cannot be empty")
        if agent_name in self._agents:
            raise ValueError(f"Agent already exists in this factory: {agent_name}")
        selected = tuple(template.tool_names if tool_names is None else tool_names)
        missing = [n for n in selected if n not in self._tools]
        if missing:
            raise ValueError(f"Unregistered tools requested: {', '.join(missing)}")
        if len(set(selected)) != len(selected):
            raise ValueError("tool_names cannot contain duplicates")

        provider_value = provider if provider is not None else template.provider
        instance = get_provider(provider_value) if isinstance(provider_value, str) else provider_value
        if not isinstance(instance, Provider):
            raise TypeError("provider must be a supported provider name or Provider instance")

        agent = CompanyAgent(name=agent_name)
        if workflow is not None:
            agent.set_workflow(workflow)
        for document in knowledge:
            if not isinstance(document, Document):
                raise TypeError("knowledge entries must be Document instances")
            agent.add_knowledge(document.source, document.text, **dict(document.metadata))
        for tool_name in selected:
            agent.add_tool(self._tools[tool_name])
        agent.connect(instance, model or template.model,
                      system=system_prompt if system_prompt is not None else template.system_prompt)
        self._agents[agent_name] = agent
        return agent

    def create_from_config(self, config: Mapping[str, Any], **runtime: Any) -> CompanyAgent:
        """Create from a restricted mapping; config cannot inject callables or secrets."""
        allowed = {"name", "provider", "model", "system_prompt", "description", "tool_names"}
        unknown = set(config) - allowed
        if unknown:
            raise ValueError(f"Unsupported agent config keys: {', '.join(sorted(unknown))}")
        if "name" not in config:
            raise ValueError("config must include a template name")
        template = AgentTemplate(
            name=str(config["name"]), provider=str(config.get("provider", "openrouter")),
            model=str(config.get("model", "")), system_prompt=str(config.get("system_prompt", "")),
            description=str(config.get("description", "")), tool_names=tuple(config.get("tool_names", ())),
        )
        if template.name not in self.templates:
            self.register_template(template)
        elif self.templates[template.name] != template:
            raise ValueError(f"Template already exists with different configuration: {template.name}")
        return self.create(template.name, **runtime)

    def get(self, name: str) -> CompanyAgent:
        try:
            return self._agents[name]
        except KeyError as exc:
            raise KeyError(f"Unknown agent: {name}") from exc

    def list_templates(self) -> list[dict[str, Any]]:
        return [{"name": t.name, "provider": t.provider, "model": t.model,
                 "description": t.description, "tool_names": list(t.tool_names)}
                for t in self.templates.values()]

    def list_agents(self) -> list[dict[str, Any]]:
        return [{"name": a.name, "ready": a.ready} for a in self._agents.values()]
