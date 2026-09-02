"""TigerDataLab AI data, retrieval, orchestration and evaluation layer."""
from .datasets import deterministic_split_records, split_records, to_classification, to_dpo, to_instruction, to_sft, to_text
from .dedup import deduplicate, fingerprint
from .evaluation import EvaluationResult, Evaluator, evaluate
from .pipeline import AIDataset, prepare
from .privacy import PIIFinding, PIIScanner, mask_record
from .providers import (
    AIResponse,
    AnthropicProvider,
    GeminiProvider,
    GroqProvider,
    MistralProvider,
    OpenAICompatibleProvider,
    OpenAIProvider,
    OpenRouterProvider,
    Provider,
    ProviderError,
    TogetherProvider,
    get_provider,
)
from .quality import label_distribution, quality_metrics
from .rag import Chunk, Document, KnowledgeBase, chunk_text
from .registry import Asset, Registry
from .router import ModelRouter, ModelTarget, RoutingError, router_from_config
from .schema import ValidationIssue, ValidationReport, validate_record, validate_records
from .system import AIResult, CompanyAI
from .agent import CompanyAgent, CompanyAgentProject
from .tools import Tool, ToolError, ToolRegistry, tool
from .training import (
    CallableTrainingBackend,
    LLMTrainer,
    TrainingBackend,
    TrainingCapabilities,
    TrainingError,
    TrainingRequest,
    TrainingDependencyError,
    UniversalTrainer,
    TransformersSFTBackend,
    register_training_backend,
    train_sft,
)
from .workflows import Workflow, WorkflowError, WorkflowResult, WorkflowStep, step

__all__ = [
    "AIDataset", "prepare", "LLMTrainer", "UniversalTrainer", "train_sft",
    "TrainingBackend", "TrainingCapabilities", "TrainingRequest", "TrainingError",
    "TrainingDependencyError", "TransformersSFTBackend", "CallableTrainingBackend",
    "register_training_backend", "PIIScanner", "PIIFinding", "mask_record", "to_sft",
    "to_instruction", "to_dpo", "to_classification", "to_text", "split_records",
    "deterministic_split_records", "deduplicate", "fingerprint", "ValidationIssue",
    "ValidationReport", "validate_record", "validate_records", "quality_metrics",
    "label_distribution", "Provider", "ProviderError", "AIResponse", "OpenAIProvider",
    "OpenAICompatibleProvider", "AnthropicProvider", "GeminiProvider", "GroqProvider",
    "OpenRouterProvider", "MistralProvider", "TogetherProvider", "get_provider", "Document",
    "Chunk", "KnowledgeBase", "chunk_text", "EvaluationResult", "Evaluator", "evaluate",
    "Tool", "ToolError", "ToolRegistry", "tool", "Workflow", "WorkflowError", "WorkflowResult",
    "WorkflowStep", "step", "ModelRouter", "ModelTarget", "RoutingError", "router_from_config",
    "Asset", "Registry", "CompanyAI", "AIResult", "CompanyAgent", "CompanyAgentProject",
]
