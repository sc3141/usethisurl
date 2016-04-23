import re
import string

# from RFC 1738, http://www.ietf.org/rfc/rfc1738.txt

_alpha = r'A-z'
_digit = r'0-9'
_extra = r"!*'(),*"
_safe_without_hyphen = r'$).+'
_hyphen = '-'
_safe = r''.join([_safe_without_hyphen, _hyphen])
_unreserved_without_hyphen = r''.join([_alpha, _digit, _extra, _safe_without_hyphen])
_unreserved = r''.join([_alpha, _digit, _extra, _safe])
_reserved = ';/?:@&='
_escape = '%'
_xchar = r''.join([_unreserved_without_hyphen, _escape, _reserved, _hyphen])

_fragment = '#'

ALLOWED_PAT = ''.join(['[', _xchar, ']'])
ALLOWED_RE = re.compile(ALLOWED_PAT)
DISALLOWED_PAT = ''.join(['[^', _xchar, ']'])
DISALLOWED_RE = re.compile(DISALLOWED_PAT)


def find_unsafe_url_char(s):
    """
    Indicates the presence of an invalid character in a prospective url
    Args:
        s(str): a prospective url

    Returns:
        ~re.MatchObject: match object which describes location and value of matched character.
         Returns None if prohibited characters are not present
    """
    return DISALLOWED_RE.search(s)


def validate_url(s, allow_fragment=False):
    """
    Performs simplistic validation of a string with respect to a url.
    The only check made is that the s contains only 'safe' characters per RFC1738
    If the string is deemed invalid, a ValueError is raised.

    Args:
        s(str): prospective url
        allow_fragment(bool): suppress errors induced by the presence of a fragment character (#)

    Returns:
        None

    Raises:
        ValueError.
    """
    unsafe = ''
    message = ''
    m = find_unsafe_url_char(s)
    if m:
        unsafe = m.group()

    if unsafe:
        if unsafe[0] == _fragment:
            if not allow_fragment:
                message = 'fragment ({}) embedded at position {:d}'.format(unsafe, m.start())
        elif unsafe.isspace():
            message = 'whitespace ({}) embedded at position {:d}'.format(unsafe.encode('string_escape'), m.start())
        elif unsafe in string.printable:
            message = 'unsafe character ({}) embedded at position {:d}'.format(m.group(), m.start())
        else:
            message = 'control character ({}) embedded at position {:d}'.format(
                unsafe.encode('string_escape'), m.start())

    if message:
        raise ValueError(': '.join(('unsafe url', message)))
