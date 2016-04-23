import re


def chunk(s, n):
    """
    Returns an iterator of chunks of size n for supplied string, s,
    Args:
        s(str): string to be 'chunked'
        n(int): size of each chunk

    Returns:
        str: a chunk of the string

    Note: This method is a generator.
    """
    if n < 1:
        raise ValueError('strutil.chunk: chunk size must be positive integer')

    # regular expression operate much faster than
    # operations which access string as a sequence.

    chunk_re = re.compile('(.){%d}' % n)
    end = 0
    for match in chunk_re.finditer(s):
        yield match.group()
        end = match.end()

    if end < len(s):
        yield s[end:]


def ellipsicate(s, limit):
    """
    Truncates a s if it is not short enough
    Args:
        s (string): s to potentially truncate
        limit (int): the amount of characters to preserve in the truncation

    Returns:
        string: if string exceeds limit, truncated string plus a trailing ellipsis

    """
    if len(s) > limit:
        return s[:limit] + '...'
    else:
        return s


