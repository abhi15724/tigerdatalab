"""JSON + cleaned-data export helpers."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ._safe_io import write_with_fallback


class NumpyJSONEncoder(json.JSONEncoder):
    def default(self, o):
        import numpy as np
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.bool_,)):
            return bool(o)
        if isinstance(o, (np.ndarray,)):
            return o.tolist()
        if pd.isna(o):
            return None
        return super().default(o)


def save_json(path: str | Path, data: dict) -> Path:
    text = json.dumps(data, indent=2, cls=NumpyJSONEncoder, default=str)
    return write_with_fallback(path, lambda p: p.write_text(text, encoding="utf-8"))


def save_cleaned_excel(path: str | Path, df: pd.DataFrame) -> Path:
    return write_with_fallback(path, lambda p: df.to_excel(p, index=False, engine="openpyxl"))
