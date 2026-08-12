"""Custom exception hierarchy for TigerDataLab.

All exceptions are designed to produce clear, user-facing messages instead
of raw stack traces bubbling up from pandas/numpy internals.
"""
from __future__ import annotations


class TigerDataLabError(Exception):
    """Base class for all TigerDataLab errors."""


class UnsupportedFileTypeError(TigerDataLabError):
    def __init__(self, path: str, supported: list[str]):
        self.path = path
        self.supported = supported
        msg = (
            f"TigerDataLab does not support this file type: '{path}'.\n"
            f"Supported formats: {', '.join(supported)}."
        )
        super().__init__(msg)


class NoTrendDataError(TigerDataLabError):
    def __init__(self, candidates: list[str] | None = None):
        candidates = candidates or []
        msg = "No valid date + numeric metric was detected for trend analysis."
        if candidates:
            msg += f"\nAvailable date candidates considered: {', '.join(candidates)}"
        super().__init__(msg)


class NoCustomerIdentifierError(TigerDataLabError):
    def __init__(self):
        super().__init__(
            "Customer-level analysis is unavailable because no customer "
            "identifier column was detected."
        )


class EmptyDatasetError(TigerDataLabError):
    def __init__(self):
        super().__init__("The dataset is empty (0 rows). Nothing to analyze.")


class UpdateMatchedZeroRowsError(TigerDataLabError):
    def __init__(self, where: dict):
        super().__init__(
            f"Update matched 0 rows for condition {where}.\nNo data was changed."
        )


class DeleteMatchedZeroRowsError(TigerDataLabError):
    def __init__(self, where: dict):
        super().__init__(
            f"Delete matched 0 rows for condition {where}.\nNo data was changed."
        )


class DestructiveSQLError(TigerDataLabError):
    def __init__(self, statement_type: str):
        super().__init__(
            f"Refusing to execute destructive SQL statement of type "
            f"'{statement_type}'. Use the DataOps API "
            f"(update/insert/delete/upsert) for explicit, audited writes."
        )


class NoBackupAvailableError(TigerDataLabError):
    def __init__(self):
        super().__init__("No backup snapshot is available to roll back to.")
