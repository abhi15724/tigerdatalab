"""TigerDataLab — unified data intelligence and AI engineering platform."""
from .config import __version__
from .core import AnalysisResult, analyze, open, large, profile, quality_check, clean_file
from .exceptions import TigerDataLabError, UnsupportedFileTypeError, NoTrendDataError, NoCustomerIdentifierError
from .platform import AIProject, CompanyAIProject, DataPipeline, DataScience, DatasetProfile, TigerDataLab, create_project
from . import ai

__all__ = [
    "__version__", "AnalysisResult", "analyze", "open", "large", "profile", "quality_check", "clean_file",
    "TigerDataLabError", "UnsupportedFileTypeError", "NoTrendDataError", "NoCustomerIdentifierError",
    "TigerDataLab", "create_project", "DataPipeline", "DataScience", "DatasetProfile", "AIProject", "CompanyAIProject", "ai",
]
