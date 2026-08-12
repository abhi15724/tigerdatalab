"""Controlled, audited, rollback-able data modification (DataOps).

Example:
    data = tdl.open("sales.xlsx")
    data.update(where={"product_id": 101}, values={"price": 499})
    data.insert({"product_id": 200, "product": "Mouse", "price": 399})
    data.delete(where={"product_id": 200})
    data.upsert({"product_id": 101, "price": 509}, key="product_id")
    data.save()
"""
from __future__ import annotations

import copy
import datetime as dt
from pathlib import Path

import pandas as pd

from ..exceptions import UpdateMatchedZeroRowsError, DeleteMatchedZeroRowsError, NoBackupAvailableError
from ..io.loaders import load


def _match_mask(df: pd.DataFrame, where: dict) -> pd.Series:
    mask = pd.Series(True, index=df.index)
    for col, val in where.items():
        if col not in df.columns:
            mask &= False
            continue
        mask &= (df[col] == val)
    return mask


class DataAsset:
    """A mutable, audited wrapper around a single tabular dataset."""

    def __init__(self, df: pd.DataFrame, source_path: str | Path, meta: dict | None = None):
        self._df = df.reset_index(drop=True)
        self.source_path = Path(source_path)
        self.meta = meta or {}
        self._backups: list[pd.DataFrame] = []
        self.audit_log: list[dict] = []

    @property
    def df(self) -> pd.DataFrame:
        return self._df

    def _snapshot(self):
        self._backups.append(self._df.copy(deep=True))
        if len(self._backups) > 20:
            self._backups.pop(0)

    def _log(self, operation: str, **kwargs):
        entry = {"timestamp": dt.datetime.now().isoformat(), "operation": operation, **kwargs}
        self.audit_log.append(entry)
        return entry

    # ---- DataOps API ----

    def update(self, where: dict, values: dict) -> dict:
        mask = _match_mask(self._df, where)
        n = int(mask.sum())
        if n == 0:
            raise UpdateMatchedZeroRowsError(where)
        self._snapshot()
        before = self._df.loc[mask, list(values.keys())].to_dict(orient="records")
        for col, val in values.items():
            if col not in self._df.columns:
                self._df[col] = None
            self._df.loc[mask, col] = val
        after = self._df.loc[mask, list(values.keys())].to_dict(orient="records")
        return self._log("update", where=where, values=values, rows_affected=n,
                          columns_affected=list(values.keys()), before=before[:5], after=after[:5])

    def insert(self, row: dict) -> dict:
        self._snapshot()
        new_row = pd.DataFrame([row])
        self._df = pd.concat([self._df, new_row], ignore_index=True)
        return self._log("insert", row=row, rows_affected=1)

    def delete(self, where: dict) -> dict:
        mask = _match_mask(self._df, where)
        n = int(mask.sum())
        if n == 0:
            raise DeleteMatchedZeroRowsError(where)
        self._snapshot()
        removed = self._df.loc[mask].to_dict(orient="records")
        self._df = self._df.loc[~mask].reset_index(drop=True)
        return self._log("delete", where=where, rows_affected=n, removed_sample=removed[:5])

    def upsert(self, row: dict, key: str) -> dict:
        if key not in row:
            raise ValueError(f"upsert requires the key column '{key}' to be present in the row dict.")
        mask = self._df[key] == row[key] if key in self._df.columns else pd.Series(False, index=self._df.index)
        if mask.any():
            return self.update(where={key: row[key]}, values={k: v for k, v in row.items() if k != key})
        else:
            entry = self.insert(row)
            entry["operation"] = "upsert_insert"
            return entry

    def merge(self, other: pd.DataFrame, on: str, how: str = "left") -> dict:
        self._snapshot()
        before_cols = set(self._df.columns)
        self._df = self._df.merge(other, on=on, how=how)
        new_cols = list(set(self._df.columns) - before_cols)
        return self._log("merge", on=on, how=how, new_columns=new_cols, rows_after=int(len(self._df)))

    def rollback(self) -> dict:
        if not self._backups:
            raise NoBackupAvailableError()
        self._df = self._backups.pop()
        return self._log("rollback", rows_after=int(len(self._df)))

    def save(self, path: str | Path | None = None) -> Path:
        target = Path(path) if path else self.source_path
        target.parent.mkdir(parents=True, exist_ok=True)
        ext = target.suffix.lower()
        if ext == ".csv":
            self._df.to_csv(target, index=False)
        elif ext in (".xlsx", ".xlsm"):
            self._df.to_excel(target, index=False, engine="openpyxl")
        elif ext == ".json":
            self._df.to_json(target, orient="records", indent=2)
        elif ext == ".parquet":
            self._df.to_parquet(target, index=False)
        else:
            self._df.to_csv(target.with_suffix(".csv"), index=False)
        self._log("save", path=str(target), rows=int(len(self._df)))
        return target

    def save_audit_log(self, path: str | Path) -> Path:
        from ..reporting.exporters import save_json
        return save_json(path, {"audit_log": self.audit_log})

    def __len__(self):
        return len(self._df)

    def __repr__(self):
        return f"<DataAsset source='{self.source_path}' rows={len(self._df)} cols={self._df.shape[1]}>"


def open_asset(path: str | Path) -> DataAsset:
    df, meta = load(path)
    return DataAsset(df, path, meta)
