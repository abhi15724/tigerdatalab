"""TigerDataLab — automated Data Analytics + Data Quality + AI Data layer.

    import tigerdatalab as tdl
    result = tdl.analyze("sales.xlsx")
    ai_data = tdl.ai.prepare("support.csv", task="sft")
"""
from .config import __version__
from .core import AnalysisResult, analyze, open, large, profile, quality_check, clean_file
from .exceptions import TigerDataLabError, UnsupportedFileTypeError, NoTrendDataError, NoCustomerIdentifierError
from . import ai

__all__ = [
    "__version__", "AnalysisResult", "analyze", "open", "large",
    "profile", "quality_check", "clean_file", "ai",
    "TigerDataLabError", "UnsupportedFileTypeError", "NoTrendDataError", "NoCustomerIdentifierError",
]
