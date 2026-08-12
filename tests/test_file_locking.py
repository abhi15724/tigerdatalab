"""Reproduces: writing cleaned_data.xlsx (or any report output) while the
file is open in Excel, or briefly locked by a cloud-sync tool like
OneDrive, raised a raw PermissionError and crashed the whole
result.report() call, losing every other output too.
"""
from pathlib import Path

import pandas as pd
import pytest

from tigerdatalab.reporting._safe_io import write_with_fallback
from tigerdatalab.reporting.exporters import save_cleaned_excel, save_json


def test_transient_lock_retries_and_succeeds_on_original_path(tmp_path):
    target = tmp_path / "transient.txt"
    calls = []

    def flaky_write(p):
        calls.append(p)
        if len(calls) < 3:
            raise PermissionError("file is locked")
        p.write_text("ok")

    result = write_with_fallback(target, flaky_write, max_retries=3, retry_delay=0.01)
    assert result == target
    assert target.read_text() == "ok"


def test_permanently_locked_file_falls_back_with_warning(tmp_path):
    # Mirrors a real Excel lock: the exact open filename can't be
    # written, but a differently-named file can.
    target = tmp_path / "locked_in_excel.xlsx"

    def realistic_lock(p):
        if p.name == target.name:
            raise PermissionError("[Errno 13] Permission denied")
        p.write_text("fallback ok")

    with pytest.warns(RuntimeWarning, match="could not be written"):
        result = write_with_fallback(target, realistic_lock, max_retries=1, retry_delay=0.01)

    assert result != target
    assert result.exists()
    assert result.stem.startswith("locked_in_excel_")


def test_locked_original_and_fallback_raises_clear_error(tmp_path):
    target = tmp_path / "always_locked.xlsx"

    def always_locked(p):
        raise PermissionError("[Errno 13] Permission denied")

    with pytest.raises(PermissionError, match="likely open in another program"):
        write_with_fallback(target, always_locked, max_retries=1, retry_delay=0.01)


def test_save_cleaned_excel_falls_back_when_locked(tmp_path, monkeypatch):
    target = tmp_path / "cleaned_data.xlsx"
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})

    import pandas as pd_module
    original_to_excel = pd_module.DataFrame.to_excel

    def patched_to_excel(self, path, *args, **kwargs):
        if Path(path).name == target.name:
            raise PermissionError("[Errno 13] Permission denied")
        return original_to_excel(self, path, *args, **kwargs)

    monkeypatch.setattr(pd_module.DataFrame, "to_excel", patched_to_excel)

    with pytest.warns(RuntimeWarning):
        result = save_cleaned_excel(target, df)

    assert result != target
    assert result.exists()
