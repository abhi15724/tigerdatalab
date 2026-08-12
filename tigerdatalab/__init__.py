"""TigerDataLab — an automated Data Analytics + Data Quality + Visualization
+ BI + DataOps layer on top of pandas, numpy, duckdb and plotly.

    import tigerdatalab as tdl
    result = tdl.analyze("sales.xlsx")
    print(result.summary())
    result.report("analysis")
"""
from .config import __version__
from .core import AnalysisResult, analyze, open, large, profile, quality_check, clean_file
from .exceptions import TigerDataLabError, UnsupportedFileTypeError, NoTrendDataError, NoCustomerIdentifierError

__all__ = [
    "__version__", "AnalysisResult", "analyze", "open", "large",
    "profile", "quality_check", "clean_file",
    "TigerDataLabError", "UnsupportedFileTypeError", "NoTrendDataError", "NoCustomerIdentifierError",
]
