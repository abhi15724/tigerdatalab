"""Format-aware loading of CSV, Excel, JSON, Parquet and SQL sources.

`load(path)` is the single entry point used by core.analyze(). It returns a
tuple of (pandas.DataFrame, dict) where the dict carries loader metadata
(source path, detected format, warnings).
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

import pandas as pd

from ..config import SUPPORTED_EXTENSIONS, DESTRUCTIVE_SQL_KEYWORDS
from ..exceptions import UnsupportedFileTypeError, DestructiveSQLError


def _check_sql_safety(sql_text: str) -> None:
    """Raise if the SQL text contains a destructive statement, unless it is
    clearly inside a string literal/comment (best-effort, not a full parser)."""
    statements = [s.strip() for s in sql_text.split(";") if s.strip()]
    for stmt in statements:
        first_word_match = re.match(r"\s*(\w+)", stmt, re.IGNORECASE)
        if not first_word_match:
            continue
        first_word = first_word_match.group(1).upper()
        if first_word in DESTRUCTIVE_SQL_KEYWORDS:
            raise DestructiveSQLError(first_word)


def _load_sql_file(path: Path) -> tuple[pd.DataFrame, dict]:
    """Execute a .sql file's non-destructive statements using an in-memory
    engine (DuckDB if available, otherwise SQLite) and return the result of
    the last SELECT statement found."""
    sql_text = path.read_text(encoding="utf-8", errors="ignore")
    _check_sql_safety(sql_text)

    statements = [s.strip() for s in sql_text.split(";") if s.strip()]
    select_statements = [s for s in statements if re.match(r"^\s*(SELECT|WITH)\b", s, re.IGNORECASE)]

    engine_used = "duckdb"
    try:
        import duckdb
        con = duckdb.connect(database=":memory:")
        last_df = None
        for stmt in statements:
            if re.match(r"^\s*(CREATE|INSERT)\b", stmt, re.IGNORECASE):
                con.execute(stmt)
            elif re.match(r"^\s*(SELECT|WITH)\b", stmt, re.IGNORECASE):
                last_df = con.execute(stmt).fetchdf()
        if last_df is None:
            raise ValueError("No SELECT statement found in SQL file.")
        return last_df, {"format": "sql", "engine": engine_used, "path": str(path)}
    except ImportError:
        engine_used = "sqlite3"
        con = sqlite3.connect(":memory:")
        cur = con.cursor()
        last_df = None
        for stmt in statements:
            if re.match(r"^\s*(CREATE|INSERT)\b", stmt, re.IGNORECASE):
                cur.execute(stmt)
            elif re.match(r"^\s*(SELECT|WITH)\b", stmt, re.IGNORECASE):
                last_df = pd.read_sql_query(stmt, con)
        con.commit()
        if last_df is None:
            raise ValueError("No SELECT statement found in SQL file.")
        return last_df, {"format": "sql", "engine": engine_used, "path": str(path)}


def _load_sqlite_db(path: Path) -> tuple[pd.DataFrame, dict]:
    """Load the largest table from a SQLite/.db file."""
    con = sqlite3.connect(str(path))
    tables = pd.read_sql_query(
        "SELECT name FROM sqlite_master WHERE type='table'", con
    )["name"].tolist()
    if not tables:
        raise ValueError(f"No tables found in database '{path}'.")
    best_table, best_len = tables[0], -1
    for t in tables:
        try:
            n = pd.read_sql_query(f"SELECT COUNT(*) AS n FROM '{t}'", con)["n"].iloc[0]
        except Exception:
            n = 0
        if n > best_len:
            best_len, best_table = n, t
    df = pd.read_sql_query(f"SELECT * FROM '{best_table}'", con)
    return df, {"format": "sqlite", "table": best_table, "path": str(path)}


def _detect_encoding(path: Path) -> str | None:
    """Best-effort encoding detection using charset-normalizer or chardet if
    either is installed. Returns None if neither library is available or
    detection fails, so the caller can fall back to the fixed try-list."""
    raw = path.read_bytes()
    try:
        from charset_normalizer import from_bytes
        result = from_bytes(raw).best()
        if result is not None:
            return result.encoding
    except ImportError:
        pass
    try:
        import chardet
        guess = chardet.detect(raw)
        if guess and guess.get("encoding"):
            return guess["encoding"]
    except ImportError:
        pass
    return None


def _read_csv_skipping_bad_lines(path: Path, encoding: str) -> tuple[pd.DataFrame, str] | None:
    """Re-read a CSV skipping rows whose field count doesn't match the
    header, instead of letting one malformed row abort the whole file.
    Returns None if this still fails, so the caller can keep trying other
    encodings."""
    bad_lines: list[list[str]] = []

    def _capture(bad_line: list[str]) -> None:
        bad_lines.append(bad_line)
        return None  # tells pandas to drop this line

    try:
        df = pd.read_csv(path, encoding=encoding, engine="python", on_bad_lines=_capture)
    except Exception:
        return None
    if df.empty:
        return None
    label = encoding
    if bad_lines:
        label = f"{encoding} (skipped {len(bad_lines)} malformed row(s) - wrong field count)"
    return df, label


def _read_csv_robust(path: Path) -> tuple[pd.DataFrame, str]:
    """Read a CSV that may not be valid UTF-8 and/or may have malformed
    rows (wrong field count).

    Real-world CSVs (especially anything exported from Excel on Windows)
    are frequently encoded as cp1252 / latin-1, not UTF-8 - a plain
    ``pd.read_csv(path)`` raises ``UnicodeDecodeError`` on bytes like 0x92
    (a Windows "smart quote"). This tries a sensible list of encodings and,
    if available, an automatic detector, before giving up.

    Separately, a single hand-edited or export-glitched row with the wrong
    number of fields (e.g. a stray extra comma) makes the C parser raise
    ``ParserError`` and abort the ENTIRE load. Rather than losing the whole
    file over one bad row, that row is skipped and the count is reported
    back in the encoding label so it's visible, not silent.
    """
    tried: list[str] = []

    candidates: list[str] = ["utf-8", "utf-8-sig"]
    detected = _detect_encoding(path)
    if detected:
        candidates.append(detected)
    candidates += ["cp1252", "latin-1"]

    last_error: Exception | None = None
    for enc in candidates:
        if enc in tried:
            continue
        tried.append(enc)
        try:
            df = pd.read_csv(path, encoding=enc)
            return df, enc
        except (UnicodeDecodeError, LookupError) as exc:
            last_error = exc
            continue
        except pd.errors.ParserError as exc:
            last_error = exc
            skip_result = _read_csv_skipping_bad_lines(path, enc)
            if skip_result is not None:
                return skip_result
            continue

    # Last resort: latin-1 can decode any byte sequence (0x00-0xFF maps
    # 1:1 to the first 256 Unicode code points), so this never raises a
    # UnicodeDecodeError - but it's a lossy guess, so only use it if
    # nothing else on our candidate list worked.
    try:
        df = pd.read_csv(path, encoding="latin-1")
        return df, "latin-1 (fallback - re-check text columns for garbled characters)"
    except pd.errors.ParserError:
        skip_result = _read_csv_skipping_bad_lines(path, "latin-1")
        if skip_result is not None:
            return skip_result
    except Exception:
        pass

    raise UnicodeDecodeError(
        "utf-8", b"", 0, 1,
        f"Could not read '{path}' with any of {tried}. Original error: {last_error}"
    )


def load(path: str | Path) -> tuple[pd.DataFrame, dict]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileTypeError(str(path), SUPPORTED_EXTENSIONS)

    if ext == ".csv":
        df, encoding_used = _read_csv_robust(path)
        meta = {"format": "csv", "path": str(path), "encoding": encoding_used}
    elif ext in (".xlsx", ".xlsm"):
        df = pd.read_excel(path, engine="openpyxl")
        meta = {"format": "excel", "path": str(path)}
    elif ext == ".json":
        df = pd.read_json(path)
        meta = {"format": "json", "path": str(path)}
    elif ext == ".parquet":
        df = pd.read_parquet(path)
        meta = {"format": "parquet", "path": str(path)}
    elif ext == ".sql":
        df, meta = _load_sql_file(path)
    elif ext in (".db", ".sqlite"):
        df, meta = _load_sqlite_db(path)
    elif ext == ".duckdb":
        import duckdb
        con = duckdb.connect(str(path), read_only=True)
        tables = con.execute(
            "SELECT table_name FROM information_schema.tables"
        ).fetchdf()["table_name"].tolist()
        if not tables:
            raise ValueError(f"No tables found in DuckDB file '{path}'.")
        df = con.execute(f'SELECT * FROM "{tables[0]}"').fetchdf()
        meta = {"format": "duckdb", "table": tables[0], "path": str(path)}
    else:  # pragma: no cover - guarded above
        raise UnsupportedFileTypeError(str(path), SUPPORTED_EXTENSIONS)

    return df, meta
