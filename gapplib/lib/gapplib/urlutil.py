
import re
import urllib

# from RFC 1738, http://www.ietf.org/rfc/rfc1738.txt

_alpha = ur'A-z'
_digit = ur'0-9'
_extra = ur"!*'(),*"
_safe_without_hyphen = ur'$).+'
_hyphen = ur'-'
_safe = ur''.join([_safe_without_hyphen, _hyphen])
_unreserved_without_hyphen = r''.join([_alpha, _digit, _extra, _safe_without_hyphen])
_unreserved = ur''.join([_alpha, _digit, _extra, _safe])
_reserved = ur';/?:@&='
_escape = ur'%'
_xchar = ur''.join([_unreserved_without_hyphen, _escape, _reserved, _hyphen])

_fragment = ur'#'

ALLOWED_PAT = ur''.join([ur'[', _xchar, u']'])
ALLOWED_RE = re.compile(ALLOWED_PAT, flags=re.UNICODE)
DISALLOWED_PAT = ur''.join([ur'[^', _xchar, u']'])
DISALLOWED_RE = re.compile(DISALLOWED_PAT, flags=re.UNICODE)

WHITE_SPACE_PAT = ur'\s'
WHITE_SPACE_RE = re.compile(WHITE_SPACE_PAT, flags=re.UNICODE)

CONTROL_CODE_PAT=ur'[\u0000-\u001F\u007F-\u009F]'
CONTROL_CODE_RE=re.compile(CONTROL_CODE_PAT, flags=re.UNICODE)

CONTROL_CODE_OR_WHITESPACE_PAT = ur''.join([
    WHITE_SPACE_PAT, ur'|', CONTROL_CODE_PAT
])
CONTROL_CODE_OR_WHITESPACE_RE = re.compile(CONTROL_CODE_OR_WHITESPACE_PAT, flags=re.UNICODE)



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


NOT_PRINT_ASCII_PAT = ur'[^ -~]+'
NOT_PRINT_ASCII_RE = re.compile(NOT_PRINT_ASCII_PAT, re.UNICODE)

def quote_non_ascii(s):
    """
    Returns a unicode in which non-ascii unicode characters have been quoted

    Args:
        s(unicode): unicode string to be quoted

    Returns:
        unicode: a quoted unicode string

    """
    start = 0
    non_ascii = [m for m in NOT_PRINT_ASCII_RE.finditer(s)]
    if non_ascii:
        quoted = []
        for m in non_ascii:
            quoted.append(s[start:m.start()])
            quoted.append(urllib.quote(m.group().encode('utf-8')))
            start = m.end()

        if start != len(s):
            quoted.append(s[start:])

        return u''.join(quoted).encode('utf-8')

    return s


def iri_to_uri(iri):

    uri = iri
    m = CONTROL_CODE_OR_WHITESPACE_RE.search(uri)
    if m:
        print u'START: ({})'.format(m.start())
        if WHITE_SPACE_RE.search(m.group()):
            raise ValueError(
               u'whitespace ({}) embedded at position {:d}'.format(
                   uri.encode('utf-8'), m.start()))
        else:
            print 'TYPE: %s' % uri.__class__.__name__
            raise ValueError(
                u'control character ({}) embedded at position {:d}'.format(
                    uri.encode('unicode_escape'), m.start()))

    quoted = quote_non_ascii(uri)

    m = find_unsafe_url_char(quoted)
    if m:
        raise ValueError(
            u'unsafe character ({}) embedded at position {:d}'.format(m.group(), m.start()))

    return quoted.encode('ascii')



