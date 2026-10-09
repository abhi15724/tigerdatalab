# Tool Development

- Define each tool with a stable name, clear description and explicit input schema.
- Reject unknown arguments; validate types, required fields and size limits before calling the handler.
- Apply least privilege. Read-only tools are the default; sensitive writes need explicit permission and enforced approval.
- Use timeouts, bounded outputs, sanitized errors and structured logs.
- Never expose unrestricted shell, filesystem, network or database access to a model by default.
- Do not treat a JSON schema alone as a security boundary; validate again inside the handler.
- Unit-test disabled tools, malformed input, exceptions, oversized results and authorization failures.
