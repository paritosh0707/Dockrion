def validate_api_key(header_value: str | None, expected: str | None) -> None:
    if not expected:
        return
    if not header_value or header_value != expected:
        raise PermissionError("Invalid API Key")
