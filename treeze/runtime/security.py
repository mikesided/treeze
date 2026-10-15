"""
Name:         security.py
Description:  Security mehods
"""
# ______________________________________________________________________________________________________________________
# Imports

from urllib.parse import urlsplit

from starlette.datastructures import Headers

# ______________________________________________________________________________________________________________________

def is_origin_allowed(
    origin: str | None,
    host: str | None,
    allowed_origins: list[str] | None = None,
) -> bool:

    if not origin or origin == 'null':
        return False

    parsed = urlsplit(origin)

    if (
        parsed.scheme not in ('http', 'https')
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        return False

    if allowed_origins is None:
        # Allow any origins
        return True
    else:
        # Explicit white list
        return origin in allowed_origins

def is_same_origin_websocket(headers: Headers) -> bool:
    """Validate a browser WebSocket handshake."""

    origin = headers.get('origin')
    host = headers.get('host')

    if not origin or not host:
        return False

    try:
        parsed = urlsplit(origin)

        if parsed.scheme not in ('http', 'https'):
            return False

        if parsed.netloc.lower() != host.lower():
            return False

        if parsed.path or parsed.query or parsed.fragment:
            return False

    except ValueError:
        return False

    # Additional protection where supported by the browser.
    fetch_site = headers.get('sec-fetch-site')

    if fetch_site is not None and fetch_site != 'same-origin':
        return False

    return True
