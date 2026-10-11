"""
Name:         openurl.py
Description:  Open a url

"""
# ______________________________________________________________________________________________________________________
# Imports
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from ..core.client_action import ClientAction
from ..core.exceptions import TreezeTypeError, TreezeValueError
from ..core.validation import Validator

# ______________________________________________________________________________________________________________________

@dataclass(frozen=True, slots=True)
class OpenUrl(ClientAction):
    type: str = field(default='open_url', init=False)
    url: str
    new_tab: bool = False

    def __post_init__(self) -> None:
        ClientAction.__post_init__(self)
        Validator.ensure(self.url, str)
        Validator.ensure(self.new_tab, bool)

        if not self.url or self.url != self.url.strip():
            raise TreezeValueError('OpenUrl.url must be a nonempty URL without surrounding whitespace.')
        if any(ord(character) < 32 for character in self.url):
            raise TreezeValueError('OpenUrl.url cannot contain control characters.')
        
        try:
            scheme = urlsplit(self.url).scheme.lower()
        except ValueError as error:
            raise TreezeValueError('OpenUrl.url is invalid.') from error
        if scheme not in ('', 'http', 'https', 'mailto', 'tel'):
            raise TreezeValueError(f'OpenUrl does not support the URL scheme {scheme!r}.')