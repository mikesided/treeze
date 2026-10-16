"""
Name:         security.py
Description:  Security mehods
"""
# ______________________________________________________________________________________________________________________
# Imports

# ______________________________________________________________________________________________________________________

def is_origin_allowed(
    origin: str | None,
    allowed_origins: list[str] | tuple[str, ...] | None = None,
) -> bool:
    """Allow every origin when unset; otherwise require an exact match."""
    return allowed_origins is None or origin in allowed_origins
