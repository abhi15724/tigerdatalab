import sqlite3
import pytest
from tigerdatalab.ai import APIConnector, PermissionPolicy, SQLConnector, Tool, ToolError, WebhookConnector


def test_permission_policy_is_deny_by_default():
    policy = PermissionPolicy()
    with pytest.raises(ToolError):
        policy.check("employee", "approve_invoice")
    policy.allow("employee", "get_invoice")
    policy.check("employee", "get_invoice")


def test_sql_connector_is_read_only_by_default():
    db = sqlite3.connect(":memory:")
    db.execute("create table invoices(id text, status text)")
    db.execute("insert into invoices values('INV-1','Pending')")
    connector = SQLConnector(db)
    assert connector.request("invoice", query="select * from invoices")[0]["status"] == "Pending"
    with pytest.raises(Exception):
        connector.request("delete", query="delete from invoices")


def test_tool_can_be_registered_for_agent_permissions():
    from tigerdatalab.ai import CompanyAgent
    agent = CompanyAgent("ap")
    agent.add_tool(Tool("get_invoice", "Read invoice", lambda invoice_id: {"id": invoice_id}))
    agent.allow_tool("employee", "get_invoice")
    agent.check_tool_permission("employee", "get_invoice")


def test_approval_workflow():
    from tigerdatalab.ai import CompanyAgent
    agent = CompanyAgent("ap")
    request = agent.request_approval("approve_invoice", {"invoice_id": "INV-1"}, requester="u1")
    assert not agent.approvals.approved(request.id)
    agent.decide_approval(request.id, True)
    assert agent.approvals.approved(request.id)
