"""Shared helper for writing output files safely on Windows.

A very common real-world failure: the target file (cleaned_data.xlsx,
dashboard.html, ...) is already open in Excel/a browser, or is briefly
locked by a cloud-sync tool (OneDrive/Dropbox/Google Drive), both of
which raise a plain PermissionError with no useful context. Rather than
crashing the whole report() call and losing every other output, this
retries briefly, then falls back to a timestamped filename so the run's
output isn't lost, and explains clearly why.
"""
from __future__ import annotations

import datetime
import time
import warnings
from pathlib import Path
from typing import Callable


def write_with_fallback(
    path: str | Path,
    write_fn: Callable[[Path], None],
    max_retries: int = 2,
    retry_delay: float = 0.5,
) -> Path:
    """Call ``write_fn(path)`` to write a file, retrying briefly on
    PermissionError (transient cloud-sync locks resolve quickly). If the
    file is still locked (most often because it's open in Excel or
    another program), write to a timestamped sibling filename instead of
    losing the output, and warn clearly about what happened."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    last_error: PermissionError | None = None
    for attempt in range(max_retries + 1):
        try:
            write_fn(path)
            return path
        except PermissionError as exc:
            last_error = exc
            if attempt < max_retries:
                time.sleep(retry_delay)

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    fallback = path.with_name(f"{path.stem}_{stamp}{path.suffix}")
    try:
        write_fn(fallback)
    except PermissionError as exc:
        raise PermissionError(
            f"Could not write to '{path}' or fallback '{fallback}'. This "
            f"file is most likely open in another program (e.g. Excel) or "
            f"locked by a sync tool (OneDrive/Dropbox/Google Drive) - "
            f"close it and re-run. Original error: {exc}"
        ) from exc

    warnings.warn(
        f"'{path}' could not be written (likely open in another program, "
        f"or locked by OneDrive/Dropbox sync) - wrote '{fallback}' "
        f"instead. Close the original file if you need that exact name.",
        RuntimeWarning,
        stacklevel=3,
    )
    return fallback
