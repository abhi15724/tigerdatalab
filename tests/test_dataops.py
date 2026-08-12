import pytest

import tigerdatalab as tdl
from tigerdatalab.exceptions import UpdateMatchedZeroRowsError, DeleteMatchedZeroRowsError, NoBackupAvailableError


def test_insert_update_delete_upsert_rollback(csv_path, tmp_path):
    data = tdl.open(str(csv_path))
    n0 = len(data)

    data.insert({"order_id": "ORD-NEW", "product_id": "SKU-99", "revenue": 999.0})
    assert len(data) == n0 + 1

    entry = data.update(where={"order_id": "ORD-NEW"}, values={"revenue": 555.0})
    assert entry["rows_affected"] == 1
    assert (data.df.loc[data.df["order_id"] == "ORD-NEW", "revenue"] == 555.0).all()

    data.delete(where={"order_id": "ORD-NEW"})
    assert len(data) == n0

    data.upsert({"order_id": "ORD-UP", "revenue": 111.0}, key="order_id")
    assert (data.df["order_id"] == "ORD-UP").any()
    data.upsert({"order_id": "ORD-UP", "revenue": 222.0}, key="order_id")
    assert (data.df.loc[data.df["order_id"] == "ORD-UP", "revenue"] == 222.0).all()

    data.rollback()
    assert (data.df.loc[data.df["order_id"] == "ORD-UP", "revenue"] == 111.0).all()

    out = data.save(tmp_path / "saved.csv")
    assert out.exists()

    audit_path = data.save_audit_log(tmp_path / "audit.json")
    assert audit_path.exists()
    assert len(data.audit_log) > 0


def test_update_zero_rows_raises(csv_path):
    data = tdl.open(str(csv_path))
    with pytest.raises(UpdateMatchedZeroRowsError):
        data.update(where={"order_id": "DOES-NOT-EXIST"}, values={"revenue": 1})


def test_delete_zero_rows_raises(csv_path):
    data = tdl.open(str(csv_path))
    with pytest.raises(DeleteMatchedZeroRowsError):
        data.delete(where={"order_id": "DOES-NOT-EXIST"})


def test_rollback_without_backup_raises(csv_path):
    data = tdl.open(str(csv_path))
    with pytest.raises(NoBackupAvailableError):
        data.rollback()
