"""
Name:         index.py
Description:  Exposes an html index page

"""
# ______________________________________________________________________________________________________________________
# Imports
from html import escape

from .assets import discover_stylesheets

# ______________________________________________________________________________________________________________________


_STYLESHEETS = discover_stylesheets()

def render_index() -> str:
    stylesheet_links = '\n'.join(
        _render_stylesheet_link(stylesheet)
        for stylesheet in _STYLESHEETS
    )

    return f'''\
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <meta
            name="viewport"
            content="width=device-width, initial-scale=1"
        >
{stylesheet_links}
    </head>
    <body>
        <div id="tz-root"></div>
        <script src="/static/client.js"></script>
    </body>
</html>
'''


def _render_stylesheet_link(url: str) -> str:
    escaped_url = escape(
        url,
        quote=True,
    )

    return (
        '        '
        f'<link rel="stylesheet" href="{escaped_url}">'
    )